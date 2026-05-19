# API Documentation: Stadt Oldenburg - Stadtverbesserer

This document details the specifications and behavior of the REST API driving the **"Stadtverbesserer" (Mängelmelder)** portal on `gemeinsam.oldenburg.de`.

---

## 1. API Specifications

The frontend of the platform connects to a public, unauthenticated backend REST service to query reported issues.

*   **Endpoint URL:** `https://gemeinsam.oldenburg.de/backend/v1/flaw-reporter/findPageableReportsWithFilter`
*   **HTTP Method:** `GET`
*   **Authentication:** None (Public Access)
*   **Content-Type:** `application/json`

---

## 2. Request Parameters

The endpoint accepts query parameters to filter, paginate, and sort reports. 

> [!WARNING]
> The parameters `flawReporterId`, `limit`, and `offset` are **strictly required**. Omitting any of these will result in an HTTP `400 Bad Request` error.

| Parameter | Data Type | Required? | Description & Allowed Values |
| :--- | :--- | :--- | :--- |
| `flawReporterId` | `Integer` | **Yes** | The module identifier. For the Stadtverbesserer service, this value must always be `24`. |
| `limit` | `Integer` | **Yes** | Page size (maximum number of records to retrieve per request, e.g. `10` or `100`). |
| `offset` | `Integer` | **Yes** | Zero-indexed offset for pagination (e.g. `0` for page 1, `100` for page 2). |
| `searchText` | `String` | No | Full-text query string to filter reports containing specific terms (e.g. `"Schlagloch"`, `"Sperrmüll"`). Case-insensitive. |
| `filteredStates` | `String` / `Array` | No | Filters by report status. Can be passed multiple times (e.g., `?filteredStates=CLOSED&filteredStates=IN_PROCESS`). <br>• Valid values: `OPEN`, `IN_PROCESS`, `CLOSED`, `NOT_RESPONSIBLE` |
| `filteredCategories`| `Integer`/ `Array` | No | Filters by category IDs. Can be passed multiple times for multiple categories (e.g., `?filteredCategories=8&filteredCategories=3`). |
| `sortParam` | `String` | No | Field to sort by. Supported keys:<br>• `"createdAt"`: Sort by report timestamp.<br>• `"id"`: Sort by report ID. |
| `ascending` | `Boolean` | No | Sort direction:<br>• `true`: Oldest first (ascending).<br>• `false`: Newest first (descending). |

---

## 3. Categories Reference (`filteredCategories`)

The portal organizes tickets into specific issue categories. Below are the integer identifiers corresponding to each category name:

| Category ID | Category Name (German) | Description |
| :---: | :--- | :--- |
| **`3`** | Straßen 🚧 | Potholes, damaged pavement, sidewalks, cycle paths. |
| **`4`** | Verkehrszeichen ⚠️ | Damaged, missing, or obscured traffic signs. |
| **`5`** | Straßenbeleuchtung 💡 | Defective street lights or dark areas. |
| **`6`** | Ampel 🚦 | Malfunctioning traffic lights. |
| **`7`** | Fundräder ⚡️🚲 | Abandoned bicycles or e-bikes in public areas. |
| **`8`** | Wilde Müllkippe 🧹 | Illegal dumping of garbage or trash bags. |
| **`9`** | Spielplätze 🧸 | Damaged playground equipment or unsafe areas. |
| **`10`** | Privates Grün an Straßen 🌲 | Encroaching hedges/branches from private property onto sidewalks. |
| **`11`** | Öffentliches Grün, Parkanlagen 🌲| Damaged park benches, overgrown public grass, fallen branches. |
| **`12`** | Danke sagen 🙏 | Positive citizen feedback. |
| **`13`** | Idee einreichen 💭 | General suggestions/ideas for city improvement. |

---

## 4. Response Schema

A successful request (`200 OK`) returns a JSON object containing two main fields:
1.  `totalCnt` (`Integer`): The total number of reports matching your filters on the server.
2.  `reports` (`Array`): A list of report objects matching the requested page.

### Report Object Fields

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `id` | `Integer` | Unique identifier for the report. |
| `createdAt` | `String` | Creation timestamp in ISO-8601 format with millisecond precision and timezone offset. |
| `replacingText` | `String` | Detailed description text submitted by the citizen. |
| `state` | `String` | Workflow state: `OPEN` (Offen), `IN_PROCESS` (In Bearbeitung), `CLOSED` (Abgeschlossen), `NOT_RESPONSIBLE` (Nicht zuständig). |
| `category` | `Object` | Nested category object (`id`, `categoryName`, `createdAt`). |
| `coordinate` | `Object` | Nested location coordinate (`latitude`, `longitude`). |
| `pictures` | `Array` | List of picture objects, each containing an S3 CDN link (`fileCDNUrl`), `id`, `filename`, and metadata. |

### Sample API Response Payload
```json
{
  "totalCnt": 553,
  "reports": [
    {
      "id": 7156,
      "createdAt": "2026-05-19T06:02:04.511+00:00",
      "replacingText": "Sehr geehrte Damen und Herren, hier wurde eine wilde Müllkippe...",
      "state": "NOT_RESPONSIBLE",
      "category": {
        "id": 8,
        "categoryName": "Wilde Müllkippe 🧹",
        "createdAt": "2025-05-09T07:39:41.807+00:00"
      },
      "coordinate": {
        "latitude": 53.164971,
        "longitude": 8.193112
      },
      "flawReporter": {
        "id": 24,
        "createdAt": "2025-04-14T11:12:52.264+00:00"
      },
      "pictures": [
        {
          "id": 3975,
          "filename": "1a97c8f5-28ec-4318-a8cd-27842b67c03e_1779170524515_flaw_reporter_report_picture.png",
          "fileCDNUrl": "https://dialog-box-prod-bucket.s3.eu-central-1.amazonaws.com/images/oldenburg/1a97c8f5-28ec-4318-a8cd-27842b67c03e_1779170524515_flaw_reporter_report_picture.png",
          "published": true,
          "createdAt": "2026-05-19T06:02:05.791+00:00"
        }
      ]
    }
  ]
}
```

---

## 5. Integration Best Practices

*   **Rate Limiting:** Although no API key is needed, avoid hammering the endpoint. Introduce a throttle delay of at least `0.5` seconds between requests when iterating through pages.
*   **JSON Parsing:** Check if nested keys like `pictures` are empty lists before fetching index `0`.
*   **Pagination Loops:** Programmatic loops should check if the length of accumulated reports equals `totalCnt` to safely terminate.
