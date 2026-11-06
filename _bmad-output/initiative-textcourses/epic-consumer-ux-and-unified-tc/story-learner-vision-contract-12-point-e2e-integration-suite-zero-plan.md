---
title: "Learner Vision Contract 12-Point E2E Integration Suite & Zero Regressions"
ticket: 16
status: done
covers: ["CAP-1", "CAP-2", "CAP-3", "CAP-4", "CAP-5", "CAP-6", "CAP-7", "CAP-8", "CAP-9", "CAP-10", "FR-46", "FR-47", "FR-48", "FR-49", "FR-50"]
---

# Story 12.16 Plan: Learner Vision Contract 12-Point E2E Integration Suite & Zero Regressions

## Objective
Implement an end-to-end integration test suite verifying all 12 points of the Learner Vision Contract against real runtime execution, confirming 100% passing across the entire test suite (385 tests) and strict Zero-BMad compliance.

## Verification Checklist
- [x] **Point 1 (Single Public Export)**: Only `skills/tc/` exists in public exports; internal engines reside in `_tc/skills/`.
- [x] **Point 2 (Clean Canvas Workspace)**: Root workspace contains only `courses/`, `status-board/`, and `_tc/`; learner visible course dirs contain only `overview.md`, `notes/` (`chapter-XX.md`), and hidden `.tc/`.
- [x] **Point 3 (5-Stage Intake & Mode Selection)**: Stage 1 records mode in `_tc/profile/preferences.yaml`.
- [x] **Point 4 (Multi-Source Discovery Proposal)**: Interactive source proposal formats canonical books and official documentation before proceeding.
- [x] **Point 5 (Zero-Loss Markdown Conversion)**: Sources convert to clean Markdown with conversion coverage ledger in `_tc/courses/<slug>/conversion-coverage.json`.
- [x] **Point 6 (Canonical 4-Hat Adversarial Research Debate)**: 4 distinct personas conduct structured research debate, logged to `_tc/research/<slug>/debate.jsonl`.
- [x] **Point 7 (Blueprint Scaffolding & Approval Gate)**: Gate 2 displays `_tc/courses/<slug>/blueprint.md` with approval before course generation.
- [x] **Point 8 (High-Density Grounded Section Plans)**: Section plans feature explicit source line citations, 3-step pedagogical flow, and Bloom diagnostic probes.
- [x] **Point 9 (Mandatory Section-Close Gate)**: Teaching progression halts until section-close approval is granted.
- [x] **Point 10 (Visible Chapter Notes Compilation)**: Section close writes compiled textbook notes to `courses/<slug>/notes/chapter-XX.md`.
- [x] **Point 11 (Scoped Memlogs Engine)**: Course-level memlogs stored in `_tc/courses/<slug>/memlog.md` and learner-level in `_tc/profile/memlog.md`.
- [x] **Point 12 (Self-Contained Local Interactive Status Dashboard)**: `status-board/index.html` generated with zero external network requests, rendering complete state snapshot.
- [x] **Zero-BMad Compliance**: Zero references to BMad in public runtime packages, skills, or scripts.
- [x] **Regression Prevention**: 385/385 tests passing green.
