---
title: 'Root _tc/ Storage Migration, Clean Canvas & Scoped Memlogs Engine'
type: 'feature'
ticket: 7
created: '2026-11-06'
status: done
baseline_revision: '0e0cd564144780d84578483350cc0b073557f49a'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'auto'
lenses_ran: []
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '_tc/INTERACTION_STANDARDS.md'
  - '_bmad-output/initiative-textcourses/change-reconcile-flow-and-unattended-compiler/change-reconcile-flow-and-unattended-compiler.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** TextCourses legacy runtime scatters machine state across duplicate root folders (`.tc/`, `_tc/`, `research/`, `sources/`, `plan/`, `profile/`, `roadmap/`), violates the learner clean-canvas contract by hiding compiled notes in internal `.tc/notes/`, and lacks scoped hierarchical memlogs for granular journey memory.

**Approach:** Consolidate all machine state, research dossiers, raw sources, profile, and roadmap under canonical root `_tc/` with a consent-gated migration engine (`tc-migrate` / `migrator.py`), enforce visible chapter notes strictly in `courses/<slug>/notes/`, update `bootstrapper.py` to produce solely canonical paths, and expand `memlog.py` to support hierarchical scopes (workspace, roadmap, research, course, chapter, section) with milestone roll-up.

## Boundaries & Constraints

**Always:**
- Route all internal machine state to root `_tc/` (`_tc/profile/`, `_tc/roadmap/`, `_tc/research/<slug>/`, `_tc/courses/<slug>/`, `_tc/cache/`, `_tc/status/`).
- Keep the visible study canvas pristine: only `courses/<slug>/notes/chapter-XX.md` exists outside `_tc/` (with `portfolio/` for capstones and `status-board/` for the dashboard).
- Require explicit user consent (`APPLY` token or `--apply`) before `tc-migrate` mutates or moves legacy folders; provide transparent dry-run inspection by default.
- Support scoped memlog append with level-appropriate granularity: log turns/decisions to the most specific active memlog, and roll up milestone summaries to chapter, course, and global memlogs.
- Maintain read-only legacy fallback during migration so existing workspaces do not hard-crash.
- Keep all code in pure Python standard library without external dependencies.
- Synchronize runtime changes across canonical `_tc/scripts/` and runtime packages via `scripts/sync_runtime.py`.

**Never:**
- Never write new files to root `.tc/`, `research/`, `sources/`, `plan/`, `plan/sources/`, root `profile/`, or root `roadmap/`.
- Never compile learner notes into `.tc/notes/` or hide them in machine folders.
- Never delete legacy files during migration without cryptographic hash or byte-parity verification.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Fresh Workspace Bootstrap | `bootstrapper.py bootstrap --target <ws>` | Creates canonical `_tc/scripts`, `_tc/cache`, `_tc/profile`, `_tc/roadmap`, `_tc/research`, `_tc/courses`, `_tc/status`, `courses`, `portfolio`, `status-board`; zero root `.tc` or `plan` | Clean error if target unwritable |
| Legacy Migration Dry Run | `migrator.py plan --workspace <legacy_ws>` | Emits migration plan JSON detailing detected legacy paths (`.tc/`, `sources/`, `plan/`) and proposed `_tc/` destinations without moving files | Fails gracefully if workspace unreadable |
| Legacy Migration Apply | `migrator.py apply --workspace <legacy_ws> --token APPLY` | Moves legacy directories into `_tc/`, updates config schema to `0.3.0`, verifies file parity, and removes migrated empty folders | Aborts without modifying disk if token is omitted or incorrect |
| Scoped Memlog Append | `memlog.py append --scope chapter --course <slug> --chapter 01 --tag concept --content "OS Primitives"` | Appends entry to `_tc/courses/<slug>/chapters/chapter-01/memlog.md` with timestamp and tag | Creates parent directories automatically if missing |
| Milestone Roll-Up | `memlog.py append --scope section --course <slug> --chapter 01 --section 01 --tag milestone --content "Completed Sec 1" --roll-up` | Appends milestone to section memlog AND rolls up a summary line to chapter, course, and global profile memlogs | Atomic append to all levels |

</intent-contract>

## Code Map

- `_tc/scripts/bootstrapper.py` -- Workspace initialization engine: update `dirs_to_create` and path generation to enforce canonical root `_tc/` tree and eliminate duplicate legacy folders.
- `_tc/scripts/migrator.py` -- Schema migrator and health auditor: upgrade schema version to `0.3.0`, add migration rules from `.tc`, `research`, `sources`, `plan`, `profile`, `roadmap` to `_tc/`, enforce consent gating (`APPLY`), and add verification checks.
- `_tc/scripts/memlog.py` -- Pedagogical memory logger: add `--scope` (`global`/`profile`, `roadmap`, `research`, `course`, `chapter`, `section`), path resolution across hierarchical scopes, and milestone roll-up capability.
- `scripts/sync_runtime.py` -- Runtime synchronization utility: syncs `_tc/scripts/*.py` to `skills/tc-init/scripts/runtime/*.py` and individual skill folders.
- `tests/test_storage_contract.py` -- New test suite validating canonical `_tc/` layout, clean canvas invariants, and migration verification.
- `tests/test_memlog_scopes.py` -- New test suite validating scoped memlog creation, path resolution, and milestone roll-up.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/bootstrapper.py` -- Update `dirs_to_create` and config paths to canonical root `_tc/` layout -- Prevents creation of legacy `.tc/`, `plan/`, `sources/` duplicate roots.
- [x] `_tc/scripts/migrator.py` -- Implement schema `0.3.0` migration logic for root `_tc/` consolidation with consent check -- Enables existing workspaces to migrate safely without data loss.
- [x] `_tc/scripts/memlog.py` -- Add hierarchical `--scope` support (`profile`, `roadmap`, `research`, `course`, `chapter`, `section`) and milestone roll-up flag -- Satisfies granular journey memory requirement (Learner Point 2).
- [x] `scripts/sync_runtime.py` -- Run runtime sync across skill runtime packages -- Ensures all skill packages share identical canonical implementations.
- [x] `tests/test_storage_contract.py` -- Write unit and integration tests for canonical storage and migration -- Proves storage contract correctness against regression.
- [x] `tests/test_memlog_scopes.py` -- Write unit tests for scoped memlogs and milestone propagation -- Proves scoped memory mechanics.

**Acceptance Criteria:**
- Given a newly bootstrapped workspace, when inspecting directories, then only `_tc/`, `courses/`, `portfolio/`, and `status-board/` exist at root, with zero occurrences of root `.tc/`, `sources/`, `plan/`, or `research/`.
- Given an existing workspace with legacy `.tc/` and root `research/`, when running `migrator.py apply` with `APPLY`, then files are safely migrated to `_tc/` and verified without loss.
- Given a learning turn in Chapter 1 Section 2, when appending with `--scope section --tag milestone --roll-up`, then the entry is logged in section memlog and milestone summaries appear in chapter, course, and global memlogs.
- Given the full test suite, when running `pytest tests/test_storage_contract.py tests/test_memlog_scopes.py`, then all tests pass with 100% green status.

## Implementation Notes

- Updated `_tc/scripts/bootstrapper.py` to only scaffold canonical `_tc/` tree (`_tc/scripts`, `_tc/cache`, `_tc/profile`, `_tc/roadmap`, `_tc/research`, `_tc/courses`, `_tc/status`) and root `courses/`, `portfolio/`, `status-board/`. Schema version upgraded to `0.3.0` with preferences and memlogs placed strictly under `_tc/profile/`.
- Updated `_tc/scripts/migrator.py` to upgrade schema version to `0.3.0`, detect legacy directories (`.tc`, `research`, `sources`, `plan`, `profile`, `roadmap`), enforce consent gate token (`APPLY`), and safely move files to `_tc/` with cryptographic SHA-256 parity verification.
- Updated `_tc/scripts/memlog.py` to introduce `--scope` resolution across hierarchical levels (`profile`/`workspace`/`global`, `roadmap`, `research`, `course`, `chapter`, `section`) and `--roll-up` flag for propagating milestone summaries up through section -> chapter -> course -> global memlogs.
- Executed `scripts/sync_runtime.py` to synchronize canonical scripts to `skills/tc-init/scripts/runtime/` and individual skill packages with 100% SHA-256 hash parity.
- Implemented `tests/test_storage_contract.py` and `tests/test_memlog_scopes.py` covering all acceptance criteria and edge cases.
- All 336 tests in the test suite pass.

## Plan Change Log

<!-- Populated during step-04 if needed -->

## Review Triage Log

<!-- Populated during step-04 -->

## Verification

**Commands:**
- `python -m pytest tests/test_storage_contract.py tests/test_memlog_scopes.py` -- expected: All tests pass.
- `python scripts/sync_runtime.py` -- expected: Runtime packages synchronized with 0 hash discrepancies.
- `python -m pytest tests/test_clean_workspace.py` -- expected: Clean workspace invariants hold.
