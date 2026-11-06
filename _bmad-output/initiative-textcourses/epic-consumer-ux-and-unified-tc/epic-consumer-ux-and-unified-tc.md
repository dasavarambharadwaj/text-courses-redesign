---
type: epic
title: "Consumer UX, Unified /tc Dispatcher & Clean Workspace Substrate"
parent: initiative-textcourses
covers: [CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6, CAP-7, CAP-8, CAP-9, CAP-10, FR-46, FR-47, FR-48, FR-49, FR-50]
after: [epic-multi-source-deterministic-compiler]
assignee: ""
status: in-progress
risk: high
---

# Epic 12: Consumer UX, Unified `/tc` Dispatcher & Clean Workspace Substrate

**Initiative**: `initiative-textcourses`  
**Slug**: `epic-consumer-ux-and-unified-tc`  
**Status**: in-progress  
**Covers**: CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6, CAP-7, CAP-8, CAP-9, CAP-10, FR-46, FR-47, FR-48, FR-49, FR-50  
**References**:
- Approved Sprint Change Proposal: `_bmad-output/initiative-textcourses/change-reconcile-flow-and-unattended-compiler/change-reconcile-flow-and-unattended-compiler.md`
- Escalation Notice: `_bmad-output/initiative-textcourses/change-reconcile-flow-and-unattended-compiler/escalation-notice.md`
- Spec: `_bmad-output/initiative-textcourses/spec-consumer-ux-and-unified-tc/spec-consumer-ux-and-unified-tc.md`
- Flowchart: `_bmad-output/initiative-textcourses/spec-consumer-ux-and-unified-tc/interaction-flowchart.md`
- Hierarchy: `_bmad-output/initiative-textcourses/spec-consumer-ux-and-unified-tc/workspace-hierarchy.md`

## Executive Summary
This epic serves as the overarching **Integration & Delivery Epic** reconciling the entire TextCourses runtime with the 12-point Learner Vision Contract established in the approved Major Sprint Change Proposal (`change-reconcile-flow-and-unattended-compiler.md`).

1. **Root `_tc/` Storage Substrate & Granular Memory (`CAP-4`, `FR-29`, `AD-15`)**:
   - Consolidates all engine internals, research dossiers, raw sources, course machine files, and decisions under a canonical `_tc/` root.
   - Preserves `courses/<slug>/notes/chapter-XX.md` as the sole visible study material on the learner's canvas.
   - Enforces hierarchical scoped memlogs across workspace, research, course, chapter, and section levels.

2. **Single Public `/tc` Entrypoint & Skill Encapsulation (`CAP-1`, `FR-46`, `AD-14`)**:
   - Strictly exports only `skills/tc/` in the agent harness (`skills-lock.json`); encapsulates all internal engines under `_tc/skills/`.
   - Routes all learner lifecycle interactions through `tc.py dispatch`, resolving the `proceed_open` continuation so topic-only runs scaffold seamlessly.

3. **Intake Execution Modes & Unattended Course Creation (`CAP-7`, `FR-47`, `AD-16`)**:
   - Captures learner execution mode (`interactive` vs `auto`) during 5-stage intake and persists in `_tc/profile/preferences.md`.
   - Auto mode executes the entire curriculum creation pipeline unattended without pausing, logging all decisions to memlog.

4. **Multi-Source Community Discovery & Interactive Approval Loop (`CAP-8`, `FR-43`)**:
   - Scans books, research papers, official RFCs/specs, GitHub repos, Reddit, Quora, and web to synthesize `_tc/research/<slug>/source-proposal.md`.
   - Interactive loop allows approval, requesting more research, adding/removing sources, or stopping, with graceful fallbacks for missing material.

5. **Zero-Loss Markdown Conversion & Coverage Audit (`CAP-3`, `FR-48`)**:
   - Converts multi-format sources into clean markdown under `_tc/research/<slug>/sources/markdown/` with 0% text omission.
   - Emits `conversion-ledger.json` and `conversion-ledger.md` mathematically proving conversion coverage.

6. **Canonical 4-Hat Adversarial Research Debate (`CAP-5`, `FR-30`, `FR-31`)**:
   - Conducts genuine multi-agent dialectic debate rounds across 4 archetypes (Architect, Investigator, Auditor, Strategist).
   - Records debate rounds and decisions in `_tc/research/<slug>/debate.jsonl` with an executive summary.

7. **Blueprint Approval Gate & Grounded Section Plans (`CAP-2`, `AD-4`)**:
   - Scaffolds `_tc/courses/<slug>/blueprint.md` for Gate 2 review prior to file generation.
   - Compiles high-density section plans specifying teaching flow, exact line spans in `source-map.toml`, and Bloom verification rubrics.

8. **Mandatory Section-Close Gate & Ephemeral Session Scrub (`CAP-6`, `CAP-9`, `FR-11`, `FR-49`, `AD-16`)**:
   - Enforces mandatory section sign-off gate across both interactive and auto modes upon mastering the final concept.
   - Compiles visible chapter notes, appends milestone entries to scoped memlogs, and permanently scrubs section conversation transcripts (`session.jsonl`).

9. **Self-Contained Local Interactive Status Dashboard (`CAP-10`, `FR-50`, `AD-17`)**:
   - Static generator outputs `status-board/index.html` from `_tc/status/state.json` on init and every state mutation.
   - Opens locally via `file://` with zero network, CDN, or server dependencies, rendering roadmap DAG, active concept pointer, harvested sources, and filtered memlog timeline.

10. **12-Point Vision Contract E2E Suite & Zero Regressions**:
    - End-to-end integration test suite (`tests/test_vision_contract.py`) asserting all 12 points of the learner vision against real runtime behavior, with 100% green status across 326+ baseline tests.

## Notes & Decisions
- `Decision: 2026-11-06 — Reopened under Major sprint change change-reconcile-flow-and-unattended-compiler.md to align with the 12-point learner vision contract.`
- `Decision: 2026-11-06 — Separate Refactor Sweep story omitted (Set Check 2.5) because Story 7 cleans the storage substrate upfront, Story 8 enforces strict public/internal packaging boundaries, and Story 16 enforces full-code Zero-BMad and zero-regression audit.`
- `Decision: 2026-11-06 — Stories 1–6 represent the initial MVP pass; Stories 7–16 constitute the authoritative sequential replan and integration lane.`

## Done When
1. Root `_tc/` is the sole authoritative storage root; all legacy directories migrate cleanly; only `courses/<slug>/notes/` remains visible.
2. Exactly one skill (`skills/tc/`) is public; `tc.py dispatch` continuation progresses without dead ends.
3. 5-stage intake captures `--mode interactive|auto`; auto mode runs curriculum creation unattended with full decision logging.
4. `scout.py` generates `source-proposal.md` spanning books, papers, RFCs, GitHub, and web; interactive gate supports approve/more/stop.
5. Extractor produces zero-loss markdown under `_tc/research/<slug>/sources/markdown/` verified by `conversion-ledger.md`.
6. Genuine 4-hat dialectic debate runs before syllabus scaffolding, emitting `debate.jsonl`.
7. Gate 2 presents `blueprint.md` prior to section generation; section plans contain line spans and verification rubrics.
8. Section Close Gate pauses in all modes; compiles visible chapter notes; permanently scrubs section transcript.
9. `status-board/index.html` opens offline via `file://` with 0 external network requests, rendering complete workspace state.
10. All 12 points in `tests/test_vision_contract.py` pass; full pytest suite passes with 0 failures and zero regressions against 326 baseline.
