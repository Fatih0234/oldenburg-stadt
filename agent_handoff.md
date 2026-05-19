# 🤖 AI Agent Handoff: Oldenburg Rad-Verbesserer Analyzer

Welcome, agent! This document serves as a complete transfer of context, architectural decisions, mathematical coordinate projection rules, and next-step guides for the Oldenburg Rad-Verbesserer project.

---

## 🎯 Project Vision
The **Rad-Verbesserer** dashboard aims to extract actionable insights from public citizen infrastructure reports (the `gemeinsam.oldenburg.de` platform) and highlight reports that negatively impact cycling infrastructure. By filtering out general vehicle-specific complaints and highlighting high-confidence cycling issues, local advocacy groups (e.g., ADFC) can create high-impact weekly newsletters and social media packs.

---

## 🛠️ Codebase Architecture

The project consists of a Python processing backend and a static, zero-CORS dark mode HTML/CSS/JS frontend dashboard:

```
oldenburg-stadt/
├── README.md                     # General project documentation
├── agent_handoff.md              # This handoff file
├── download_osm_bike.py          # Queries Overpass API for local bike network GeoJSON
├── score_reports.py              # Spatial mapping, metric projection, scoring engine
├── generate_data_js.py           # Packs compiled databases into data.js
├── data.js                       # Frontend static data store (avoids local CORS issues)
├── index.html                    # Dashboard main UI structure
├── style.css                     # Premium styling, animations, responsive design rules
└── app.js                        # Leaflet map logic, custom pins, UI filters, markdown generator
```

### 1. Spatial Geometry & Metric Projections (`pyproj`)
**CRITICAL**: Standard GPS coordinates (WGS84, `EPSG:4326`) express positions in angular degrees. Distance calculations in degrees are inaccurate.
* In [score_reports.py](file:///Volumes/T7/projects/oldenburg-stadt/score_reports.py), we project all coordinates into **UTM Zone 32N (`EPSG:32632`)** representing Germany.
* Under `EPSG:32632`, all coordinate pairs are represented as metric Cartesian coordinates (X, Y in meters), which allows the `shapely` geometry library to perform precise nearest-point calculations in meters.

### 2. Proximity Matching & The Scoring Formula
We compute a cycling confidence score ($0$ to $100+$) for each report using a multi-factor formula defined in [score_reports.py](file:///Volumes/T7/projects/oldenburg-stadt/score_reports.py):

$$\text{Score} = \text{KeywordMatch} + \text{ProximityScore} + \text{CategoryScore} + \text{CorridorBonus} + \text{StatusAgeAdjustment}$$

*   **Keyword Match (+50):** Description matches German cycling keywords (e.g., *Radweg*, *Fahrrad*, *Radspur*, *Lastenrad*).
*   **Proximity to OSM Bike Network:**
    *   $\le 10\text{m}$: **+35 pts**
    *   $\le 25\text{m}$: **+20 pts**
    *   $\le 50\text{m}$: **+10 pts**
*   **Category Relevance:**
    *   *Fundräder* (Abandoned bikes): **+50 pts** (almost 100% cycling-relevant)
    *   *Roads, Signs, Lights, Overhanging foliage*: **+15 pts** (often impacts safety/visibility)
    *   *Trees/Branches*: **+10 pts**
*   **ADFC/City Priority Corridor Bonus (+20):** If within 50m of an official priority bicycle corridor (such as *FAST FLIN*, *Green Wave*, *Pophankenweg*, *Ammerländer Heerstraße*).
*   **Ticket Status & Age Adjustments:**
    *   Open/Active: **+10 pts**
    *   Closed/Fixed: **-20 pts**
    *   Not Responsible/External: **-15 pts**
    *   Older than 180 days: **-10 pts**

### 3. Frontend Data Binding (`data.js`)
To allow the dashboard to run out-of-the-box by double-clicking `index.html` (under `file://` protocols), we do not make dynamic HTTP `fetch()` requests to JSON databases. This bypasses the browser's local Cross-Origin Resource Sharing (CORS) sandbox block.
*   [generate_data_js.py](file:///Volumes/T7/projects/oldenburg-stadt/generate_data_js.py) translates our processed data models into a single JavaScript file ([data.js](file:///Volumes/T7/projects/oldenburg-stadt/data.js)) containing:
    *   `CLASSIFIED_REPORTS`: Array of the 553 classified citizen tickets.
    *   `BIKE_NETWORK_GEOJSON`: GeoJSON structure of local OSM cycleways.

---

## 🎨 Design System & Audit Upgrades

We completed a comprehensive UI/UX audit to polish the design and make it production-ready. Ensure any future frontend modifications adhere to these system components:

1.  **Typography**: Outfit (headings, `font-family: var(--font-heading)`) paired with Inter (body copy, `font-family: var(--font-body)`) loaded from Google Fonts.
2.  **Color System**: Curated dark theme (`#0b0f19`) featuring:
    *   `--accent-emerald: #10b981` / `--accent-cyan: #06b6d4`
    *   Confidence Tiers: Confirmed (`#ef4444`), Likely (`#f97316`), Possible (`#facc15`), Other (`#869ab0`).
3.  **Custom Div Markers**: We do not use standard circle markers. We use custom `L.divIcon` HTML pins (`.marker-pin` in [style.css](file:///Volumes/T7/projects/oldenburg-stadt/style.css)) which feature pulsing glows and hover zoom scales.
4.  **Deterministic Block Markdown Preview**: A line-by-line parser in [app.js](file:///Volumes/T7/projects/oldenburg-stadt/app.js) correctly parses Markdown lists (`*`), headings (`#`, `##`), and line breaks into standard HTML elements without greedily wrapping the entire page in `<ul>` elements.
5.  **Active Card Highlighting**: Clicking the metric cards toggles the `.active` class, applying a glowing cyan border that indicates which filter is selected.
6.  **Responsive Layout**: The sidebar scroll list `.issue-list` utilizes a dynamic height `calc(100vh - 365px)` to fit perfectly on all desktop and laptop screen layouts.
7.  **Modern Clipboard API**: Text copying is handled asynchronously via `navigator.clipboard.writeText` with an automatic fallback mechanism utilizing `document.execCommand`.

---

## 🔮 Roadmap & Potential Future Tasks

If the user requests additional features or improvements, here are recommended implementation paths:

### 1. Interactive Classification Threshold Sliders
*   **Goal**: Allow users to adjust scoring thresholds directly from the dashboard.
*   **Implementation**: Add slider elements to the sidebar. In `app.js`, dynamically re-classify and filter `CLASSIFIED_REPORTS` when sliders are dragged, updating the map markers and cards in real-time.

### 2. Live Overpass Queries in Python
*   **Goal**: Ensure data is completely up to date with OSM.
*   **Implementation**: Enhance `download_osm_bike.py` to optionally pull the latest Overpass elements programmatically without hardcoded mirror links if they fail.

### 3. Drag-and-Drop Newsletter Layouts
*   **Goal**: Allow editing the order of newsletter reports before copying.
*   **Implementation**: Use HTML5 Drag & Drop API on the issue items within the newsletter preview panel to let users reorder reports, then regenerate the Markdown representation in real-time.

### 4. Interactive Report Submissions (Mapping Mode)
*   **Goal**: Allow manual creation of reports directly on the map.
*   **Implementation**: Add a "Draw Marker" toggle using Leaflet's drawing tools. Users can drop a pin, fill out a small card, and append it to the locally stored list.

Good luck coding, agent! Feel free to build upon this robust foundation.
