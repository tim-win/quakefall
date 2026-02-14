# CLAUDE.md - QuakeFall Project Context

## What Is This

QuakeFall is a browser-based arena FPS: Quake 3 movement mechanics + Titanfall-style pilot/titan asymmetric gameplay, compiled to WebAssembly and running in Chrome. Free-to-play, cosmetics-only monetization.

## Tech Stack

- **Engine**: ioquake3 (C, GPL v2) — open-source Quake 3 engine, tracked as a git submodule at `external/ioq3` (fork: `tim-win/ioq3`, branch: `quakefall-titan`)
- **Compiler**: Emscripten — cross-compiles C to WebAssembly
- **Rendering**: OpenGL in C → Emscripten translates to WebGL automatically
- **Networking**: Emscripten POSIX socket emulation (UDP→WebSocket) + Node.js WebSocket↔UDP proxy (`proxy.js`)
- **Server**: Native ioquake3 dedicated server (`ioq3ded`) running standard UDP
- **Persistence**: Emscripten IDBFS — IndexedDB-backed filesystem at `/q3home` for player config
- **Map compiler**: q3map2 from NetRadiant-Custom (`external/netradiant/`)

## Project Structure

```
quakefall/
├── CLAUDE.md              ← you are here
├── titanfall_design_doc.txt  ← full game design (movement, weapons, titans, modes)
├── proxy.js               ← WebSocket↔UDP relay (30 lines)
├── package.json           ← Node.js deps (just `ws`)
├── tools/
│   └── generate_city_map.py  ← procedural city map generator
├── maps/
│   └── qfcity1.map/bsp   ← first city map (4x4 block grid)
├── docs/
│   ├── explored-alternatives.md  ← engines/networking approaches we evaluated
│   └── architecture/             ← research from architecture phase
├── external/
│   ├── ioq3/              ← ioquake3 engine (git submodule, modified)
│   ├── emsdk/             ← Emscripten SDK (gitignored, download separately)
│   └── netradiant/        ← NetRadiant-Custom for q3map2 (gitignored, download separately)
├── hello.c                ← proof-of-concept: C → browser
└── hello_gl.c             ← proof-of-concept: OpenGL → WebGL
```

## How The Build Works

### Prerequisites
```bash
# Emscripten SDK (one-time setup)
git clone https://github.com/emscripten-core/emsdk external/emsdk
cd external/emsdk && ./emsdk install latest && ./emsdk activate latest
source external/emsdk/emsdk_env.sh
```

### Building ioquake3 for Browser (WASM)
```bash
cd external/ioq3
emcmake cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 8
cp build/Release/baseq3/vm/*.qvm build/Release/demoq3/vm/
```
Output: `external/ioq3/build/Release/` (ioquake3.html, .js, .wasm, config)

**Important**: Rebuilds regenerate `ioquake3.html` and `ioquake3-config.json` from source templates. Always edit `code/web/client.html.in` and `code/web/client-config.json`, not the build output.

### Building Native Dedicated Server
```bash
cd external/ioq3
cmake -S . -B build-native -DCMAKE_BUILD_TYPE=Release -DBUILD_SERVER=ON
cmake --build build-native --parallel 8
cp build-native/Release/baseq3/vm/*.qvm build-native/Release/demoq3/vm/
```

### Game Assets
The Q3 demo pak (`pak0.pk3`, 45MB) must be in `<build-dir>/demoq3/`. Extracted from the freely-distributable Q3 Linux demo installer.

## Engine Modifications

All modifications live in the `external/ioq3` submodule on the `quakefall-titan` branch.

### Infrastructure
- **HTML template** (`code/web/client.html.in`): Defaults to `demoq3`, networking on, IDBFS at `/q3home`, WebSocket proxy auto-config
- **Emscripten build** (`cmake/platforms/emscripten.cmake`): Added `-lidbfs.js` for IndexedDB filesystem
- **CD key removal** (`code/q3_ui/ui_menu.c`): Removed unconditionally (was blocking browser users)
- **Game data config** (`code/web/client-config.json`): Custom maps listed for WASM client loading

### Titan Mode (Phase 1)
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

## Running Multiplayer Locally

```bash
# Terminal 1: Q3 dedicated server (MUST use vm_game 0)
cd external/ioq3/build-native/Release
DISPLAY= ./ioq3ded +set com_basegame demoq3 +set sv_pure 0 +set dedicated 1 +set vm_game 0 +map qfcity1

# Terminal 2: WebSocket proxy
node proxy.js

# Terminal 3: HTTP server for browser client
python3 -m http.server 8080 --bind 0.0.0.0 --directory external/ioq3/build/Release

# Browser: open http://<hostname>:8080/ioquake3.html
# Open console (~), type: /connect <server-ip>
```

## Custom Map Pipeline

### Generator
`tools/generate_city_map.py` — procedural city layout with buildings, streets, spawn points, items, sealed skybox.

### Compile & Deploy
```bash
Q3MAP2=external/netradiant/squashfs-root/usr/bin/q3map2.x86_64
BASEPATH=external/ioq3/build-native/Release

$Q3MAP2 -game quake3 -fs_basepath $BASEPATH -fs_game demoq3 -meta maps/qfcity1.map
$Q3MAP2 -game quake3 -fs_basepath $BASEPATH -fs_game demoq3 -vis maps/qfcity1.map
$Q3MAP2 -game quake3 -fs_basepath $BASEPATH -fs_game demoq3 -light -fast -samples 2 -bounce 2 maps/qfcity1.map

cp maps/qfcity1.bsp external/ioq3/build-native/Release/demoq3/maps/
cp maps/qfcity1.bsp external/ioq3/build/Release/demoq3/maps/
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

## What's Next

1. **Titan mode Phase 2**: Entity-based enter/exit flow (call down a titan, climb in/out)
2. **Parkour movement**: Wall running, wall jumping, sliding — extend `bg_pmove.c`
3. **Titan hitboxes**: Multi-entity system (shoot between legs, target weak points)
4. **Map iteration**: Better textures, more vertical gameplay, narrow pilot alleys
5. **Weapons**: Pilot arsenal + titan arsenal

## Known Quirks

- **Server MUST use `+set vm_game 0`**: q3lcc QVM compiler generates corrupted bytecode for titan code, causing multiplayer BAD ANIMATION crashes. Native .so works correctly. Client QVMs (cgame, ui) are fine.
- **Always check for duplicate servers**: `ps aux | grep ioq3ded` before starting — duplicates on port 27960 cause network corruption.
- **QVM code != Emscripten code**: QVM files (game/, cgame/, q3_ui/) are compiled by q3lcc, not emcc. `#ifdef __EMSCRIPTEN__` does not work in QVM code.
- **Edit source templates, not build output**: Rebuilds regenerate HTML and config JSON from `code/web/` sources.
- **Suppress GTK dialog**: Use `DISPLAY=` when running headless dedicated server.
- **IDBFS in Emscripten 5.x**: Use `module.FS.filesystems.IDBFS`, not `module.IDBFS`.
- **Console commands need `/` prefix**: ioquake3 `con_autochat` sends bare text as chat.
