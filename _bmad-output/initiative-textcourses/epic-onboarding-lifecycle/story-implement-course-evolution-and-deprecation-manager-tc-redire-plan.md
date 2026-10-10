---
title: 'Story 2.2: Implement course evolution and deprecation manager (tc-redirect-course)'
type: 'feature'
ticket: 2
created: '2026-10-10'
status: 'draft'
baseline_revision: 'ce28f1f'
route: 'full'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context:
  - '_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md'
  - '_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md'
  - '_bmad-output/initiative-textcourses/epic-onboarding-lifecycle/epic-onboarding-lifecycle.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Ingested documentation sources change over time, but completed learner notes must remain immutable and permanent without losing contextual awareness of superseded content.

**Approach:** Implement `skills/tc-redirect-course/SKILL.md` and `skills/tc-redirect-course/scripts/redirector.py`. The redirector uses `hash_tracker.py` to identify source drift, identifies affected unfinished sections in `course.toml`, and prepends non-destructive deprecation notice blocks to completed `notes.md` without modifying historical notes bodies.

## Boundaries & Constraints

**Always:**
- Strictly preserve completed `notes.md` body content bit-for-bit when adding deprecation headers (FR-20, AD-7).
- Use `hash_tracker.py` to compute source deltas in `plan/sources/` (FR-19).
- Include PEP 723 script header in `redirector.py`.
- Output structured JSON to stdout on success (exit 0) and stderr on error (exit 1).
- Keep zero BMad references in user-facing prompts, templates, or scripts.

**Never:**
- Never rewrite, delete, or truncate completed sections in `course.toml` or `notes.md`.
- Never introduce external system daemon or database dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Detect Source Drift | `redirector.py diff-sources --path <course_dir>` | Returns list of modified/added source files and affected chapters, exits 0 | If plan/sources missing, exits 1 |
| Prepend Deprecation | `redirector.py deprecate --path <notes.md> --reason "API v2 superseded"` | Prepends markdown alert block to top of file preserving existing body, exits 0 | If file missing, exits 1 |
| Existing Deprecation | `redirector.py deprecate` on file already having alert | Does not duplicate alert, exits 0 | Idempotent |

</frozen-after-approval>

## Code Map

- `skills/tc-redirect-course/SKILL.md` -- Non-destructive course evolution and source update prompt.
- `skills/tc-redirect-course/scripts/redirector.py` -- Deterministic script for source delta inspection and note deprecation markers.
- `tests/test_redirector.py` -- Pytest test suite covering source diffing, notes deprecation prepending, and body immutability.

## Tasks & Acceptance

**Execution:**
- [ ] `skills/tc-redirect-course/scripts/redirector.py` -- Implement redirector CLI with `diff-sources`, `deprecate`, and `inspect` subcommands (FR-19, FR-20, AD-7).
- [ ] `skills/tc-redirect-course/SKILL.md` -- Implement course evolution skill prompt guiding learner through updates (FR-20).
- [ ] `tests/test_redirector.py` -- Unit tests validating source drift calculation, notes deprecation idempotency, and bitwise body preservation.

**Acceptance Criteria:**
- Given a `notes.md` file, when `redirector.py deprecate` runs, a deprecation alert block is prepended while the original content remains unchanged.
- Given modified sources, `redirector.py diff-sources` correctly lists affected unfinished sections.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes

## Plan Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run skills/tc-redirect-course/scripts/redirector.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_redirector.py` -- expected: All unit tests pass with exit code 0.
