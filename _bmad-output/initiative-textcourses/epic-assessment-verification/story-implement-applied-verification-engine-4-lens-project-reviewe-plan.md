---
title: "Implement applied verification engine, 4-lens project reviewer, and capstone evaluator (tc-practicals)"
type: "feature"
ticket: 2
created: "2026-10-10"
status: done
baseline_revision: "049e864"
route: "full"
route_source: "auto"
risk: "medium"
review: "quick"
review_source: "pinned"
lenses_ran: ["quick-lens"]
review_loop_iteration: 1
context:
  - "_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md"
  - "_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md"
  - "_bmad-output/initiative-textcourses/epic-assessment-verification/epic-assessment-verification.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Theoretical instruction and diagnostic Q&A cannot replace authentic hands-on project creation. Without objective deliverable contracts and multi-perspective verification, practical project evaluations can become subjective, non-deterministic, or disconnected from the learner's demonstrated weak areas.
**Approach:** Implement `_tc/scripts/practical_evaluator.py` and `skills/tc-practicals/SKILL.md`. Formulates customizable practical project briefs in `portfolio/project-XX/project-spec.md` weighted toward recurring misconceptions from `test-ledger.jsonl` (FR-16), restricts requirements to deterministic verifiable contracts (paths, test commands, expected outputs, FR-17), evaluates submitted deliverables across 4 objective review lenses (Functional Completeness, Edge Cases & Robustness, Architecture & Craft, Verification Integrity, FR-18), produces `portfolio/project-XX/review-report.md`, and updates `course.toml` course status to `completed` upon satisfactory review.

## Boundaries & Constraints

**Always:**
- Include PEP 723 inline script header (`requires-python = ">=3.11"`, `tomli-w>=1.0.0`).
- Apply default project intake parameters: Medium Complexity, Weekend Sprint / 4-hour budget, Balanced Depth/Breadth (FR-16).
- Weight project challenges toward diagnosed misconceptions found in `test-ledger.jsonl` (FR-16).
- Require verifiable deliverable contracts restricted to deterministic artifacts: explicit file paths, test commands, expected outputs (FR-17).
- Execute review across 4 distinct objective lenses: (1) Functional Completeness, (2) Edge Cases & Robustness, (3) Architecture & Craft, (4) Verification Integrity (FR-18).
- Atomically update `course.toml` to `completed` upon overall passing review.
- Output structured JSON to stdout on exit 0, stderr on exit 1.
- Strict zero BMad references in user-facing prompts, templates, and scripts.

**Never:**
- Never require non-deterministic or un-evaluable deliverables (e.g. video links, vague essays).
- Never skip the 4-lens evaluation structure during project review.
- Never write to disk without atomic replace on TOML or clean file writing in `portfolio/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Initialize Brief | `practical_evaluator.py init-brief --course <slug>` | Reads `test-ledger.jsonl`, weights spec toward misconceptions, writes `portfolio/project-01/project-spec.md`, exits 0 | If course missing, exits 1 |
| Review Pass | `practical_evaluator.py review --course <slug> --project-id 01 --verdict PASS ...` | Writes `review-report.md`, marks spec approved, marks `course.toml` `completed`, exits 0 | If spec missing, exits 1 |
| Review Needs Work | `practical_evaluator.py review --course <slug> --project-id 01 --verdict NEEDS_WORK ...` | Writes `review-report.md` with remediation tasks, leaves course in-progress, exits 0 | If spec missing, exits 1 |

</frozen-after-approval>

## Code Map

- `_tc/scripts/practical_evaluator.py` & `skills/tc-practicals/scripts/practical_evaluator.py` -- Practical project evaluator CLI providing `init-brief` and `review` subcommands.
- `skills/tc-practicals/SKILL.md` -- Applied verification skill prompt, customizable brief intake, 4-lens project reviewer, and milestone completion flow.
- `tests/test_practical_evaluator.py` -- Pytest test suite validating misconception-weighted brief generation, verifiable deliverable contracts, 4-lens review reports, course status transition, and zero-BMad invariant.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/practical_evaluator.py` & `skills/tc-practicals/scripts/practical_evaluator.py` -- Implement practical evaluator CLI with `init-brief` and `review` subcommands (FR-16, FR-17, FR-18).
- [x] `skills/tc-practicals/SKILL.md` -- Implement hands-on practical project skill prompt with 4-lens review protocol (FR-16, FR-17, FR-18).
- [x] `tests/test_practical_evaluator.py` -- Unit tests validating misconception weighting, verifiable deliverable contracts, 4-lens review pass, course completion update, and zero BMad invariants.

**Acceptance Criteria:**
- `practical_evaluator.py init-brief` incorporates misconceptions from `test-ledger.jsonl` into `project-spec.md`.
- `project-spec.md` specifies explicit deliverable paths and automated verification commands.
- `practical_evaluator.py review` generates `review-report.md` across 4 lenses and updates `course.toml` status to `completed` on PASS.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes
- `practical_evaluator.py` implements customizable brief intake with Medium defaults (medium complexity, weekend sprint budget, balanced depth/breadth) or custom user proposals.
- It scans `test-ledger.jsonl` for historical diagnosed misconceptions and explicitly weights them into the generated `portfolio/project-XX/project-spec.md`.
- The 4-lens review pass evaluates Functional Completeness, Edge Cases & Robustness, Architecture & Craft, and Verification Integrity, outputting `portfolio/project-XX/review-report.md`.
- On PASS, `project-spec.md` status updates to `approved`, and `course.toml` course and chapter statuses transition to `completed`.
- Verified zero BMad occurrences across scripts and skills.
- 5 unit tests pass, and full test suite has 167/167 tests passing.

## Plan Change Log
- None.

## Review Triage Log
- quick-lens: All acceptance criteria met, all 5 unit tests pass cleanly, zero BMad references verified.

## Verification

**Commands:**
- `uv run _tc/scripts/practical_evaluator.py --help`
- `uv run pytest tests/test_practical_evaluator.py`

