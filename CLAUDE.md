# CLAUDE.md - QuakeFall Project Context

## What Is This

QuakeFall is a browser-based arena FPS: Quake 3 movement mechanics + Titanfall-style pilot/titan asymmetric gameplay, compiled to WebAssembly and running in Chrome. Free-to-play, cosmetics-only monetization.

## Agent Workflow

This project uses structured long-running agent sessions. **Read these before starting work:**

- **`docs/anthropic-long-running-agents.md`** — Full workflow specification (session structure, commit discipline, validation rules)
- **`features.json`** — Immutable feature contract. All features start as `"failing"`. Only flip to `"passing"` after full validation. Never edit feature specs.
- **`claude-progress.txt`** — Living state. What's done, what's in progress, blockers, next steps. **Read this at session start. Update it at session end and after every milestone.**

### Validation Is YOUR Job

**You do not hand features back to the user for testing.** You implement, you build, you start the server, you test, you confirm it works, you screenshot if visual, and THEN you mark it passing. The validation steps in `features.json` are instructions for YOU to execute, not acceptance criteria for the user. If you can't validate a feature yourself (e.g., requires a second human player), document exactly what you tested and what remains, and leave it as `"failing"`.

### Session Startup Checklist
1. Read `claude-progress.txt` and recent `git log`
2. Read `features.json` to find highest-priority incomplete feature
3. Verify build compiles cleanly (`tools/build.sh native`)
4. Begin work on a single feature

### Commit Convention
```
feat(titan-hitbox): add child entity spawn on titan enter
[WIP] feat(titan-debug): rendering works but wireframe mode incomplete
```
Always commit submodule (`external/ioq3`) first, then parent repo.

## Tech Stack

- **Engine**: ioquake3 (C, GPL v2) — git submodule at `external/ioq3` (fork: `tim-win/ioq3`, branch: `quakefall-titan`)
- **Compiler**: Emscripten — cross-compiles C to WebAssembly
- **Rendering**: OpenGL in C → Emscripten translates to WebGL automatically
- **Networking**: Emscripten POSIX socket emulation (UDP→WebSocket) + Node.js WebSocket↔UDP proxy (`proxy.js`)
- **Server**: Native ioquake3 dedicated server (`ioq3ded`) running standard UDP
- **Persistence**: Emscripten IDBFS — IndexedDB-backed filesystem at `/q3home` for player config
- **Map compiler**: q3map2 from NetRadiant-Custom (`external/netradiant/`)

## Project Structure

```
quakefall/
├── CLAUDE.md                 ← project constitution (static)
├── claude-progress.txt       ← living state (updated by agents)
├── features.json             ← feature contract (immutable specs, mutable status)
├── titanfall_design_doc.txt  ← full game design doc
├── proxy.js                  ← WebSocket↔UDP relay
├── package.json              ← Node.js deps (just `ws`)
├── tools/
│   ├── build.sh              ← compile native/wasm (tools/build.sh native)
│   ├── server.sh             ← server management (tools/server.sh start|stop|restart|status|log)
│   ├── rcon.py               ← RCON client (python3 tools/rcon.py 'status')
│   ├── compile_map.sh        ← map compile+deploy (tools/compile_map.sh maps/foo.map)
│   └── generate_city_map.py  ← procedural city map generator
├── maps/
│   └── qfcity1.map/bsp      ← first city map
├── docs/
│   ├── anthropic-long-running-agents.md  ← agent workflow spec
│   ├── explored-alternatives.md
│   └── architecture/
├── external/
│   ├── ioq3/                 ← ioquake3 engine (git submodule, modified)
│   ├── emsdk/                ← Emscripten SDK (gitignored)
│   └── netradiant/           ← NetRadiant-Custom for q3map2 (gitignored)
└── hello.c / hello_gl.c     ← proof-of-concept files
```

## Tooling Quick Reference

```bash
# Build
tools/build.sh native          # Compile native server + client (~30s)
tools/build.sh wasm            # Compile WASM browser client
tools/build.sh all             # Both

# Server management
tools/server.sh start          # Start ioq3ded (checks for duplicates, sets rcon)
tools/server.sh stop           # Kill server
tools/server.sh restart        # Stop + start
tools/server.sh status         # Check if running
tools/server.sh log            # Tail server log
tools/server.sh log 100        # Tail last 100 lines

# RCON (server must be running)
python3 tools/rcon.py status              # Player list
python3 tools/rcon.py "map qfcity1"       # Change map
python3 tools/rcon.py "titan_parts"       # Dump titan hitbox state (when implemented)

# Map compilation
tools/compile_map.sh maps/qfcity1.map    # BSP/VIS/LIGHT + deploy to both build dirs

# Environment overrides
QF_MAP=testmap tools/server.sh start     # Start with different map
QF_RCON=secret tools/server.sh start     # Different rcon password
```

## Building From Scratch

### Prerequisites
```bash
# Emscripten SDK (one-time, for WASM builds only)
git clone https://github.com/emscripten-core/emsdk external/emsdk
cd external/emsdk && ./emsdk install latest && ./emsdk activate latest
source external/emsdk/emsdk_env.sh
```

### Native Build (Primary Development Path)
```bash
tools/build.sh native
```
Output: `external/ioq3/build-native/Release/` (ioq3ded, ioquake3, .so files)

### WASM Build (Browser Client)
```bash
tools/build.sh wasm
```
Output: `external/ioq3/build/Release/` (ioquake3.html, .js, .wasm)

**Important**: Rebuilds regenerate `ioquake3.html` and `ioquake3-config.json` from source templates. Always edit `code/web/client.html.in` and `code/web/client-config.json`, not the build output.

### Game Assets
The Q3 demo pak (`pak0.pk3`, 45MB) must be in `<build-dir>/demoq3/`. Extracted from the freely-distributable Q3 Linux demo installer.

## Running Multiplayer Locally

```bash
# Terminal 1: Dedicated server (tools handle all the flags)
tools/server.sh start

# Terminal 2: WebSocket proxy (for browser clients)
node proxy.js

# Terminal 3: HTTP server (for browser clients)
python3 -m http.server 8080 --bind 0.0.0.0 --directory external/ioq3/build/Release

# Native client: run external/ioq3/build-native/Release/ioquake3 directly
# Browser client: open http://<hostname>:8080/ioquake3.html
# Connect: open console (~), type /connect <server-ip>
```

## Engine Modifications

All modifications live in the `external/ioq3` submodule on the `quakefall-titan` branch.

### Infrastructure
- **HTML template** (`code/web/client.html.in`): Defaults to `demoq3`, networking on, IDBFS at `/q3home`, WebSocket proxy auto-config
- **Emscripten build** (`cmake/platforms/emscripten.cmake`): Added `-lidbfs.js` for IndexedDB filesystem
- **CD key removal** (`code/q3_ui/ui_menu.c`): Removed unconditionally (was blocking browser users)
- **Game data config** (`code/web/client-config.json`): Custom maps listed for WASM client loading

### Titan Mode (Phase 1 — Single Bounding Box)
Console command `/titan` toggles titan mode. Files modified:
- `bg_public.h` — `PMF_TITAN` flag (32768) + dimension constants
- `bg_pmove.c` — Titan bbox in `PM_CheckDuck()`, jump disabled in `PM_CheckJump()`
- `g_local.h` — `titanMode` field on `gclient_s`
- `g_active.c` — Per-frame speed scale + flag application
- `g_client.c` — Spawn dimensions/health for titans
- `g_cmds.c` — `Cmd_Titan_f()` + dispatch entry
- `cg_consolecmds.c` — `trap_AddCommand("titan")`
- `cg_players.c` — Graceful handling of bad animation numbers (clamp instead of crash)

Parameters: 500 HP, ±30 width, 80 height, viewheight 56, 0.6x speed, no jumping.

## Custom Map Pipeline

### Generator
`tools/generate_city_map.py` — procedural city layout with buildings, streets, spawn points, items, sealed skybox.

### Compile & Deploy
```bash
tools/compile_map.sh maps/qfcity1.map
```
WASM client also needs the BSP listed in `code/web/client-config.json`.

### .map Brush Format
q3map2 `PlaneFromPoints` uses `cross(p2-p0, p1-p0)` — outward normals. For box (x1,y1,z1)→(x2,y2,z2):
- Left (-X): `(x1,y1,z2) (x1,y1,z1) (x1,y2,z1)`
- Right (+X): `(x2,y2,z2) (x2,y2,z1) (x2,y1,z1)`
- Back (-Y): `(x2,y1,z1) (x1,y1,z1) (x1,y1,z2)`
- Front (+Y): `(x2,y2,z2) (x1,y2,z2) (x1,y2,z1)`
- Bottom (-Z): `(x1,y2,z1) (x1,y1,z1) (x2,y1,z1)`
- Top (+Z): `(x2,y2,z2) (x2,y1,z2) (x1,y1,z2)`

## Known Quirks

- **Server MUST use `+set vm_game 0`**: q3lcc QVM compiler generates corrupted bytecode for titan code, causing multiplayer BAD ANIMATION crashes. Native .so works correctly. Client QVMs (cgame, ui) are fine. `tools/server.sh` handles this automatically.
- **Always check for duplicate servers**: `tools/server.sh` checks for this, but if running manually: `ps aux | grep ioq3ded` — duplicates on port 27960 cause network corruption.
- **QVM code != Emscripten code**: QVM files (game/, cgame/, q3_ui/) are compiled by q3lcc, not emcc. `#ifdef __EMSCRIPTEN__` does not work in QVM code.
- **Edit source templates, not build output**: Rebuilds regenerate HTML and config JSON from `code/web/` sources.
- **Suppress GTK dialog**: Use `DISPLAY=` when running headless dedicated server. `tools/server.sh` handles this.
- **IDBFS in Emscripten 5.x**: Use `module.FS.filesystems.IDBFS`, not `module.IDBFS`.
- **Console commands need `/` prefix**: ioquake3 `con_autochat` sends bare text as chat.
