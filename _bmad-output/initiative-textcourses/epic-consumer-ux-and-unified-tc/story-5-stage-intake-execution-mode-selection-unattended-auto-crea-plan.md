---
title: '5-Stage Intake, Execution Mode Selection & Unattended Auto Creation'
type: 'feature'
ticket: 9
created: '2026-11-06'
status: done
baseline_revision: '8e9e5296e626e27a94ff03d93dc06bebeec1ea36'
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

**Problem:** TextCourses intake and preference systems do not support execution mode selection (`interactive` vs `auto`). Learners who prefer unattended automated course generation are forced to manually click through acquisition gates and blueprint approval gates, while learners who want full control have no formalized mode setting. Additionally, creation decisions in unattended runs are not systematically recorded.

**Approach:**
1. Expand preferences schema in `_tc/scripts/bootstrapper.py` to capture `mode: "interactive" | "auto"` (persisted in `_tc/profile/preferences.md`).
2. Add `--mode` CLI option to `bootstrapper.py bootstrap`, `set-preferences`, and `_tc/scripts/tc.py dispatch`.
3. In `_tc/scripts/tc.py dispatch`:
   - Interactive mode: pause at Material Acquisition / Source Proposal Gate, and pause at Blueprint Approval Gate.
   - Auto mode: automatically select best available sources, synthesize curriculum, write blueprint, auto-approve blueprint, log all autonomous decisions in `_tc/profile/memlog.md` and `_tc/courses/<slug>/memlog.md`, and transition directly to `state: "teaching"`.
   - Maintain identical teaching turns and mandatory Section Close Gate in both modes (`FR-47`).
4. Implement `tests/test_mode_selection.py` verifying mode persistence, unattended creation execution in auto mode, creation checkpoint pauses in interactive mode, and identical teaching behavior.

## Boundaries & Constraints

**Always:**
- Persist `mode: interactive` or `mode: auto` in `_tc/profile/preferences.md` frontmatter.
- In `auto` mode, record every autonomous decision (source selection, gap fallback, blueprint approval) in scoped memlogs.
- Ensure teaching behavior is 100% identical in both modes.
- Ensure the Section Close Gate is mandatory in both modes (`FR-47`). Auto mode must NEVER bypass section sign-off.
- Pure Python standard library, zero external runtime dependencies.

**Never:**
- Never bypass the Section Close Gate in auto mode.
- Never write preferences outside canonical `_tc/profile/preferences.md` (except read-only legacy fallbacks).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Mode Setting CLI | `set-preferences --mode auto` | Updates `_tc/profile/preferences.md` with `mode: "auto"` | Validates choice in {"interactive", "auto"} |
| Dispatch with --mode | `dispatch("Topic", --mode auto)` | Persists mode, executes full creation unattended, advances to teaching | Graceful failure if topic invalid |
| Interactive Mode Run | `dispatch("Topic")` with mode=interactive | Pauses at `state: "acquisition_gate"` | Waits for user response |
| Auto Mode Run | `dispatch("Topic")` with mode=auto | Bypasses creation gates, logs decisions, lands at `state: "teaching"` | Logs all decisions to memlog |
| Teaching Parity | `dispatch("1")` in teaching turn | Advances lesson concept identically in both interactive and auto | Uniform error handling |

</intent-contract>

## Code Map

- `_tc/scripts/bootstrapper.py` -- Add `mode` parameter to `compile_preferences_content`, `parse_preferences_file`, `cmd_set_preferences`, and `bootstrap`.
- `_tc/scripts/tc.py` -- Read and persist `mode`; support `--mode` CLI argument; implement unattended creation bypass and decision logging when `mode == "auto"`.
- `scripts/sync_runtime.py` -- Synchronize updated scripts to runtime destinations.
- `tests/test_mode_selection.py` -- Dedicated test suite validating mode persistence, interactive pauses, unattended auto creation, and teaching parity.

## Tasks & Acceptance

**Execution:**
- [x] Update `_tc/scripts/bootstrapper.py` to support `mode` (`interactive`/`auto`) in preferences -- Enables mode storage in `_tc/profile/preferences.md`.
- [x] Update `_tc/scripts/tc.py` to accept `--mode` and implement auto-mode creation pipeline with decision logging -- Fulfills `CAP-7` and `FR-47`.
- [x] Run `scripts/sync_runtime.py` -- Keeps all runtime copies synchronized.
- [x] Create `tests/test_mode_selection.py` -- Proves mode selection and autonomy boundaries against regression.
- [x] Run full test suite -- Verify 100% pass rate.

**Acceptance Criteria:**
- Given `bootstrapper.py set-preferences --mode auto`, when inspecting `_tc/profile/preferences.md`, then `mode: "auto"` is present.
- Given a fresh workspace with `mode: interactive`, when dispatching a topic, then execution pauses at `acquisition_gate`.
- Given a fresh workspace with `mode: auto`, when dispatching a topic, then creation executes without pausing, decisions are logged in memlog, and state reaches `teaching`.
- Given an active lesson, when dispatching choices `1`, `2`, `3`, then behavior is identical regardless of mode.
- Given `pytest tests/test_mode_selection.py`, all tests pass green.

## Implementation Notes

- Added `DEFAULT_MODES = ["interactive", "auto"]` to `_tc/scripts/bootstrapper.py`, updated `compile_preferences_content` and `parse_preferences_file` to support `mode` frontmatter, and added `--mode` argument to `bootstrap` and `set-preferences`.
- Updated `_tc/scripts/memlog.py` to export Python API `append_entry(...)` for programmatic scoped logging with milestone roll-up.
- Updated `_tc/scripts/tc.py` to accept `--mode` / `-m`, parse active mode from preferences, and execute unattended course creation when `mode == "auto"`, logging autonomous decisions to `_tc/profile/memlog.md` and `_tc/courses/<slug>/memlog.md` while advancing straight to `state: "teaching"`.
- Maintained strict teaching parity across both modes: lesson navigation and diagnostic inquiries function identically, and Section Close Gate is preserved.
- Added `tests/test_mode_selection.py` (4 tests) covering mode persistence, interactive pauses, unattended auto creation, and teaching parity.
- Re-synchronized runtime scripts with 100% hash parity.

## Plan Change Log

<!-- Populated during step-04 if needed -->

## Review Triage Log

<!-- Populated during step-04 -->

## Verification

**Commands:**
- `python -m pytest tests/test_mode_selection.py` -- expected: All tests pass.
- `python scripts/sync_runtime.py` -- expected: Clean sync with 0 discrepancies.
- `python -m pytest tests/test_dispatcher_continuation.py tests/test_public_surface.py` -- expected: All tests pass.
