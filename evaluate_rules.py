import os
import json
import re
import pandas as pd

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
            return False, [], [], []
        else:
            return True, ['category_7_bike'], [], []
            
    # Find matching items for debugging
    matched_pos = [pat for pat in BIKE_KEYWORDS if re.search(pat, text_lower)]
    matched_neg = [pat for pat in NEG_KEYWORDS if re.search(pat, text_lower)]
    matched_hazard = [pat for pat in HAZARD_KEYWORDS if re.search(pat, text_lower)]
    
    has_pos = len(matched_pos) > 0
    has_neg = len(matched_neg) > 0
    has_hazard = len(matched_hazard) > 0
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
                
    return result, matched_pos, matched_neg, matched_hazard

# Evaluate
tp, fp, tn, fn = 0, 0, 0, 0
fp_cases = []
fn_cases = []
fn_subcats = {}
fn_directness = {}

for r in records:
    pred, m_pos, m_neg, m_haz = classify_regex(r["text"], r["categoryId"])
    actual = r["llm_is_cycling"]
    
    info = {**r, "m_pos": m_pos, "m_neg": m_neg, "m_haz": m_haz}
    
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
    print(f"Matches: Pos={r['m_pos']} | Neg={r['m_neg']} | Haz={r['m_haz']}")
    print("-" * 50)

print("\n--- SAMPLE FALSE NEGATIVES (Regex said NO, LLM said YES) ---")
for r in fn_cases[:8]:
    print(f"ID: {r['id']} | Cat: {r['categoryName']} ({r['categoryId']})")
    print(f"Directness: {r['llm_directness']} | Subcategory: {r['llm_subcategory']}")
    print(f"Text: {r['text'][:120]}")
    print(f"LLM Explanation: {r['llm_explanation']}")
    print(f"Matches: Pos={r['m_pos']} | Neg={r['m_neg']} | Haz={r['m_haz']}")
    print("-" * 50)
