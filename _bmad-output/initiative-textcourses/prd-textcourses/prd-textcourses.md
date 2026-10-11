---
title: "Product Requirements Document: TextCourses 2.0 (textcourses.com)"
status: "in-review"
created: "2026-10-10"
updated: "2026-10-11"
version: "2.0.0"
---

# PRD: TextCourses 2.0 (textcourses.com)
**The Sovereign, Personality-Driven Autonomous Apprenticeship Platform**

---

## 0. Document Purpose

This Product Requirements Document (PRD) establishes the authoritative product, functional, and non-functional specifications for **TextCourses 2.0** (`textcourses.com`). It serves technical product managers, systems architects, skill prompt engineers, and downstream implementers. 

TextCourses 2.0 synthesizes the initial framework specifications with the strategic breakthroughs forged in [brainstorm-teacher-personality-framework.md](file:///home/bharath/Documents/Code/text-courses-redesign/_bmad-output/initiative-textcourses/brainstorm-teacher-personality-framework/brainstorm-teacher-personality-framework.md). All requirements are numbered globally as stable references (`FR-1` through `FR-29`). Technical choices that belong strictly to implementation architecture live in downstream specifications (`bmad-architecture`).

---

## 1. Vision

TextCourses transforms any local filesystem workspace into an **Autonomous Apprenticeship Engine**. Moving past the industrial classroom model of passive video courses (Coursera, Udemy) and amnesic, wall-of-text chat feeds (ChatGPT, Claude), TextCourses unifies the relentless milestone discipline of a master curriculum with the fluid, adaptive depth of 1-on-1 expert Socratic mentorship.

In an era saturated by free, commoditized AI text generation, passive reading has near-zero educational defensibility. TextCourses establishes an **AI-proof moat** through three foundational mechanics:
1. **Conversational Single-Topic Apprenticeship:** Socratic, single-concept micro-turns adhering to a learner-tailored style profile, culminating in a standardized Next-Action Fork (`[1] Next Topic`, `[2] Test Me`, `[3] Re-explain`, `[4] Custom Question`).
2. **Automated Background Knowledge Distillation:** Mandatory auto-compilation of every finished lesson into a personalized reference textbook (`notes.md`) on disk without breaking flow state.
3. **Malleable, Learner-Configured Curriculum & Proof of Work:** Active learner co-creation of curricula grounded in verified documentation via the Triad Consensus Loop, coupled with verifiable applied portfolio projects (`portfolio/`) evaluated across four parallel objective review lenses.

The filesystem hierarchy (`Roadmap` ➔ `Course` ➔ `Chapter` ➔ `Section`) serves as the apprentice's navigational compass, while `notes.md` acts as the workshop journal and `portfolio/` contains unassailable human proof of work.

---

## 2. Target User & Journeys

### 2.1 Jobs To Be Done (JTBD)
- **JTBD-1 (Deep Mastery):** When I encounter a complex, high-stakes domain (e.g. Distributed Consensus, Quantitative Finance, Rust Internals), I want a structured, exhaustive, zero-fluff curriculum that adapts to my technical background so that I achieve authentic operational fluency in weeks rather than months.
- **JTBD-2 (Sovereign Pacing & Compaction):** When learning through AI, I want to control my progression turn-by-turn and retain permanent, distilled notes on my disk so that I never suffer from chat amnesia or unverified wall-of-text skimming.
- **JTBD-3 (Verifiable Proof of Competence):** When completing a subject, I want to build real, working projects that are objectively evaluated across multiple technical lenses so that I have genuine proof-of-work for my portfolio or employer.
- **JTBD-4 (Team Knowledge Standard):** When onboarding junior engineers or technical analysts, I want to provide a reproducible, doc-grounded learning repository so that new hires ramp up with zero hallucinated practices.

### 2.2 Non-Users (v1)
- **The Passive Skimmer:** Learners looking for 5-minute infotainment video clips, auto-playing lectures, or multiple-choice gamification badges.
- **The Proctored Credential Hunter:** Students needing accredited university degrees, proctored biometric exam monitoring, or state-mandated certifications.
- **The Web Dashboard Clicker:** Users unwilling to interact with a filesystem, CLI, or editor-native AI agent harness.

### 2.3 Key User Journeys

#### UJ-1: Maya Architectures a Grounded Distributed Systems Curriculum
- **Persona & Context:** Maya, a senior backend engineer switching into distributed database development.
- **Entry State:** Fresh local directory. Invokes `/tc-init` via her IDE AI assistant.
- **Path:**
  1. `tc-init` guides Maya through a selectable intake (Software Engineer - Systems, Experienced Practitioner, Technical Direct style profile).
  2. Maya triggers `/tc-create "Distributed Consensus & Raft from Scratch"`, selecting *Applied Creation* archetype.
  3. Maya provides a link to the canonical Raft paper and etcd documentation.
  4. `tc-research` scouts the doc ToCs into `.tc/research/raft/`.
  5. The Triad Consensus Loop reconciles the draft against verified docs; `tc-verify-course` confirms zero missing prerequisites.
- **Climax:** Maya approves the interactive roadmap preview. The filesystem structure (`plan/` and `courses/course-01-raft/`) is generated cleanly to disk in seconds.
- **Resolution:** Maya types `/tc-teach` to launch Chapter 1, Section 1 immediately.
- **Edge Case:** If `tc-research` encounters a paywall or rate limit, it falls back to Tier 2 with an explicit `unverified` flag, escalating to Maya for approval rather than guessing.

#### UJ-2: David Learns Lock-Free Primitives Without Breaking Flow
- **Persona & Context:** David, a systems programmer studying memory ordering.
- **Entry State:** In-progress section in `courses/course-01-concurrency/chapter-02/section-01-atomics/`.
- **Path:**
  1. David runs `/tc-teach`. The AI inspects `lesson-plan.md` and loads David's *Code-First + Math* style profile.
  2. The AI delivers a single, dense explanation of Acquire-Release semantics with a worked example and fatal anti-pattern.
  3. Turn closes with the standardized Next-Action Fork.
  4. David selects `[1] Next Topic`. The AI ticks the concept checkmark in `lesson-plan.md` and seamlessly continues to memory barriers.
  5. When the final concept in the section completes, `tc-teach` automatically compiles `notes.md` in the background, prints a 3-bullet recap, updates `course.toml` to `status: review`, and presents the next chapter fork.
- **Climax:** David finishes the section in uninterrupted flow with zero bureaucratic approval prompts, while a high-density `notes.md` reference is securely saved on disk.
- **Resolution:** David advances to Section 2 or triggers diagnostic testing.

#### UJ-3: Elena Tests Mental Models and Tracks Misconceptions
- **Persona & Context:** Elena, a bioinformatics graduate student learning Python algorithmic complexity.
- **Entry State:** Completed Section 3 of Foundations.
- **Path:**
  1. Elena picks `[2] Test me on this topic first` from the fork (or types `/tc-test-me`).
  2. `tc-test-me` reads completed `notes.md` and past entries in `test-ledger.jsonl`.
  3. `tc-test-me` generates a diagnostic hinge scenario: *"Function A uses a dict lookup inside a generator loop over list B. If list B has $N$ items and dict has $M$ items, what is worst-case time complexity?"*
  4. Elena answers incorrectly, conflating generator evaluation with immediate allocation.
  5. `tc-test-me` identifies the misconception, explains the mechanism concisely, and appends a structured record with code `CONFUSION_GENERATOR_LAZY_VS_EAGER` to `test-ledger.jsonl`.
- **Climax:** Elena sees exactly where her mental model cracked without ever being asked to copy-paste code into chat.
- **Resolution:** Next time Elena runs `tc-test-me` or `tc-practicals`, the system remembers this misconception and tests edge cases around lazy evaluation.

#### UJ-4: Marcus Builds and Verifies a Practical Capstone Deliverable
- **Persona & Context:** Marcus, a self-taught engineer finalizing an in-memory database course.
- **Entry State:** All 4 chapters marked `review` in `course.toml`.
- **Path:**
  1. Marcus runs `/tc-practicals`. The skill reads his preferences and `test-ledger.jsonl` (which flags past confusion on crash recovery).
  2. `tc-practicals` offers project customization: Medium complexity, weekend sprint budget, focused on Write-Ahead Log (WAL) recovery.
  3. Marcus accepts; `portfolio/project-01/project-spec.md` is generated with 4 verifiable deliverable requirements and automated test runners.
  4. Marcus builds the code in `portfolio/project-01/workspace/` and tells the agent he is ready for review.
  5. `tc-practicals` executes a 4-Lens Review (Functional Completeness, Edge Cases, Architecture & Craft, Verification Integrity).
- **Climax:** The agent generates `portfolio/project-01/review-report.md`, marking the WAL implementation PASS with a warning on unbuffered fsync throughput.
- **Resolution:** `course.toml` transitions to `status: completed`. Marcus has a verifiable git artifact for his portfolio.

#### UJ-5: Elena Architectures a Data Science Track via Triad Inception Party Mode
- **Persona & Context:** Elena, an analytics engineer wanting to master Data Science and Machine Learning.
- **Entry State:** Fresh workspace initialized via `/tc-init`.
- **Path:**
  1. Elena invokes `/tc-roadmap "Data Science Track"`.
  2. The Triad Faculty assembles in visible Party Mode:
     - 🔬 **Marie (The Scout)** analyzes modern 2026 data stacks (Arrow, Polars, PyTorch, DuckDB).
     - 🗺️ **Aristotle (The Cartographer)** sketches a 4-course sequence: Vector Primitives ➔ Probabilistic Foundations ➔ Applied ML ➔ Neural Systems.
     - ⚖️ **Hypatia (The Auditor)** flags linear algebra prerequisite bounds and requests baseline verification.
  3. The Triad presents Elena with 3 sharp diagnostic hinge questions assessing her Python, SQL, and linear algebra proficiency.
  4. Elena passes the Python and SQL checks; the Triad marks Course 1 as `[WAIVED]` in `roadmap/roadmap.toml`.
  5. Aristotle activates Course 2 (*Vectorized Wrangling & Matrix Foundations*) and seamlessly dispatches `/tc-create`.
- **Climax:** Elena is placed at her exact learning frontier without sitting through remedial syntax, with an auditable roadmap on disk.
- **Resolution:** The entire caucus debate and placement decisions are logged to `profile/memlog.md`.

#### UJ-6: Marcus Experiences an Adaptive Faculty Tag-Team Handoff
- **Persona & Context:** Marcus, learning Distributed Storage Systems, has chosen Euclid as his primary instructor.
- **Entry State:** Working through Chapter 1, Section 2 on Write-Ahead Log (WAL) durability.
- **Path:**
  1. Euclid provides an axiomatic, state-machine derivation of disk sync boundaries.
  2. Marcus selects `[3] Re-explain / Deeper` to explore failure modes. Euclid provides a second mathematical breakdown.
  3. Marcus still struggles with how the OS page cache interacts with power failures and selects `[3]` again.
  4. Detecting repeated conceptual friction, the tutor offers an **Adaptive Faculty Handoff**: `[3] Tag-in ⚡ Feynman for an intuitive physical analogy`.
  5. Marcus accepts. Feynman steps in acknowledging Euclid's prior state trace, using an everyday physical postal metaphor.
  6. The breakthrough occurs; Marcus selects `[1] Next Concept`.
- **Climax:** Marcus overcomes cognitive blockage through a tag-team pedagogical shift rather than repetitive lectures.
- **Resolution:** The handoff is atomically appended to `courses/distributed-storage/memlog.md`: `- (handoff) Euclid handed off to Feynman: learner needed physical intuition for WAL torn writes`.

---

## 3. Glossary

- **Autonomous Apprenticeship Engine**: The architectural paradigm of TextCourses pairing master-curriculum discipline with fluid 1-on-1 Socratic AI mentorship.
- **Curriculum Blueprint**: The high-level pedagogical structure spanning `plan/roadmap.toml`, chapter manifests, and prerequisite DAGs.
- **Lesson Plan (`lesson-plan.md`)**: The internal instructor blueprint containing concept checklists, golden paths, fatal anti-patterns, and metacognitive probes. Strictly read by AI agents; never read by the learner.
- **Compiled Notes (`notes.md`)**: The permanent, distilled student reference book generated post-section completion, structured around the lesson-plan concept checklist and styled to learner preferences.
- **Next-Action Fork**: The standardized 4-option turn conclusion closing every single `tc-teach` explanation (`[1] Next Topic`, `[2] Test Me`, `[3] Re-explain`, `[4] Custom`).
- **Test Ledger (`test-ledger.jsonl`)**: Machine-readable assessment log appending timestamped records of diagnostic questions, learner answers, diagnosed misconceptions, and remediation tags.
- **Portfolio Deliverable (`portfolio/`)**: Hands-on human proof-of-work project artifacts (code, tests, schemas, analytical memos) evaluated against deterministic criteria.
- **Triad Consensus Loop**: The closed-loop authoring cycle between `tc-create` (architect), `tc-research` (scout), and `tc-verify-course` (auditor) preventing ungrounded curricula.
- **Style Profile**: Learner preference profile configured in `plan/preferences.md` balancing technical density, code inclusion, and conceptual depth.
- **Evolvable Profile**: The mechanism whereby `tc-teach` suggests style profile adjustments at chapter boundaries based on learner interaction patterns.
- **Context Manifest**: The formal per-skill stage-aware specification of which files must be loaded in full, summarized, or excluded to preserve context window budgets.
- **Deprecation Marker**: A non-destructive Markdown header appended to completed `notes.md` by `tc-redirect-course` flagging superseded content without modifying the original text.

---

## 4. Features & Functional Requirements

### 4.1 Onboarding & Navigation (`tc-init`)

**Description:** Manages workspace initialization, learner intake, style configuration, and progress scanning. It rejects open-ended essay prompts in favor of scannable, numbered selections with an `Other` write-in option. Realizes UJ-1.

#### FR-1: Low-Friction, Turn-by-Turn Structured Intake & Role Diversity
The system SHALL capture learner profile data through a conversational, turn-by-turn numbered intake asking strictly ONE question per turn across Learner Identity, Target Domain, 10-Option Role Diversity, Domain Experience Level, and Explanation Density. Realizes UJ-1.
- **Consequences (testable):**
  - System asks exactly one question per turn and awaits learner input before proceeding to the next turn, eliminating cognitive fatigue.
  - Presents exactly 9 diverse professional roles + `[10] Other (write-in)` (including Software Engineer, Product Manager, Student, Lawyer, Healthcare, Teacher, Designer, Finance, Sales/Ops).
  - Domain experience level provides `[4] Custom (write-in)` to allow hybrid/custom learning objectives.
  - Dynamically tags the most suitable option with `(Recommended)` based on prior answers.
  - System writes selected attributes into `profile/preferences.md` and `plan/preferences.md`.
  - Re-running `/tc-init` on an existing workspace displays current preferences with an option to retain or re-configure.

#### FR-2: Pedagogical Style Automation (Zero-Jargon Derivation)
The system SHALL eliminate confusing comparative style previews and preferred style selection prompts during intake, automatically deriving the optimal pedagogical style directives from the learner's chosen master teacher persona and explanation density level. Realizes UJ-1, UJ-2.
- **Consequences (testable):**
  - Intake flow completely avoids asking the learner to decipher sample paragraphs or pick abstract style codes (e.g., "A + C").
  - Pedagogical styles (e.g. intuitive analogies for Feynman, practical code-first for Turing, gentle step-by-step for Hypatia) are automatically synthesized into `profile/preferences.md`.
  - At chapter boundaries during `tc-teach`, the system inspects interaction latency and questions, and SHALL prompt the learner if a style profile adjustment is recommended.

#### FR-3: Workspace State Scanner
When invoked in an existing workspace, `tc-init` SHALL inspect all `course.toml` and `roadmap.toml` manifests, identify the active section (`in_progress` or `review`), and output the exact next recommended action command. Realizes UJ-1.
- **Consequences (testable):**
  - If no course exists, suggests `/tc-create`.
  - If section is `in_progress`, outputs command to resume `/tc-teach`.
  - If all sections in chapter are in `review`, suggests `/tc-test-me` or `/tc-practicals`.

---

### 4.2 Curriculum Architecture & Grounded Generation (`tc-create`, `tc-research`, `tc-verify-course`)

**Description:** Transforms user intent into an exhaustive, prerequisite-verified curriculum using one of 5 Universal Archetypes, grounded in verified web/doc research via the Triad Consensus Loop. Realizes UJ-1.

#### FR-4: The 5 Universal Curriculum Archetypes
The system SHALL structure generated courses around one of 5 selectable pedagogical archetypes: Applied Creation, Forensic Dilemma, Axiomatic Primitives, Spiral Immersion, or Reverse Engineering. Realizes UJ-1.
- **Consequences (testable):**
  - User can select the archetype during `/tc-create` interactive mode.
  - The generated `overview.md` explicitly documents the chosen archetype and pedagogical rationale.

#### FR-5: User-Supplied Curriculum Ingestion
The system SHALL accept external curriculum inputs (reference URLs, syllabus tables, or pasted chapter lists) during `/tc-create` and adapt them as the structural backbone of the course. Realizes UJ-1.
- **Consequences (testable):**
  - External input chapters are mapped to `chapter-XX/` directories with user chapter titles preserved.
  - Missing prerequisites or conceptual leaps are surfaced via `tc-verify-course` before disk generation.

#### FR-6: Multi-Tier Research Scouting with Confidence Scoring (`tc-research`)
The system SHALL extract ToCs, API indexes, and syllabi from public documentation into `.tc/research/<slug>/` using a 3-tier fallback with confidence scoring (`high`, `medium`, `low`). Realizes UJ-1.
- **Consequences (testable):**
  - Scraped sources are tagged `verified` in `metadata.json`.
  - Fallback LLM benchmark synthesis is explicitly tagged `unverified`.
  - If overall confidence is below `medium`, the system MUST halt and prompt the user to review the research digest or provide local reference files.
  - Can be invoked directly as a standalone skill by the user.

#### FR-7: Pre-Flight Curriculum Audit (`tc-verify-course`)
The system SHALL execute an independent pre-flight audit scanning all drafted `lesson-plan.md` files against research digests for prerequisite DAG violations, vocabulary leaps, and deprecated APIs. Realizes UJ-1.
- **Consequences (testable):**
  - Fails course creation if a concept in Section $K$ requires undefined terminology from Section $K+N$.
  - Generates an audit report in `.tc/cache/audit-preflight.md`.
  - Zero critical findings required before files are committed to `courses/`.
  - Can be invoked directly as a standalone skill by the user.

#### FR-8: The Triad Consensus Loop
The system SHALL execute an automated consensus cycle between `tc-create`, `tc-research`, and `tc-verify-course` before writing files to disk. Realizes UJ-1.
- **Consequences (testable):**
  - Curriculum reconciliations, audit critiques, and consensus resolutions are recorded in `.tc/cache/consensus-trace.jsonl` for full auditability.

---

### 4.3 Instructional Delivery & Flow-Preserving Notes (`tc-teach`)

**Description:** Delivers single-concept conversational deep dives, maintains session checkmarks, auto-compiles permanent notes to disk, and closes every turn with the Next-Action Fork. Realizes UJ-2.

#### FR-9: Substantial Single-Concept Delivery
The system SHALL deliver instruction bounded strictly to one concept per message, sized appropriately to justify generation latency, adhering strictly to the active Style Profile. Realizes UJ-2.
- **Consequences (testable):**
  - Explanations include scannable bold mechanics, formatted code/tables, and worked examples paired with fatal anti-patterns.
  - Zero unsolicited multi-concept lecturing in a single turn.

#### FR-10: Standardized Next-Action Fork
The system SHALL conclude every instructional response with the exact 4-option Next-Action Fork. Realizes UJ-2.
- **Consequences (testable):**
  - Fork options: `[1] Yes, continue to next topic`, `[2] Test me on this topic first`, `[3] Explain this differently / Give me another practical example`, `[4] Custom question`.
  - Entering `1` immediately delivers the next topic checklist item.
  - Entering `2` invokes the diagnostic challenge for the current concept.

#### FR-11: Automated Flow-Preserving Notes Compilation
Upon completing the final concept checklist item in a section, the system SHALL automatically compile `notes.md` in the background, write it to disk, print a concise 3-bullet recap, and update `course.toml` to `status: review`. Realizes UJ-2.
- **Consequences (testable):**
  - `notes.md` is guaranteed to exist on disk before section advancement is unlocked.
  - Learner can immediately advance to the next section via `[1]` without waiting for or engaging in a mandatory multi-turn approval dialogue.
  - Learner may optionally edit or request re-distillation of `notes.md`.

#### FR-12: Session Hygiene & Live Compaction
The system SHALL toggle checkmarks in `lesson-plan.md` in real-time as concepts are completed, ensuring sessions can be interrupted and resumed with zero state loss. Realizes UJ-2.
- **Consequences (testable):**
  - Interrupting an agent turn and restarting `/tc-teach` reads the latest checkmark and resumes at the exact unfinished concept.
  - Recommends ending the session after completing one section to maintain AI instruction fidelity.

---

### 4.4 Diagnostic Conceptual Assessment (`tc-test-me`)

**Description:** Conducts 100% question-based diagnostic evaluations of learner mental models without code copy-pasting, logging all outcomes to a persistent ledger. Realizes UJ-3.

#### FR-13: 100% Question-Based Testing (Zero Code Pasting)
The system SHALL evaluate learner mastery strictly through scenario-based diagnostic questions, hinge dilemmas, and mechanism trade-offs, NEVER prompting the learner to paste code into chat. Realizes UJ-3.
- **Consequences (testable):**
  - Questions evaluate boundary conditions, failure modes, and architectural implications.
  - Learner responds via conceptual explanation or numbered trade-off selection.

#### FR-14: Persistent Diagnostic Assessment Ledger
The system SHALL append every diagnostic test interaction to `courses/<slug>/test-ledger.jsonl`. Realizes UJ-3.
- **Consequences (testable):**
  - Record schema includes: `timestamp`, `course`, `chapter`, `section`, `question_type`, `prompt`, `learner_response`, `outcome`, `diagnosed_misconception`, `remediation_summary`, `confidence_level`.
  - Machine-parsable JSONL written atomically.

#### FR-15: Cumulative Boundary Rule
The system SHALL test only concepts that exist in sections marked `review` or `completed` in `course.toml`, strictly forbidding future concept leaks. Realizes UJ-3.
- **Consequences (testable):**
  - Test questions never introduce terminology or mechanics from upcoming uncompleted sections.

---

### 4.5 Applied Proof-of-Work & Multi-Lens Verification (`tc-practicals`)

**Description:** Formulates customizable hands-on project briefs and evaluates user deliverables across four parallel objective review lenses. Realizes UJ-4.

#### FR-16: Customizable Project Brief Intake
The system SHALL customize practical projects based on learner preferences (Complexity, Time Budget, Depth/Breadth) with Medium defaults, or adapt to a custom user project idea. Realizes UJ-4.
- **Consequences (testable):**
  - Generates `portfolio/project-XX/project-spec.md` with explicit, AI-verifiable deliverable contracts.
  - If `test-ledger.jsonl` contains recurring misconceptions, project tasks SHALL be weighted to exercise those specific weak areas.

#### FR-17: Verifiable Deliverable Constraints
The system SHALL restrict required project deliverables to artifacts an AI can deterministically evaluate (code, test suites, schemas, formatted design memos). Realizes UJ-4.
- **Consequences (testable):**
  - Every project spec specifies explicit file paths, test commands, and expected pass/fail outputs.

#### FR-18: Multi-Lens Project Review Pass
The system SHALL review submitted deliverables across 4 parallel objective lenses: (1) Functional Completeness, (2) Edge Cases & Robustness, (3) Architecture & Craft, and (4) Verification Integrity. Realizes UJ-4.
- **Consequences (testable):**
  - Generates `portfolio/project-XX/review-report.md` detailing findings per lens.
  - On satisfactory review, updates `course.toml` chapter or course status to `completed`.

---

### 4.6 Lifecycle & Evolution Management (`tc-redirect-course`, `tc-migrate`)

**Description:** Manages non-destructive course updates and safe workspace migrations with explicit user consent. Realizes UJ-1, UJ-2.

#### FR-19: Cryptographic Source Hash Tracking
The system SHALL track ingested source files in `plan/sources/ledger.toml` using SHA-256 hashes to detect added, modified, or deleted references. Realizes UJ-1.
- **Consequences (testable):**
  - Re-running `tc-redirect-course` reads delta changes and computes affected unfinished chapters.

#### FR-20: Completed Lesson Immutability & Non-Destructive Deprecation
The system SHALL NEVER rewrite, edit, or delete completed sections. When new sources supersede completed content, it SHALL only append new sub-sections after completed content, or prepend non-destructive Deprecation Markers to `notes.md`. Realizes UJ-2.
- **Consequences (testable):**
  - Completed `notes.md` bodies are preserved bit-for-bit, with at most a `> ⚠️ Deprecation Marker` block prepended.

#### FR-21: Safe Schema Migration with Mandatory User Consent
`tc-migrate` SHALL inspect legacy or damaged workspaces, generate a transparent `migration-plan.md`, and MUST require explicit user confirmation before moving or modifying any files on disk. Realizes UJ-1.
- **Consequences (testable):**
  - Zero disk modifications occur without typed user confirmation.

---

### 4.7 Context Engineering & Harness Agnosticism

**Description:** Enforces token efficiency and surface versatility across all AI runtime environments.

#### FR-22: Context Loading Manifests per Stage
Each `tc-*` skill SHALL define and adhere to a strict Context Loading Manifest specifying files loaded in full, summarized, or omitted per operational stage, enforced via structured tool calls. Realizes UJ-1, UJ-2, UJ-3, UJ-4.
- **Consequences (testable):**
  - `tc-teach` loads only active `lesson-plan.md`, `preferences.md`, current chapter's prior `notes.md` (summary), and rolling misconception summaries. It NEVER glob-loads other chapters.
  - Total context consumption per teaching turn remains under 25% of naive all-in-one chat sessions.

#### FR-23: AI-Harness Agnosticism
All `tc-*` skills SHALL function identically across any AI environment providing filesystem read/write access (Terminal CLI, VS Code extension, Cursor, JetBrains, or web wrapper). Realizes UJ-1.
- **Consequences (testable):**
  - Skill prompts rely solely on standard filesystem paths and JSON/TOML/Markdown formats, requiring no proprietary API wrappers.

---

### 4.8 TextCourses 2.0: Personality-Driven Faculty, Macro Roadmaps & Sovereign Memory

**Description:** Upgrades TextCourses from an isolated single-course engine into a personality-driven apprenticeship platform featuring living master teacher personas, multi-course roadmaps with live Triad Inception Party Mode, a two-tier chronological memory log, and streamlined folder ergonomics. Realizes UJ-5, UJ-6.

#### FR-24: Streamlined Kid-Friendly Teacher Personas
The system SHALL present a streamlined roster of 3 intuitive, kid-friendly primary master teachers during intake with descriptions understandable by a 10-year-old. Realizes UJ-1, UJ-6.
- **Consequences (testable):**
  - Chiron (`/tc-init`) presents 3 distinct, accessible teaching personas + `[4] Other (write-in)`:
    - **⚡ Feynman (The Everyday Explainer)**: Fun, simple, uses everyday stories and real-world analogies, zero confusing jargon.
    - **🦉 Hypatia (The Step-by-Step Mentor)**: Patient, gentle, guides you step-by-step from zero without skipping anything.
    - **💻 Turing (The Practical Builder)**: Logical, hands-on, focuses on building things, how it works under the hood, and real code.
  - Specialized non-teaching agents (Marie for research, Aristotle for roadmap DAGs, Leonardo for portfolio project reviews) remain dedicated to their pipeline roles and are not thrust upon learners as teaching style choices during intake.
  - The chosen primary teacher is persisted to `profile/preferences.md`.
  - Instructional delivery in `/tc-teach` adopts the selected teacher's persona, tone, and invariants.

#### FR-25: Adaptive Faculty Tag-Team Handoffs & Dynamic Switching
When a learner encounters conceptual friction by requesting re-explanation twice on the same concept, the system SHALL proactively offer an in-character faculty handoff to an alternate teacher. Realizes UJ-6.
- **Consequences (testable):**
  - The Next-Action Fork in `/tc-teach` surfaces a tag-team option: `[3] Tag-in <Teacher B> for an alternate angle`.
  - Teacher B initiates instruction explicitly referencing Teacher A's prior explanation using context from `memlog.md`.
  - The handoff event is atomically appended to `courses/<slug>/memlog.md`.
  - Learners can switch their primary teacher at any time, updating `profile/preferences.md`.

#### FR-26: Multi-Course Macro Roadmaps & DAG Orchestration (`tc-roadmap`)
The system SHALL provide a dedicated macro-curriculum skill (`tc-roadmap`) orchestrated by **🗺️ Aristotle (The Cartographer)** to decompose expansive domains into structured multi-course roadmaps. Realizes UJ-5.
- **Consequences (testable):**
  - Decomposes broad topics (e.g., Data Science, Distributed Systems) into 3–6 sequential, atomic courses.
  - Generates `roadmap/roadmap.toml` managing track status (`not_started`, `active`, `completed`) and inter-course prerequisite DAGs.
  - Generates human-readable `roadmap/overview.md` with visual progress indicators.
  - Automates dispatch to `/tc-create` for the active starting course.

#### FR-27: Live Triad Inception Roundtable & Diagnostic Placement
`tc-roadmap` SHALL execute the Triad Consensus Loop visibly in open Party Mode between Marie (The Scout), Aristotle (The Cartographer), and Hypatia (The Auditor), culminating in interactive diagnostic placement questions for the learner. Realizes UJ-5.
- **Consequences (testable):**
  - Marie evaluates modern industry standards, official documentation ToCs, and current libraries.
  - Aristotle drafts the multi-course progression and milestones.
  - Hypatia audits prerequisite contracts and challenges cognitive leaps.
  - The Triad presents 2–4 targeted hinge diagnostic questions to evaluate learner baseline proficiencies.
  - Confirmed prior proficiencies are marked `[WAIVED]` in `roadmap/roadmap.toml`, placing the learner directly at their optimal frontier.
  - Rationale and debate transcripts are preserved in `profile/memlog.md`.

#### FR-28: Two-Tier Pedagogical Memory Logging (`_tc/scripts/memlog.py`)
The system SHALL maintain a two-tier append-only chronological memory log across all learning sessions, eliminating chat amnesia without token budget bloat. Realizes UJ-2, UJ-5, UJ-6.
- **Consequences (testable):**
  - **Global Journey Log (`profile/memlog.md`)**: Records macro milestones, track completions, and global faculty notes.
  - **Course Pedagogical Memory (`courses/<slug>/memlog.md`)**: Logs granular instructional events using structured tags:
    - `- (concept by <Teacher>) <Mechanism taught>`
    - `- (question by user) <Query raised>`
    - `- (insight by user) <Learner mental model breakthrough>`
    - `- (misconception) <Confusion identified>`
    - `- (handoff) <Teacher handoff>`
    - `- (milestone) <Section completed or test passed>`
  - Managed via deterministic script `_tc/scripts/memlog.py` using atomic append writes.
  - `/tc-teach` loads the trailing 15 lines of `memlog.md` on session resume to ensure seamless conversational continuity.

#### FR-29: Streamlined Sovereign Folder Architecture & BMad Ecosystem Parity
The system SHALL enforce a unified, human-navigable filesystem layout and full BMad packaging compliance across all skills. Realizes UJ-1.
- **Consequences (testable):**
  - Eliminates `.tc/` vs `_tc/` ambiguity by consolidating all engine scripts, caches, and configs under visible `_tc/`.
  - Flattens 4-level deep course nesting into direct chapter textbook files: `courses/<slug>/notes/chapter-XX.md`.
  - Links practical capstones directly to courses: `portfolio/<slug>-project/`.
  - Equips all 10 skills with `bmod.toml` manifests and 3-tier `customize.toml` override support.
  - Eliminates triplicate script redundancy by routing all skills exclusively to `_tc/scripts/`.

#### FR-30: Autonomous 5-Hat Deep Research Engine (`tc-research` / `scout.py`)
The system SHALL provide a dedicated pre-course autonomous research agent orchestrated by **🔬 Marie (The Empirical Investigator)** to harvest, evaluate, and synthesize comprehensive domain knowledge before course creation. Realizes UJ-4, UJ-5.
- **Consequences (testable):**
  - Executes multi-round targeted web searches and scrapes authoritative official documentation and specifications.
  - Applies **5-Hat Critical Reflection (Tree-of-Thought Dialectic)**:
    1. *Industry Practitioner Hat*: Real-world production patterns and industry standards.
    2. *Academic Purist Hat*: Formal foundational models, mathematical proofs, and core invariants.
    3. *Beginner Friction Hunter Hat*: Hidden assumed knowledge, confusing syntax, and common mental blocks.
    4. *Edge-Case Systems Engineer Hat*: Concurrency hazards, resource leaks, failure modes, and performance cliffs.
    5. *Modern Ecosystem Reviewer Hat*: Deprecated patterns, breaking changes in latest versions, and modern idiomatic tooling.
  - Formulates secondary and tertiary search queries based on identified gaps across the 5 perspectives.
  - Synthesizes findings into a visible root-level dossier directory `research/<topic-slug>/`:
    - `dossier.md`: Comprehensive topic taxonomy, core mental models, code patterns, and verified pitfalls.
    - `sources.json`: Provenance citations, URLs, scraped titles, and retrieval timestamps.
    - `five-hats-critique.md`: The 5-perspective dialectic review highlighting gaps and production realities.

#### FR-31: Adversarial Triad Consensus Dialectic with Live Fact-Checking (`tc-create`)
Course creation SHALL be governed by a rigorous adversarial debate between **Daedalus (Curriculum Architect)**, **Marie (Empirical Investigator)**, and **Hypatia (Logic Auditor)**, requiring verified consensus before course files can be committed to disk. Realizes UJ-1, UJ-4.
- **Consequences (testable):**
  - Daedalus proposes candidate chapter/section structures grounded in learner intent (`profile/preferences.md`) and pre-existing research dossiers (`research/<topic-slug>/dossier.md`).
  - Marie actively challenges proposed topics against empirical documentation, performing live web search queries to verify latest version APIs or dispute controversial claims.
  - Hypatia ruthlessly audits cognitive leaps, prerequisite ordering, and vocabulary contracts, rejecting any section that uses untaught concepts.
  - The Triad deliberates across critique rounds until full consensus is reached; a course cannot be created if any critic dissents.
  - Daedalus personalizes the curriculum to the learner's profile, explicitly filling any pedagogical or practical gaps missed by the broad research dossier.
  - Full deliberation rounds and arguments are preserved in `_tc/cache/consensus-trace.jsonl`.

#### FR-32: Human-First Textbook Notes vs AI-First Token-Minimal Memlog Engine
The system SHALL maintain a strict linguistic register separation between human learner notes and AI pedagogical working memory. Realizes UJ-2, UJ-3, UJ-6.
- **Consequences (testable):**
  - **Human-First Notes (`notes/chapter-XX.md`)**: Compiled strictly for human learners. Written in clear, accessible, intuitive English with clear mental models, relatable analogies, annotated code implementations, and instructor attribution. Free of technical shorthand or prompt metadata.
  - **AI-First Memlog (`memlog.md`)**: Compiled strictly for AI agents. Employs ultra-dense, token-minimal notation (e.g. key-value shorthand, compact concept tags, error signatures) conveying complete semantic context with minimal token overhead.
  - **Closed Conversation Tracing Loop**: `/tc-teach` automatically appends taught concepts (`- (concept by <Teacher>) <slug>:<invariant>`) and learner custom inquiries (`- (question) <query>`) to `courses/<slug>/memlog.md`.
  - `/tc-test-me` mirrors diagnostic outcomes (`- (misconception) <category>`) and milestones (`- (milestone) <section-completed>`) directly to `courses/<slug>/memlog.md`.

#### FR-33: Root-Level Research Substrate & Workspace Transparency
The workspace SHALL expose all research materials in a visible root-level directory and provide an automated human-readable orientation guide upon initialization. Realizes UJ-1.
- **Consequences (testable):**
  - Scaffolds visible `research/` at workspace root alongside `courses/`, `roadmap/`, `profile/`, `portfolio/`, and `_tc/`.
  - Bootstrapping automatically deploys `WORKSPACE_GUIDE.md` (and `README.md` if absent) at the workspace root describing the exact purpose, files, and editability of every directory.
  - Ensures a newcomer or collaborator inspecting the workspace instantly understands the complete layout.

#### FR-34: Beginner-to-Core Pedagogical Adaptation
The system SHALL treat a beginner competency declaration (`beginner`, `novice`, or starting from scratch) as a foundational constraint across research, curriculum architecture, teaching, and diagnostic testing.
- **Consequences (testable):**
  - When profile (`profile/preferences.md`) or user prompt indicates beginner level, `course_builder.py` sets `competency_level = "beginner"`, enforces foundational prerequisite laddering, avoids jumping into complex patterns, and constructs smaller incremental learning steps.
  - `scout.py` / `/tc-research` gives maximum priority to `beginner_friction_hunter` and `intuitive_metaphorist` critical hats, auditing all implicit assumptions and flagging potential cognitive overload points.
  - `/tc-teach` assigns primary pedagogical leadership to **Hypatia (The Empathetic Tutor)** or Feynman, enforcing Socratic pacing and strictly forbidding unexplained abstractions.
  - `/tc-test-me` begins diagnostic verification with intuitive conceptual understanding before advancing to mechanical stress tests.

#### FR-35: Autonomous Multi-Path Curriculum Brainstorming & Hat Validation
When creating a course (`/tc-create`), the system SHALL NOT prompt the learner with open-ended or stalling questions asking how to create the course. Instead, it SHALL autonomously generate multiple distinct curriculum architectures, stress-test them through the Universal Critical Hats, and converge via adversarial Triad debate.
- **Consequences (testable):**
  - `course_builder.py` automatically synthesizes four distinct pedagogical architectures:
    1. *Foundational / First-Principles Path* (theory-first, axioms to application)
    2. *Hands-on / Project-First Path* (build real artifacts from Day 1, introduce theory just-in-time)
    3. *Problem-Driven / Diagnostic Path* (failure modes, root-cause debugging, crisis response)
    4. *Intuitive / Metaphor-First Path* (mental models, visceral real-world analogies)
  - The generated paths are evaluated and validated through the active Universal Critical Hats (Applied Practitioner, Academic Purist, Beginner Friction Hunter, Edge-Case Systems Engineer, Resource Tradeoff Optimizer).
  - The Faculty Triad (Daedalus, Marie, Hypatia) debates the tradeoffs, synthesizes the optimal hybrid tailored to the learner's profile, and outputs `courses/<slug>/curriculum-brainstorm.md` alongside `consensus-deliberation.md`.

#### FR-36: In-Loop Practical Instruction & AI Practical Evaluation
When the learner indicates a desire to learn with practicals (`practical_focus = true`, hands-on exercises, or labs), the system SHALL embed the practicals agent into the active teaching loop and validate each lesson's practical challenge using AI.
- **Consequences (testable):**
  - `/tc-teach` includes **Daedalus (The Master Craftsman)** / `practical_evaluator.py` into every lesson turn, scaffolding a concrete, executable challenge in `courses/<slug>/lessons/lesson-XX/practical.md`.
  - The learner submits their practical solution directly, and the AI practical evaluator analyzes execution, correctness invariants, edge cases, and code craft.
  - The evaluator returns structured diagnostic feedback (status `pass`/`retry`, rubric score, specific corrections).
  - Section mastery and progress advancement in `ledger.toml` require successful practical verification.

#### FR-37: Zero-Unexplained-Jargon & Human-First Readability Guardrail
All text intended for human reading (notes, explanations, guides) SHALL be written in clear, accessible, plain English and MUST NEVER introduce unexplained domain jargon.
- **Consequences (testable):**
  - Every technical or domain-specific term must either be established in an earlier chapter or explicitly explained in-depth with a relatable everyday analogy upon its first appearance.
  - `notes_compiler.py` enforces a readability and jargon audit (`audit_jargon_and_readability`), ensuring all newly introduced technical terms feature an intuitive breakdown box before use.
  - Faculty teaching prompts in `teach_engine.py` strictly forbid technical gatekeeping or ungrounded terminology, requiring visceral analogies before formal definitions.

#### FR-38: Unified Runtime Dispatcher (`_tc/scripts/tc.py` CLI)
The system SHALL provide a unified CLI entrypoint `_tc/scripts/tc.py` dispatching all runtime commands (`init`, `research`, `create`, `teach`, `eval`, `notes`, `audit`, `dag`), consolidating script invocation into a single source of truth and eliminating redundant script duplication across skill folders. Realizes UJ-1, UJ-2, UJ-4.
- **Consequences (testable):**
  - Running `python _tc/scripts/tc.py <subcommand>` routes directly to the corresponding engine module with consistent argument parsing and unified error handling.
  - All skill prompts reference `_tc/scripts/tc.py` or `_tc/scripts/<module>.py`, terminating manual copies into `skills/*/scripts/runtime/`.

#### FR-39: Persistent Socratic Session State (`session.jsonl`)
The instruction engine SHALL record structured conversational turn snapshots into `courses/<slug>/session.jsonl` upon every concept transition and interactive exchange, ensuring long-term pedagogical continuity across sessions. Realizes UJ-2, UJ-6.
- **Consequences (testable):**
  - Logs timestamp, active section, concept, faculty persona, learner inputs, teacher explanations, and Socratic state.
  - Resuming `/tc-teach` automatically restores dialogue context from the last active session record without relying solely on chat window context.

#### FR-40: Dynamic Context-Adaptive Next-Action Fork
The instruction engine SHALL dynamically synthesize Next-Action Fork options based on the active pedagogical state, presenting immediate contextual actions such as practical challenge submissions, diagnostic testing, or concept advancement. Realizes UJ-2.
- **Consequences (testable):**
  - When a practical challenge is pending (`practical_pending = true`), option `[1]` dynamically adapts to `- [1] Submit Practical Solution: Daedalus evaluates your code`.
  - When all concepts in a section are mastered and practicals are passed, option `[1]` dynamically adapts to `- [1] Advance to Next Section: Compiles notes and begins next chapter`.

#### FR-41: Resilient Cross-Platform Hash Checksum Normalization
The integrity tracking engine (`hash_tracker.py`) SHALL normalize line endings (`\r\n` to `\n`) and strip trailing whitespace prior to computing SHA-256 hashes for course notes, manifests, and lesson plans. Realizes UJ-1, UJ-5.
- **Consequences (testable):**
  - Git line-ending normalization (e.g. `core.autocrlf`) and cross-platform checkouts do not trigger false-positive tampering warnings in `hash_tracker.py` or `auditor.py`.
  - Verification succeeds consistently across Linux, macOS, and Windows.

#### FR-42: Universal Zero-Cognitive-Overload Pacing & Centralized Interaction Standards
All TextCourses skills, agents, and interactive flows SHALL adhere to strict cognitive lightness standards designed for any learner (from a 10-year-old child to seasoned professionals). Realizes UJ-1, UJ-2, UJ-6.
- **Consequences (testable):**
  - **Strict Single Question Invariant**: Interactive sessions MUST ask strictly ONE question or menu choice per turn, awaiting user response before proceeding. Bundling multiple questions or menus into a single message is strictly prohibited.
  - **10-Year-Old Plain English Standard**: All menu descriptions, personas, and prompts must be written in simple, scannable, jargon-free English easily comprehended by a 10-year-old.
  - **Dynamic Recommendation Indicators**: Every menu dynamically marks the most contextual choice with `(Recommended)` based on prior answers in the interaction.
  - **Related Decisions Scannable Summary**: When a workflow involves multiple related parts or decisions (e.g. multi-part refactoring or final onboarding recap), the system presents a single scannable summary at the end with simple short options so the user never has to scroll up and down repeatedly.
  - **Centralized Instruction Source of Truth**: All skills reference `_tc/INTERACTION_STANDARDS.md` to guarantee unified conversational behavior across the platform.

#### FR-43: Autonomous Multi-Source Deep Harvester & Community Consensus Sourcing (`tc-research`, `harvester.py`, `scout.py`)
The research engine spearheaded by **🔬 Marie Curie** SHALL autonomously discover, acquire, and ingest best-in-class, gold-standard learning materials from multiple authoritative channels before course creation. Realizes UJ-1, UJ-4, UJ-5.
- **Consequences (testable):**
  - **FR-43.1: Community Consensus & Gold-Standard Discovery**: Scans community recommendations and practitioner reviews (Reddit e.g. `r/learnprogramming`, `r/rust`, `r/datascience`, Hacker News, university reading lists) to determine the consensus gold-standard textbooks, authoritative guides, and landmark courses for the target domain. Compiles structured consensus records into `research/<slug>/gold-standards.md`.
  - **FR-43.2: Automated GitHub Repository & Open Textbook Harvester**: Searches GitHub for open-source repositories containing courseware, markdown textbooks, or authoritative reference implementations. Automatically clones or downloads repository contents into `research/<slug>/sources/repos/` and extracts table of contents hierarchies.
  - **FR-43.3: YouTube Lecture & Video Transcript Extractor**: Downloads and formats transcripts/subtitles from landmark YouTube lectures and courses into `research/<slug>/sources/transcripts/` using `yt-dlp` or timedtext APIs, cleaning timestamps into readable, annotated transcript blocks.
  - **FR-43.4: Graceful Fallback & Explicit Material Acquisition Gate**: If a gold-standard book is commercial/copyrighted and cannot be automatically downloaded, Marie explicitly informs the learner of the exact title, latest edition, and author, prompting them to place the file in `research/<slug>/sources/` or proceed with open web documentation.
  - **FR-43.5: Multi-Source Evidence Dossier Synthesis**: Ingests all harvested repositories, video transcripts, and user-provided source files into `research/<slug>/sources.json`, `research/<slug>/digest.json`, and `research/<slug>/dossier.md` for seamless consumption by `tc-create`.

#### FR-44: AI-Era Research Grounding & AI-Pro Hat Engine (`tc-research`, `scout.py`)
The research engine SHALL systematically investigate and document how the modern AI era transforms the domain, identifying what legacy practices are obsolete, what new AI-adjacent topics/tools must be integrated, and providing a dedicated AI-Pro critical hat for learner exploration. Realizes UJ-1, UJ-4, UJ-5.
- **Consequences (testable):**
  - **FR-44.1: Mandatory AI-Era Domain Analysis**: Every research dossier (`dossier.md`) and machine digest (`digest.json`) MUST include an AI-Era landscape section detailing:
    1. What has changed in the AI era for the subject (automated routine boilerplate vs. essential architectural focus).
    2. What AI-adjacent tools, libraries, models, or workflows should be included in discussion.
    3. AI hallucination failure modes and adversarial verification guardrails every practitioner must cultivate.
  - **FR-44.2: AI-Pro Critical Hat (`ai_pro_strategist`)**: A dedicated critical lens in the Universal Hat Registry evaluating LLM augmentation, agentic workflows, prompt/context ergonomics, and hallucination defense. Selectable via `--ai` or `--hats ai_pro`.
  - **FR-44.3: AI-Era Pedagogical Co-Design**: Downstream curriculum generation (`tc-create`) and instruction (`tc-teach`) ingest the AI-era landscape to weave modern AI-assisted problem solving, automated testing, and verification habits into course chapters.

---

## 5. Non-Goals (Explicit)

- **Not a Video/Audio Streaming Platform:** TextCourses will NEVER generate or host video lectures, audio voiceovers, or avatar animations in v1. Text and code are the primary medium.
- **Not a Mandatory Quiz Gate:** TextCourses will NEVER block a learner from advancing because they refused to answer a quiz. Active recall is always optional and user-sovereign.
- **Not a Cloud SaaS Platform in v1:** TextCourses will NEVER require cloud user accounts, remote database syncing, or proprietary servers. It is 100% local-first and filesystem-native.
- **Not a Cheat-Proof Testing Authority:** `tc-test-me` is a self-diagnostic tool for the learner, not a proctored, anti-cheat exam engine. We trust the learner.
- **Not a Copyright Violator:** TextCourses will NEVER scrape or ingest paywalled proprietary books without explicit user provision of legal local notes.

---

## 6. MVP Scope

### 6.1 In Scope (MVP)
- **8 User-Facing Commands:** `tc-init`, `tc-roadmap`, `tc-create`, `tc-teach`, `tc-test-me`, `tc-practicals`, `tc-redirect-course`, `tc-migrate`.
- **2 Internal Engine Skills:** `tc-research` and `tc-verify-course` (invoked via Triad Consensus Loop, and directly standalone).
- **The Sovereign Faculty:** 10 world-renowned master teacher personas with distinct teaching philosophies, adaptive density, and tag-team handoffs.
- **Two-Tier Pedagogical Memlog:** Global learner timeline (`profile/memlog.md`) and course-level session memory (`courses/<slug>/memlog.md`) via atomic `memlog.py`.
- **Streamlined Sovereign Filesystem Layout:** Visible `_tc/` (engine & cache), `roadmap/`, `profile/`, `courses/<slug>/notes/chapter-XX.md` (flat readable textbook), and `portfolio/<slug>-project/`.
- **5 Universal Curriculum Archetypes:** Fully selectable during course creation.
- **Automated Background Notes Compilation:** Guaranteed generation of flat textbook notes upon section completion.
- **4-Lens Project Review Pass:** Functional, Edge Cases, Craft, Verification Integrity.
- **Universal Safety Guardrail:** Hard refusal gate on weapons/CBRN, malware, NSFW, and illegal content across all skills.
- **Zero-Guessing Rule:** Direct clarification with numbered options + `Other` write-in option on ambiguity.

### 6.2 Out of Scope for MVP
- **Web UI / Graphical Dashboard:** Deferred to post-v1 community tools.
- **Multiplayer / Cohort Progress Syncing:** Peer synchronization deferred to v2.
- **Automated Spaced Repetition Scheduling:** Automated cron-based spaced repetition deferred to v2 (`tc-test-me` operates on-demand in v1).
- **Public Course Blueprint Registry (`textcourses.com`):** Cloud registry hosting deferred to v2.

---

## 7. Success Metrics & Counter-Metrics

### 7.1 Primary Metrics
- **SM-1 (Course Completion Rate):** $>45\%$ of created courses reach `completed` status across all chapters (validates FR-4, FR-9, FR-11). *Compared to industry MOOC standard of ~5-10%.*
- **SM-2 (Zero Ungrounded Syllabi):** $100\%$ of generated courses pass the Triad Consensus Loop with verified research or explicit user-acknowledged fallback before files are written to disk (validates FR-6, FR-7, FR-8).
- **SM-3 (Portfolio Verification Density):** $>80\%$ of completed courses contain at least one verified practical project deliverable passing the 4-Lens Review in `portfolio/` (validates FR-16, FR-17, FR-18).

### 7.2 Secondary Metrics
- **SM-4 (Context Token Efficiency):** Average tokens consumed per instructional turn remains $<4,000$ tokens regardless of total course size (validates FR-22).
- **SM-5 (Resumption Rate):** $>70\%$ of interrupted teaching sessions successfully resume from the latest checked concept in `lesson-plan.md` without restarting the section (validates FR-12).

### 7.3 Counter-Metrics (Do Not Optimize)
- **SM-C1 (Do Not Optimize for Pure Generation Speed):** Do not minimize time-to-create at the expense of Triad Consensus verification or learner curriculum co-design. High-friction, high-agency curriculum architecture is a desired design invariant.
- **SM-C2 (Do Not Optimize for Word Count):** Do not artificially expand `notes.md` word counts. High-density, scannable reference points are superior to verbose lecture transcripts.
- **SM-C3 (Do Not Optimize for Test Question Volume):** Do not bombard the user with quiz questions. One sharp diagnostic hinge question is superior to 10 trivia checks.

---

## 8. Constraints, Guardrails & Developer Contracts

### 8.1 Universal Safety Refusal Policy (Hard Guardrail)
Across all 9 skills, the system SHALL enforce an immediate refusal policy on topics involving:
1. Weapons creation, explosives, chemical/biological/radiological/nuclear (CBRN) hazards.
2. Malware authoring, exploitation frameworks, or active computer hacking instruction.
3. Sexually explicit, NSFW, or non-consensual content.
4. Illegal or illicit operations.
Permitted topics are strictly restricted to legitimate professional, academic, scientific, engineering, artistic, and practical educational domains.

### 8.2 Zero-Guessing & Low Cognitive Load Clarifications
Whenever an AI skill experiences ambiguity, doubt, or missing user context, it is **strictly forbidden from hallucinating or guessing**. It MUST prompt the learner directly with:
- Numbered, concise options covering the most likely intents.
- An explicit `[Other] (Write-in)` option.
- Minimal cognitive load (no essay questions).

### 8.3 CLI & Agent Public Surface Contracts
Each skill SHALL expose a consistent slash command interface and accept standardized arguments:
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

### 8.4 Empirical Decision Provenance & Audit Trail
The `.tc/cache/` directory SHALL retain all prompt logs, consensus reconciliation records, and research scrape metadata indefinitely. It SHALL NOT be deleted by standard operations, ensuring that agents always understand why historical curriculum and pedagogical decisions were made.

---

## 9. Open Questions & Resolutions

1. **[OQ-1] Schema Serialization (RESOLVED):** Manifests standardize on TOML (`course.toml`, `roadmap.toml`, `ledger.toml`) for human readability and config editing; append-only assessment logs standardize on JSONL (`test-ledger.jsonl`) for atomic, structured parsing.
2. **[OQ-2] Spaced Repetition Scheduling in v2 (RESOLVED):** v2 spaced repetition will rely strictly on local filesystem timestamp scanning in `test-ledger.jsonl` rather than an external background daemon, preserving local sovereignty and simplicity.
3. **[OQ-3] Offline Mode (RESOLVED):** In air-gapped environments, `tc-research` falls back to Tier 2 LLM training knowledge (explicitly marked `unverified`) or user-supplied local files in `plan/sources/`.

---

## 10. Assumptions Index

- **[ASSUMPTION: §4.1 / FR-1]**: Learners prefer structured numbered menus over open-ended intake prompts to reduce cognitive overhead.
- **[ASSUMPTION: §4.2 / FR-4]**: The 5 Curriculum Archetypes sufficiently cover the structural pedagogical models required across technical and non-technical domains.
- **[ASSUMPTION: §4.3 / FR-11]**: Background automated compilation of `notes.md` with instant progression preserves learner flow state while satisfying the knowledge permanence requirement.
- **[ASSUMPTION: §4.4 / FR-13]**: Question-based diagnostic testing without code copy-pasting is preferred by developers and modern learners who find chat code-pasting tedious.
- **[ASSUMPTION: §4.5 / FR-16]**: Medium defaults (intermediate complexity, weekend sprint budget, balanced depth/breadth) represent the ideal default intake for practical projects.
- **[ASSUMPTION: §4.7 / FR-22]**: Stage-aware context manifests enforced via explicit tool reads will keep token consumption within sustainable context budgets across arbitrarily large courses.
- **[ASSUMPTION: §8.4]**: Preserving `.tc/cache/` decision traces does not create noticeable disk bloat for text-based educational repositories.
