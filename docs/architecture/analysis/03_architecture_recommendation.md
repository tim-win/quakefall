# QuakeFall Architecture Recommendation

**Date**: 2025-10-14
**Status**: 🔴 **DECISION REQUIRED** - Pending HumbleNet viability testing
**Authors**: Technical Architecture Team

## Executive Summary

This document synthesizes our research into engine and networking options for **QuakeFall**, a browser-first Quake 3 + Titanfall hybrid FPS game. Our analysis strongly supports a single architectural recommendation with a clearly defined risk mitigation path.

---

## Recommended Architecture

### Core Stack

```
┌─────────────────────────────────────────────┐
│          QuakeFall Game Logic               │
│   (Pilots, Titans, Parkour Movement)       │
├─────────────────────────────────────────────┤
│         ioquake3 Engine (GPL v2)            │
│  (Rendering, Physics, Input, Audio)         │
├─────────────────────────────────────────────┤
│    HumbleNet Networking Layer (BSD-3)       │
│      (WebRTC Abstraction, P2P/Server)       │
├─────────────────────────────────────────────┤
│         Platform Layer                      │
│  Native (SDL) | Browser (Emscripten+WebGL)  │
└─────────────────────────────────────────────┘
```

### Component Breakdown

| Layer | Technology | Justification | Alternatives Rejected |
|-------|------------|---------------|----------------------|
| **Engine** | ioquake3 | 2MB footprint, proven netcode, GPL v2 | Godot (too big), Bevy (immature), Unity/Unreal (massive) |
| **Networking** | HumbleNet | Only WebRTC solution for unified native+browser code | WebSocket (too slow), Custom (too expensive) |
| **Platform** | Emscripten + Native SDL | Official ioquake3 support, mature toolchain | N/A - no alternatives |
| **Server Model** | Client-hosted (Phase 1) | Zero infra cost, instant matchmaking | Dedicated servers (Phase 2+) |

---

## Why This Architecture?

### 1. It's the Only Path That Meets All Requirements

**From `titanfall_design_doc.txt`**:
- ✅ Browser-first (<10MB download) → ioquake3 is 2MB
- ✅ WebRTC networking → HumbleNet provides this
- ✅ Cross-platform (native + browser) → Both compile from same code
- ✅ Excellent netcode → Quake 3 netcode is legendary
- ✅ F2P commercial use → GPL v2 + BSD-3 licenses allow this

**Critical insight**: No other combination of engine + networking satisfies these constraints.

### 2. Proven Technology Stack

This is not experimental architecture - it's **already been built**:

- **ioquake3 + Emscripten**: Multiple working examples (QuakeJS, ioquake3.js)
- **HumbleNet + Quake 3**: Exists at https://github.com/HumbleNet/quake3
- **WebRTC for games**: Battle-tested in production games

We're not inventing new technology, we're **combining existing solutions**.

### 3. Correct Abstraction Layers

Each layer has a clear responsibility:
- **ioquake3**: Handles FPS fundamentals (rendering, physics, weapons)
- **HumbleNet**: Abstracts WebRTC complexity behind simple API
- **Game logic**: We focus on unique features (titans, parkour)

This maximizes our effort on **differentiated gameplay**, not infrastructure.

---

## The HumbleNet Risk

### The Problem

HumbleNet was abandoned in 2017 (~8 years ago). Key concerns:

1. **Dependency rot**: Uses FlatBuffers 1.6.0 (2017), Emscripten has evolved significantly
2. **WebRTC API changes**: Browser WebRTC APIs have changed since 2017
3. **libwebrtc updates**: Native WebRTC library has new versions
4. **Unknown unknowns**: What else breaks with modern toolchains?

### Why We Can't Skip This Test

**We must know if HumbleNet is viable BEFORE committing to this architecture.**

If it's broken beyond repair, we face a 2+ month detour to build custom WebRTC integration.

### Risk Mitigation Strategy

```
┌──────────────────────────────────────────────────────────┐
│ PHASE 0: Viability Test (1-2 weeks)                      │
├──────────────────────────────────────────────────────────┤
│ 1. Clone HumbleNet/quake3                                │
│ 2. Attempt compilation with modern tools                 │
│ 3. Test basic multiplayer (native + browser)             │
│ 4. Document required fixes                               │
│                                                           │
│ DECISION GATE:                                           │
│ ✅ Works with <1 week fixes → Proceed with HumbleNet     │
│ ⚠️ Requires 1-2 weeks fixes → Still worth it             │
│ ❌ Fundamentally broken → Pivot to custom WebRTC         │
└──────────────────────────────────────────────────────────┘
```

**This test is NON-NEGOTIABLE.** We cannot plan further without this data.

---

## Alternative Path (If HumbleNet Fails)

### Custom WebRTC Integration

**Architecture**:
```
┌─────────────────────────────────────────────┐
│          QuakeFall Game Logic               │
├─────────────────────────────────────────────┤
│         ioquake3 Engine (GPL v2)            │
├─────────────────────────────────────────────┤
│    Custom WebRTC Abstraction Layer          │
│  ┌──────────────┐     ┌──────────────┐     │
│  │ Native:      │     │ Browser:     │     │
│  │ libdatachan  │     │ Emscripten   │     │
│  │ or libwebrtc │     │ WebRTC API   │     │
│  └──────────────┘     └──────────────┘     │
└─────────────────────────────────────────────┘
```

**Implementation Plan**:
1. Design unified C API (similar to HumbleNet)
2. Implement native side with libdatachannel (lighter than libwebrtc)
3. Implement browser side with Emscripten WebRTC bindings
4. Build signaling server for peer discovery
5. Test extensively across platforms

**Timeline**: 4-8 weeks full-time work
**Risk**: Medium - WebRTC is complex but well-documented
**Cost**: Delays Phase 1 prototype significantly

**Key libraries to evaluate**:
- **libdatachannel** (C++, BSD-2): Lighter weight than full libwebrtc
- **emscripten-webrtc-sdk**: Emscripten WebRTC bindings (if exists)
- **Custom signaling server**: WebSocket-based (simpler than HumbleNet's)

---

## Development Phases (Assuming HumbleNet Works)

### Phase 0: Foundation (Weeks 1-2) 🔴 CURRENT

**Goal**: Validate technical feasibility

- ✅ Document architecture options (DONE)
- ⏭️ Test HumbleNet compilation
- ⏭️ Verify basic multiplayer works
- ⏭️ Choose architecture path definitively

**Deliverable**: Go/no-go decision on HumbleNet

### Phase 1: Core Prototype (Weeks 3-14)

**Goal**: Prove the concept is fun

**Tech tasks**:
- Set up ioquake3 build pipeline (native + browser)
- Integrate HumbleNet networking
- Basic test map
- Simple main menu + server browser

**Gameplay tasks**:
- Implement basic Titan entity (larger player, slower movement)
- Titan call-down sequence
- Basic pilot vs titan weapon balance
- Core earn/call titan loop

**Deliverable**: Playable prototype demonstrating pilot/titan asymmetry

### Phase 2: Movement Expansion (Weeks 15-18)

**Goal**: Test if parkour breaks balance

- Wall running implementation
- Wall jumping
- Sliding
- Movement accuracy penalties (design doc requirement)

**Deliverable**: Full movement system for playtesting

### Phase 3: Combat Depth (Weeks 19-26)

**Goal**: Refined combat feel

- Full weapon roster (rockets, railgun, lightning gun, plasma)
- Titan weapon variety (chain gun, titan rockets, charge beam)
- Railgun tracer system (design doc anti-cheese mechanic)
- Titan drone system (awareness counterplay)

**Deliverable**: Balanced combat with counterplay

### Phase 4: Content & Polish (Weeks 27-38)

**Goal**: Releasable game

- 3-5 maps (mix of open + dense geometry)
- Game modes (FFA, TDM, LTS)
- Visual polish
- Sound design
- Performance optimization

**Deliverable**: Public alpha/beta

### Phase 5: Live Service (Ongoing)

- Cosmetic shop (F2P monetization)
- Dedicated server infrastructure
- Matchmaking service
- Competitive ladders
- Content updates

---

## Technical Specifications

### Build Targets

| Platform | Toolchain | Distribution | Priority |
|----------|-----------|--------------|----------|
| **Browser** | Emscripten → WASM | Web hosting | 🔴 P0 (Primary) |
| Linux (x64) | GCC/Clang | AppImage / Flatpak | 🟡 P1 |
| Windows (x64) | MinGW-w64 | .exe installer | 🟡 P1 |
| macOS (ARM64) | Clang | .dmg / .app bundle | 🟢 P2 |

**Browser is Priority 0** - it's the primary platform per design doc.

### Performance Targets

From `titanfall_design_doc.txt`:

| Metric | Target | Status |
|--------|--------|--------|
| Initial download | <10MB | ✅ ioquake3 is ~2MB + assets |
| Frame rate | 60+ FPS | ✅ Q3 runs on toasters |
| Latency | <100ms | ⚠️ Depends on WebRTC/network |
| Load time | <5s | ✅ Likely achievable |

### Development Environment Requirements

**Minimum**:
- Modern C/C++ compiler (GCC 9+, Clang 10+, MSVC 2019+)
- Emscripten SDK (latest stable)
- CMake 3.15+
- Git

**For HumbleNet** (if viable):
- FlatBuffers compiler (may need update from 1.6.0)
- libwebrtc development headers (native builds)

**For custom WebRTC** (fallback):
- libdatachannel or libwebrtc development libraries
- Signaling server stack (Node.js + WebSocket recommended)

---

## Licensing & Commercial Viability

### Component Licenses

| Component | License | Commercial Use | Attribution | Source Distribution |
|-----------|---------|----------------|-------------|---------------------|
| ioquake3 | GPL v2 | ✅ Allowed | Required | **Engine mods only** |
| HumbleNet | BSD-3-Clause | ✅ Allowed | Required | ❌ Not required |
| Game Assets | Proprietary | ✅ Our IP | N/A | ❌ Not required |
| Game Logic | Proprietary | ✅ Our IP | N/A | ❌ Not required |

### GPL v2 Implications

**What we MUST open-source**:
- Any modifications to ioquake3 engine code
- Engine-level features (e.g., new rendering features)

**What we can keep proprietary**:
- All game logic (titans, pilots, abilities)
- All assets (models, textures, sounds)
- Networking integration code (if BSD-3)
- Game modes and design
- Cosmetic shop system

**Monetization strategy is COMPATIBLE**:
- F2P distribution: ✅ Allowed
- Cosmetic microtransactions: ✅ Allowed
- All gameplay free: ✅ Aligns with GPL spirit

**Reference**: GPL v2 FAQ confirms this is legal and common practice (see: commercial games on id Tech engines).

---

## Key Technical Challenges

### 1. Parkour Movement Implementation

**Challenge**: ioquake3 has Q3 movement, we need to add:
- Wall running
- Wall jumping
- Ledge climbing
- Sliding

**Solution**: Extend player movement code (`bg_pmove.c`)
- Wall detection via ray casting
- Velocity manipulation for wall runs
- State machine for movement modes

**Risk**: Medium - movement code is complex but well-documented
**Timeline**: 2-3 weeks for basic implementation, 4-6 weeks for polish

### 2. Titan Entity System

**Challenge**: Titans are fundamentally different from pilots:
- Different hitboxes (much larger)
- Different movement physics
- Different camera perspectives
- Pilot-titan transitions

**Solution**: Extend player class system
- New entity type with custom bbox
- Separate movement code path
- Titan-specific weapon handling

**Risk**: Medium - requires deep engine understanding
**Timeline**: 2-4 weeks for basic implementation

### 3. Browser Performance Optimization

**Challenge**: WebAssembly is ~50-70% native speed
- Intensive physics calculations
- Many entities (pilots + titans + projectiles)
- 60 FPS target on low-end hardware

**Solution**:
- Aggressive LOD (level of detail) system
- Reduced simulation complexity for distant entities
- Optional graphics quality settings
- Testing on range of hardware

**Risk**: Low - Q3 is inherently lightweight
**Timeline**: Ongoing throughout development

### 4. Network Bandwidth Management

**Challenge**: WebRTC bandwidth varies by connection
- Need to support low-bandwidth players
- Voice chat (optional feature) uses additional bandwidth

**Solution**:
- Adaptive update rates (fewer updates on slow connections)
- Delta compression (Q3 already does this)
- Optional quality settings (reduce model detail over network)
- Voice chat as optional feature with quality settings

**Risk**: Low-Medium - Q3 netcode handles this
**Timeline**: Tuning during beta testing

---

## Success Criteria

### Technical Validation (Phase 1)

- ✅ Native build compiles and runs on Linux/Windows/macOS
- ✅ Browser build runs at 60+ FPS on 5-year-old laptop
- ✅ Multiplayer works: 2+ players can connect and play
- ✅ Basic pilot vs titan gameplay loop is functional
- ✅ Download size <10MB (base game + one map)

### Gameplay Validation (Phase 2-3)

- ✅ Parkour movement feels good (internal playtest feedback)
- ✅ Titans feel powerful but not overpowered
- ✅ Pilots can evade/damage titans with skill
- ✅ Movement has adequate skill ceiling
- ✅ Combat is fun for both roles

### Launch Readiness (Phase 4)

- ✅ 3+ balanced maps
- ✅ Multiple game modes working
- ✅ Stable with 12+ players
- ✅ Cosmetic shop functional
- ✅ Positive beta tester feedback

---

## Conclusion & Next Steps

### Architectural Decision

**We recommend**: **ioquake3 + HumbleNet** architecture
**Contingent on**: HumbleNet viability testing (1-2 weeks)
**Fallback plan**: Custom WebRTC integration (4-8 week delay)

### This Week's Actions

1. **Clone HumbleNet repositories**
   ```bash
   git clone https://github.com/HumbleNet/HumbleNet
   git clone https://github.com/HumbleNet/quake3
   ```

2. **Attempt compilation**
   - Follow HumbleNet build instructions
   - Update dependencies as needed (FlatBuffers, etc.)
   - Document all issues encountered

3. **Test basic functionality**
   - Run native build, verify movement/rendering
   - Run browser build, verify it works
   - Test multiplayer: connect two clients

4. **Document findings**
   - What works out of the box?
   - What requires fixes?
   - Estimated effort to production-ready state

5. **Make go/no-go decision**
   - If viable: Proceed with Phase 1 planning
   - If broken: Begin custom WebRTC design

### Stakeholder Decision Required

**Question**: Do we proceed with HumbleNet viability testing?

**Options**:
- ✅ **YES (RECOMMENDED)**: Start testing immediately, 1-2 week timeline
- ❌ NO: Skip HumbleNet, begin custom WebRTC design now (4-8 week delay)

**Our recommendation**: Test HumbleNet first. Even if there's only a 50% chance it works, the time savings (6+ weeks) justify the 1-2 week investigation.

---

## References

- [Engine Alternatives Analysis](./01_engine_alternatives.md)
- [Networking Architecture Analysis](./02_networking_architecture.md)
- [Design Document](../../titanfall_design_doc.txt)
- [HumbleNet Documentation](../references/humblenet_readme.html)
- [ioquake3 Documentation](../references/ioquake3_readme.md)
- [Emscripten Networking](../references/emscripten_networking.html)

---

**Document Status**: 🟢 **COMPLETE** - Ready for stakeholder review
**Next Review**: After HumbleNet viability testing (Week 2)
