# Engine Alternatives Analysis

**Date**: 2025-10-14
**Purpose**: Document and justify the choice of ioquake3 as the game engine for the QuakeFall project.

## Requirements Summary

From the design document (`titanfall_design_doc.txt`), our engine must support:

1. **Browser deployment** - WebAssembly/Emscripten compilation
2. **Small footprint** - Target <10MB initial download for browser
3. **Cross-platform** - Native builds (Windows, macOS, Linux) + browser
4. **Fast-paced FPS gameplay** - Quake 3 style movement with parkour additions
5. **Excellent netcode** - Client-server prediction, lag compensation
6. **Commercial use** - F2P game with cosmetic monetization

## Candidates Evaluated

### 1. ioquake3 ✅ SELECTED

**Description**: Community-maintained Quake 3 Arena engine (GPL v2)

**Pros**:
- ✅ Tiny footprint (~2MB total engine)
- ✅ Proven WebAssembly ports exist
- ✅ Excellent netcode (20+ years of battle-testing)
- ✅ GPL v2 license allows commercial use
- ✅ Code-first development (no editor bloat)
- ✅ Active maintenance (as of 2024-2025)
- ✅ Official Emscripten support built-in
- ✅ Full IPv6 support, VoIP support
- ✅ Perfect foundation for Q3-style movement

**Cons**:
- ⚠️ Older codebase requires C/C++ expertise
- ⚠️ No modern editor/tooling
- ⚠️ Will need custom parkour movement implementation

**References**:
- [`references/ioquake3_readme.md`](../references/ioquake3_readme.md)
- Official repo: https://github.com/ioquake/ioq3

**Verdict**: **Best fit** - Meets all requirements, proven technology

---

### 2. Godot ❌ REJECTED

**Description**: Modern open-source game engine with Godot Script/C#

**Pros**:
- ✅ Modern editor and tooling
- ✅ Active development and community
- ✅ WebAssembly export support

**Cons**:
- ❌ **27-33MB WebAssembly export by default** (3x over budget)
- ❌ Modern engine overhead inappropriate for "runs on toasters" goal
- ❌ Overkill for arena FPS needs

**Verdict**: **Rejected** - File size bloat violates core design pillar

---

### 3. Bevy ❌ REJECTED

**Description**: Modern ECS game engine in Rust

**Pros**:
- ✅ Modern architecture (ECS)
- ✅ Rust safety guarantees
- ✅ Growing community

**Cons**:
- ❌ **17-33MB WASM builds** (exceeds budget)
- ❌ Rust complexity adds development overhead
- ❌ Less mature than alternatives
- ❌ Smaller community/fewer resources for FPS development

**Verdict**: **Rejected** - File size + maturity concerns

---

### 4. Unity/Unreal ❌ REJECTED

**Description**: Commercial AAA game engines

**Pros**:
- ✅ Professional tooling
- ✅ Extensive documentation
- ✅ Large asset ecosystems

**Cons**:
- ❌ **Multi-GB downloads** (completely violates browser-first design)
- ❌ Complex licensing for commercial use
- ❌ Massive overkill for project scope
- ❌ Revenue sharing or licensing fees

**Verdict**: **Rejected** - Wrong tool for "accessible, lightweight" goals

---

### 5. GoldSrc/Xash3D ❌ REJECTED

**Description**: Half-Life 1 engine and its open-source reimplementation

**Pros**:
- ✅ Similar era to Quake 3
- ✅ Proven FPS capabilities
- ✅ Lightweight

**Cons**:
- ❌ **Licensing nightmare** (Half-Life SDK conflicts with open-source goals)
- ❌ Less active community than ioquake3
- ❌ Worse netcode than Quake 3

**Verdict**: **Rejected** - Legal and technical concerns

---

## Decision Matrix

| Engine | Size | WebAssembly | Netcode | License | Active Dev | Score |
|--------|------|-------------|---------|---------|------------|-------|
| **ioquake3** | ✅ 2MB | ✅ Native | ✅ Best | ✅ GPL v2 | ✅ Yes | **5/5** |
| Godot | ❌ 27-33MB | ⚠️ Works | ⚠️ OK | ✅ MIT | ✅ Yes | 2/5 |
| Bevy | ❌ 17-33MB | ⚠️ Works | ⚠️ DIY | ✅ MIT | ⚠️ Young | 1/5 |
| Unity | ❌ GB+ | ❌ Poor | ⚠️ OK | ❌ Commercial | ✅ Yes | 1/5 |
| Unreal | ❌ GB+ | ❌ Poor | ⚠️ OK | ❌ Commercial | ✅ Yes | 1/5 |
| GoldSrc | ✅ Small | ⚠️ Possible | ⚠️ OK | ❌ Complex | ⚠️ Limited | 2/5 |

## Final Recommendation

**ioquake3 is the clear winner** for this project. It uniquely satisfies all critical requirements:

1. **Accessibility**: 2MB footprint means instant browser loading
2. **Proven Technology**: 20+ years of refinement, no surprises
3. **Perfect Netcode**: Q3's client-server prediction is legendary
4. **Commercial Viability**: GPL v2 allows F2P + cosmetic sales model
5. **Right Tool**: Purpose-built for exactly this type of game

The only significant challenge is implementing parkour movement (wall running, sliding, etc.), but this is **game logic** that we'd need to implement in any engine. ioquake3's clean C codebase makes this feasible.

## Next Steps

1. Set up ioquake3 development environment
2. Verify WebAssembly compilation works
3. Test basic movement and netcode
4. Begin parkour movement prototyping

---

**See also**:
- [`02_networking_architecture.md`](./02_networking_architecture.md) - Networking layer analysis
- [`../references/ioquake3_readme.md`](../references/ioquake3_readme.md) - Full ioquake3 documentation
