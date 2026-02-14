# CLAUDE.md - QuakeFall Project Context

## What Is This

QuakeFall is a browser-based arena FPS: Quake 3 movement mechanics + Titanfall-style pilot/titan asymmetric gameplay, compiled to WebAssembly and running in Chrome. Free-to-play, cosmetics-only monetization.

## Tech Stack (Proven & Working)

- **Engine**: ioquake3 (C, GPL v2) — the open-source Quake 3 engine
- **Compiler**: Emscripten — cross-compiles C to WebAssembly
- **Rendering**: OpenGL in C → Emscripten translates to WebGL automatically
- **Networking**: Emscripten's built-in POSIX socket emulation (converts UDP sendto/recvfrom to WebSocket) + a tiny Node.js WebSocket↔UDP proxy
- **Server**: Native ioquake3 dedicated server (`ioq3ded`) running standard UDP
- **Persistence**: Emscripten IDBFS — IndexedDB-backed filesystem for saving player config across sessions

## How The Build Works

### Emscripten SDK
Installed at `external/emsdk/`. Activate with:
```bash
source external/emsdk/emsdk_env.sh
```

### Building ioquake3 for Browser (WASM)
```bash
cd external/ioq3
emcmake cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 8
```
Output lands in `external/ioq3/build/Release/`:
- `ioquake3.html` — the page you open (generated from `code/web/client.html.in`)
- `ioquake3.js` — Emscripten glue code
- `ioquake3.wasm` — the compiled engine (~2.3MB)
- `ioquake3-config.json` — lists game data files to load (copied from `code/web/client-config.json`)

**Important**: Rebuilds regenerate `ioquake3.html` and `ioquake3-config.json` from source templates. Always edit the source files (`code/web/client.html.in` and `code/web/client-config.json`), not the build output.

After building, copy QVMs to the demoq3 game directory:
```bash
cp build/Release/baseq3/vm/*.qvm build/Release/demoq3/vm/
```

### Building Native Dedicated Server
```bash
cd external/ioq3
cmake -S . -B build-native -DCMAKE_BUILD_TYPE=Release -DBUILD_SERVER=ON
cmake --build build-native --parallel 8
```
Binary: `external/ioq3/build-native/Release/ioq3ded`

### Game Assets
The Q3 demo pak (`pak0.pk3`, 45MB) must be placed in a `demoq3/` directory alongside the built binaries. QVM files (game logic bytecode) are built automatically by cmake and go in `demoq3/vm/`. The demo pak was extracted from the freely-distributable Q3 Linux demo installer from `ftp.gwdg.de`.

To set up game data for a build:
```bash
mkdir -p <build-dir>/demoq3/vm
cp <path-to-pak0.pk3> <build-dir>/demoq3/
cp <build-dir>/baseq3/vm/*.qvm <build-dir>/demoq3/vm/
```

## Engine Modifications (in external/ioq3, gitignored)

These changes live in `external/ioq3/` which is gitignored. They must be reapplied if the repo is re-cloned.

### HTML Template (`code/web/client.html.in`)
- `com_basegame` defaults to `demoq3` (no URL query params needed)
- `net_enabled 1` (networking on by default)
- `fs_homepath /q3home` (config writes to known persistent path)
- WebSocket config auto-connects proxy on same hostname port 27961
- IDBFS mounted at `/q3home` — syncs from IndexedDB on load, syncs back on page unload + every 30 seconds
- Player nickname, keybinds, favorites, and all Q3 settings persist across browser sessions

### Emscripten Build Config (`cmake/platforms/emscripten.cmake`)
- Added `-lidbfs.js` to link options for IndexedDB filesystem support

### CD Key Removal (`code/q3_ui/ui_menu.c`)
- CD key check removed unconditionally (was blocking browser users every session)
- Note: QVM code is compiled by q3lcc, NOT emcc — `#ifdef __EMSCRIPTEN__` does NOT work in QVM code

### Game Data Config (`code/web/client-config.json`)
- Added `qfcity1.bsp` to `demoq3` files list so custom maps load in browser

## Networking Architecture

### The Problem
Browsers can't do UDP. Q3 servers speak UDP. We need a bridge.

### The Solution (Surprisingly Simple)
Emscripten has a POSIX socket emulation layer (`libsockfs.js`). When ioquake3's C code calls `sendto()` on a UDP socket, Emscripten automatically converts it to a WebSocket message. No C code changes needed.

A 30-line Node.js proxy (`proxy.js`) sits between browser and server:
```
Browser (WASM)          proxy.js              Q3 Server (native)
sendto() in C    →    WebSocket→UDP    →    normal UDP packets
recvfrom() in C  ←    WebSocket←UDP    ←    normal UDP packets
```

### Running Multiplayer Locally
```bash
# Terminal 1: Q3 dedicated server
cd external/ioq3/build-native/Release
DISPLAY= ./ioq3ded +set com_basegame demoq3 +set sv_pure 0 +set dedicated 1 +map qfcity1

# Terminal 2: WebSocket proxy
node proxy.js

# Terminal 3: HTTP server for browser client
python3 -m http.server 8080 --bind 0.0.0.0 --directory external/ioq3/build/Release

# Browser: open http://<hostname>:8080/ioquake3.html
# Open console (~), type: connect <server-ip>
```

No URL query params needed. No CD key prompt. Settings persist across sessions.

Proxy listens on WebSocket port 27961, forwards to Q3 server UDP port 27960. Tested at 3ms ping on localhost.

## Project Structure

```
quakefall/
├── CLAUDE.md              ← you are here
├── titanfall_design_doc.txt  ← full game design (movement, weapons, titans, modes)
├── proxy.js               ← WebSocket↔UDP relay for networking
├── hello.c                ← proof: C → browser pipeline works
├── hello_gl.c             ← proof: OpenGL rendering in browser works
├── package.json           ← Node.js deps (just `ws` for the proxy)
├── tools/                 ← build tools and generators
│   └── generate_city_map.py  ← procedural city map generator
├── maps/                  ← generated .map source files and compiled .bsp
│   └── qfcity1.map/bsp   ← first city map (4x4 block grid)
├── docs/                  ← architecture research & analysis
│   ├── README.md          ← guide to all docs
│   └── architecture/
│       ├── analysis/      ← engine comparison, networking analysis, recommendations
│       └── references/    ← fetched external docs (HumbleNet, Emscripten, ioquake3)
└── external/              ← cloned repos (gitignored)
    ├── emsdk/             ← Emscripten SDK
    ├── ioq3/              ← ioquake3 engine (modified — see Engine Modifications above)
    ├── netradiant/        ← NetRadiant-Custom (contains q3map2 BSP compiler)
    ├── HumbleNet/         ← WebRTC library (explored, not needed)
    └── humblenet-quake3/  ← HumbleNet Q3 fork (explored, not needed)
```

## What's Been Validated

1. **C → browser pipeline**: hello.c compiles with emcc, runs in Chrome ✅
2. **Graphics pipeline**: OpenGL spinning triangle renders via WebGL ✅
3. **Full Q3 engine in browser**: ioquake3 compiles to WASM, renders maps, runs game logic ✅
4. **Browser↔server networking**: WebSocket proxy bridges browser client to native Q3 dedicated server, 3ms ping, bidirectional data flow ✅
5. **Custom map pipeline**: Procedural Python → .map → q3map2 (BSP/VIS/LIGHT) → playable in browser ✅
6. **Cross-machine multiplayer**: Two players on different machines connected to the same custom map via LAN ✅
7. **Persistent browser storage**: IDBFS saves player config (nickname, keybinds, favorites) to IndexedDB, survives page reload ✅
8. **Zero-friction browser launch**: No CD key, no URL params, just open the page and play ✅

## Custom Map Pipeline

### Map Generator
`tools/generate_city_map.py` generates Q3 `.map` files procedurally. Currently creates a city layout with:
- 4x4 grid of city blocks with buildings of varying heights (256-1024 units)
- Wide streets (384 units, titan-friendly) between blocks
- Open central plaza with low cover walls
- Buildings with doors on south and east sides, interior platforms
- Stairs for rooftop access
- Weapon pickups, ammo, health, armor scattered throughout
- 16 spawn points across streets and plaza
- Sealed skybox with sun lighting (`skies/xtoxicsky_q3ctf3` shader)

### Compiling Maps
q3map2 is in `external/netradiant/squashfs-root/usr/bin/q3map2.x86_64`. Three passes:
```bash
Q3MAP2=external/netradiant/squashfs-root/usr/bin/q3map2.x86_64
BASEPATH=external/ioq3/build-native/Release

# 1. BSP (geometry)
$Q3MAP2 -game quake3 -fs_basepath $BASEPATH -fs_game demoq3 -meta maps/qfcity1.map

# 2. VIS (visibility culling)
$Q3MAP2 -game quake3 -fs_basepath $BASEPATH -fs_game demoq3 -vis maps/qfcity1.map

# 3. LIGHT (lightmaps — sky shader provides sun + ambient)
$Q3MAP2 -game quake3 -fs_basepath $BASEPATH -fs_game demoq3 -light -fast -samples 2 -bounce 2 maps/qfcity1.map
```

### Deploying Maps
Copy the compiled `.bsp` to both server and client game data:
```bash
cp maps/qfcity1.bsp external/ioq3/build-native/Release/demoq3/maps/  # native server
cp maps/qfcity1.bsp external/ioq3/build/Release/demoq3/maps/          # WASM client
```
The WASM client also needs the BSP listed in `code/web/client-config.json` (source) under the `demoq3` files array. After editing, re-run cmake configure or manually copy to `build/Release/ioquake3-config.json`. Browser must hard-refresh after config changes.

### Q3 .map Brush Format (Critical Detail)
q3map2's `PlaneFromPoints` uses `cross(p2-p0, p1-p0)` — outward-pointing normals. For an axis-aligned box from (x1,y1,z1) to (x2,y2,z2), the correct winding order is:
- Left (x=x1, -X): `(x1,y1,z2) (x1,y1,z1) (x1,y2,z1)`
- Right (x=x2, +X): `(x2,y2,z2) (x2,y2,z1) (x2,y1,z1)`
- Back (y=y1, -Y): `(x2,y1,z1) (x1,y1,z1) (x1,y1,z2)`
- Front (y=y2, +Y): `(x2,y2,z2) (x1,y2,z2) (x1,y2,z1)`
- Bottom (z=z1, -Z): `(x1,y2,z1) (x1,y1,z1) (x2,y1,z1)`
- Top (z=z2, +Z): `(x2,y2,z2) (x2,y1,z2) (x1,y1,z2)`

Use float format (`%.3f`), tab indentation, and 3 trailing flag integers (`0 0 0`). Winding was derived by decompiling q3dm1.bsp as a reference.

## What's Next

1. **Titan mode**: Player transformation — bigger bounding box, slower speed, more HP, restricted movement. Console command first, then entity-based enter/exit flow.
2. **Parkour movement**: Wall running, wall jumping, sliding — extend `bg_pmove.c`
3. **Titan hitboxes**: 6-10 sub-entities per titan that move together (shoot between legs, etc.) — entity parenting system
4. **Map iteration**: Improve city map — better textures, more vertical gameplay, narrow alleys for pilots
5. **Weapons**: Pilot arsenal (rockets, railgun, lightning gun) + titan arsenal (chain gun, titan rockets, charge beam)

## Architecture Decisions Made

| Decision | Choice | Why |
|----------|--------|-----|
| Engine | ioquake3 | 2MB WASM, proven netcode, GPL v2 compatible with F2P |
| Networking | Emscripten WebSocket + proxy | Dead simple, no WebRTC needed, no HumbleNet needed |
| Server model | Native dedicated servers | Reliable, no host advantage, $5/mo VPS |
| Titan hitboxes | Multi-entity approach | Each limb is a separate entity, uses existing collision, optimize later if needed |
| Physics | None (Q3 built-in) | Q3's movement/collision handles everything needed |
| Persistence | Emscripten IDBFS at /q3home | IndexedDB-backed, automatic sync, zero config for players |

## Things That Were Explored But Not Needed

- **HumbleNet**: WebRTC abstraction library from 2017. Cloned and investigated but the simple WebSocket proxy approach made it unnecessary.
- **Custom WebRTC integration**: Not needed since WebSocket latency is acceptable and the proxy approach is trivial.
- **Godot/Bevy/Unity/Unreal**: All rejected for WASM size (27-33MB+). ioquake3 is 2.3MB.

## Known Quirks

- ioquake3 shows a GTK "Home Directory Files Upgrade" dialog on first native run. Use `DISPLAY=` to suppress when running headless dedicated server.
- Rebuilds regenerate HTML and config JSON from templates. Always edit source files in `code/web/`, not build output.
- QVM code (game/, cgame/, q3_ui/) is compiled by q3lcc, NOT Emscripten. `#ifdef __EMSCRIPTEN__` does not work there.
- Two Q3 server processes can accidentally spawn if you're not careful with backgrounding. Check with `ps aux | grep ioq3ded`.
- IDBFS access in Emscripten 5.x: use `module.FS.filesystems.IDBFS`, not `module.IDBFS`.
