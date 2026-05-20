import os
import json
import re
import pandas as pd

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

records = []
for _, row in df.iterrows():
    rid = row['id']
    if rid in labels_v2:
        records.append({
            "id": rid,
            "text": str(row['replacingText']) if pd.notna(row['replacingText']) else "",
            "categoryId": int(row['categoryId']),
            "llm_is_cycling": labels_v2[rid]["is_cycling_related"],
            "llm_directness": labels_v2[rid].get("directness", "unrelated")
        })

# Define starting sets
BIKE_KEYWORDS = [
    r'radweg\w*', r'fahrradweg\w*', r'radfahrer\w*', r'radfahren\w*', r'radfahrende\w*',
    r'fahrrad\w*', r'radspur\w*', r'fahrradstraße\w*', r'radler\w*', r'radpiste\w*',
    r'veloweg\w*', r'radüberweg\w*', r'lastenrad\w*', r'fahrradständer\w*', r'radschutzstreifen\w*',
    r'schutzstreifen\w*', r'radroute\w*', r'fahrradroute\w*', r'radverkehr\w*', r'anlehnbügel\w*',
    r'fahrradbügel\w*', r'radler\w*', r'rad-?\s*und\s*-?gehweg\w*', r'geh-?\s*und\s*-?radweg\w*',
    r'rad/gehweg\w*', r'fahrrads\w*', r'fahrräder\w*', r'schulweg\w*', r'schüler\w*', 
    r'\brad\b', r'\bräder\b', r'\bbike\b', r'\bbikes\b', r'\bkinder\b', r'\bkind\w*'
]

NEG_KEYWORDS = [
    r'\bspielplatz\w*', r'\bspielgerät\w*', r'\bschaukel\w*', r'\brutsche\w*', r'\bsandkiste\w*',
    r'\bkleidercontainer\w*', r'\btextilcontainer\w*', r'\baltkleider\w*', r'\bsperrmüll\w*',
    r'\bhausmüll\w*', r'\bkatze\w*', r'\bkatzen\w*', r'\bhundekot\w*', r'\bhundehaufen\w*',
    r'\bhund\b', r'\bhunde\b',
    r'\bwilder müll\w*', r'\bmülltonne\w*', r'\bgelber sack\w*', r'\bgelbe säcke\w*',
    r'\bplakat\w*', r'\bgraffiti\w*', r'\baufkleber\w*', r'\bschulhof\w*', r'\bparkanlage\w*',
    r'\bglascontainer\w*', r'\baltglascontainer\w*', r'\bautofahrer\w*', r'\bvandalismus\w*',
    r'\babfluss\w*', r'\bwasserzug\w*', r'\bgraben\b', r'\bgully\w*', r'\bböschung\w*', r'\bwaldstück\w*',
    r'\bwohnwagen\w*', r'\bmercedes\w*', r'\baudi\b', r'\bpkw\b', r'\bauto\b'
]

HAZARD_KEYWORDS = [
    r'schlagloch\w*', r'schlaglöcher\w*', r'loch\b', r'löcher\b', r'uneben\w*', r'abgesackt\w*',
    r'absackung\w*', r'absackungen\w*', r'kante\w*', r'absatz\w*', r'wurzel\w*', r'baumwurzel\w*',
    r'bodenwelle\w*', r'pflasterstein\w*', r'pflastersteine\w*', r'kopfsteinpflaster\w*',
    r'risse\w*', r'riss\b', r'asphalt\w*', r'fahrbahn\w*',
    r'scherben\w*', r'glasscherben\w*', r'glas\b', r'hecke\w*', r'sträucher\w*',
    r'äste\b', r'zweige\b', r'überhang\w*', r'überhängend\w*', r'bewuchs\w*', r'zugewachsen\w*',
    r'zuparken\w*', r'zugeparkt\w*', r'blockiert\w*', r'versperrt\w*', r'hindernis\w*',
    r'poller\w*', r'pfosten\w*', r'sperrpfosten\w*', r'kuhle\w*',
    r'ampel\w*', r'ampelschaltung\w*', r'induktionsschleife\w*', r'sensor\w*',
    r'schild\w*', r'beschilderung\w*', r'wegweiser\w*',
    r'sturzgefahr\w*', r'rutschgefahr\w*', r'unfallgefahr\w*', r'gefahrenstelle\w*',
    r'marode\w*', r'schade[n]?\b', r'beschädigt\w*', r'begehbar\w*', r'passierbar\w*', r'befahrbar\w*'
]

# We can also test candidate positive keywords to expand BIKE_KEYWORDS
CANDIDATE_POS = [
    r'fahrradfahrer\w*', r'lastenräder\w*', r'stellplatz\w*', r'stellplätze\w*', r'radstreifen\w*',
    r'überqueren\w*', r'querung\w*', r'einmündung\w*', r'kreuzung\w*', r'hindurch\w*', r'ampelanlage\w*',
    r'ohne kennzeichen\w*', r'abgemeldet\w*', r'nicht angemeldet\w*'
]

CANDIDATE_NEG = [
    r'parkbucht\w*', r'parkplatz\w*', r'parkstreifen\w*', r'müllwagen\w*', r'müllfahrzeug\w*',
    r'tüv\w*', r'abgemeldeter\w*', r'abgemeldetes\w*', r'wohnmobil\w*', r'anhänger\w*'
]

def evaluate(pos_list, neg_list, haz_list):
    pos_re = re.compile('|'.join(pos_list), re.IGNORECASE) if pos_list else None
    neg_re = re.compile('|'.join(neg_list), re.IGNORECASE) if neg_list else None
    haz_re = re.compile('|'.join(haz_list), re.IGNORECASE) if haz_list else None
    
    tp, tn, fp, fn = 0, 0, 0, 0
    for r in records:
        text_lower = r["text"].lower()
        has_pos = bool(pos_re.search(text_lower)) if pos_re else False
        has_neg = bool(neg_re.search(text_lower)) if neg_re else False
        has_haz = bool(haz_re.search(text_lower)) if haz_re else False
        
        pred = False
        if r["categoryId"] == 7:
            garbage_keywords = [r'müll', r'möbel', r'abfall', r'sperrmüll', r'schrott', r'entsorgt', r'reifen', r'mülltonne']
            has_garbage = any(re.search(pat, text_lower) for pat in garbage_keywords)
            if has_garbage and not any(x in text_lower for x in ['rad', 'fahrrad', 'bike']):
                pred = False
            else:
                pred = True
        elif has_pos:
            # Negation overrides
            allowed_overrides = [r'radweg\w*', r'fahrradweg\w*', r'radspur\w*', r'fahrradstraße\w*', r'schulweg\w*', r'schüler\w*', r'\brad\b', r'\bräder\b']
            has_override = any(re.search(pat, text_lower) for pat in allowed_overrides)
            if has_neg and not has_override:
                pred = False
            else:
                pred = True
        elif has_haz:
            is_infra_hazard = any(re.search(pat, text_lower) for pat in [r'ampel\w*', r'schild\w*', r'beschilderung\w*'])
            if r["categoryId"] in [3, 4, 6, 10, 11] and (not has_neg or is_infra_hazard):
                avoid_terms = [r'spielplatz', r'wohngebiet']
                if any(re.search(pat, text_lower) for pat in avoid_terms):
                    pred = False
                else:
                    pred = True
                    
        actual = r["llm_is_cycling"]
        if pred and actual:
            tp += 1
        elif pred and not actual:
            fp += 1
        elif not pred and actual:
            fn += 1
        else:
            tn += 1
            
    acc = (tp + tn) / len(records)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
    return acc, f1, tp, tn, fp, fn

base_acc, base_f1, tp, tn, fp, fn = evaluate(BIKE_KEYWORDS, NEG_KEYWORDS, HAZARD_KEYWORDS)
print(f"Base Configuration:")
print(f"  Accuracy : {base_acc:.2%}")
print(f"  F1 Score : {base_f1:.2%}")
print(f"  TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")

# Greedy search on candidates
best_pos = list(BIKE_KEYWORDS)
best_neg = list(NEG_KEYWORDS)
current_acc = base_acc
current_f1 = base_f1

print("\n--- Optimizing BIKE_KEYWORDS ---")
for cand in CANDIDATE_POS:
    test_pos = best_pos + [cand]
    acc, f1, tp, tn, fp, fn = evaluate(test_pos, best_neg, HAZARD_KEYWORDS)
    # We want to optimize primarily F1 score and accuracy
    if f1 > current_f1 or (f1 == current_f1 and acc > current_acc):
        print(f"  Added positive pattern '{cand}' -> F1: {f1:.2%} (Acc: {acc:.2%})")
        best_pos.append(cand)
        current_acc = acc
        current_f1 = f1

print("\n--- Optimizing NEG_KEYWORDS ---")
for cand in CANDIDATE_NEG:
    test_neg = best_neg + [cand]
    acc, f1, tp, tn, fp, fn = evaluate(best_pos, test_neg, HAZARD_KEYWORDS)
    if f1 > current_f1 or (f1 == current_f1 and acc > current_acc):
        print(f"  Added negative pattern '{cand}' -> F1: {f1:.2%} (Acc: {acc:.2%})")
        best_neg.append(cand)
        current_acc = acc
        current_f1 = f1

# Report final
acc, f1, tp, tn, fp, fn = evaluate(best_pos, best_neg, HAZARD_KEYWORDS)
print(f"\nFinal Configuration:")
print(f"  Accuracy : {acc:.2%}")
print(f"  F1 Score : {f1:.2%}")
print(f"  TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")
print(f"Optimized BIKE_KEYWORDS: {best_pos}")
print(f"Optimized NEG_KEYWORDS: {best_neg}")
