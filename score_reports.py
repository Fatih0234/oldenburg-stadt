import os
import json
import re
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pyproj import Transformer
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

# 1. Configuration & Constants
CURRENT_TIME = datetime.now(timezone.utc) # Use actual run time dynamically

# Keywords indicating cycling-related issues
BIKE_KEYWORDS = [
    r'radwe[gh]\w*', r'fahrradwe[gh]\w*', r'radspur\w*', r'fahrradstraße\w*', r'radschutzstreifen\w*',
    r'schutzstreifen\w*', r'radroute\w*', r'fahrradroute\w*', r'radverkehr\w*',
    r'rad-?\s*und\s*-?gehweg\w*', r'geh-?\s*und\s*-?radweg\w*', r'rad/gehweg\w*',
    r'rad-?\s*und\s*-?fußweg\w*', r'fuß-?\s*und\s*-?radweg\w*',
    r'rad-?\s*und\s*-?wanderweg\w*', r'wander-?\s*und\s*-?radweg\w*',
    r'radüberweg\w*', r'fahrradständer\w*', r'anlehnbügel\w*', r'fahrradbügel\w*', r'stellplatz\w*', r'stellplätze\w*',
    r'lastenrad\w*', r'radler\w*', r'radfahrer\w*', r'radlerin\w*', r'radfahrende\w*',
    r'\bfahrrad\b', r'\bfahrrads\b', r'\bfahrräder\b', r'\bbike\b', r'\bbikes\b',
    r'\bschulweg\w*', r'\bschüler\w*', r'\brad\b', r'\bräder\b'
]

# Unrelated keywords that often trigger false positives
NEG_KEYWORDS = [
    r'\bspielplatz\w*', r'\bspielgerät\w*', r'\bschaukel\w*', r'\brutsche\w*', r'\bsandkiste\w*',
    r'\bkleidercontainer\w*', r'\btextilcontainer\w*', r'\baltkleider\w*', r'\bsperrmüll\w*',
    r'\bhausmüll\w*', r'\bkatze\w*', r'\bkatzen\w*', r'\bhundekot\w*', r'\bhundehaufen\w*',
    r'\bhund\b', r'\bhunde\b',
    r'\bwilder müll\w*', r'\bmülltonne\w*', r'\bgelber sack\w*', r'\bgelbe säcke\w*',
    r'\bplakat\w*', r'\bgraffiti\w*', r'\baufkleber\w*', r'\bschulhof\w*', r'\bparkanlage\w*',
    r'\bglascontainer\w*', r'\baltglascontainer\w*', r'\bautofahrer\w*', r'\bvandalismus\w*',
    r'\babfluss\w*', r'\bwasserzug\w*', r'\bgraben\b', r'\bgully\w*', r'\bböschung\w*', r'\bwaldstück\w*',
    r'\bwohnwagen\w*', r'\bmercedes\w*', r'\baudi\b', r'\bpkw\b', r'\bauto\b',
    r'abgemeldeter\w*', r'radio\w*', r'parkplatz\w*', r'sticker\w*', r'vollgeklebt\w*', r'beklebt\w*',
    r'rasen\w*', r'parkstreifen\w*', r'parkbucht\w*', r'anhänger\w*', r'bootstrailer\w*'
]

HAZARD_KEYWORDS = [
    r'scherben\w*', r'glasscherben\w*', r'glas\b',
    r'schlagloch\w*', r'schlaglöcher\w*', r'loch\b', r'löcher\b', r'uneben\w*', r'abgesackt\w*',
    r'absackung\w*', r'absackungen\w*', r'kante\w*', r'absatz\w*', r'wurzel\w*', r'baumwurzel\w*',
    r'bodenwelle\w*', r'pflasterstein\w*', r'pflastersteine\w*', r'kopfsteinpflaster\w*',
    r'risse\w*', r'riss\b', r'asphalt\w*', r'fahrbahn\w*',
    r'hecke\w*', r'sträucher\w*', r'äste\b', r'zweige\b', r'überhang\w*', r'überhängend\w*',
    r'bewuchs\w*', r'zugewachsen\w*', r'zuparken\w*', r'zugeparkt\w*', r'blockiert\w*', r'versperrt\w*',
    r'hindernis\w*', r'poller\w*', r'pfosten\w*', r'sperrpfosten\w*', r'kuhle\w*',
    r'ampel\w*', r'ampelschaltung\w*', r'induktionsschleife\w*', r'sensor\w*',
    r'schild\w*', r'beschilderung\w*', r'wegweiser\w*',
    r'sturzgefahr\w*', r'rutschgefahr\w*', r'unfallgefahr\w*', r'gefahrenstelle\w*',
    r'marode\w*', r'schade[n]?\b', r'beschädigt\w*', r'begehbar\w*', r'passierbar\w*', r'befahrbar\w*'
]

pos_regex = re.compile('|'.join(BIKE_KEYWORDS), re.IGNORECASE)
neg_regex = re.compile('|'.join(NEG_KEYWORDS), re.IGNORECASE)
hazard_regex = re.compile('|'.join(HAZARD_KEYWORDS), re.IGNORECASE)

def classify_regex(text, category_id):
    text_lower = text.lower()
    
    # Category 7 is Fundräder (abandoned bikes)
    if category_id == 7:
        garbage_keywords = [r'müll', r'möbel', r'abfall', r'sperrmüll', r'schrott', r'entsorgt', r'reifen', r'mülltonne']
        has_garbage = any(re.search(pat, text_lower) for pat in garbage_keywords)
        if has_garbage and not any(x in text_lower for x in ['rad', 'fahrrad', 'bike']):
            return False
        else:
            return True
            
    # Find matching items
    matched_pos = [pat for pat in BIKE_KEYWORDS if re.search(pat, text_lower)]
    matched_neg = [pat for pat in NEG_KEYWORDS if re.search(pat, text_lower)]
    
    has_pos = len(matched_pos) > 0
    has_neg = len(matched_neg) > 0
    has_glass = any(re.search(pat, text_lower) for pat in [r'scherben\w*', r'glasscherben\w*'])
    
    result = False
    
    if has_pos:
        allowed_overrides = [
            r'radweg\w*', r'fahrradweg\w*', r'radspur\w*', r'fahrradstraße\w*', r'schulweg\w*', r'schüler\w*',
            r'radfahrer\w*', r'radfahrende\w*', r'fahrrad\w*', r'\brad\b'
        ]
        has_override = any(re.search(pat, text_lower) for pat in allowed_overrides)
        if has_neg and not has_override:
            result = False
        else:
            result = True
    elif has_glass and category_id in [3, 8]:
        if not has_neg:
            result = True
                
    return result

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
    
    # Run optimized regex classification (heuristic)
    is_cycling_related_regex = classify_regex(text, category_id)
    
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
        # Fallback to regex
        is_cycling_related = is_cycling_related_regex
        directness = "indirect" if is_cycling_related else "unrelated"
        subcategory = "other_cycling" if is_cycling_related else "unrelated"
        llm_confidence = 0.5  # Heuristic classification
        needs_human_review = True
        explanation_de = "Automatisch klassifiziert via Heuristik (Regex-Regeln)."
        
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
