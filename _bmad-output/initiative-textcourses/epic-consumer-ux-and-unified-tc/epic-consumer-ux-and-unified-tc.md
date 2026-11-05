---
type: epic
title: "Consumer UX, Unified /tc Dispatcher & Clean Workspace Substrate"
parent: initiative-textcourses
covers: [CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6]
after: [epic-multi-source-deterministic-compiler]
assignee: ""
status: done
risk: medium
---

# Epic 12: Consumer UX, Unified `/tc` Dispatcher & Clean Workspace Substrate

**Initiative**: `initiative-textcourses`  
**Slug**: `epic-consumer-ux-and-unified-tc`  
**Status**: done  
**Covers**: CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6  
**References**:
- Spec: `_bmad-output/initiative-textcourses/spec-consumer-ux-and-unified-tc/spec-consumer-ux-and-unified-tc.md`
- Flowchart: `_bmad-output/initiative-textcourses/spec-consumer-ux-and-unified-tc/interaction-flowchart.md`
- Hierarchy: `_bmad-output/initiative-textcourses/spec-consumer-ux-and-unified-tc/workspace-hierarchy.md`

## Executive Summary
This epic addresses user experience friction by transforming the deterministic multi-source engine into a serene, consumer-grade personal tutor:

1. **Pure-Python Drop-in Workspace Auto-Ingestion (`CAP-3`)**:
   - Automatically detects `.pdf` and `.epub` files placed anywhere in the workspace (`/`, `books/`, `sources/`, `research/`) and invokes `extractor.py` silently with pre-flight scanned-image density checks.

2. **Two-Tier Clean Workspace Substrate (`CAP-4`)**:
   - Encapsulates internal machine state (`course.toml`, `source-map.toml`, `coverage-ledger.md`, `memlog.md`, `session.jsonl`, `plans/`) inside a hidden `courses/<slug>/.tc/` folder, surfacing only `overview.md` and compiled `notes/` in the user's course root.
   - Dual-path search fallback maintains 100% backwards compatibility for existing courses.

3. **Token-Bounded Deliberation Summarizer (`CAP-5`)**:
   - Runs multi-agent Triad consensus silently in the background, outputting a concise $\le 40$-word summary paragraph to the chat, while preserving full debate traces in `.tc/consensus-deliberation.md`.

4. **Interactive Checkpoint Gates & Material Acquisition Pause (`CAP-2`)**:
   - Eliminates unattended steamrolling by pausing at key pedagogical milestones:
     - Missing material acquisition pause (drop proprietary book or proceed with open docs).
     - Curriculum approval gate (syllabus review before scaffolding).
     - 4-Option Action Fork after every lesson turn.

5. **Unified `/tc` Skill & Intelligent State Machine (`CAP-1`, `CAP-6`)**:
   - Single front door `/tc` that dispatches based on workspace context (intake -> curriculum -> lesson delivery).
   - Preserves all power-user subcommands (`/tc test`, `/tc practical`, `/tc notes`, etc.) and the high-velocity 4-Option Action Fork.

6. **Full Verification Suite & Zero-BMad Invariant**:
   - Comprehensive test suite validating end-to-end consumer UX, with 0 regressions across all 296 existing tests and zero references to BMad.

## Done When
1. Dropping a PDF into workspace auto-triggers extraction and density probe without manual CLI commands.
2. New courses encapsulate engine state in `.tc/` while keeping `overview.md` and `notes/` clean; all engine scripts fall back cleanly to legacy root paths.
3. Triad deliberation chat summaries are strictly $\le 40$ words.
4. Interactive gates pause gracefully at missing books, curriculum approval, and action forks.
5. `/tc` routes seamlessly through all stages of the learning lifecycle.
6. Full regression suite passes with 100% test success and Zero-BMad compliance.
