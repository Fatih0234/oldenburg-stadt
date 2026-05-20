# Classification Methodology

This project classifies Oldenburg citizen reports by how strongly they relate to cycling infrastructure, cycling safety, and bicycle parking.

## Label Quality Hierarchy

Use this hierarchy when discussing labels:

1. Human-reviewed gold labels.
2. Stronger LLM silver labels.
3. Previous LLM labels.
4. Rule-based regex labels.

Do not call any LLM output ground truth by default. The stronger LLM output is `labels_v2_silver` until reviewed.

## Current Production Pipeline

The production pipeline currently uses:

- `classify_reports_llm.py` to create cached LLM classifications.
- `score_reports.py` to combine LLM or regex classification with OSM bike-network distance and metadata.
- `evaluate_rules.py` to compare regex rules against the cached LLM labels.
- `optimize_regex.py` to explore keyword changes.
- `generate_data_js.py` to compile dashboard data.

The final dashboard label is not only a text classifier output. It is a score that combines:

- cycling-related classifier match;
- confidence penalty for confident non-cycling labels;
- distance to mapped OSM bike infrastructure;
- report category relevance;
- priority corridor bonus;
- report state;
- report age.

## V2 Labeling Objective

`labels_v2` should separate semantic cycling relevance from spatial proximity. The key additional field is `directness`.

Recommended interpretation:

- `direct`: use for explicit cycling infrastructure, bike parking, bicycle streets, cycleways, bike lanes, shared paths, bicycle signals, or hazards clearly on cycling space.
- `indirect`: use for general infrastructure that materially affects cyclists, such as unsafe crossings, visibility, traffic signals, or road defects on likely cycling routes.
- `nearby_only`: use when the text is not cycling-specific and only proximity to a bike route suggests possible relevance.
- `unrelated`: use when no meaningful cycling impact is evident.

## Why Directness Matters

The old binary label mixes several different concepts:

- direct bike-lane or cycleway issues;
- general road defects that cyclists may encounter;
- sidewalk complaints where bicycle access is unclear;
- general urban maintenance reports near cycling routes;
- unrelated reports located close to bicycle infrastructure.

This creates false positives in the dashboard and makes regex optimization brittle. V2 labels should make these cases explicit.

## Evaluation Principle

Optimize explainable rules against `labels_v2_silver`, but validate on a held-out split and inspect disagreements. A rule change is acceptable only when it improves validation metrics or clearly improves maintainability without metric regression.

Key metrics:

- accuracy;
- precision;
- recall;
- F1;
- false-positive count;
- false-negative count;
- metrics by `categoryId`;
- metrics by `subcategory`;
- metrics by `directness`.

## Human Review Policy

Human review is required for:

- low-confidence LLM labels;
- disagreements between old LLM, new LLM, and regex;
- `nearby_only` labels that may influence dashboard scoring;
- ambiguous sidewalk, road-defect, parked-car, and abandoned-object cases;
- high-impact dashboard cases that would appear as confirmed or likely cycling issues.

Reviewed cases should be stored separately as `classification/labels/labels_gold_reviewed.json` or equivalent, not mixed into the silver label file without provenance.
