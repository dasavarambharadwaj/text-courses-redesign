# Story Plan: Beginner-to-Core Pedagogical Adaptation

**Story ID**: 1  
**Epic**: `epic-pedagogical-brainstorm-practicals-and-jargon-guardrail`  
**Status**: in-progress  
**Covers**: FR-34  

## Context & Objectives
When a user declares themselves as a `beginner` (or novice/starter), the entire engine must calibrate to this constraint:
- **Research (`scout.py` / `/tc-research`)**: Prioritize `beginner_friction_hunter` and `intuitive_metaphorist` hats. Expose implicit domain assumptions and flag cognitive friction points.
- **Course Creation (`course_builder.py` / `/tc-create`)**: Set `competency_level = "beginner"`. Enforce prerequisite laddering, scaffold smaller pedagogical increments, and avoid jumping into complex architecture.
- **Teaching (`teach_engine.py` / `/tc-teach`)**: Assign primary pedagogical lead to **Hypatia (The Empathetic Tutor)** or Feynman. Enforce gentle Socratic pacing and strictly forbid unexplained abstractions.
- **Testing (`diagnostic_tester.py` / `/tc-test-me`)**: Focus diagnostic probes on conceptual intuition and fundamental mechanics before testing edge cases.

## Acceptance Criteria
1. `course_builder.py` detects beginner profile settings or prompt cues and generates beginner-adapted chapters with explicit foundational prerequisite laddering.
2. `scout.py` dynamically prioritizes `beginner_friction_hunter` and `intuitive_metaphorist` when beginner focus is specified.
3. `teach_engine.py` adjusts cognitive load, sets Hypatia as primary tutor, and forbids unexplained leaps.
4. Comprehensive unit tests verify beginner calibration across the lifecycle.
