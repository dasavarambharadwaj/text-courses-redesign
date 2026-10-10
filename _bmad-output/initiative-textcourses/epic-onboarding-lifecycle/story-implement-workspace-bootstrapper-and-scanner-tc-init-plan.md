---
title: 'Story 2.1: Implement workspace bootstrapper and scanner (tc-init)'
type: 'feature'
ticket: 1
created: '2026-10-10'
status: done
baseline_revision: 'ce28f1f'
route: 'full'
route_source: 'auto'
risk: 'medium'
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

**Problem:** Learners entering TextCourses for the first time need an instantaneous setup (<60s) that bootstraps the local filesystem substrate, records personalized learner preferences, and scans active progress to guide them to the exact next action.

**Approach:** Implement the `tc-init` skill package in `skills/tc-init/SKILL.md` along with its deterministic substrate `skills/tc-init/scripts/bootstrapper.py` (and `_tc/scripts/bootstrapper.py`). When invoked in an empty directory, it sets up `.tc/`, `plan/`, `courses/`, `portfolio/`, copies runtime scripts, and records `plan/preferences.md`. When invoked in an existing workspace, it scans manifests and recommends the next command.

## Boundaries & Constraints

**Always:**
- Use PEP 723 inline script metadata in `bootstrapper.py` declaring Python `>=3.11`.
- Ensure `bootstrapper.py bootstrap` creates `.tc/config.json`, `plan/`, `courses/`, and `portfolio/`, copying deployed engine scripts from `_tc/scripts/`.
- Ensure `bootstrapper.py scan` outputs structured JSON indicating course/roadmap status and the exact recommended command (`/tc-create`, `/tc-teach`, `/tc-test-me`, `/tc-practicals`).
- Strictly adhere to `FR-1`, `FR-2`, `FR-3`, and `AD-6`.
- Keep zero BMad references in user-facing prompts, templates, or scripts.

**Never:**
- Never overwrite existing manifests, preferences, or notes when running bootstrap on an existing directory.
- Never introduce cloud accounts, remote APIs, or heavy external dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Bootstrap Empty Workspace | `bootstrapper.py bootstrap --path <dir>` | Creates `.tc/`, `plan/`, `courses/`, `portfolio/`, copies engine scripts, exits 0 | Creates parent directories if missing |
| Scan Empty Workspace | `bootstrapper.py scan --path <dir>` | Returns `{"status": "empty", "recommendation": "/tc-create"}`, exits 0 | If dir does not exist, exits 1 |
| Scan In-Progress Course | `bootstrapper.py scan --path <dir>` | Inspects `course.toml`, detects active section, returns recommendation `/tc-teach`, exits 0 | N/A |
| Scan Review Chapter | `bootstrapper.py scan --path <dir>` | Detects all chapter sections in `review`, returns recommendation `/tc-test-me`, exits 0 | N/A |
| Scan Completed Course | `bootstrapper.py scan --path <dir>` | Detects course completed, returns recommendation `/tc-practicals`, exits 0 | N/A |

</frozen-after-approval>

## Code Map

- `skills/tc-init/SKILL.md` -- Canonical onboarding skill prompt: structured numbered intake, style preview, and state scanner.
- `skills/tc-init/scripts/bootstrapper.py` -- Deterministic workspace initialization and scanner CLI.
- `_tc/scripts/bootstrapper.py` -- Canonical engine bootstrapper deployed to workspaces.
- `tests/test_bootstrapper.py` -- Unit tests validating workspace bootstrapping, script copying, and state scanner recommendations.

## Tasks & Acceptance

**Execution:**
- [x] `skills/tc-init/scripts/bootstrapper.py` & `_tc/scripts/bootstrapper.py` -- Implement bootstrapper CLI with `bootstrap` and `scan` subcommands (FR-3, AD-6).
- [x] `skills/tc-init/SKILL.md` -- Implement canonical onboarding skill prompt covering structured intake, style picker, preferences compilation, and next-action scanner (FR-1, FR-2, FR-3).
- [x] `tests/test_bootstrapper.py` -- Pytest test suite covering directory layout, engine copying, and progress scanning recommendations.

**Acceptance Criteria:**
- Given an empty directory, `bootstrapper.py bootstrap` creates valid folder layout and deploys runtime scripts.
- Given a course with in_progress section, `bootstrapper.py scan` outputs recommendation `/tc-teach`.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes

## Plan Change Log

## Review Triage Log

- Verified 15/15 unit tests in `tests/test_bootstrapper.py` passed cleanly.
- Verified 95/95 overall test suite passed cleanly.
- Verified strict zero-BMad references in `skills/tc-init/` and `_tc/scripts/bootstrapper.py`.
- Verified PEP 723 inline metadata and non-destructive initialization.

## Verification

**Commands:**
- `uv run _tc/scripts/bootstrapper.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_bootstrapper.py` -- expected: All unit tests pass with exit code 0.
- `uv run pytest` -- expected: 100% of test suite passes cleanly.
