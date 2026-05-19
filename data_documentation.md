# Data Documentation: Stadtverbesserer Snapshot (CSV)

This document describes the structure, contents, and column schemas of the dataset saved in [stadtverbesserer_snapshot.csv](file:///Volumes/T7/projects/oldenburg-stadt/stadtverbesserer_snapshot.csv).

---

## 1. Snapshot Overview

*   **File Name:** `stadtverbesserer_snapshot.csv`
*   **Total Records:** 553 rows
*   **Total Columns:** 9 columns
*   **Export Date:** 19 May 2026
*   **Date Range Covered:** 01 January 2025 to 19 May 2026
*   **Primary Key:** `id` (Report ID)

The CSV contains a flattened snapshot of all citizen reports retrieved from the "Gemeinsam Oldenburg - Stadtverbesserer" portal. All nested structures (like geographical coordinates and categories) have been unpacked into distinct columns.

---

## 2. Column Schema

Below is the definition, data type, and details for each column in the CSV file:

| Column Name | Data Type | Nullable | Description | Example Value |
| :--- | :--- | :---: | :--- | :--- |
| **`id`** | `Integer` | No | Unique ticket identifier assigned by the platform. | `7156` |
| **`createdAt`** | `String` | No | Creation timestamp of the report in ISO-8601 format. | `2026-05-19T06:02:04.511+00:00` |
| **`state`** | `String` | No | Current workflow state of the report. <br>• `OPEN` (Offen / Neu)<br>• `IN_PROCESS` (In Bearbeitung)<br>• `CLOSED` (Gelöst)<br>• `NOT_RESPONSIBLE` (Nicht zuständig) | `IN_PROCESS` |
| **`categoryId`** | `Integer` | No | Numeric ID representing the category of the issue (e.g. `8` for trash). | `8` |
| **`categoryName`** | `String` | No | Human-readable category title (German, includes emoji icon). | `Wilde Müllkippe 🧹` |
| **`latitude`** | `Float` | Yes | Geolocation Latitude (WGS 84 coordinate system). | `53.164971` |
| **`longitude`** | `Float` | Yes | Geolocation Longitude (WGS 84 coordinate system). | `8.193112` |
| **`replacingText`** | `String` | Yes | Citizen's text description. Carriage returns and newlines have been replaced with spaces to ensure single-line CSV rows. | `"Sehr geehrte Damen und Herren..."` |
| **`firstPictureUrl`** | `String` | Yes | CDN URL of the primary image attached to the report. Blank if no image was uploaded. | `https://dialog-box-prod-bucket.s3.eu-central-1.amazonaws.com/...` |

---

## 3. Data Insights

### Status Frequency

*   **`IN_PROCESS`**: 322 reports (58.2%) — Active investigations or scheduled repairs.
*   **`NOT_RESPONSIBLE`**: 159 reports (28.8%) — Issues that fall outside the city's jurisdiction (e.g., private land, federal roads) or were rejected.
*   **`CLOSED`**: 59 reports (10.7%) — Successfully resolved and completed issues.
*   **`OPEN`**: 13 reports (2.4%) — Newly submitted reports awaiting triage.

### Top Categories

*   **Straßen  🚧**: 252 reports (45.6%)
*   **Wilde Müllkippe 🧹**: 170 reports (30.7%)
*   **Privates Grün an Straßen 🌲**: 35 reports (6.3%)
*   **Verkehrszeichen ⚠️**: 31 reports (5.6%)

---

## 4. Usage Recipes

Here are code snippets to load and inspect the dataset programmatically.

### Python (Standard CSV Library)
```python
import csv

csv_path = "stadtverbesserer_snapshot.csv"

with open(csv_path, mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 3:
            break
        print(f"Report #{row['id']}: [{row['categoryName']}] in state {row['state']}")
        print(f"  Coordinates: {row['latitude']}, {row['longitude']}")
        print(f"  Description: {row['replacingText'][:60]}...\n")
```

### Python (Pandas DataFrames)
```python
import pandas as pd

# Load dataset
df = pd.read_csv("stadtverbesserer_snapshot.csv")

# Parse timestamps
df['createdAt'] = pd.to_datetime(df['createdAt'])

# Filter for active trash reports
active_trash = df[(df['categoryName'].str.contains("Müll")) & (df['state'] == "IN_PROCESS")]

# Group by category and status
summary = df.groupby(['categoryName', 'state']).size().unstack(fill_value=0)
print(summary)
```

### R (tidyverse)
```R
library(tidyverse)

# Load and parse
df <- read_csv("stadtverbesserer_snapshot.csv") %>%
  mutate(createdAt = as.POSIXct(createdAt, format="%Y-%m-%dT%H:%M:%S"))

# Count reports by status
df %>%
  count(state, sort = TRUE)
```
