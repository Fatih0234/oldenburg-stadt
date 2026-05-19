import json
import re
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pyproj import Transformer
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

# 1. Configuration & Constants
CURRENT_TIME = datetime(2026, 5, 20, 0, 0, 0, tzinfo=timezone.utc) # Project current time

# Keywords in German indicating cyclist impact
BIKE_KEYWORDS = [
    r'\bradweg\w*', r'\bfahrradweg\w*', r'\bradfahrer\w*', r'\bradfahrende\w*',
    r'\bfahrrad\w*', r'\bradspur\w*', r'\bfahrradstraße\w*', r'\bradler\w*',
    r'\bradpiste\w*', r'\bzweirad\w*', r'\bveloweg\w*', r'\bradüberweg\w*',
    r'\brad-und gehweg\w*', r'\bgeh- und radweg\w*', r'\brad- und gehweg\w*',
    r'\blastenrad\w*'
]
keyword_regex = re.compile('|'.join(BIKE_KEYWORDS), re.IGNORECASE)

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
    lat = row['latitude']
    lon = row['longitude']
    category_name = str(row['categoryName'])
    category_id = int(row['categoryId'])
    state = str(row['state'])
    created_at_str = str(row['createdAt'])
    text = str(row['replacingText']) if pd.notna(row['replacingText']) else ""
    
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
    # A. Keyword Score (+50)
    has_keywords = bool(keyword_regex.search(text))
    keyword_score = 50 if has_keywords else 0
    
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
        
    total_score = keyword_score + dist_score + category_score + corridor_bonus + state_score + recency_score
    
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
        "has_cycling_keywords": has_keywords,
        "score_keywords": keyword_score,
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
