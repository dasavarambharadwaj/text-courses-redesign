---
title: "Product Brief: TextCourses Framework (textcourses.com)"
status: "complete"
created: "2026-10-10"
updated: "2026-10-10"
---

# Product Brief: TextCourses (textcourses.com)
**A Sovereign, Domain-Agnostic, AI-Proof Text-Based Learning Framework**

---

## Executive Summary

**TextCourses** (`textcourses.com`) is an open, filesystem-native learning framework that transforms any local workspace into an **Autonomous Apprenticeship Engine**. Moving beyond the industrial model of passive classrooms, it pairs lightweight AI skills with a customizable, learner-configured curriculum to provide the relentless milestone discipline of a master syllabus combined with the fluid, adaptive depth of 1-on-1 expert mentorship.

In an era saturated by free, commoditized AI text generation, passive reading has near-zero educational defensibility. TextCourses establishes an **AI-proof moat** through three core mechanics: **(1)** conversational single-topic teaching with adaptive style profiles tailored by the learner, **(2)** automated background distillation of every completed lesson into a permanent, personalized reference book (`notes.md`) before advancing, and **(3)** a malleable, learner-configured curriculum that the user actively shapes — not a one-shot AI dump. The filesystem hierarchy (`Roadmap` ➔ `Course` ➔ `Chapter` ➔ `Section`) serves as the apprentice's navigational compass, while `notes.md` acts as the workshop journal and `portfolio/` contains verifiable human proof of work.

All internal framework plumbing, web scrapings, decision traces, and runtime caches are sequestered cleanly in a hidden `.tc/` directory, keeping user-facing directories pristine while maintaining total explainability for agents. Course creation operates through a self-correcting **Triad Consensus Loop** (`tc-create` + `tc-research` + `tc-verify-course`) with confidence-scored research and systematic hallucination mitigation. Evaluation is cleanly separated between **pure question-based diagnostic testing (`tc-test-me`)** and **hands-on practical projects (`tc-practicals`)** evaluated across multiple objective review lenses. Every skill embeds hardwired safety guardrails, low-cognitive-load interaction patterns, and dynamic behavioral adaptation, keeping the learner in sovereign control. **The `tc-*` skills are AI-harness-agnostic** — they run in any environment that provides an AI agent with filesystem access: terminal CLI, VS Code / IDE extension, web wrapper, or any future surface. The terminal is one interface, not the only one.

---

## The Problem

Self-directed learners today are caught between two deeply flawed paradigms:

1. **The Static MOOC Trap (Coursera, Udemy, edX):**
   - **One-Size-Fits-All Rigidity:** Static video lectures that cannot adapt to an individual’s prior knowledge, personal pace, or specific technical background.
   - **Context Blindness:** When learners get stuck or have questions, they are thrown into unmoderated forums where keeping personal context is impossible.
   - **Abysmal Completion Rates:** Passive video consumption leads to boredom, distraction, and low retention.

2. **The Ephemeral AI Chat Trap (ChatGPT, Claude, Gemini):**
   - **Chat Amnesia & Bloat:** Long conversations quickly blow context windows or disappear into endless sidebar feeds with zero cumulative structure.
   - **The "Lecture Wall" Illusion:** Raw AI naturally outputs 500-word walls of text. Learners skim, nod along, and experience an illusion of competence, but retain almost nothing when asked to apply concepts.
   - **Lack of a Persistent Curriculum State:** Chatbots have no concept of syllabus milestones, prerequisites, or mastery ledgers.
   - **Latency-to-Value Deficit & Tone Mismatch:** Waiting 5–8 seconds for an AI stream only to receive two simplistic, patronizing analogies frustrates advanced practitioners.

3. **The AI Defensibility Void:**
   - Because anyone can prompt an AI to generate course notes in seconds, passive notes no longer demonstrate real-world competence to employers, peers, or the learners themselves.

---

## The Solution

TextCourses provides a structured, terminal/editor-native framework where learning is treated as a clean, progressive build pipeline:

```text
├── .tc/                                  # Internal runtime, caches & scraping data
│   ├── config.json                       # Framework metadata & local settings
│   ├── cache/                            # Decision traces, audit logs & empirical prompt caches (preserved for agent explainability)
│   └── research/                         # Scraped intelligence (ToCs, benchmarks)
│       └── <topic-slug>/
│           ├── metadata.json             # Search queries, URLs, timestamps
│           └── curriculum-digest.md      # Synthesized domain outline
├── plan/                                 # User-facing strategic cockpit
│   ├── roadmap.md                        # Macro learning trajectory
│   ├── roadmap.toml                      # Machine-readable status tracker
│   ├── preferences.md                    # Learner intake, background & style
│   └── sources/                          # Raw reference inputs & PDFs
│       └── ledger.toml                   # Cryptographic hash & ingestion tracker
└── courses/                              # Generated living textbook
    └── course-01-foundations/
        ├── course.toml                   # Course manifest & section status tracker
        ├── test-ledger.jsonl             # Persistent question-based assessment history
        ├── overview.md                   # Syllabus, prerequisites & high-level outcomes
        ├── portfolio/                    # Verifiable human proof-of-work artifacts
        │   └── project-01/               # Practical project deliverables & review reports
        └── chapter-01-core-concepts/
            ├── chapter-overview.md       # Chapter objectives & topic index
            └── section-01-fundamentals/
                ├── lesson-plan.md        # Teacher's checklist (AI only - never read by user)
                └── notes.md              # Distilled student textbook (post-completion)
```

---

## In-Depth Skill Specifications

TextCourses organizes its capabilities into 9 skills: **7 Primary User Commands** (directly driven by learner intent) and **2 Internal Pipeline Engine Skills** (`tc-research`, `tc-verify-course`). While the engine skills run automatically within pipelines like the Triad Consensus Loop, they remain **fully standalone and directly invokable** if the learner wishes to run dedicated deep research or execute independent curriculum audits manually.

### 1. `tc-init`: Frictionless, Selectable Onboarding & Navigation
`tc-init` manages workspace initialization and navigation. It deliberately avoids open-ended essay prompts (*"Describe your background..."*), employing a crisp, selectable intake:

1. **Learner Identity**: Name and target domain/skill to master.
2. **Background & Role Taxonomy**: Selectable numbered options with search/filter and an `Other` write-in option:
   - `[1]` Software Engineer (Backend / Systems / DevOps)
   - `[2]` Frontend / Full-Stack Developer
   - `[3]` Data Scientist / ML Engineer / Quant
   - `[4]` Product Manager / Technical Business Analyst
   - `[5]` Student / Academic Researcher
   - `[6]` Other (Custom write-in)
3. **Domain Experience Level**:
   - `[1]` Complete Beginner (Start from ground zero; focus on intuition)
   - `[2]` Familiar with Basics (Skip intro fluff; focus on core mechanics)
   - `[3]` Experienced Practitioner (Focus on internals, edge cases, deep architecture)
4. **Text Length & Explanation Density Selector (Transparent Token/Detail Trade-Offs)**:
   - `[1] Short & Sweet (High-Velocity / Minimal Tokens)`: ~60–100 words per concept; high density, compact analogies, zero fluff.
   - `[2] Example-Driven (Practical & Balanced)`: ~150–200 words per concept; concrete real-world code snippets, step-by-step walkthroughs, or case studies.
   - `[3] Deep-Dive Technical (Comprehensive & Academic)`: ~250–350 words per concept; exhaustive underlying mechanics, historical context, edge cases, and derivations.
5. **Interactive Style Preview & Custom Profile Picker**:
   - Displays live sample previews demonstrating how different voices explain a concept:
     - *Style A (Direct Technical & Internals)*: Architecture, Big-O, zero analogies.
     - *Style B (Analogy & Intuition)*: Metaphorical bridges for beginners.
     - *Style C (Code & Case-First)*: Practical implementation snippets and benchmarks.
     - *Style D (First-Principles & Math)*: Axioms, equations, and formal proofs.
   - Allows single selection or multi-selection (e.g. `A + C` -> *"Technical + Code-First, No Analogies"*), creating a tailored profile in `plan/preferences.md`.
   - **Evolvable Profiles:** The style profile is not static. At chapter boundaries, `tc-teach` may suggest profile adjustments based on observed interaction patterns (e.g., *"You've been asking for more technical depth — want to shift from 'Balanced' to 'Deep-Dive Technical'?"*). The learner approves or declines; `plan/preferences.md` is updated accordingly. The profile evolves with the learner.
6. **State-Scanner Navigation**: In an existing workspace, `tc-init` inspects all manifests, identifies sections in `review` or `in_progress`, and points the learner to the exact next action.

---

### 2. `tc-create`: The Curriculum Architect
`tc-create` transforms an intent (e.g. `/tc-create "Data Science from Scratch"`) into a structured course.

#### Operating Modes:
- **Interactive Mode**: Pauses at four major pedagogical decision forks:
  1. *Track Specialization*: e.g. Statistical ML vs Deep Learning vs Full Spectrum.
  2. *Depth vs Breadth*: Pragmatic Practitioner (6 high-velocity chapters) vs Rigorous Foundations (12 chapters).
  3. *Source Review*: Shows discovered research from `tc-research` and allows adding personal notes/PDFs.
  4. *Roadmap Approval*: User reviews, re-orders, renames, or prunes chapters before files are generated.
- **Automatic Mode**: Reads `plan/preferences.md`, dispatches `tc-research` in the background, applies industry-standard consensus defaults, and writes the curriculum without intermediate prompts.
- **User-Supplied Curriculum Input**: At any point during creation, the learner can supply a **reference course** (URL, course name, or syllabus link) or **paste a chapter-level curriculum** directly. `tc-create` uses this as a structural scaffold — adapting, reordering, or expanding it based on the learner's preferences and `tc-research` intelligence — rather than generating a curriculum from scratch.

#### The 5 Universal Curriculum Archetypes (Domain-Agnostic):
1. **Applied Creation ("Build from Scratch")**: Structured around building one ambitious, working artifact from start to finish (e.g. build an in-memory database, draft a novella, compose a jazz fugue).
2. **Forensic Dilemma ("Incident & Autopsy")**: Every chapter begins with an unsolved real-world failure or crisis (e.g. a $400M trading glitch, a medical diagnostic mystery, an aircraft engineering failure). Concepts are taught as diagnostic tools.
3. **Axiomatic Primitives ("Bedrock Truths")**: Strips all high-level shortcuts; starts from irreducible physical, logical, or mathematical axioms and builds deductively (e.g. logic gates, epistemological axioms, music overtone series).
4. **The Spiral Immersion ("Iterative Nuance")**: Bruner's Spiral model: Cycle 1 achieves functional fluency; Cycle 2 re-visits with technical precision; Cycle 3 re-visits with advanced edge cases.
5. **Reverse Engineering (Backward Design / UbD)**: Starts with the real-world professional capability or assessment rubric, reverse-engineering the minimum viable mastery path without fluff.

#### The Triad Consensus Loop:
Before writing to disk, `tc-create` executes a closed-loop consensus cycle:
- `tc-create` (Architect) drafts the syllabus.
- `tc-research` (Scout) supplies verified documentation from `.tc/research/`.
- `tc-verify-course` (Auditor) audits the draft against the research for prerequisite leaps, deprecated syntax, or gaps.
- They reconcile and converge; files are written to `courses/` only upon zero critical audit findings.

#### Evidence-Based Prompt Engineering in `lesson-plan.md`:
- **Curse of Knowledge Inversion**: Vocabulary contract forbidding technical terms that were not previously defined.
- **Worked Example + Fatal Anti-Pattern**: Every concept pairs the Golden Path with the Fatal Mistake.
- **Cognitive Load Ceiling**: Capped at 3–5 micro-concepts per section, delivered one at a time.
- **Metacognitive "Why" Probes**: Embeds self-explanation questions forcing semantic encoding.

---

### 3. `tc-teach`: Conversational Tutor & Pacing Engine
`tc-teach` is the core instructional delivery engine:

1. **Substantial Single-Topic Modules**:
   - Delivers a complete, intellectually rewarding explanation sized to justify AI generation latency.
   - Strictly bounded to **one topic per message** with high scannability (short paragraphs, bolded mechanics, formatted code/tables).
   - Adheres strictly to the learner's style profile (e.g. no simplistic analogies if the user selected *Technical Direct*).
2. **The Standardized Next-Action Fork (Every Turn)**:
   - Closes every explanation with an explicit, numbered choice:
     ```text
     Can we proceed to the next topic: [Next Topic Name]?
     [1] Yes, continue to next topic
     [2] Test me on this topic first (Diagnostic challenge)
     [3] Explain this differently / Give me another practical example
     [4] Custom question (Ask anything you want to clarify)
     ```
   - Typing `1` maintains maximum learning velocity; typing `2` triggers active recall.
3. **Mid-Session Persistence & Compaction**:
   - Toggles checkmarks in `lesson-plan.md` live so sessions survive interruptions.
   - **Automated Notes Compilation (Flow-Preserving Gate):** Upon completing the final concept in a section, `tc-teach` automatically distills the teaching discussions into permanent `notes.md` in the background (operating autonomously). It writes the file to disk, presents a concise recap, and keeps the learner in uninterrupted flow: the learner can advance immediately via `[1] Next Topic`, test with `[2] Test Me`, or optionally tweak the notes. Advancement requires `notes.md` to exist on disk, but never blocks the learner behind tedious bureaucratic approval.
   - **Notes Distillation Quality Spec:** `notes.md` is structured around the `lesson-plan.md` concept checklist — every checked concept maps to a concise, scannable reference entry matching the learner's style profile.
   - Updates `course.toml` to `status: review` and presents the Next-Action Fork.
4. **Session Hygiene:** Each `tc-teach` session should target **one section** (not marathon multi-section runs). Fresh sessions prevent AI instruction drift and context degradation. Checkmarks in `lesson-plan.md` ensure seamless resumption across sessions.

---

### 4. `tc-test-me`: 100% Question-Based Conceptual Testing & Ledger
- **Zero Code Copy-Pasting**: `tc-test-me` never asks learners to paste code into chat.
- **Diagnostic Scenarios & Hinge Questions**: Focuses strictly on testing mental models, mechanism trade-offs, and boundary failure modes through targeted scenario questions.
- **Persistent Test Ledger (`courses/<slug>/test-ledger.jsonl`)**: Records every question asked, learner answer, diagnosed misconceptions, and score. Subsequent sessions read this ledger to reinforce past weaknesses.
- **The Cumulative Boundary Rule**: Strictly tests only concepts from completed sections, preventing future concept leaks.

---

### 5. `tc-practicals`: Real Projects with Multi-Lens AI Verification
Dedicated hands-on workshop for course-level project application:

1. **Intake & Scope Customization**:
   - Asks learner preferences with **Medium defaults**:
     - *Complexity*: Beginner / Intermediate (Medium - default) / Advanced
     - *Time Budget*: 1-2 hours / Weekend sprint (default) / Multi-week capstone
     - *Depth & Breadth*: Focused deep-dive / Balanced full-stack (default) / Broad multi-system
   - **User Custom Project Ideas**: If the user already has an idea (*"I want to build a crypto arbitrage bot"*), `tc-practicals` adapts to their intent and builds a tailored, structured project spec around it!
   - **Diagnostic-Informed Weighting**: When `test-ledger.jsonl` exists, `tc-practicals` reads the rolling misconception summary and optionally weights project exercises toward areas where the learner has shown recurring weaknesses — turning diagnostic data into targeted applied practice.
2. **Verifiable Deliverables in `portfolio/`**:
   - Writes a project specification (`portfolio/project-01/project-spec.md`) specifying only deliverables an AI can deterministically verify (working code, passing test suites, schemas, formatted memos).
3. **Multi-Lens Review Pass (The BMad Review Pattern)**:
   - Evaluates deliverables across **four parallel objective lenses**:
     - *Lens 1: Functional Completeness* (all requirements met)
     - *Lens 2: Edge Cases & Robustness* (error handling, boundary values)
     - *Lens 3: Architecture & Craft* (clean structure, idiomatic design)
     - *Lens 4: Verification Integrity* (test coverage, passing test runners)
   - Outputs a structured review report and marks the course/chapter `completed`.

---

### 6. `tc-research`: Web Intelligence & Scraping Scout
- **Lightweight Pipeline**: Uses headless search and readability extraction (via `trafilatura` or markdown proxy reader `r.jina.ai`) to extract structured Tables of Contents, API indices, and syllabus benchmarks into `.tc/research/<slug>/`.
- **3-Tier Failure Fallback**:
  1. *Tier 1 (Alternative Mirrors / GitHub Repos)*: Tries official mirrors, awesome-lists, or raw GitHub docs. Tagged `verified` in `metadata.json`.
  2. *Tier 2 (LLM Internal Benchmark Synthesis)*: Synthesizes canonical syllabus from model training knowledge. Explicitly tagged `unverified` in `metadata.json` with a disclaimer log. `tc-verify-course` applies **heightened scrutiny** to any curriculum section grounded in unverified sources.
  3. *Tier 3 (User Ingestion Prompt)*: In interactive mode, prompts learner to provide a local file or proceed with defaults.
- **Confidence Scoring & Escalation**: Every research output carries a confidence score (`high` / `medium` / `low`) in `metadata.json`. When overall confidence drops below `medium` (e.g., Tier 1 failed and Tier 2 produced sparse results), `tc-research` **forces interactive user review** rather than silently passing low-confidence data to the Triad Consensus Loop.

---

### 7. `tc-verify-course`: Independent Curriculum Auditor
- Acts as the adversarial reviewer in the Triad Consensus Loop.
- Scans `lesson-plan.md` files for prerequisite DAG violations, obsolete syntax, or gaps before course creation or course redirection is committed to disk.

---

### 8. `tc-redirect-course`: Course Change Manager
- Detects newly added or modified source materials in `plan/sources/` using cryptographic hashes in `ledger.toml`.
- Assesses impact strictly on unfinished (`not_started` and `in_progress`) chapters, leaving completed work intact.
- **Completed Lesson Immutability (Hard Rule):** Completed sections and their `lesson-plan.md` / `notes.md` are **never edited, rewritten, or retroactively modified**. If new material is relevant to a completed topic, `tc-redirect-course` may only **append new sections or sub-topics after the existing completed content** — never alter what the learner already finished.
- **Deprecation Markers (Non-Destructive):** When new material supersedes content in a completed section, `tc-redirect-course` may append a non-destructive deprecation header to the top of the completed `notes.md` (e.g., `> ⚠️ Some content in this section has been superseded by Section 8.3 — see updated coverage there.`). The body of the notes remains untouched; only the annotation header is added.
- Runs `tc-verify-course` on the changes and presents an interactive before/after proposal before applying edits.

---

### 9. `tc-migrate`: Workspace Health & Safe Migration Engine
- Inspects repositories for non-canonical or legacy directory layouts.
- Previews transparent migration plans (`migration-plan.md`) with explicit file maps.
- **The Golden Rule**: Strictly requires explicit user confirmation before moving or modifying any files.

---

## Universal Operational Principles Across All Skills

1. **Generic, Steerable Prompt Design**: Skill system instructions are fully steerable by user prompts. The filesystem structure (`.tc/`, `plan/`, `courses/`) is the only rigid invariant.
2. **Systematic Hallucination Mitigation & Low Cognitive Load Clarifications**: No LLM system can guarantee zero hallucinations. TextCourses mitigates this through the Triad Consensus Loop, confidence-scored research, and explicit `unverified` source tagging as defense-in-depth. When an AI skill experiences ambiguity or doubt, it is **strictly forbidden from guessing**. It must ask the user directly using numbered, scannable options + an `Other` write-in option, eliminating cognitive overload.
3. **Dynamic Context & Behavioral Pattern Learning**: Skills read patterns from the learner's ongoing interactions (response latency, areas of friction, preference for code vs. concepts) and dynamically calibrate pacing, vocabulary, and check questions in subsequent sessions.
4. **Universal Safety & Professional Guardrails**: Hard policy gate across all 9 skills refusing topics related to weapons/CBRN, malware/exploits, sexually explicit/NSFW material, or illegal operations. Restricted strictly to legitimate professional, academic, scientific, and practical educational skills.
5. **Context Engineering & Stage-Aware Loading**: Each `tc-*` skill defines a **context loading manifest** — a specification of exactly which files to load fully, which to summarize, and which to skip, based on the skill's current operational stage. This prevents context window blowout on large courses and ensures every token of context is purposeful:
   - `tc-teach` (teaching a section): Loads current `lesson-plan.md` (full), `plan/preferences.md` (full), current chapter's prior `notes.md` (summary), `test-ledger.jsonl` (rolling misconception summary, not raw JSONL). Skips all other chapters.
   - `tc-create` (building curriculum): Loads `plan/preferences.md` (full), `.tc/research/` digests (full), existing `course.toml` manifests (full). Skips all `notes.md` and `lesson-plan.md` files.
   - `tc-test-me` (testing): Loads completed `notes.md` for tested sections (summary), `test-ledger.jsonl` (full — needs misconception history), `plan/preferences.md` (full). Skips `lesson-plan.md` and research data.
   - `tc-verify-course` (auditing): Loads all `lesson-plan.md` files (full), `.tc/research/` (full). Skips `notes.md`, `test-ledger.jsonl`, and preferences.
   - `tc-practicals` (project generation): Loads `course.toml` (full), completed `notes.md` (summary), `plan/preferences.md` (full). Skips lesson plans and test ledgers.
   - Other skills follow the same principle: **load only what the current stage needs**.
   - **Enforcement:** Context manifests are enforced at the prompt instruction level. Implementations should use **structured tool calls** (explicit file reads by path) rather than glob-loading entire directories, providing a programmatic enforcement surface where possible.
6. **AI-Harness Agnosticism**: All `tc-*` skills are surface-agnostic. They run in any environment providing an AI agent with filesystem access — terminal CLI, IDE extension, web wrapper, or future interfaces.

---

## What Makes This Different (The AI-Proof Moat)

| Dimension | Generic AI Chat / MOOCs | TextCourses (`textcourses.com`) |
|---|---|---|
| **Learning Mode** | Passive video watching / text walls | Substantial single-topic deep dives with scannable layout |
| **Pacing Control** | Unstructured chat drift or auto-play | Predictable Next-Action Fork (`[1] Next`, `[2] Test`, `[3] Re-explain`) |
| **Testing Experience** | Boring code copy-pasting into chat | **100% question-based** diagnostic testing with `test-ledger.jsonl` |
| **Practical Projects** | None or unverified toys | Dedicated `tc-practicals` with **4-lens AI review** in `portfolio/` |
| **Teaching Style** | Generic one-size-fits-all voice | Live Style Preview Picker with multi-select custom hybrid profiles |
| **Quality Control** | Single-shot prompt generation | Pre-flight Triad Consensus Loop (`tc-create` + `tc-research` + `tc-verify-course`) |
| **Sovereignty & Governance**| Cloud platform lock-in | 100% local filesystem with explicit user approval for migrations |
| **State & Memory** | Amnesic after chat close | Machine-readable manifests (`course.toml`, `ledger.toml`, `.tc/`) |
| **Safety Invariants** | Uncontrolled or arbitrary refusals | Hardwired professional educational guardrail policy |
| **Knowledge Artifact** | No persistent output / generic AI dump | Mandatory learner-approved `notes.md` per section — a personalized textbook shaped by interaction, not a copy-paste |

---

## Who This Serves

### Primary Persona: The Deep Autonomous Learner
- **Profile:** Software engineers, data scientists, researchers, career switchers, and technical professionals who need to master complex, high-stakes topics (Distributed Systems, Rust, Machine Learning Internals, Corporate Finance, etc.).
- **Core Need:** Wants structured, exhaustive curricula without fluff, with total control over pacing, notes, and practical challenges.
- **Success Outcome:** Finishes a course in weeks rather than months, possessing a comprehensive personal textbook (`notes.md`) and a portfolio of completed projects.

### Secondary Persona: The Technical Mentor / Team Lead
- **Profile:** Engineering managers, senior architects, or educators onboarding new developers or junior analysts.
- **Core Need:** Wants to provide team members with a standardized, reproducible learning repository grounded in official documentation and internal company guides.
- **Success Outcome:** New hires run `tc-init`, follow a verified roadmap, and demonstrate competence through local portfolio artifacts.

---

## Success Criteria

1. **Pedagogical Freedom & Retention:** Learners retain high engagement through conversational learning, enjoying full freedom to engage in optional active-recall probes without feeling trapped in rigid quizzes.
2. **Curriculum Rigor & Systematic Hallucination Mitigation:** 100% of generated courses pass the Triad Consensus Loop with confidence-scored research before user presentation, systematically mitigating obsolete APIs, prerequisite leaps, and ungrounded claims through layered defense-in-depth.
3. **Verifiable Practical Mastery:** Learners produce high-quality, authentic deliverables in `portfolio/` verified across 4 objective review lenses by `tc-practicals`.
4. **Workflow Adherence & Reliability:** Zero corrupted workspaces: skills enforce sequence preconditions, preventing out-of-order execution, while `tc-migrate` ensures 100% schema compliance under user consent.
5. **Token & Context Efficiency:** Course execution uses <25% of the token overhead of naive all-in-one chat sessions due to delta source reading (`ledger.toml`) and session compaction.

---

## Scope

### In Scope (MVP)
- **9 Canonical Skills:** `tc-init`, `tc-create`, `tc-research`, `tc-teach`, `tc-verify-course`, `tc-test-me`, `tc-practicals`, `tc-redirect-course`, and `tc-migrate`.
- **Precondition & Sequence Guardrails:** Built-in validation in every skill ensuring proper execution sequence.
- **Mandatory Filesystem Layout:** Standardized directory hierarchy (`.tc/`, `plan/`, `courses/`, `portfolio/`) with machine manifests.
- **The Triad Consensus Loop in `tc-create`:** Automated author-research-auditor loop.
- **Multi-Lens Project Evaluation in `tc-practicals`:** 4-lens review pass for portfolio deliverables.
- **Persistent Assessment Tracking:** `test-ledger.jsonl` tracking all diagnostic questions and responses.
- **Universal Safety Guardrails:** Hard policy gate rejecting non-educational or hazardous topics.
- **Package Distribution:** Packaged as an installable skill repository compatible with `skills-lock.json`.

### Explicitly Out of Scope (MVP)
- **Cloud SaaS Web Dashboards:** Framework remains strictly local-first and editor/CLI-native.
- **Mandatory Quiz Gates:** Active recall probes are never blockers; progression is always user-sovereign.
- **Synchronous Multiplayer Classrooms:** Focused on single-learner mastery; peer cohort syncing is deferred.
- **Automated Video/Audio Narration:** Text and code remain the primary, distraction-free medium.
- **Proprietary Paywalled Book Ingestion:** Respects copyright; relies on official web documentation, open syllabi, and user-provided notes.

---

## Vision (2–3 Years)

If TextCourses succeeds, it becomes the **open standard for sovereign, AI-assisted self-education**:
- **Community Blueprint Registry (`textcourses.com`):** A public registry where expert engineers and educators share vetted roadmaps, course blueprints, and practical rubrics (e.g. *"Canonical Distributed Systems Blueprint"*).
- **Verifiable Proof-of-Work Portfolios:** Local course completion bundles can be cryptographically signed or published to GitHub/web as verified portfolios, serving as unassailable proof of technical mastery for hiring and credentials.
