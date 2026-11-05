# TextCourses Course-Correction & Improvement Plan

> **Status**: 🟡 **Draft / Planning — Execution Paused**  
> **Last Updated**: 2026-11-01  
> **Initiative**: `initiative-textcourses`  
> **Next Step**: Awaiting additional issues and requirements from user before implementation.

---

## Part 1: Approved Improvements (Ready for Implementation)

### 1.1 Intake Protocol Streamlining (Drop Explanation Density)
- **Problem**: In `tc-init`, Stage 5 asks *"How detailed would you like each lesson to be?"* with word counts (`~60–100` vs `~150–200` vs `~250–350` words). The user hasn't taken a lesson yet, causing cognitive fatigue and abstract meta-guessing.
- **Root Cause & Redundancy**: Domain experience level (Beginner vs Familiar vs Practitioner) already determines pedagogical depth. `bootstrapper.py` already derives density from experience level.
- **Fix**:
  - Remove Stage 5 (Explanation Density) from [`skills/tc-init/SKILL.md`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/skills/tc-init/SKILL.md).
  - Update [`_tc/INTERACTION_STANDARDS.md`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/INTERACTION_STANDARDS.md) to codify the clean 5-stage intake sequence.
  - Automatically infer density (`beginner` $\rightarrow$ `balanced`, `practitioner` $\rightarrow$ `deep_dive`) in [`_tc/scripts/bootstrapper.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/bootstrapper.py).

### 1.2 Master Teacher Archetype Sharpening (Remove Semantic Blur)
- **Problem**: Hypatia (*"step-by-step from first principles without skipping anything"*) and Turing (*"logical, hands-on, focuses on system internals, how things work under the hood"*) felt identical to technical learners.
- **Fix**: Redefine the personas into 3 mutually exclusive, crisp pedagogical pillars:
  1. **[1] Feynman (Intuitive / Analogy-First) ⚡**: Everyday metaphors, mental models, zero unexplained jargon before intuition clicks.
  2. **[2] Turing (Case-First / Applied Builder) 💻**: Hands-on, practical execution: real-world case studies, runnable snippets, concrete deliverables, and failure modes.
  3. **[3] Hypatia (First-Principles / Deep Rigor) 🦉**: Step-by-step logical derivation, core axioms, formal proofs, and architectural design trade-offs.
  4. **[4] Other (write-in)**

### 1.3 Multi-Select & Hybrid Teacher Combinations (`1, 2`, `1, 3`, etc.)
- **Problem**: Learners cannot pick dual qualities (e.g. Feynman intuition + Turing code-first). Entering `"1, 2"` or `"feynman, turing"` previously broke in `bootstrapper.py` due to an exclusive `if/elif` chain and string matching failure.
- **Fix**:
  - Update `bootstrapper.py` to parse comma/plus-separated lists of numbers or names.
  - Dynamically compose style keys and pedagogical directives:
    - `1, 2` $\rightarrow$ **The Intuitive Builder** (`analogy` + `code_first`)
    - `1, 3` $\rightarrow$ **The Conceptual Master** (`analogy` + `math`)
    - `2, 3` $\rightarrow$ **The Systems Architect** (`code_first` + `math`)
    - `1, 2, 3` $\rightarrow$ **The Polymath** (`analogy` + `code_first` + `math`)

### 1.4 Remove Legacy Involuntary Overrides
- **Problem**: `course_builder.py:185` and `teach_engine.py:172` forcibly overwrote `feynman` to `hypatia` whenever the learner was marked beginner.
- **Fix**: Remove the forced override so learner preferences are strictly respected.

### 1.5 Lifecycle & Next-Action Flow Correction (`/tc-init` -> `/tc-research` -> `/tc-create`)
- **Problem**: After `/tc-init`, the prompt and `bootstrapper.py scan` directly suggest `/tc-create "<subject>"`, bypassing the pre-course research phase entirely.
- **Why This Is Broken**:
  - FR-30 and the PRD explicitly define **Pre-Course Research Primacy**: Marie Curie (`tc-research`) scouts authoritative documentation, benchmarks against canonical syllabi, runs 5-Hat critique, and writes `research/<slug>/dossier.md` *before* course scaffolding.
  - Suggesting `/tc-create` directly bypasses the visible research phase (`research/<slug>/dossier.md`, `five-hats-critique.md`, `sources.json`) and prevents the user from inspecting sources or using `/tc-index` for custom PDFs/books.
  - While `course_builder.py` has a background scout fallback, the canonical user journey is research first.
- **Fix**:
  - Update `VALID_RECOMMENDATIONS` in `bootstrapper.py` to include `"/tc-research"`.
  - Update `bootstrapper.py scan`:
    - If neither `courses/` nor `research/` exists $\rightarrow$ recommend `/tc-research "<subject>"`.
    - If `research/<slug>/dossier.md` exists but no `courses/` $\rightarrow$ recommend `/tc-create "<slug>"`.
  - Update `skills/tc-init/SKILL.md` concluding next-action prompt:
    - Primary recommendation: `/tc-research "<subject>"` (5-Hat deep research & syllabus benchmarking).
    - Alternative fast-track: `/tc-create "<subject>"` (jump straight into course scaffolding with background research).

### 1.6 Deep Domain Goal Elicitation (In-Depth Topic Description in Intake)
- **Problem**: In `tc-init`, Stage 2 asks a terse one-liner: *"What specific subject, skill, or topic do you want to learn?"*, prompting superficial answers (e.g. "rust" or "distributed systems").
- **Why This Hurts Research & Curriculum Quality**:
  - `tc-research` (Marie Curie) and `tc-create` (Daedalus & Triad) generate generic textbook syllabi when deprived of rich context on specific focus areas, real-world problems to solve, tools/frameworks, and end goals.
  - `bootstrapper.py set-preferences` didn't store `--subject` or `--goals` into `profile/preferences.md` frontmatter, losing learner intent.
- **Fix**:
  - Expand Stage 2 prompt in [`skills/tc-init/SKILL.md`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/skills/tc-init/SKILL.md) to explicitly prompt for an in-depth description with guidance:
    - Core topic & domain
    - Specific focus areas, tools, or frameworks
    - Concrete end goals or target project
    - Concepts to emphasize or skip
  - Add `--subject` and `--goals` parameters to `bootstrapper.py set-preferences`.
  - Persist `target_subject` and `learning_goals` in `profile/preferences.md` (both frontmatter and a dedicated `## Target Domain & Learning Goals` section).
  - Allow `tc-research` and `tc-create` to auto-read domain intent from `profile/preferences.md`.

### 1.7 Memory, Session Continuity & Decision Storage Integrity Audit
- **Problem & Identified Gaps**:
  1. **Teaching Dialogue Amnesia (`skills/tc-teach` -> `session.jsonl`)**: While `teach_engine.py` provides `log-turn`, `skills/tc-teach/SKILL.md` never commands the agent to invoke `log-turn` during interactive exchanges (re-explanations, student inquiries, dialogue). Only concept advancement (`[1]`) was logged, leaving the conversational exchange unrecorded.
  2. **Global Journey Memlog Disconnect (`profile/memlog.md`)**: `profile/memlog.md` is initialized on `/tc-init`, but no scripts (`course_builder.py`, `diagnostic_tester.py`, `practical_evaluator.py`) write macro milestones (course creation, course graduation, track completion) to it.
  3. **Capstone Review Outcome Dropped from Memlog (`tc-practicals`)**: When `practical_evaluator.py` approves a project in `portfolio/`, it updates `course.toml` and writes `review-report.md`, but fails to mirror the milestone into `courses/<slug>/memlog.md` and `profile/memlog.md`.
  4. **Trailing Context Incompleteness on Session Recovery**: `teach_engine.py session` loads the last 5 events from `session.jsonl`, but did not return trailing entries from `courses/<slug>/memlog.md` (which holds misconceptions and question tags).
- **Fix**:
  - Update [`skills/tc-teach/SKILL.md`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/skills/tc-teach/SKILL.md) to mandate calling `uv run _tc/scripts/teach_engine.py log-turn` after each conversational turn (dialogue, re-explanation, custom inquiry).
  - Update [`_tc/scripts/teach_engine.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/teach_engine.py) `get_teaching_session` to return both `recent_session_history` (`session.jsonl`) and `recent_memlog_entries` (`memlog.md`).
  - Update [`_tc/scripts/course_builder.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/course_builder.py) to log course inception to `profile/memlog.md`.
  - Update [`_tc/scripts/practical_evaluator.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/practical_evaluator.py) to log capstone review approval (`- (milestone) practical:capstone_passed:project-XX`) to both `courses/<slug>/memlog.md` and `profile/memlog.md`.
  - Update [`_tc/scripts/diagnostic_tester.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/diagnostic_tester.py) to log course completion milestones to `profile/memlog.md`.

### 1.8 Internalization of Roadmap Engine & Scope-Aware Auto-Decomposition
- **Problem**:
  1. `tc-roadmap` currently exists as an awkward standalone user command. Learners are confused about whether to run `/tc-init`, `/tc-roadmap`, or `/tc-create`.
  2. A multi-course roadmap is not always necessary. If a learner enters a focused topic (e.g. "Raft Consensus", "Rust Async Runtime"), forcing a multi-course sequence creates artificial bloat.
  3. Too many internal skills (`tc-roadmap`, `tc-verify-course`, `tc-redirect-course`, `tc-migrate`) are exposed as public slash commands, cluttering the user interface.
- **Fix**:
  1. **Strict Public vs Internal Skill Taxonomy**:
     - **Public Learner Skills (The Core Verbs)**:
       - `/tc-init` (Onboard learner, configure profile & evaluate scope)
       - `/tc-research` (5-Hat domain research & syllabus benchmarking)
       - `/tc-index` (Ingest custom textbooks, PDFs, and code repositories)
       - `/tc-create` (Scaffold course via Triad Consensus)
       - `/tc-teach` (Active conversational lesson delivery)
       - `/tc-test-me` (Diagnostic placement & active recall testing)
       - `/tc-practicals` (Applied capstone build & 4-lens review)
     - **Internal Substrate Engines (Never called directly by users)**:
       - `tc-roadmap` $\rightarrow$ Internal decomposition engine (invoked automatically during `tc-init` for broad topics).
       - `tc-verify-course` $\rightarrow$ Internal logic & DAG auditor (invoked internally by `course_builder.py`).
       - `tc-redirect-course` $\rightarrow$ Internal drift manager (triggered when sources change).
       - `tc-migrate` $\rightarrow$ Internal schema migrator.
  2. **Scope-Aware Automatic Decomposition in `/tc-init`**:
     - When the learner describes their domain in `tc-init` Stage 2:
       - **Macro / Broad Discipline** (e.g. "Software Architecture", "Machine Learning Systems", "Distributed Systems"):
         - The system automatically triggers the Cartographer (Aristotle) to decompose the domain into a structured sequence of 3–5 focused courses in `roadmap/roadmap.toml`.
         - Presents the synthesized multi-course roadmap to the learner and recommends researching Course 1: `/tc-research "<course-1-slug>"`.
       - **Micro / Focused Topic** (e.g. "Raft Consensus", "LSM-Trees", "Git Internals"):
         - Recognizes the topic as single-course scope, skips `roadmap.toml`, and proceeds directly to `/tc-research "<topic-slug>"`.

### 1.9 Universal Pedagogical Decoupling (Anti-Software Bias & Domain Generalization)
- **Problem**:
  1. **Roadmap Granularity Confusion**: A roadmap should decompose a broad discipline into **independent, standalone subjects** with their own distinct literature, canonical textbooks, and independent study paths (e.g. *Computer Networking* vs *Storage Engines* vs *Distributed Consensus*; or *Anatomy* vs *Physiology* vs *Pharmacology*). It must NOT break a single topic into artificial chapters or sub-topics.
  2. **Domain-Specific Hardcoding in Practical Evaluator**:
     - `practical_evaluator.py:510` explicitly checks for code syntax:
       `any(k in text for k in ["def ", "class ", "fn ", "function ", "struct ", "impl ", "let ", "var ", "const ", "return "])`
       Non-software learners (law, medicine, finance, humanities, visual design) fail evaluation and receive penalties for "Missing concrete code implementation"!
     - Deliverable templates hardcode `src/` and `tests/` code directory structures.
  3. **Domain-Specific Phrasing in `tc-teach` and Style Directives**:
     - `skills/tc-teach/SKILL.md` hardcodes `Code Walkthrough / Table`.
     - `bootstrapper.py` style directives define `code_first` exclusively in terms of "practical code implementations".
- **Fix**:
  1. **Canonical Independent-Subject Roadmaps**:
     - Codify that roadmap decomposition separates distinct, independently learnable subjects with sovereign reference literature, not subtopics.
  2. **Domain-Agnostic Practical Evaluation**:
     - In `practical_evaluator.py`, remove the programming keyword check. Evaluate submissions against domain-appropriate artifacts (legal case briefs, clinical differential diagnoses, financial valuations, architectural diagrams, essays, or code).
     - Standardize deliverable folders to `deliverables/` or `solution/` alongside optional `src/`.
  3. **Universalize Instructional Directives & Style Labels**:
     - In `skills/tc-teach/SKILL.md`, generalize:
       `- **Concrete Application / Worked Example / Case Study / Code**: Practical implementation, clinical scenario, legal analysis, or code walkthrough.`
     - In `bootstrapper.py`, update `code_first` / `applied_builder` to **Case-First & Applied Builder** (grounding explanations in case studies, real-world scenarios, worked analyses, or working code).
     - Reframe Turing / Builder persona menu so it resonates universally with engineers, lawyers, doctors, designers, and scientists alike:
       `[2] Turing (Case-First / Applied Builder) 💻 — Hands-on, practical execution: real-world case studies, runnable snippets, concrete deliverables, and failure modes.`

### 1.10 RAG Grounding in Teaching & Automated Hallucination Verification
- **Problem**:
  1. **Teaching Without Source Grounding**: While `_tc/scripts/indexer.py` builds SQLite FTS5 RAG databases (`rag-db/index.db`) and `tc-create` queries it, **`tc-teach` never touches RAG**! `teach_engine.py` delivers single-concept lessons purely from LLM weights without pulling source citations, risking hallucinations.
  2. **Manual RAG Step Disconnect**: After `/tc-research` scouts sources, the index is not automatically compiled into `rag-db/index.db` unless someone manually runs `tc index build`.
  3. **Measuring Grounding / Hallucination Rate**: There is no automated test measuring whether curriculum concepts are backed by evidence in `index.db`.
- **Fix**:
  1. **Auto-Build RAG Index in Research**:
     - At the end of `/tc-research`, automatically call `indexer.py build` so `research/<slug>/rag-db/` is immediately query-ready without manual intervention.
  2. **Inject Grounded Source Excerpts into `/tc-teach`**:
     - Update `teach_engine.py session` to query `courses/<slug>/rag-db/index.db` for the active concept using BM25.
     - Return the top 2–3 source excerpts with provenance citations in the `session` JSON payload.
     - In `skills/tc-teach/SKILL.md`, instruct the teacher to anchor the lesson strictly in these excerpts, ensuring zero hallucinated APIs or false facts.
  3. **Automated Internal Grounding Verification (No Public Skill Bloat)**:
     - Keep RAG verification **internal** (do NOT expose separate `/build-rag` or `/verify-rag` public slash commands).
     - Add `indexer.py verify-grounding --slug <slug>`: Audits every concept in `course.toml` against `index.db`, outputting a **Corroboration Score** (0–100%) and flagging unsupported concepts.
     - Hypatia checks this score during Triad Consensus in `tc-create`.

---

## Part 2: Additional Issues & Upcoming Changes

*(This section will capture all additional issues provided by the user before code execution begins.)*

- [ ] **Issue 1**: *(Pending user input)*
- [ ] **Issue 2**: *(Pending user input)*
- [ ] **Issue 3**: *(Pending user input)*

---

## Part 3: Files to Modify Upon Approval

| File Path | Description of Changes |
| :--- | :--- |
| [`skills/tc-init/SKILL.md`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/skills/tc-init/SKILL.md) | Drop Stage 5 density question, sharpen Stage 5 teacher menu & add combo tip, update next-action recommendation to `/tc-research`, expand Stage 2 domain elicitation, universalize persona descriptions. |
| [`skills/tc-teach/SKILL.md`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/skills/tc-teach/SKILL.md) | Mandate `log-turn` invocation after every interactive dialogue, re-explanation, or student question; universalize single-concept lesson template (case study / worked example / code); ground lessons in retrieved source excerpts. |
| [`_tc/INTERACTION_STANDARDS.md`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/INTERACTION_STANDARDS.md) | Update intake standard from 6 stages to 5 stages, align lifecycle progression, mandate conversational turn logging, codify universal domain decoupling. |
| [`_tc/scripts/bootstrapper.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/bootstrapper.py) | Parse hybrid teacher inputs, compose style arrays, auto-derive density, add `/tc-research` to state machine recommendations, persist `--subject` and `--goals`, generalize `code_first` to Case-First & Applied Builder. |
| [`_tc/scripts/course_builder.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/course_builder.py) | Remove involuntary beginner teacher reassignment, read goals from preferences, mirror course creation to `profile/memlog.md`. |
| [`_tc/scripts/teach_engine.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/teach_engine.py) | Remove involuntary beginner teacher reassignment, enrich `session` output with trailing `memlog.md` entries alongside `session.jsonl`, inject top BM25 source citations for active concept from `rag-db/index.db`. |
| [`_tc/scripts/practical_evaluator.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/practical_evaluator.py) | Mirror capstone pass milestones to `courses/<slug>/memlog.md` and `profile/memlog.md`; remove domain-specific programming keyword checks; generalize deliverable inspection. |
| [`_tc/scripts/diagnostic_tester.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/diagnostic_tester.py) | Mirror course completion milestones to `profile/memlog.md`. |
| [`_tc/scripts/indexer.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/_tc/scripts/indexer.py) | Add `verify-grounding` subcommand auditing curriculum concepts against `index.db` citations. |
| [`skills/tc-roadmap/SKILL.md`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/skills/tc-roadmap/SKILL.md) | Mark as internal engine (callable by `tc-init`), not a public user-facing slash skill. |
| [`skills/tc-verify-course/SKILL.md`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/skills/tc-verify-course/SKILL.md) | Mark as internal Triad auditor (callable by `course_builder.py`), not a public user-facing slash skill. |
| [`skills/tc-init/scripts/runtime/`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/skills/tc-init/scripts/runtime/) | Synchronize updated runtime scripts. |
| [`tests/test_bootstrapper.py`](file:///C:/Users/dasav/Documents/Code/text-courses-redesign/tests/test_bootstrapper.py) | Add unit tests verifying hybrid combinations (`1, 2`, `1, 3`, etc.), `/tc-research` scan recommendation, and goal persistence. |

---

## Part 4: Verification Checklist

- [ ] `python -m pytest tests/test_bootstrapper.py` passes with hybrid teacher assertions and research recommendations.
- [ ] `python -m pytest tests/test_indexer.py` passes with RAG grounding and verification assertions.
- [ ] `python -m pytest tests/test_e2e_tracer.py` passes end-to-end.
- [ ] Full test suite passes: `python -m pytest tests/`.
- [ ] No regression in BMad tickets or CLI commands.
