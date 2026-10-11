# TextCourses 2.0: Personality-Driven Apprenticeship & Macro Architecture
## Synthesis of Brainstorming Findings & Strategic Intent

### 1. Executive Summary & Purpose
This intent document crystallizes the strategic evolution of the TextCourses framework from a single-course deterministic engine into **TextCourses 2.0: A Sovereign, Personality-Driven Apprenticeship Platform**. It resolves five critical defects identified in the v1 prototype:
1. **Macro-Curriculum Blindness**: Replaced with multi-course **Roadmaps** and live **Triad Party Mode Inception**.
2. **Clinical Onboarding Sliders**: Replaced with direct **Teacher Personality Selection** (The Sovereign Faculty).
3. **Session Amnesia**: Replaced with a **Two-Tier Pedagogical Memlog** capturing conversational breakthroughs and taught concepts.
4. **Cognitive Folder Friction**: Replaced with a clean, unified, human-navigable workspace layout.
5. **Skill Ecosystem Asymmetry**: Replaced with full **BMad Standard Parity** (`customize.toml`, `bmod.toml`, and unified scripts).

---

### 2. Core Pillars & Detailed Requirements

#### Pillar 1: The Sovereign Faculty (Teacher Personality Selection)
- **Elimination of Clinical Sliders**: Onboarding no longer forces learners to choose word counts (60–100 words vs. 250–350 words) or abstract style tags (`direct_technical`, `analogy_intuition`).
- **Direct Persona Hiring**: In `/tc-init`, Chiron introduces a Faculty Roster of world-renowned master teachers:
  - **⚡ Feynman (The Intuitive Builder)**: High-energy, analogy-first, mechanical intuition, allergic to jargon.
  - **📐 Euclid (The Axiomatic Purist)**: Direct, mathematically rigorous, proofs from first principles, code-first.
  - **🦉 Socrates (The Dialectic Inquisitor)**: Probing, questions over answers, isolates contradictions.
  - **🎨 Leonardo (The Master Craftsman)**: Workshop builder, demanding proof-of-work, rigorous 4-lens reviews.
- **Adaptive Faculty Tag-Team Handoff**:
  - When a learner clicks `[3] Re-explain / Deeper` twice on a single concept, the tutor detects conceptual friction.
  - The Next-Action Fork surfaces an adaptive faculty handoff option (e.g., *"⚡ Call in Feynman for an intuitive analogy"* or *"📐 Call in Euclid for a formal state trace"*).
  - Teacher B steps in acknowledging Teacher A's prior explanation, using context from `memlog.md`.
  - The handoff is atomically logged to `courses/<slug>/memlog.md`.
  - Learners can switch their primary teacher dynamically, persisted to `profile/preferences.md`.

#### Pillar 2: Macro Roadmaps & Triad Inception Party Mode
- **The Domain Inception Problem**: Broad fields like Data Science, Distributed Systems, or Compilers cannot be compressed into a single course. They require a multi-course sequence.
- **Dedicated Skill (`tc-roadmap`)**:
  - Orchestrated by **🗺️ Aristotle (The Cartographer)**.
  - Coordinates a live **Triad Inception Roundtable (Party Mode)**:
    - **🔬 Marie (The Empirical Scout)**: Evaluates current technical landscape, official documentation, and modern industry standards.
    - **🗺️ Aristotle (The Cartographer)**: Maps the macro sequence, courses, and dependency DAG.
    - **⚖️ Hypatia (The Logic Auditor)**: Audits prerequisite contracts, identifying circular dependencies or cognitive leaps.
  - **Live Diagnostic Placement**: The Triad generates 3 targeted hinge questions to probe the learner's baseline.
  - **Automatic Course Waiving**: Prior proficiencies are marked as `[WAIVED]` in `roadmap/roadmap.toml`, identifying the optimal starting course (`[ACTIVE]`).
  - Seamlessly dispatches `tc-create` to scaffold the first active course.

#### Pillar 3: Two-Tier Pedagogical Memlog
- **Global Learner Timeline (`profile/memlog.md`)**:
  - Tracks high-level milestones across all courses, track certifications, and faculty handoffs.
- **Course Pedagogical Memory (`courses/<slug>/memlog.md`)**:
  - Append-only chronological trace managed by `_tc/scripts/memlog.py`.
  - Structured pedagogical vocabulary:
    - `- (concept by <Teacher>) <Exact mechanism and invariant taught>`
    - `- (question by user) <Query or edge case raised by learner>`
    - `- (insight by user) <Learner breakthrough or mental model connection>`
    - `- (misconception) <Confusion identified during dialogue or testing>`
    - `- (analogy by <Teacher>) <Specific metaphor that clicked>`
    - `- (handoff) <Teacher A handed off to Teacher B with rationale>`
    - `- (milestone) <Section completed, test passed, or project reviewed>`
- **Turn Context Injection**: `/tc-teach` reads the trailing 15 lines of `memlog.md` on resume, guaranteeing conversational memory across sessions without blowing token budgets.

#### Pillar 4: Streamlined Sovereign Folder Architecture
- **Elimination of Dot-Folder Ambiguity**: Merge `.tc/` into `_tc/`. All runtime scripts, caches, and internal configurations reside visibly in `_tc/`.
- **Top-Level Clean Hierarchy**:
  ```text
  <workspace>/
  ├── _tc/                          # Engine: scripts, cache, config.json
  ├── roadmap/                      # Macro curriculum: roadmap.toml, overview.md
  ├── profile/                      # Learner preferences.md & global memlog.md
  ├── courses/
  │   └── <course-slug>/
  │       ├── course.toml           # Course manifest & section DAG
  │       ├── syllabus.md           # Human-readable syllabus
  │       ├── test-ledger.jsonl     # Diagnostic quiz logs
  │       ├── memlog.md             # Turn-by-turn pedagogical memory
  │       ├── notes/                # FLAT HUMAN-READABLE TEXTBOOK
  │       │   ├── chapter-01.md     # Consolidated chapter notes
  │       │   └── chapter-02.md
  │       └── chapters/             # AI instructional lesson plans
  │           └── ch01-basics/
  │               ├── sec01-wal.md
  │               └── sec02-memtable.md
  └── portfolio/
      └── <course-slug>-project/    # Verifiable deliverable repo
          ├── project-spec.md
          ├── review-report.md
          ├── src/
          └── tests/
  ```

#### Pillar 5: Complete BMad Standard Parity
- **Full Metadata Packaging**: Equip all 10 skills with `bmod.toml` declaring dependencies, versions, and sources.
- **Customization Cascades**: Add `customize.toml` to every skill with agent personas, icons, principles, and interactive menus.
- **Script Consolidation**: Eliminate script triplication across `skills/tc-*/scripts/`. All skills invoke the canonical scripts located strictly in `_tc/scripts/`.

---

### 3. Downstream Transition
This intent document serves as the direct specification input for:
1. `bmad-prd`: Generating the formal PRD for TextCourses 2.0.
2. `bmad-architecture`: Updating `architecture-textcourses.md` to record the new folder schemas and DAG APIs.
3. `bmad-ticket`: Slicing the PRD into epics, stories, and executable implementation tasks.
