# Networking Architecture Analysis

**Date**: 2025-10-14
**Purpose**: Evaluate networking solutions for cross-platform (native + browser) multiplayer

## Project Requirements

### Design Goals (from `titanfall_design_doc.txt`)

- **WebRTC data channels** for game state (UDP-like, low latency)
- **Cross-platform**: Same networking code for Windows/macOS/Linux/Browser
- **P2P or client-hosted**: Lightweight enough that a browser tab can run the server
- **Low latency**: Fast-paced Quake 3 movement requires <100ms target

### Critical Constraint

The game must use **identical networking code** across:
- Native builds (Windows, macOS, Linux distributables)
- Browser builds (WebAssembly)

This rules out solutions that require separate implementations for native vs browser.

---

## The Browser Networking Problem

### What Browsers Support

| Technology | Latency | Browser Support | Native Support | Notes |
|-----------|---------|----------------|----------------|-------|
| **HTTP/Fetch** | High | ✅ Native | ✅ Easy | Too slow for real-time games |
| **WebSocket** | Medium-High | ✅ Native | ⚠️ Via libraries | TCP-based, not ideal for FPS |
| **WebRTC** | Low | ✅ Native | ⚠️ Via libwebrtc | UDP-like, perfect for games |
| **Native UDP** | Lowest | ❌ Impossible | ✅ Perfect | Browsers cannot use UDP |

### The WebRTC Imperative

**WebRTC is the ONLY option** that satisfies our requirements:

1. ✅ **Low latency** - UDP-like data channels
2. ✅ **Browser native** - Built into all modern browsers
3. ✅ **Native support** - libwebrtc works on all desktop platforms
4. ✅ **Unified codebase** - Same API can compile for both targets
5. ✅ **P2P capable** - Supports both client-hosted and dedicated servers

**Reference**: [`../references/emscripten_networking.html`](../references/emscripten_networking.html)

> "direct UDP communication is not available in browsers" but "WebRTC Data Channels offer UDP-like communication"

---

## Networking Solution Candidates

### 1. HumbleNet (2017) ⚠️ POSSIBLE BUT RISKY

**What it is**: Cross-platform C API wrapping WebRTC for game networking

**Architecture**:
- Provides BSD-socket-like API over WebRTC
- Supports both native (libwebrtc) and browser (Emscripten) compilation
- Includes signaling server for peer discovery
- Already integrated into a Quake 3 fork

**References**:
- [`../references/humblenet_readme.html`](../references/humblenet_readme.html)
- [`../references/humblenet_quake3_readme.md`](../references/humblenet_quake3_readme.md)
- [`../references/mozilla_humblenet_article.html`](../references/mozilla_humblenet_article.html)

**Pros**:
- ✅ **Exactly what we need** - WebRTC wrapper with unified API
- ✅ **Proven with Quake 3** - Fork exists at https://github.com/HumbleNet/quake3
- ✅ **Cross-platform** - Native + browser from same code
- ✅ **Low latency** - WebRTC data channels (UDP-like)
- ✅ **P2P support** - Includes signaling/STUN/TURN

**Cons**:
- ❌ **Last updated 2017** (~8 years old)
- ❌ **Minimal maintenance** (27 commits total, abandoned project)
- ❌ **Old dependencies** - FlatBuffers 1.6.0 (2017), may not work with modern toolchains
- ❌ **Unknown compatibility** with modern Emscripten/WebRTC versions
- ⚠️ **Risk**: May require significant modernization work

**Status**: Abandoned open-source project (Mozilla/Humble Bundle collaboration)

**Assessment**:
This is the "easy path if it works, nightmare if it doesn't" option. The HumbleNet Quake 3 fork is exactly what we need architecturally, but its age is a major concern. Modern WebRTC and Emscripten have changed significantly since 2017.

**Recommendation**: Test compilation first before committing. If it works with minimal fixes, this is the fastest path to market. If it requires major updates, consider alternatives.

---

### 2. Native ioquake3 + WebSocket Proxy ❌ NOT RECOMMENDED

**What it is**: Emscripten's built-in WebSocket→BSD socket translation

**Architecture**:
- Emscripten translates BSD socket calls to WebSockets
- Native builds use UDP sockets
- Requires separate code paths or WebSockify proxy

**References**:
- [`../references/emscripten_networking.html`](../references/emscripten_networking.html)
- QuakeJS project: https://github.com/inolen/quakejs

**Pros**:
- ✅ Built into Emscripten (no external dependencies)
- ✅ Proven working (QuakeJS uses this)
- ⚠️ Easier setup than WebRTC

**Cons**:
- ❌ **TCP-based** - Higher latency than UDP/WebRTC
- ❌ **Native/browser incompatibility** - Different protocols
- ❌ **Not truly unified** - Requires platform-specific code or proxy
- ❌ **Worse for FPS games** - TCP head-of-line blocking hurts real-time gameplay

**Assessment**:
This violates our "unified codebase" requirement. QuakeJS documentation explicitly states: "networking is done through WebSockets, which unfortunately means that native builds and web builds currently can't interact with each other."

**Verdict**: **Rejected** - Doesn't meet cross-platform requirement, worse latency

---

### 3. Modern WebRTC Library (Custom Integration) ⚠️ HIGH EFFORT

**What it is**: Use a modern WebRTC library and write our own integration layer

**Potential libraries**:
- libwebrtc (official, C++, heavy)
- libdatachannel (C++, lighter weight)
- Custom Emscripten WebRTC bindings

**Pros**:
- ✅ Modern, maintained codebase
- ✅ Full control over implementation
- ✅ Future-proof
- ✅ Can optimize for our specific needs

**Cons**:
- ❌ **Significant development effort** (weeks/months)
- ❌ **Complex WebRTC setup** (signaling, ICE, STUN/TURN)
- ❌ **Learning curve** for team
- ❌ **Testing burden** across multiple platforms
- ⚠️ **Risk**: Delays core gameplay development

**Assessment**:
This is the "perfect but expensive" option. If HumbleNet can't be salvaged, this becomes necessary, but it's a major time investment.

**Verdict**: **Fallback option** - Only pursue if HumbleNet fails

---

### 4. OpenArena Live Approach 🔍 UNKNOWN

**What it is**: Browser-based OpenArena port using WebRTC

**Status**: Limited documentation, appears to be integrated with Kosmi.io platform

**Assessment**: Insufficient technical details available. May be proprietary or platform-specific.

**Verdict**: **Insufficient information** - Cannot evaluate

---

## Decision Matrix

| Solution | Latency | Unified Code | Effort | Risk | Maintenance | Score |
|----------|---------|--------------|--------|------|-------------|-------|
| **HumbleNet** | ✅ Low | ✅ Yes | ⚠️ Unknown | ⚠️ High | ❌ Abandoned | **3/5** |
| WebSocket | ❌ Medium | ❌ No | ✅ Low | ✅ Low | ✅ Active | 2/5 |
| Custom WebRTC | ✅ Low | ✅ Yes | ❌ High | ⚠️ Medium | ✅ We own it | 3/5 |

---

## Architectural Recommendation

### Phase 1: Test HumbleNet Viability (1-2 weeks)

**Action items**:
1. Clone HumbleNet/quake3 fork
2. Attempt compilation with modern toolchains:
   - Emscripten SDK (latest)
   - Modern C++ compiler
   - Update FlatBuffers if needed
3. Test basic networking functionality (native + browser)
4. Assess modernization effort required

**Decision points**:
- ✅ **If it compiles with minor fixes**: Use HumbleNet, save months of work
- ⚠️ **If it requires moderate effort** (<2 weeks fixes): Still worth it
- ❌ **If it's fundamentally broken**: Abandon, pursue custom WebRTC

### Phase 2A: HumbleNet Path (if viable)

**Advantages**:
- Fastest time to working multiplayer
- Proven architecture for Quake 3
- Focus effort on gameplay, not networking infrastructure

**Work required**:
- Update dependencies (FlatBuffers, libwebrtc bindings)
- Test with modern browsers/Emscripten
- Fix any compatibility issues
- Document for team

### Phase 2B: Custom WebRTC Path (if HumbleNet fails)

**Advantages**:
- Modern, maintainable codebase
- Full control and understanding
- Future-proof

**Work required**:
- Design WebRTC abstraction layer
- Implement signaling protocol
- Write Emscripten bindings
- Extensive cross-platform testing
- 4-8 weeks estimated effort

---

## Server Architecture Options

Both approaches support flexible server models:

### Option A: Client-Hosted (P2P)
**Architecture**: One browser/native client acts as server host
**Pros**: No infrastructure costs, instant matchmaking
**Cons**: Host advantage, scalability limits
**Verdict**: ✅ **Recommended for initial launch** (matches design doc vision)

### Option B: Dedicated Servers
**Architecture**: Standalone server processes (also using WebRTC)
**Pros**: Fair gameplay, scalable, competitive-ready
**Cons**: Infrastructure costs, deployment complexity
**Verdict**: ✅ **Add later** for competitive modes

### Implementation Notes
WebRTC supports both models with same code:
- Client-hosted: One peer acts as "authoritative" host
- Dedicated: Server runs as standalone WebRTC peer
- **The design doc suggests client-hosted** ("one user can run the server on their browser")

This is architecturally sound - Quake 3's netcode handles this model well.

---

## Key Risks & Mitigations

### Risk 1: HumbleNet is Unmaintainable
**Likelihood**: Medium
**Impact**: High (2+ month delay)
**Mitigation**: Test compilation immediately, have custom WebRTC as fallback

### Risk 2: WebRTC Complexity
**Likelihood**: Low (if using HumbleNet) / High (if custom)
**Impact**: High
**Mitigation**: Allocate sufficient time for testing/debugging

### Risk 3: Browser Compatibility
**Likelihood**: Low (WebRTC is well-supported)
**Impact**: Medium
**Mitigation**: Test on Chrome, Firefox, Safari early

### Risk 4: NAT Traversal Failures
**Likelihood**: Medium (some corporate networks block WebRTC)
**Impact**: Medium (some players can't connect)
**Mitigation**: Provide TURN server fallback (costs money but guarantees connectivity)

---

## Next Steps

### Immediate (This Week)
1. ✅ Document architecture options (this document)
2. ⏭️ Clone and test HumbleNet compilation
3. ⏭️ Evaluate effort required to modernize

### Short-term (Next 2 Weeks)
- **If HumbleNet works**: Integrate into project, test multiplayer
- **If HumbleNet fails**: Begin custom WebRTC design

### Long-term (Post-MVP)
- Set up dedicated server infrastructure
- Implement matchmaking service
- Add TURN server for NAT traversal reliability

---

**See also**:
- [`01_engine_alternatives.md`](./01_engine_alternatives.md) - Engine selection analysis
- [`03_architecture_recommendation.md`](./03_architecture_recommendation.md) - Final recommendations
- [`../references/humblenet_readme.html`](../references/humblenet_readme.html) - HumbleNet documentation
- [`../references/emscripten_networking.html`](../references/emscripten_networking.html) - Emscripten networking options
