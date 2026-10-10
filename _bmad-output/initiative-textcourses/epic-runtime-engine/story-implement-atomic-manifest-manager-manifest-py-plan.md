---
title: 'Story 1.1: Implement atomic manifest manager (manifest.py)'
type: 'feature'
ticket: 1
created: '2026-10-10'
status: done
baseline_revision: 'bb98a418c3b61400d8cb7ea5963be16cdf0e55bd'
route: 'oneshot'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'auto'
lenses_ran: []
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md'
  - '_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** TextCourses requires a deterministic substrate to read, validate, and mutate `course.toml` and `roadmap.toml` manifests without risk of LLM formatting hallucinations or partial-write corruptions during interrupted turns.

**Approach:** Implement `_tc/scripts/manifest.py` with PEP 723 inline script metadata, exposing a CLI interface for reading progress, updating section lifecycle states (`not_started`, `in_progress`, `review`, `completed`), and enforcing schema compliance via POSIX atomic file replacement (`os.fsync` + `os.replace`).

## Boundaries & Constraints

**Always:**
- Use atomic write-and-replace (`.tmp` file write -> `os.fsync` -> `os.replace`) on all TOML write operations.
- Include PEP 723 script header declaring Python `>=3.11` and `tomli-w>=1.0.0`.
- Print structured JSON to `stdout` on success (`exit 0`), and `{"ok": false, "error": "<message>"}` to `stderr` on failure (`exit 1`).
- Strictly adhere to `AD-1`, `AD-2`, `AD-3` of the TextCourses Architecture Spine.

**Never:**
- Never perform in-place direct writes that could truncate manifests if interrupted.
- Never introduce external system daemon or database dependencies.
- Never write BMad references or names into output manifests or user-facing strings.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Init Course Manifest | `manifest.py init-course --path <dir> --slug rust-basics --title "Rust Basics"` | Creates `course.toml` with default metadata, status `not_started`, exits 0 | If directory missing, creates parent directories |
| Read Progress State | `manifest.py get-status --path <dir>` | Outputs JSON with total sections, completed count, active chapter/section, exits 0 | If `course.toml` missing, exits 1 with `"error": "Manifest not found"` |
| Advance Section Status | `manifest.py advance --path <dir> --chapter 1 --section 2 --status review` | Updates section 2 in chapter 1 to `review`, atomically replaces file, exits 0 | If chapter/section out of bounds, exits 1 with `"error": "Section not found"` |
| Invalid TOML Schema | `manifest.py validate --path <corrupted.toml>` | Rejects invalid TOML or missing required keys, exits 1 | Outputs detailed validation error message |

</intent-contract>

## Code Map

- `_tc/scripts/manifest.py` -- Primary deterministic manifest manager CLI with atomic replacement and validation logic.
- `tests/test_manifest.py` -- Unit tests validating manifest creation, state transitions, atomic replacements, and error handling.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/manifest.py` -- Create manifest manager CLI with PEP 723 header, `init-course`, `init-roadmap`, `get-status`, `advance`, and `validate` subcommands -- Core deterministic substrate for state mutations (AD-1, AD-3).
- [x] `tests/test_manifest.py` -- Implement pytest test suite verifying atomic write semantics, schema validations, and CLI outputs -- Ensures verification integrity.

**Acceptance Criteria:**
- Given an empty workspace directory, when `manifest.py init-course` is executed, then `course.toml` is written with valid TOML format and `get-status` returns `not_started`.
- Given an existing `course.toml`, when `manifest.py advance` transitions a section from `in_progress` to `review`, then the file is atomically updated on disk without data loss.
- Given a malformed TOML file, when `manifest.py validate` runs, then it exits with code 1 and prints structured error details to stderr.

## Implementation Notes

- Implemented `_tc/scripts/manifest.py` with PEP 723 inline script metadata declaring Python `>=3.11` and `tomli-w>=1.0.0`.
- Ensured atomic file updates via `atomic_write_toml` using `.tmp` write, `f.flush()`, `os.fsync(f.fileno())`, and `os.replace`.
- Supported all five required subcommands: `init-course`, `init-roadmap`, `get-status`, `advance`, and `validate`.
- Built comprehensive test suite `tests/test_manifest.py` covering all CLI commands, lifecycle state updates, error responses, invalid TOML parsing, and atomic write temp-file cleanup.
- Configured isolated pytest runs in `pyproject.toml` and verified 11 passing tests.

## Plan Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run _tc/scripts/manifest.py --help` -- expected: Displays available subcommands and options with exit code 0.
- `uv run pytest tests/test_manifest.py` -- expected: All unit tests pass with exit code 0.
