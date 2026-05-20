# Goal Context: Improve Cycling Classification Rules

This document is context for a future Codex `/goal` session. It defines the intended objective, boundaries, verification surface, and stop conditions.

## Recommended Goal

```text
/goal Improve the explainable rule-based cycling classifier against labels_v2_silver while preserving the dashboard output schema. Use only score_reports.py, evaluate_rules.py or evaluate_rules_v2.py, optimize_regex.py, and diagnostic files under classification/. Target at least 90% F1 and 90% recall on the holdout set, not just the dev set. Keep rules maintainable: prefer category/directness-aware rules over broad keyword additions. After each iteration, run the evaluation, report confusion-matrix changes, inspect the largest false-positive and false-negative clusters, and only keep changes that improve holdout performance or clearly improve maintainability without metric regression. If the target cannot be reached with maintainable rules, stop and produce a report explaining remaining error patterns and recommend whether to use a hybrid LLM/rule fallback.
```

## Outcome

The rule-based classifier should become a maintainable, explainable fallback that agrees well with `labels_v2_silver` and performs acceptably on a held-out validation split.

The goal is not to blindly maximize agreement with an LLM. The goal is to improve explainable classification while identifying cases that need human-reviewed gold labels.

## Verification Surface

The goal session should use:

- deterministic dev and holdout splits;
- metrics against `labels_v2_silver`;
- confusion matrices before and after each change;
- disagreement reports;
- false-positive and false-negative cluster summaries;
- final dashboard schema compatibility checks.

Required metrics:

- accuracy;
- precision;
- recall;
- F1;
- true positives;
- true negatives;
- false positives;
- false negatives;
- metrics by `categoryId`;
- metrics by `subcategory`;
- metrics by `directness`.

## Constraints

- Preserve the current dashboard output schema in `classified_reports.json` and `data.js`.
- Keep rule changes explainable.
- Avoid broad keyword additions that improve dev metrics but create obvious false positives.
- Do not treat `labels_v2_silver` as perfect truth.
- Do not overwrite gold labels with LLM output.
- Do not make UI changes during classifier optimization unless explicitly requested.
- Do not rotate or remove existing production artifacts unless explicitly requested.

## Suggested Iteration Policy

1. Establish baseline metrics on dev and holdout.
2. Inspect false-negative clusters.
3. Improve one cluster at a time.
4. Run evaluation after each rule change.
5. Revert or adjust any change that improves dev but worsens holdout without a defensible reason.
6. Inspect false-positive clusters after recall improvements.
7. Stop when target metrics are reached or when further changes become unmaintainable.

## Stop Conditions

Stop and report if:

- holdout F1 and recall cannot both reach 90% with maintainable rules;
- remaining errors require map inspection or human judgment;
- LLM silver labels appear internally inconsistent;
- rule complexity becomes difficult to explain;
- production schema compatibility would be broken.

## Expected Final Output

The goal session should end with:

- changed files list;
- baseline and final metrics;
- confusion-matrix delta;
- strongest remaining false-positive clusters;
- strongest remaining false-negative clusters;
- recommendation for human review or hybrid fallback;
- confirmation that dashboard output schema remains compatible.
