# Classification Labels

This directory stores versioned label sets.

Recommended files:

- `labels_v1_gemini.json`: previous LLM labels, if exported from `llm_classification_cache.json`.
- `labels_v2_silver.json`: stronger structured LLM labels using `classification/schemas/labels_v2.schema.json`.
- `labels_gold_reviewed.json`: human-reviewed labels for ambiguous and high-impact cases.

Do not treat silver labels as ground truth. Use them as a stronger reference set for rule improvement and disagreement discovery.
