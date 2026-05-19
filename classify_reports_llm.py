import os
import sys
import json
import pandas as pd
from typing import Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# 1. Schema Definitions
class CyclingClassification(BaseModel):
    id: int = Field(description="The unique ID of the report being classified.")
    is_cycling_related: bool = Field(
        description="True if the issue is a physical defect, safety hazard, obstruction, or comfort/convenience issue affecting cyclists or cycling infrastructure."
    )
    subcategory: Literal[
        "pothole_damage", "glass_debris", "vegetation_block", "illegal_parking_obstruction",
        "signal_light_timing", "crossing_safety", "signage_detours", "bike_parking",
        "other_cycling", "unrelated"
    ] = Field(description="The specific subtype/nature of the issue.")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for this classification, from 0.0 to 1.0."
    )
    explanation_de: str = Field(
        description="A short, one-sentence explanation in German of why this classification was chosen."
    )

class BatchCyclingClassification(BaseModel):
    classifications: list[CyclingClassification]

# 2. Configuration & API Setup
CACHE_FILE = "llm_classification_cache.json"
CSV_FILE = "stadtverbesserer_snapshot.csv"
MODEL_ID = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
BATCH_SIZE = 15

print("Initializing Gemini Client...")
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
    print("Please run: export GEMINI_API_KEY='your_api_key'", file=sys.stderr)
    sys.exit(1)

client = genai.Client()

# 3. Load Cache
cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
        print(f"Loaded {len(cache)} cached classifications.")
    except Exception as e:
        print(f"⚠️ Warning: Could not parse cache file: {e}. Reinitializing.")

# 4. Load CSV Reports
if not os.path.exists(CSV_FILE):
    print(f"❌ ERROR: Source dataset '{CSV_FILE}' not found.", file=sys.stderr)
    sys.exit(1)

df = pd.read_csv(CSV_FILE)
df['id'] = df['id'].astype(str)

# Filter out already cached records
uncached_df = df[~df['id'].isin(cache.keys())].copy()
total_uncached = len(uncached_df)

if total_uncached == 0:
    print("✅ All reports are already classified and cached. Nothing to do!")
    sys.exit(0)

print(f"Found {total_uncached} uncached reports. Processing in batches of {BATCH_SIZE} using model '{MODEL_ID}'...")

# 5. Batch Processing Loop
SYSTEM_PROMPT = """You are an expert cycling infrastructure safety inspector working with the ADFC (German Cyclist Association) in Oldenburg, Germany.
Your task is to analyze citizen-submitted maintenance reports (in German) and classify them.

Classify each report based on whether it is cycling-related:
- is_cycling_related = True: Any physical defects, cleaning requests, safety hazards, obstructions, traffic signal issues, or network comfort issues that directly or disproportionately affect bicycle riders or cycling infrastructure (e.g. cycleways, cycle streets, shared paths, bike parking, right-turning vehicle conflicts).
- is_cycling_related = False: General urban issues that do not affect cycling or are far from bicycle lanes (e.g. highway potholes, trash dumping in residential parks/playgrounds, broken streetlights in general neighborhoods, abandoned cars in standard parking spaces).

Subcategories to use:
- pothole_damage: Potholes, asphalt cracks, root damage, or buckling on paths.
- glass_debris: Glass shards, debris, leaves, mud, or snow/ice blocking lanes.
- vegetation_block: Overgrown hedges, bushes, branches blocking clearance or sightlines.
- illegal_parking_obstruction: Parked cars, vans, construction signs, or trash bins blocking bike lanes.
- signal_light_timing: Inductive traffic loop sensors failing to detect bikes, or green-light phase too short.
- crossing_safety: Dangerous crossings, missing markings, or conflict zones with turning cars.
- signage_detours: Missing or broken bicycle signposts, or poorly routed construction detours.
- bike_parking: Lack of bike stands or poor/damaged bike parking racks.
- other_cycling: Any other bike-related issues.
- unrelated: For all issues where is_cycling_related is False.

Be objective. Ignore standard keyword tricks; focus on the true intent and physical location described by the citizen."""

uncached_records = uncached_df.to_dict(orient="records")

for i in range(0, total_uncached, BATCH_SIZE):
    batch = uncached_records[i:i + BATCH_SIZE]
    batch_num = (i // BATCH_SIZE) + 1
    total_batches = (total_uncached + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")
    
    # Format batch items for prompt
    items_text = []
    for item in batch:
        text = str(item.get("replacingText", "")).strip()
        cat = str(item.get("categoryName", "")).strip()
        items_text.append(f"Report ID: {item['id']}\nCategory: {cat}\nDescription: {text}\n---")
    
    prompt = "Classify the following batch of citizen reports:\n\n" + "\n".join(items_text)
    
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=BatchCyclingClassification,
                temperature=0.1
            )
        )
        
        # Parse output
        result = json.loads(response.text)
        classifications = result.get("classifications", [])
        
        # Save to local cache memory
        for cl in classifications:
            cache[str(cl["id"])] = {
                "is_cycling_related": cl["is_cycling_related"],
                "subcategory": cl["subcategory"],
                "confidence": cl["confidence"],
                "explanation_de": cl["explanation_de"]
            }
            
        # Write cache to file immediately to prevent data loss if interrupted
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
            
        print(f"  Successfully processed batch {batch_num}. Cache updated.")
        
    except Exception as e:
        print(f"❌ Error processing batch {batch_num}: {e}")
        # Continue to next batch, keeping cache of what succeeded
        continue

print(f"\nAll processing completed! Cache now contains {len(cache)} classifications.")
