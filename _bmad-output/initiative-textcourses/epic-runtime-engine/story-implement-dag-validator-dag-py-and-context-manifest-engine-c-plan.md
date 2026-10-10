---
title: 'Story 1.3: Implement DAG validator (dag.py) and context manifest engine (context.py)'
type: 'feature'
ticket: 3
created: '2026-10-10'
status: 'built'
baseline_revision: '7db3feb'
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

**Problem:** Curriculum generation and runtime instruction can suffer from circular prerequisite dependencies, conceptual leaps, and token context bloat if agents blindly read entire course repositories or miss dependency cycles.

**Approach:** Implement `_tc/scripts/dag.py` using Python's standard `graphlib.TopologicalSorter` to validate prerequisite dependency graphs and compute topological build orders without token cost. Implement `_tc/scripts/context.py` to enforce the Stage Loading Matrix across all TextCourses skills, outputting strict authorized file manifests to maintain turn budgets under 4,000 tokens.

## Boundaries & Constraints

**Always:**
- Use standard library `graphlib.TopologicalSorter` in `dag.py` to detect cycles (`CycleError`) and validate dependency trees.
- Enforce the Stage Loading Matrix strictly in `context.py` according to Architectural Decision `AD-5` and `FR-22`.
- Include PEP 723 script header declaring Python `>=3.11` and standard library dependencies.
- Output structured JSON to stdout on success (`exit 0`), and `{"ok": false, "error": "<msg>"}` to stderr on failure (`exit 1`).
- Strictly adhere to `AD-1`, `AD-4`, `AD-5`, `FR-7`, `FR-8`, and `FR-22`.

**Never:**
- Never load out-of-scope chapters, future sections, or raw logs into authorized context manifests.
- Never write BMad references or names into output manifests or user-facing strings.
- Never introduce heavy external dependencies beyond standard library or `tomli-w` if TOML generation is needed.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Validate Valid DAG | `dag.py validate --path <course.toml>` | Returns `{"ok": true, "valid": true, "order": [...]}` with topological order, exits 0 | N/A |
| Detect Dependency Cycle | `dag.py validate --path <cyclic_course.toml>` | Catches `graphlib.CycleError`, returns `{"ok": false, "error": "Circular dependency detected", "cycle": [...]}`, exits 1 | Outputs specific cycle nodes |
| Detect Missing Prereq | `dag.py validate --path <missing_prereq.toml>` | Rejects reference to nonexistent chapter/section ID, exits 1 | Identifies missing antecedent ID |
| Skill Context Manifest | `context.py get-manifest --skill tc-teach --path <course_dir>` | Returns exact authorized files (`course.toml`, active `lesson-plan.md`, `notes.md`, `test-ledger.jsonl`), exits 0 | If active section missing, exits 1 with guidance |
| Unauthorized File Check | `context.py check --skill tc-test-me --file future/lesson-plan.md` | Returns `{"authorized": false, "reason": "Future section access forbidden"}`, exits 1 | Rejects leak of upcoming concepts |

</frozen-after-approval>

## Code Map

- `_tc/scripts/dag.py` -- Deterministic graph validation CLI using `graphlib.TopologicalSorter` for cycle detection and topological ordering.
- `_tc/scripts/context.py` -- Context loading engine enforcing Stage Loading Matrix constraints per skill.
- `tests/test_dag.py` -- Unit tests verifying cycle detection, topological ordering, and missing antecedent rejection.
- `tests/test_context.py` -- Unit tests verifying authorized manifest generation and boundary enforcement across skills.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/dag.py` -- Implement DAG validator CLI with PEP 723 header, `validate`, and `order` subcommands using `graphlib.TopologicalSorter` (AD-4, FR-7, FR-8).
- [x] `_tc/scripts/context.py` -- Implement context manifest engine with PEP 723 header, `get-manifest` and `check` subcommands enforcing the Stage Loading Matrix (AD-5, FR-22).
- [x] `tests/test_dag.py` -- Pytest test suite covering valid DAGs, cyclic graphs, missing prerequisite references, and edge cases.
- [x] `tests/test_context.py` -- Pytest test suite covering authorized file manifests, stage boundaries, and out-of-scope read rejections.

**Acceptance Criteria:**
- Given a `course.toml` with prerequisite declarations, when `dag.py validate` runs, it outputs topological order or halts with detailed cycle diagnosis.
- Given a skill invocation (e.g. `tc-teach`), when `context.py get-manifest` runs, it outputs only authorized file paths keeping context budgets under 4,000 tokens.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes

- Implemented `_tc/scripts/dag.py` with PEP 723 metadata using `graphlib.TopologicalSorter` for cycle detection and topological ordering (`validate`, `order` subcommands).
- Implemented `_tc/scripts/context.py` with PEP 723 metadata enforcing the Stage Loading Matrix across all 9 skills (`get-manifest`, `check`, `matrix` subcommands).
- Built test suites in `tests/test_dag.py` (15 tests) and `tests/test_context.py` (14 tests).
- All 58 unit tests across the repository pass cleanly with exit code 0.

## Plan Change Log

## Review Triage Log

- `verdicts`: 0 high, 0 medium, 0 low, 0 false. Clean pass: 29/29 tests passed, cycle error handling and Stage Loading Matrix limits verified with zero external runtime dependencies.

## Verification

**Commands:**
- `uv run _tc/scripts/dag.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run _tc/scripts/context.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_dag.py tests/test_context.py` -- expected: All unit tests pass with exit code 0.
