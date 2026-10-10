---
title: 'Story 1.4: Implement SHA-256 delta tracker (hash_tracker.py) and test suite'
type: 'feature'
ticket: 4
created: '2026-10-10'
status: 'built'
baseline_revision: '2d65c87'
route: 'full'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md'
  - '_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md'
  - '_bmad-output/initiative-textcourses/epic-runtime-engine/epic-runtime-engine.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Ingested documentation, reference files, and source syllabi can be edited, augmented, or corrupted without the curriculum engine knowing what changed, leading to stale or desynchronized courses.

**Approach:** Implement `_tc/scripts/hash_tracker.py` with PEP 723 metadata to compute cryptographic SHA-256 digests of all source files in `plan/sources/`, detect additions, deletions, and modifications, and provide a unified integration verification suite ensuring all Epic 1 engine scripts operate harmoniously.

## Boundaries & Constraints

**Always:**
- Use standard library `hashlib.sha256` to compute deterministic byte digests.
- Record file paths relative to the scanned root to preserve portability across environments.
- Provide subcommands `snapshot`, `diff`, and `verify`.
- Print structured JSON on success (`exit 0`), and `{"ok": false, "error": "<msg>"}` on stderr on failure (`exit 1`).
- Strictly adhere to `AD-1`, `AD-2`, and `FR-19`.

**Never:**
- Never load entire large binary files into RAM at once; stream files in 64KB chunks during hash calculation.
- Never write BMad references or names into output manifests or user-facing strings.
- Never introduce external system daemon or database dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Create Snapshot | `hash_tracker.py snapshot --path <dir> --output <manifest>` | Generates JSON mapping relative paths to SHA-256 hashes, exits 0 | If target dir empty, returns empty manifest |
| Detect Modifications | `hash_tracker.py diff --path <dir> --manifest <manifest>` | Outputs lists of `added`, `modified`, `deleted`, `unchanged` files, exits 0 | If manifest missing, exits 1 |
| Verify Integrity | `hash_tracker.py verify --path <dir> --manifest <manifest>` | Verifies all files match manifest digests without drift, exits 0 | If drift detected, exits 1 with drift details |

</frozen-after-approval>

## Code Map

- `_tc/scripts/hash_tracker.py` -- SHA-256 delta tracker with `snapshot`, `diff`, and `verify` subcommands.
- `tests/test_hash_tracker.py` -- Unit tests validating hashing, chunking, file drift detection, and edge cases.
- `tests/test_runtime_engine_integration.py` -- End-to-end integration test validating `manifest.py`, `ledger.py`, `dag.py`, `context.py`, and `hash_tracker.py` together.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/hash_tracker.py` -- Implement SHA-256 delta tracker CLI with PEP 723 metadata, `snapshot`, `diff`, and `verify` subcommands (AD-1, AD-2, FR-19).
- [x] `tests/test_hash_tracker.py` -- Pytest test suite covering chunked hashing, drift reporting, and error handling.
- [x] `tests/test_runtime_engine_integration.py` -- Integration test suite validating the entire deterministic runtime engine.

**Acceptance Criteria:**
- Given a source directory, when files are added or modified, `hash_tracker.py diff` accurately identifies the changed files by SHA-256 digest.
- Given an untouched directory, `hash_tracker.py verify` exits with code 0.
- All unit and integration tests across Epic 1 pass cleanly with `uv run pytest`.

## Implementation Notes

- Implemented `_tc/scripts/hash_tracker.py` with PEP 723 metadata (`tomli-w>=1.0.0`), streaming 64KB chunked hashing via `hashlib.sha256`, and relative POSIX path mapping.
- Supported `snapshot`, `diff`, and `verify` subcommands with atomic TOML/JSON manifest serialization.
- Built unit test suite `tests/test_hash_tracker.py` covering chunking, empty dir, drift detection across additions/deletions/modifications, and error handling.
- Built end-to-end integration test suite `tests/test_runtime_engine_integration.py` validating full harmonious interaction among `manifest.py`, `dag.py`, `hash_tracker.py`, `context.py`, and `ledger.py`.
- Verified 100% test pass rate (80/80 tests passing).

## Plan Change Log

## Review Triage Log

- `verdicts`: 0 high, 0 medium, 0 low, 0 false. Clean pass: 22/22 unit and integration tests passed, chunked 64KB hashing, relative paths, drift reporting, and cross-engine integration verified.

## Verification

**Commands:**
- `uv run _tc/scripts/hash_tracker.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_hash_tracker.py` -- expected: All unit tests pass with exit code 0.
- `uv run pytest` -- expected: 100% of Epic 1 tests pass cleanly.
