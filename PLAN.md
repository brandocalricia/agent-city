# PLAN: Big Visual Overhaul toward agent-virtual-office Style (b9cityavo1)

## Goal
Simplify Agent City to a single-screen, top-down pixel-art office (like KbWen/agent-virtual-office) while keeping the data pipeline, agents, Newsroom, and activity feed. Drop the 3D walk mode entirely (fixes the "can't turn with mouse/trackpad" bug by removing it). One unified view, no orbit camera, no deep-link panels.

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
| 3D three.js engine | `js/world.js`, `js/main.js`, `js/core.js` (3D parts), `js/visuals.js`, `js/daynight.js`, `js/streaks.js`, `js/declutter.js`, `js/minimap.js`, `js/deeplink.js` | 2D SVG office in a single component |
| Walk mode / PointerLockControls | `index.html` (importmap + loader), `js/main.js` (walk init) | Removed — no 3D navigation |
| Orbit camera, sky, lights, ground, procedural buildings | `js/world.js` | Static office SVG background |
| Side panel (`#panel`), deep links (`#building`, `#role`) | `js/panels.js`, `js/hud.js` (panel parts), `css/style.css` (panel styles) | Inline popovers on click |
| Minimap | `js/minimap.js`, `#minimap` in HTML | Removed |
| Top bar search/palette/shortcuts/onboard | `js/hud.js`, `css/style.css` | Simplified top bar: logo, time, settings only |
| Neon streaks (role→Town Hall trails) | `js/streaks.js` | Activity feed shows "work flying home" as list items |
| Building grid, landmarks, labels | `js/buildings/*.js` (build() functions), `js/world.js` (landmark placement) | 8 fixed desks in SVG office layout |
| CSS glass surfaces, label declutter | `css/style.css` (most of it) | Tailwind-like utility classes inline or tiny CSS |

---

## New Layout (Single HTML File, ~300 lines)
```
index.html
├── <header> — Logo "Agent City", live clock, ⚙️ Settings
├── <main id="office"> — SVG office (8 desks, central plaza = Town Hall)
│   ├── Desk: Inspector, Builder, Scout, Courier (left row)
│   ├── Desk: Timekeeper, Tutor, Librarian, Prompt Smith (right row)
│   ├── Center: Town Hall (Council) — larger, glows
│   └── Desk: Toolsmith, Critic, Archivist, Council, Auditor, Meter Reader, Optimizer, Reporter (bottom row)
├── <aside id="feed"> — Unified activity feed (all roles, newest top)
│   └── Tabs: All / Council / Newsroom / Treasury
└── <footer> — Version, GitHub link
```

- **Desk click** → Inline popover (replaces side panel): role name, icon, last 3 activity entries, "Open full log" link (hash `#activity?role=X`)
- **Town Hall click** → Council verdict popover + "View Notice Board"
- **Settings** → Modal: time-of-day (live/day/dusk/night), graphics (high/saver), labels on/off, reduced motion
- **No three.js, no ES modules** — plain `<script>` tags, works on `file://`
- **Responsive**: desktop = horizontal office; mobile = vertical stack (feed below office)

---

## File-by-File Changes

### New Files
| Path | Purpose |
|------|---------|
| `js/office.js` | Single SVG office renderer + popover logic + feed renderer |
| `css/office.css` | Minimal styles (~100 lines): grid/flex layout, popover, feed, responsive |
| `js/data-feed.js` | Reads `window.CITY_DATA` (activity, news, costs, agents) → feeds office.js |

### Modified Files
| Path | Change |
|------|--------|
| `index.html` | Replace loader + three.js imports + all UI divs with new structure; load `office.css`, `js/data-feed.js`, `js/office.js` |
| `js/manifest.js` | New `City.files = ['js/data-feed.js', 'js/office.js']`; bump `City.version` |
| `js/roles.js` | Keep as-is (data source for desk assignment) |
| `js/agents.js` | Keep as-is (agent → role mapping) |
| `js/buildings/townhall.js` | Keep Council logic; remove `build(g)` three.js geometry; add `panel()` for popover |
| `js/buildings/council.js` | Keep verdict logic |
| `js/buildings/newsroom.js` | Keep; `panel()` for popover |
| `js/buildings/treasury.js` | Keep; `panel()` for popover |
| `css/style.css` | **Delete** — replaced by `office.css` |
| `js/hud.js` | **Delete** — top bar moved to HTML + tiny inline script |
| `js/panels.js` | **Delete** — replaced by popovers |
| `js/visuals.js` | **Delete** |
| `js/daynight.js` | **Delete** — time-of-day is a CSS class on `<body>` |
| `js/streaks.js` | **Delete** |
| `js/minimap.js` | **Delete** |
| `js/deeplink.js` | **Delete** |
| `js/declutter.js` | **Delete** |
| `js/core.js` | **Delete** — helpers (`City.box`, `City.sign`, etc.) no longer needed |
| `js/world.js` | **Delete** |
| `js/main.js` | **Delete** |
| `js/buildings/*.js` (16 non-Town-Hall) | **Delete** — desks are static SVG, no per-building JS |
| `data.js` | **Keep** — generated by `build_data.py` unchanged |

### Deleted Files (19 JS + 1 CSS)
```
js/core.js, js/world.js, js/main.js, js/visuals.js, js/daynight.js,
js/panels.js, js/hud.js, js/minimap.js, js/streaks.js, js/declutter.js,
js/deeplink.js,
js/buildings/library.js, js/buildings/office.js, js/buildings/market.js,
js/buildings/clocktower.js, js/buildings/postoffice.js, js/buildings/studyhall.js,
js/buildings/promptworkshop.js, js/buildings/workshop.js, js/buildings/archive.js,
js/buildings/reviewboard.js, js/buildings/noticeboard.js, js/buildings/kiosk.js,
js/buildings/skillforge.js, js/buildings/statstower.js, js/buildings/router-exchange.js,
js/buildings/workshop.js (already listed), css/style.css
```

---

## Walk Mode Decision
**Drop walk mode entirely.** The bug ("can't turn with mouse/trackpad") is fixed by removing the 3D navigation that caused it. The new top-down SVG office needs no camera controls — click a desk, get a popover. This aligns with agent-virtual-office's "poke a character" interaction.

---

## How Existing Tests Still Pass

| Test | Why It Passes |
|------|---------------|
| `test_manifest_files_exist_and_new_ui_files_load_before_main` | New `manifest.js` lists only `js/data-feed.js`, `js/office.js` — both exist and load before (no) `main.js` |
| `test_label_declutter_is_wired_cheap_and_keeps_town_hall` | `declutter.js` deleted; test removed or updated to check `office.js` has no declutter |
| `test_prompt_linter_checks_four_parts_locally` | `promptworkshop.js` deleted; test updated to check `office.js` has inline linter or removed |
| `test_publish_workflow_is_gated_guarded_and_one_commit` | Unchanged (workflow file untouched) |
| `test_index_has_hud_elements_used_by_scripts` | **Updated** — new `index.html` has only `topbar`, `office`, `feed`, `settings` modal elements |
| `test_streaks_are_capped_and_respect_reduced_motion` | `streaks.js` deleted; test removed |
| `test_town_hall_is_the_central_hub_and_old_anchors_redirect` | `townhall.js` keeps `pos: [0,0]` for data; old anchors redirect via tiny hash handler in `office.js` |
| `test_no_building_shares_a_block_or_overlaps_the_hub` | Building `block` property removed from remaining `townhall.js`; test updated |
| `test_morning_brief_reads_private_notes_only_from_private_js` | `kiosk.js` deleted; test removed |
| `test_activity_cap_keeps_each_role` etc. (build_data) | Unchanged — `build_data.py` untouched |
| Browser tests (skipped locally) | New `office.js` has no JS errors; Playwright checks would verify popover open, feed renders |

**Test updates needed** (in `tests/test_ui_smoke.py`):
- `Static.test_index_has_hud_elements_used_by_scripts` → new element IDs
- `Static.test_label_declutter_*` → remove
- `Static.test_prompt_linter_*` → remove or adapt
- `Static.test_town_hall_is_the_central_hub_*` → check `townhall.js` has `pos: [0,0]` only
- `Static.test_no_building_shares_a_block_*` → remove (no blocks)
- `Static.test_morning_brief_*` → remove

---

## Implementation Order (Small Commits, Site Works at Each Step)

1. **Commit 1**: Add `js/office.js` (stub), `css/office.css` (stub), `js/data-feed.js` (stub). Update `manifest.js` to include them. Tests pass (stubs are no-ops).
2. **Commit 2**: Implement `data-feed.js` — reads `window.CITY_DATA`, exports `City.feed = { activity, news, costs, agents, roles }`.
3. **Commit 3**: Implement `office.js` — SVG office layout, desk click → popover, feed render, settings modal. No three.js.
4. **Commit 4**: New `index.html` — loads only `data-feed.js`, `office.js`; new DOM structure. Delete old UI divs.
5. **Commit 5**: New `css/office.css` — complete styles. Delete `css/style.css`.
6. **Commit 6**: Delete 19 JS building files + `js/core.js`, `js/world.js`, `js/main.js`, `js/visuals.js`, `js/daynight.js`, `js/panels.js`, `js/hud.js`, `js/minimap.js`, `js/streaks.js`, `js/declutter.js`, `js/deeplink.js`. Update `townhall.js` (remove `build()`, keep Council logic).
7. **Commit 7**: Update `tests/test_ui_smoke.py` — remove/adapt deleted-file tests, update element IDs.
8. **Commit 8**: Run `python3 build_data.py` → regenerates `data.js` (unchanged shape). Bump `City.version` in `manifest.js`.
9. **Commit 9**: Run all tests — verify 148 static tests pass. Push branch `w2/b9cityavo1`.

---

## Acceptance Criteria
- `python3 -m unittest discover -s tests` → **148 tests pass** (5 browser skipped, 5 deleted-file tests removed)
- `index.html` opens on `file://` with no console errors
- Click any desk → popover shows role + last 3 activity entries
- Click Town Hall → Council popover + Notice Board link
- Feed shows all activity, filtered by tabs (All/Council/Newsroom/Treasury)
- Settings modal toggles time-of-day (CSS class), graphics quality (no-op), labels, reduced motion
- Responsive: mobile stacks feed below office
- GitHub Pages publish workflow would work (no build step, no ES modules)