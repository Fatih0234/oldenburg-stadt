---

version: alpha
name: Rad-Verbesserer Oldenburg
description: A playful, smart, map-first civic intelligence design system for a cycling infrastructure dashboard in Oldenburg. Designed to feel youthful, energetic, and interactive while remaining credible for city planners, administrations, and cycling advocates.
colors:

# Brand Core

primary: "#00C48C"
on-primary: "#052E23"
primary-soft: "#DDFBEF"
primary-glow: "rgba(0, 196, 140, 0.28)"

secondary: "#2F8CFF"
on-secondary: "#061B33"
secondary-soft: "#E2F0FF"
secondary-glow: "rgba(47, 140, 255, 0.26)"

tertiary: "#FF6B5F"
on-tertiary: "#3B0905"
tertiary-soft: "#FFE5E1"
tertiary-glow: "rgba(255, 107, 95, 0.28)"

accent-sun: "#FFC857"
accent-lilac: "#A78BFA"
accent-lime: "#A3E635"

# Light Theme

background: "#F6F8F3"
on-background: "#17211D"
surface: "#FFFFFF"
surface-soft: "#F0F6F1"
surface-raised: "#FFFFFF"
surface-map: "#EAF1EC"
on-surface: "#17211D"
on-surface-muted: "#60736A"
on-surface-subtle: "#889991"
outline: "#C9D8D0"
outline-strong: "#91A79D"

# Dark Theme

background-dark: "#08131A"
on-background-dark: "#ECF7F2"
surface-dark: "#101C24"
surface-soft-dark: "#152832"
surface-raised-dark: "#1B303B"
surface-map-dark: "#071015"
on-surface-dark: "#ECF7F2"
on-surface-muted-dark: "#A7BBB2"
on-surface-subtle-dark: "#748982"
outline-dark: "#2D4651"
outline-strong-dark: "#4F6F78"

# Map & Data

route-cycle: "#00C48C"
route-cycle-secondary: "#2F8CFF"
route-selected: "#FFDD66"
map-water: "#B8E7F6"
map-park: "#DDF6DA"
map-road: "#FFFFFF"
map-road-dark: "#15242D"

# Severity / Classification

confirmed: "#F05252"
confirmed-soft: "#FFE0E0"
confirmed-muted: "#B94747"
confirmed-glow: "rgba(240, 82, 82, 0.32)"

likely: "#FF8A3D"
likely-soft: "#FFE8D8"
likely-muted: "#BD6428"
likely-glow: "rgba(255, 138, 61, 0.3)"

possible: "#F7C948"
possible-soft: "#FFF5C7"
possible-muted: "#A77A12"
possible-glow: "rgba(247, 201, 72, 0.28)"

generic: "#7A8A99"
generic-soft: "#E7ECEF"
generic-muted: "#5C6B78"
generic-glow: "rgba(122, 138, 153, 0.18)"

# UI Utility

success: "#00C48C"
warning: "#F7C948"
error: "#F05252"
info: "#2F8CFF"
focus-ring: "#2F8CFF"
shadow-soft: "rgba(20, 46, 35, 0.12)"
shadow-float: "rgba(20, 46, 35, 0.18)"
shadow-dark: "rgba(0, 0, 0, 0.38)"

typography:
display-hero:
fontFamily: Space Grotesk
fontSize: 34px
fontWeight: 700
lineHeight: 1.02
letterSpacing: -0.04em
display-metric:
fontFamily: Space Grotesk
fontSize: 32px
fontWeight: 700
lineHeight: 1
letterSpacing: -0.035em
headline-lg:
fontFamily: Space Grotesk
fontSize: 24px
fontWeight: 700
lineHeight: 1.12
letterSpacing: -0.025em
headline-md:
fontFamily: Space Grotesk
fontSize: 19px
fontWeight: 700
lineHeight: 1.2
letterSpacing: -0.015em
headline-sm:
fontFamily: Space Grotesk
fontSize: 16px
fontWeight: 700
lineHeight: 1.25
letterSpacing: -0.01em
body-lg:
fontFamily: Inter
fontSize: 15px
fontWeight: 400
lineHeight: 1.55
body-md:
fontFamily: Inter
fontSize: 13px
fontWeight: 400
lineHeight: 1.5
body-bold:
fontFamily: Inter
fontSize: 13px
fontWeight: 650
lineHeight: 1.35
label-caps:
fontFamily: Inter
fontSize: 10px
fontWeight: 800
lineHeight: 1
letterSpacing: 0.11em
caption:
fontFamily: Inter
fontSize: 11px
fontWeight: 500
lineHeight: 1.35
data-mono:
fontFamily: IBM Plex Mono
fontSize: 12px
fontWeight: 600
lineHeight: 1.25
nav-label:
fontFamily: Inter
fontSize: 12px
fontWeight: 700
lineHeight: 1.1

rounded:
xs: 6px
sm: 10px
md: 14px
lg: 20px
xl: 28px
xxl: 36px
full: 9999px

spacing:
unit: 4px
xxs: 4px
xs: 8px
sm: 12px
md: 16px
lg: 24px
xl: 32px
xxl: 48px
sidebar-width: 424px
detail-panel-width: 400px
map-control-gap: 12px
panel-padding: 18px
card-padding: 16px
mobile-gutter: 14px

components:
button-primary:
backgroundColor: "{colors.primary}"
textColor: "{colors.on-primary}"
typography: "{typography.body-bold}"
rounded: "{rounded.full}"
padding: 12px
height: 42px
button-primary-hover:
backgroundColor: "{colors.accent-sun}"
textColor: "{colors.on-tertiary}"
button-secondary:
backgroundColor: "{colors.surface-raised}"
textColor: "{colors.on-surface}"
typography: "{typography.body-bold}"
rounded: "{rounded.full}"
padding: 12px
height: 42px
button-secondary-dark:
backgroundColor: "{colors.surface-raised-dark}"
textColor: "{colors.on-surface-dark}"
typography: "{typography.body-bold}"
rounded: "{rounded.full}"
padding: 12px
height: 42px
card-briefing:
backgroundColor: "{colors.surface-raised}"
textColor: "{colors.on-surface}"
rounded: "{rounded.xl}"
padding: 18px
card-briefing-dark:
backgroundColor: "{colors.surface-raised-dark}"
textColor: "{colors.on-surface-dark}"
rounded: "{rounded.xl}"
padding: 18px
card-filter:
backgroundColor: "{colors.surface}"
textColor: "{colors.on-surface}"
rounded: "{rounded.lg}"
padding: 14px
issue-row:
backgroundColor: "{colors.surface-raised}"
textColor: "{colors.on-surface}"
typography: "{typography.body-md}"
rounded: "{rounded.lg}"
padding: 14px
detail-panel:
backgroundColor: "{colors.surface-raised}"
textColor: "{colors.on-surface}"
rounded: "{rounded.xl}"
padding: 20px
marker-pin:
backgroundColor: "{colors.primary}"
textColor: "{colors.on-primary}"
rounded: "{rounded.full}"
size: 34px
chip-active:
backgroundColor: "{colors.primary-soft}"
textColor: "{colors.on-primary}"
typography: "{typography.caption}"
rounded: "{rounded.full}"
padding: 8px
------------

## Overview

Rad-Verbesserer Oldenburg is a playful civic intelligence interface for discovering, understanding, and prioritizing cycling infrastructure issues across the city.

The product should feel like a living urban map rather than a static municipal dashboard. It is designed for a mixed audience: city planners and administrations should feel that the tool is credible and evidence-based, while younger citizens and cycling advocates should feel that the interface is approachable, energetic, and worth exploring.

The design personality is:

* playful but not childish
* smart but not cold
* friendly but not casual
* urban but not gritty
* energetic but not chaotic
* premium but not corporate
* experimental but still usable

The interface should make the city feel alive. Movement, hover states, animated route proximity, and map-focused transitions are part of the identity. The UI should avoid looking like generic SaaS, police/security software, or crypto dashboards.

The core metaphor is **a friendly civic radar for cycling safety**: the map detects weak spots, the briefing tells the story, and the selected issue panel explains why a report matters.

## Colors

The color system should be colorful but controlled. Rad-Verbesserer Oldenburg should not be dominated by a single brand color. Instead, it uses a neutral civic map foundation with energetic accents.

The palette has three layers:

1. **Civic Neutral Base**
   Soft off-white, warm gray-green, and deep blue-green surfaces keep the interface trustworthy and readable. These colors prevent the product from becoming too childish or visually noisy.

2. **Energetic Brand Accents**
   Mint, sky blue, coral, and sun yellow create the youthful, playful character. These accents are used for motion, highlights, onboarding, active states, and moments of discovery.

3. **Functional Data Colors**
   Severity colors are intentionally less loud by default and become more expressive only during focus, hover, or selection. This keeps the map readable while preserving the meaning of confirmed, likely, possible, and generic issues.

Green should mostly represent cycling infrastructure and positive movement. It should not be the only brand color. Blue represents spatial intelligence and navigation. Coral adds human urgency and energy. Yellow is used for route focus, optimism, and selected-path illumination.

### Light Theme

The light theme is the public daytime version. It should feel optimistic, civic, airy, and approachable. Use a soft map canvas, white raised cards, rounded panels, and colorful but restrained accent moments.

### Dark Theme

The dark theme is the exploration/night version. It should feel like an energetic cycling radar, but not like police surveillance or cyber-security software. Avoid black-heavy interfaces. Use deep blue-green surfaces, glowing route lines, and soft neon accents only around active map states.

### Severity Colors

Severity color should communicate importance without overwhelming the whole interface.

* Confirmed issues use red/coral, but only selected or urgent states should glow.
* Likely issues use orange, but remain softer in default state.
* Possible issues use yellow as a warm check-case signal.
* Generic issues use muted slate and should visually recede.

Severity should never replace hierarchy. The selected issue, current map focus, and user task should determine what is most visible.

## Typography

The typography should feel modern, youthful, and precise.

Use **Space Grotesk** for the logo, section headlines, briefing cards, and large metrics. It gives the interface a friendly technical character without feeling corporate.

Use **Inter** for body text, labels, issue descriptions, filters, and dense UI content. It remains readable in compact dashboard contexts.

Use **IBM Plex Mono** only for small data details such as IDs, coordinates, score breakdowns, distances, and timestamps. Do not overuse monospace typography, because too much of it can make the product feel like an engineering console.

Typography should be expressive in the briefing area and calmer in the issue list. Avoid all-caps overuse. HUD-style labels are allowed, but they should feel like friendly wayfinding, not military interface language.

## Layout

The interface uses a **Map-First Civic Storytelling Layout**.

The map is the main stage. Side panels support the investigation but should not feel like they dominate the city. The layout should preserve the existing structure:

* left sidebar for briefing, filters, and guided investigation
* central map for exploration
* right detail panel for selected issue evidence
* floating controls for heatmap, theme, and map actions

The left sidebar should combine three roles:

1. **Monthly briefing** — what changed and what matters now
2. **Investigation control** — filters, search, and AI relevance
3. **Story guide** — cards that can zoom or fly the map to meaningful places

The right detail panel should feel like an **evidence dossier**, not a generic data drawer. It should explain:

* what happened
* where it happened
* why it matters for cyclists
* how AI classified it
* how close it is to cycling infrastructure
* what a planner or advocate can do next

On desktop, panels may float slightly above the map with visible spacing. On mobile, the sidebar becomes a bottom or full-screen sheet, and the selected issue panel becomes a bottom-anchored card.

The design should support playful spatial transitions:

* monthly briefing card zooms to a hotspot
* selected marker opens an evidence panel
* route proximity line connects issue to nearest cycling path
* filters visibly update the map

## Elevation & Depth

Depth should be created through **soft civic layering**, not heavy glassmorphism.

Use gentle shadows, tonal surfaces, and thin borders. Cards should feel tangible and touchable, almost like soft map labels or civic information stickers placed above the city.

Avoid excessive blur and transparent glass effects. The current design leans too much toward command-center glassmorphism; the redesign should be warmer and more physical.

Recommended depth levels:

1. **Map Canvas**
   Soft, low-contrast geographic foundation. It should never fight with markers or route overlays.

2. **Civic Panels**
   Sidebar and detail panels use raised surfaces with rounded edges and soft shadows. They should feel stable and trustworthy.

3. **Interactive Cards**
   Briefing cards, filter cards, and issue rows lift slightly on hover. Use small translation, scale, and shadow changes.

4. **Focus Elements**
   Selected markers, selected routes, and active issue panels can use glow and animation. These are the only places where stronger visual effects should appear.

5. **Motion Layers**
   Route proximity lines, map zoom/fly transitions, and score animations should create delight without adding clutter.

## Shapes

The shape language is rounded, friendly, and tactile.

Use large radii for major panels and moderate radii for cards. This supports the friendly citizen-map direction. Avoid sharp enterprise-dashboard geometry.

* Major panels: 24–28px radius
* Briefing cards: 20–24px radius
* Filter cards: 16–20px radius
* Inputs and buttons: pill or 14–18px radius
* Markers and chips: fully rounded
* Small tags: pill-shaped

Do not mix very sharp rectangles with very rounded cards in the same area. Consistency matters because the product already has many UI elements.

## Components

### Logo

The logo should be animated and characterful.

Preferred direction: a small cyclist or bicycle icon moving through a simplified city-map scene, with a radar pulse or route trail forming the project's identity. The logo may animate briefly on app load, then settle into a compact static mark.

Logo animation should be lightweight SVG or CSS animation, not a heavy video. It should suggest movement, cycling, and urban discovery. Avoid mascots that feel childish.

Possible logo behavior:

* cyclist moves along a curved route line
* small radar pulse expands from the bike
* route dots appear behind it
* the wordmark slides or fades in after the bike arrives

### Map

The map should be visually beautiful within the first five seconds. This is the primary wow moment.

The base map should be minimal and neutral. Roads, parks, and water should stay quiet. Cycling routes, issue markers, selected routes, and hotspots carry the visual energy.

Use:

* muted base map
* colorful cycling route overlays
* animated selected route proximity line
* soft marker pulses
* hover previews
* cluster expansion motion
* heatmap as a smooth mode shift, not just a layer toggle

Map controls should feel like friendly floating tools, not default GIS controls.

### Markers

Markers should be expressive but disciplined.

Default markers:

* circular or rounded badge style
* severity-colored rim
* white or dark center depending on theme
* small category icon or minimal symbol
* no excessive emojis

Hover state:

* marker lifts slightly
* rim brightens
* small tooltip appears
* route proximity preview may appear if available

Selected state:

* marker becomes larger
* concentric pulse appears
* nearest cycling route highlights
* detail panel opens smoothly
* map optionally draws a subtle connector/path from issue to route

### Monthly Briefing Cards

Monthly briefing cards are not just stats. They are entry points into the story of the city.

Each briefing card should:

* have a strong metric
* include a short narrative label
* feel clickable
* animate on hover
* fly or zoom the map to the relevant area when clicked
* briefly highlight affected markers/routes

The briefing section should feel like a civic news digest, not a KPI block.

### Sidebar Filters

Filters should be playful and tactile, but still efficient.

Filter cards should use:

* soft raised surfaces
* icon or visual severity strip
* animated active states
* count changes with number animation
* visible map feedback after click

When a filter is active, the related markers on the map should feel more present while inactive categories gently fade.

### Issue Stream

The issue list should feel like a live civic feed.

Each issue row should include:

* category symbol
* short title or category
* issue ID
* distance to cycling path
* status
* severity
* short citizen description

Hovering an issue row should preview its marker on the map. Clicking it should open the evidence dossier and fly the map smoothly.

Rows should avoid clutter. Use progressive disclosure: show enough to choose, then let the detail panel explain.

### Detail Panel

The selected issue panel should feel like an evidence dossier for planners and advocates.

It should include:

* severity badge
* issue title/category
* citizen report quote
* AI classification explanation
* relevance score
* score breakdown
* nearest route/segment
* satellite or street context
* Google Maps and Street View actions

The panel should open with a smooth slide/fade from the right. The selected score may count up from 0 to its final value. The route proximity line may animate at the same time.

The panel should make the user feel: “I understand why this issue matters.”

### Relevance Score

The relevance score should not feel like a game score that trivializes safety. It should feel like an evidence confidence indicator.

Use:

* animated count-up
* radial or vertical progress treatment
* itemized signal breakdown
* softer colors unless score is selected
* clear German explanation

Avoid making the score look like a leaderboard.

### Buttons and Actions

Primary buttons are rounded and energetic. They should feel like clear next actions.

Examples:

* “Zur Karte springen”
* “Hotspot anzeigen”
* “Route prüfen”
* “Street View öffnen”
* “Filter anwenden”
* “Tour starten”

Use one primary action per panel. Secondary actions remain quieter.

### Onboarding

The onboarding tour should feel like a guided city ride.

Tone:

* friendly
* short
* visual
* map-connected
* not childish

Avoid long explanations. Each onboarding step should spotlight one thing and show what the user can do next.

## Do's and Don'ts

### Do

* Do make the map beautiful and alive within the first five seconds.
* Do use playful motion to show cause and effect.
* Do keep city planners and administrations comfortable through strong hierarchy, evidence clarity, and accessibility.
* Do make the monthly briefing feel like a civic story, not just statistics.
* Do use SVG for logo animation, route trails, proximity lines, and lightweight illustration.
* Do reserve strong glow effects for selected markers, active routes, and focus states.
* Do keep German UI copy clear, short, and action-oriented.
* Do support both light and dark themes as equally polished but emotionally different experiences.
* Do provide reduced-motion alternatives for all animations.
* Do keep severity colors meaningful but less loud until selected or focused.

### Don't

* Don't make the product look like a generic SaaS dashboard.
* Don't make it look like police, surveillance, cyber-security, or military software.
* Don't make it look like a crypto dashboard.
* Don't overuse glassmorphism.
* Don't rely on too many emojis.
* Don't make the UI childish even though it is playful.
* Don't use animation that hides important data or delays user tasks.
* Don't let brand colors compete with severity colors.
* Don't make green the entire brand; reserve it mainly for cycling infrastructure and positive movement.
* Don't make every card glow or bounce.
* Don't sacrifice contrast or readability for visual excitement.

### Motion Principles

Motion is part of the Rad-Verbesserer identity.

Use motion to explain spatial relationships:

* a briefing card zooms to a hotspot
* a selected issue draws a route proximity line
* filter changes ripple into marker visibility
* the detail panel opens as the marker becomes active
* score values count up only when they enter focus

Motion should be fast, responsive, and lightweight.

Recommended timings:

* hover microinteraction: 120–180ms
* card selection: 180–240ms
* panel open/close: 260–360ms
* map focus/fly transition: 700–1100ms
* score count-up: 600–900ms
* logo intro: 1200–1800ms maximum

Use easing that feels springy but controlled:

* default: cubic-bezier(0.2, 0.8, 0.2, 1)
* playful: cubic-bezier(0.34, 1.56, 0.64, 1)
* map movement: ease-out or native map easing

Respect reduced motion:

* replace fly/zoom with shorter pan or instant focus
* disable repeated pulsing
* keep hover states color/outline-based
* avoid animated score count-up when reduced motion is enabled

### SVG & Illustration

Use SVGs as a major part of the redesign.

Best SVG opportunities:

* animated Rad-Verbesserer cyclist logo
* route trail line
* radar pulse
* small city skyline or street grid motif
* empty states
* onboarding illustrations
* severity icons
* proximity line between report and cycling route

SVG style should be geometric, friendly, and simple. Avoid detailed cartoons. The illustration system should feel like an urban map sticker set.
