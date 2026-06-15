# Graph Report - GRAVITY  (2026-06-15)

## Corpus Check
- 109 files · ~163,373 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1609 nodes · 4397 edges · 82 communities (77 shown, 5 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 348 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7a3e0372`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]

## God Nodes (most connected - your core abstractions)
1. `User` - 124 edges
2. `Goal` - 49 edges
3. `Habit` - 41 edges
4. `HabitLog` - 33 edges
5. `Nudge` - 28 edges
6. `HealthData` - 26 edges
7. `UserProfile` - 26 edges
8. `T()` - 23 edges
9. `T()` - 23 edges
10. `T()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `E5()` --calls--> `btn()`  [INFERRED]
  Gravity (1)/gravity-gallery.js → Gravity (2)/gravity-app.js
- `E5()` --calls--> `btn()`  [INFERRED]
  Gravity copy 2/gravity-gallery.js → Gravity (2)/gravity-app.js
- `Image` --uses--> `UserProfile`  [INFERRED]
  simulator/display/gravity_sim.py → core/profile.py
- `UserProfile` --uses--> `Schedule`  [INFERRED]
  tests/test_profile_extraction.py → core/profile.py
- `UserProfile` --uses--> `Goal`  [INFERRED]
  tests/test_nudge_logic.py → core/profile.py

## Import Cycles
- 1-file cycle: `backend/main.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/nudges.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/research.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/push.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/goals.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/device.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/memory.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/onboarding.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/calendar.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/habits.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/analytics.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/auth.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/integrations.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/review.py -> backend/main.py`
- 2-file cycle: `backend/main.py -> backend/routers/files.py -> backend/main.py`

## Communities (82 total, 5 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (25): build_user_state(), decide_nudge(), evaluate_nudge(), generate_nudge_content(), load_prompt(), UserProfile, Call 2 — Content.     Only runs when decision says yes.     Generates the actual, Main entry point for the nudge engine.      Takes a profile and current state, r (+17 more)

### Community 1 - "Community 1"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 2 - "Community 2"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 3 - "Community 3"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 4 - "Community 4"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 5 - "Community 5"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 6 - "Community 6"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 7 - "Community 7"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 8 - "Community 8"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 9 - "Community 9"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 10 - "Community 10"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 11 - "Community 11"
Cohesion: 0.18
Nodes (44): A1(), A2(), A3(), A4(), A5(), A6(), A7(), arc() (+36 more)

### Community 12 - "Community 12"
Cohesion: 0.20
Nodes (42): apply_circle_mask(), arc(), arc_sq(), bot_label(), brackets(), chord_hw(), dot(), _font() (+34 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (12): ABC, DisplayBackend, HardwareBackend, Image, PygameBackend, device_sim.py — Hardware device abstraction stub.  In production this will drive, Abstract backend — Pygame simulator or real SPI hardware., Push a 360×360 PIL image to the display. (+4 more)

### Community 14 - "Community 14"
Cohesion: 0.05
Nodes (37): 1. Fix visual quality of screens.py, 2. Build layout_engine.py, 3. Wire gravity_sim.py to layout_engine.py, 4. Add click/touch navigation, 5. Build nudge overlay screen, 6. Add Direction B and C screen variants, AI Architecture, Context Architecture (for backend) (+29 more)

### Community 15 - "Community 15"
Cohesion: 0.08
Nodes (14): D1(), D10(), D2(), D3(), D4(), D5(), D8(), E5() (+6 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (14): D1(), D10(), D2(), D3(), D4(), D5(), D8(), E5() (+6 more)

### Community 17 - "Community 17"
Cohesion: 0.08
Nodes (14): D1(), D10(), D2(), D3(), D4(), D5(), D8(), E5() (+6 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (61): AsyncSession, Redis, User, Redis, Redis, Nudge, NudgeSettings, Per-user nudge preferences — one row per user, created on first access. (+53 more)

### Community 19 - "Community 19"
Cohesion: 0.21
Nodes (30): appSections, btn(), chip(), I, M1(), M2(), M3(), M4() (+22 more)

### Community 20 - "Community 20"
Cohesion: 0.22
Nodes (14): AsyncSession, Redis, User, get_integration_status(), get_redis(), get_today_health(), HealthSyncRequest, HealthSyncResponse (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.15
Nodes (27): AsyncSession, Redis, User, AIClient, ai_complete(), build_system_prompt(), delete_session(), extract_profile_data() (+19 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (23): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+15 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (18): bell(), droplet(), L1(), L10(), L12(), L13(), L15(), L16() (+10 more)

### Community 24 - "Community 24"
Cohesion: 0.13
Nodes (18): bell(), droplet(), L1(), L10(), L12(), L13(), L15(), L16() (+10 more)

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (18): bell(), droplet(), L1(), L10(), L12(), L13(), L15(), L16() (+10 more)

### Community 26 - "Community 26"
Cohesion: 0.13
Nodes (18): bell(), droplet(), L1(), L10(), L12(), L13(), L15(), L16() (+10 more)

### Community 27 - "Community 27"
Cohesion: 0.13
Nodes (18): bell(), droplet(), L1(), L10(), L12(), L13(), L15(), L16() (+10 more)

### Community 28 - "Community 28"
Cohesion: 0.13
Nodes (18): bell(), droplet(), L1(), L10(), L12(), L13(), L15(), L16() (+10 more)

### Community 29 - "Community 29"
Cohesion: 0.13
Nodes (18): bell(), droplet(), L1(), L10(), L12(), L13(), L15(), L16() (+10 more)

### Community 30 - "Community 30"
Cohesion: 0.09
Nodes (44): AsyncSession, Redis, User, AsyncSession, AsyncSession, Redis, BaseModel, UserLocation (+36 more)

### Community 31 - "Community 31"
Cohesion: 0.31
Nodes (21): arc(), botLabel(), check(), curve(), dot(), f(), faceFocus(), faceGoal() (+13 more)

### Community 32 - "Community 32"
Cohesion: 0.19
Nodes (21): AsyncSession, User, UserFile, _build_cycle_review_data(), _build_habit_analytics(), Config, delete_file(), FileResponse (+13 more)

### Community 33 - "Community 33"
Cohesion: 0.15
Nodes (22): AsyncSession, User, OAuth2PasswordRequestForm, create_token(), get_current_user(), hash_password(), login(), logout() (+14 more)

### Community 34 - "Community 34"
Cohesion: 0.14
Nodes (13): AI prompt conventions, Architecture overview, Display system coordinate conventions, graphify, GRAVITY — Claude Code Project Context, Key product rules (never violate), Module connections, Running tests (+5 more)

### Community 35 - "Community 35"
Cohesion: 0.09
Nodes (57): AsyncSession, User, AsyncSession, Redis, User, AsyncSession, AsyncSession, Redis (+49 more)

### Community 36 - "Community 36"
Cohesion: 0.24
Nodes (10): AsyncSession, Redis, _build_rule_based_layout(), _compute_streak(), generate_layout(), Layout service — generates the UI layout JSON for a user's device screen. For no, Return the layout instruction JSON for this user's device.     Consumed by the d, Choose visual direction from user profile. A=Terminal, B=Orbital, C=Minimal. (+2 more)

### Community 37 - "Community 37"
Cohesion: 0.28
Nodes (3): WebSocket, ConnectionManager, Broadcast an event to all active connections for a user.

### Community 38 - "Community 38"
Cohesion: 0.22
Nodes (8): Built By, Current Stage: Stage 0 — Brain First, Documentation, GRAVITY, Project Structure, Running Tests, Running the Simulator, What It Is

### Community 39 - "Community 39"
Cohesion: 0.25
Nodes (7): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 40 - "Community 40"
Cohesion: 0.29
Nodes (6): Image, display_renderer.py — Render pipeline stub.  Connects a layout (from layout_engi, Main render loop — NOT BUILT.      Will:     1. Load/refresh profile from profil, Render a single screen synchronously. Used by tests and the Pygame sim.     scre, render_loop(), render_single()

### Community 41 - "Community 41"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 42 - "Community 42"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 43 - "Community 43"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 44 - "Community 44"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 54 - "Community 54"
Cohesion: 0.18
Nodes (17): AsyncSession, User, AsyncSession, PushToken, Expo push notification token per user device., Push notification router.    POST /push/register    ← app registers/updates its, Register or refresh an Expo push token for this user's device., Deactivate a push token on logout. (+9 more)

### Community 69 - "Community 69"
Cohesion: 0.09
Nodes (35): AsyncSession, User, AsyncSession, Memory, Memory, Config, delete_memory(), MemoryResponse (+27 more)

### Community 70 - "Community 70"
Cohesion: 0.12
Nodes (44): AsyncSession, Goal, User, AsyncSession, AsyncSession, Goal, Redis, User (+36 more)

### Community 71 - "Community 71"
Cohesion: 0.21
Nodes (18): load_profile(), The complete model of a Gravity user.     Built during onboarding, refined over, Save a profile to disk as a JSON file.     Returns the path it was saved to., Load a profile from disk by name.     Returns None if no profile exists for that, save_profile(), UserProfile, UserProfile, nudge_tester.py — CLI tool to fire nudge test scenarios against a profile.  Usag (+10 more)

### Community 72 - "Community 72"
Cohesion: 0.10
Nodes (29): User, fetch_url(), Research router — web search, content extraction, exercise database.    POST /re, Search the web via SearXNG. Returns [] if SearXNG is not running., Extract clean text content from a URL via Jina Reader., Full research pipeline: search → extract top sources in parallel.     Use this w, Search the Wger open exercise database., Suggest exercises based on the user's active goal. (+21 more)

### Community 73 - "Community 73"
Cohesion: 0.18
Nodes (16): apply_circular_clip(), build_screens(), fire_test_nudge(), get_profiles_mtime(), load_profile_dict(), load_profile_obj(), main(), pil_to_surface() (+8 more)

### Community 74 - "Community 74"
Cohesion: 0.20
Nodes (16): apply_extracted_data(), build_context_summary(), extract_profile_data(), load_prompt(), UserProfile, Run a single onboarding phase.          How it works:     1. Load the system pro, Load a prompt file from core/prompts/, Build a short plain-English summary of what we know about     the user so far. I (+8 more)

### Community 75 - "Community 75"
Cohesion: 0.20
Nodes (9): 1. First Deploy, 2. SSL Renewal, 3. Updating the App, 4. Viewing Logs, 5. Database Backup, 6. Environment Variables, 7. Service Status, Gravity — Production Deployment (+1 more)

### Community 76 - "Community 76"
Cohesion: 0.33
Nodes (9): build_layout(), _days_remaining(), _focus_line(), _nonneg_display(), layout_engine.py — Builds an ordered list of screen configs from a UserProfile., Format non-negotiables as checklist items, capped at 5., Short motivational focus line from profile data., Build an ordered list of screen configs for a given profile.      Each config: (+1 more)

### Community 78 - "Community 78"
Cohesion: 0.17
Nodes (10): Config, get_settings(), Settings, Base, init_db(), lifespan(), BaseSettings, DeclarativeBase (+2 more)

### Community 79 - "Community 79"
Cohesion: 0.16
Nodes (17): get_db(), AsyncSession, Redis, User, device_heartbeat(), FirmwareResponse, get_device_state(), get_firmware_info() (+9 more)

### Community 80 - "Community 80"
Cohesion: 0.24
Nodes (9): build_pdf(), generate_cycle_review_pdf(), generate_habit_report_pdf(), PDF generator — produces downloadable reports for users. Templates in backend/te, Sync. Load Jinja2 template from backend/templates/pdf/{template_name}.html,, Generic async wrapper — offloads sync WeasyPrint to a thread., 6-month cycle review PDF.     ctx  — user context dict from context_service.buil, 30-day habit analytics report PDF.     ctx       — user context dict     analyti (+1 more)

### Community 81 - "Community 81"
Cohesion: 0.67
Nodes (3): WebSocket, Persistent WebSocket connection per user.     Auth: JWT passed as ?token= query, websocket_endpoint()

## Knowledge Gaps
- **160 isolated node(s):** `WEEK`, `STREAK14`, `directions`, `main`, `gallerySections` (+155 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UserProfile` connect `Community 71` to `Community 0`, `Community 73`, `Community 74`, `Community 76`, `Community 30`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `User` connect `Community 70` to `Community 32`, `Community 33`, `Community 35`, `Community 69`, `Community 72`, `Community 78`, `Community 79`, `Community 18`, `Community 20`, `Community 21`, `Community 54`, `Community 30`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `build_layout()` connect `Community 76` to `Community 73`, `Community 12`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 105 inferred relationships involving `User` (e.g. with `AsyncSession` and `User`) actually correct?**
  _`User` has 105 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `Goal` (e.g. with `AsyncSession` and `User`) actually correct?**
  _`Goal` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `Habit` (e.g. with `AsyncSession` and `User`) actually correct?**
  _`Habit` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `HabitLog` (e.g. with `AsyncSession` and `User`) actually correct?**
  _`HabitLog` has 25 INFERRED edges - model-reasoned connections that need verification._