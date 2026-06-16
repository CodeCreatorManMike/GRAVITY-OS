## Build Context

Read `GRAVITY/GRAVITY_BUILD_CONTEXT.md` at the start of every session. It captures all
architectural decisions (hardware, voice, camera, UI, storage, AI provider strategy, outcome
tracking, demo build order) that are not derivable from the code alone.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## caveman mode

Say "caveman mode" or "/caveman" to activate ultra-compressed responses (~75% fewer output tokens, full technical accuracy). Use for long coding sessions to save credits. Levels: lite / full (default) / ultra. Say "stop caveman" to revert.

## Key rules (from build context)

- Device is a dumb terminal. Never add routing logic to firmware.
- Every AI call must log an AIInteraction row. No exceptions.
- MinIO for all file storage. Never write uploaded bytes to local filesystem.
- Two-tier AI routing: Groq for high-frequency cheap calls, Claude for high-stakes.
- Camera is V2 only. Do not add camera features to V1 scope.
- MicroPython stays on firmware. No C++/C#.
