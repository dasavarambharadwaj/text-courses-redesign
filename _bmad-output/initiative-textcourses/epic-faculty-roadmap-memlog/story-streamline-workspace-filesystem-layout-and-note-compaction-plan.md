---
title: "Streamline Workspace Filesystem Layout and Note Compaction"
type: "refactor"
ticket: 2
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

**Problem:** The v1 filesystem layout created cognitive friction and confusion between `.tc/` and `_tc/`, hid internal engine configurations and caches in hidden dot-directories, buried textbook notes 4 levels deep in individual section directories (`courses/<slug>/chapter-XX/section-YY/notes.md`), and lacked unified macro-roadmap (`roadmap/`) and profile (`profile/`) root locations.

**Approach:** Refactor `bootstrapper.py`, `course_builder.py`, `notes_compiler.py`, and supporting scripts to standardize on the sovereign `_tc/` engine root (unifying scripts, cache, and config), initialize `profile/` and `roadmap/` directories, initialize course-level `memlog.md`, scaffold flat chapter textbook notes at `courses/<slug>/notes/chapter-XX.md` while maintaining backwards compatibility with legacy layout.

</frozen-after-approval>

## Implementation Notes

Initial oneshot implementation of FR-29 filesystem streamlining. All 182 tests pass.

## Review Triage Log

- quick-lens: All acceptance criteria met; unit tests pass; backwards compatibility verified.
