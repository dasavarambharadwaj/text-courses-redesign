---
title: "Implement curriculum pre-flight auditor and vocabulary validator (tc-verify-course)"
type: "feature"
ticket: 2
created: "2026-10-10"
status: done
baseline_revision: "5eee253"
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
  - "_bmad-output/initiative-textcourses/epic-curriculum-creation/epic-curriculum-creation.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Poorly structured courses suffer from prerequisite leaps, circular topic dependencies, and unverified APIs. Pre-flight auditing must reject flawed curriculum proposals before any files are written to disk.
**Approach:** Implement `skills/tc-verify-course/SKILL.md` and `skills/tc-verify-course/scripts/auditor.py` (and canonical `_tc/scripts/auditor.py`). The auditor performs topological DAG cycle validation via `dag.py`, audits vocabulary introduction contracts, and cross-checks proposed topics against research digests, classifying findings into CRITICAL, WARNING, and INFO.

## Boundaries & Constraints

**Always:**
- Include PEP 723 inline script header (`requires-python = ">=3.11"`, `tomli-w>=1.0.0`).
- Use `dag.py` to validate topological acyclicity of chapter/section prerequisites (FR-7, AD-4).
- Enforce vocabulary contracts: required prerequisites must be introduced by topological ancestor sections.
- Categorize findings into `CRITICAL`, `WARNING`, and `INFO`.
- Exit with code 0 if 0 CRITICAL findings; exit with code 1 if 1 or more CRITICAL findings exist.
- Output structured JSON to stdout on exit 0, stderr on exit 1.
- Strict zero BMad references.

**Never:**
- Never pass a curriculum proposal that contains prerequisite cycles.
- Never write files to `courses/` directly from `auditor.py`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid Curriculum | `auditor.py audit --manifest course.toml` | All DAG checks and vocabulary contracts pass; exits 0 | Clean report with 0 critical findings |
| Cyclic Prerequisites | `course.toml` with sec-1 -> sec-2 -> sec-1 | Identifies cycle via `dag.py`; logs CRITICAL finding; exits 1 | Lists exact cycle path in findings |
| Premature Vocabulary | Section requires term not yet introduced | Identifies missing prerequisite vocabulary; logs CRITICAL; exits 1 | Lists missing term and section ID |
| Ungrounded Topic | Topic has no matching entry in research digest | Logs WARNING; if 0 critical, exits 0 | Warns without failing build |
| In-Memory Manifest JSON | Pass JSON string or path to audit | Audits data structure directly, exits 0/1 | If invalid syntax, exits 1 |

</frozen-after-approval>

## Code Map

- `skills/tc-verify-course/SKILL.md` -- Auditor skill prompt for curriculum validation and Triad Consensus Loop.
- `skills/tc-verify-course/scripts/auditor.py` & `_tc/scripts/auditor.py` -- Deterministic pre-flight DAG and vocabulary contract validation substrate.
- `tests/test_auditor.py` -- Pytest test suite covering valid courses, prerequisite cycles, vocabulary contract violations, research cross-checks, and zero BMad references.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/auditor.py` & `skills/tc-verify-course/scripts/auditor.py` -- Implement auditor CLI with DAG check, vocabulary contract validation, and research cross-checking (FR-7, AD-4).
- [x] `skills/tc-verify-course/SKILL.md` -- Implement pre-flight curriculum auditor skill prompt (FR-7).
- [x] `tests/test_auditor.py` -- Unit tests validating acyclicity, vocabulary introduction enforcement, research cross-checking, and zero-BMad invariant.

**Acceptance Criteria:**
- Given a course manifest with cycles or missing vocabulary prerequisites, `auditor.py audit` reports CRITICAL findings and exits 1.
- Given a valid course manifest, `auditor.py audit` reports 0 CRITICAL findings and exits 0.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes

Implemented `auditor.py` with PEP 723 metadata, DAG cycle checks via `graphlib.TopologicalSorter`, vocabulary introduction prerequisites verification across topological orders, and research digest cross-checking. Implemented `skills/tc-verify-course/SKILL.md`.

## Plan Change Log

## Review Triage Log

- Verified 9/9 unit tests in `tests/test_auditor.py` pass cleanly.
- Verified 127/127 full test suite pass cleanly.
- Verified zero BMad references across scripts, skills, and tests.
- Verified critical rejection of cycles and missing prerequisite vocabulary.

## Verification

**Commands:**
- `uv run _tc/scripts/auditor.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_auditor.py` -- expected: All unit tests pass with exit code 0.
