---
title: "Implement conversational instruction skill and Next-Action Fork orchestrator (tc-teach)"
type: "feature"
ticket: 3
created: "2026-10-10"
status: done
baseline_revision: "fa7e61e"
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
  - "_bmad-output/initiative-textcourses/epic-instruction-delivery/epic-instruction-delivery.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Conversational instruction easily derails into verbose lectures, token bloat, and unstructured Q&A without clear boundaries or guaranteed progress.
**Approach:** Implement `skills/tc-teach/SKILL.md` and `skills/tc-teach/scripts/teach_engine.py` (and canonical `_tc/scripts/teach_engine.py`). Integrates `context.py`, enforces single-concept delivery bounded by active style preferences, concludes every turn with the standardized 4-option Next-Action Fork, and coordinates `lesson_tracker.py` and `notes_compiler.py` to compile textbook notes upon section completion.

## Boundaries & Constraints

**Always:**
- Include PEP 723 inline script header (`requires-python = ">=3.11"`, `tomli-w>=1.0.0`).
- Deliver strictly one bounded concept per instructional turn with bold mechanics, formatted code/tables, and worked-example/fatal-mistake pairs (FR-9).
- Conclude every instructional turn with the standardized 4-option Next-Action Fork (FR-10).
- Check `plan/preferences.md` for active Style Profile and Density.
- Coordinate `lesson_tracker.py` and `notes_compiler.py` to compile `notes.md` automatically upon completing final concept (FR-11, FR-12).
- Output structured JSON to stdout on exit 0, stderr on exit 1.
- Strict zero BMad references in user-facing prompts, templates, and scripts.

**Never:**
- Never blur multiple concepts into a multi-page lecture in a single turn.
- Never omit the Next-Action Fork from an instructional turn.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Active Session Init | `teach_engine.py session --course <slug>` | Identifies active in-progress section and next uncompleted concept; exits 0 | If course missing, exits 1 |
| Advance Concept | `teach_engine.py advance --course <slug>` | Ticks off active concept in `lesson-plan.md`; if section complete, triggers `notes_compiler.py` and returns `section_completed: true`, exits 0 | If already complete, reports completion status |
| Render Fork | `teach_engine.py fork` | Outputs standardized markdown Next-Action Fork block and JSON options, exits 0 | Always succeeds |

</frozen-after-approval>

## Code Map

- `skills/tc-teach/SKILL.md` -- Primary teaching skill prompt, single-concept pedagogical rules, and Next-Action Fork loop.
- `skills/tc-teach/scripts/teach_engine.py` & `_tc/scripts/teach_engine.py` -- Deterministic teaching engine coordinating session discovery, concept advancement, and automatic notes compilation.
- `tests/test_teach_engine.py` -- Pytest test suite covering session discovery, concept advancement, Next-Action Fork formatting, automated notes compilation trigger, and zero BMad references.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/teach_engine.py` & `skills/tc-teach/scripts/teach_engine.py` -- Implement teach engine CLI with `session`, `advance`, and `fork` subcommands (FR-9, FR-10, AD-5).
- [x] `skills/tc-teach/SKILL.md` -- Implement conversational instruction skill prompt (FR-9, FR-10).
- [x] `tests/test_teach_engine.py` -- Unit tests validating session resolution, concept advancement, Next-Action Fork rendering, automatic notes compilation trigger, and zero-BMad invariant.

**Acceptance Criteria:**
- Given an active course, `teach_engine.py session` resolves current active section and unchecked concept.
- `teach_engine.py advance` ticks concept and triggers notes compilation on section completion.
- `teach_engine.py fork` outputs the 4-option Next-Action Fork.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes
- `teach_engine.py` orchestrates session context discovery, advances `lesson-plan.md` concepts via `lesson_tracker.py`, and when a section completes, triggers `notes_compiler.py` to compile `notes.md` with 3-bullet recap and marks the section status as `review`.
- Formatted the standardized 4-option Next-Action Fork:
  1. Continue to next concept
  2. Deep dive / show edge cases
  3. Practical exercise / test understanding
  4. Skip to section summary / test me
- Verified all zero-BMad constraints across scripts, skills, and docstrings.

## Plan Change Log
- None.

## Review Triage Log
- quick-lens: All acceptance criteria met, all 5 unit tests pass cleanly, PEP 723 headers present, no BMad leakage.

## Verification

**Commands:**
- `uv run _tc/scripts/teach_engine.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_teach_engine.py` -- expected: All unit tests pass with exit code 0.

