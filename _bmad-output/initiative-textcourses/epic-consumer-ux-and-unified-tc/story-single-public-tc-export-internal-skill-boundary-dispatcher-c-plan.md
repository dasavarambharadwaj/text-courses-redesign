---
title: 'Single Public /tc Export, Internal Skill Boundary & Dispatcher Continuation'
type: 'feature'
ticket: 8
created: '2026-11-06'
status: done
baseline_revision: '00f4e94b27ef3ef3c1ba98564a2382a9e4f19162'
route: 'full'
route_source: 'auto'
risk: 'high'
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

**Problem:** TextCourses exposes 12 separate skill directories under `skills/` (`tc` plus eleven `tc-*` packages), exposing internal engines as public commands and cluttering the agent harness. Furthermore, `skills-lock.json` contains no entry for `tc`, and the unified dispatcher `tc.py dispatch` contains a fatal continuation dead-end: when a learner responds with `1` (`proceed_open`) at the Material Acquisition Gate, `dispatch` returns `state: creating_course` without invoking course creation or advancing to the Blueprint Approval Gate.

**Approach:**
1. Enforce strict single public export: move all internal capability packages (`tc-create`, `tc-index`, `tc-init`, `tc-migrate`, `tc-practicals`, `tc-redirect-course`, `tc-research`, `tc-roadmap`, `tc-teach`, `tc-test-me`, `tc-verify-course`) under `_tc/skills/`. Keep solely `skills/tc/` in the public `skills/` directory.
2. Update `skills-lock.json` to export solely `tc` among TextCourses packages.
3. Update `skills/tc/SKILL.md` to remove obsolete subcommand listings (`/tc test`, etc.) and `uv run` references, routing all lifecycle interactions strictly through `_tc/scripts/tc.py dispatch`.
4. Fix `tc.py dispatch`: when `proceed_open` or `files_detected` occurs, automatically synthesize the curriculum via `create_course`, write the course blueprint (`_tc/courses/<slug>/blueprint.md`), register the Curriculum Approval Gate, and return `state: blueprint` with the active artifact path.
5. Update `scripts/sync_runtime.py` and existing test paths to respect the encapsulated `_tc/skills/` architecture while preserving 100% test pass rate.

## Boundaries & Constraints

**Always:**
- Keep strictly `skills/tc/` under `skills/`; all internal capabilities must reside under `_tc/skills/`.
- Ensure `skills-lock.json` exports `tc` with valid path and hash, and contains 0 `tc-*` keys.
- Ensure `tc.py dispatch` is the sole public command entrypoint; when `action` is `proceed_open` or `files_detected`, advance directly to `state: blueprint` with active artifact path.
- Keep all code in pure Python standard library with 0 third-party runtime dependencies.
- Update `scripts/sync_runtime.py` to synchronize to canonical locations without failing.

**Never:**
- Never expose `tc-create`, `tc-teach`, `tc-test-me`, or other internal packages in the public `skills/` directory.
- Never return a dead-end `state: creating_course` from `proceed_open` without active gate and blueprint state.
- Never use `uv run` in generated or edited skills/scripts.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Public Surface Inspection | Inspect `skills/` directory | Only `skills/tc/` exists; zero `tc-*` directories | Test failure if extraneous skills exist |
| Skills Lock Audit | Inspect `skills-lock.json` | Contains `"tc"` entry; contains zero `"tc-*"` entries | Test failure if `tc-*` is exported |
| Dispatch Intake | `dispatch()` in fresh workspace | Returns `state: intake_needed`, prompt | Graceful greeting |
| Dispatch Acquisition Gate | `dispatch("Topic")` with no docs | Returns `state: acquisition_gate`, recommended books | Default canonical book fallback |
| Dispatch Continuation | `dispatch("1")` after acquisition gate | Synthesizes course, writes blueprint, returns `state: blueprint`, active artifact, approval gate prompt | Clean error if synthesis fails |
| Dispatch Lesson Start | `dispatch("1")` at approval gate | Begins lesson 1, returns `state: teaching`, context, 4-Option Action Fork | Clean error if course missing |

</intent-contract>

## Code Map

- `skills/` -- Pruned to contain exclusively `tc/`.
- `_tc/skills/` -- Encapsulated directory housing all internal capability packages (`tc-init`, `tc-research`, `tc-create`, `tc-teach`, `tc-test-me`, `tc-practicals`, `tc-verify-course`, `tc-redirect-course`, `tc-migrate`, `tc-index`, `tc-roadmap`).
- `skills/tc/SKILL.md` -- Single public skill definition routing all interactions to `_tc/scripts/tc.py dispatch`.
- `skills-lock.json` -- Agent skills lockfile updated to export solely `tc`.
- `_tc/scripts/tc.py` -- Unified dispatcher: fix continuation logic so `proceed_open` and `files_detected` invoke `create_course`, generate `blueprint.md`, and return `state: blueprint`.
- `_tc/scripts/course_builder.py` -- Course builder: ensure `_tc/courses/<slug>/blueprint.md` is generated during course scaffolding.
- `scripts/sync_runtime.py` -- Update synchronization targets to `_tc/skills/`.
- `tests/test_public_surface.py` -- New test asserting only `skills/tc/` exists, `skills-lock.json` exports only `tc`, and `_tc/skills/` contains internal packages.
- `tests/test_dispatcher_continuation.py` -- New test asserting `dispatch("1")` after acquisition gate advances to `state: blueprint` with blueprint artifact and gate options.
- `tests/test_unified_tc.py` -- Update legacy assertions from `creating_course` to `blueprint`.

## Tasks & Acceptance

**Execution:**
- [x] Move internal skills from `skills/tc-*` to `_tc/skills/` and remove `skills/tc-*` -- Enforces single public skill boundary (`FR-46`).
- [x] Update `skills/tc/SKILL.md` -- Prune internal subcommand documentation and remove `uv run` -- Pure public interface.
- [x] Update `skills-lock.json` -- Add `tc` entry and ensure zero `tc-*` entries -- Public lockfile alignment.
- [x] Update `_tc/scripts/tc.py` and `_tc/scripts/course_builder.py` -- Wire `proceed_open` to course builder, generate `blueprint.md`, and advance to `state: blueprint` -- Eliminates dead-end bug (`CAP-1`).
- [x] Update `scripts/sync_runtime.py` and dependent tests -- Ensure sync targets `_tc/skills/` and existing tests find internal skills.
- [x] Write `tests/test_public_surface.py` and `tests/test_dispatcher_continuation.py` -- Full regression verification.

**Acceptance Criteria:**
- Given `skills/`, when listing directory contents, then only `tc` exists and zero `tc-*` packages exist.
- Given `skills-lock.json`, when inspecting keys, then `"tc"` is present and zero `"tc-*"` keys exist.
- Given a pending acquisition gate, when invoking `tc.py dispatch --input "1"`, then curriculum is synthesized, `_tc/courses/<slug>/blueprint.md` is written, and returned state is `"blueprint"`.
- Given `pytest tests/test_public_surface.py tests/test_dispatcher_continuation.py`, all tests pass green with zero regressions across the suite.

## Implementation Notes

- Encapsulated all 11 internal capability packages (`tc-create`, `tc-index`, `tc-init`, `tc-migrate`, `tc-practicals`, `tc-redirect-course`, `tc-research`, `tc-roadmap`, `tc-teach`, `tc-test-me`, `tc-verify-course`) into `_tc/skills/`, leaving strictly `skills/tc/` in the public directory.
- Updated `skills/tc/SKILL.md` to remove power-user subcommands and `uv run` references, routing all lifecycle flows through `_tc/scripts/tc.py dispatch`.
- Updated `skills-lock.json` with a dedicated `"tc"` entry and verified zero `"tc-*"` entries are exported.
- Updated `_tc/scripts/tc.py` continuation logic: resolving an acquisition gate with `1` (`proceed_open`) or detected documents directly synthesizes the curriculum via `create_course`, scaffolds the blueprint artifact, registers the Curriculum Approval Gate, and returns `state: blueprint` alongside `active_artifact`.
- Updated `_tc/scripts/course_builder.py` to generate `_tc/courses/<slug>/blueprint.md` (and legacy encapsulated `courses/<slug>/.tc/blueprint.md`) without leaking files into the clean canvas root.
- Updated `scripts/sync_runtime.py` to target `_tc/skills/` and synced with zero hash discrepancies.
- Created `tests/test_public_surface.py` (4 tests) and `tests/test_dispatcher_continuation.py` (5 tests).
- Full test suite verified green: 345 passed, 0 failures, 0 regressions.

## Plan Change Log

<!-- Populated during step-04 if needed -->

## Review Triage Log

<!-- Populated during step-04 -->

## Verification

**Commands:**
- `python -m pytest tests/test_public_surface.py tests/test_dispatcher_continuation.py` -- expected: All tests pass.
- `python -m pytest tests/test_unified_tc.py` -- expected: All tests pass.
- `python scripts/sync_runtime.py` -- expected: Clean sync with 0 errors.
