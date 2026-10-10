# Intent Document: TextCourses Framework (textcourses.com)
**A Sovereign, Domain-Agnostic, AI-Proof Learning Framework**

---

## 1. Executive Summary & Problem Space

### 1.1 The Core Dilemma in Modern Learning
Current self-directed learning in the age of generative AI faces two distinct failure modes:
1. **Traditional Online Platforms (Coursera, Udemy, etc.):** Rigid, one-size-fits-all curricula with zero context retention. They cannot adapt to an individual learner's unique background, pace, or roadblocks, and asking deep exploratory questions is frustrating or impossible.
2. **Generic AI Chatbots (ChatGPT, Claude, etc.):** Highly conversational but crippled by **ephemeral chat amnesia**, lack of persistent curriculum state, hallucinated progression, and passive consumption. Learners experience an illusion of competence ("the lecture wall") where passively reading AI explanations results in near-zero durable retention.
3. **Latency-to-Value & Tone Mismatch:** Waiting 5–8 seconds for an AI stream only to receive two simplistic, patronizing analogies frustrates advanced practitioners.

### 1.2 The Vision: TextCourses (`textcourses.com`)
**TextCourses** is a lightweight, domain-agnostic, filesystem-based AI learning framework. It transforms any local directory into a living, interactive digital textbook and persistent curriculum ledger. Operating across any domain—software engineering, quantitative finance, neurobiology, classical languages, jurisprudence, music theory, or philosophy—it gives learners sovereign control over their education.

### 1.3 The Strategic "AI-Proof" Moat
In a world where LLMs can generate infinite explanatory text for free, passive reading has zero defensibility. TextCourses establishes an AI-proof moat through:
- **Mandatory Structural Rigor:** Strict, standardized filesystem conventions (`.tc/`, `plan/`, `courses/`, `chapter-*`, `section-*`) and machine manifests (`course.toml`, `roadmap.toml`, `ledger.toml`).
- **Internal Framework Directory (`.tc/`):** All runtime caches, scraping logs, and operational data live in `.tc/`, keeping user-facing course directories clean and human-friendly.
- **The Triad Consensus Loop (`tc-create`):** An automated closed loop where the Architect (`tc-create`), Scout (`tc-research`), and Auditor (`tc-verify-course`) reconcile facts and prerequisites before writing files to disk.
- **Decoupled Pedagogical Blueprints (`lesson-plan.md`):** High-rigor teaching checklists are kept separate from the student's personal notes (`notes.md`), ensuring verified concept coverage during interactive sessions.
- **Substantial Single-Topic Modules & Predictable Next-Action Forks (`tc-teach`):** Sized and formatted to justify AI latency; strictly scoped to one topic with scannable formatting; closes with a friction-free `[1] Next`, `[2] Test`, `[3] Re-explain`, `[4] Custom` prompt.
- **Tangible Proof-of-Work Portfolios (`portfolio/`):** Completing courses yields verifiable, human-crafted artifacts (working code, case studies, financial models, written theses) certified by evaluation drills.

---

## 2. In-Depth Specifications: `tc-init`, `tc-create`, and `tc-teach`

### 2.1 `tc-init`: Frictionless, Selectable Onboarding & Style Preview
- **Identity & Topic**: Learner name and subject to master.
- **Background Taxonomy**: Selectable numbered options (Software Engineer, Fullstack, Data Scientist, Product Manager, Student/Researcher, Other write-in).
- **Domain Experience**: Beginner, Familiar with basics, Advanced practitioner.
- **Text Length & Explanation Density Selector**:
  - `Short & Sweet`: ~60–100 words/concept (High velocity, minimal tokens).
  - `Example-Driven`: ~150–200 words/concept (Balanced, real-world examples).
  - `Deep-Dive Technical`: ~250–350 words/concept (Comprehensive, internal mechanics, derivations).
- **Interactive Style Preview Picker**:
  - Displays side-by-side sample previews (Direct Technical [No Analogies], Analogy & Intuition, Code & Case-First, First-Principles Math).
  - Allows single selection or multi-selection (e.g. `A + C` -> *"Technical + Code-First, No Analogies"*), creating a tailored profile in `plan/preferences.md`.
- **Navigation Scanner**: Detects in-progress and review states across existing manifests to route learners directly to the next step.

### 2.2 `tc-create`: The Curriculum Architect
- **Operating Modes**:
  - `Interactive Mode`: Surfaces 4 key decision forks (Track Specialization, Depth vs Breadth, Discovered Sources Review, Draft Roadmap Approval).
  - `Automatic Mode`: Uses preferences and consensus defaults for instant generation.
- **5 Universal Curriculum Archetypes**:
  1. *Applied Creation ("Build from Scratch")*: Building one masterwork end-to-end.
  2. *Forensic Dilemma ("Incident & Autopsy")*: Case-based crisis diagnosis.
  3. *Axiomatic Primitives ("Bedrock Truths")*: Ground-up deductive construction from irreducible axioms.
  4. *Spiral Immersion ("Iterative Nuance")*: Multi-cycle broadening from conversational fluency to deep mastery.
  5. *Reverse Engineering (Backward Design / UbD)*: Professional outcome-driven scaffolding.
- **Triad Consensus Loop**: Cross-checks draft syllabus against `.tc/research/` official documentation via `tc-verify-course` before writing to disk.
- **Empirical Prompt Engineering in `lesson-plan.md`**: Curse of Knowledge inversion vocabulary contracts, Golden Path vs Fatal Trap pairs, 3-concept cognitive load caps, and self-explanation "Why" probes.

### 2.3 `tc-teach`: Conversational Delivery & Pacing
- **Substantial Single-Topic Modules**: Delivers a complete, intellectually rewarding explanation sized to justify AI generation latency, strictly bounded to one topic per message with high scannability.
- **The Standardized Next-Action Fork**:
  ```text
  Can we proceed to the next topic: [Next Topic Name]?
  [1] Yes, continue to next topic
  [2] Test me on this topic first (Diagnostic challenge)
  [3] Explain this differently / Give me another practical example
  [4] Custom question (Ask anything you want to clarify)
  ```
- **Mid-Session Persistence & Compaction**: Checkmarks in `lesson-plan.md` persist live; compiles conversations into permanent `notes.md` upon completion.

### 2.4 `tc-research`: Web Intelligence & 3-Tier Fallback
- Lightweight scraping via search + readability extractor (`trafilatura` or `r.jina.ai`) into `.tc/research/<slug>/`.
- 3-tier fallback: Mirrors/GitHub raw ➔ LLM verified benchmark synthesis ➔ Interactive local file prompt.

---

## 3. Directory Layout

```text
├── .tc/                                  # Internal runtime, caches & scraping data
│   ├── config.json                       # Framework metadata & local settings
│   ├── cache/                            # Ephemeral prompt and session caches
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
        ├── overview.md                   # Syllabus, prerequisites & high-level outcomes
        ├── portfolio/                    # Verifiable human proof-of-work artifacts
        └── chapter-01-core-concepts/
            ├── chapter-overview.md       # Chapter objectives & topic index
            ├── assignment.md             # Optional hands-on practical assignment
            └── section-01-fundamentals/
                ├── lesson-plan.md        # Teacher's checklist (AI only - never read by user)
                └── notes.md              # Distilled student textbook (post-completion)
```

---

## 4. The 8-Skill `tc-*` Suite

Installed via `npx skills add <github-url>/textcourses`:

| Skill | Category | Responsibility |
|---|---|---|
| **`tc-init`** | Navigation | Onboards fresh workspaces (with style preview picker) or analyzes existing manifests. |
| **`tc-create`** | Course | Generates roadmap, course manifest, chapter structures, and `lesson-plan.md` checklists via Triad Consensus. |
| **`tc-research`** | Web / Docs | Scrapes official documentation, tables of contents, and canonical curricula into `.tc/research/`. |
| **`tc-teach`** | Learner | Conducts live, topic-by-topic conversational lessons from `lesson-plan.md` with Next-Action Forks; compiles `notes.md`. |
| **`tc-verify-course`**| Course | Audits the curriculum for prerequisite jumps, missing edge cases, and structural integrity. |
| **`tc-test-me`** | Learner | Administers optional oral defense grilling, Socratic checks, quizzes, and evaluates practical assignments. |
| **`tc-redirect-course`**| Course | Detects newly added sources via `ledger.toml` and applies delta updates to upcoming lesson plans. |
| **`tc-migrate`** | Migration | Inspects workspaces for non-standard or legacy folder layouts and proposes structured migrations; **never modifies without explicit user approval**. |
