import requests
import json

# Define the bounding box for Oldenburg city based on the coordinate stats:
# min_lat: 53.085, max_lat: 53.198, min_lon: 8.130, max_lon: 8.301
# We expand it slightly to ensure we capture all connecting bike paths.
bbox = "(53.05,8.10,53.22,8.32)"

overpass_url = "https://overpass.kumi.systems/api/interpreter"
overpass_query = f"""
[out:json][timeout:180];
(
  // Dedicated cycleways
  way["highway"="cycleway"]{bbox};

  // Roads with mapped cycle infrastructure
  way["cycleway"]{bbox};
  way["cycleway:left"]{bbox};
  way["cycleway:right"]{bbox};
  way["cycleway:both"]{bbox};

  // Shared paths where bicycles are designated/allowed
  way["highway"="path"]["bicycle"~"designated|yes"]{bbox};
  way["highway"="footway"]["bicycle"~"designated|yes"]{bbox};

  // Bicycle streets / Fahrradstraßen
  way["bicycle_road"="yes"]{bbox};
  way["cyclestreet"="yes"]{bbox};
);
out geom;
"""

print("Sending request to Overpass API...")
headers = {
    "User-Agent": "OldenburgBikeProject/1.0 (contact: fatih.karahan@example.com)",
    "Accept-Charset": "utf-8"
}
try:
    # Use POST with form data
    response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=180)
    response.raise_for_status()
    data = response.json()
    
    # Save the raw JSON response
    output_file = "oldenburg_osm_bike.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    num_elements = len(data.get("elements", []))
    print(f"Success! Saved {num_elements} OSM elements to {output_file}")
except Exception as e:
    print(f"Error querying Overpass API: {e}")
    # Fallback to GET just in case
    print("Trying GET request fallback...")
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, headers=headers, timeout=180)
        response.raise_for_status()
        data = response.json()
        output_file = "oldenburg_osm_bike.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        num_elements = len(data.get("elements", []))
        print(f"Fallback Success! Saved {num_elements} OSM elements to {output_file}")
    except Exception as e_fallback:
        print(f"Fallback also failed: {e_fallback}")

