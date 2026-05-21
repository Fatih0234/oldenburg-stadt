import json
import os
import sys
from typing import Literal

import pandas as pd
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, model_validator
from classification.rules import should_route_to_llm


class CyclingClassificationV2(BaseModel):
    id: str = Field(description="The stable report ID from the source dataset.")
    is_cycling_related: bool = Field(
        description="True when the issue directly or materially affects cyclists, cycling infrastructure, or bicycle parking."
    )
    directness: Literal["direct", "indirect", "nearby_only", "unrelated"] = Field(
        description="How directly the issue affects cycling."
    )
    subcategory: Literal[
        "pothole_damage",
        "glass_debris",
        "vegetation_block",
        "illegal_parking_obstruction",
        "signal_light_timing",
        "crossing_safety",
        "signage_detours",
        "bike_parking",
        "other_cycling",
        "unrelated",
    ] = Field(description="The specific subtype/nature of the issue.")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for this classification, from 0.0 to 1.0.",
    )
    needs_human_review: bool = Field(
        description="True for ambiguous reports, low-confidence labels, or cases requiring location/map inspection."
    )
    reason_de: str = Field(
        description="A short, one-sentence German explanation of why this classification was chosen."
    )

    @model_validator(mode="after")
    def validate_unrelated_consistency(self):
        if not self.is_cycling_related:
            if self.directness != "nearby_only":
                self.directness = "unrelated"
            self.subcategory = "unrelated"
        return self


class BatchCyclingClassificationV2(BaseModel):
    classifications: list[CyclingClassificationV2]


LABELS_FILE = "classification/labels/labels_v2_silver.json"
PROMPT_FILE = "classification/prompts/classification_prompt_v2.md"
CSV_FILE = "stadtverbesserer_snapshot.csv"
ENV_FILE = ".env"


def load_dotenv(path: str = ENV_FILE) -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_dotenv()

MODEL_ID = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
BATCH_SIZE = int(os.environ.get("CLASSIFICATION_BATCH_SIZE", "15"))
CLASSIFICATION_SCOPE = os.environ.get("CLASSIFICATION_SCOPE", "hybrid_review")


def load_existing_labels() -> dict[str, dict]:
    if not os.path.exists(LABELS_FILE):
        return {}

    with open(LABELS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return {str(item["id"]): item for item in data}

    if isinstance(data, dict):
        return {str(key): value for key, value in data.items()}

    raise ValueError(f"{LABELS_FILE} must contain a list or object of labels.")


def write_labels(labels_by_id: dict[str, dict]) -> None:
    os.makedirs(os.path.dirname(LABELS_FILE), exist_ok=True)
    labels = sorted(labels_by_id.values(), key=lambda item: int(item["id"]) if str(item["id"]).isdigit() else str(item["id"]))
    with open(LABELS_FILE, "w", encoding="utf-8") as f:
        json.dump(labels, f, indent=2, ensure_ascii=False)


def load_system_prompt() -> str:
    if not os.path.exists(PROMPT_FILE):
        raise FileNotFoundError(f"Missing prompt file: {PROMPT_FILE}")

    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    return (
        prompt
        + "\n\nReturn exactly one classification object for every input report ID. "
        + "Do not omit IDs and do not add IDs that are not in the batch."
    )


def main() -> int:
    print("Initializing Gemini client...")
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        return 1

    if not os.path.exists(CSV_FILE):
        print(f"ERROR: Source dataset '{CSV_FILE}' not found.", file=sys.stderr)
        return 1

    client = genai.Client()
    system_prompt = load_system_prompt()

    labels_by_id = load_existing_labels()
    print(f"Loaded {len(labels_by_id)} existing v2 labels from {LABELS_FILE}.")

    df = pd.read_csv(CSV_FILE)
    df["id"] = df["id"].astype(str)

    uncached_df = df[~df["id"].isin(labels_by_id.keys())].copy()
    if CLASSIFICATION_SCOPE == "hybrid_review":
        uncached_df = uncached_df[
            uncached_df.apply(
                lambda row: should_route_to_llm(
                    str(row.get("replacingText", "")) if pd.notna(row.get("replacingText", "")) else "",
                    int(row.get("categoryId", 0)),
                ),
                axis=1,
            )
        ].copy()
    elif CLASSIFICATION_SCOPE != "all":
        print(
            "ERROR: CLASSIFICATION_SCOPE must be 'hybrid_review' or 'all'.",
            file=sys.stderr,
        )
        return 1

    total_uncached = len(uncached_df)

    if total_uncached == 0:
        if CLASSIFICATION_SCOPE == "hybrid_review":
            print("No uncached hybrid review candidates require LLM classification.")
        else:
            print("All reports are already classified in labels_v2_silver.json.")
        return 0

    print(
        f"Found {total_uncached} unclassified reports in scope '{CLASSIFICATION_SCOPE}'. "
        f"Processing in batches of {BATCH_SIZE} using model '{MODEL_ID}'."
    )

    uncached_records = uncached_df.to_dict(orient="records")

    for i in range(0, total_uncached, BATCH_SIZE):
        batch = uncached_records[i : i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total_uncached + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")

        items_text = []
        expected_ids = {str(item["id"]) for item in batch}
        for item in batch:
            text = str(item.get("replacingText", "")).strip()
            category_name = str(item.get("categoryName", "")).strip()
            category_id = str(item.get("categoryId", "")).strip()
            items_text.append(
                "\n".join(
                    [
                        f"Report ID: {item['id']}",
                        f"Category ID: {category_id}",
                        f"Category: {category_name}",
                        f"Description: {text}",
                        "---",
                    ]
                )
            )

        user_prompt = "Classify the following batch of citizen reports:\n\n" + "\n".join(items_text)

        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=BatchCyclingClassificationV2,
                ),
            )

            result = json.loads(response.text)
            classifications = BatchCyclingClassificationV2.model_validate(result).classifications
            received_ids = {str(item.id) for item in classifications}
            missing_ids = expected_ids - received_ids
            extra_ids = received_ids - expected_ids

            if missing_ids or extra_ids:
                raise ValueError(
                    f"Batch ID mismatch. Missing: {sorted(missing_ids)}. Extra: {sorted(extra_ids)}."
                )

            for classification in classifications:
                labels_by_id[str(classification.id)] = classification.model_dump()

            write_labels(labels_by_id)
            print(f"  Processed batch {batch_num}. Saved {len(labels_by_id)} total v2 labels.")
        except Exception as exc:
            print(f"ERROR: Failed to process batch {batch_num}: {exc}", file=sys.stderr)
            print("Progress so far has been saved. Re-run the script to resume.", file=sys.stderr)
            return 1

    print(f"Classification complete. Wrote {len(labels_by_id)} labels to {LABELS_FILE}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
