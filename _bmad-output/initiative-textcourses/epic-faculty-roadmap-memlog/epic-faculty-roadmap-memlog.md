---
type: epic
title: "Personality-Driven Faculty, Macro-Roadmap & Sovereign Memory"
parent: initiative-textcourses
covers: [FR-24, FR-25, FR-26, FR-27, FR-28, FR-29]
after: [epic-onboarding-lifecycle, epic-curriculum-creation, epic-instruction-delivery]
assignee: ""
risk: medium
status: done
---

# Epic 6: Personality-Driven Faculty, Macro-Roadmap & Sovereign Memory

## Overview
Epic 6 delivers the major architectural evolution of **TextCourses 2.0**:
1. **The Sovereign Faculty**: Replaces dry clinical configuration sliders with living master teacher personas (Feynman, Euclid, Socrates, Leonardo, etc.) and adaptive tag-team faculty handoffs.
2. **Macro-Roadmap Architecture (`tc-roadmap`)**: Unlocks multi-course curriculum tracks (e.g. Data Science) via live Triad Inception Party Mode (Marie, Aristotle, Hypatia) and diagnostic placement testing.
3. **Two-Tier Pedagogical Memlog**: Implements persistent, append-only conversational memory for the learner's journey (`profile/memlog.md` and `courses/<slug>/memlog.md`).
4. **Streamlined Sovereign Filesystem Layout**: Eliminates `.tc/` vs `_tc/` ambiguity and flattens deeply nested notes into accessible chapter textbooks.
5. **Full BMad Ecosystem Parity**: Standards-compliant `bmod.toml` manifests, 3-tier `customize.toml` configuration, and single-source runtime scripts.

## Requirements Covered
- `FR-24`: Teacher Persona Selection & The Sovereign Faculty
- `FR-25`: Adaptive Faculty Tag-Team Handoffs & Dynamic Switching
- `FR-26`: Multi-Course Macro Roadmaps & DAG Orchestration (`tc-roadmap`)
- `FR-27`: Live Triad Inception Roundtable & Diagnostic Placement
- `FR-28`: Two-Tier Pedagogical Memory Logging (`_tc/scripts/memlog.py`)
- `FR-29`: Streamlined Sovereign Folder Architecture & BMad Ecosystem Parity

## Sliced Stories
1. `story-implement-two-tier-pedagogical-memlog-engine`: Standalone PEP 723 `_tc/scripts/memlog.py` engine and unit tests.
2. `story-streamline-workspace-filesystem-layout`: Refactor `bootstrapper.py`, `course_builder.py`, and `notes_compiler.py` to use visible `_tc/` and flat `notes/chapter-XX.md`.
3. `story-implement-macro-roadmap-engine-extensions`: Extend `manifest.py` and `dag.py` to support course additions, DAG verification, and status advancement in `roadmap.toml`.
4. `story-implement-tc-roadmap-skill-and-triad-party-mode`: Author `skills/tc-roadmap/` with Aristotle persona, Triad Party Mode caucus, and diagnostic placement.
5. `story-implement-sovereign-faculty-personas-and-tag-team-handoffs`: Configure `customize.toml` across all skills with 10 teacher personas, Chiron faculty onboarding, and `tc-teach` tag-team handoff hooks.
