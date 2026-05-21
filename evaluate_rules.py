import os
import json
import pandas as pd
from classification.rules import classify_report_rules

# Load files
CSV_FILE = "stadtverbesserer_snapshot.csv"
LABELS_FILE = "classification/labels/labels_v2_silver.json"

if not os.path.exists(CSV_FILE) or not os.path.exists(LABELS_FILE):
    print("Error: snapshot CSV or labels_v2_silver.json missing.")
    exit(1)

df = pd.read_csv(CSV_FILE)
df['id'] = df['id'].astype(str)

with open(LABELS_FILE, "r", encoding="utf-8") as f:
    raw_labels = json.load(f)

if isinstance(raw_labels, list):
    labels_v2 = {str(item["id"]): item for item in raw_labels}
elif isinstance(raw_labels, dict):
    labels_v2 = {str(key): value for key, value in raw_labels.items()}
else:
    raise ValueError("labels_v2_silver.json must contain a list or object.")

# Align data
records = []
for _, row in df.iterrows():
    rid = row['id']
    if rid in labels_v2:
        label = labels_v2[rid]
        records.append({
            "id": rid,
            "text": str(row['replacingText']) if pd.notna(row['replacingText']) else "",
            "categoryName": str(row['categoryName']),
            "categoryId": int(row['categoryId']),
            "llm_is_cycling": label["is_cycling_related"],
            "llm_subcategory": label["subcategory"],
            "llm_directness": label.get("directness", "unrelated"),
            "llm_explanation": label.get("reason_de") or label.get("explanation_de", "")
        })

print(f"Loaded {len(records)} reports aligned with labels_v2_silver.")

def classify_regex(text, category_id):
    decision = classify_report_rules(text, category_id)
    return (
        decision.is_regex_candidate,
        decision.matches["bike"],
        decision.matches["neg"],
        decision.matches["surface"] + decision.matches["hazard"],
        decision.route,
    )

# Evaluate
tp, fp, tn, fn = 0, 0, 0, 0
fp_cases = []
fn_cases = []
fn_subcats = {}
fn_directness = {}
routes = {}

for r in records:
    pred, m_pos, m_neg, m_haz, route = classify_regex(r["text"], r["categoryId"])
    actual = r["llm_is_cycling"]
    routes[route] = routes.get(route, 0) + 1
    
    info = {**r, "m_pos": m_pos, "m_neg": m_neg, "m_haz": m_haz, "route": route}
    
    if pred and actual:
        tp += 1
    elif pred and not actual:
        fp += 1
        fp_cases.append(info)
    elif not pred and actual:
        fn += 1
        fn_cases.append(info)
        subcat = r["llm_subcategory"]
        fn_subcats[subcat] = fn_subcats.get(subcat, 0) + 1
        directness = r["llm_directness"]
        fn_directness[directness] = fn_directness.get(directness, 0) + 1
    else:
        tn += 1

total = len(records)
accuracy = (tp + tn) / total
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print(f"\nEvaluation Results:")
print(f"  Accuracy : {accuracy:.2%} ({tp+tn}/{total})")
print(f"  Precision: {precision:.2%}")
print(f"  Recall   : {recall:.2%}")
print(f"  F1 Score : {f1:.2%}")
print(f"  True Positives  : {tp}")
print(f"  True Negatives  : {tn}")
print(f"  False Positives : {fp}")
print(f"  False Negatives : {fn}")

print("\n--- HYBRID ROUTE COUNTS ---")
for route, count in sorted(routes.items(), key=lambda x: x[1], reverse=True):
    print(f"  {route:<30}: {count:>3} ({count / total:.1%})")

print("\n--- FALSE NEGATIVES BY LLM SUBCATEGORY ---")
for subcat, count in sorted(fn_subcats.items(), key=lambda x: x[1], reverse=True):
    print(f"  {subcat:<30}: {count}")

print("\n--- FALSE NEGATIVES BY DIRECTNESS ---")
for directness, count in sorted(fn_directness.items(), key=lambda x: x[1], reverse=True):
    print(f"  {directness:<30}: {count}")

print("\n--- SAMPLE FALSE POSITIVES (Regex said YES, LLM said NO) ---")
for r in fp_cases[:8]:
    print(f"ID: {r['id']} | Cat: {r['categoryName']} ({r['categoryId']})")
    print(f"Directness: {r['llm_directness']} | Subcategory: {r['llm_subcategory']}")
    print(f"Text: {r['text'][:120]}")
    print(f"LLM Explanation: {r['llm_explanation']}")
    print(f"Route: {r['route']} | Matches: Pos={r['m_pos']} | Neg={r['m_neg']} | Haz={r['m_haz']}")
    print("-" * 50)

print("\n--- SAMPLE FALSE NEGATIVES (Regex said NO, LLM said YES) ---")
for r in fn_cases[:8]:
    print(f"ID: {r['id']} | Cat: {r['categoryName']} ({r['categoryId']})")
    print(f"Directness: {r['llm_directness']} | Subcategory: {r['llm_subcategory']}")
    print(f"Text: {r['text'][:120]}")
    print(f"LLM Explanation: {r['llm_explanation']}")
    print(f"Route: {r['route']} | Matches: Pos={r['m_pos']} | Neg={r['m_neg']} | Haz={r['m_haz']}")
    print("-" * 50)
