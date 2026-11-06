# Sprint Change Proposal: Reconcile the Learner Vision, Public Surface, and Runtime Contract

**Initiative:** `initiative-textcourses`  
**Date:** 2026-11-05  
**Prepared by:** OpenCode (Developer agent)  
**Status:** Approved  
**Approved:** 2026-11-06  
**Scope:** **Major** — fundamental replan and runtime correction  
**Review mode:** Batch  
**Canonical storage decision:** root `_tc/` is the single research, source, course-state, decision, and learning-history root; learner notes remain visible under `courses/<slug>/notes/`  
**Supersedes:** the previous revision of this file at the same path

---

## Correction Notice

The previous revision was directionally correct, but it was not safe to execute. It treated a runtime gap as a documentation-synchronization exercise and asserted completion that the code does not support.

The corrected position is:

1. **This is implementation work, not documentation synchronization.** The runtime is missing or has broken implementations for the learner’s 12-point flow.
2. **The prior success criteria were false.** All four were marked `[x]`; none were evidenced against the runtime.
3. **The prior storage layout contradicted the learner’s point 2.** `research/<slug>/sources/` is outside `_tc/`; the corrected contract moves it under `_tc/research/<slug>/sources/`.
4. **The prior proposal assumed artifacts that do not exist.** The PRD ends at `FR-45`; `FR-46` through `FR-50` are absent. The UX spec ends at `CAP-6`; `CAP-7` and `CAP-8` are absent.
5. **The prior proposal omitted the two most important blockers:** only `tc` may be public, and section closure must require approval in every mode.
6. **The 326-test suite is green, but it does not cover the missing behavior.** One test actually codifies the Gate 1 dead end as expected behavior.

No runtime code, tests, skill packages, tickets, or planning artifacts were modified during this review. This proposal is the only corrected artifact produced by this workflow.

---

## Section 1: Issue Summary

### 1.1 Trigger and Context

The trigger is the completion claim for **Epic 12: Consumer UX, Unified `/tc` Dispatcher & Clean Workspace Substrate** and its end-to-end story, `story-end-to-end-consumer-ux-integration-suite-zero-regressions-plan.md`.

An end-to-end review compared the learner’s 12-point flow in `flow.html` against:

- `skills/tc/SKILL.md` and the other `skills/tc-*` packages;
- `_tc/scripts/tc.py`, `checkpoint_manager.py`, `teach_engine.py`, `notes_compiler.py`, `bootstrapper.py`, `course_builder.py`, and related engines;
- `tests/`;
- the PRD, architecture spine, both canonical specs, the initiative file, and `tickets.toml`.

The review is captured in `actual-flow.html`. Its twelve verbatim quotes and status matrix are the evidence base for this proposal. The “Fully Aligned” badges in `flow.html` are static markup, not computed runtime state.

### 1.2 Core Problem Statement

TextCourses currently has **two front doors and an incomplete runtime**:

- The public `/tc` skill checks gates, auto-ingests dropped books, and teaches an existing course, but it never calls `tc.py dispatch` and does not document course creation.
- The Python dispatcher models more of the intended state machine, but the topic-only “proceed with open docs” branch returns `state: creating_course` without calling `create_course`.
- Notes compile into the hidden `.tc/notes/` directory instead of the visible `courses/<slug>/notes/` directory.
- There is no intake mode choice, no auto-creation path, no source-approval loop, no dashboard generator, no section-close gate, and no session scrub.
- The planning artifacts describe a mixture of `.tc/`, `_tc/`, root `research/`, root `sources/`, and per-course states. None of them match the learner’s point 2.

**Issue type:** misunderstanding of original requirements plus a failed implementation approach. The product contract was partially captured, then implemented in disconnected pieces and marked done before the 12-point flow was actually enforced.

### 1.3 Supporting Evidence

| Evidence | Observation |
|---|---|
| Topic-only dispatch | `dispatch("Distributed Storage")` → `acquisition_gate`. `dispatch("1")` → `state: creating_course`, `action: proceed_open`, and `courses/` remains empty. The next `dispatch("1")` creates a new acquisition gate with slug `1`. |
| Notes path | `compile_notes` sets `course_dir = manifest_file.parent`, which is `courses/<slug>/.tc/`. The flat chapter file lands at `.tc/notes/chapter-XX.md`; the visible `notes/chapter-XX.md` remains a scaffold. |
| Public surface | Twelve TextCourses skill folders exist under `skills/` (`tc` plus eleven `tc-*` packages). Only `tc-roadmap` and `tc-verify-course` are labeled internal. `skills-lock.json` contains no `tc` or `tc-*` entry. |
| Auto mode | No `--mode interactive|auto` parser exists. Every acquisition and approval gate always pauses. |
| Dashboard | No dashboard generator exists. `flow.html` is a static specification page and does not read `_tc` state. |
| Section close | No close gate exists. The last concept tick marks the section `review`, compiles notes, and leaves `session.jsonl` in place. |
| Practical completion | A caller-supplied practical `PASS` can mark the entire course, all chapters, and all sections `completed`, bypassing section sign-off. |
| Test suite | `326 passed in 291.88s`. No test covers auto mode, dashboard generation, section close, or session deletion. `tests/test_unified_tc.py` asserts the dead-end `creating_course` response. |
| Artifact drift | The PRD ends at `FR-45`; the UX spec ends at `CAP-6`; the PRD MVP defers the dashboard; the PRD non-goal rejects mandatory gates but `FR-11` explicitly allows advancement without approval. |

### 1.4 Vision Status Matrix

**Verdict: 0 of 12 points fully evidenced.** Six are partial, four are absent, one is violated, and one is not enforced.

| # | Learner point (verbatim in Appendix A) | Status | Runtime evidence |
|---|---|---|---|
| 1 | Only `tc` exported; all others internal | **Not enforced** | 12 skill folders (`tc` plus eleven `tc-*` packages); only two labeled internal; `/tc` does not call `tc.py dispatch`; no `tc` entry in `skills-lock.json`. |
| 2 | Research/docs/decisions in `_tc`; only notes outside; memlogs per folder/section/chapter | **Violated** | Bootstrapper creates `_tc`, `.tc`, `research`, `sources`, `plan/sources`, `profile`, `roadmap`, and `portfolio`; memlogs are course-level and global only. |
| 3 | Intake asks topic, preferences, and execution mode | **Absent** | No mode question or parser; intake asks goal/topic, experience, and practicals. |
| 4 | Interactive research proposes the best sources and takes approval, then continues or stops | **Partial** | Gate 1 lists recommended books and found specs; no source proposal, no Reddit/Quora/general-web discovery, no “do more research” loop. |
| 5 | Auto mode runs all creation steps without approval; agent decides | **Absent** | All gates pause; no headless branch or mode switch. |
| 6 | Fetch all resources into the course research folder; missing material → user decides or supplies | **Partial / fragmented** | RFCs and papers are harvested; drop-in extraction goes to `sources/extracted/`; there is no focused per-course fallback. |
| 7 | Convert any material to Markdown without text loss; verify coverage; intense 4-hat debate | **Partial / unverified** | PDF/EPUB/Markdown/text extraction exists; no zero-loss coverage verification; the “hats” are a templated critique, and the same critique is written under three filenames. |
| 8 | Create roadmap, indexing, and a thorough course the teaching agent can read | **Partial** | Course builder scaffolds a fixed 4-chapter × 2-section course; `toc_aligner` is not called; `source_mapper` scans an often-empty `sources/raw/`; indexing is a separate manual command. |
| 9 | Interactive roadmap explanation, artifact review, final approval, then section plans covering teaching, coverage, verification | **Partial** | Gate 2 is created after the course is already scaffolded; section plans are generic and contain no source coverage or verification design. |
| 10 | `tc` teaches directly; conversation in `_tc`; notes on section completion; delete conversation history | **Partial / broken path** | Turn events go to `.tc/session.jsonl`; notes go to `.tc/notes/`; nothing deletes or truncates the session. |
| 11 | Track every context/decision; ask approval to close a section in every mode; teaching does not vary by mode | **Absent** | No section-close gate; completion is a state flip; practical `PASS` can complete the whole course; no mode distinction exists. |
| 12 | HTML dashboard on first initiation and when folders are formed; reads `_tc`; beautiful and interactive | **Absent** | No generator, no `status.html`, no `status-board/`; `flow.html` is static. |

---

## Section 2: Impact Analysis

### 2.1 Epic Impact

All twelve epics are affected by path or test updates. The substantive replan is concentrated in Epics 4, 5, 6, 9, 10, 11, and 12. The `done` status of any epic whose done criteria are contradicted below must be reopened.

| Epic | Current state | Impact |
|---|---|---|
| 1 — Runtime Engine | Done | Path and fixture updates for the new `_tc/` layout; no feature rescope. |
| 2 — Onboarding & Lifecycle | Done | Bootstrapper must stop creating duplicate roots, create the canonical `_tc/` tree, move profile/roadmap inside `_tc/`, and trigger dashboard generation. Reopen the bootstrapper story. |
| 3 — Curriculum Creation | Done | Course builder must produce a blueprint artifact for Gate 2 before section plans are finalized; section plans must include teaching, coverage, and verification. Reopen the course-builder story. |
| 4 — Instruction Delivery | Done | Notes compiler must write visible `courses/<slug>/notes/chapter-XX.md`; section close gate and session scrub must be added. Reopen the notes-compiler story. |
| 5 — Assessment & Verification | Done | A practical or diagnostic `PASS` must not mark the whole course complete; section close approval remains the only completion gate. Reopen assessment stories. |
| 6 — Faculty/Roadmap/Memlog | Done | Profile, roadmap, memlogs, and course state move under `_tc/`; memlogs must exist at workspace, research, course, chapter, and section scope. Reopen the layout and memlog stories. |
| 7 — Research & Dialectic | Done | The research debate must become a real 4-hat adversarial protocol with a decision log, not a templated critique. Reopen the research story. |
| 8 — Pedagogical Brainstorm/Practicals | Done | Section-plan verification and practical completion semantics must align with the close gate. Reopen the practical story. |
| 9 — Unified Dispatcher | Done | `tc.py` must stop dead-ending at Gate 1, become the only public dispatch path, add mode handling, and fix session paths. Reopen the dispatcher and session stories. |
| 10 — Sovereign Harvester/RAG | Done | All research and source paths move under `_tc/research/<slug>/`; add source proposal/approval, fetch-all, missing-material fallback, conversion coverage, and 4-hat debate evidence. Reopen harvester, indexer, and catalog stories. |
| 11 — Multi-Source Compiler | Done | Extractor must produce a zero-loss conversion ledger; source map must use the new paths and must not write fake pointers; coverage must fail on zero sources. Reopen compiler stories. |
| 12 — Consumer UX & Unified `/tc` | **Done, but contradicted** | Rewrite CAP-4 from per-course `.tc/` to root `_tc/`; add CAP-7 through CAP-10; add public-surface, auto-mode, source-approval, section-close, dashboard, and vision-contract stories. This is the integration epic. |

### 2.2 Story Impact

| Current story | Required change |
|---|---|
| `epic-consumer-ux-and-unified-tc/story-two-tier-clean-workspace-substrate-encapsulation-engine-cap-plan.md` | Rewrite from `courses/<slug>/.tc/` to root `_tc/`; visible study surface is `courses/<slug>/notes/`; remove `.tc`, root `research/`, `sources/`, and `plan/sources/`. |
| `epic-consumer-ux-and-unified-tc/story-interactive-checkpoint-gates-material-acquisition-pause-cap-plan.md` | Add mode branch, source proposal/approval loop, Gate 2 before section plans, and section-close gate. |
| `epic-consumer-ux-and-unified-tc/story-unified-tc-skill-intelligent-state-machine-cap-1-cap-6-plan.md` | Make `tc` the only public skill; route every state through `tc.py dispatch`; remove public power-user subcommands. |
| `epic-consumer-ux-and-unified-tc/story-end-to-end-consumer-ux-integration-suite-zero-regressions-plan.md` | Replace the 296-test claim with the 326-test baseline and add the 12-point vision contract suite. |
| `epic-unified-dispatcher-session-continuity-and-resilience/story-unified-runtime-dispatcher-plan.md` | Fix the `proceed_open` dead end; call the builder; add mode handling; return the next state, not `creating_course`. |
| `epic-unified-dispatcher-session-continuity-and-resilience/story-persistent-socratic-session-state-plan.md` | Move to per-section transcripts under `_tc/courses/<slug>/sessions/`; delete the section transcript only after close approval. |
| `epic-instruction-delivery/story-implement-textbook-notes-compiler-and-section-transition-man-plan.md` | Write visible chapter notes; add section close gate; do not advance on final tick; scrub the section transcript after approval. |
| `epic-faculty-roadmap-memlog/story-streamline-workspace-filesystem-layout-and-note-compaction-plan.md` | Move profile, roadmap, course state, and memlogs into `_tc/`; remove duplicate roots. |
| `epic-faculty-roadmap-memlog/story-implement-two-tier-pedagogical-memlog-engine-plan.md` | Add workspace, research, course, chapter, and section memlogs with milestone roll-up. |
| `epic-sovereign-knowledge-harvest-and-rag-engine/story-multi-source-deep-harvester-and-gold-standards-plan.md` | Write under `_tc/research/<slug>/`; add source proposal, fetch-all, and missing-material fallback. |
| `epic-sovereign-knowledge-harvest-and-rag-engine/story-potato-proof-sovereign-rag-indexer-and-fts5-engine-plan.md` | Move `rag-db/` under `_tc/research/<slug>/`; consume converted markdown; do not create course-level or root duplicates. |
| `epic-sovereign-knowledge-harvest-and-rag-engine/story-cross-source-catalog-synthesis-and-non-mirroring-curriculum-plan.md` | Add 4-hat debate evidence and conversion/coverage references; use `_tc/research/<slug>/rag-db/catalog.json`. |
| `epic-multi-source-deterministic-compiler/story-pure-python-verbatim-ingestion-pre-flight-probe-extractor-py-plan.md` | Add zero-loss `conversion-ledger.json` and `.md`; block below 100% text coverage unless approved. |
| `epic-multi-source-deterministic-compiler/story-complete-coverage-verification-ledger-plan.md` | Fail on zero sources; distinguish conversion coverage from curriculum coverage; write to `_tc/courses/<slug>/coverage-ledger.md`. |
| `epic-multi-source-deterministic-compiler/story-conveyor-belt-chapter-pipeline-symbol-table-source-map-plan.md` | Use `_tc/research/<slug>/sources/markdown/` and `_tc/courses/<slug>/source-map.toml`; never write fake line pointers. |
| `epic-assessment-verification/*` | Remove whole-course completion on a single practical or diagnostic pass; require section close approval. |
| `epic-autonomous-research-dialectic-synthesis/story-autonomous-five-hat-deep-research-engine-plan.md` | Replace the templated five-hat critique with the canonical four-hat debate protocol plus optional specialist lenses. |

### 2.3 Artifact Conflicts

| Artifact | Conflict | Required change |
|---|---|---|
| PRD `prd-textcourses.md` | `FR-11` explicitly allows advancement without approval. | Rewrite as notes compile + mandatory section-close gate. |
| PRD | `FR-29` says consolidate under visible `_tc/` but the MVP and many requirements still use `.tc/`, `research/<slug>/`, `sources/`, and `plan/sources/`. | Adopt the canonical root `_tc/` tree in §4.1 and apply the path replacement table. |
| PRD | Only `FR-1`–`FR-45` exist; `FR-46`–`FR-50` are absent. | Add `FR-46`–`FR-50` for public surface, modes, zero-loss conversion, section close, and dashboard. |
| PRD | MVP defers the dashboard and lists nine public commands. | Move the local dashboard into MVP; make `/tc` the only public command. |
| PRD | `UJ-2` climax celebrates “zero bureaucratic approval prompts.” | Rewrite to show notes compilation followed by a close-approval step. |
| PRD | `profile/`, `roadmap/`, `plan/`, `courses/<slug>/course.toml`, and `session.jsonl` paths conflict with root `_tc/`. | Apply the path replacement table; keep only notes visible. |
| Architecture `architecture-textcourses.md` | Generated workspace tree uses `.tc/`, root `profile/`, `research/`, `roadmap/`, and root course manifests. | Replace with the canonical tree; add AD-14 through AD-17. |
| Architecture | Says 10 skills and 254 tests. | One public skill plus internal capabilities; 326-test baseline plus new tests. |
| Architecture | Defers GUI/web dashboard. | Local generated status board is in scope; only hosted SaaS dashboard remains deferred. |
| UX spec `spec-consumer-ux-and-unified-tc.md` | CAP-4 encodes hidden per-course `.tc/`. | Rewrite to root `_tc/` plus visible notes. |
| UX spec | CAP-2 assumes every run pauses; no auto mode. | Add mode branch; auto bypasses creation gates only. |
| UX spec | Ends at CAP-6; no CAP-7/CAP-8. | Add CAP-7–CAP-10. |
| UX spec | Constraint says 296 tests. | Use 326 baseline plus vision-contract tests. |
| `workspace-hierarchy.md` | Entire two-tier `.tc/` tree is obsolete. | Replace with the root `_tc/` contract and scoped memlogs. |
| `interaction-flowchart.md` | Only shows interactive gates; no auto path, source-approval loop, Gate 2 ordering, or close gate. | Rewrite the flow. |
| `spec-multi-source-compiler.md` | Uses `research/<slug>/sources/` and `courses/<slug>/source-map.toml`. | Apply the path replacement table; add conversion coverage. |
| `source-map-schema.md` | `raw_path` examples point to root `research/`; course map at course root. | Update examples and storage paths. |
| `product-brief.md` | Describes `.tc/`, `plan/`, nine skills, immediate progression, and no dashboard. | Rewrite current-state sections; do not rewrite historical memlogs. |
| `initiative-textcourses.md` | Claims `FR-1`–`FR-23`, nine skills, and old `/tc-init` / `/tc-create` commands. | Update to the full requirement set, one public skill, and `/tc` lifecycle. |
| `tickets.toml` | Epics 10–12 are done; CAP-7–CAP-10 absent. | Reopen and resequence; add stories and dependencies. |
| `skills-lock.json` | No `tc` or `tc-*` entries. | Export exactly `tc`; internal capabilities are not exported. |
| Tests | 326 pass, but none cover the missing paths; one test asserts the dead end. | Add the vision-contract suite; update tests that encode obsolete layouts. |

### 2.4 Technical and Operational Impact

- **Storage migration:** Existing workspaces may contain `.tc/`, root `research/`, `sources/`, `plan/sources/`, root `profile/`, and root `roadmap/`. `tc-migrate` must preview and apply a consent-gated move to `_tc/`. New writes go only to the canonical tree. Read-only legacy fallback may remain during migration.
- **Public packaging:** Moving internal skills out of `skills/` changes the installed surface. This is intentional: the harness must expose only `tc`. Internal prompts become resources under `_tc/skills/`, not installable skills.
- **Data model:** `course.toml`, `source-map.toml`, `coverage-ledger.md`, `test-ledger.jsonl`, memlogs, and session transcripts all change paths. The dashboard consumes a derived snapshot rather than reading hidden files directly from the browser.
- **Teaching lifecycle:** Completion changes from a state flip to an explicit close conversation. Practical and diagnostic passes no longer complete a course.
- **Performance:** No new daemon or external service. The dashboard is a generated static HTML file; conversion coverage adds a deterministic ledger pass; the 4-hat debate adds bounded model work during research, not during every teaching turn.
- **MVP:** The MVP must expand to include modes, source approval, zero-loss conversion, close gates, dashboard, and the single public surface. Deferring the dashboard is no longer compatible with the learner’s stated contract.
- **Risk:** High. The storage migration touches every engine; the public-surface change touches packaging; the close gate changes teaching semantics. The work is still tractable because the compiler and harvester primitives exist.

### 2.5 Change Navigation Checklist Results

| Item | Status | Finding |
|---|---|---|
| 1.1 Triggering story | Done | Epic 12 completion claim and its E2E story; no single runtime story triggered it. |
| 1.2 Core problem | Done | Misunderstanding of requirements plus a failed implementation approach. |
| 1.3 Evidence | Done | Runtime reproductions, 326 passing tests, artifact conflicts, and the 12-point matrix. |
| 2.1 Current epic | Done | Epic 12 cannot remain done. |
| 2.2 Epic changes | Done | Reopen Epics 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, and 12; Epic 1 receives path/test updates. |
| 2.3 Remaining epics | Done | All epics receive path or test updates; substantive replan in the epics listed above. |
| 2.4 New epics | Done | No new epic required; Epic 12 becomes the integration owner. |
| 2.5 Order/priority | Done | Storage contract first, then public surface/dispatcher, then modes/research, then teaching close, then dashboard, then E2E. |
| 3.1 PRD | Action-needed | `FR-11`, `FR-29`, `FR-30`, `FR-38`–`FR-40`, `FR-43`, `FR-45`, MVP, and paths require edits; add `FR-46`–`FR-50`. |
| 3.2 Architecture | Action-needed | Workspace tree, skill packaging, paths, memlogs, session lifecycle, dashboard, and deferred section require edits. |
| 3.3 UI/UX | Action-needed | Rewrite CAP-1, CAP-2, CAP-4, CAP-6; add CAP-7–CAP-10; rewrite both companions. |
| 3.4 Other artifacts | Action-needed | Product brief, initiative file, tickets, specs, tests, `skills-lock.json`, and dashboard. |
| 4.1 Direct Adjustment | Viable | Viable only if done epics are reopened and the storage contract is treated as normative. Effort high; risk high. |
| 4.2 Potential Rollback | Partially viable | Roll back the `done` claims and the prior proposal, not the working compiler/harvester code. Full code rollback is not justified. |
| 4.3 MVP Review | Viable | Expand MVP; do not reduce it. The dashboard, modes, close gate, and single public surface are now core. |
| 4.4 Selected path | Done | Hybrid: direct adjustment + planning rollback + MVP expansion. Classified Major. |
| 5.1 Issue summary | Done | Section 1. |
| 5.2 Epic/artifact impact | Done | Sections 2.1–2.3. |
| 5.3 Recommended path | Done | Section 3. |
| 5.4 MVP/action plan | Done | Sections 3.3 and 5.4. |
| 5.5 Handoff | Done | Section 5. |
| 6.1 Checklist completion | Done | All applicable sections addressed. |
| 6.2 Proposal accuracy | Done | Corrected against runtime evidence; all prior unchecked claims removed. |
| 6.3 User approval | **Action-needed** | Explicit approval is required before implementation. |
| 6.4 Next steps | **Action-needed** | Handoff responsibilities and sequencing are defined; user must approve. |

---

## Section 3: Recommended Approach

### 3.1 Options Evaluated

| Option | Assessment | Effort | Risk |
|---|---|---|---|
| **Direct Adjustment** — modify existing stories in place | Viable only after reopening the `done` epics. The current backlog cannot be “adjusted” as documentation because the runtime is missing the behavior. | High | High |
| **Potential Rollback** — revert completed stories | Not justified as a code strategy. The compiler, harvester, and teaching primitives are useful. Roll back the unsupported `done` claims and the prior proposal, not the code. | Medium | Medium |
| **MVP Review** — reduce or redefine scope | The dashboard, modes, source approval, close gate, and public surface are now part of the product contract. Reducing them would repeat the original failure. Expand the MVP instead. | High | High |
| **Selected: Hybrid** — direct adjustment + planning rollback + MVP expansion | Reopen the contradicted epics, make root `_tc/` normative, add the missing stories, and sequence the work around the storage contract. | High | High |

### 3.2 Selected Path and Rationale

**Selected path:** Hybrid direct adjustment with a Major replan.

**Why:**

1. The learner’s 12 points are a product contract, not optional polish. Seven of them are absent or broken, and five more are partial.
2. The storage confusion is the root cause of several failures: notes, research, sessions, memlogs, and dashboards all disagree about where state lives. Fixing the contract first prevents another round of split paths.
3. The public surface is wrong. Adding features behind `/tc` while leaving eleven other skill folders exposed does not satisfy point 1.
4. The teaching invariant is wrong. Compiling notes and advancing without approval does not satisfy points 10 and 11, and auto mode must not weaken teaching.
5. Documentation-only edits would produce another “Fully Aligned” page with no runtime evidence.

**What is not proposed:** rewriting the compiler, harvester, or teaching engine from scratch. The existing primitives are reused; the work is to connect them, correct their contracts, and remove contradictory paths.

### 3.3 Effort, Risk, and Timeline

- **Effort:** approximately **15–25 engineer-days** for one developer, or **3–5 sprints** for a small team. The largest items are storage migration, public-surface packaging, source-approval/auto flow, and the vision-contract test suite.
- **Risk:** **High**. Storage migration touches every engine; the close gate changes teaching semantics; public packaging changes what the harness exposes. Mitigation: migrate behind a consent-gated tool, keep read-only legacy fallback during transition, and land the vision-contract tests before declaring any epic done.
- **Timeline impact:** **3–4 weeks** of replan and implementation before the 12-point contract can be demonstrated. The exact calendar depends on how much of the existing test suite must be rewritten for the new paths.
- **MVP impact:** **Expanded**. The local dashboard, mode selection, source approval, zero-loss conversion, section close gate, and single public surface move into MVP. Only hosted SaaS dashboards and multi-user features remain deferred.

---

## Section 4: Detailed Change Proposals

### 4.1 Canonical Storage Contract (Normative)

This contract resolves the `.tc/` vs `_tc/` conflict and the learner’s point 2. It is the single source of truth for every artifact edit and story.

```text
workspace/
├── _tc/                                  # Single authoritative root
│   ├── scripts/                          # Runtime engines
│   ├── skills/                           # Internal capability packages (never exported)
│   ├── INTERACTION_STANDARDS.md
│   ├── config.json
│   ├── cache/
│   │   ├── checkpoint.json
│   │   ├── consensus-trace.jsonl
│   │   └── audit-preflight.md
│   ├── profile/
│   │   ├── preferences.md
│   │   └── memlog.md                     # Global journey memory
│   ├── roadmap/
│   │   ├── roadmap.toml
│   │   ├── roadmap.md
│   │   └── memlog.md
│   ├── research/
│   │   └── <slug>/
│   │       ├── source-proposal.md        # Interactive source approval artifact
│   │       ├── gold-standards.md
│   │       ├── dossier.md
│   │       ├── digest.json
│   │       ├── sources.json
│   │       ├── debate.jsonl              # 4-hat decision log
│   │       ├── debate-summary.md
│   │       ├── conversion-ledger.md
│   │       ├── conversion-ledger.json
│   │       ├── memlog.md
│   │       ├── sources/
│   │       │   ├── raw/
│   │       │   ├── markdown/             # Zero-loss converted text
│   │       │   ├── rfcs/
│   │       │   ├── papers/
│   │       │   ├── docs/
│   │       │   ├── repos/
│   │       │   ├── transcripts/
│   │       │   └── user-provided/
│   │       └── rag-db/
│   │           ├── index.db
│   │           ├── catalog.json
│   │           └── manifest.json
│   ├── courses/
│   │   └── <slug>/
│   │       ├── course.toml
│   │       ├── overview.md
│   │       ├── blueprint.md              # Gate 2 review artifact
│   │       ├── source-map.toml
│   │       ├── coverage-ledger.md
│   │       ├── test-ledger.jsonl
│   │       ├── memlog.md
│   │       ├── sessions/
│   │       │   └── <chapter>/<section>.jsonl
│   │       └── chapters/
│   │           └── <chapter>/
│   │               ├── memlog.md
│   │               └── sections/<section>/
│   │                   ├── memlog.md
│   │                   ├── lesson-plan.md
│   │                   └── notes.md
│   └── status/
│       └── state.json                    # Derived dashboard snapshot
├── courses/
│   └── <slug>/
│       └── notes/
│           └── chapter-XX.md             # The only visible study material
├── portfolio/
│   └── <slug>-project/                   # Learner proof-of-work, not study material
└── status-board/
    └── index.html                        # Generated interface; reads _tc snapshot
```

**Normative rules:**

1. `_tc/` is the only root for research, source material, course state, decisions, memlogs, profile, and roadmap. Root `.tc/`, `research/`, `sources/`, `plan/`, `profile/`, and `roadmap/` are prohibited for new writes.
2. The only visible **study material** is `courses/<slug>/notes/chapter-XX.md`. `overview.md`, `blueprint.md`, manifests, plans, ledgers, and session transcripts live under `_tc/`.
3. `portfolio/` remains outside `_tc/` because it is the learner’s proof-of-work deliverable, not research or course state. `status-board/` is a generated interface, not study material.
4. Memlogs exist at every relevant scope: `_tc/profile/memlog.md`, `_tc/roadmap/memlog.md`, `_tc/research/<slug>/memlog.md`, `_tc/courses/<slug>/memlog.md`, `_tc/courses/<slug>/chapters/<chapter>/memlog.md`, and `_tc/courses/<slug>/chapters/<chapter>/sections/<section>/memlog.md`.
5. Append to the most specific active memlog. On section close, also append a milestone to the chapter, course, and global memlogs. Do not duplicate every turn at every level.
6. Conversation is stored per section at `_tc/courses/<slug>/sessions/<chapter>/<section>.jsonl`. On approved close, delete that section transcript only. Notes and memlog summaries survive.
7. New engines resolve canonical paths first. A read-only legacy fallback may exist only for migration; no engine may write to a legacy root.
8. `tc-migrate` must preview every move and require consent. It must not delete a legacy file until the canonical copy is verified.
9. `status-board/index.html` is self-contained and generated from `_tc/status/state.json` plus the canonical files. It must not require a server, CDN, external font, or network access.
10. The dashboard is regenerated on init and after every state mutation that changes a course, research artifact, gate, memlog, or skill package.

### 4.2 Runtime Contract and State Flow

The intended flow, with the mode branch:

```text
/tc
  → intake (topic + preferences + mode)
  → research analysis
  → source proposal
      ├─ interactive: approve / request more / remove / stop
      └─ auto: agent selects, logs, continues
  → fetch all approved sources to _tc/research/<slug>/sources/
      ├─ missing material: interactive asks user; auto logs decision and proceeds
  → convert to Markdown + conversion ledger
  → 4-hat adversarial debate + decision log
  → roadmap + blueprint
      ├─ interactive: Gate 2, review artifact in _tc, approve
      └─ auto: agent approves, logs
  → section plans (teaching, coverage, verification)
  → teaching turns (identical in both modes)
  → section close gate (mandatory in both modes)
      ├─ approve: write visible notes, log memlogs, delete section transcript
      └─ revise: stay in section
  → next section
```

| Step | Interactive mode | Auto mode | Teaching behavior |
|---|---|---|---|
| Intake | Asks topic, preferences, mode | Same | N/A |
| Research source proposal | Presents best sources; waits for approval or more research | Agent chooses; logs rationale | N/A |
| Missing material | User decides or supplies | Agent decides; logs gap | N/A |
| Gate 2 / blueprint | Presents artifact; waits | Agent approves; logs | N/A |
| Section plans | Created after approval | Created immediately | Same |
| Teaching | Same | Same | Identical |
| Section close | Mandatory approval | Mandatory approval | Identical |
| Notes + session scrub | After approval | After approval | Identical |

**Dispatcher requirements:**

- `tc.py dispatch` is the only lifecycle entrypoint. `skills/tc/SKILL.md` must call it for intake, creation, teaching, gates, and status.
- `proceed_open` must call the course builder (or blueprint builder), not return a dead-end `creating_course`.
- `start_lesson` must open the first teaching turn, not just return context.
- Every response must include the next state, the active artifact path, and the next action.
- The public skill must not expose `/tc test`, `/tc practicals`, `/tc notes`, `/tc roadmap`, `/tc redirect`, `/tc verify`, `/tc research`, `/tc extract`, or `/tc init` as public commands. Those are internal capabilities invoked by `/tc`.

**Section close gate:**

- Triggered after the final concept is mastered, never before.
- Shows the notes path, a short recap, the section coverage summary, and the verification status.
- Options: approve close, revise notes, re-explain, keep session open.
- In auto mode the gate still appears. There is no bypass.
- On approval: set section to `completed`, append section/chapter/course/global memlog entries, delete the section transcript, and present the next section.
- Until approval: section stays `review`; the next section cannot start.

### 4.3 PRD Changes

#### PRD Change 1: `FR-11` and `UJ-2` — Section Close Replaces Flow-Preserving Auto-Advance

**Section:** `4.3 Instructional Delivery & Flow-Preserving Notes` and `UJ-2`

**OLD:**

```markdown
#### FR-11: Automated Flow-Preserving Notes Compilation
Upon completing the final concept checklist item in a section, the system SHALL automatically compile `notes.md` in the background, write it to disk, print a concise 3-bullet recap, and update `course.toml` to `status: review`. Realizes UJ-2.
- **Consequences (testable):**
  - `notes.md` is guaranteed to exist on disk before section advancement is unlocked.
  - Learner can immediately advance to the next section via `[1]` without waiting for or engaging in a mandatory multi-turn approval dialogue.
  - Learner may optionally edit or request re-distillation of `notes.md`.
```

**NEW:**

```markdown
#### FR-11: Notes Compilation and Section-Close Gate
Upon completing the final concept checklist item in a section, the system SHALL compile the section notes into `courses/<slug>/notes/chapter-XX.md`, append the section/chapter/course memlogs, and open a Section Close Gate. Realizes UJ-2, UJ-6.
- **Consequences (testable):**
  - The visible chapter notes file exists before the close gate opens.
  - The learner reviews the recap and notes path and explicitly approves close in BOTH interactive and auto modes.
  - Until approval, the section remains `review` and the next section cannot start.
  - On approval, the section becomes `completed`, the section transcript is deleted, and the approval is recorded in the section/chapter/course/global memlogs.
  - The learner may revise or request re-distillation before approval.
```

**UJ-2 OLD:**

```markdown
5. When the final concept in the section completes, `tc-teach` automatically compiles `notes.md` in the background, prints a 3-bullet recap, updates `course.toml` to `status: review`, and presents the next chapter fork.
- **Climax:** David finishes the section in uninterrupted flow with zero bureaucratic approval prompts, while a high-density `notes.md` reference is securely saved on disk.
- **Resolution:** David advances to Section 2 or triggers diagnostic testing.
```

**UJ-2 NEW:**

```markdown
5. When the final concept in the section completes, `/tc` compiles the visible chapter notes, prints a 3-bullet recap, and opens the Section Close Gate.
- **Climax:** David reviews the recap and the chapter notes, approves close, and the section transcript is removed while the notes remain.
- **Resolution:** Only after approval does David advance to Section 2 or trigger diagnostic testing.
```

**Rationale:** Point 11 requires close approval in every mode. `FR-11` currently says the opposite, so the PRD must change before the runtime can be considered correct.

---

#### PRD Change 2: `FR-29` — Make Root `_tc/` and Visible Notes Canonical

**Section:** `FR-29 Streamlined Sovereign Folder Architecture & BMad Ecosystem Parity`

**OLD:**

```markdown
- **Consequences (testable):**
  - Eliminates `.tc/` vs `_tc/` ambiguity by consolidating all engine scripts, caches, and configs under visible `_tc/`.
  - Flattens 4-level deep course nesting into direct chapter textbook files: `courses/<slug>/notes/chapter-XX.md`.
  - Links practical capstones directly to courses: `portfolio/<slug>-project/`.
  - Equips all 10 skills with `bmod.toml` manifests and 3-tier `customize.toml` override support.
  - Eliminates triplicate script redundancy by routing all skills exclusively to `_tc/scripts/`.
```

**NEW:**

```markdown
- **Consequences (testable):**
  - Root `_tc/` is the single authoritative root for research, sources, course state, decisions, memlogs, profile, and roadmap.
  - The only visible study material is `courses/<slug>/notes/chapter-XX.md`; `overview.md`, `blueprint.md`, manifests, plans, ledgers, and session transcripts live under `_tc/`.
  - `.tc/`, root `research/`, root `sources/`, `plan/sources/`, root `profile/`, and root `roadmap/` are prohibited for new writes.
  - `portfolio/` remains the learner’s proof-of-work deliverable outside `_tc/`; it is not study material.
  - Memlogs exist at workspace, research, course, chapter, and section scope.
  - Only `tc` is public. Internal capability packages live under `_tc/skills/` and are not exported.
  - All engine invocations route through `_tc/scripts/`; no skill-local runtime copies.
```

**Rationale:** Points 1, 2, and 11. This also resolves the PRD’s own `.tc/` vs `_tc/` contradiction.

---

#### PRD Change 3: `FR-30` — Four Voting Hats, Not a Templated Five-Hat Critique

**Section:** `FR-30 Autonomous 5-Hat Deep Research Engine`

**OLD:**

```markdown
- Applies **5-Hat Critical Reflection (Tree-of-Thought Dialectic)**:
  1. *Industry Practitioner Hat*
  2. *Academic Purist Hat*
  3. *Beginner Friction Hunter Hat*
  4. *Edge-Case Systems Engineer Hat*
  5. *Modern Ecosystem Reviewer Hat*
```

**NEW:**

```markdown
- Applies the **4-Hat Adversarial Debate** as the canonical research protocol:
  1. *Industry Practitioner Hat*: production patterns and operational reality.
  2. *Academic Purist Hat*: formal models, invariants, and proofs.
  3. *Beginner Friction Hunter Hat*: hidden assumptions and cognitive load.
  4. *Edge-Case Systems Engineer Hat*: concurrency, failure modes, and performance cliffs.
- Every source, topic, and roadmap decision MUST receive at least one challenge round. If unresolved, a second round is required.
- The AI-Era/Modern Ecosystem lens may join as a non-voting specialist when relevant; it is not a fifth debate seat.
- Every decision is written to `_tc/research/<slug>/debate.jsonl` with positions, evidence, resolution, confidence, and dissent; the readable summary is `debate-summary.md`.
```

**Rationale:** Point 7 asks for an intense 4-hat debate, not a single templated critique replicated under three filenames.

---

#### PRD Change 4: `FR-8` — Gate 2 Reviews a Blueprint Before Section Plans

**Section:** `FR-8 The Triad Consensus Loop`

**OLD:**

```markdown
- **Consequences (testable):**
  - Curriculum reconciliations, audit critiques, and consensus resolutions are recorded in `.tc/cache/consensus-trace.jsonl` for full auditability.
```

**NEW:**

```markdown
- **Consequences (testable):**
  - Curriculum reconciliations, audit critiques, and consensus resolutions are recorded in `_tc/cache/consensus-trace.jsonl`.
  - Course creation writes a reviewable blueprint to `_tc/courses/<slug>/blueprint.md` before section plans are finalized.
  - Interactive mode presents the blueprint and waits for approval; auto mode records the agent’s decision and continues.
  - After approval, every section plan contains: (a) a teaching plan, (b) a source-coverage map with line spans, and (c) a verification plan with diagnostic questions and mastery criteria.
```

**Rationale:** Point 9. The current gate appears after scaffolding, so it is not a real review gate.

---

#### PRD Change 5: `FR-38`, `FR-39`, `FR-40` — One Public Dispatcher, Per-Section Sessions, Close-Aware Fork

**Section:** `FR-38`–`FR-40`

**OLD (FR-38 excerpt):**

```markdown
The system SHALL provide a unified CLI entrypoint `_tc/scripts/tc.py` dispatching all runtime commands (`init`, `research`, `create`, `teach`, `eval`, `notes`, `audit`, `dag`), consolidating script invocation into a single source of truth and eliminating redundant script duplication across skill folders.
```

**NEW (FR-38 excerpt):**

```markdown
The system SHALL expose exactly one public skill, `/tc`, and route every lifecycle state through `_tc/scripts/tc.py dispatch` (`intake`, `research`, `create`, `teach`, `test`, `practicals`, `notes`, `status`, `migrate`). Internal engines are invoked by `/tc`; they are not public commands.
- `skills/tc/` is the only installed skill; `skills-lock.json` exports exactly `tc`.
- Internal capability packages live under `_tc/skills/` and are not listed as public commands.
- The dispatcher must return the next state and active artifact path; it must not return a dead-end `creating_course`.
```

**OLD (FR-39 excerpt):**

```markdown
The instruction engine SHALL record structured conversational turn snapshots into `courses/<slug>/session.jsonl` upon every concept transition and interactive exchange.
```

**NEW (FR-39 excerpt):**

```markdown
The instruction engine SHALL record structured conversational turns into `_tc/courses/<slug>/sessions/<chapter>/<section>.jsonl` for the active section. On approved section close, the section transcript is deleted; notes and memlog summaries remain. A new section starts with a fresh transcript.
```

**OLD (FR-40 excerpt):**

```markdown
- When all concepts in a section are mastered and practicals are passed, option `[1]` dynamically adapts to `- [1] Advance to Next Section: Compiles notes and begins next chapter`.
```

**NEW (FR-40 excerpt):**

```markdown
- When all concepts in a section are mastered and practicals are passed, option `[1]` adapts to `- [1] Review Notes and Close Section`. It opens the Section Close Gate; it does not advance until the learner approves.
```

**Rationale:** Points 1, 10, and 11. The fork must not silently bypass the close gate.

---

#### PRD Change 6: `FR-43` and `FR-45` — Research Paths, Source Approval, and Fetch-All

**Section:** `FR-43` and `FR-45`

**OLD (FR-43 path examples):**

```markdown
- **FR-43.1:** ... `research/<slug>/gold-standards.md`.
- **FR-43.2:** ... `research/<slug>/sources/repos/`.
- **FR-43.3:** ... `research/<slug>/sources/transcripts/`.
- **FR-43.4:** ... place the file in `research/<slug>/sources/` or proceed.
- **FR-43.5:** ... `research/<slug>/sources.json`, `research/<slug>/digest.json`, and `research/<slug>/dossier.md`.
```

**NEW (FR-43 path examples):**

```markdown
- **FR-43.1:** ... `_tc/research/<slug>/gold-standards.md`.
- **FR-43.2:** ... `_tc/research/<slug>/sources/repos/`.
- **FR-43.3:** ... `_tc/research/<slug>/sources/transcripts/`.
- **FR-43.4:** ... place the file in `_tc/research/<slug>/sources/user-provided/` or proceed.
- **FR-43.5:** ... `_tc/research/<slug>/sources.json`, `_tc/research/<slug>/digest.json`, and `_tc/research/<slug>/dossier.md`.
- **FR-43.6 Source Proposal & Approval Loop:** After research analysis, write `_tc/research/<slug>/source-proposal.md` with the best books, papers, official docs, repositories, courses, and general-web findings, including rationale and availability. Interactive mode offers approve, request more research, remove/add a source, or stop. Auto mode lets the agent choose and records the decision in the research memlog and `debate.jsonl`.
- **FR-43.7 Fetch-All & Missing-Material Fallback:** After approval (or auto selection), fetch every selected resource into `_tc/research/<slug>/sources/`. If a resource cannot be obtained, interactive mode asks the learner to proceed or supply it; auto mode records the gap and proceeds with the best available open material. No source is silently dropped.
```

**OLD (FR-45 path examples):**

```markdown
- **FR-45.2:** ... `research/<slug>/sources/catalog.json`.
- **FR-45.3:** ... `research/<slug>/sources/index.db`.
- **FR-45.6:** When `research/<slug>/sources/` contains zero files...
- **FR-45.8:** ... (`courses/<slug>/rag-db/` and `research/<slug>/rag-db/`).
```

**NEW (FR-45 path examples):**

```markdown
- **FR-45.2:** ... `_tc/research/<slug>/rag-db/catalog.json`.
- **FR-45.3:** ... `_tc/research/<slug>/rag-db/index.db`.
- **FR-45.6:** When `_tc/research/<slug>/sources/` contains zero files...
- **FR-45.8:** ... only `_tc/research/<slug>/rag-db/`; no course-level or root duplicate.
```

**Rationale:** Points 4, 6, and 7. This also removes the root `research/` contradiction.

---

#### PRD Change 7: Add `FR-46`–`FR-50`

**Section:** New `4.11` after `FR-45`

```markdown
### 4.11 Learner-Control, Source Integrity, and Status Surface

#### FR-46: Single Public Entrypoint & Internal Capability Boundary
Only the `tc` skill is public. All other capabilities are internal and callable only by `tc` or its dispatcher.
- `skills/tc/` is the only installed skill; `skills-lock.json` exports exactly `tc`.
- Internal capability packages live under `_tc/skills/` and are not documented as public commands.
- `/tc` calls `_tc/scripts/tc.py dispatch` for every lifecycle state.
- A test asserts that `skills/` contains no other `tc-*` package and that `skills-lock.json` exports only `tc`.

#### FR-47: Intake Mode Selection & Autonomy Boundary
Intake captures the topic, preferences, and an explicit execution mode: `interactive` or `auto`.
- Interactive: source proposal approval and Gate 2 blueprint approval are required.
- Auto: all creation steps run without approval; the agent selects sources, resolves gaps, and records every decision in the research/course memlogs and debate log.
- Teaching behavior is identical in both modes.
- The Section Close Gate is mandatory in both modes; auto mode never bypasses section sign-off.

#### FR-48: Zero-Loss Material Conversion & Coverage Ledger
Every text-bearing source is converted to Markdown without text loss using a type-specific extractor.
- Supported types include PDF, EPUB, DOCX, HTML, Markdown, plain text, reStructuredText, source code, notebooks, transcripts, JSON, TOML, YAML, and CSV.
- For each source, `_tc/research/<slug>/conversion-ledger.json` and `.md` record: source hash, pages/sections, input characters, output characters, omitted images/tables, omission reasons, and coverage percentage.
- Text coverage must be 100%. An omission requires explicit learner approval in interactive mode or an explicit agent decision in auto mode; it is never silent.
- Scanned image PDFs fail fast with clear guidance; OCR remains a non-goal.
- The curriculum coverage audit is separate and must map every source section to a course section or an approved deduplication.

#### FR-49: Section Close Gate & Session Lifecycle
After the final concept is mastered, `/tc` compiles the visible chapter notes and opens the Section Close Gate.
- The gate shows the notes path, recap, coverage summary, and verification status.
- Options: approve close, revise notes, re-explain, keep session open.
- Approval is required in interactive and auto modes.
- On approval: section status becomes `completed`, memlog entries are appended at section/chapter/course/global scope, and the section transcript is deleted.
- No next section can start before approval.

#### FR-50: Initiation Status Dashboard
A self-contained status dashboard is generated when `/tc` first initializes the workspace and after every state mutation.
- Output: `status-board/index.html`, generated from `_tc/status/state.json` and the canonical `_tc/` files.
- It shows the roadmap, active course/chapter/section/concept, source and conversion coverage, research debate summary, memlog timeline, decisions, unresolved gates, and the next action.
- It is interactive, responsive, accessible, and works with no server, CDN, external font, or network access.
- `flow.html` is a static specification page, not the dashboard.
```

**Rationale:** These five requirements close the gaps that the prior proposal assumed were already covered.

---

#### PRD Change 8: MVP, Non-Goals, Assumptions, and Public Surface

**Section:** `6.1 In Scope`, `6.2 Out of Scope`, `5. Non-Goals`, `8.3`, `10. Assumptions Index`

**OLD (MVP excerpts):**

```markdown
- **9 User-Facing Commands:** `tc-init`, `tc-roadmap`, `tc-create`, `tc-teach`, `tc-test-me`, `tc-practicals`, `tc-redirect-course`, `tc-migrate`, `tc-index`.
- **2 Internal Engine Skills:** `tc-research` and `tc-verify-course`.
- **Two-Tier Pedagogical Memlog:** Global learner timeline (`profile/memlog.md`) and course-level session memory (`courses/<slug>/memlog.md`).
- **Streamlined Sovereign Filesystem Layout:** Visible `_tc/` (engine & cache), `roadmap/`, `profile/`, `courses/<slug>/notes/chapter-XX.md`, and `portfolio/<slug>-project/`.
```

**NEW (MVP excerpts):**

```markdown
- **1 Public Skill/Command:** `/tc`. All other capabilities are internal.
- **Internal Capability Packages:** research, verification, indexing, migration, and practical evaluation live under `_tc/skills/` and are invoked by `/tc`.
- **Scoped Pedagogical Memlogs:** `_tc/profile/memlog.md`, `_tc/roadmap/memlog.md`, `_tc/research/<slug>/memlog.md`, `_tc/courses/<slug>/memlog.md`, chapter memlog, and section memlog.
- **Root `_tc/` Storage:** research, sources, course state, decisions, and history inside `_tc/`; only `courses/<slug>/notes/chapter-XX.md` is visible study material.
- **Execution Modes:** interactive source/roadmap approval and unattended auto creation, with identical teaching and mandatory section close.
- **Zero-Loss Conversion Ledger:** every source converted to Markdown with an auditable coverage record.
- **Generated Status Dashboard:** `status-board/index.html`, regenerated on init and state changes.
```

**OLD (out-of-scope excerpt):**

```markdown
- **Web UI / Graphical Dashboard:** Deferred to post-v1 community tools.
```

**NEW (out-of-scope excerpt):**

```markdown
- **Hosted SaaS Dashboard / Cloud UI:** Deferred. The local generated `status-board/index.html` is in scope.
- **Unattended Teaching:** Auto mode applies to course creation only. Teaching and section close are always learner-gated.
```

**OLD (non-goal excerpt):**

```markdown
- **Not a Mandatory Quiz Gate:** TextCourses will NEVER block a learner from advancing because they refused to answer a quiz. Active recall is always optional and user-sovereign.
```

**NEW (non-goal excerpt):**

```markdown
- **Not a Mandatory Quiz Gate:** Active recall remains optional. The Section Close Gate is a notes/learning sign-off, not a quiz, and it does not require a test answer.
```

**OLD (public surface excerpts):**

```markdown
- `/tc-init [--reconfigure]`
- `/tc-roadmap "<domain-or-track>" [--mode party-mode|auto]`
- `/tc-create "<topic>" [--mode interactive|auto] [--archetype <slug>] [--reference <url|text>]`
- `/tc-research "<topic>" [--depth <shallow|deep>]`
- `/tc-verify-course [course-slug]`
- `/tc-teach [course-slug] [chapter-num] [section-num]`
- `/tc-test-me [course-slug] [--all|--chapter <num>]`
- `/tc-practicals [course-slug] [--project <id>]`
- `/tc-redirect-course [course-slug]`
- `/tc-migrate [--dry-run]`
```

**NEW (public surface excerpt):**

```markdown
- `/tc` — the only public command. It accepts a topic, a natural-language request, or a reply to the active gate/fork.
- Internal engines are not public commands. They are invoked by `/tc` through `_tc/scripts/tc.py dispatch`.
- `/tc` supports `--mode interactive|auto` at intake; the mode is persisted in `_tc/profile/preferences.md`.
```

**OLD (assumption excerpt):**

```markdown
- **[ASSUMPTION: §4.3 / FR-11]**: Background automated compilation of `notes.md` with instant progression preserves learner flow state while satisfying the knowledge permanence requirement.
```

**NEW (assumption excerpt):**

```markdown
- **[ASSUMPTION: §4.3 / FR-11]**: Automatic notes compilation followed by an explicit Section Close Gate preserves both knowledge permanence and learner sovereignty. The learner reviews notes before the section is closed.
```

**Rationale:** The MVP, public surface, non-goals, and assumptions must agree with points 1, 5, 10, and 11.

---

#### PRD Change 9: Global Path and Terminology Replacements

Apply these replacements everywhere in the PRD, including user journeys, requirements, MVP, constraints, and assumptions.

| Old text | New text |
|---|---|
| `.tc/research/<slug>/` | `_tc/research/<slug>/` |
| `research/<slug>/` | `_tc/research/<slug>/` |
| `.tc/cache/` | `_tc/cache/` |
| `courses/<slug>/.tc/` | `_tc/courses/<slug>/` |
| `courses/<slug>/course.toml` | `_tc/courses/<slug>/course.toml` |
| `courses/<slug>/overview.md` | `_tc/courses/<slug>/overview.md` |
| `courses/<slug>/memlog.md` | `_tc/courses/<slug>/memlog.md` |
| `courses/<slug>/session.jsonl` | `_tc/courses/<slug>/sessions/<chapter>/<section>.jsonl` |
| `courses/<slug>/source-map.toml` | `_tc/courses/<slug>/source-map.toml` |
| `courses/<slug>/coverage-ledger.md` | `_tc/courses/<slug>/coverage-ledger.md` |
| `courses/<slug>/test-ledger.jsonl` | `_tc/courses/<slug>/test-ledger.jsonl` |
| `profile/preferences.md` | `_tc/profile/preferences.md` |
| `profile/memlog.md` | `_tc/profile/memlog.md` |
| `plan/preferences.md` | `_tc/profile/preferences.md` |
| `plan/sources/` | `_tc/research/<slug>/sources/user-provided/` |
| `roadmap/roadmap.toml` | `_tc/roadmap/roadmap.toml` |
| `roadmap/roadmap.md` | `_tc/roadmap/roadmap.md` |
| `courses/<slug>/rag-db/` and `research/<slug>/rag-db/` | `_tc/research/<slug>/rag-db/` |
| `all 9 skills` / `all 10 skills` | one public `tc` skill plus internal `_tc/skills/` capabilities |
| `296 tests` / `254 tests` | `326` baseline tests plus the new vision-contract tests |

Also update the glossary entries for `Compiled Notes`, `Next-Action Fork`, `Style Profile`, and `Test Ledger` so they use the canonical paths and the close-gate semantics.

---

### 4.4 Architecture Changes

#### Architecture Change 1: Replace the Generated Workspace Tree

**Section:** `Generated Learner Workspace Structure`

**OLD (key roots):**

```text
.tc/
_tc/
profile/
roadmap/
research/<slug>/
courses/<slug>/course.toml
courses/<slug>/memlog.md
courses/<slug>/session.jsonl
courses/<slug>/notes/
```

**NEW:**

Replace the entire tree with the canonical tree in **§4.1**. The non-negotiable points are:

- `_tc/` is the only machine/research/docs root.
- `profile/` and `roadmap/` live under `_tc/`.
- `research/<slug>/` lives under `_tc/research/`.
- `course.toml`, `overview.md`, `blueprint.md`, `source-map.toml`, `coverage-ledger.md`, `test-ledger.jsonl`, plans, memlogs, and sessions live under `_tc/courses/<slug>/`.
- The visible course root contains only `notes/`.
- `status-board/index.html` is generated at the workspace root.
- `portfolio/` remains the learner’s proof-of-work deliverable.

**Rationale:** The current tree is the source of the duplicate-state bugs.

#### Architecture Change 2: Add AD-14 — Single Public Surface

```markdown
### AD-14 — Single Public Surface & Internal Capability Boundary
- **Binds:** Skill packaging, `skills/tc/`, `_tc/skills/`, `skills-lock.json`, `tc.py`.
- **Prevents:** Learners discovering internal engines, bypassing `/tc`, or running a second front door that disagrees with the dispatcher.
- **Rule:** Exactly one skill is exported: `tc`. All other capability packages live under `_tc/skills/` and are invoked by `/tc` or `tc.py dispatch`. `skills-lock.json` exports exactly `tc`. Public docs and command menus list exactly one command.
```

#### Architecture Change 3: Add AD-15 — Root `_tc/` Storage and Scoped Memlogs

```markdown
### AD-15 — Root `_tc/` Storage & Scoped Memlog Topology
- **Binds:** `bootstrapper.py`, `course_builder.py`, `notes_compiler.py`, `teach_engine.py`, `scout.py`, `indexer.py`, `harvester.py`, `memlog.py`, `migrator.py`.
- **Prevents:** Duplicate roots, split readers/writers, hidden notes, and lost decisions.
- **Rule:**
  1. New writes go only to the canonical tree in `workspace-hierarchy.md`.
  2. `.tc/`, root `research/`, root `sources/`, `plan/sources/`, root `profile/`, and root `roadmap/` are legacy read-only paths during migration.
  3. Memlogs exist at workspace, research, course, chapter, and section scope. Append to the most specific active scope; roll up milestones to parents.
  4. `tc-migrate` previews every move and requires consent. No legacy file is deleted until the canonical copy is verified.
```

#### Architecture Change 4: Add AD-16 — Mode Boundary and Section Close

```markdown
### AD-16 — Execution Mode Boundary & Teaching Invariant
- **Binds:** `tc.py`, `checkpoint_manager.py`, `course_builder.py`, `teach_engine.py`, `notes_compiler.py`.
- **Prevents:** Auto mode weakening teaching, section advancement without approval, and practical/diagnostic passes completing a course.
- **Rule:**
  1. `interactive` and `auto` affect creation only.
  2. Auto mode bypasses source approval and Gate 2; it logs every decision.
  3. Teaching behavior is identical in both modes.
  4. The Section Close Gate is mandatory in both modes.
  5. No practical or diagnostic result can mark a section or course `completed` without close approval.
```

#### Architecture Change 5: Add AD-17 — Generated Status Dashboard

```markdown
### AD-17 — Generated Status Dashboard
- **Binds:** `tc.py`, `bootstrapper.py`, `status_dashboard.py`, `_tc/status/state.json`, `status-board/index.html`.
- **Prevents:** A static mock dashboard, browser CORS failures, external network dependencies, and stale status views.
- **Rule:**
  1. The dashboard is generated on `/tc` initialization and after every state mutation.
  2. The generator reads `_tc/` and writes a self-contained `status-board/index.html` with an embedded state snapshot.
  3. It must work from `file://` with no server, CDN, external font, or network request.
  4. It must expose roadmap, active pointer, source/conversion coverage, debate summary, memlog timeline, gates, and next action.
```

#### Architecture Change 6: Update AD-4, AD-6, AD-10, AD-12, AD-13, and Repository Structure

- **AD-4:** `.tc/research/` → `_tc/research/`; `.tc/cache/` → `_tc/cache/`.
- **AD-6:** “9 installable skills” → one public `tc` skill plus internal packages under `_tc/skills/`.
- **AD-8 / AD-9:** “all 10 skills” → the public `tc` contract plus internal capabilities.
- **AD-10:** all `research/<slug>/` paths → `_tc/research/<slug>/`; source proposal, fetch-all, and missing-material fallback become part of the rule.
- **AD-12 / AD-13:** `rag-db/` only under `_tc/research/<slug>/`; `catalog.json` path updated.
- **Repository structure:** replace the ten-skill list with `skills/tc/` plus `_tc/skills/`; update the test count from 254 to 326 baseline plus new tests.

#### Architecture Change 7: Deferred Section

**OLD:**

```markdown
4. **GUI / Web Dashboard Interface:**
   - *Reason Deferred:* Editor/CLI and agent harnesses provide the distraction-free build substrate. A graphical web viewer is a downstream companion tool.
```

**NEW:**

```markdown
4. **Hosted GUI / Cloud Dashboard:**
   - *Reason Deferred:* A hosted, multi-user dashboard remains out of scope. The local generated `status-board/index.html` is in scope.
```

#### Architecture Change 8: Data and Integration Contracts

- `source-map-schema.md`: update `raw_path` examples to `_tc/research/<slug>/sources/markdown/...`; update the map location to `_tc/courses/<slug>/source-map.toml`.
- `coverage-ledger.md`: distinguish conversion coverage from curriculum coverage; both are required.
- `session.jsonl`: document per-section transcripts and deletion on approved close.
- `memlog.md`: document scope resolution and milestone roll-up.
- `conversion-ledger.json`: add a schema for source hash, input/output characters, pages/sections, omissions, and coverage percentage.
- `status/state.json`: add the dashboard snapshot schema.
- Diagrams: update the compiler pipeline to show `_tc/research/<slug>/sources/markdown/`, conversion coverage, 4-hat debate, blueprint approval, section plans, and close gate.

---

### 4.5 UX Specification Changes

#### UX Change 1: Rewrite the “Why” and Success Signal

**OLD (excerpt):**

```markdown
2. Preserving step-by-step interactive human checkpoints (including graceful book-acquisition pauses) rather than unattended steamrolling.
4. Encapsulating machine state into a hidden `.tc/` directory to keep the workspace calm and focused.
```

**NEW (excerpt):**

```markdown
2. Offering two creation modes: interactive source/roadmap approval, or unattended auto creation with agent decisions. Teaching and section close remain learner-gated in both modes.
4. Encapsulating research, sources, course state, decisions, and history in root `_tc/`, with only `courses/<slug>/notes/` visible as study material.
```

Update the success signal to show: one `/tc` command, a mode choice, source approval in interactive mode, auto creation in auto mode, a generated dashboard, visible notes, and a mandatory section close gate.

#### UX Change 2: CAP-1 — Only `tc` Is Public

**OLD (excerpt):**

```markdown
- **CAP-1**
  - **intent:** System consolidates all user-facing interactions behind a single conversational `/tc` entrypoint that intelligently routes intent across onboarding, course creation, and lesson delivery without exposing multiple administrative commands.
  - **success:** In an uninitialized workspace, `/tc` launches interactive setup; when given a topic or books, `/tc` drives the curriculum pipeline; on an active course, `/tc` seamlessly advances or resumes the active lesson.
```

**NEW (excerpt):**

```markdown
- **CAP-1**
  - **intent:** System exposes exactly one public skill, `/tc`. Every other capability is internal and callable only by `/tc` or `tc.py dispatch`.
  - **success:** `skills/` contains only `tc`; `skills-lock.json` exports only `tc`; every lifecycle state is reached through `/tc`; no internal engine is presented as a public command.
```

#### UX Change 3: CAP-2 — Gates Only in Interactive; Section Close in Both

**OLD (excerpt):**

```markdown
- **CAP-2**
  - **intent:** System maintains step-by-step interactive checkpoints after research, material acquisition, and course creation, asking the user for confirmation before proceeding to the next phase.
  - **success:** When gold-standard textbooks cannot be openly harvested, `/tc` pauses at an acquisition gate asking the user to supply the file or proceed with open docs; after course synthesis, `/tc` presents the roadmap and awaits user approval before launching Lesson 1.
```

**NEW (excerpt):**

```markdown
- **CAP-2**
  - **intent:** System offers interactive creation checkpoints (source proposal, missing material, Gate 2 blueprint) and auto creation with agent decisions. Teaching is identical in both modes and always ends with a mandatory Section Close Gate.
  - **success:** Interactive mode pauses for source approval and blueprint approval. Auto mode runs creation without approval and logs decisions. Both modes compile notes and require close approval before the next section.
```

#### UX Change 4: CAP-4 — Root `_tc/`, Visible Notes

**OLD (excerpt):**

```markdown
- **CAP-4**
  - **intent:** System encapsulates all internal machine files (`source-map.toml`, `coverage-ledger.md`, `course.toml`, `memlog.md`, `session.jsonl`) inside a hidden `courses/<slug>/.tc/` directory, surfacing only clean human-facing study files (`overview.md` and `notes/`) in the course root.
  - **success:** The user's course folder displays only `overview.md` and compiled textbook notes, while all runtime engines, validators, and audit ledgers operate with zero degradation against the encapsulated `.tc/` directory.
```

**NEW (excerpt):**

```markdown
- **CAP-4**
  - **intent:** System encapsulates research, sources, course state, decisions, memlogs, profile, and roadmap in root `_tc/`; the only visible study material is `courses/<slug>/notes/chapter-XX.md`.
  - **success:** A new workspace contains no `.tc/`, root `research/`, `sources/`, or `plan/sources/`; the visible course folder contains only `notes/`; every engine reads and writes the canonical `_tc/` paths.
```

#### UX Change 5: CAP-6 — Close-Aware Fork

**OLD (excerpt):**

```markdown
- **CAP-6**
  - **intent:** System preserves the standardized 4-Option Action Fork at the conclusion of every instructional turn...
```

**NEW (excerpt):**

```markdown
- **CAP-6**
  - **intent:** System preserves the standardized 4-Option Action Fork... When the section’s final concept is mastered, option `[1]` opens the Section Close Gate instead of advancing immediately.
  - **success:** Every turn ends with the fork; `[1]` on a completed section shows “Review Notes and Close Section”; no next section starts before approval.
```

#### UX Change 6: Add CAP-7–CAP-10

```markdown
- **CAP-7 — Execution Mode Selection & Auto Creation**
  - **intent:** Intake captures `interactive` or `auto`; auto runs all creation steps without approval while the agent decides and logs.
  - **success:** Auto creates research, sources, conversion, debate, roadmap, blueprint, and section plans without pausing; every decision appears in the memlog/debate log; teaching still requires close approval.

- **CAP-8 — Interactive Source Proposal & Research Loop**
  - **intent:** After research, present the best sources from books, papers, official docs, GitHub, Reddit, Quora, and general web; accept approval, more research, add/remove, or stop.
  - **success:** `_tc/research/<slug>/source-proposal.md` lists sources with rationale and availability; “more research” produces an updated proposal; approval fetches all selected sources.

- **CAP-9 — Section Close Gate & Ephemeral Session**
  - **intent:** After the final concept, compile visible chapter notes, show the close gate, and require approval in every mode.
  - **success:** The section stays `review` until approval; on approval the visible notes exist, memlogs are appended, and the section transcript is deleted.

- **CAP-10 — Generated Status Dashboard**
  - **intent:** Generate a self-contained, interactive HTML dashboard on init and after state changes, reading `_tc/`.
  - **success:** `status-board/index.html` opens from `file://`, shows the roadmap/active pointer/sources/coverage/memlogs/gates, and updates after regeneration with no network access.
```

#### UX Change 7: Constraints and Tests

**OLD (excerpt):**

```markdown
- **Zero Breaking Changes**: All 296 unit/integration tests must continue passing; backwards compatibility maintained across legacy paths and commands.
```

**NEW (excerpt):**

```markdown
- **Zero Silent Regressions**: The 326-test baseline must pass or be intentionally updated for the new storage contract. Legacy paths may be read during migration but must not be written. New vision-contract tests must cover all 12 points.
```

#### UX Change 8: Rewrite `workspace-hierarchy.md`

Replace the entire two-tier `.tc/` document with the canonical tree and rules from **§4.1**. The new document must state:

- root `_tc/` is authoritative;
- visible study material is only `courses/<slug>/notes/`;
- `portfolio/` is proof-of-work;
- `status-board/` is an interface;
- scoped memlogs;
- per-section sessions and deletion on close;
- migration and legacy read-only fallback.

#### UX Change 9: Rewrite `interaction-flowchart.md`

Replace the current interactive-only flowchart with:

1. `/tc` intake → topic + preferences + mode.
2. Research → source proposal.
3. Interactive branch: approve / more research / add-remove / stop.
4. Auto branch: agent selects and logs.
5. Fetch all → convert → conversion ledger → 4-hat debate.
6. Roadmap + blueprint.
7. Interactive Gate 2 (artifact in `_tc/`) or auto decision.
8. Section plans with teaching/coverage/verification.
9. Teaching turns with the 4-option fork.
10. Mandatory Section Close Gate in both modes.
11. Notes written; memlogs appended; section transcript deleted.
12. Dashboard regenerated after state changes.

#### UX Change 10: Update `spec-multi-source-compiler` and Companions

- `spec-multi-source-compiler.md`: change source paths to `_tc/research/<slug>/sources/`; add conversion coverage and 4-hat debate; update the success signal.
- `source-map-schema.md`: update map location and `raw_path` examples; add the conversion ledger schema reference.
- `architecture-diagrams.md`: show the canonical paths, conversion coverage, debate, blueprint approval, section plans, and close gate.
- `vocabulary-contract.md`: update `session.jsonl` and `memlog.md` paths; note that section close deletes the transcript but preserves memlog summaries.

---

### 4.6 Ticket and Story Changes

#### Epic Changes

| Epic | Change |
|---|---|
| 1 — Runtime Engine | Keep done; update path fixtures and manifest tests. |
| 2 — Onboarding & Lifecycle | Reopen bootstrapper story; remove duplicate roots; create canonical `_tc/` tree; trigger dashboard. |
| 3 — Curriculum Creation | Reopen course-builder story; blueprint before section plans; section-plan content contract. |
| 4 — Instruction Delivery | Reopen notes-compiler story; visible notes; close gate; session scrub. |
| 5 — Assessment & Verification | Reopen practical/diagnostic stories; remove whole-course completion on PASS. |
| 6 — Faculty/Roadmap/Memlog | Reopen layout and memlog stories; root `_tc/`; scoped memlogs. |
| 7 — Research & Dialectic | Reopen research story; 4-hat debate; decision log. |
| 8 — Pedagogical Brainstorm/Practicals | Reopen practical story; close-gate semantics; section verification. |
| 9 — Unified Dispatcher | Reopen dispatcher/session stories; Gate 1 dead end; mode; public surface. |
| 10 — Sovereign Harvester/RAG | Reopen harvester/indexer/catalog stories; `_tc/research` paths; source proposal/fetch; conversion coverage. |
| 11 — Multi-Source Compiler | Reopen extractor/toc/coverage/source-map stories; zero-loss conversion; no fake pointers. |
| 12 — Consumer UX & Unified `/tc` | Reopen all stories; rewrite CAP-4; add CAP-7–CAP-10; add integration stories. |

#### Stories to Add or Rewrite

1. `story-single-public-tc-export-and-internal-skill-boundary`
   - Only `skills/tc/`; internal packages under `_tc/skills/`; `skills-lock.json` exports only `tc`.
2. `story-root-tc-storage-migration-and-scoped-memlogs`
   - Canonical tree; migration tool; no duplicate roots; memlogs at all scopes.
3. `story-intake-mode-selection-and-auto-creation`
   - Topic + preferences + mode; auto creation; decision logging.
4. `story-interactive-source-approval-loop`
   - Source proposal; approve/more/remove/stop; fetch-all; missing-material fallback.
5. `story-zero-loss-conversion-and-coverage-ledger`
   - Type-specific extraction; conversion ledger; 100% text coverage; no silent omissions.
6. `story-four-hat-research-debate`
   - Four voting hats; challenge rounds; `debate.jsonl`; readable summary.
7. `story-blueprint-gate-and-section-plans`
   - Blueprint artifact before section plans; teaching/coverage/verification in every plan.
8. `story-section-close-gate-and-session-scrub`
   - Mandatory close in both modes; visible notes; memlog entries; transcript deletion.
9. `story-status-dashboard-generator`
   - `status-board/index.html`; snapshot; self-contained; regenerated on state changes.
10. `story-vision-contract-e2e-suite`
    - 12-point acceptance matrix; storage/public-surface/mode/close/dashboard tests.

#### Resequencing

1. Storage contract + migration + scoped memlogs.
2. Single public surface + dispatcher dead-end fix.
3. Mode selection + source approval + auto creation.
4. Conversion coverage + 4-hat debate.
5. Blueprint + section plans + Gate 2 ordering.
6. Teaching close + notes + session scrub.
7. Dashboard generator.
8. Vision-contract E2E suite and full regression.

---

### 4.7 Test and Verification Changes

Add or update these tests:

| Test file | Purpose |
|---|---|
| `tests/test_vision_contract.py` | One test per learner point; asserts observable runtime behavior, not documentation. |
| `tests/test_storage_contract.py` | No `.tc/`, root `research/`, `sources/`, or `plan/sources/`; canonical `_tc/` writes; notes visible. |
| `tests/test_public_surface.py` | Only `skills/tc/` exists; `skills-lock.json` exports only `tc`; internal packages are not public. |
| `tests/test_dispatcher_continuation.py` | `proceed_open` calls the builder and returns the next state, not a dead end. |
| `tests/test_mode_selection.py` | Intake persists `interactive`/`auto`; auto bypasses creation gates; teaching behavior is identical. |
| `tests/test_source_approval_loop.py` | Source proposal, approve, more research, add/remove, stop, fetch-all, missing material. |
| `tests/test_conversion_coverage.py` | Conversion ledger records input/output; 100% text coverage; omissions require approval; no silent loss. |
| `tests/test_section_close_gate.py` | Close gate in both modes; no advance before approval; notes visible; transcript deleted after approval. |
| `tests/test_status_dashboard.py` | Dashboard generated at init and after state changes; self-contained; contains active pointer, sources, coverage, memlogs, gates. |
| `tests/test_memlog_scopes.py` | Workspace/research/course/chapter/section memlogs; milestone roll-up; no duplicate turn spam. |
| `tests/test_notes_compiler.py` | Update expected path to `courses/<slug>/notes/chapter-XX.md`; assert visible file, not `.tc/notes`. |
| `tests/test_clean_workspace.py` | Replace `.tc/` expectations with root `_tc/` and visible notes. |
| `tests/test_unified_tc.py` | Replace the dead-end assertion with continuation and mode coverage. |
| `tests/test_interactive_gates.py` | Add mode-aware gate behavior and close gate. |
| `tests/test_auditor.py` | Coverage fails on zero sources; conversion coverage is separate from curriculum coverage. |

**Verification commands:**

```bash
python -m pytest -q
python -m pytest tests/test_vision_contract.py -q
python _tc/scripts/tc.py dispatch --input "<topic>" --workspace <tmp> --json
python _tc/scripts/tc.py dispatch --input "1" --workspace <tmp> --json
```

The first two must pass. The last two must not reproduce the old dead end: after `proceed_open`, a course/blueprint must exist and the next state must be Gate 2 or teaching, not a new acquisition gate.

---

### 4.8 Dashboard Specification

**Output:** `status-board/index.html` plus `_tc/status/state.json`.

**Generation triggers:** `/tc` initialization; course/research state changes; gate changes; notes compilation; section close; migration; any memlog append that changes status.

**Sections:**

1. **Overview:** workspace name, active mode, active course, progress ring.
2. **Roadmap:** courses, chapters, sections, status badges, prerequisites.
3. **Active pointer:** course/chapter/section/concept, next action, unresolved gate.
4. **Research:** sources by type, source proposal status, fetch status, conversion coverage, curriculum coverage.
5. **Debate:** 4-hat summary, open disagreements, decision count.
6. **Memory:** memlog timeline with filters for decision/change/context/learning/approval/milestone.
7. **Files:** links/paths to `_tc` artifacts, notes, and the active plan.
8. **Health:** missing sources, failed conversions, stale dashboard, unresolved close gates.

**Interaction:** filter by course/chapter/status/hat; expand evidence; search memlog; toggle raw JSON; responsive tables; accessible labels; reduced-motion support; no-JS fallback that still shows the snapshot.

**Constraints:** no CDN, no external font, no network request, no server, no arbitrary browser filesystem access. The generator reads `_tc/` locally and embeds the snapshot.

---

## Section 5: Implementation Handoff

### 5.1 Scope Classification and Routing

**Scope:** **Major** — fundamental replan.

**Routing:**

1. **Product Manager / Solution Architect** — approve the PRD, architecture, both spec updates, and the root `_tc/` contract.
2. **Product Owner / `bmad-ticket`** — reopen the contradicted epics/stories, add the new stories, update `tickets.toml`, and resequence.
3. **Developer agent** — implement the approved stories; do not start with runtime edits until the artifact and ticket changes are approved.
4. **Reviewer** — verify the 12-point contract against runtime evidence, not static badges.

### 5.2 Deliverables

- Corrected Sprint Change Proposal (this file).
- PRD edits in §4.3.
- Architecture edits in §4.4.
- UX/spec edits in §4.5.
- Ticket replan in §4.6.
- Test plan in §4.7.
- Dashboard specification in §4.8.
- No runtime code changes in this workflow.

### 5.3 Success Criteria

These are intentionally unchecked. They become checked only when runtime evidence and tests exist.

- [ ] **1. Single public surface:** `skills/` contains only `tc`; `skills-lock.json` exports only `tc`; no internal capability is a public command; `/tc` calls `tc.py dispatch`.
- [ ] **2. Root `_tc/` storage:** research, sources, course state, decisions, profile, roadmap, and memlogs live under `_tc/`; only `courses/<slug>/notes/` is visible study material; no `.tc/`, root `research/`, `sources/`, or `plan/sources/` writes.
- [ ] **3. Scoped memlogs:** workspace, research, course, chapter, and section memlogs exist and receive the right events; milestone roll-up works.
- [ ] **4. Intake and mode:** `/tc` asks topic, preferences, and `interactive`/`auto`; the mode is persisted and used.
- [ ] **5. Interactive source approval:** source proposal lists books, papers, docs, GitHub, Reddit/Quora/general web; approve/more/remove/stop works; approval fetches all selected sources.
- [ ] **6. Auto creation:** auto mode runs research, fetch, conversion, debate, roadmap, blueprint, and section plans without approval; every decision is logged.
- [ ] **7. Missing material:** interactive asks the user to proceed or supply; auto records the gap and proceeds with the best available material.
- [ ] **8. Zero-loss conversion:** every source has a conversion ledger; text coverage is 100% or explicitly approved; no silent omission.
- [ ] **9. Four-hat debate:** every source/topic/roadmap decision has a debate record; four voting hats; challenge rounds; readable summary.
- [ ] **10. Roadmap and section plans:** blueprint exists before section plans; every plan contains teaching, source coverage with line spans, and verification.
- [ ] **11. Teaching and close:** `/tc` teaches directly; conversation is stored per section under `_tc/`; visible chapter notes are compiled; section close requires approval in both modes; transcript is deleted after approval.
- [ ] **12. Dashboard:** `status-board/index.html` is generated on init and state changes, reads `_tc/`, is interactive and self-contained, and shows roadmap, active pointer, sources, coverage, memlogs, gates, and next action.
- [ ] **13. Regression:** the 326-test baseline passes or is intentionally updated; the new vision-contract suite passes; no test asserts a missing behavior as success.

### 5.4 Sequencing and Timeline

| Phase | Work | Gate |
|---|---|---|
| 0 | Approve this proposal and the root `_tc/` contract | User approval |
| 1 | Update PRD, architecture, both specs, UX companions, initiative, product brief | PM/Architect approval |
| 2 | Reopen epics/stories; add new stories; update `tickets.toml` | PO / `bmad-ticket` |
| 3 | Implement storage migration, scoped memlogs, and canonical paths | Storage-contract tests |
| 4 | Implement single public surface and dispatcher continuation | Public-surface + dispatcher tests |
| 5 | Implement modes, source approval, auto creation, fetch-all | Mode/source tests |
| 6 | Implement conversion coverage, 4-hat debate, blueprint, section plans | Compiler/research tests |
| 7 | Implement close gate, visible notes, session scrub | Teaching-contract tests |
| 8 | Implement dashboard generator | Dashboard tests |
| 9 | Run vision-contract E2E and full regression | 12/12 evidence |

**Estimate:** 15–25 engineer-days for one developer; 3–5 sprints for a small team; 3–4 weeks calendar impact. The estimate assumes the existing compiler/harvester primitives are reused.

### 5.5 Explicit Exclusions

- No runtime code was modified by this workflow.
- No tests were modified by this workflow.
- No skill packages were moved by this workflow.
- No tickets or epics were reopened by this workflow.
- No planning artifact other than this proposal was edited.
- The runtime implementation begins only after explicit approval and the ticket replan.

### 5.6 Handoff Responsibilities

| Role | Responsibility |
|---|---|
| User | Approve the proposal and the root `_tc/` contract; resolve any remaining product choices. |
| Product Manager / Architect | Apply the PRD, architecture, spec, and UX edits; confirm the storage and mode contracts. |
| Product Owner / `bmad-ticket` | Reopen contradicted epics, add stories, update dependencies, and resequence. |
| Developer agent | Implement the approved stories; keep the canonical paths; add tests before claiming completion. |
| Reviewer | Verify each of the 12 points against runtime evidence and the vision-contract suite. |

---

## Appendix A: Learner Vision Ledger — 12 Verbatim Points

These quotes are preserved exactly from `flow.html` / `actual-flow.html`, including spelling and punctuation. They are the acceptance contract for this change.

1. **Point 01 — Single public entrypoint** — **Not enforced**  
   > "1. only tc skill should be exported out. no other skill should be accessible. All are internal and only tc can call those."

2. **Point 02 — Clean canvas and granular memory** — **Violated**  
   > "2. all study material and research and docs stay in _tc folder. just notes stays outside. Each and every decision and each and every change that i ask or how im learning and everything should be stored in memlog of that specific folder or section or chapter based on what im doing."

3. **Point 03 — Intake and execution mode** — **Absent**  
   > "3. first tc asks me what i wnt to learn. then it asks some preference questions. We should also give onemore option that should we go straight to teaching without involving user at all. or we can ask each decision interactive way to create a course andd include user in every stage."

4. **Point 04 — Interactive research and source approval** — **Partial**  
   > "4. After asking all preferences.. if user chooses interactive, research agent will do all analysis and ask user these are the materials we need and these are the best material out there. this research agent should suggest from github, research papers, books, official docs etc etc. it should look at all the places on internet like reddit and quora and general articles to find the best courses or best books or best any form of material. then take approval from user that if the sources mentioned are ok or not. Then based on user input, do more research or stop research and go to next step."

5. **Point 05 — Unattended auto mode** — **Absent**  
   > "5. But if user selects no interactive mode in previous question, just go ahead with all steps and dont ask for approval thats it. but still all steps should run and agent will take decisions automatically."

6. **Point 06 — Fetch resources and missing-material fallback** — **Partial / fragmented**  
   > "6. Then after research step is done, research agent should fetch all docs and resources from internet and place it in research folder based on course.if agent is not able to find any material, let user decide its ok or user will get the material himself and place it in researhc folder."

7. **Point 07 — Verbatim Markdown, coverage, and 4-hat debate** — **Partial / unverified**  
   > "7. after all this.. agent shoudl create material into md file. resource can be of any type, it should convert that all to md without any text removed. use code or use any library and decide based on type of material.. agent should also verify if all material is covered or not. that should also be a very good research. I think research agents debate internally and think with 4 hats. but that is not working as exptected i think. they should all debate each and every decision and it should be a intense ddiscussion to do research. each point will be critically analyzed."

8. **Point 08 — Course, roadmap, and indexing** — **Partial**  
   > "8. after all this research and material collection. create course will do its thing. create roadmap and create indexxing and all complexx things and create a course out of material collected. it will skim through each topic and do a very thorough well thought course/roadmap/courses. it will also make it easy for teach agent to read the material easily."

9. **Point 09 — Roadmap approval and section plans** — **Partial**  
   > "9. If user selects interactive, explain all roadmap and course structure to user and ask for review of artifact thats in _tc folder somewhere. And then at the final approval. start creating sections etc etc and how to teach that what to cover and how to verify user knowledge etc etc will all be in section plan."

10. **Point 10 — Teach, log, compile notes, delete history** — **Partial / broken path**  
    > "10. then tc should directly teach and store all conversation in _tc folder somewhere and when that section is completed, it writes notes and deletes conversation history from _tc."

11. **Point 11 — Continuous memory and section sign-off** — **Absent**  
    > "11. everything should be tracked and every context and decision taken in this journey should be considered for future conversation or learn or anything. at the end it should also ask for approval to closee the section whether they chose interactive or not. teach wont cchange based on interactive or not. course creatiion and all do."

12. **Point 12 — Interactive status dashboard** — **Absent**  
    > "12. There should also be a dashboard created. a html file that should be coming when a skill is initiated first and when folder structure is formed. it shoudl have a interactive way of seeing where we are. the status will all be in this files maybe toml, json i dont know. but this html file or a folder all together called status board should read all files from _tc and show it in beautiful way."

---

## Appendix B: Evidence and Reproductions

### B.1 Test Run

```text
python -m pytest -q
........................................................................ [ 22%]
........................................................................ [ 44%]
........................................................................ [ 66%]
........................................................................ [ 88%]
......................................                                   [100%]
326 passed in 291.88s (0:04:51)
```

The suite does not cover auto mode, dashboard generation, section close, session deletion, source approval, or the single-public-surface invariant. `tests/test_unified_tc.py` currently asserts the dead-end `state == "creating_course"` response.

### B.2 Topic-Only Dispatch Reproduction

```text
dispatch("Distributed Storage")
# → state: acquisition_gate, slug: distributed-storage

dispatch("1")
# → state: creating_course, action: proceed_open
# → courses/ is empty

dispatch("1")
# → state: acquisition_gate, slug: "1"
# → research/1/ is created
```

### B.3 Notes Path Reproduction

```text
compile_notes(...)
# → notes_file:       .../.tc/plans/.../notes.md
# → chapter_notes_file: .../.tc/notes/chapter-01.md
# → visible courses/<slug>/notes/chapter-01.md: unchanged scaffold
```

### B.4 Public Surface Reproduction

```text
skills/
  tc/
  tc-create/
  tc-index/
  tc-init/
  tc-migrate/
  tc-practicals/
  tc-redirect-course/
  tc-research/
  tc-roadmap/
  tc-teach/
  tc-test-me/
  tc-verify-course/

skills-lock.json: no "tc" or "tc-*" entry
```

### B.5 Artifact Counts

- PRD: ends at `FR-45`; `FR-46`–`FR-50` absent.
- UX spec: ends at `CAP-6`; `CAP-7`–`CAP-10` absent.
- `flow.html`: static “Fully Aligned” badges, not computed state.
- `tests/`: 326 passing tests; no coverage for the missing paths.

---

## Appendix C: Revision History

| Date | Revision | Change |
|---|---|---|
| 2026-11-05 | v1 | Initial proposal (superseded). |
| 2026-11-05 | v2 | Corrected scope to Major; removed false `[x]` success criteria; added the 12-point evidence matrix; adopted root `_tc/` + visible notes; added single-public-surface, mode, zero-loss conversion, section close, and dashboard requirements; added ticket and test replan. |
| 2026-11-06 | v3 | Approved by the user. Finalized status and issued the Major-scope handoff. |

---

## Approval Record

- **Approved by:** User
- **Approved on:** 2026-11-06
- **Workflow:** `bmad-correct-course` (batch review)
- **Scope classification:** **Major** — fundamental replan
- **Routing:** Product Manager / Solution Architect → Product Owner (`bmad-ticket`) → Developer agent → Reviewer
- **Implementation status:** Not started. No runtime, test, ticket, or planning artifact may change until the receiving lane accepts this proposal.
- **Success gate:** All 13 criteria in §5.3 must be evidenced by runtime behavior and tests; documentation claims are not evidence.
