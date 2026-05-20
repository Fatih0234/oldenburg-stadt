// Global State variables
let map;
let geojsonLayer;
let markerLayerGroup;
let activeFilters = new Set(); // Empty Set means all issues
let timeFilter = 'all'; // 'all', '7d', '30d', '90d', 'custom'
let customStartDate = null;
let customEndDate = null;
let currentSlideIndex = 0;
let activeMarker = null;
let reportMarkers = {};
let showHeatmap = false;
let heatmapLayer = null;
let carouselImages = [];
let activeSlideIndex = 0;
let activeReportId = null;
let monthlyDigestData = null;

const SUBCATEGORY_NAMES = {
    'pothole_damage': 'Schlagloch / Fahrbahnschaden',
    'glass_debris': 'Scherben / Verschmutzung',
    'vegetation_block': 'Überhängendes Grün / Äste',
    'illegal_parking_obstruction': 'Falschparker / Hindernis',
    'signal_light_timing': 'Ampelschaltung / Sensor',
    'crossing_safety': 'Gefährliche Kreuzung',
    'signage_detours': 'Wegweisung / Umleitung',
    'bike_parking': 'Fahrradständer',
    'other_cycling': 'Sonstiges Radthema',
    'unrelated': 'Nicht radspezifisch'
};

// Initialize when DOM content is loaded
document.addEventListener('DOMContentLoaded', () => {
    updateStats();
    updateMonthlyDigest();
    initMap();
    renderIssueList();
    initSidebarToggle();
    initOnboarding();
});



// 2. Metrics Statistics
function updateStats() {
    let counts = {
        'Confirmed cycling issue': 0,
        'Likely cycling issue': 0,
        'Possibly affects cyclists': 0,
        'Not cycling-specific': 0
    };

    const timeFiltered = getTimeFilteredReports(true);

    timeFiltered.forEach(r => {
        if (counts.hasOwnProperty(r.cyclist_impact_label)) {
            counts[r.cyclist_impact_label]++;
        }
    });

    document.getElementById('count-confirmed').textContent = counts['Confirmed cycling issue'];
    document.getElementById('count-likely').textContent = counts['Likely cycling issue'];
    document.getElementById('count-possible').textContent = counts['Possibly affects cyclists'];
    document.getElementById('count-generic').textContent = counts['Not cycling-specific'];
}

// 2.2. Monthly Civic Insight Digest
function isStrongCyclingReport(report) {
    return report.cyclist_impact_label === 'Confirmed cycling issue' ||
        report.cyclist_impact_label === 'Likely cycling issue';
}

function getReportsInRollingWindow(days, offsetDays = 0) {
    if (typeof CLASSIFIED_REPORTS === 'undefined' || !Array.isArray(CLASSIFIED_REPORTS)) {
        return [];
    }

    const ref = getReferenceDate();
    const end = new Date(ref.getTime() - offsetDays * 24 * 60 * 60 * 1000);
    const start = new Date(end.getTime() - days * 24 * 60 * 60 * 1000);

    return CLASSIFIED_REPORTS.filter(report => {
        if (!report.createdAt) return false;
        const itemDate = new Date(report.createdAt);
        return itemDate >= start && itemDate <= end;
    });
}

function getTopStreetSegment(reports) {
    const segmentMap = new Map();

    reports.forEach(report => {
        const segment = (report.nearest_segment_name || '').trim();
        if (!segment) return;

        if (!segmentMap.has(segment)) {
            segmentMap.set(segment, {
                segment,
                count: 0,
                reports: []
            });
        }

        const entry = segmentMap.get(segment);
        entry.count += 1;
        entry.reports.push(report);
    });

    return Array.from(segmentMap.values()).sort((a, b) => b.count - a.count || a.segment.localeCompare(b.segment, 'de'))[0] || null;
}

function getTopCyclingReport(reports) {
    return reports
        .filter(isStrongCyclingReport)
        .sort((a, b) => {
            const scoreDiff = (b.confidence_score || 0) - (a.confidence_score || 0);
            if (scoreDiff !== 0) return scoreDiff;

            const distA = Number.isFinite(Number(a.distance_to_bike_path_meters)) ? Number(a.distance_to_bike_path_meters) : 9999;
            const distB = Number.isFinite(Number(b.distance_to_bike_path_meters)) ? Number(b.distance_to_bike_path_meters) : 9999;
            if (distA !== distB) return distA - distB;

            return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
        })[0] || null;
}

function getGermanImpactLabel(label) {
    switch (label) {
        case 'Confirmed cycling issue':
            return 'bestätigt radrelevant';
        case 'Likely cycling issue':
            return 'wahrscheinlich radrelevant';
        case 'Possibly affects cyclists':
            return 'möglicherweise radrelevant';
        default:
            return 'allgemeine Meldung';
    }
}

function formatPeriodLabel() {
    const ref = getReferenceDate();
    const start = new Date(ref.getTime() - 30 * 24 * 60 * 60 * 1000);
    const options = { day: '2-digit', month: 'short' };
    return `${start.toLocaleDateString('de-DE', options)} bis ${ref.toLocaleDateString('de-DE', options)}`;
}

function setBriefingCardDisabled(cardId, disabled) {
    const card = document.getElementById(cardId);
    if (card) {
        card.disabled = disabled;
        card.classList.toggle('is-disabled', disabled);
    }
}

function updateMonthlyDigest() {
    const briefing = document.getElementById('monthly-briefing');
    if (!briefing) return;

    const currentReports = getReportsInRollingWindow(30);
    const previousReports = getReportsInRollingWindow(30, 30);
    const currentCyclingReports = currentReports.filter(isStrongCyclingReport);
    const previousCyclingReports = previousReports.filter(isStrongCyclingReport);
    const topSegment = getTopStreetSegment(currentReports);
    const topCyclingReport = getTopCyclingReport(currentReports);

    monthlyDigestData = {
        currentReports,
        currentCyclingReports,
        previousCyclingReports,
        topSegment,
        topCyclingReport
    };

    const periodLabel = document.getElementById('briefing-period-label');
    if (periodLabel) {
        periodLabel.textContent = formatPeriodLabel();
    }

    const trendValue = document.getElementById('briefing-trend-value');
    const trendTitle = document.getElementById('briefing-trend-title');
    const trendDetail = document.getElementById('briefing-trend-detail');
    const cyclingDelta = currentCyclingReports.length - previousCyclingReports.length;
    const deltaText = cyclingDelta === 0
        ? 'gleich viele radrelevante wie im Zeitraum davor'
        : `${Math.abs(cyclingDelta)} radrelevante ${cyclingDelta > 0 ? 'mehr' : 'weniger'} als im Zeitraum davor`;

    if (trendValue && trendTitle && trendDetail) {
        trendValue.textContent = currentCyclingReports.length;
        trendTitle.textContent = `${currentCyclingReports.length} radrelevante Meldungen im letzten Monat`;
        trendDetail.textContent = `${currentReports.length} Meldungen insgesamt, ${deltaText}.`;
    }
    setBriefingCardDisabled('briefing-trend-card', currentReports.length === 0);

    const hotspotValue = document.getElementById('briefing-hotspot-value');
    const hotspotTitle = document.getElementById('briefing-hotspot-title');
    const hotspotDetail = document.getElementById('briefing-hotspot-detail');
    if (hotspotValue && hotspotTitle && hotspotDetail) {
        if (topSegment) {
            hotspotValue.textContent = topSegment.count;
            hotspotTitle.textContent = `${topSegment.segment} war der häufigste Meldepunkt`;
            hotspotDetail.textContent = `${topSegment.count} Meldungen im Monatsfenster. Anklicken zeigt den Schwerpunkt auf der Karte.`;
        } else {
            hotspotValue.textContent = '0';
            hotspotTitle.textContent = 'Kein Straßenschwerpunkt erkennbar';
            hotspotDetail.textContent = 'Für diesen Zeitraum fehlen Straßensegmente.';
        }
    }
    setBriefingCardDisabled('briefing-hotspot-card', !topSegment);

    const focusValue = document.getElementById('briefing-focus-value');
    const focusTitle = document.getElementById('briefing-focus-title');
    const focusDetail = document.getElementById('briefing-focus-detail');
    if (focusValue && focusTitle && focusDetail) {
        if (topCyclingReport) {
            focusValue.textContent = topCyclingReport.confidence_score || 0;
            focusTitle.textContent = `Fokusfall #${topCyclingReport.id}: ${topCyclingReport.categoryName || 'Meldung'}`;
            focusDetail.textContent = `${topCyclingReport.nearest_segment_name || 'Unbekannter Abschnitt'}, ${getGermanImpactLabel(topCyclingReport.cyclist_impact_label)}.`;
        } else {
            focusValue.textContent = '0';
            focusTitle.textContent = 'Kein radrelevanter Fokusfall';
            focusDetail.textContent = 'Im Monatsfenster gibt es keine bestätigten oder wahrscheinlichen Radverkehrsmeldungen.';
        }
    }
    setBriefingCardDisabled('briefing-focus-card', !topCyclingReport);
}

// 2.5. Sidebar Folding Integration (Foldable Sidebar with premium transitions)
function initSidebarToggle() {
    const toggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (!sidebar) return;

    // Retrieve saved state preference
    const savedState = localStorage.getItem('sidebar-collapsed');
    if (savedState === 'true') {
        sidebar.classList.add('collapsed');
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-label', 'Sidebar ausklappen');
            toggleBtn.setAttribute('title', 'Sidebar ausklappen (B)');
        }
        // Slightly delay map invalidation to let layout settle
        setTimeout(() => {
            if (map) map.invalidateSize();
        }, 200);
    }
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleSidebar);
    }
    
    // Keyboard shortcut (B to toggle sidebar, unless focus is in input/textarea)
    document.addEventListener('keydown', (e) => {
        if ((e.key === 'b' || e.key === 'B') && 
            document.activeElement.tagName !== 'INPUT' && 
            document.activeElement.tagName !== 'TEXTAREA') {
            e.preventDefault();
            toggleSidebar();
        }
    });
}

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');
    if (!sidebar) return;
    
    const isCollapsed = sidebar.classList.toggle('collapsed');
    localStorage.setItem('sidebar-collapsed', isCollapsed);
    
    // Update accessibility description
    if (toggleBtn) {
        toggleBtn.setAttribute('aria-label', isCollapsed ? 'Sidebar ausklappen' : 'Sidebar einklappen');
        toggleBtn.setAttribute('title', isCollapsed ? 'Sidebar ausklappen (B)' : 'Sidebar einklappen (B)');
    }
    
    // Premium transition resize loop: continuously recalculate map size during the 400ms CSS animation
    const startTime = performance.now();
    const duration = 400;
    
    function updateMapSize(time) {
        const elapsed = time - startTime;
        if (map) {
            map.invalidateSize();
        }
        if (elapsed < duration) {
            requestAnimationFrame(updateMapSize);
        }
    }
    requestAnimationFrame(updateMapSize);
}

// 3. Map Initialization & Layer Rendering
function initMap() {
    // Center of Oldenburg (Oldb)
    map = L.map('map', {
        zoomControl: false
    }).setView([53.1412, 8.2125], 13);
    
    // Add custom zoom control at top right
    L.control.zoom({ position: 'topright' }).addTo(map);

    // Dark Matter Map Tiles (CartoDB) - Looks extremely premium and techy!
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // Style and Render OSM Bike Network Layer
    if (typeof BIKE_NETWORK_GEOJSON !== 'undefined') {
        geojsonLayer = L.geoJSON(BIKE_NETWORK_GEOJSON, {
            style: (feature) => {
                const isBicycleRoad = feature.properties.bicycle_road === 'yes';
                return {
                    color: isBicycleRoad ? '#06b6d4' : '#10b981', // Cyan for bicycle streets, emerald for cycleways
                    weight: isBicycleRoad ? 3 : 1.8,
                    opacity: 0.35,
                    dashArray: isBicycleRoad ? '5, 5' : null
                };
            },
            onEachFeature: (feature, layer) => {
                const name = feature.properties.name || "Radweg / Fahrradstraße";
                const type = feature.properties.highway || "Infrastruktur";
                layer.bindTooltip(`<strong>${name}</strong> (${type})`, {
                    sticky: true,
                    className: 'map-tooltip'
                });

                // Hover highlighting
                layer.on('mouseover', function () {
                    this.setStyle({
                        opacity: 0.85,
                        weight: 3.5
                    });
                });
                layer.on('mouseout', function () {
                    const isBicycleRoad = feature.properties.bicycle_road === 'yes';
                    this.setStyle({
                        opacity: 0.35,
                        weight: isBicycleRoad ? 3 : 1.8
                    });
                });
            }
        }).addTo(map);
    }

    // Initialize Marker Cluster Group for Reports with density-specific custom cluster styling
    markerLayerGroup = L.markerClusterGroup({
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        maxClusterRadius: 40,
        iconCreateFunction: function(cluster) {
            const childCount = cluster.getChildCount();
            let sizeClass = 'cluster-small';
            if (childCount >= 100) sizeClass = 'cluster-large';
            else if (childCount >= 20) sizeClass = 'cluster-medium';
            
            return L.divIcon({
                html: `<div class="custom-cluster ${sizeClass}"><span>${childCount}</span></div>`,
                className: 'custom-cluster-icon',
                iconSize: [40, 40]
            });
        }
    }).addTo(map);
    updateMapMarkers();
}

// Helper to map Category ID to standard Emoji glyph
function getCategoryEmoji(categoryId) {
    switch (categoryId) {
        case 3: return '🚧'; // Straßen
        case 4: return '⚠️'; // Verkehrszeichen
        case 5: return '💡'; // Straßenbeleuchtung
        case 6: return '🚦'; // Ampel
        case 7: return '🚲'; // Fundräder
        case 8: return '🧹'; // Wilde Müllkippe
        case 9: return '🧸'; // Spielplätze
        case 10: return '🌿'; // Privates Grün an Straßen
        case 11: return '🌳'; // Öffentliches Grün, Parkanlagen
        default: return '📍';
    }
}

// 4. Update Markers on Map Based on Current Filters
function updateMapMarkers() {
    // Clear pins
    markerLayerGroup.clearLayers();
    reportMarkers = {};

    // Clear active marker class
    setActiveMarker(null);

    if (showHeatmap) {
        renderHeatmap();
    } else {
        // Clear heatmap if present
        if (heatmapLayer && map.hasLayer(heatmapLayer)) {
            map.removeLayer(heatmapLayer);
        }

        const filtered = getFilteredReports();
        
        filtered.forEach(report => {
            if (!report.latitude || !report.longitude) return;

            const markerClass = getMarkerPinClass(report.cyclist_impact_label);
            const emoji = getCategoryEmoji(report.categoryId);
            const markerIcon = L.divIcon({
                className: 'custom-div-icon',
                html: `<div class="marker-pin ${markerClass}">${emoji}</div>`,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            });

            const marker = L.marker([report.latitude, report.longitude], {
                icon: markerIcon
            });

            // Click handler to select and fly to marker
            marker.on('click', () => {
                selectReport(report);
            });

            reportMarkers[report.id] = marker;
            markerLayerGroup.addLayer(marker);
        });
    }
}

// Heatmap Mode Toggle Actions
function toggleHeatmap() {
    showHeatmap = !showHeatmap;
    const btn = document.getElementById('btn-toggle-heatmap');
    
    if (showHeatmap) {
        if (btn) {
            btn.innerHTML = '<span class="btn-icon">📍</span> Pins anzeigen';
            btn.classList.add('active-heatmap');
        }
        if (map.hasLayer(markerLayerGroup)) {
            map.removeLayer(markerLayerGroup);
        }
        renderHeatmap();
    } else {
        if (btn) {
            btn.innerHTML = '<span class="btn-icon">🗺️</span> Heatmap anzeigen';
            btn.classList.remove('active-heatmap');
        }
        if (heatmapLayer && map.hasLayer(heatmapLayer)) {
            map.removeLayer(heatmapLayer);
        }
        markerLayerGroup.addTo(map);
    }
}

// Generate density heatpoints based on report coordinates and weight
function renderHeatmap() {
    if (heatmapLayer && map.hasLayer(heatmapLayer)) {
        map.removeLayer(heatmapLayer);
    }

    const filtered = getFilteredReports();
    const heatPoints = [];

    filtered.forEach(report => {
        if (report.latitude && report.longitude) {
            const score = report.confidence_score !== undefined ? report.confidence_score : 50;
            const intensity = Math.max(0.2, Math.min(1.0, score / 100));
            heatPoints.push([report.latitude, report.longitude, intensity]);
        }
    });

    heatmapLayer = L.heatLayer(heatPoints, {
        radius: 25,
        blur: 15,
        maxZoom: 16,
        minOpacity: 0.3,
        gradient: {
            0.2: '#3b82f6', // blue
            0.4: '#06b6d4', // cyan
            0.6: '#10b981', // emerald
            0.8: '#f59e0b', // amber
            1.0: '#ef4444'  // red
        }
    }).addTo(map);
}

// Helper to select a report, fly to it, and trigger pulsing active ripple
function selectReport(report) {
    if (showHeatmap) {
        toggleHeatmap(); // Automatically switch to Pins Mode to locate the marker
    }

    activeReportId = report.id;
    showMapDetails(report);
    setActiveRowInList(report.id);
    
    if (!report.latitude || !report.longitude) return;
    
    const marker = reportMarkers[report.id];
    if (marker) {
        // Zoom and resolve clusters if target is currently hidden inside one
        markerLayerGroup.zoomToShowLayer(marker, () => {
            map.flyTo([report.latitude, report.longitude], 16, {
                duration: 1.2,
                easeLinearity: 0.25
            });
            setTimeout(() => {
                setActiveMarker(marker);
            }, 100);
        });
    } else {
        map.flyTo([report.latitude, report.longitude], 16, {
            duration: 1.2,
            easeLinearity: 0.25
        });
    }
}

// Helper to manage and apply ripple style on active marker
function setActiveMarker(marker) {
    if (activeMarker) {
        const prevEl = activeMarker.getElement();
        if (prevEl) {
            const pin = prevEl.querySelector('.marker-pin');
            if (pin) pin.classList.remove('active-pin-ripple');
        }
    }
    
    activeMarker = marker;
    
    if (activeMarker) {
        const el = activeMarker.getElement();
        if (el) {
            const pin = el.querySelector('.marker-pin');
            if (pin) pin.classList.add('active-pin-ripple');
        }
    }
}

function getMarkerPinClass(label) {
    switch (label) {
        case 'Confirmed cycling issue': return 'marker-pin-confirmed';
        case 'Likely cycling issue': return 'marker-pin-likely';
        case 'Possibly affects cyclists': return 'marker-pin-possible';
        default: return 'marker-pin-generic';
    }
}

// Helper to get color code
function getLabelColor(label) {
    switch (label) {
        case 'Confirmed cycling issue': return '#ef4444'; // Red
        case 'Likely cycling issue': return '#f97316'; // Orange
        case 'Possibly affects cyclists': return '#facc15'; // Yellow
        default: return '#64748b'; // Generic Grey
    }
}

// 5. Filtering Functions
function getFilteredReports() {
    let filtered = getTimeFilteredReports(false);
    
    // Apply real-time search queries if present
    const searchInput = document.getElementById('search-input');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    
    if (query) {
        filtered = filtered.filter(r => {
            const text = (r.replacingText || '').toLowerCase();
            const cat = (r.categoryName || '').toLowerCase();
            const street = (r.nearest_segment_name || '').toLowerCase();
            const idStr = String(r.id);
            return text.includes(query) || cat.includes(query) || street.includes(query) || idStr.includes(query);
        });
    }

    // Sort by createdAt date descending (most recent first)
    filtered = [...filtered].sort((a, b) => {
        const timeA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
        const timeB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
        return timeB - timeA;
    });

    return filtered;
}

// Live Search Handlers
function handleSearch(value) {
    const clearBtn = document.getElementById('search-clear-btn');
    if (clearBtn) {
        clearBtn.style.display = value ? 'block' : 'none';
    }
    renderIssueList();
    updateMapMarkers();
}

function clearSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.value = '';
        handleSearch('');
    }
}

function getReferenceDate() {
    const now = new Date();
    if (!CLASSIFIED_REPORTS || CLASSIFIED_REPORTS.length === 0) {
        return now;
    }
    
    let latestTimestamp = 0;
    CLASSIFIED_REPORTS.forEach(r => {
        if (r.createdAt) {
            const dateVal = new Date(r.createdAt).getTime();
            if (dateVal > latestTimestamp) {
                latestTimestamp = dateVal;
            }
        }
    });
    
    if (latestTimestamp === 0) {
        return now;
    }
    
    const latestReportDate = new Date(latestTimestamp);
    const diffTime = Math.abs(now - latestReportDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays > 14) {
        return latestReportDate;
    }
    return now;
}

function getTimeFilteredReports(excludeConfidence = false) {
    let reports = CLASSIFIED_REPORTS;
    
    if (timeFilter !== 'all') {
        const ref = getReferenceDate();
        let minDate = null;
        
        if (timeFilter === '7d') {
            minDate = new Date(ref.getTime() - 7 * 24 * 60 * 60 * 1000);
        } else if (timeFilter === '30d') {
            minDate = new Date(ref.getTime() - 30 * 24 * 60 * 60 * 1000);
        } else if (timeFilter === '90d') {
            minDate = new Date(ref.getTime() - 90 * 24 * 60 * 60 * 1000);
        } else if (timeFilter === 'custom') {
            const start = customStartDate ? new Date(customStartDate) : null;
            const end = customEndDate ? new Date(customEndDate) : null;
            
            reports = reports.filter(r => {
                if (!r.createdAt) return false;
                const itemDate = new Date(r.createdAt);
                if (start && itemDate < start) return false;
                if (end) {
                    const endOfDay = new Date(end);
                    endOfDay.setHours(23, 59, 59, 999);
                    if (itemDate > endOfDay) return false;
                }
                return true;
            });
        }
        
        if (minDate && timeFilter !== 'custom') {
            reports = reports.filter(r => r.createdAt && new Date(r.createdAt) >= minDate);
        }
    }
    
    if (!excludeConfidence) {
        if (activeFilters.size > 0) {
            reports = reports.filter(r => activeFilters.has(r.cyclist_impact_label));
        }
    }
    
    return reports;
}


function toggleConfidenceFilter(label) {
    if (activeFilters.has(label)) {
        activeFilters.delete(label);
    } else {
        activeFilters.add(label);
    }
    
    updateFilterUI();
    renderIssueList();
    updateMapMarkers();
}

function updateFilterUI() {
    // Synchronize metric cards active state
    const cardMap = {
        'Confirmed cycling issue': '.gradient-confirmed',
        'Likely cycling issue': '.gradient-likely',
        'Possibly affects cyclists': '.gradient-possible',
        'Not cycling-specific': '.gradient-generic'
    };
    
    for (const [label, selector] of Object.entries(cardMap)) {
        const card = document.querySelector(selector);
        if (card) {
            if (activeFilters.has(label)) {
                card.classList.add('active');
            } else {
                card.classList.remove('active');
            }
        }
    }
}

function clearFilters() {
    activeFilters.clear();
    updateFilterUI();
    renderIssueList();
    updateMapMarkers();
}

function handleTimePresetChange() {
    const select = document.getElementById('time-preset-select');
    timeFilter = select.value;
    
    const customInputs = document.getElementById('custom-date-inputs');
    if (timeFilter === 'custom') {
        customInputs.classList.remove('hidden');
        
        // Populate default values for date inputs if they are empty
        const ref = getReferenceDate();
        const formattedRef = ref.toISOString().split('T')[0];
        
        const startInput = document.getElementById('start-date');
        const endInput = document.getElementById('end-date');
        
        if (!startInput.value) {
            // Default start to 30 days before reference date
            const defaultStart = new Date(ref.getTime() - 30 * 24 * 60 * 60 * 1000);
            startInput.value = defaultStart.toISOString().split('T')[0];
            customStartDate = startInput.value;
        }
        if (!endInput.value) {
            endInput.value = formattedRef;
            customEndDate = endInput.value;
        }
    } else {
        customInputs.classList.add('hidden');
    }
    
    // Trigger updates for all reactive components
    updateStats();
    renderIssueList();
    updateMapMarkers();
}

function handleCustomDateChange() {
    customStartDate = document.getElementById('start-date').value;
    customEndDate = document.getElementById('end-date').value;
    
    updateStats();
    renderIssueList();
    updateMapMarkers();
}

function setRollingThirtyDayView() {
    const select = document.getElementById('time-preset-select');
    if (select) {
        select.value = '30d';
    }
    timeFilter = '30d';

    const customInputs = document.getElementById('custom-date-inputs');
    if (customInputs) {
        customInputs.classList.add('hidden');
    }
}

function setSearchQuery(query) {
    const searchInput = document.getElementById('search-input');
    const clearBtn = document.getElementById('search-clear-btn');

    if (searchInput) {
        searchInput.value = query;
    }
    if (clearBtn) {
        clearBtn.style.display = query ? 'block' : 'none';
    }
}

function refreshDashboardViews() {
    updateStats();
    updateFilterUI();
    renderIssueList();
    updateMapMarkers();
}

function focusReportsOnMap(reports) {
    if (!map || !Array.isArray(reports)) return;

    const points = reports
        .filter(report => report.latitude && report.longitude)
        .map(report => [report.latitude, report.longitude]);

    if (points.length === 0) return;

    if (showHeatmap) {
        toggleHeatmap();
    }

    if (points.length === 1) {
        map.flyTo(points[0], 16, {
            duration: 1.1,
            easeLinearity: 0.25
        });
        return;
    }

    const bounds = L.latLngBounds(points);
    map.fitBounds(bounds.pad(0.18), {
        maxZoom: 16,
        animate: true,
        duration: 1
    });
}

function handleMonthlyInsightClick(type) {
    if (!monthlyDigestData) {
        updateMonthlyDigest();
    }
    if (!monthlyDigestData) return;

    setRollingThirtyDayView();

    if (type === 'trend') {
        setSearchQuery('');
        activeFilters.clear();
        activeFilters.add('Confirmed cycling issue');
        activeFilters.add('Likely cycling issue');
        refreshDashboardViews();
        focusReportsOnMap(monthlyDigestData.currentCyclingReports);
    } else if (type === 'hotspot' && monthlyDigestData.topSegment) {
        activeFilters.clear();
        setSearchQuery(monthlyDigestData.topSegment.segment);
        refreshDashboardViews();
        focusReportsOnMap(monthlyDigestData.topSegment.reports);
    } else if (type === 'focus' && monthlyDigestData.topCyclingReport) {
        setSearchQuery('');
        activeFilters.clear();
        activeFilters.add('Confirmed cycling issue');
        activeFilters.add('Likely cycling issue');
        refreshDashboardViews();
        selectReport(monthlyDigestData.topCyclingReport);
    }
}

// 6. Issue List Sidebar Rendering
function renderIssueList() {
    const listContainer = document.getElementById('issue-list-elements');
    const filteredCountBadge = document.getElementById('filtered-count');
    
    const reports = getFilteredReports();
    filteredCountBadge.textContent = reports.length;
    
    if (reports.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state">
                <span>🔍</span>
                <p>Keine Berichte entsprechen diesem Filter.</p>
            </div>
        `;
        return;
    }

    listContainer.innerHTML = '';
    
    // Show top 100 in sidebar to prevent DOM lag, scroll lazy loading could be added but 100 is plenty
    const displayedReports = reports.slice(0, 100);

    displayedReports.forEach(r => {
        const dateObj = new Date(r.createdAt);
        const formattedDate = dateObj.toLocaleDateString('de-DE', { day: '2-digit', month: 'short' });
        const color = getLabelColor(r.cyclist_impact_label);
        const stateEmoji = r.state === 'CLOSED' ? '✅' : (r.state === 'IN_PROCESS' ? '⏳' : '📥');
        
        const card = document.createElement('div');
        
        let impactClass = 'impact-generic';
        if (r.cyclist_impact_label === 'Confirmed cycling issue') impactClass = 'impact-confirmed';
        else if (r.cyclist_impact_label === 'Likely cycling issue') impactClass = 'impact-likely';
        else if (r.cyclist_impact_label === 'Possibly affects cyclists') impactClass = 'impact-possible';
        
        card.className = `issue-row ${impactClass}`;
        card.setAttribute('data-id', r.id);
        
        const categoryEmoji = getCategoryEmoji(r.categoryId);
        const displayDistance = r.distance_to_bike_path_meters !== undefined && r.distance_to_bike_path_meters !== null
            ? `${Number(r.distance_to_bike_path_meters).toFixed(1)}m to path`
            : '--';
        
        card.innerHTML = `
            <div class="issue-row-icon-wrapper" style="border-color: ${color}4d; background: ${color}10;">
                <span class="row-category-emoji" style="font-size: 1.25rem;">${categoryEmoji}</span>
            </div>
            <div class="issue-row-body">
                <div class="issue-row-header">
                    <span class="issue-cat">
                        ${r.categoryName} <span class="issue-id">#${r.id}</span>
                    </span>
                    <span class="issue-dist-tag">${displayDistance}</span>
                </div>
                <p class="issue-snippet">${r.replacingText || 'Keine Beschreibung vorhanden.'}</p>
                <div class="issue-meta">
                    <span class="issue-state-badge state-${r.state.toLowerCase() === 'closed' ? 'closed' : (r.state.toLowerCase() === 'in_process' ? 'process' : 'open')}">${stateEmoji} ${r.state}</span>
                    <span class="issue-date">${formattedDate}</span>
                </div>
            </div>
        `;

        card.addEventListener('click', () => {
            selectReport(r);
        });

        listContainer.appendChild(card);
    });

    if (activeReportId) {
        setActiveRowInList(activeReportId);
    }
}

// Helper to highlight selected list row and scroll it into view
function setActiveRowInList(reportId) {
    const rows = document.querySelectorAll('.issue-row');
    rows.forEach(row => {
        row.classList.remove('active');
    });
    
    const activeRow = document.querySelector(`.issue-row[data-id="${reportId}"]`);
    if (activeRow) {
        activeRow.classList.add('active');
        activeRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// 7. Floating Details Overlay Control
function showMapDetails(report) {
    const overlay = document.getElementById('map-details-card');
    
    // Set report ID
    const idEl = document.getElementById('overlay-id');
    if (idEl) {
        idEl.textContent = `#${report.id}`;
    }
    
    document.getElementById('overlay-label').textContent = report.cyclist_impact_label;
    document.getElementById('overlay-label').className = `badge`;
    document.getElementById('overlay-label').style.backgroundColor = getLabelColor(report.cyclist_impact_label);
    document.getElementById('overlay-label').style.color = '#fff';
    
    document.getElementById('overlay-category').textContent = report.categoryName;
    
    const dateObj = new Date(report.createdAt);
    const formattedDate = dateObj.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById('overlay-date').innerHTML = `📅 Gemeldet: ${formattedDate}`;
    document.getElementById('overlay-desc').textContent = report.replacingText || "Keine Textbeschreibung.";
    
    // Render LLM classification details
    const llmBox = document.getElementById('overlay-llm-box');
    if (report.subcategory) {
        const subcatPretty = SUBCATEGORY_NAMES[report.subcategory] || report.subcategory;
        const isCycling = report.is_cycling_related;
        const borderColor = isCycling ? '#10b981' : '#64748b';
        const bgColor = isCycling ? 'rgba(16, 185, 129, 0.05)' : 'rgba(100, 116, 139, 0.05)';
        const titleColor = isCycling ? '#10b981' : '#94a3b8';
        
        llmBox.innerHTML = `
            <div class="llm-info-box card-glass" style="margin-top: 12px; margin-bottom: 12px; padding: 12px; border-left: 3px solid ${borderColor}; background: ${bgColor}; border-radius: 8px;">
                <div style="font-weight: 600; font-size: 0.85rem; color: ${titleColor}; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                    <img src="assets/ui/ai_bot_badge.png" class="badge-img-icon" alt="AI Badge"> <span>KI-Klassifizierung: ${subcatPretty}</span>
                </div>
                <div style="font-style: italic; font-size: 0.85rem; color: #cbd5e1; line-height: 1.45;">"${report.explanation_de}"</div>
            </div>
        `;
    } else {
        llmBox.innerHTML = '';
    }

    // Relevance Score Spotlight
    const scoreValEl = document.getElementById('relevance-score-value');
    if (scoreValEl) {
        scoreValEl.textContent = report.confidence_score;
        const scoreColor = getLabelColor(report.cyclist_impact_label);
        scoreValEl.style.color = scoreColor;
        scoreValEl.style.textShadow = `0 0 10px ${scoreColor}33`;
    }

    // Stats grid
    const statsGrid = document.getElementById('overlay-stats-grid');
    let penaltyHtml = '';
    if (report.score_penalty && report.score_penalty < 0) {
        penaltyHtml = `<div class="stat-item">AI downrank: <span class="stat-val penalty-val">${report.score_penalty}</span></div>`;
    }
    
    const formatScore = (val) => val >= 0 ? `+${val}` : `${val}`;
    
    statsGrid.innerHTML = `
        <div class="stat-item">Distance to path: <span class="stat-val">${report.distance_to_bike_path_meters} m</span></div>
        <div class="stat-item">Category signal: <span class="stat-val bonus-val">+${report.score_category}</span></div>
        <div class="stat-item">Route proximity: <span class="stat-val bonus-val">${formatScore(report.score_distance)}</span></div>
        <div class="stat-item">Text signal: <span class="stat-val bonus-val">+${report.score_keywords}</span></div>
        ${penaltyHtml}
        <div class="stat-item">Status / Recency: <span class="stat-val">${formatScore(report.score_state + report.score_recency)}</span></div>
    `;
    
    if (report.nearest_segment_name) {
        statsGrid.innerHTML += `<div class="stat-item segment-item" style="grid-column: span 2">Nearest Segment: <span class="stat-val" style="word-break: break-all;">${report.nearest_segment_name}</span></div>`;
    }

    // Media swipeable gallery carousel logic
    const carouselContainer = document.getElementById('overlay-carousel-container');
    const slidesContainer = document.getElementById('overlay-carousel-slides');
    const dotsContainer = document.getElementById('overlay-carousel-dots');
    
    if (report.firstPictureUrl && typeof report.firstPictureUrl === 'string' && report.firstPictureUrl !== 'NaN') {
        carouselContainer.classList.remove('hidden');
        
        // Construct an array of images: use primary and add 1-2 stock context images for demo
        const images = [report.firstPictureUrl];
        if (report.categoryId === 8) { // Wilde Müllkippe
            images.push('https://images.unsplash.com/photo-1611284446314-60a58ac0deb9?auto=format&fit=crop&w=400&q=80');
            images.push('https://images.unsplash.com/photo-1530587191325-3db32d826c18?auto=format&fit=crop&w=400&q=80');
        } else if (report.categoryId === 3 || report.categoryId === 4) { // Straßen / Verkehrszeichen
            images.push('https://images.unsplash.com/photo-1541888946425-d81bb19240f5?auto=format&fit=crop&w=400&q=80');
            images.push('https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=400&q=80');
        } else {
            images.push('https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=400&q=80');
        }
        
        carouselImages = images;
        activeSlideIndex = 0;
        
        // Generate slides HTML
        slidesContainer.innerHTML = '';
        carouselImages.forEach(imgSrc => {
            const slide = document.createElement('div');
            slide.className = 'carousel-slide';
            slide.innerHTML = `<img src="${imgSrc}" alt="Report details image">`;
            slidesContainer.appendChild(slide);
        });
        
        // Generate indicators
        if (dotsContainer) {
            dotsContainer.innerHTML = '';
            carouselImages.forEach((_, idx) => {
                const dot = document.createElement('div');
                dot.className = `carousel-dot ${idx === 0 ? 'active' : ''}`;
                dot.addEventListener('click', () => showSlide(idx));
                dotsContainer.appendChild(dot);
            });
        }
        
        const prevArrow = document.getElementById('overlay-carousel-prev');
        const nextArrow = document.getElementById('overlay-carousel-next');
        if (prevArrow && nextArrow) {
            if (carouselImages.length <= 1) {
                prevArrow.style.display = 'none';
                nextArrow.style.display = 'none';
                if (dotsContainer) dotsContainer.style.display = 'none';
            } else {
                prevArrow.style.display = 'flex';
                nextArrow.style.display = 'flex';
                if (dotsContainer) dotsContainer.style.display = 'flex';
            }
        }
        
        showSlide(0);
        setupCarouselSwipe(slidesContainer);
    } else {
        carouselContainer.classList.add('hidden');
        carouselImages = [];
    }

    // Satellite context and action triggers
    const satContainer = document.getElementById('overlay-satellite-container');
    const satIframe = document.getElementById('overlay-satellite-iframe');
    const streetViewLink = document.getElementById('overlay-streetview-link');
    const directionLink = document.getElementById('overlay-direction-link');

    if (report.latitude && report.longitude) {
        directionLink.href = `https://www.google.com/maps/search/?api=1&query=${report.latitude},${report.longitude}`;
        directionLink.style.display = 'flex';

        if (streetViewLink) {
            streetViewLink.href = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${report.latitude},${report.longitude}`;
            streetViewLink.style.display = 'flex';
        }

        if (satContainer && satIframe) {
            satIframe.src = `https://maps.google.com/maps?q=${report.latitude},${report.longitude}&z=19&t=k&output=embed`;
            satContainer.classList.remove('hidden');
        }
    } else {
        if (satContainer) satContainer.classList.add('hidden');
        if (satIframe) satIframe.src = '';
        if (streetViewLink) streetViewLink.style.display = 'none';
        directionLink.style.display = 'none';
    }

    overlay.classList.remove('closed');
}

function hideMapDetails() {
    document.getElementById('map-details-card').classList.add('closed');
    setActiveMarker(null);
    activeReportId = null;
    const rows = document.querySelectorAll('.issue-row');
    rows.forEach(row => {
        row.classList.remove('active');
    });
}

// Carousel Slide Actions
function prevSlide() {
    showSlide(activeSlideIndex - 1);
}

function nextSlide() {
    showSlide(activeSlideIndex + 1);
}

function showSlide(index) {
    const slidesContainer = document.getElementById('overlay-carousel-slides');
    if (!slidesContainer || carouselImages.length === 0) return;

    if (index < 0) {
        index = carouselImages.length - 1;
    } else if (index >= carouselImages.length) {
        index = 0;
    }

    activeSlideIndex = index;
    slidesContainer.style.transform = `translateX(-${activeSlideIndex * 100}%)`;

    const dots = document.querySelectorAll('.carousel-dot');
    dots.forEach((dot, idx) => {
        if (idx === activeSlideIndex) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

// Touch swipe gesture configurations
function setupCarouselSwipe(element) {
    let startX = 0;
    let endX = 0;

    element.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
    }, { passive: true });

    element.addEventListener('touchend', (e) => {
        endX = e.changedTouches[0].clientX;
        handleSwipe();
    }, { passive: true });

    function handleSwipe() {
        const diffX = startX - endX;
        const threshold = 50; 
        if (Math.abs(diffX) > threshold) {
            if (diffX > 0) {
                nextSlide();
            } else {
                prevSlide();
            }
        }
    }
}

// =============================================================================
// Onboarding Tour Controller
// =============================================================================

const TOUR_STEPS = [
    {
        title: '🚲 Willkommen beim Rad-Verbesserer!',
        text: 'Dieses Dashboard analysiert öffentliche Bürgerberichte und identifiziert Mängel, die die Fahrradinfrastruktur in Oldenburg betreffen. Bereit für eine kurze Tour?',
        target: null,  // Step 1 is centered – no target element highlight
        position: 'center',
        onEnter: null,
        onLeave: null,
    },
    {
        title: '📈 Monatsbriefing',
        text: 'Das Monatsbriefing zeigt belastbare Signale aus den letzten 30 Tagen: Trend, häufigster Schwerpunkt und ein konkreter Fokusfall für die Detailprüfung.',
        target: '#monthly-briefing',
        position: 'right',
        onEnter: null,
        onLeave: null,
    },
    {
        title: '📊 KI-Konfidenz-Metriken',
        text: 'Die KI klassifiziert jeden Bericht in vier Kategorien: Bestätigt, Wahrscheinlich, Möglich und Allgemein. Klicken Sie auf eine Karte, um nur Berichte dieser Kategorie zu filtern.',
        target: '.metrics-grid',
        position: 'right',
        onEnter: null,
        onLeave: null,
    },
    {
        title: '🔍 Suche & Zeitfilter',
        text: 'Durchsuchen Sie Berichte nach Beschreibung, Straße oder ID. Der Zeitfilter schränkt Ergebnisse auf einen bestimmten Zeitraum ein – ideal um aktuelle Probleme im Blick zu behalten.',
        target: '.control-group',
        position: 'right',
        onEnter: null,
        onLeave: null,
    },
    {
        title: '📋 Mängel-Detailansicht',
        text: 'Klicken Sie auf einen Eintrag in der Liste oder einen Pin auf der Karte, um die vollständige Analyse zu sehen: Satellitenansicht, KI-Begründung, Relevanzscore und direkten Street-View-Link.',
        target: '#map-details-card',
        position: 'left',
        onEnter: function() {
            // Programmatically select the first cycling report so the card slides out
            const filtered = getFilteredReports();
            const firstCycling = filtered.find(r =>
                r.cyclist_impact_label === 'Confirmed cycling issue' ||
                r.cyclist_impact_label === 'Likely cycling issue'
            ) || filtered[0];
            if (firstCycling) {
                selectReport(firstCycling);
            }
        },
        onLeave: function(direction) {
            // If user goes back, close the detail card so it doesn't linger
            if (direction === 'back') {
                hideMapDetails();
            }
        },
    },
    {
        title: '🗺️ Interaktive Karte',
        text: 'Die Leaflet-Karte zeigt Pins für alle Berichte – farbkodiert nach KI-Konfidenz. Zoomen, clustern, oder schalten Sie auf Heatmap-Modus um, um Problembereiche auf einen Blick zu erkennen.',
        target: '#map',
        position: 'top-left',
        onEnter: null,
        onLeave: null,
    },
];

let tourActive = false;
let tourCurrentStep = 0;

function initOnboarding() {
    // Wire up the "Tour" button in the sidebar header
    const tourBtn = document.getElementById('btn-tour-trigger');
    if (tourBtn) {
        tourBtn.addEventListener('click', startTour);
    }

    // Wire up tour card controls
    const nextBtn = document.getElementById('tour-next-btn');
    const prevBtn = document.getElementById('tour-prev-btn');
    const closeBtn = document.getElementById('tour-close-btn');
    if (nextBtn) nextBtn.addEventListener('click', tourNext);
    if (prevBtn) prevBtn.addEventListener('click', tourPrev);
    if (closeBtn) closeBtn.addEventListener('click', closeTour);

    // Wire up welcome toast
    const toastStartBtn = document.getElementById('welcome-toast-start-btn');
    const toastSkipBtn = document.getElementById('welcome-toast-skip-btn');
    const toastCloseBtn = document.getElementById('welcome-toast-close-btn');
    if (toastStartBtn) toastStartBtn.addEventListener('click', () => {
        dismissToast();
        startTour();
    });
    if (toastSkipBtn) toastSkipBtn.addEventListener('click', dismissToast);
    if (toastCloseBtn) toastCloseBtn.addEventListener('click', dismissToast);

    // Backdrop click closes the tour
    const backdrop = document.getElementById('onboarding-backdrop');
    if (backdrop) backdrop.addEventListener('click', closeTour);

    // Keyboard: Escape to close, ArrowRight to advance, ArrowLeft to go back
    document.addEventListener('keydown', handleTourKeydown);

    // Show welcome toast after a short delay if not seen before
    const hasSeen = localStorage.getItem('rad-onboarding-seen');
    if (!hasSeen) {
        setTimeout(showWelcomeToast, 1200);
    }
}

function showWelcomeToast() {
    const toast = document.getElementById('welcome-onboarding-toast');
    if (!toast) return;
    toast.classList.remove('hidden');
}

function dismissToast(markSeen = true) {
    const toast = document.getElementById('welcome-onboarding-toast');
    if (!toast) return;
    toast.classList.add('dismissing');
    setTimeout(() => {
        toast.classList.add('hidden');
        toast.classList.remove('dismissing');
    }, 350);
    if (markSeen) {
        localStorage.setItem('rad-onboarding-seen', 'true');
    }
}

function startTour() {
    // Dismiss toast if still visible
    const toast = document.getElementById('welcome-onboarding-toast');
    if (toast && !toast.classList.contains('hidden')) {
        dismissToast(false);
    }

    tourActive = true;
    tourCurrentStep = 0;

    // Build step progress dots
    buildTourDots();

    // Show backdrop + card
    const backdrop = document.getElementById('onboarding-backdrop');
    const card = document.getElementById('onboarding-card');
    if (backdrop) {
        backdrop.classList.remove('hidden');
        // Trigger visible transition after next frame
        requestAnimationFrame(() => backdrop.classList.add('visible'));
    }
    if (card) {
        card.classList.remove('tour-hidden');
        card.classList.add('visible');
    }

    renderTourStep(tourCurrentStep);
}

function buildTourDots() {
    const dotsEl = document.getElementById('tour-dots');
    if (!dotsEl) return;
    dotsEl.innerHTML = '';
    TOUR_STEPS.forEach((_, i) => {
        const dot = document.createElement('div');
        dot.className = `tour-dot${i === 0 ? ' active' : ''}`;
        dot.addEventListener('click', () => jumpToTourStep(i));
        dotsEl.appendChild(dot);
    });
}

function updateTourDots(stepIndex) {
    document.querySelectorAll('.tour-dot').forEach((dot, i) => {
        dot.classList.toggle('active', i === stepIndex);
    });
}

function renderTourStep(stepIndex) {
    const step = TOUR_STEPS[stepIndex];
    if (!step) return;

    // Update text content
    const titleEl = document.getElementById('tour-step-title');
    const textEl = document.getElementById('tour-step-text');
    const progressEl = document.getElementById('tour-progress-text');
    const nextBtn = document.getElementById('tour-next-btn');
    const prevBtn = document.getElementById('tour-prev-btn');
    const highlight = document.getElementById('onboarding-highlight');

    if (titleEl) titleEl.textContent = step.title;
    if (textEl) textEl.textContent = step.text;
    if (progressEl) progressEl.textContent = `${stepIndex + 1} von ${TOUR_STEPS.length}`;

    // Update buttons
    if (prevBtn) prevBtn.style.visibility = stepIndex === 0 ? 'hidden' : 'visible';
    if (nextBtn) nextBtn.textContent = stepIndex === TOUR_STEPS.length - 1 ? '✓ Fertig' : 'Weiter →';

    updateTourDots(stepIndex);

    // Position highlight and card
    if (step.target) {
        const targetEl = document.querySelector(step.target);
        if (targetEl && highlight) {
            highlight.classList.remove('hidden');
            positionHighlight(targetEl, highlight);
            positionCard(targetEl, step.position);
        }
    } else {
        // Center card on screen, no highlight
        if (highlight) highlight.classList.add('hidden');
        centerCard();
    }

    // Run step enter hook if present
    if (step.onEnter) {
        // Delay slightly so the card is positioned first
        setTimeout(() => step.onEnter(), step.target ? 300 : 0);
    }
}

function positionHighlight(targetEl, highlightEl) {
    const PAD = 10;
    const rect = targetEl.getBoundingClientRect();
    highlightEl.style.top = `${rect.top - PAD}px`;
    highlightEl.style.left = `${rect.left - PAD}px`;
    highlightEl.style.width = `${rect.width + PAD * 2}px`;
    highlightEl.style.height = `${rect.height + PAD * 2}px`;
}

function positionCard(targetEl, position) {
    const card = document.getElementById('onboarding-card');
    if (!card) return;

    const CARD_W = 320;
    const CARD_GAP = 20;
    const PAD = 10;
    const rect = targetEl.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    // Measure card height roughly (will be set after render)
    const cardH = card.offsetHeight || 220;

    let top, left;

    switch (position) {
        case 'right':
            left = rect.right + PAD + CARD_GAP;
            top = rect.top + (rect.height / 2) - (cardH / 2);
            // If would overflow right, flip to left
            if (left + CARD_W > vw - 12) {
                left = rect.left - CARD_W - CARD_GAP;
            }
            break;
        case 'left':
            left = rect.left - CARD_W - CARD_GAP;
            top = rect.top + (rect.height / 2) - (cardH / 2);
            if (left < 12) {
                left = rect.right + PAD + CARD_GAP;
            }
            break;
        case 'top-left':
            left = rect.left + PAD;
            top = rect.top - cardH - CARD_GAP;
            if (top < 12) top = rect.bottom + CARD_GAP;
            break;
        case 'bottom':
            left = rect.left + (rect.width / 2) - (CARD_W / 2);
            top = rect.bottom + CARD_GAP;
            break;
        default:
            // center
            left = vw / 2 - CARD_W / 2;
            top = vh / 2 - (cardH / 2);
    }

    // Clamp to viewport
    left = Math.max(12, Math.min(left, vw - CARD_W - 12));
    top = Math.max(12, Math.min(top, vh - cardH - 12));

    card.style.left = `${left}px`;
    card.style.top = `${top}px`;
}

function centerCard() {
    const card = document.getElementById('onboarding-card');
    if (!card) return;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const CARD_W = 320;
    const cardH = card.offsetHeight || 220;
    card.style.left = `${vw / 2 - CARD_W / 2}px`;
    card.style.top = `${vh / 2 - cardH / 2}px`;
}

function tourNext() {
    if (!tourActive) return;
    const step = TOUR_STEPS[tourCurrentStep];
    if (step && step.onLeave) step.onLeave('next');

    if (tourCurrentStep >= TOUR_STEPS.length - 1) {
        closeTour(true);
        return;
    }
    tourCurrentStep++;
    renderTourStep(tourCurrentStep);
}

function tourPrev() {
    if (!tourActive || tourCurrentStep <= 0) return;
    const step = TOUR_STEPS[tourCurrentStep];
    if (step && step.onLeave) step.onLeave('back');
    tourCurrentStep--;
    renderTourStep(tourCurrentStep);
}

function jumpToTourStep(index) {
    if (!tourActive) return;
    const step = TOUR_STEPS[tourCurrentStep];
    if (step && step.onLeave) step.onLeave('jump');
    tourCurrentStep = index;
    renderTourStep(tourCurrentStep);
}

function closeTour(markComplete = false) {
    tourActive = false;

    const backdrop = document.getElementById('onboarding-backdrop');
    const card = document.getElementById('onboarding-card');
    const highlight = document.getElementById('onboarding-highlight');

    if (backdrop) {
        backdrop.classList.remove('visible');
        setTimeout(() => backdrop.classList.add('hidden'), 400);
    }
    if (card) {
        card.classList.remove('visible');
        card.classList.add('tour-hidden');
    }
    if (highlight) {
        highlight.classList.add('hidden');
    }

    if (markComplete) {
        localStorage.setItem('rad-onboarding-seen', 'true');
    }
}

function handleTourKeydown(e) {
    if (!tourActive) return;
    if (e.key === 'Escape') closeTour();
    if (e.key === 'ArrowRight') tourNext();
    if (e.key === 'ArrowLeft') tourPrev();
}
