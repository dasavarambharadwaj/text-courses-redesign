---
title: "Implement tc-roadmap Skill and Triad Inception Party Mode"
type: "feature"
ticket: 4
created: "2026-10-11"
status: "done"
baseline_revision: "9fb2bc994d17118d8327a3e847fffc4a8408ddc4"
route: "oneshot"
route_source: "auto"
risk: "high"
review: "quick"
review_source: "pinned"
lenses_ran: ["quick-lens"]
review_loop_iteration: 1
context:
  - "_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md"
  - "_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md"
  - "_bmad-output/initiative-textcourses/epic-faculty-roadmap-memlog/epic-faculty-roadmap-memlog.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Learners embarking on expansive macro domains (e.g. Distributed Systems, Machine Learning Engineering, Compilers) cannot fit the entire scope into a single course without severe context bloat or superficial treatment. Learners also lack a guided multi-course roadmap architecture and diagnostic placement testing to waive known subjects.

**Approach:** Implement `skills/tc-roadmap/SKILL.md` orchestrated by 🗺️ Aristotle (The Cartographer). Integrates the Triad Inception Roundtable Party Mode caucus (🔬 Marie the Empirical Scout, 🗺️ Aristotle the Cartographer, ⚖️ Hypatia the Logic Auditor), generates `roadmap/roadmap.toml` and `roadmap/overview.md`, conducts 2–4 hinge diagnostic placement questions to mark mastered courses as `[WAIVED]`, logs inception events to `profile/memlog.md`, and dispatches the first active course to `/tc-create`.

</frozen-after-approval>

## Implementation Notes

Initial oneshot implementation of FR-26 and FR-27 tc-roadmap skill and Triad Inception Party Mode. All 190 tests pass.

## Review Triage Log

- quick-lens: All acceptance criteria met; unit tests pass; Triad Inception caucus, placement tests, and zero BMad references verified.
