---
title: "Product Requirements Document: TextCourses (textcourses.com)"
status: "final"
created: "2026-10-10"
updated: "2026-10-10"
---

# PRD: TextCourses (textcourses.com)
**The Sovereign, Open-Source Autonomous Apprenticeship Engine**

---

## 0. Document Purpose

This Product Requirements Document (PRD) establishes the authoritative product, functional, and non-functional specifications for **TextCourses** (`textcourses.com`). It serves technical product managers, systems architects, skill prompt engineers, and downstream implementers. 

TextCourses synthesizes the prior [product-brief.md](file:///home/bharath/Documents/Code/text-courses-redesign/_bmad-output/initiative-textcourses/product-brief/product-brief.md), embodying decisions made during multi-lens elicitation. All requirements are anchored to the Glossary (§3) and numbered globally as stable references (`FR-1` through `FR-23`). Technical choices that belong strictly to implementation architecture live in downstream specifications (`bmad-architecture`).

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

#### FR-1: Frictionless Structured Intake
The system SHALL capture learner profile data through a multi-stage numbered intake covering Role Taxonomy, Domain Experience, and Explanation Density. Realizes UJ-1.
- **Consequences (testable):**
  - System presents exactly 5 predefined roles + `[6] Other (write-in)`.
  - System writes selected attributes into `plan/preferences.md` in valid Markdown frontmatter + body format.
  - Re-running `/tc-init` on an existing workspace displays current preferences with an option to retain or re-configure.

#### FR-2: Interactive Style Preview & Evolvable Profile Picker
The system SHALL display live comparative sample explanations across 4 standard pedagogical voices (Direct Technical, Analogy-Intuition, Code-First, First-Principles/Math) and allow single- or multi-select combination. Realizes UJ-1, UJ-2.
- **Consequences (testable):**
  - Multi-selection (e.g. `A + C`) compiles a compound style directive in `plan/preferences.md`.
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

## 5. Non-Goals (Explicit)

- **Not a Video/Audio Streaming Platform:** TextCourses will NEVER generate or host video lectures, audio voiceovers, or avatar animations in v1. Text and code are the primary medium.
- **Not a Mandatory Quiz Gate:** TextCourses will NEVER block a learner from advancing because they refused to answer a quiz. Active recall is always optional and user-sovereign.
- **Not a Cloud SaaS Platform in v1:** TextCourses will NEVER require cloud user accounts, remote database syncing, or proprietary servers. It is 100% local-first and filesystem-native.
- **Not a Cheat-Proof Testing Authority:** `tc-test-me` is a self-diagnostic tool for the learner, not a proctored, anti-cheat exam engine. We trust the learner.
- **Not a Copyright Violator:** TextCourses will NEVER scrape or ingest paywalled proprietary books without explicit user provision of legal local notes.

---

## 6. MVP Scope

### 6.1 In Scope (MVP)
- **7 User-Facing Commands:** `tc-init`, `tc-create`, `tc-teach`, `tc-test-me`, `tc-practicals`, `tc-redirect-course`, `tc-migrate`.
- **2 Internal Engine Skills:** `tc-research` and `tc-verify-course` (invoked via Triad Consensus Loop, and directly standalone).
- **Standardized Filesystem Layout:** `.tc/`, `plan/`, `courses/`, `portfolio/` with `course.toml`, `roadmap.toml`, `ledger.toml`, and `test-ledger.jsonl`.
- **5 Universal Curriculum Archetypes:** Fully selectable during course creation.
- **4 Pedagogical Style Voices:** Direct Technical, Analogy-Intuition, Code-First, First-Principles/Math.
- **Automated Background Notes Compilation:** Guaranteed generation of `notes.md` upon section completion.
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
