# Effective Harnesses for Long-Running Agents

> Reference notes from Anthropic's engineering blog post:
> https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

## Core Problem

Long-running agents must work across multiple context windows / sessions, each starting with no memory of prior work. This is analogous to shift-based engineers who need clear handoffs to maintain continuity.

## Two-Part Architecture

### 1. Initializer Agent

A specialized first session that bootstraps the project environment:

- **`init.sh` script** — automates dev server startup and environment setup so future sessions don't waste context on setup
- **`claude-progress.txt`** — a living document tracking what's been done, what's in progress, and what's next
- **Initial git commit** — establishes a clean baseline to track all agent-added files

### 2. Coding Agent

Subsequent sessions follow a structured, incremental approach:

- Work on a **single feature** per session
- Leave **clear artifacts** (progress notes, git commits) for the next session
- Maintain **clean, mergeable code** at all times

## Key Strategies

### Feature List as a Contract

- Create a comprehensive JSON feature list (200+ features) at project start
- Each feature starts as "failing"
- Features are never removed or edited — only marked as passing once properly implemented and tested
- This prevents the agent from prematurely declaring the project "done"

### Incremental Progress Pattern

- Work feature-by-feature, not all-at-once
- Git commit after each feature so problematic changes can be reverted
- Write progress summaries that the next session can read to pick up where you left off

### Session Startup Checklist

Every coding session begins with:

1. Run `pwd` to confirm the working directory
2. Read git logs and progress files to understand current state
3. Select the highest-priority incomplete feature
4. Begin work

### Testing as a Gate

- Agents tend to mark features as "complete" without proper testing
- Mitigate this by providing browser automation tools (e.g., Puppeteer MCP) for end-to-end verification
- Never trust a feature is done until it's been tested in the actual runtime environment

## Common Failure Modes

| Problem | Solution |
|---|---|
| Agent declares project "complete" prematurely | Maintain a comprehensive, immutable feature list |
| Bugs go undocumented between sessions | Initialize a git repo with structured progress notes |
| Features marked done without real testing | Provide browser automation tools for E2E verification |
| Wasted context on environment setup | Provide an `init.sh` script that handles all setup |

## Design Principles

1. **Treat agents like shift workers** — clear handoff docs, defined tasks, structured progress tracking
2. **Small increments over big sweeps** — one feature at a time, committed and documented
3. **Artifacts are the memory** — git history + progress files bridge context windows
4. **Testing is non-negotiable** — always verify in the actual environment before marking done
5. **Never edit the spec to match the code** — the feature list is the source of truth

## Open Questions

- Does a single general-purpose coding agent perform best, or is a multi-agent architecture (initializer + coder + tester) superior?
- These patterns may extend beyond web dev to domains like scientific research and financial modeling
