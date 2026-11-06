---
title: "Course Blueprint Approval Gate & High-Density Grounded Section Plans"
ticket: 13
status: done
---

# Implementation Plan & Execution: Story 12.13 (CAP-2, AD-4)

## Overview
Reconcile curriculum creation with Gate 2 (Curriculum Blueprint Approval) and generate high-density section lesson plans strictly grounded in harvested authoritative literature.

## Key Changes Made
1. **Source Discovery & Mapping (`_tc/scripts/source_mapper.py`)**:
   - Expanded source candidate directories to include `_tc/research/<slug>/sources/markdown/`, `_tc/research/<slug>/sources/raw/`, and legacy source trees while ignoring metadata files.
   - Saves canonical `_tc/courses/<slug>/source-map.toml` with line spans, headings, and verbatim anchors, and mirrors to `courses/<slug>/.tc/source-map.toml`.
   - Updated `read_source_pointer` to check canonical `_tc/courses/<slug>/source-map.toml` first with robust source markdown resolution.

2. **Blueprint & High-Density Section Plan Scaffolding (`_tc/scripts/course_builder.py`)**:
   - Compiles source-map prior to lesson plan scaffolding to bind exact line spans into section plans.
   - Generates `_tc/courses/<slug>/blueprint.md` (and `courses/<slug>/.tc/blueprint.md`) featuring header metadata, deliberation summary, comprehensive curriculum structure with prerequisites, and verification strategy.
   - Generates high-density `lesson-plan.md` in both `_tc/courses/<slug>/plans/...` and `courses/<slug>/.tc/plans/...` featuring:
     - **Teaching Plan**: 3-step pedagogical flow (Intuitive Metaphor & Core Invariant -> Technical Formalism -> Applied Practical Exercise), core invariants checklist, and verified prerequisites.
     - **Source-Coverage Map**: Grounded citations with source IDs, heading breadcrumbs, and exact line spans.
     - **Verification Plan**: Bloom diagnostic probes (Bloom 2 Comprehension, Bloom 4 Analysis, Bloom 5 Evaluation), failure injection scenarios, and explicit mastery criteria.
     - **Next Action on Completion**: Directives for notes compilation, ledger logging, and triggering section-close gate.
   - Canonicalizes course manifest writing to `_tc/courses/<slug>/course.toml` as well as `courses/<slug>/.tc/course.toml`.

3. **Curriculum Approval Gate 2 (`_tc/scripts/checkpoint_manager.py`)**:
   - Updated `create_approval_gate` to surface `_tc/courses/<slug>/blueprint.md` path in prompt and metadata.
   - Preserves interactive options `[1] Start Lesson 1` and `[2] Adjust Roadmap` while auto mode auto-approves with memlog tracking.

4. **Runtime Synchronization & Verification**:
   - Synced scripts across runtime and skills directories.
   - Verified with unit tests in `tests/test_blueprint_and_section_plans.py` and `tests/test_interactive_gates.py`.
