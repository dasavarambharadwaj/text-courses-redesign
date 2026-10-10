---
title: "Implement diagnostic assessment engine and conceptual testing skill (tc-test-me)"
type: "feature"
ticket: 1
created: "2026-10-10"
status: done
baseline_revision: "d1d864a"
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

**Problem:** Learners often develop superficial mental models or deceptive fluency when copying code or reading passive text. Furthermore, assessments risk leaking upcoming concepts or burdening learners with tedious code-pasting in chat.
**Approach:** Implement `_tc/scripts/diagnostic_tester.py` and `skills/tc-test-me/SKILL.md`. Conducts 100% question-based conceptual diagnostic testing (zero code pasting in chat, FR-13), strictly enforces the Cumulative Boundary Rule (testing only review/completed sections and omitting `lesson-plan.md` to prevent future concept leaks, FR-15, AD-5), records assessment outcomes atomically to `test-ledger.jsonl` via `ledger.py` (FR-14), and transitions section status in `course.toml` from `review` to `completed` upon passing.

## Boundaries & Constraints

**Always:**
- Include PEP 723 inline script header (`requires-python = ">=3.11"`, `tomli-w>=1.0.0`).
- Enforce 100% question-based testing: scenario hinge questions, trade-offs, and failure mode probing. NEVER prompt the learner to paste code into chat (FR-13).
- Strictly enforce Cumulative Boundary Rule: only test sections with `status == "review"` or `status == "completed"`; strictly forbid introducing concepts from upcoming sections (FR-15).
- Strictly omit `lesson-plan.md` from the context during testing (AD-5 Stage Loading Matrix).
- Atomically record assessments to `test-ledger.jsonl` with valid schema using POSIX file locking (`fcntl.flock`) (FR-14, AD-1).
- Update section status in `course.toml` to `completed` when assessment passes.
- Output structured JSON to stdout on exit 0, stderr on exit 1.
- Strict zero BMad references in user-facing prompts, templates, and scripts.

**Never:**
- Never ask the learner to write or paste code in chat during tests.
- Never test concepts from `not-started` or `in-progress` sections.
- Never write to disk without atomic temp-file replace for `course.toml` or locked append for `test-ledger.jsonl`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Prepare Assessment | `diagnostic_tester.py prepare --course <slug>` | Returns eligible review/completed sections, notes summaries, and misconception digest; exits 0 | If course not found or no eligible sections, exits 1 with structured error |
| Record Pass | `diagnostic_tester.py record --course <slug> --chapter <ch> --section <sec> --outcome pass ...` | Appends record to `test-ledger.jsonl`, updates `course.toml` section status to `completed`, exits 0 | Exits 1 on invalid section or missing fields |
| Record Fail | `diagnostic_tester.py record --course <slug> --chapter <ch> --section <sec> --outcome fail ...` | Appends misconception record to `test-ledger.jsonl`, leaves section in `review`, exits 0 | Exits 1 on invalid section or missing fields |

</frozen-after-approval>

## Code Map

- `_tc/scripts/diagnostic_tester.py` & `skills/tc-test-me/scripts/diagnostic_tester.py` -- Diagnostic assessment CLI providing `prepare` and `record` subcommands.
- `skills/tc-test-me/SKILL.md` -- Question-based diagnostic testing prompt, Socratic hinge scenarios, Cumulative Boundary rule, and zero-code-pasting contract.
- `tests/test_diagnostic_tester.py` -- Unit tests verifying cumulative boundaries, ledger recording, course.toml status updates, and zero BMad references.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/diagnostic_tester.py` & `skills/tc-test-me/scripts/diagnostic_tester.py` -- Implement diagnostic tester CLI with `prepare` and `record` subcommands.
- [x] `skills/tc-test-me/SKILL.md` -- Implement diagnostic testing skill with zero code copy-pasting and cumulative boundary rules.
- [x] `tests/test_diagnostic_tester.py` -- Unit tests validating cumulative boundaries, atomic ledger recording, course.toml status updates, and zero BMad invariants.

**Acceptance Criteria:**
- `diagnostic_tester.py prepare` identifies eligible sections and excludes uncompleted/future sections.
- `diagnostic_tester.py record` appends records to `test-ledger.jsonl` and transitions `review` sections to `completed` on pass.
- `skills/tc-test-me/SKILL.md` strictly enforces zero code pasting and cumulative boundaries.
- All unit tests pass cleanly with `uv run pytest`.

## Implementation Notes
- `diagnostic_tester.py` strictly excludes sections in `not-started` and `in-progress` state, ensuring zero concept leakage from upcoming sections.
- It parses `notes.md` summaries and loads recent misconceptions from `test-ledger.jsonl` with `fcntl.flock`.
- Assessment records conform to the canonical ledger schema and are written with `fcntl.flock(f.fileno(), fcntl.LOCK_EX)`. Passing an assessment updates the section's status to `completed` atomically in `course.toml`.
- `skills/tc-test-me/SKILL.md` sets a strict invariant against copy-pasting code in chat, focusing on conceptual hinge scenarios.
- All 6 unit tests pass, and full test suite has 162/162 tests passing.

## Plan Change Log
- None.

## Review Triage Log
- quick-lens: All acceptance criteria met, all tests passing cleanly, zero BMad references verified.

## Verification

**Commands:**
- `uv run _tc/scripts/diagnostic_tester.py --help`
- `uv run pytest tests/test_diagnostic_tester.py`

