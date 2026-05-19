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
├── classify_reports_llm.py       # Queries Gemini for Pydantic structured classifications
├── score_reports.py              # Spatial mapping, metric projection, scoring engine (LLM & regex fallback)
├── evaluate_rules.py             # Computes Accuracy, F1, Precision, and Recall for regex heuristic
├── optimize_regex.py             # Runs greedy keyword pattern searches to optimize rules
├── llm_classification_cache.json # Cached LLM output mapping report ID to classification details
├── generate_data_js.py           # Packs compiled databases into data.js
├── data.js                       # Frontend static data store (avoids local CORS issues)
├── index.html                    # Dashboard main UI structure
├── style.css                     # Premium styling, animations, responsive design rules
└── app.js                        # Leaflet map logic, custom pins, UI filters, newsletter generator
```

### 1. Spatial Geometry & Metric Projections (`pyproj`)
**CRITICAL**: Standard GPS coordinates (WGS84, `EPSG:4326`) express positions in angular degrees. Distance calculations in degrees are inaccurate.
* In [score_reports.py](file:///Volumes/T7/projects/oldenburg-stadt/score_reports.py), we project all coordinates into **UTM Zone 32N (`EPSG:32632`)** representing Germany.
* Under `EPSG:32632`, all coordinate pairs are represented as metric Cartesian coordinates (X, Y in meters), which allows the `shapely` geometry library to perform precise nearest-point calculations in meters.

### 2. Proximity Matching & The Scoring Formula
We compute a cycling confidence score ($0$ to $100+$) for each report using a multi-factor formula defined in [score_reports.py](file:///Volumes/T7/projects/oldenburg-stadt/score_reports.py):

$$\text{Score} = \text{LLMMatch} + \text{LLMPenalty} + \text{ProximityScore} + \text{CategoryScore} + \text{CorridorBonus} + \text{StatusAgeAdjustment}$$

*   **LLM Match (+50):** Description is classified as cycling-related by the LLM (or falls back to the optimized regex heuristic).
*   **LLM Confidence Penalty (-45):** A strong negative score is applied if the LLM is confident that the issue does not affect cycling infrastructure (e.g. issues on main car lanes), suppressing false positives.
*   **Proximity to OSM Bike Network:**
    *   $\le 10\text{m}$: **+35 pts**
    *   $\le 25\text{m}$: **+20 pts**
    *   $\le 50\text{m}$: **+10 pts**
*   **Category Relevance:**
    *   *Fundräder* (Abandoned bikes): **+50 pts**
    *   *Roads, Signs, Lights, Overhanging foliage*: **+15 pts**
    *   *Trees/Branches*: **+10 pts**
*   **ADFC/City Priority Corridor Bonus (+20):** If within 50m of an official priority bicycle corridor.
*   **Ticket Status & Age Adjustments:**
    *   Open/Active: **+10 pts**
    *   Closed/Fixed: **-20 pts**
    *   Not Responsible/External: **-15 pts**
    *   Older than 180 days: **-10 pts**

### 3. Classification Engine (LLM vs Heuristic Fallback)
*   **Google GenAI SDK Integration:** [classify_reports_llm.py](file:///Volumes/T7/projects/oldenburg-stadt/classify_reports_llm.py) runs the primary categorization using `gemini-2.5-flash-lite`. It extracts:
    *   `is_cycling_related` (boolean)
    *   `subcategory` (10 specific cycling tiers like `pothole_damage`, `glass_debris`, etc.)
    *   `confidence` (float)
    *   `explanation_de` (German context text)
*   **Local Cache (`llm_classification_cache.json`):** Persists LLM API responses to control cost and latency.
*   **Regex Rule-Set:** When a report is not present in the LLM cache, [score_reports.py](file:///Volumes/T7/projects/oldenburg-stadt/score_reports.py) uses an optimized regex rule-set that matches the LLM with **84.45% accuracy** and an **83.96% F1 score**.
*   **Diagnostics:**
    *   [evaluate_rules.py](file:///Volumes/T7/projects/oldenburg-stadt/evaluate_rules.py) evaluates the regex rules against the LLM cache.
    *   [optimize_regex.py](file:///Volumes/T7/projects/oldenburg-stadt/optimize_regex.py) performs greedy pattern optimization.

### 4. Frontend Data Binding (`data.js`)
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

## 🗺️ Premium Interactive UI/UX Architecture

We have implemented key upgrades that transform the dashboard into a state-of-the-art interactive tool:

### 1. Marker Clustering & Pin Glyphs
*   **Clustering**: Integrated `Leaflet.markercluster` via CDN. The cluster node uses a custom `divIcon` with class `.custom-cluster`. Highlight rings indicate item count density: `.cluster-small` (emerald, <20 items), `.cluster-medium` (cyan, 20–99 items), and `.cluster-large` (coral, >=100 items).
*   **Emoji Glyphs**: Every map pin is represented as a custom HTML tag containing a subcategory-specific emoji glyph inside `.marker-pin`. When hovered, the pin inflates to `1.4x` via CSS transform transitions (`cubic-bezier(0.175, 0.885, 0.32, 1.275)`).

### 2. Smooth Glides & Selected Ripple
*   **Glides**: Swapped immediate map movements with `map.flyTo([lat, lng], 16, { duration: 1.2, easeLinearity: 0.25 })`.
*   **Ripple Pulse**: Triggered by `setActiveMarker()`. It adds class `.active-pin-ripple` to the selected pin's element. It draws an absolute-positioned pseudo-element expanding outward via a CSS keyframe animation (`pinRipple`), pulsing in the color of the selected report's classification tier.

### 3. Slide-Out Details Sidebar
*   **Layout**: Converted the details block `#map-details-card` into a fixed right sidebar.
*   **Transitions**: Instead of toggling `display`, it transitions the X-axis transform (`translateX(100%)` to `translateX(0)`) using `transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)`.

### 4. Dynamic Density Heatmap Mode
*   **Heatmap**: Uses `Leaflet.heat` (`L.heatLayer`). Points are constructed dynamically in `renderHeatmap()` as `[latitude, longitude, intensity]`. Intensity is scaled based on confidence score (from `0.2` to `1.0`).
*   **State Control**: Toggled via `toggleHeatmap()`, which manages the `showHeatmap` global boolean, replaces the HTML button state, and swaps Leaflet layers (`markerLayerGroup` vs `heatmapLayer`).
*   **Smart Fallback**: Clicking an issue from the sidebar list auto-disables Heatmap Mode (`showHeatmap = false`) and loads the pins layer so that `selectReport` can target the specific pin element and trigger the selection ripple.

### 5. Multi-Image Media Carousel
*   **Data Injection**: Renders inside `#overlay-carousel-slides` dynamically using the global `carouselImages` array. Mocks secondary slides for testing category actions if only one photo is present.
*   **Slide Transitions**: Sliding is controlled via `showSlide(index)` which applies a horizontal translation (`translateX(-index * 100%)`) on the slides track.
*   **Touch Gesture Support**: Configured inside `setupCarouselSwipe(element)` using passive listeners for `touchstart` and `touchend`. Calculates horizontal drag delta (`startX - endX`) and triggers `nextSlide()` or `prevSlide()` on swipe thresholds of >50px.

### 6. Embedded Satellite Map & Action Deep-Links
*   **Preview Iframe**: Renders a Google Maps embed iframe `#overlay-satellite-iframe` pointed to `q={latitude},{longitude}&z=19&t=k&output=embed` inside the details sidebar, showing real-world surface conditions.
*   **Direct Viewport Panoramas**: Configures direct deep-links to external Google Street View using viewpoints:
    ```
    https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={latitude},{longitude}
    ```

### 7. Unified Filtering Pipeline
*   **Pipeline**: All lists and map layers are filtered through `getFilteredReports()`. It runs the query sequentially:
    1. Apply time preset or custom date range filters inside `getTimeFilteredReports()`.
    2. Apply confidence classification filter card filters.
    3. Apply live text input search queries matching report ID, text description, subcategory, or street.

---

## 🔮 Roadmap & Potential Future Tasks

If the user requests additional features or improvements, here are recommended implementation paths:

### 1. Interactive Classification Threshold Sliders
*   **Goal**: Allow users to adjust scoring thresholds directly from the dashboard.
*   **Implementation**: Add slider elements to the sidebar. In `app.js`, dynamically re-classify and filter `CLASSIFIED_REPORTS` when sliders are dragged, updating the map markers and cards in real-time.

### 2. Live Overpass Queries in Python
*   **Goal**: Ensure data is completely up to date with OSM.
*   **Implementation**: Enhance `download_osm_bike.py` to programmatically pull the latest Overpass elements without relying on hardcoded mirror links if they fail.

### 3. Drag-and-Drop Newsletter Layouts
*   **Goal**: Allow editing the order of newsletter reports before copying.
*   **Implementation**: Use HTML5 Drag & Drop API on the issue items within the newsletter preview panel to let users reorder reports, then regenerate the Markdown representation in real-time.

### 4. Interactive Report Submissions (Mapping Mode)
*   **Goal**: Allow manual creation of reports directly on the map.
*   **Implementation**: Add a "Draw Marker" toggle using Leaflet's drawing tools. Users can drop a pin, fill out a small card, and append it to the locally stored list.

Good luck coding, agent! Feel free to build upon this robust foundation.
