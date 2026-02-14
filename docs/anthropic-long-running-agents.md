# Long-Running Agent Harness for QuakeFall

> Adapted from Anthropic's engineering blog posts on long-running agents and multi-agent compiler builds.
> Tailored to the QuakeFall project: single-agent, incremental, session-based workflow.

## Core Problem

Long-running agents must work across multiple context windows / sessions, each starting with no memory of prior work. This is analogous to shift-based engineers who need clear handoffs to maintain continuity.

## Static vs. Living State

### CLAUDE.md is Static

`CLAUDE.md` is the project constitution. It describes **how the project works**, not **what has been done**. Agents never modify it.

CLAUDE.md contains:
- Build commands and prerequisites
- Project structure and tech stack
- Known quirks and landmines (QVM compiler bug, IDBFS, brush winding)
- Architectural constraints and decisions
- Testing and validation instructions
- Pointers to living state files

CLAUDE.md does NOT contain:
- Current implementation status (that's `claude-progress.txt`)
- Feature roadmap or task lists (that's `features.json`)
- Lists of files modified for specific features (that's git history)

### Living State Files

These are the agent's memory between sessions:

- **`claude-progress.txt`** — free-form notes: what's done, what's in progress, blockers, next steps. Updated by the agent at the end of every session and after every major milestone.
- **`features.json`** — the immutable feature contract (see below). Agent only flips `"failing"` to `"passing"`.
- **Git history** — the actual record of what changed and why. Agents commit early and often.

## Session Structure

### Startup Checklist

Every session begins with:

1. Read `claude-progress.txt` and recent git log to understand current state
2. Read `features.json` to find the highest-priority incomplete feature
3. Verify the build compiles cleanly before making changes
4. Begin work on a single feature

### Work Loop

For each feature:

1. Implement the minimum change needed
2. Build and test (see Validation below)
3. Commit with a message referencing the feature name
4. Update `claude-progress.txt`
5. Mark the feature as passing in `features.json` only after validation
6. Move to the next feature

### Session End

Before context runs out or work is paused:

1. Commit all work in progress (even if incomplete — use `[WIP]` prefix)
2. Update `claude-progress.txt` with: what was accomplished, what's partially done, what to do next, any blockers or discoveries
3. Ensure submodule state is committed in the parent repo if changed

## Feature List as a Contract

- `features.json` contains every planned feature, each starting as `"failing"`
- Features are **never removed or edited** — only marked as `"passing"` once implemented and validated
- This prevents the agent from prematurely declaring the project "done"
- Features should be granular enough that each is achievable in a single session

## Git Discipline

### Commit Early, Commit Often

- Commit after each meaningful change, not just at the end of a feature
- Every commit message must reference which feature it relates to
- Use conventional format: `feat(titan-enter): add embark command and entity spawn`
- WIP commits are fine: `[WIP] feat(titan-enter): entity spawns but no collision yet`

### Submodule Awareness

The engine lives in `external/ioq3` (a git submodule). When modifying engine code:

- Commit inside the submodule first (`cd external/ioq3 && git add && git commit`)
- Then commit the submodule reference update in the parent repo
- Never leave the parent repo pointing at an uncommitted submodule state
- Both repos must tell a coherent story in their git logs

### Revert Safety

Frequent commits exist so that broken changes can be reverted cleanly. If a feature implementation breaks something and can't be fixed quickly, `git revert` the commits and move on. Don't spend a full session debugging one issue.

## Validation

### Build Validation

Every change must compile. Run the build and check the exit code. If it fails, fix it before committing.

### Runtime Validation

For any gameplay or server-side feature:
- Start the dedicated server with the new code
- Verify the server starts without errors
- Connect a client and exercise the feature
- Check server console for crashes, warnings, or error messages

### Visual / UI Validation

For any feature that has a visible effect (player model changes, HUD elements, movement mechanics, visual effects):
- **Take a screenshot** proving the feature works as expected
- Save screenshots to `docs/screenshots/` with descriptive names: `titan-embark-sequence.png`, `wallrun-third-person.png`
- A feature with visual output is not "passing" without a screenshot showing it working

### What "Passing" Means

A feature can only be marked `"passing"` in `features.json` when ALL of:
1. The code compiles without new warnings
2. The server starts and runs without errors
3. The feature works as described in the feature spec
4. Visual features have screenshot evidence
5. The change is committed with a proper message

## Context Window Hygiene

Context is finite and precious. Do not waste it on noise.

### Build Output

- **Never** dump raw build output into the conversation. Pipe builds to a log file: `cmake --build build 2>&1 | tee /tmp/build.log`
- Check the exit code first. Only read the log file if the build failed.
- When reading error logs, grep for `error:` — don't read the whole file.

### Server Output

- Redirect server output to a log file when testing
- Check for specific error patterns (`ERROR`, `FATAL`, `BAD`) rather than reading the full log
- Pre-filter output before consuming it as context

### General Rule

If a command produces more than ~50 lines of output, it should go to a file. The agent reads only what's needed from that file. Thousands of lines of compiler warnings burning context is thousands of lines not spent on implementation.

## Common Failure Modes

| Problem | Solution |
|---|---|
| Agent declares project "complete" prematurely | Immutable feature list — only flip failing to passing |
| Bugs go undocumented between sessions | `claude-progress.txt` updated after every milestone |
| Features marked done without real testing | Screenshot evidence required for visual features |
| Wasted context on build noise | Pipe output to files, grep for errors |
| Submodule state drifts from parent repo | Always commit submodule first, then parent |
| Agent rewrites CLAUDE.md with status updates | CLAUDE.md is static — state goes in progress files |
| Agent spends full session debugging one bug | Revert and move on — frequent commits enable this |

## Design Principles

1. **Treat agents like shift workers** — clear handoff docs, defined tasks, structured progress tracking
2. **Small increments over big sweeps** — one feature at a time, committed and documented
3. **Artifacts are the memory** — git history + progress files bridge context windows
4. **Testing is non-negotiable** — verify in the actual environment before marking done
5. **Never edit the spec to match the code** — the feature list is the source of truth
6. **Protect context** — log files over stdout, grep over cat, precision over thoroughness
7. **Git is the backbone** — commit often, commit descriptively, commit submodules coherently
