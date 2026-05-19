import json
import os

def generate_data_js():
    print("Reading classified_reports.json...")
    with open("classified_reports.json", "r", encoding="utf-8") as f:
        reports = json.load(f)
        
    print("Reading oldenburg_osm_bike.json...")
    with open("oldenburg_osm_bike.json", "r", encoding="utf-8") as f:
        osm_data = json.load(f)
        
    # Convert OSM data to clean GeoJSON LineStrings
    elements = osm_data.get("elements", [])
    features = []
    
    for el in elements:
        if el.get("type") == "way" and "geometry" in el:
            coords = el["geometry"]
            if len(coords) < 2:
                continue
            
            # GeoJSON coordinates are [lon, lat]
            line_coords = [[pt["lon"], pt["lat"]] for pt in coords]
            
            tags = el.get("tags", {})
            properties = {
                "id": el["id"],
                "name": tags.get("name", ""),
                "highway": tags.get("highway", ""),
                "bicycle_road": tags.get("bicycle_road", "") or tags.get("cyclestreet", "")
            }
            
            # Clean up properties to save space
            properties = {k: v for k, v in properties.items() if v}
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": line_coords
                },
                "properties": properties
            })
            
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    print(f"Constructed GeoJSON with {len(features)} bike path features.")
    
    # Write as JS file
    output_file = "data.js"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("// This file is auto-generated. Do not edit manually.\n\n")
        f.write("const CLASSIFIED_REPORTS = ")
        json.dump(reports, f, indent=2, ensure_ascii=False)
        f.write(";\n\n")
        f.write("const BIKE_NETWORK_GEOJSON = ")
        json.dump(geojson, f, indent=2, ensure_ascii=False)
        f.write(";\n")
        
    print(f"Successfully generated {output_file} ({os.path.getsize(output_file) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    generate_data_js()
