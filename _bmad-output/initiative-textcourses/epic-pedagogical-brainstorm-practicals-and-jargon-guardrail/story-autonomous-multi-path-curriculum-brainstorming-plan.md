# Story Plan: Autonomous Multi-Path Curriculum Brainstorming & Hat Validation

**Story ID**: 2  
**Epic**: `epic-pedagogical-brainstorm-practicals-and-jargon-guardrail`  
**Status**: in-progress  
**Covers**: FR-35  

## Context & Objectives
Course creation must never stall by asking the learner "what way do you want this course created?".
Instead, `course_builder.py` and `/tc-create` must autonomously generate four distinct curricular philosophies:
1. **Foundational / First-Principles Path**: Formal theory, axioms, mathematical invariants, and systematic bottom-up building.
2. **Hands-on / Project-First Path**: Build working artifacts from Day 1, introducing theoretical mechanics just-in-time.
3. **Problem-Driven / Diagnostic Path**: Start from production failure modes, postmortems, and debugging scenarios.
4. **Intuitive / Metaphor-First Path**: Visceral everyday mental models and high-level architectural intuition down to implementation.

These 4 architectures are then subjected to the Universal Critical Hats (Applied Practitioner, Academic Purist, Beginner Friction Hunter, Edge-Case Systems Engineer, Resource Optimizer).
The Triad (Daedalus, Marie, Hypatia) debates the merits, synthesizes the optimal hybrid tailored to the learner's preferences, and outputs:
- `courses/<slug>/curriculum-brainstorm.md`
- `courses/<slug>/consensus-deliberation.md`
- Complete course files without user prompting.

## Acceptance Criteria
1. `course_builder.py` contains `brainstorm_curriculum_paths()` generating the 4 structural models.
2. The paths are evaluated by the Universal Critical Hats and debated by the Faculty Triad.
3. The resulting synthesis is written to `courses/<slug>/curriculum-brainstorm.md`.
4. `/tc-create` skill documentation and scripts operate 100% autonomously without interactive questionnaire prompts.
5. Unit tests verify multi-path generation, critical evaluation, and brainstorm output.
