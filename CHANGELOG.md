# Changelog — Rad-Verbesserer Oldenburg

All notable changes to the visual look & feel, branding, and sidebar layout.

---

## [Unreleased] — Visual & UI refresh

### 🎨 Theme & design system
- **New design system** — `DESIGN.md` (Rad-Verbesserer Oldenburg, alpha) is now the single source of truth for the visual language. Map-first, playful, smart, urban, premium-but-not-corporate.
- **Color palette reworked end-to-end**
  - Brand: emerald `#00C48C` (primary), friendly blue `#2F8CFF` (secondary), warm coral `#FF6B5F` (tertiary), sunny yellow / lilac / lime accents.
  - Light theme: soft green-tinted off-white background (`#F6F8F3`), white surfaces, sage outlines.
  - Dark theme: deep cool blue-black (`#08131A`), cool slate surfaces, warm sodium accents.
- **Typography upgraded**
  - Display: **Space Grotesk** (replaces Outfit — more confident, more character).
  - Body: **Inter**.
  - Data / numbers: **IBM Plex Mono** — gives the radar counts and metric chips a precise, instrumented feel.
- **Light + Dark + System** — theme picker now supports system mode in addition to explicit light/dark, persisted across sessions.
- **No more made-up logos / old PNG branding** — `assets/branding/logo.png` is no longer used in the sidebar. All logos are inlined SVG.

### 🛰️ Dynamic SVG logo (sidebar)
- The old static logo is gone. In its place sits an **inlined, animated SVG scene**:
  - A radar pulse in the center.
  - Two cyclists riding along a wavy road, looping continuously.
  - A trail of route dots fades behind them.
- **Dark-theme easter egg**: a warm sodium street-lamp head shines down from the top-left of the badge, casting a light cone and a glowing pool onto the road behind the riders. The cyclists brighten as they pass through the beam. Light theme is unchanged.
- Everything is plain inline SVG — no image assets, no external requests.

### 🧭 Sidebar redesign (more minimal)
- **Unified filter section** — Search, time window, and relevance are now one cohesive panel instead of three scattered blocks.
- **Confidence chips replace the 4 big metric cards** — same colors, same active-state sync, just compact pills. Frees up a lot of vertical space.
- **Issue stream promoted** — the live Meldungsstrom list now appears above the briefing so the most actionable content is closer to the eye line.
- **Briefing demoted** — the Monatsbriefing is now a collapsible section (collapsed by default), with a chevron and a smooth expand/collapse animation. Its open/closed state is remembered via `localStorage`.
- **Sticky bug fix** — the ARBEITSFILTER card no longer occludes the list header when scrolling. The filter scrolls with the content; users scroll back up to reach it.
- **Tour updated** — onboarding tour steps reordered to match the new layout, briefing auto-expands/collapses during the relevant step, cleanup runs reliably on every tour exit.

### 🗑️ Removed
- `assets/branding/logo.png` from the logo slot (replaced by inline SVG).
- Four oversized `.metric-card` blocks (replaced by confidence chips).
- Standalone "Search and Time Filters" + "Filter Matrix" sections (merged into a single filter panel).
- `transform`-based entrance animation on `.tab-panel` (was breaking sticky positioning for descendants).

### ✅ Unchanged
- Filter pipeline logic.
- Map behaviour, hero, and sidebar fold behaviour.
- Data layer (`fetch_reports.py`, `classified_reports.*`).

---

## Commits in this batch

| Commit      | Type     | Summary                                                                                  |
|-------------|----------|------------------------------------------------------------------------------------------|
| `3f37ffd`   | feat(ui) | Rework dashboard styling; add dark-theme street-light SVG logo; import new `svgs/` set   |
| `e62bc31`   | refactor | Unify sidebar filters; confidence chips; demote briefing; chevron + localStorage persist |
| `b9ca1c2`   | fix      | Stop ARBEITSFILTER from occluding list header; tour cleanup hardening                    |
