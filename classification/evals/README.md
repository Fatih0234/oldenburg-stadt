# Classification Evals

This directory is for diagnostic scripts and generated evaluation outputs.

Recommended future files:

- `evaluate_rules_v2.py`: compares rule predictions to `labels_v2_silver` and optional gold labels.
- `split_labels.py`: creates deterministic dev and holdout splits.
- `metrics_v2.json`: machine-readable metrics from the latest evaluation run.
- `disagreement_cases.csv`: review queue containing false positives, false negatives, low-confidence labels, and classifier disagreements.

Evaluation should report metrics by:

- full dataset;
- dev split;
- holdout split;
- `categoryId`;
- `subcategory`;
- `directness`.
