---
title: "Implement session hygiene manager and lesson-plan progress tracker (lesson_tracker.py)"
type: "feature"
ticket: 1
created: "2026-10-10"
status: done
baseline_revision: "6b387c9"
route: "full"
route_source: "auto"
risk: "low"
review: "quick"
review_source: "pinned"
lenses_ran: []
review_loop_iteration: 0
context:
  - "_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md"
  - "_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md"
  - "_bmad-output/initiative-textcourses/epic-instruction-delivery/epic-instruction-delivery.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Chat sessions can be interrupted mid-lesson, and without persistent on-disk checklist state, agents repeat already-mastered concepts or lose lesson continuity.
**Approach:** Implement `_tc/scripts/lesson_tracker.py`. Inspects `lesson-plan.md` checklists, parses live concept checkmarks (`[ ]` vs `[x]`), resolves the current active concept for interruption recovery, and atomically updates checkmarks as concepts are taught.

## Boundaries & Constraints

**Always:**
- Include PEP 723 inline script header (`requires-python = ">=3.11"`, `tomli-w>=1.0.0`).
- Parse and update markdown checklists (`- [ ]` and `- [x]`) in `lesson-plan.md` (FR-12, AD-5).
- Use POSIX atomic writes (temp file + `os.fsync` + `os.replace`) to ensure zero file corruption on crash.
- Support `status`, `current`, and `tick` subcommands.
- Output structured JSON to stdout on exit 0, stderr on exit 1.
- Strict zero BMad references.

**Never:**
- Never modify user notes (`notes.md`) in `lesson_tracker.py`.
- Never corrupt markdown formatting or non-checklist headings in `lesson-plan.md`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Active Concept Lookup | `lesson_tracker.py current --path <section_dir>` | Returns first unchecked concept and index, exits 0 | If all checked, reports completed: true, exits 0 |
| Tick Off Concept | `lesson_tracker.py tick --path <section_dir> --index 1` | Replaces `[ ]` with `[x]` at index 1 atomically, exits 0 | If index out of bounds, exits 1 |
| Status Inspection | `lesson_tracker.py status --path <section_dir>` | Returns total, completed, remaining counts and list of items, exits 0 | If lesson-plan.md missing, exits 1 |
| Interruption Recovery | Call `current` on partially checked lesson plan | Returns the exact next unfinished concept without repeating previous | Idempotent |

</frozen-after-approval>

## Code Map

- `_tc/scripts/lesson_tracker.py` -- Deterministic lesson-plan checklist inspector and session hygiene tracker.
- `tests/test_lesson_tracker.py` -- Pytest test suite covering checklist parsing, tick updating, interruption recovery, and zero BMad references.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/lesson_tracker.py` -- Implement lesson tracker CLI with `status`, `current`, and `tick` subcommands (FR-12, AD-5).
- [x] `tests/test_lesson_tracker.py` -- Unit tests validating checklist parsing, atomic checkmark updating, interruption recovery, and zero-BMad invariant.

**Acceptance Criteria:**
- Given a `lesson-plan.md` with items, `lesson_tracker.py current` accurately identifies the first uncompleted concept.
- `lesson_tracker.py tick` updates the checklist item on disk atomically.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes

Implemented `lesson_tracker.py` with PEP 723 metadata, regex checklist parsing (`[ ]` vs `[x]`), interruption recovery via `current`, and atomic file updating via `tick`.

## Plan Change Log

## Review Triage Log

- Verified 7/7 unit tests in `tests/test_lesson_tracker.py` pass cleanly.
- Verified 145/145 full test suite pass cleanly.
- Verified zero BMad references across scripts and tests.
- Verified atomic checklist tick without corrupting non-checklist lines.

## Verification

**Commands:**
- `uv run _tc/scripts/lesson_tracker.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_lesson_tracker.py` -- expected: All unit tests pass with exit code 0.
