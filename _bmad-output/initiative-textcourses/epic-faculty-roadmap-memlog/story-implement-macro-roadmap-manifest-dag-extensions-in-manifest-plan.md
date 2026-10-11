---
title: "Implement Macro-Roadmap Manifest & DAG Extensions in manifest.py and dag.py"
type: "feature"
ticket: 3
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

**Problem:** `manifest.py` and `dag.py` only managed single-course schemas (`course.toml`), lacking subcommands and graph algorithms for multi-course macro roadmap orchestration (`roadmap.toml`) where tracks declare sequences of courses with inter-course prerequisite DAGs, dynamic course addition, cycle verification, and status advancement (`not_started`, `active`, `completed`, `waived`).

**Approach:** Extend `manifest.py` with `add-course` and `advance-course` subcommands for `roadmap.toml` manifests, enhance `manifest.py validate` for roadmap courses, and extend `dag.py` to parse and topologically sort multi-course roadmap DAGs, detecting cycles and missing antecedent courses at zero token cost.

</frozen-after-approval>

## Implementation Notes

Initial oneshot implementation of FR-26 roadmap manifest and DAG engine extensions. All 186 unit tests pass.

## Review Triage Log

- quick-lens: All acceptance criteria met; unit tests pass; multi-course DAG validation and status progression verified.
