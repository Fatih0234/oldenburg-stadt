// Global State variables
let map;
let geojsonLayer;
let markerLayerGroup;
let activeFilter = 'all'; // 'all', 'cycling-only', or specific label
let timeFilter = 'all'; // 'all', '7d', '30d', '90d', 'custom'
let customStartDate = null;
let customEndDate = null;
let currentSlideIndex = 0;

const SUBCATEGORY_NAMES = {
    'pothole_damage': 'Schlagloch / Fahrbahnschaden 🕳️',
    'glass_debris': 'Scherben / Verschmutzung 🧹',
    'vegetation_block': 'Überhängendes Grün / Äste 🌿',
    'illegal_parking_obstruction': 'Falschparker / Hindernis 🚗',
    'signal_light_timing': 'Ampelschaltung / Sensor 🚦',
    'crossing_safety': 'Gefährliche Kreuzung ⚠️',
    'signage_detours': 'Wegweisung / Umleitung 🪧',
    'bike_parking': 'Fahrradständer 🚲',
    'other_cycling': 'Sonstiges Radthema 🚴',
    'unrelated': 'Nicht radspezifisch ⚪'
};

// Initialize when DOM content is loaded
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    updateStats();
    initMap();
    renderIssueList();
    generateNewsletter();
    generateSocialAssets();
});

// 1. Sidebar Tabs Navigation
function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    const panels = document.querySelectorAll('.tab-panel');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const targetPanel = document.getElementById(`panel-${tab.dataset.tab}`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });

    // Preview tabs in Newsletter panel
    const previewTabs = document.querySelectorAll('.preview-tab');
    const renderedPreview = document.getElementById('newsletter-rendered');
    const markdownPreview = document.getElementById('newsletter-markdown');

    previewTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            previewTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            if (tab.dataset.format === 'rendered') {
                renderedPreview.classList.remove('hidden');
                markdownPreview.classList.add('hidden');
            } else {
                renderedPreview.classList.add('hidden');
                markdownPreview.classList.remove('hidden');
            }
        });
    });
}

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

    // Initialize Marker Layer Group for Reports
    markerLayerGroup = L.layerGroup().addTo(map);
    updateMapMarkers();
}

// 4. Update Markers on Map Based on Current Filters
function updateMapMarkers() {
    markerLayerGroup.clearLayers();

    const filtered = getFilteredReports();
    
    filtered.forEach(report => {
        if (!report.latitude || !report.longitude) return;

        const markerClass = getMarkerPinClass(report.cyclist_impact_label);
        const markerIcon = L.divIcon({
            className: 'custom-div-icon',
            html: `<div class="marker-pin ${markerClass}"></div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });

        const marker = L.marker([report.latitude, report.longitude], {
            icon: markerIcon
        });

        // Click handler to open floating details overlay
        marker.on('click', () => {
            showMapDetails(report);
            map.setView([report.latitude, report.longitude], 16);
        });

        markerLayerGroup.addLayer(marker);
    });
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
        if (activeFilter === 'cycling-only') {
            reports = reports.filter(r => 
                r.cyclist_impact_label === 'Confirmed cycling issue' || 
                r.cyclist_impact_label === 'Likely cycling issue'
            );
        } else if (activeFilter !== 'all') {
            reports = reports.filter(r => r.cyclist_impact_label === activeFilter);
        }
    }
    
    return reports;
}

function getFilteredReports() {
    return getTimeFilteredReports(false);
}

function filterByConfidence(label) {
    activeFilter = label;
    
    // Update active filter pills styling
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.metric-card').forEach(c => c.classList.remove('active'));
    
    // Add active state to clicked metric card
    let cardClass = '';
    if (label === 'Confirmed cycling issue') cardClass = '.gradient-confirmed';
    else if (label === 'Likely cycling issue') cardClass = '.gradient-likely';
    else if (label === 'Possibly affects cyclists') cardClass = '.gradient-possible';
    else if (label === 'Not cycling-specific') cardClass = '.gradient-generic';
    
    if (cardClass) {
        const card = document.querySelector(cardClass);
        if (card) card.classList.add('active');
    }
    
    renderIssueList();
    updateMapMarkers();
}

function clearFilters() {
    activeFilter = 'all';
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.metric-card').forEach(c => c.classList.remove('active'));
    document.getElementById('pill-all').classList.add('active');
    
    renderIssueList();
    updateMapMarkers();
}

function filterCyclingOnly() {
    activeFilter = 'cycling-only';
    document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.metric-card').forEach(c => c.classList.remove('active'));
    document.getElementById('pill-cycling-only').classList.add('active');
    
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
    generateNewsletter();
    generateSocialAssets();
}

function handleCustomDateChange() {
    customStartDate = document.getElementById('start-date').value;
    customEndDate = document.getElementById('end-date').value;
    
    updateStats();
    renderIssueList();
    updateMapMarkers();
    generateNewsletter();
    generateSocialAssets();
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
        card.className = 'issue-row';
        card.innerHTML = `
            <div class="issue-row-header">
                <span class="issue-cat">
                    <span class="dot" style="background-color: ${color}"></span>
                    ${r.categoryName}
                </span>
                <span class="issue-dist-tag">${r.distance_to_bike_path_meters}m to path</span>
            </div>
            <p class="issue-snippet">${r.replacingText || 'Keine Beschreibung vorhanden.'}</p>
            <div class="issue-meta">
                <span>ID: #${r.id} | ${stateEmoji} ${r.state}</span>
                <span>${formattedDate}</span>
            </div>
        `;

        card.addEventListener('click', () => {
            showMapDetails(r);
            if (r.latitude && r.longitude) {
                map.setView([r.latitude, r.longitude], 16);
            }
        });

        listContainer.appendChild(card);
    });
}

// 7. Floating Details Overlay Control
function showMapDetails(report) {
    const overlay = document.getElementById('map-details-card');
    
    document.getElementById('overlay-label').textContent = report.cyclist_impact_label;
    document.getElementById('overlay-label').className = `badge`;
    document.getElementById('overlay-label').style.backgroundColor = getLabelColor(report.cyclist_impact_label);
    document.getElementById('overlay-label').style.color = '#fff';
    
    document.getElementById('overlay-category').textContent = report.categoryName;
    
    const dateObj = new Date(report.createdAt);
    document.getElementById('overlay-date').textContent = `Gemeldet am: ${dateObj.toLocaleString('de-DE')}`;
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
            <div class="llm-info-box card-glass" style="margin-top: 12px; margin-bottom: 12px; padding: 10px; border-left: 3px solid ${borderColor}; background: ${bgColor}; border-radius: 4px;">
                <div style="font-weight: 600; font-size: 0.85rem; color: ${titleColor}; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    🤖 <span>KI-Klassifizierung: ${subcatPretty}</span>
                </div>
                <div style="font-style: italic; font-size: 0.85rem; color: #cbd5e1;">"${report.explanation_de}"</div>
            </div>
        `;
    } else {
        llmBox.innerHTML = '';
    }

    // Stats grid
    const statsGrid = document.getElementById('overlay-stats-grid');
    let penaltyHtml = '';
    if (report.score_penalty && report.score_penalty < 0) {
        penaltyHtml = `<div class="stat-item">LLM Penalty: <span style="color: #ef4444">${report.score_penalty}</span></div>`;
    }
    
    statsGrid.innerHTML = `
        <div class="stat-item">Relevance Score: <span>${report.confidence_score} pts</span></div>
        <div class="stat-item">Distance to path: <span>${report.distance_to_bike_path_meters} m</span></div>
        <div class="stat-item">Category Bonus: <span>+${report.score_category}</span></div>
        <div class="stat-item">Path Distance: <span>+${report.score_distance}</span></div>
        <div class="stat-item">LLM Match: <span>+${report.score_keywords}</span></div>
        ${penaltyHtml}
        <div class="stat-item">Status / Recency: <span>${report.score_state + report.score_recency}</span></div>
    `;
    
    if (report.nearest_segment_name) {
        statsGrid.innerHTML += `<div class="stat-item" style="grid-column: span 2">Nearest Segment: <span style="word-break: break-all;">${report.nearest_segment_name}</span></div>`;
    }

    // Image loading
    const imgContainer = document.getElementById('overlay-image-container');
    const img = document.getElementById('overlay-image');
    if (report.firstPictureUrl) {
        img.src = report.firstPictureUrl;
        imgContainer.classList.remove('hidden');
    } else {
        imgContainer.classList.add('hidden');
    }
    
    // Google Maps link
    document.getElementById('overlay-direction-link').href = `https://www.google.com/maps/search/?api=1&query=${report.latitude},${report.longitude}`;

    overlay.classList.remove('hidden');
}

function hideMapDetails() {
    document.getElementById('map-details-card').classList.add('hidden');
}

// 8. Weekly Newsletter Auto-Generator
function generateNewsletter() {
    const timeFiltered = getTimeFilteredReports(true);
    
    // Filter active issues only (OPEN or IN_PROCESS)
    const activeReports = timeFiltered.filter(r => r.state === 'OPEN' || r.state === 'IN_PROCESS');
    
    // Filter by cyclist impact level
    const confirmed = activeReports.filter(r => r.cyclist_impact_label === 'Confirmed cycling issue');
    const likely = activeReports.filter(r => r.cyclist_impact_label === 'Likely cycling issue');
    const resolved = timeFiltered.filter(r => r.state === 'CLOSED' && r.cyclist_impact_label !== 'Not cycling-specific');
    
    const countConfirmed = confirmed.length;
    const countLikely = likely.length;
    const countResolved = resolved.length;

    // Build the newsletter text (Markdown format)
    let md = `# 🚲 Wöchentlicher Radweg-Gesundheitsbericht Oldenburg\n`;
    md += `*Ausgabe vom ${new Date().toLocaleDateString('de-DE', { day: '2-digit', month: 'long', year: 'numeric' })}*\n\n`;
    md += `Moin liebe Radelnde in Oldenburg!\n\n`;
    md += `Willkommen zur neuesten Ausgabe unseres Gesundheitsberichts für Oldenburger Radwege. Diese Woche haben wir die aktuellsten Tickets aus der städtischen Mängelplattform *Stadtverbesserer* analysiert und mit dem OpenStreetMap-Radnetz abgeglichen.\n\n`;
    
    md += `### 📊 Die Lage auf den Straßen\n`;
    md += `* **Kritische Radwegmängel (Bestätigt):** \`${countConfirmed}\` aktive Probleme 🚨\n`;
    md += `* **Wahrscheinliche Beeinträchtigungen:** \`${countLikely}\` Meldungen nahe Radwegen 🚧\n`;
    md += `* **Gelöste Probleme der letzten Zeit:** \`${countResolved}\` behobene Mängel 🎉\n\n`;
    
    md += `---\n\n`;
    
    md += `## 🚨 Top 3 Kritische Mängel auf Radwegen\n`;
    if (confirmed.length > 0) {
        // Take top 3 confirmed sorted by score descending
        const top3 = confirmed.sort((a, b) => b.confidence_score - a.confidence_score).slice(0, 3);
        top3.forEach((r, idx) => {
            const streetName = r.nearest_segment_name ? ` auf der ${r.nearest_segment_name}` : '';
            md += `### ${idx+1}. ${r.categoryName}${streetName} (ID: #${r.id})\n`;
            md += `* **Beschreibung:** "${r.replacingText}"\n`;
            md += `* **Distanz zum Radweg:** ${r.distance_to_bike_path_meters} Meter\n`;
            md += `* **Standort:** [In Google Maps anzeigen](https://www.google.com/maps/search/?api=1&query=${r.latitude},${r.longitude}) | Relevanzscore: \`${r.confidence_score} pts\`\n\n`;
        });
    } else {
        md += `Glücklicherweise gibt es aktuell keine direkt als kritisch bestätigten Radweg-Mängel! 🌟\n\n`;
    }
    
    md += `---\n\n`;
    
    md += `## 🚧 Brennpunkte an Hauptverkehrsachsen (Watchlist)\n`;
    // Find active likely reports near named corridors
    const corridorReports = likely.filter(r => r.nearest_segment_name !== "").slice(0, 3);
    if (corridorReports.length > 0) {
        corridorReports.forEach(r => {
            md += `* **${r.nearest_segment_name} (${r.categoryName}):** ${r.replacingText.substring(0, 120)}... [#${r.id}] [Karte](https://www.google.com/maps/search/?api=1&query=${r.latitude},${r.longitude})\n`;
        });
    } else {
        md += `Keine akuten Meldungen auf unseren priorisierten Fahrradkorridoren diese Woche.\n`;
    }
    md += `\n---\n\n`;
    
    md += `## 🎉 Gelöst & Freie Fahrt\n`;
    if (resolved.length > 0) {
        const topResolved = resolved.slice(0, 2);
        topResolved.forEach(r => {
            md += `* **Behoben:** ${r.categoryName} nahe ${r.nearest_segment_name || "Radweg"} (ID: #${r.id}) - *"${r.replacingText.substring(0, 100)}..."*\n`;
        });
    } else {
        md += `Keine neu gelösten Radweg-Meldungen registriert.\n`;
    }
    
    md += `\n---\n\n`;
    md += `*Haben Sie einen Mangel entdeckt? Melden Sie ihn auf gemeinsam.oldenburg.de und unser System erfasst ihn automatisch. Bis zur nächsten Woche, gute und sichere Fahrt!* 🚴‍♀️💨`;

    // Render Preview HTML
    const renderedContainer = document.getElementById('newsletter-rendered');
    const mdContainer = document.getElementById('newsletter-markdown');
    
    mdContainer.textContent = md;
    
    // Line-by-line custom parser for preview formatting to prevent greedy list issues
    const lines = md.split('\n');
    let html = '';
    let inList = false;
    
    lines.forEach(line => {
        if (line.startsWith('* ')) {
            if (!inList) {
                html += '<ul>';
                inList = true;
            }
            let itemContent = line.substring(2);
            itemContent = parseInlineMarkdown(itemContent);
            html += `<li>${itemContent}</li>`;
        } else {
            if (inList) {
                html += '</ul>';
                inList = false;
            }
            
            if (line.startsWith('# ')) {
                html += `<h1>${parseInlineMarkdown(line.substring(2))}</h1>`;
            } else if (line.startsWith('## ')) {
                html += `<h2>${parseInlineMarkdown(line.substring(3))}</h2>`;
            } else if (line.startsWith('### ')) {
                html += `<h3>${parseInlineMarkdown(line.substring(4))}</h3>`;
            } else if (line.trim() === '---') {
                html += '<hr>';
            } else if (line.trim() === '') {
                // Empty line, ignore
            } else {
                html += `<p>${parseInlineMarkdown(line)}</p>`;
            }
        }
    });
    if (inList) {
        html += '</ul>';
    }
    
    renderedContainer.innerHTML = html;
}

function parseInlineMarkdown(text) {
    return text
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<span class="badge">$1</span>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
}

function copyNewsletterMarkup(format) {
    const text = document.getElementById('newsletter-markdown').textContent;
    navigator.clipboard.writeText(text).then(() => {
        alert("Markdown in die Zwischenablage kopiert!");
    }).catch(err => {
        console.error("Fehler beim Kopieren: ", err);
    });
}

// 9. Telegram & Instagram Social Media Generation
function generateSocialAssets() {
    const timeFiltered = getTimeFilteredReports(true);
    
    // A. Telegram Broadcast Template
    const activeReports = timeFiltered.filter(r => r.state === 'OPEN' || r.state === 'IN_PROCESS');
    const confirmedCount = activeReports.filter(r => r.cyclist_impact_label === 'Confirmed cycling issue').length;
    const likelyCount = activeReports.filter(r => r.cyclist_impact_label === 'Likely cycling issue').length;
    
    let tele = `🚴‍♂️ *Oldenburger Rad-Watchdog Update* 🚴‍♂️\n\n`;
    tele += `Dies ist der Radweg-Zustandbericht dieser Woche:\n\n`;
    tele += `📊 *Statistik:* \n`;
    tele += `🚨 *${confirmedCount}* bestätigte Radwegschäden\n`;
    tele += `🚧 *${likelyCount}* Behinderungen an Radachsen\n\n`;
    tele += `🔥 *Kritischste Baustelle diese Woche:*\n`;
    
    const topConfirmed = activeReports
        .filter(r => r.cyclist_impact_label === 'Confirmed cycling issue')
        .sort((a,b) => b.confidence_score - a.confidence_score)[0];
        
    if (topConfirmed) {
        tele += `📍 *${topConfirmed.nearest_segment_name || "Radweg"}* (${topConfirmed.categoryName})\n`;
        tele += `💬 "${topConfirmed.replacingText.substring(0, 110)}..."\n`;
        tele += `🔗 Koordinaten: ${topConfirmed.latitude.toFixed(4)}, ${topConfirmed.longitude.toFixed(4)}\n\n`;
    }
    
    tele += `Bleibt sicher auf den Rädern! Meldet Schäden unter gemeinsam.oldenburg.de. 👍`;
    document.getElementById('telegram-text').value = tele;

    // B. Instagram Slides Generation
    const track = document.getElementById('insta-carousel-track');
    track.innerHTML = ''; // Clear existing slides
    
    const slidesData = [
        {
            bg: 'slide-bg-grad1',
            title: 'OLDENBURG BIKE WATCH',
            bigStat: `🚨 ${confirmedCount}`,
            desc: 'Aktive kritische Radwegschäden in Oldenburg diese Woche gemeldet. Wie sicher fährst du?',
            footer: 'Wöchentlicher Report // @OldenburgRadeln'
        },
        {
            bg: 'slide-bg-grad2',
            title: 'BRENnPUNKT RADWEG',
            bigStat: topConfirmed ? `📍 #${topConfirmed.id}` : 'ALL CLEAR',
            desc: topConfirmed 
                ? `Schlagloch/Hindernis auf der ${topConfirmed.nearest_segment_name || "Hauptachse"}: "${topConfirmed.replacingText.substring(0, 90)}..."`
                : 'Diese Woche wurden keine akuten Schäden auf Fahrradwegen bestätigt.',
            footer: 'Top-Gefahrenstelle // Check die Karte'
        },
        {
            bg: 'slide-bg-grad3',
            title: 'WATCHLIST RADACHSEN',
            bigStat: `🚧 ${likelyCount}`,
            desc: 'Mängel wie blockiertes Grün, Ampelausfälle oder verstopfte Gullys an Haupt-Fahrradstraßen.',
            footer: 'Infrastruktur-Check // Bleib aufmerksam'
        },
        {
            bg: 'slide-bg-grad4',
            title: 'MELDE MIT & SORGE FÜR MEHR SICHERHEIT',
            bigStat: '🚴‍♀️✨',
            desc: 'Nutze das Oldenburger Stadtverbesserer-Portal! Jede Meldung füttert unseren Algorithmus für sicherere Straßen.',
            footer: 'Link in Bio // Rad-Watchdog Oldenburg'
        }
    ];

    slidesData.forEach((s, idx) => {
        const slide = document.createElement('div');
        slide.className = `carousel-slide ${s.bg}`;
        slide.innerHTML = `
            <div class="slide-header">
                <span class="slide-brand">RADWEG-REPORT</span>
                <span class="slide-number">Slide ${idx+1} / 4</span>
            </div>
            <div class="slide-body">
                <h2 class="slide-title">${s.title}</h2>
                <div class="slide-big-stat">${s.bigStat}</div>
                <p class="slide-desc">${s.desc}</p>
            </div>
            <div class="slide-footer">
                <span>${s.footer}</span>
                <span>Swipe ➔</span>
            </div>
        `;
        track.appendChild(slide);
    });

    currentSlideIndex = 0;
    updateCarouselPosition();
}

// Swipe slide navigations
function slideCarousel(direction) {
    currentSlideIndex += direction;
    if (currentSlideIndex < 0) currentSlideIndex = 0;
    if (currentSlideIndex > 3) currentSlideIndex = 3;
    
    updateCarouselPosition();
}

function updateCarouselPosition() {
    const track = document.getElementById('insta-carousel-track');
    const indicator = document.getElementById('carousel-indicator-text');
    
    track.style.transform = `translateX(-${currentSlideIndex * 25}%)`;
    indicator.textContent = `Slide ${currentSlideIndex + 1} / 4`;
}

// Copy text function for textareas
function copyText(id) {
    const textarea = document.getElementById(id);
    navigator.clipboard.writeText(textarea.value).then(() => {
        alert("Text in die Zwischenablage kopiert!");
    }).catch(err => {
        console.error("Fehler beim Kopieren: ", err);
        textarea.select();
        document.execCommand('copy');
        alert("Text in die Zwischenablage kopiert (Fallback)!");
    });
}
