# CLAUDE.md - QuakeFall Project Context

## What Is This

QuakeFall is a browser-based arena FPS: Quake 3 movement mechanics + Titanfall-style pilot/titan asymmetric gameplay, compiled to WebAssembly and running in Chrome. Free-to-play, cosmetics-only monetization.

## Tech Stack (Proven & Working)

- **Engine**: ioquake3 (C, GPL v2) — the open-source Quake 3 engine
- **Compiler**: Emscripten — cross-compiles C to WebAssembly
- **Rendering**: OpenGL in C → Emscripten translates to WebGL automatically
- **Networking**: Emscripten's built-in POSIX socket emulation (converts UDP sendto/recvfrom to WebSocket) + a tiny Node.js WebSocket↔UDP proxy
- **Server**: Native ioquake3 dedicated server (`ioq3ded`) running standard UDP

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
- `ioquake3.html` — the page you open
- `ioquake3.js` — Emscripten glue code
- `ioquake3.wasm` — the compiled engine (~2.3MB)
- `ioquake3-config.json` — lists game data files to load

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

### Key Configuration
The Emscripten build needs these flags (in `cmake/platforms/emscripten.cmake`):
```
-sINCOMING_MODULE_JS_API=canvas,arguments,locateFile,preRun,websocket
-sWEBSOCKET_URL=ws://
```

The HTML file needs the websocket config in the Module options:
```javascript
ioquake3({
    canvas: canvas,
    websocket: { url: 'ws://localhost:27961/' },
    // ...
});
```

And `net_enabled` must be set to `1` (the default Emscripten template sets it to `0`).

### Running Multiplayer Locally
```bash
# Terminal 1: Q3 dedicated server
cd external/ioq3/build-native/Release
DISPLAY= ./ioq3ded +set com_basegame demoq3 +set sv_pure 0 +set dedicated 1 +map q3dm1

# Terminal 2: WebSocket proxy
node proxy.js

# Terminal 3: HTTP server for browser client
python3 -m http.server 8080 --directory external/ioq3/build/Release

# Browser: open http://localhost:8080/ioquake3.html?com_basegame=demoq3
# Open console (~), type: connect 127.0.0.1
```

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
├── docs/                  ← architecture research & analysis
│   ├── README.md          ← guide to all docs
│   └── architecture/
│       ├── analysis/      ← engine comparison, networking analysis, recommendations
│       └── references/    ← fetched external docs (HumbleNet, Emscripten, ioquake3)
└── external/              ← cloned repos (gitignored)
    ├── emsdk/             ← Emscripten SDK
    ├── ioq3/              ← ioquake3 engine (the main engine we use)
    ├── HumbleNet/         ← WebRTC library (explored, not needed)
    └── humblenet-quake3/  ← HumbleNet Q3 fork (explored, not needed)
```

## What's Been Validated

1. **C → browser pipeline**: hello.c compiles with emcc, runs in Chrome ✅
2. **Graphics pipeline**: OpenGL spinning triangle renders via WebGL ✅
3. **Full Q3 engine in browser**: ioquake3 compiles to WASM, renders maps, runs game logic ✅
4. **Browser↔server networking**: WebSocket proxy bridges browser client to native Q3 dedicated server, 3ms ping, bidirectional data flow ✅

## What's Next (Not Yet Started)

1. **Game logic**: Add titan entity type (bigger bounding box, slower speed, more HP) — modify QVM game code
2. **Parkour movement**: Wall running, wall jumping, sliding — extend `bg_pmove.c`
3. **Titan hitboxes**: 6-10 sub-entities per titan that move together (shoot between legs, etc.) — entity parenting system
4. **Custom maps**: BSP maps with mix of open areas (titan advantage) and dense geometry (pilot advantage)
5. **Weapons**: Pilot arsenal (rockets, railgun, lightning gun) + titan arsenal (chain gun, titan rockets, charge beam)

## Architecture Decisions Made

| Decision | Choice | Why |
|----------|--------|-----|
| Engine | ioquake3 | 2MB WASM, proven netcode, GPL v2 compatible with F2P |
| Networking | Emscripten WebSocket + proxy | Dead simple, no WebRTC needed, no HumbleNet needed |
| Server model | Native dedicated servers | Reliable, no host advantage, $5/mo VPS |
| Titan hitboxes | Multi-entity approach | Each limb is a separate entity, uses existing collision, optimize later if needed |
| Physics | None (Q3 built-in) | Q3's movement/collision handles everything needed |

## Things That Were Explored But Not Needed

- **HumbleNet**: WebRTC abstraction library from 2017. Cloned and investigated but the simple WebSocket proxy approach made it unnecessary.
- **Custom WebRTC integration**: Not needed since WebSocket latency is acceptable and the proxy approach is trivial.
- **Godot/Bevy/Unity/Unreal**: All rejected for WASM size (27-33MB+). ioquake3 is 2.3MB.

## CD Key Bypass

The Q3 demo shows a CD key prompt. Open console with backtick (`) and type `devmap q3dm1` to bypass it and load directly into a map. When connecting to a server via `connect`, the CD key screen doesn't block gameplay.

## Known Quirks

- ioquake3 shows a GTK "Home Directory Files Upgrade" dialog on first native run. Use `DISPLAY=` to suppress when running headless dedicated server.
- The Emscripten build's HTML template resets on rebuild (cmake regenerates it from `code/web/client.html.in`). Edits to `net_enabled` and `websocket` config need to be reapplied after rebuild, or made in the template source.
- Two Q3 server processes can accidentally spawn if you're not careful with backgrounding. Check with `ps aux | grep ioq3ded`.
