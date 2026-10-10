---
title: 'Story 2.3: Implement consent-gated schema migrator (tc-migrate)'
type: 'feature'
ticket: 3
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

**Problem:** Over time, workspace schemas evolve. Modifying filesystem layouts without transparency or explicit user consent risks corrupting learner artifacts or breaking sovereign workspaces.

**Approach:** Implement `skills/tc-migrate/SKILL.md` and `skills/tc-migrate/scripts/migrator.py`. The migrator inspects workspace health, generates a dry-run `migration-plan.md` report, and strictly requires explicit typed user confirmation (`--confirm "APPLY"`) before executing any file modifications on disk.

## Boundaries & Constraints

**Always:**
- Strictly require explicit confirmation token (`--confirm`) before applying file mutations (FR-21, AD-8).
- Provide a non-destructive dry-run mode that outputs a transparent plan report.
- Include PEP 723 script header declaring Python `>=3.11`.
- Output structured JSON to stdout on success (exit 0) and stderr on error (exit 1).
- Keep zero BMad references in user-facing prompts, templates, or scripts.

**Never:**
- Never modify or move files on disk without explicit typed confirmation.
- Never delete historical learner notes or assessment ledgers during migration.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Health Check | `migrator.py check --path <workspace>` | Returns status (`healthy`, `needs_migration`, `corrupt`), exits 0 | If workspace missing, exits 1 |
| Dry-Run Plan | `migrator.py plan --path <workspace>` | Outputs proposed migration steps to stdout and writes `migration-plan.md`, exits 0 | Makes no changes to course files |
| Apply Without Confirm | `migrator.py apply --path <workspace>` | Fails immediately with `"error": "Confirmation required"`, exits 1 | Zero files modified |
| Apply With Confirm | `migrator.py apply --path <workspace> --confirm APPLY` | Applies migrations atomically, updates schema versions, exits 0 | Rolls back on error |

</frozen-after-approval>

## Code Map

- `skills/tc-migrate/SKILL.md` -- Workspace health check and consent-gated migration prompt.
- `skills/tc-migrate/scripts/migrator.py` -- Deterministic script for health audits, dry-run reports, and consent-gated migrations.
- `tests/test_migrator.py` -- Pytest test suite covering health checks, dry-run planning, confirmation gate rejection, and atomic migration execution.

## Tasks & Acceptance

**Execution:**
- [ ] `skills/tc-migrate/scripts/migrator.py` -- Implement migrator CLI with `check`, `plan`, and `apply` subcommands (FR-21, AD-8).
- [ ] `skills/tc-migrate/SKILL.md` -- Implement migration skill prompt guiding user through transparent health reviews and consent gating.
- [ ] `tests/test_migrator.py` -- Unit tests validating health checks, dry-run safety, and confirmation enforcement.

**Acceptance Criteria:**
- Given an outdated workspace, `migrator.py plan` generates a dry run without altering files.
- Given `migrator.py apply` without `--confirm`, it rejects execution with code 1.
- Given `migrator.py apply --confirm APPLY`, it executes migration safely.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes

## Plan Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run skills/tc-migrate/scripts/migrator.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_migrator.py` -- expected: All unit tests pass with exit code 0.
