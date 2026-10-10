---
title: 'Story 1.2: Implement assessment ledger engine (ledger.py)'
type: 'feature'
ticket: 2
created: '2026-10-10'
status: done
baseline_revision: 'b86a11f'
route: 'full'
route_source: 'auto'
risk: 'medium'
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

**Problem:** TextCourses requires an append-only, concurrency-safe diagnostic assessment ledger (`test-ledger.jsonl`) that records learner diagnostic outcomes and misconceptions without risk of file corruption or context window degradation when agents query historical results.

**Approach:** Implement `_tc/scripts/ledger.py` with PEP 723 metadata, exposing CLI subcommands for atomic JSONL appending with `fcntl.flock` file locking, schema validation, and a `summarize` query returning a compact (<100 tokens) JSON digest of active misconceptions and weak sections.

## Boundaries & Constraints

**Always:**
- Use POSIX advisory file locking (`fcntl.flock(f.fileno(), fcntl.LOCK_EX)`) during all ledger append operations.
- Flush and sync (`os.fsync`) to disk before releasing locks.
- Format all ledger entries as single-line valid JSON objects.
- Guarantee the `summarize` output is ultra-compact (<100 tokens / <400 characters) to prevent prompt bloat in instructional agents (AD-3, AD-5).
- Print structured JSON on success (`exit 0`), and `{"ok": false, "error": "<msg>"}` on stderr on failure (`exit 1`).
- Strictly adhere to `AD-1`, `AD-3`, `FR-14`, and `FR-16`.

**Never:**
- Never overwrite, truncate, or rewrite `test-ledger.jsonl` (strict append-only invariant).
- Never introduce external system daemon, database, or heavy Python dependencies beyond standard library.
- Never write BMad references or names into output files, schemas, or user-facing strings.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Append Record | `ledger.py append --path <dir> --record '<json>'` | Appends record with UTC ISO timestamp under `fcntl.flock`, exits 0 | If directory missing, creates parent dirs; if invalid JSON, exits 1 |
| Missing Required Keys | `ledger.py append --path <dir> --record '{"score": 1}'` | Validates schema, rejects incomplete record, exits 1 | Outputs specific missing field names |
| Summarize Ledger | `ledger.py summarize --path <dir>` | Aggregates pass rate, deduplicated active misconceptions, and weak sections (<100 tokens), exits 0 | If ledger missing or empty, returns zeroed digest with exit 0 |
| Validate Ledger | `ledger.py validate --path <test-ledger.jsonl>` | Verifies all JSON lines conform to schema, exits 0 | Reports invalid lines and schema discrepancies, exits 1 |
| Concurrent Appends | Simultaneous writes to same `test-ledger.jsonl` | Sequential serialized appends without interleaved or corrupted lines | Locks block until acquisition; atomic append |

</frozen-after-approval>

## Code Map

- `_tc/scripts/ledger.py` -- Deterministic assessment ledger engine with `append`, `summarize`, and `validate` subcommands using `fcntl.flock`.
- `tests/test_ledger.py` -- Unit and integration tests verifying schema validation, append locking, compact summaries, and concurrency resilience.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/ledger.py` -- Implement assessment ledger CLI with PEP 723 metadata, `fcntl.flock` atomic appends, schema validation, and compact `<100` token summarizer -- Core deterministic substrate for diagnostic tracking (AD-1, AD-3, FR-14, FR-16).
- [x] `tests/test_ledger.py` -- Implement pytest test suite verifying record appending, schema errors, concurrent write safety, and summary token constraints -- Ensures verification integrity.

**Acceptance Criteria:**
- Given a target course directory, when `ledger.py append` records a diagnostic interaction, then a valid single-line JSON record is appended with file locking and `os.fsync`.
- Given a populated `test-ledger.jsonl` with multiple attempts and misconceptions, when `ledger.py summarize` runs, then it outputs a deduplicated digest with `total_tests`, `pass_rate`, `weak_sections`, and `active_misconceptions` under 100 tokens.
- Given a corrupt or incomplete JSONL file, when `ledger.py validate` runs, then it exits with code 1 and identifies the faulty line numbers.

## Implementation Notes

- Implemented `_tc/scripts/ledger.py` with PEP 723 script metadata, POSIX advisory file locking via `fcntl.flock(LOCK_EX)` during append, `f.flush()` and `os.fsync()` before release, and shared read lock `fcntl.flock(LOCK_SH)` during summarization and validation.
- Schema validation enforces `REQUIRED_RECORD_FIELDS` (`course`, `chapter`, `section`, `question_type`, `prompt`, `learner_response`, `outcome`) and validates ISO timestamp injection when omitted.
- `summarize` command generates ultra-compact digests (<100 tokens / <380 characters) containing `total_tests`, `pass_rate`, `weak_sections`, and deduplicated `active_misconceptions`.
- `validate` verifies each line in `test-ledger.jsonl`, reporting specific line numbers for syntax or schema failures.
- Added comprehensive pytest suite in `tests/test_ledger.py` with 18 tests covering CLI help, parent directory creation, atomic appends, sequential and stdin writes, schema error handling, invalid outcome validation, corrupt line validation, compact summarization token limits, course slug resolution, and multi-process concurrent append safety with process pools.
- Full test suite (29 tests across `test_manifest.py` and `test_ledger.py`) passes cleanly with exit code 0.

## Plan Change Log

## Review Triage Log

- `verdicts`: 0 high, 0 medium, 0 low, 0 false. Clean pass: 18/18 ledger tests passed, all ACs satisfied, schema and compaction invariants (<100 tokens) verified.

## Verification

**Commands:**
- `uv run _tc/scripts/ledger.py --help` -- expected: Displays available subcommands (`append`, `summarize`, `validate`) with exit code 0.
- `uv run pytest tests/test_ledger.py` -- expected: All unit and concurrency tests pass cleanly with exit code 0.
- `uv run pytest` -- expected: Full test suite (both `test_manifest.py` and `test_ledger.py`) passes with exit code 0.
