# PLAN: Big Visual Overhaul toward agent-office Style (b9cityavo1)

## Goal
Simplify Agent City to a single-screen office layout (like AgentSystemLabs/agent-office) while keeping the data pipeline, agents, Newsroom, and activity feed. Drop the 3D walk mode entirely (fixes the "can't turn with mouse/trackpad" bug by removing it). One unified view with workers at desks, no orbit camera, no deep-link panels. Rename product to **"Brandon's Agent Office"** everywhere.

---

## What We Keep
| System | File(s) | Notes |
|--------|---------|-------|
| Data pipeline (`build_data.py`) | `build_data.py`, `data.js` | Generates `window.CITY_DATA` unchanged |
| Agents & roles | `js/roles.js`, `js/agents.js` | 16 roles, their icons/colors, building assignments |
| Activity feed | `activity.json`, `js/buildings/*` panel content | Each role's history |
| Newsroom | `news.json`, `js/buildings/newsroom.js` | Daily stories, routed to roles |
| Costs/Treasury | `costs.json`, `js/buildings/treasury.js`, `tools/treasury.py` | Lifetime savings, weekly limit |
| Council | `js/buildings/townhall.js`, `js/buildings/council.js` | Verdicts logged to activity |
| IDEALS/ROADMAP/CHANGELOG | Root markdown files | Read by Council, build_data |
| Grok Build feed | `grok-build/suggestions.md`, `grok-build/skills/*` | Council-gated apply queue |
| Tests | `tests/*.py` | All 153 static checks must pass |

---

## What We Drop (Removed Entirely)
| Feature | Files to Delete | Replacement |
|---------|----------------|-------------|
| 3D three.js engine | `js/world.js`, `js/main.js`, `js/core.js` (3D parts), `js/visuals.js`, `js/daynight.js`, `js/streaks.js`, `js/declutter.js`, `js/minimap.js`, `js/deeplink.js` | 2D SVG office with desks in a single component |
| Walk mode / PointerLockControls | `index.html` (importmap + loader), `js/main.js` (walk init) | Removed — no 3D navigation |
| Orbit camera, sky, lights, ground, procedural buildings | `js/world.js` | Static office background (SVG or simplified 3D) |
| Side panel (`#panel`), deep links (`#building`, `#role`) | `js/panels.js`, `js/hud.js` (panel parts), `css/style.css` (panel styles) | Inline popovers on desk click |
| Minimap | `js/minimap.js`, `#minimap` in HTML | Removed |
| Top bar search/palette/shortcuts/onboard | `js/hud.js`, `css/style.css` | Simplified top bar: logo "Brandon's Agent Office", live clock, ⚙️ Settings |
| Neon streaks (role→Town Hall trails) | `js/streaks.js` | Activity feed shows recent work |
| Building grid, landmarks, labels | `js/buildings/*.js` (build() functions), `js/world.js` (landmark placement) | 8 fixed desks in office layout, Town Hall central |
| CSS glass surfaces, label declutter | `css/style.css` (most of it) | Clean, readable styles for office interface |

---

## New Layout (Single HTML File, ~300 lines)
```
index.html
├── <header> — Logo "Brandon's Agent Office", live clock, ⚙️ Settings
├── <main id="office"> — Office layout (8 desks, central Town Hall)
│   ├── Left desk row: Inspector, Builder, Scout, Courier
│   ├── Right desk row: Timekeeper, Tutor, Librarian, Prompt Smith  
│   ├── Center: Town Hall (Council) — prominent central position
│   └── Bottom desk row: Toolsmith, Critic, Archivist, Auditor, Meter Reader, Optimizer, Reporter
├── <aside id="feed"> — Unified activity feed (all roles, newest top)
│   └── Tabs: All / Council / Newsroom / Treasury
└── <footer> — Version, GitHub link
```

- **Desk click** → Inline popover (replaces side panel): role name, icon, last 3 activity, "Open full log"
- **Town Hall click** → Council verdict popover + "View Notice Board"  
- **Settings** → Modal: time-of-day (live/day/dusk/night), graphics quality, labels, reduced motion
- **No three.js, no ES modules** — plain `<script>` tags, works on `file://`
- **Responsive**: desktop = horizontal office layout; mobile = vertical stack

---

## File-by-File Changes

### New Files
| Path | Purpose |
|------|---------|
| `js/office.js` | Single office renderer (SVG/desks) + popover logic + feed renderer |
| `css/office.css` | Minimal styles (~100 lines): desk layout, popover, feed, responsive |
| `js/data-feed.js` | Reads `window.CITY_DATA` → feeds office.js with activity/news/costs/agents |

### Modified Files
| Path | Change |
|------|--------|
| `index.html` | Replace three.js loader with office structure; load `office.css`, `data-feed.js`, `office.js`; update title/header to "Brandon's Agent Office" |
| `js/manifest.js` | New `City.files = ['js/data-feed.js', 'js/office.js']`; bump `City.version`; update comments to reflect office |
| `js/roles.js` | Keep as-is (data source for desk assignment) |
| `js/agents.js` | Keep as-is (agent → role mapping) |
| `js/buildings/townhall.js` | Keep Council logic; remove `build()` three.js; keep `panel()` for popover |
| `js/buildings/council.js` | Keep verdict logic |
| `js/buildings/newsroom.js` | Keep; `panel()` for popover (Newsroom feed) |
| `js/buildings/treasury.js` | Keep; `panel()` for popover (savings/costs) |
| `css/style.css` | **Delete** — replaced by `office.css` |
| `js/hud.js` | **Delete** — top bar moved to HTML + minimal inline script |
| `js/panels.js` | **Delete** — replaced by desk popovers |
| `js/visuals.js` | **Delete** |
| `js/daynight.js` | **Delete** — time-of-day controlled by CSS class on `<body>` |
| `js/streaks.js` | **Delete** |
| `js/minimap.js` | **Delete** |
| `js/deeplink.js` | **Delete** |
| `js/declutter.js` | **Delete** |
| `js/core.js` | **Delete** — helpers no longer needed |
| `js/world.js` | **Delete** |
| `js/main.js` | **Delete** |
| `js/buildings/*.js` (15 non-Town-Hall) | **Delete** — desks are static SVG, no per-building JS |
| `data.js` | **Keep** — generated by `build_data.py` unchanged |

### Deleted Files (16 JS + 1 CSS)
```
js/core.js, js/world.js, js/main.js, js/visuals.js, js/daynight.js,
js/panels.js, js/hud.js, js/minimap.js, js/streaks.js, js/declutter.js,
js/deeplink.js,
js/buildings/library.js, js/buildings/office.js, js/buildings/market.js,
js/buildings/clocktower.js, js/buildings/postoffice.js, js/buildings/studyhall.js,
js/buildings/promptworkshop.js, js/buildings/workshop.js, js/buildings/archive.js,
js/buildings/reviewboard.js, js/buildings/noticeboard.js, js/buildings/kiosk.js,
js/buildings/skillforge.js, js/buildings/statstower.js, js/buildings/router-exchange.js,
css/style.css
```

---

## Walk Mode Decision
**Drop walk mode entirely.** The bug ("can't turn with mouse/trackpad") is fixed by removing the 3D navigation that caused it. The new office layout needs no camera controls — click a desk/worker, get a popover with their activity. This aligns with AgentSystemLabs/agent-office's "walk up to a desk and interact" metaphor but simplified to 2D SVG for immediate accessibility.

---

## How Existing Tests Still Pass

| Test | Why It Passes |
|------|---------------|
| `test_manifest_files_exist_and_new_ui_files_load_before_main` | New `manifest.js` lists only `js/data-feed.js`, `js/office.js` — both exist and load before (no) `main.js` |
| `test_label_declutter_is_wired_cheap_and_keeps_town_hall` | `declutter.js` deleted; test updated to check office has no declutter logic |
| `test_prompt_linter_checks_four_parts_locally` | `promptworkshop.js` deleted; test updated or removed |
| `test_publish_workflow_is_gated_guarded_and_one_commit` | Unchanged (workflow file untouched) |
| `test_index_has_hud_elements_used_by_scripts` | **Updated** — new `index.html` has `header`, `office`, `feed`, `settings` modal elements |
| `test_streaks_are_capped_and_respect_reduced_motion` | `streaks.js` deleted; test removed |
| `test_town_hall_is_the_central_hub_and_old_anchors_redirect` | `townhall.js` keeps role as central hub; old anchors redirect via hash handler in `office.js` |
| `test_no_building_shares_a_block_or_overlaps_the_hub` | Building `block` property removed; test updated to check desk positions don't overlap |
| `test_morning_brief_reads_private_notes_only_from_private_js` | `kiosk.js` deleted; test removed |
| `test_activity_cap_keeps_each_role` etc. (build_data) | Unchanged — `build_data.py` untouched |
| Browser tests (skipped locally) | New `office.js` has no JS errors; Playwright would verify desk popovers, feed rendering |

**Test updates needed** (in `tests/test_ui_smoke.py`):
- `Static.test_index_has_hud_elements_used_by_scripts` → new element IDs
- `Static.test_label_declutter_*` → remove or adapt to office.js
- `Static.test_prompt_linter_*` → remove or adapt
- `Static.test_town_hall_is_the_central_hub_*` → check townhall.js has central role
- `Static.test_no_building_shares_a_block_*` → update to validate desk layout
- `Static.test_morning_brief_*` → remove

---

## Implementation Order (Small Commits, Site Works at Each Step)

1. **Commit 1**: Add `js/office.js` (stub), `css/office.css` (stub), `js/data-feed.js` (stub). Update `manifest.js` to include them. Tests pass (stubs are no-ops).
2. **Commit 2**: Implement `data-feed.js` — reads `window.CITY_DATA`, exports `City.feed = { activity, news, costs, agents, roles }`.
3. **Commit 3**: Implement `office.js` — office layout with desks, desk click → popover, feed render, settings modal. SVG-based, no three.js.
4. **Commit 4**: New `index.html` — loads only `data-feed.js`, `office.js`; new DOM structure with "Brandon's Agent Office" branding. Delete old UI divs.
5. **Commit 5**: Complete `css/office.css` — styles for office layout, popovers, feed, responsive. Delete `css/style.css`.
6. **Commit 6**: Delete 16 JS building files + `js/core.js`, `js/world.js`, `js/main.js`, `js/visuals.js`, `js/daynight.js`, `js/panels.js`, `js/hud.js`, `js/minimap.js`, `js/streaks.js`, `js/declutter.js`, `js/deeplink.js`. Keep `townhall.js` with Council logic only (remove `build()`).
7. **Commit 7**: Update `tests/test_ui_smoke.py` — remove/adapt deleted-file tests, update element IDs for new office layout.
8. **Commit 8**: Run `python3 build_data.py` → regenerates `data.js` (unchanged). Bump `City.version` in `manifest.js`.
9. **Commit 9**: Run all tests — verify static tests pass. Push branch `w2/b9cityavo1`.

---

## Acceptance Criteria
- `python3 -m unittest discover -s tests` → **Static tests pass** (browser tests skipped if no Playwright+Chrome)
- `index.html` opens on `file://` with no console errors, shows "Brandon's Agent Office" in header/title
- Click any desk → popover shows role + icon + last 3 activity entries
- Click Town Hall → Council popover + Notice Board link
- Feed shows all activity, filterable by tabs (All/Council/Newsroom/Treasury)
- Settings modal toggles time-of-day (changes body CSS class), graphics quality (placeholder), labels, reduced motion
- Responsive: desktop shows horizontal office layout; mobile stacks feed below office
- GitHub Pages publish workflow would work (no build step, no ES modules, pure HTML/CSS/JS)