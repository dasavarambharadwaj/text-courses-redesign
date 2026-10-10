---
title: "Implement textbook notes compiler and section transition manager (notes_compiler.py)"
type: "feature"
ticket: 2
created: "2026-10-10"
status: done
baseline_revision: "ec491ac"
route: "full"
route_source: "auto"
risk: "medium"
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

**Problem:** Learners need an authoritative, sovereign reference textbook compiling everything they learn without having to manually summarize chat logs or pause their flow state.
**Approach:** Implement `_tc/scripts/notes_compiler.py`. Upon completing all checklist concepts in a section, the compiler automatically distills the lesson into a permanent `notes.md` (3-bullet recap, technical mechanics, worked examples, fatal mistakes) and atomically transitions the section status in `course.toml` from `in_progress` to `review`.

## Boundaries & Constraints

**Always:**
- Include PEP 723 inline script header (`requires-python = ">=3.11"`, `tomli-w>=1.0.0`).
- Produce structured textbook `notes.md` containing a 3-bullet recap, core mechanics, worked examples, and fatal mistakes (FR-11).
- Strictly preserve existing notes: never overwrite an existing `notes.md` file without explicit append or confirmation (AD-3, AD-7).
- Update section status in `course.toml` to `review` atomically upon successful compilation.
- Output structured JSON to stdout on exit 0, stderr on exit 1.
- Strict zero BMad references.

**Never:**
- Never delete or corrupt existing completed notes.
- Never advance a section status to `review` if `notes.md` write fails.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Section Notes Compilation | `notes_compiler.py compile --section-dir <sec_dir> --title "..." --recap "b1" "b2" "b3"` | Writes `notes.md`; updates `course.toml` to `review`; exits 0 | If course.toml missing, writes notes with warning |
| Existing Notes Collision | `compile` called on directory already having `notes.md` | Rejects overwrite with `"already_exists": true`, exits 1 | Preserves existing file intact |
| Inspect Notes State | `notes_compiler.py inspect --section-dir <sec_dir>` | Reports presence, size, recap items, and course status, exits 0 | If missing notes.md, reports compiled: false |

</frozen-after-approval>

## Code Map

- `_tc/scripts/notes_compiler.py` -- Deterministic notes compiler and course section transition engine.
- `tests/test_notes_compiler.py` -- Pytest test suite covering textbook notes formatting, non-destructive write safety, course.toml transition, and zero BMad references.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/notes_compiler.py` -- Implement notes compiler CLI with `compile` and `inspect` subcommands (FR-11, AD-3).
- [x] `tests/test_notes_compiler.py` -- Unit tests validating 3-bullet recap formatting, atomic write, course status transition, and zero-BMad invariant.

**Acceptance Criteria:**
- Given section completion, `notes_compiler.py compile` writes valid `notes.md` with 3-bullet recap and marks section as `review` in `course.toml`.
- Re-compiling refuses to overwrite existing notes without error flag.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes

Implemented `notes_compiler.py` with PEP 723 metadata, 3-bullet recap textbook formatting, collision prevention preserving immutable notes, and atomic section status transition to 'review' in `course.toml`.

## Plan Change Log

## Review Triage Log

- Verified 6/6 unit tests in `tests/test_notes_compiler.py` pass cleanly.
- Verified 151/151 full test suite pass cleanly.
- Verified zero BMad references across scripts and tests.
- Verified collision safety preventing accidental overwrite of existing notes.

## Verification

**Commands:**
- `uv run _tc/scripts/notes_compiler.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_notes_compiler.py` -- expected: All unit tests pass with exit code 0.
