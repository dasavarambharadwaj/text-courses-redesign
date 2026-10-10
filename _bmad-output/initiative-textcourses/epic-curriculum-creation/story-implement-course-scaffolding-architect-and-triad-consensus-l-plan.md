---
title: "Implement course scaffolding architect and Triad Consensus Loop (tc-create)"
type: "feature"
ticket: 3
created: "2026-10-10"
status: done
baseline_revision: "6d35da5"
route: "full"
route_source: "auto"
risk: "high"
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

**Problem:** Hand-crafted or unverified AI curricula fail to balance pedagogical structure, jump prerequisites, or skip essential ground truth. Courses must be systematically generated across the 5 Universal Archetypes, grounded in verified documentation, and reconciled through the Triad Consensus Loop before being written to disk.
**Approach:** Implement `skills/tc-create/SKILL.md` and `skills/tc-create/scripts/course_builder.py` (and canonical `_tc/scripts/course_builder.py`). The builder ingests syllabus text or reference links, coordinates the Triad Consensus Loop (Scout -> Architect -> Auditor), logs reconciliation traces to `.tc/cache/consensus-trace.jsonl`, and scaffolds approved courses into `courses/<slug>/` with `course.toml`, `overview.md`, and section `lesson-plan.md` files.

## Boundaries & Constraints

**Always:**
- Include PEP 723 inline script header (`requires-python = ">=3.11"`, `tomli-w>=1.0.0`).
- Support the 5 Universal Archetypes: `applied_creation`, `forensic_dilemma`, `axiomatic_primitives`, `spiral_immersion`, `reverse_engineering` (FR-4).
- Ingest syllabus text, outlines, or reference course links (FR-5).
- Execute Triad Consensus Loop: Scout (`scout.py`) -> Architect (`course_builder.py`) -> Auditor (`auditor.py`) (FR-8, AD-4).
- Log reconciliation events to `.tc/cache/consensus-trace.jsonl` using POSIX atomic append.
- Commit files to `courses/<slug>/` ONLY when consensus is reached with 0 critical findings.
- Output structured JSON to stdout on exit 0, stderr on exit 1.
- Strict zero BMad references in user-facing prompts, templates, and scripts.

**Never:**
- Never write files to `courses/` if auditor detects CRITICAL findings.
- Never generate empty `notes.md` placeholder files during scaffolding (`notes.md` is created only upon section completion by `tc-teach`).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Scaffold Course | `course_builder.py create --slug distributed-sys --title "..." --archetype applied_creation` | Coordinates triad loop; logs trace; scaffolds `courses/distributed-sys/` with `course.toml`, `overview.md`, `lesson-plan.md`; exits 0 | If critical audit findings persist, exits 1 |
| Ingest Syllabus Outline | Pass `--outline-file outline.md` or `--url ...` | Parses topics into chapters/sections with prerequisites; audits and scaffolds, exits 0 | If outline unparseable, exits 1 |
| Consensus Failure Rejection | Auditor rejects candidate curriculum with cycles | Logs rejection to consensus trace; halts without writing to `courses/`; exits 1 | Leaves disk clean |
| Consensus Trace Log | Any course creation run | Appends JSONL events to `.tc/cache/consensus-trace.jsonl` | Atomic flock append |

</frozen-after-approval>

## Code Map

- `skills/tc-create/SKILL.md` -- Primary curriculum generation skill prompt and conversational archetype intake.
- `skills/tc-create/scripts/course_builder.py` & `_tc/scripts/course_builder.py` -- Deterministic curriculum architect, Triad Consensus Loop orchestrator, and directory scaffolder.
- `tests/test_course_builder.py` -- Pytest test suite covering all 5 archetypes, syllabus ingestion, Triad Consensus validation, consensus trace logging, and zero BMad references.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/course_builder.py` & `skills/tc-create/scripts/course_builder.py` -- Implement course builder CLI with `create`, `scaffold`, and `reconcile` subcommands (FR-4, FR-5, FR-8, AD-4).
- [x] `skills/tc-create/SKILL.md` -- Implement canonical curriculum creation skill prompt guiding user through archetype selection and syllabus tuning.
- [x] `tests/test_course_builder.py` -- Unit tests validating 5 archetypes, Triad Consensus Loop, consensus-trace logging, and zero-BMad invariant.

**Acceptance Criteria:**
- Given topic and archetype, `course_builder.py create` runs Triad Consensus Loop, logs trace to `.tc/cache/consensus-trace.jsonl`, and writes valid `courses/<slug>/course.toml`, `overview.md`, and `lesson-plan.md`.
- Given an invalid curriculum with cycles, consensus fails and zero files are written to `courses/<slug>/`.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes

Implemented `course_builder.py` with PEP 723 metadata, 5 Universal Archetypes, Triad Consensus Loop orchestrating `scout.py` and `auditor.py`, atomic `fcntl.flock` append to `.tc/cache/consensus-trace.jsonl`, and safe course directory scaffolding without prematurely creating `notes.md`. Implemented `skills/tc-create/SKILL.md`.

## Plan Change Log

## Review Triage Log

- Verified 11/11 unit tests in `tests/test_course_builder.py` pass cleanly across all 5 archetypes.
- Verified 138/138 full test suite pass cleanly.
- Verified zero BMad references across scripts, skills, and tests.
- Verified consensus trace logging in `.tc/cache/consensus-trace.jsonl`.

## Verification

**Commands:**
- `uv run _tc/scripts/course_builder.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_course_builder.py` -- expected: All unit tests pass with exit code 0.
