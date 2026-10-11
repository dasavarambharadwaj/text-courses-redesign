---
title: "Implement Sovereign Faculty Personas, Chiron Onboarding, and Adaptive Tag-Team Handoffs"
type: "feature"
ticket: 5
created: "2026-10-11"
status: "done"
baseline_revision: "9fb2bc994d17118d8327a3e847fffc4a8408ddc4"
route: "oneshot"
route_source: "auto"
risk: "medium"
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

**Problem:** Learners previously had to configure clinical, abstract sliders (e.g., word count density, style tags) rather than learning from authentic, living master teachers. Furthermore, when learners struggled with repeated explanations, tutors lacked an adaptive tag-team handoff mechanism to bring in a fresh pedagogical perspective with shared memory. Finally, skills lacked standardized packaging manifests (`bmod.toml`) and customizable personas (`customize.toml`).

**Approach:** Equip all 10 skills with `bmod.toml` and 3-tier `customize.toml` declaring the 10 Sovereign Faculty personas. Update `skills/tc-init/SKILL.md` so Chiron conducts direct faculty hiring persisted to `profile/preferences.md`. Update `skills/tc-teach/SKILL.md` and `teach_engine.py` to adapt instructional tone to the chosen teacher and execute adaptive tag-team faculty handoffs on repeated friction, logging handoffs atomically to `courses/<slug>/memlog.md` via `memlog.py`.

</frozen-after-approval>

## Implementation Notes

Completed oneshot implementation of FR-24, FR-25, and FR-29 Sovereign Faculty Personas, Chiron Onboarding, and Tag-Team Handoffs. All 197 unit tests pass.

## Review Triage Log

- quick-lens: All acceptance criteria met; unit tests pass (197 passing); bmod.toml and customize.toml added to all 10 skills; sovereign faculty personas defined; teacher choice persisted to preferences; tag-team handoff support in teach_engine and tc-teach; memlog.py handoff logging; zero BMad references verified.
