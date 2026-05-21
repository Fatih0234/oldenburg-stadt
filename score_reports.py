import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pyproj import Transformer
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from classification.rules import classify_report_rules

# 1. Configuration & Constants
CURRENT_TIME = datetime.now(timezone.utc) # Use actual run time dynamically

def classify_regex(text, category_id):
    return classify_report_rules(text, category_id).is_regex_candidate

# Priority corridors defined by city and ADFC (Fahrradstraßen, Premiumrouten, Green Waves)
PRIORITY_CORRIDORS = {
    "Saarstraße", "Sedanstraße", "Wardenburgstraße", "Ziegelhofstraße", 
    "Würzburger Straße", "Mittelweg", "Babenend", "Rauhehorst", "Nedderend", 
    "Rüthningstraße", "Melkbrink", "Friedrich-August-Platz", "Ofener Straße", 
    "Ammerländer Heerstraße", "Pophankenweg", "Nadorster Straße", "Ole Karkpadd",
    "Elritzenweg", "Querweg", "Haarenufer", "Herbartstraße"
}

# EPSG:4326 (WGS84) to EPSG:32632 (UTM zone 32N) projection for Germany (units in meters)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:32632", always_xy=True)

# Load V2 silver labels
LABELS_V2_FILE = "classification/labels/labels_v2_silver.json"
labels_v2 = {}
if os.path.exists(LABELS_V2_FILE):
    try:
        with open(LABELS_V2_FILE, "r", encoding="utf-8") as f:
            raw_labels_v2 = json.load(f)
        if isinstance(raw_labels_v2, list):
            labels_v2 = {str(item["id"]): item for item in raw_labels_v2}
        elif isinstance(raw_labels_v2, dict):
            labels_v2 = {str(key): value for key, value in raw_labels_v2.items()}
        else:
            raise ValueError("labels_v2_silver.json must contain a list or object.")
        print(f"Loaded {len(labels_v2)} v2 silver labels.")
    except Exception as e:
        print(f"Warning: Failed to load v2 silver labels: {e}")
else:
    print("Warning: classification/labels/labels_v2_silver.json not found. Running with regex fallback only.")

# 2. Load and Project OSM Bike Network
print("Loading OSM bike network...")
with open("oldenburg_osm_bike.json", "r", encoding="utf-8") as f:
    osm_data = json.load(f)

elements = osm_data.get("elements", [])
bike_segments = []

for el in elements:
    if el.get("type") == "way" and "geometry" in el:
        coords = el["geometry"]
        if len(coords) < 2:
            continue
        
        # Project coords to UTM zone 32N
        projected_coords = []
        for pt in coords:
            x, y = transformer.transform(pt["lon"], pt["lat"])
            projected_coords.append((x, y))
            
        line = LineString(projected_coords)
        tags = el.get("tags", {})
        
        bike_segments.append({
            "id": el["id"],
            "geometry": line,
            "name": tags.get("name", ""),
            "highway": tags.get("highway", ""),
            "cycleway": tags.get("cycleway", "") or tags.get("cycleway:both", "") or tags.get("cycleway:left", "") or tags.get("cycleway:right", ""),
            "bicycle_road": tags.get("bicycle_road", "") or tags.get("cyclestreet", "")
        })

print(f"Loaded {len(bike_segments)} projected bike network segments.")

# 3. Load Reports
print("Loading Stadtverbesserer reports...")
df = pd.read_csv("stadtverbesserer_snapshot.csv")
df_coords = df[df['latitude'].notna() & df['longitude'].notna()].copy()
print(f"Processing {len(df_coords)} reports with coordinates.")

# 4. Scorer Function
def score_report(row):
    report_id = str(row['id'])
    lat = row['latitude']
    lon = row['longitude']
    category_name = str(row['categoryName'])
    category_id = int(row['categoryId'])
    state = str(row['state'])
    created_at_str = str(row['createdAt'])
    text = str(row['replacingText']) if pd.notna(row['replacingText']) else ""
    
    # Run hybrid rule router. Clear cases are classified locally; ambiguous
    # generic hazards are routed to cached/future LLM review.
    rule_decision = classify_report_rules(text, category_id)
    is_cycling_related_regex = rule_decision.is_regex_candidate
    
    # Fetch from v2 silver labels.
    has_llm = report_id in labels_v2
    if has_llm:
        llm_data = labels_v2[report_id]
        is_cycling_related = llm_data.get("is_cycling_related", False)
        directness = llm_data.get("directness", "unrelated")
        subcategory = llm_data.get("subcategory", "unrelated")
        llm_confidence = llm_data.get("confidence", 0.0)
        needs_human_review = llm_data.get("needs_human_review", False)
        explanation_de = llm_data.get("reason_de") or llm_data.get("explanation_de", "Klassifiziert via LLM.")
    else:
        is_cycling_related = rule_decision.is_cycling_related
        directness = rule_decision.directness
        subcategory = rule_decision.subcategory
        llm_confidence = rule_decision.confidence
        needs_human_review = rule_decision.needs_llm_review
        explanation_de = rule_decision.reason_de
        
    is_cycling_related_llm = llm_data.get("is_cycling_related", False) if has_llm else None
    
    # Coordinates in UTM 32N
    rx, ry = transformer.transform(lon, lat)
    report_point = Point(rx, ry)
    
    # Find closest segment and its distance
    min_dist = float('inf')
    closest_seg = None
    
    for seg in bike_segments:
        dist = report_point.distance(seg["geometry"])
        if dist < min_dist:
            min_dist = dist
            closest_seg = seg
            
    # Calculate Scores
    # A. LLM Relevance Score (+50 if cycling-related, or penalty if unrelated and LLM is confident)
    # We map score_llm to score_keywords for frontend compatibility.
    score_llm = 50 if is_cycling_related else 0
    
    penalty_score = 0
    if not is_cycling_related and llm_confidence > 0.6:
        penalty_score = -45
        
    # B. Distance Score (up to +35)
    dist_score = 0
    if min_dist <= 10.0:
        dist_score = 35
    elif min_dist <= 25.0:
        dist_score = 20
    elif min_dist <= 50.0:
        dist_score = 10
        
    # C. Category Score (up to +50)
    # 7 is Fundräder (abandoned bikes)
    # 3: Straßen, 4: Verkehrszeichen, 6: Ampel, 5: Straßenbeleuchtung, 10: Privates Grün (encroaching hedges)
    # 11: Öffentliches Grün (blocking branches, fallen trees)
    category_score = 0
    if category_id == 7:
        category_score = 50
    elif category_id in [3, 4, 5, 6, 10]:
        category_score = 15
    elif category_id == 11:
        category_score = 10
        
    # D. Corridor Priority Bonus (+20)
    corridor_bonus = 0
    if closest_seg and closest_seg["name"] in PRIORITY_CORRIDORS:
        # Only apply corridor bonus if within 50m of the corridor
        if min_dist <= 50.0:
            corridor_bonus = 20
            
    # E. State Score (+10 to -20)
    state_score = 0
    if state in ["OPEN", "IN_PROCESS"]:
        state_score = 10
    elif state == "CLOSED":
        state_score = -20
    elif state == "NOT_RESPONSIBLE":
        state_score = -15
        
    # F. Recency Score (-10 if older than 180 days)
    recency_score = 0
    try:
        # Handle formats like 2025-01-01T22:16:23.000+00:00
        # Clean offset representation
        clean_date_str = created_at_str.split('.')[0].replace('Z', '')
        if '+' in clean_date_str:
            clean_date_str = clean_date_str.split('+')[0]
        dt = datetime.strptime(clean_date_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        age_days = (CURRENT_TIME - dt).days
        if age_days > 180:
            recency_score = -10
    except Exception as e:
        # Fallback if parsing fails
        pass
        
    total_score = score_llm + penalty_score + dist_score + category_score + corridor_bonus + state_score + recency_score
    total_score = max(0, total_score) # Clamped to 0
    
    # Classify Confidence Label
    if total_score >= 70:
        label = "Confirmed cycling issue"
    elif total_score >= 40:
        label = "Likely cycling issue"
    elif total_score >= 20:
        label = "Possibly affects cyclists"
    else:
        label = "Not cycling-specific"
        
    return pd.Series({
        "nearest_segment_id": closest_seg["id"] if closest_seg else None,
        "nearest_segment_name": closest_seg["name"] if closest_seg else "",
        "distance_to_bike_path_meters": round(min_dist, 2),
        "is_cycling_related": is_cycling_related,
        "is_cycling_related_regex": is_cycling_related_regex,
        "is_cycling_related_llm": is_cycling_related_llm,
        "directness": directness,
        "subcategory": subcategory,
        "llm_confidence": llm_confidence,
        "needs_human_review": needs_human_review,
        "explanation_de": explanation_de,
        "score_keywords": score_llm,
        "score_penalty": penalty_score,
        "score_distance": dist_score,
        "score_category": category_score,
        "score_corridor": corridor_bonus,
        "score_state": state_score,
        "score_recency": recency_score,
        "confidence_score": total_score,
        "cyclist_impact_label": label
    })

# Apply scoring
scored_info = df_coords.apply(score_report, axis=1)
df_scored = pd.concat([df_coords, scored_info], axis=1)

# 5. Output and stats
print("\n=== CLASSIFICATION SUMMARY ===")
summary_stats = df_scored['cyclist_impact_label'].value_counts()
for label, count in summary_stats.items():
    pct = (count / len(df_scored)) * 100
    print(f"  {label:<25}: {count:>3} ({pct:.1f}%)")

# Save results
df_scored.to_csv("classified_reports.csv", index=False)

# Convert to JSON for easier web usage
json_records = df_scored.to_dict(orient="records")
with open("classified_reports.json", "w", encoding="utf-8") as f:
    json.dump(json_records, f, indent=2, ensure_ascii=False)

print("\nSaved output to classified_reports.csv and classified_reports.json")
