# QuakeFall Documentation

This directory contains architectural research, analysis, and recommendations for the QuakeFall project.

## Quick Start

**START HERE**: [`architecture/analysis/03_architecture_recommendation.md`](./architecture/analysis/03_architecture_recommendation.md)

This is the executive summary document that ties together all research and provides actionable recommendations.

---

## Directory Structure

```
docs/
├── README.md (this file)
└── architecture/
    ├── references/          # External documentation (fetched via wget)
    │   ├── humblenet_readme.html
    │   ├── humblenet_quake3_readme.md
    │   ├── mozilla_humblenet_article.html
    │   ├── emscripten_networking.html
    │   └── ioquake3_readme.md
    │
    └── analysis/            # Our analysis documents
        ├── 01_engine_alternatives.md
        ├── 02_networking_architecture.md
        └── 03_architecture_recommendation.md
```

---

## Document Guide

### Analysis Documents (Read in Order)

#### 1. [Engine Alternatives Analysis](./architecture/analysis/01_engine_alternatives.md)

**Purpose**: Why we chose ioquake3 over alternatives

**Key findings**:
- ioquake3 is the only engine meeting size requirements (<10MB)
- Proven WebAssembly support
- Best-in-class netcode for FPS games
- GPL v2 license compatible with F2P model

**Alternatives rejected**: Godot, Bevy, Unity, Unreal, GoldSrc/Xash3D

---

#### 2. [Networking Architecture Analysis](./architecture/analysis/02_networking_architecture.md)

**Purpose**: Evaluate networking solutions for cross-platform multiplayer

**Key findings**:
- WebRTC is the ONLY viable option for unified native+browser code
- HumbleNet provides exactly this, but is from 2017 (abandoned)
- Must test HumbleNet viability before committing
- Fallback: Custom WebRTC integration (4-8 week effort)

**Critical decision**: Test HumbleNet compilation this week

---

#### 3. [Architecture Recommendation](./architecture/analysis/03_architecture_recommendation.md) 🔴 **MAIN DOCUMENT**

**Purpose**: Synthesize all research into actionable plan

**Recommended stack**:
- **Engine**: ioquake3
- **Networking**: HumbleNet (pending viability test)
- **Platform**: Emscripten (browser) + SDL (native)
- **Server model**: Client-hosted P2P (Phase 1)

**Next steps**:
1. Test HumbleNet compilation (1-2 weeks)
2. Make go/no-go decision
3. Either proceed with HumbleNet OR pivot to custom WebRTC

**Status**: 🔴 Awaiting HumbleNet viability test

---

### Reference Documents

These are external documentation files fetched for offline reference:

#### [HumbleNet README](./architecture/references/humblenet_readme.html)

Official HumbleNet documentation. Describes the WebRTC wrapper library.

**Source**: https://github.com/HumbleNet/HumbleNet

---

#### [HumbleNet Quake3 README](./architecture/references/humblenet_quake3_readme.md)

Documentation for the HumbleNet Quake 3 fork. This is the most directly relevant reference - it's already what we're trying to build.

**Source**: https://github.com/HumbleNet/quake3

---

#### [Mozilla HumbleNet Article](./architecture/references/mozilla_humblenet_article.html)

2017 Mozilla Hacks article introducing HumbleNet. Good high-level overview of the technology.

**Source**: https://hacks.mozilla.org/2017/06/introducing-humblenet-a-cross-platform-networking-library-that-works-in-the-browser/

---

#### [Emscripten Networking Docs](./architecture/references/emscripten_networking.html)

Official Emscripten documentation on networking options. Explains why WebRTC is necessary for UDP-like communication in browsers.

**Source**: https://emscripten.org/docs/porting/networking.html

**Key quote**: "direct UDP communication is not available in browsers"

---

#### [ioquake3 README](./architecture/references/ioquake3_readme.md)

Official ioquake3 documentation. Describes engine features, build process, and Emscripten support.

**Source**: https://github.com/ioquake/ioq3

---

## Key Decisions

### Decision 1: Engine Selection ✅ DECIDED

**Decision**: Use ioquake3
**Rationale**: Only engine meeting all requirements (size, netcode, license)
**Status**: ✅ Decided
**Document**: [`01_engine_alternatives.md`](./architecture/analysis/01_engine_alternatives.md)

---

### Decision 2: Networking Approach 🔴 PENDING

**Decision**: Use HumbleNet (pending viability test)
**Rationale**: Only WebRTC solution with unified native+browser API
**Status**: 🔴 **BLOCKED** - Must test compilation first
**Document**: [`02_networking_architecture.md`](./architecture/analysis/02_networking_architecture.md)

**Action required**: Clone and test HumbleNet this week

**Decision gate**:
- ✅ If HumbleNet works with <2 weeks fixes → Use it
- ❌ If fundamentally broken → Build custom WebRTC (4-8 week delay)

---

### Decision 3: Server Architecture 🟡 TENTATIVE

**Decision**: Client-hosted P2P for Phase 1
**Rationale**: Matches design doc vision ("run server in browser"), zero infra cost
**Status**: 🟡 Tentative - can add dedicated servers later
**Document**: [`02_networking_architecture.md`](./architecture/analysis/02_networking_architecture.md)

---

## Research Questions Answered

### Q: Why not use a modern engine like Godot or Bevy?

**A**: File size. Godot exports 27-33MB to WebAssembly, Bevy exports 17-33MB. Our budget is <10MB total. ioquake3 is ~2MB.

**See**: [`01_engine_alternatives.md`](./architecture/analysis/01_engine_alternatives.md)

---

### Q: Why do we need WebRTC? Can't we just use WebSockets?

**A**: WebSocket is TCP-based (high latency, head-of-line blocking). Fast-paced FPS games need UDP-like communication. WebRTC Data Channels provide this in browsers.

Additionally, WebSocket would require separate code paths for native (UDP) and browser (WebSocket), violating our "unified codebase" requirement.

**See**: [`02_networking_architecture.md`](./architecture/analysis/02_networking_architecture.md)

---

### Q: Is HumbleNet still maintained?

**A**: No. Last update was 2017 (~8 years ago). This is why we must test compilation viability before committing to this architecture.

**See**: [`02_networking_architecture.md`](./architecture/analysis/02_networking_architecture.md) - "The HumbleNet Risk" section

---

### Q: What if HumbleNet doesn't work?

**A**: We build our own WebRTC abstraction layer using modern libraries (libdatachannel for native, browser WebRTC API for Emscripten). Estimated 4-8 weeks effort.

**See**: [`03_architecture_recommendation.md`](./architecture/analysis/03_architecture_recommendation.md) - "Alternative Path" section

---

### Q: Can we legally monetize this as F2P with cosmetics?

**A**: Yes. ioquake3 is GPL v2, which requires open-sourcing engine modifications but allows proprietary game logic and assets. Cosmetic monetization is explicitly compatible.

**See**: [`03_architecture_recommendation.md`](./architecture/analysis/03_architecture_recommendation.md) - "Licensing & Commercial Viability" section

---

### Q: What's the critical path to a playable prototype?

**A**:
1. Test HumbleNet (1-2 weeks) 🔴 **CURRENT**
2. Set up build pipeline (1 week)
3. Implement basic titans (2-4 weeks)
4. Create test map (1-2 weeks)
5. Prototype core loop (2-3 weeks)

**Total: ~12 weeks to playable prototype** (assuming HumbleNet works)

**See**: [`03_architecture_recommendation.md`](./architecture/analysis/03_architecture_recommendation.md) - "Development Phases" section

---

## Next Actions

### This Week (Week of 2025-10-14)

- [ ] Clone HumbleNet repositories
- [ ] Attempt compilation with modern toolchains (Emscripten, GCC/Clang)
- [ ] Test basic multiplayer (native + browser)
- [ ] Document findings
- [ ] Make go/no-go decision on HumbleNet

### Next Week (If HumbleNet is viable)

- [ ] Set up project repository structure
- [ ] Configure build system (CMake + Emscripten)
- [ ] Create hello-world prototype (compile and run)
- [ ] Begin Phase 1 planning

### Next Week (If HumbleNet is not viable)

- [ ] Design custom WebRTC abstraction layer
- [ ] Evaluate libdatachannel vs libwebrtc
- [ ] Prototype signaling server
- [ ] Estimate revised timeline

---

## Contributing to Documentation

When adding new documents:

1. **Reference documents** go in `architecture/references/`
   - Use `wget` to fetch complete pages when possible
   - Preserve original URLs in comments
   - Name files descriptively

2. **Analysis documents** go in `architecture/analysis/`
   - Use numbered prefixes for reading order (01_, 02_, etc.)
   - Link to reference documents for sources
   - Include decision status (✅ decided, 🔴 pending, 🟡 tentative)

3. **Update this README**
   - Add new documents to directory structure
   - Add to appropriate section (Analysis or Reference)
   - Update "Next Actions" if priorities change

---

## Questions?

If you have questions about the architecture:

1. Check if it's answered in "Research Questions Answered" section above
2. Read the relevant analysis document (01, 02, or 03)
3. Check reference documents for technical details
4. If still unclear, discuss with team

---

**Last updated**: 2025-10-14
**Status**: 🔴 Phase 0 (Architecture Research) - Awaiting HumbleNet viability test
