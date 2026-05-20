# Human Review Guide

Human review converts uncertain silver labels into defensible gold labels.

## Review Inputs

Each reviewed case should include:

- report ID;
- original German report text;
- category ID and category name;
- coordinates when available;
- old LLM label;
- `labels_v2_silver` label;
- regex label;
- score and dashboard label if already scored;
- reason for review.

## Review Decision Fields

Use the same core fields as `labels_v2`:

- `id`;
- `is_cycling_related`;
- `directness`;
- `subcategory`;
- `confidence`;
- `needs_human_review`;
- `reason_de`.

For reviewed labels, set `needs_human_review` to false unless the case remains unresolved.

## Review Criteria

Mark as cycling-related when the report clearly affects:

- a cycleway, bike lane, bicycle street, bike route, or shared bike/foot path;
- bicycle parking;
- a crossing or signal used by cyclists;
- cyclist safety, visibility, or passability;
- an obstruction or hazard on cycling space.

Mark as unrelated when:

- the issue is a general car-lane or parking-space complaint with no cycling impact;
- the issue is a general sidewalk complaint where bicycle use is not indicated;
- the report is about trash, graffiti, playgrounds, parks, pets, or private property without cycling impact;
- the only signal is that the report is geographically near a bike route.

Use `nearby_only` when:

- the text is not cycling-specific;
- the case may still matter for dashboard prioritization because it is close to mapped cycling infrastructure;
- map inspection is needed before operational use.

## Priority Cases To Review

Review these first:

- all low-confidence labels below 0.75;
- all old-LLM vs new-LLM disagreements;
- all regex vs `labels_v2_silver` disagreements;
- all `nearby_only` labels;
- all reports that become `Confirmed cycling issue` in dashboard scoring;
- ambiguous parked-car, abandoned-car, sidewalk, and road-defect cases.

## Storage

Store human-reviewed output separately from silver labels:

```text
classification/labels/labels_gold_reviewed.json
```

Do not silently overwrite `labels_v2_silver.json`. If gold labels supersede silver labels in evaluation, document that provenance in the evaluation output.
