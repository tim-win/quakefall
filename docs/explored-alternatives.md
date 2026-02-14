# Explored Alternatives

Technologies investigated during QuakeFall's architecture phase that were ultimately not needed.

## Engines Considered

| Engine | WASM Size | Verdict |
|--------|-----------|---------|
| ioquake3 | 2.3 MB | **Selected** — tiny WASM, proven netcode, GPL v2 |
| Godot | ~27 MB | Too large for browser |
| Bevy | ~30 MB | Too large, Rust ecosystem complexity |
| Unity | ~33 MB | Too large, licensing concerns |
| Unreal | N/A | No viable WASM path |

See `docs/architecture/analysis/01_engine_alternatives.md` for the full comparison.

## HumbleNet (WebRTC)

WebRTC abstraction library from 2017 (Mozilla-funded). Cloned and investigated as a potential browser networking solution.

- Repo: `https://github.com/nickverlinden/HumbleNet`
- Q3 fork: `https://github.com/nickverlinden/humblenet-quake3`
- Analysis: `docs/architecture/analysis/04_humblenet_viability_report.md`

**Why not needed**: Emscripten's built-in POSIX socket emulation (`libsockfs.js`) automatically converts `sendto()`/`recvfrom()` calls to WebSocket messages. A 30-line Node.js proxy bridges WebSocket↔UDP to the native Q3 server. This is far simpler than integrating WebRTC, and WebSocket latency is acceptable for our use case.

## Custom WebRTC Integration

Considered building a custom WebRTC layer for peer-to-peer connections.

**Why not needed**: The WebSocket proxy approach adds ~1ms latency and requires no C code changes. WebRTC would add complexity (STUN/TURN servers, NAT traversal) for marginal latency improvement that doesn't matter for a server-authoritative game.

## References

The `docs/architecture/references/` directory contains fetched documentation from the research phase:
- `emscripten_networking.html` — Emscripten networking docs
- `humblenet_*.md/html` — HumbleNet documentation
- `ioquake3_readme.md` — ioquake3 project readme
