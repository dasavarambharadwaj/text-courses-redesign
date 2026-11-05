---
title: 'Overhaul Intake, Memory Continuity, RAG Grounding & Universal Pedagogy'
type: 'refactor'
ticket: ''
created: '2026-11-01'
status: 'done'
baseline_revision: '852bbb6df446c6912573e727090574f93fd40976'
route: 'oneshot'
route_source: 'pinned'
risk: 'medium'
review: 'quick'
review_source: 'auto'
lenses_ran: []
review_loop_iteration: 0
followup_review_recommended: false
context:
  - 'PLAN.md'
  - '_tc/INTERACTION_STANDARDS.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** TextCourses onboarding suffers from cognitive fatigue in explanation density guessing and blurred teacher archetypes; lacks multi-select/hybrid teacher combination parsing; skips `/tc-research` by jumping directly to `/tc-create`; starves domain elicitation with one-line prompts; drops interactive teaching dialogue from `session.jsonl` and macro milestones from `profile/memlog.md`; exposes internal Triad tools (`tc-roadmap`, `tc-verify-course`) as public commands; hardcodes code-only checks in `practical_evaluator.py`; and completely omits RAG retrieval during `/tc-teach`.

**Approach:** Streamline `/tc-init` to a clean 5-stage intake with in-depth domain goal elicitation and orthogonal hybrid teacher selection; auto-recommend `/tc-research` before course scaffolding; internalize `tc-roadmap` with scope-aware multi-course decomposition for broad disciplines; decouple practical evaluations and style directives from software-only assumptions; mandate conversational turn logging via `teach_engine.py log-turn`; mirror macro milestones to `profile/memlog.md`; and wire SQLite FTS5 RAG retrieval directly into `tc-teach` to anchor all lesson delivery in authoritative sources.

## Boundaries & Constraints

**Always:**
- Keep all state mutations deterministic via Python standard library in `_tc/scripts/`.
- Synchronize all runtime script edits from `_tc/scripts/` to `skills/tc-init/scripts/runtime/` and related skills.
- Adhere strictly to the Universal Interaction Standards in `_tc/INTERACTION_STANDARDS.md` (FR-42): strictly 1 question per turn, plain English, dynamic `(Recommended)` tags.
- Support hybrid teacher combinations (`1, 2`, `1, 3`, `2, 3`, `all`) and merge their style keys and pedagogical directives without discarding components.
- Ensure all non-software learners (law, medicine, finance, design, humanities) pass practical evaluations and receive domain-appropriate case-study instruction.

**Never:**
- Never force learners to choose word count density during onboarding.
- Never override learner-selected teacher personas (eliminate involuntary beginner-to-Hypatia reassignment).
- Never fail practical project submissions simply for lacking Python/Rust programming keywords (`def`, `class`, `fn`).
- Never expose internal engine tools (`tc-roadmap`, `tc-verify-course`, `tc-redirect-course`, `tc-migrate`) as public user-facing slash skills.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Hybrid Teacher Selection | `set-preferences --teacher "1, 2"` | `profile/preferences.md` records `teacher: Feynman + Turing` and `styles_selected: [analogy, code_first]` | Preserves both styles cleanly |
| In-Depth Domain Goals | `set-preferences --subject "Systems" --goals "Raft, LSM"` | `profile/preferences.md` stores `target_subject` and `learning_goals` in frontmatter and body | Fallbacks to default if omitted |
| Workspace Scan Without Courses | `bootstrapper.py scan` (no courses, no research) | Returns `recommendation: /tc-research "<subject>"` | If research dossier exists, returns `/tc-create` |
| Non-Software Capstone Evaluation | Legal brief or medical analysis submitted to `practical_evaluator.py` | Evaluates against substantive rubric; does NOT fail for missing `def` / `fn` keywords | Rejects only empty or non-substantive text |
| Teaching Turn Dialogue Logging | Interactive exchange in `/tc-teach` | `teach_engine.py log-turn` appends event to `session.jsonl` | File locked with advisory retry |
| RAG Grounding in Teaching | `teach_engine.py session --course <slug>` | Returns active concept, recent session events, memlog tags, and top 2–3 BM25 source excerpts | Gracefully empty excerpts if no RAG DB |

</intent-contract>

## Code Map

- `_tc/scripts/bootstrapper.py`: Preference compilation, teacher parsing, density auto-inference, workspace scanner recommendations (`/tc-research`), goal persistence.
- `skills/tc-init/SKILL.md`: 5-stage intake protocol, in-depth Stage 2 prompt, sharpened Stage 5 teacher menu with combo tips, concluding next-action recommendation.
- `skills/tc-teach/SKILL.md`: Mandatory `log-turn` execution on interactive turns, universal worked-example/case-study lesson structure, RAG citation grounding.
- `_tc/INTERACTION_STANDARDS.md`: Codify 5-stage intake, universal pedagogical decoupling, public vs internal skill taxonomy.
- `_tc/scripts/course_builder.py`: Remove involuntary teacher override, read goals from preferences, mirror course creation to `profile/memlog.md`.
- `_tc/scripts/teach_engine.py`: Remove involuntary teacher override, enrich `session` output with trailing `memlog.md` entries, inject top BM25 source excerpts from `rag-db/index.db`.
- `_tc/scripts/practical_evaluator.py`: Remove programming syntax keyword checks (`def`, `fn`, `struct`), generalize deliverable inspection to `deliverables/` and `solution/`, mirror capstone pass to `profile/memlog.md` and `memlog.md`.
- `_tc/scripts/diagnostic_tester.py`: Mirror course completion milestones to `profile/memlog.md`.
- `_tc/scripts/indexer.py`: Add `verify-grounding` subcommand auditing curriculum concepts against `index.db` citations.
- `skills/tc-roadmap/SKILL.md` & `skills/tc-verify-course/SKILL.md`: Mark as internal engines rather than public user commands.
- `skills/tc-init/scripts/runtime/`: Mirrored copies of all updated runtime scripts.
- `tests/test_bootstrapper.py` & `tests/test_indexer.py`: Unit tests verifying hybrid teachers, research recommendations, RAG grounding, and domain decoupling.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/bootstrapper.py` -- Update preference compiler to parse multi-select teachers (`1, 2`, `feynman + turing`), merge style arrays, auto-derive density from experience, persist `--subject` and `--goals`, and add `/tc-research` to state machine recommendations.
- [x] `skills/tc-init/SKILL.md` -- Drop Stage 5 density question, expand Stage 2 domain goal elicitation, update Stage 5 teacher menu with orthogonal copy and combo tips, and conclude with `/tc-research "<subject>"` recommendation.
- [x] `_tc/INTERACTION_STANDARDS.md` -- Update intake standard from 6 stages to 5 stages, align lifecycle progression, mandate conversational turn logging, and codify universal domain decoupling.
- [x] `_tc/scripts/course_builder.py` -- Remove involuntary beginner teacher reassignment and mirror course creation milestone to `profile/memlog.md`.
- [x] `_tc/scripts/teach_engine.py` -- Remove involuntary beginner teacher reassignment, enrich `get_teaching_session` with trailing `memlog.md` entries, and inject top BM25 source citations for active concept from `rag-db/index.db`.
- [x] `skills/tc-teach/SKILL.md` -- Mandate calling `teach_engine.py log-turn` on interactive exchanges, universalize single-concept lesson template (case study / worked example / code), and anchor lessons in retrieved source citations.
- [x] `_tc/scripts/practical_evaluator.py` -- Remove programming keyword checks (`def`, `class`, `fn`, `struct`), generalize deliverable inspection to `deliverables/` or `solution/`, and mirror capstone pass to `courses/<slug>/memlog.md` and `profile/memlog.md`.
- [x] `_tc/scripts/diagnostic_tester.py` -- Mirror course completion milestones to `profile/memlog.md`.
- [x] `_tc/scripts/indexer.py` -- Add `verify-grounding` subcommand auditing curriculum concepts against `index.db` citations.
- [x] `skills/tc-roadmap/SKILL.md` & `skills/tc-verify-course/SKILL.md` -- Re-classify as internal engines.
- [x] `skills/tc-init/scripts/runtime/` -- Synchronize all updated runtime scripts from `_tc/scripts/`.
- [x] `tests/test_bootstrapper.py` & `tests/test_indexer.py` -- Add unit tests verifying hybrid teacher parsing, goal persistence, research recommendations, and RAG grounding verification.

**Acceptance Criteria:**
- Given a call to `bootstrapper.py set-preferences --teacher "1, 2"`, when inspected, `preferences.md` records both `analogy` and `code_first` styles without dropping either. (PASSED)
- Given an empty workspace, when `bootstrapper.py scan` runs, then `recommendation` is `/tc-research "<subject>"`. (PASSED)
- Given a non-software submission (legal analysis or clinical review) to `practical_evaluator.py`, when evaluated, it does not fail for missing programming syntax. (PASSED)
- Given an active teaching session, when `teach_engine.py session` runs, then the output includes active concept, trailing memlog tags, recent session turns, and retrieved RAG excerpts. (PASSED)
- Given full test suite execution `python -m pytest tests/`, all tests pass with zero regressions. (PASSED: 268/268 passed in 48.59s)

## Implementation Notes

- **Intake Redesign**: Dropped Stage 5 Explanation Density; explanation depth is derived automatically from domain experience level. Deep goal elicitation prompts added to Stage 2 (`--subject` and `--goals` persisted into `profile/preferences.md`).
- **Hybrid Teacher Blends**: Sharpened 3 orthogonal teacher archetypes (Feynman, Hypatia, Turing/Applied Builder) and added combo parsing (`1, 2`, `1, 3`, `2, 3`, `all`). Fixed involuntary beginner reassignment in `course_builder.py` and `teach_engine.py`.
- **Lifecycle Alignment**: Empty workspace scan returns `/tc-research "<subject>"` to ensure 5-Hat research precedes course generation. Fast-track `/tc-create` documented as secondary option.
- **Universal Pedagogy**: Generalised practical evaluator from code keyword checks (`def`, `fn`, `class`) to substantive analytical depth, structured arguments, and contingency safeguards. Reframed `code_first` to `Case-First & Applied Builder`.
- **Zero-Gap Memory Logging**: `teach_engine.py log-turn` mandated for interactive conversational exchanges; capstone completions and course graduation mirrored to `profile/memlog.md`.
- **RAG Grounding**: `teach_engine.py session` enriched with top 2 BM25 source citations from `courses/<slug>/rag-db/index.db`. Added `indexer.py verify-grounding` subcommand auditing curriculum concepts against indexed sources.
- **Internal Engine Tools**: `tc-roadmap` and `tc-verify-course` clearly designated as internal background engines invoked automatically rather than public user commands. Scope-aware roadmap decomposition codified for broad multi-disciplinary domains.
- **Runtime Synchronization & Test Suite**: Mirrored all script modifications to `skills/tc-init/scripts/runtime/` and individual skill folders. Test suite expanded to 268 unit tests, passing 100% with zero regressions.

## Plan Change Log

- 2026-11-01: Plan authored and approved via BMad change proposal.
- 2026-11-02: Executed all implementation tasks and verified across entire test suite. Status updated to done.

## Review Triage Log

- All changes verified by deterministic test suite and syntax compilation.
- Zero BMad references invariant verified across all runtime scripts and skills.

## Design Notes

- Complies fully with Universal Interaction Standards (FR-42), ADRs 1–5, and potato-proof hardware boundaries.
