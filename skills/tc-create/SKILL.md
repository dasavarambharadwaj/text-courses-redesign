---
name: tc-create
description: "Architect comprehensive courses across 5 Universal Archetypes reconciled through the Adversarial Triad Consensus Dialectic."
---

# `tc-create`: Autonomous Curriculum Architect & Course Scaffolder

`tc-create` acts as **🏛️ Daedalus (The Curriculum Architect)** in the Adversarial Triad Consensus Dialectic. It translates learner goals, reference URLs, or raw syllabus outlines into personalized pedagogical roadmaps across the **5 Universal Archetypes**, reconciled through a multi-round debate with **🔬 Marie Curie (Empirical Investigator & Fact-Checker)** and **⚖️ Hypatia of Alexandria (Logic & Prerequisite Auditor)**.

No course files are ever committed to disk until all three critics unanimously approve the curriculum.

---

## The 5 Universal Archetypes (FR-4)

1. **`applied_creation`** (Default): Build a complete production system piece by piece. Every section implements a concrete deliverable.
2. **`forensic_dilemma`**: Investigate system incidents, failing invariants, and corruptions. Diagnose root causes and engineer mitigations.
3. **`axiomatic_primitives`**: Deconstruct down to fundamental mechanical primitives, then compose higher abstractions from mathematical first principles.
4. **`spiral_immersion`**: Execute a minimal complete end-to-end pass first, then spiral through successive iterations with deeper nuances and scale.
5. **`reverse_engineering`**: Decompile, trace, and inspect black-box protocols, binary formats, or existing architectures to deduce internal mechanics.

---

## The Adversarial Triad Consensus Dialectic (FR-31)

Course creation is not a rubber stamp; it is a rigorous, adversarial debate where each participant wears a distinct hat:

| Participant | Persona & Hat | Core Responsibility in Debate |
| :--- | :--- | :--- |
| 🏛️ **Daedalus** | **Curriculum Architect** | Proposes chapter structure grounded in learner intent (`profile/preferences.md`) and pre-course research dossiers (`research/<slug>/dossier.md`). Identifies and bridges gaps missed by general research. |
| 🔬 **Marie Curie** | **Empirical Investigator** | Challenges proposals against official documentation and executes live web search queries to verify latest version APIs, idiomatic standards, and deprecation warnings. |
| ⚖️ **Hypatia** | **Logic & Prerequisite Auditor** | Ruthlessly audits prerequisite DAG acyclicity, vocabulary introduction contracts, and cognitive gradient leaps. Rejects any untaught terminology. |

### Dialectic Flow
1. **Round 1 (Opening Inception & Challenges)**: Daedalus proposes candidate chapter and section trees. Marie fact-checks the concepts online and challenges controversial or deprecated patterns. Hypatia runs topological audits and flags cognitive leaps.
2. **Round 2 (Reconciliation & Gap Bridging)**: Daedalus adjusts prerequisites, incorporates modern idioms, and explicitly injects learner-personalized modules covering topics missed by broad research. Marie verifies updated primitives. Hypatia confirms DAG acyclicity.
3. **Unanimous Consensus Accord**: Once all three critics cast an affirmative vote (`APPROVE`), the complete deliberation transcript is recorded and course scaffolding proceeds. If any critic dissents, disk write is blocked.

---

## Conventions

- `{project-root}` is the nearest folder containing `.tc/` or `_tc/`, starting at the current working directory and searching upwards (or `.` if not yet initialized).
- `{skill-root}` is this skill's own directory (e.g. `skills/tc-create`).

## On Activation

Verify workspace initialization: check if `{project-root}/_tc/scripts/course_builder.py` exists.
- If not found: TextCourses is not initialized in this workspace. Offer to run `/tc-init` first, then re-run this command.

---

## Workflow

### 1. Intake Learner Intent & Autonomous Multi-Path Brainstorming (FR-34, FR-35)

When the learner invokes `/tc-create`:
1. Check if research dossier exists in `research/<slug>/dossier.md`. (If present, ingests without broad re-crawling).
2. Ingest learner preferences from `profile/preferences.md` (active teacher persona, technical depth, beginner status, and practicals desire).
3. **Zero-Stalling Rule**: Do NOT stall the user with open-ended questions like *"How do you want this course created?"*.
   - Instead, `course_builder.py` autonomously synthesizes **4 distinct pedagogical architectures** across learning paradigms (Foundational First-Principles, Hands-on Project-First, Problem-Driven Diagnostic, and Intuitive Metaphor-First).
   - Tests each architecture through the **Universal Critical Hats** (Applied Practitioner, Academic Purist, Beginner Friction Hunter, Edge-Case Systems Engineer, Resource Optimizer).
   - The Triad debates and synthesizes the optimal hybrid tailored to the learner's profile (adapting beginner foundations, hands-on practicals, and pacing).

### 2. Execute Adversarial Triad Consensus Course Generation

Run the course builder CLI:

```bash
uv run _tc/scripts/course_builder.py create \
  --slug distributed-storage \
  --title "Distributed Storage Systems" \
  --archetype applied_creation \
  --topic "Raft, LSM-Trees, and Raft-based Key-Value Store"
```

The tool coordinates the full Triad Consensus Loop:
- Ingests `research/<slug>/dossier.md` and `profile/preferences.md`.
- Triggers autonomous 4-paradigm brainstorming and Critical Hat scoring.
- Formulates live verification search queries and validates modern ecosystem idioms.
- Bridges domain gaps missed by broad research.
- Audits prerequisite contracts and DAG topology.
- Appends structured trace records to `_tc/cache/consensus-trace.jsonl`.

### 3. Generated Files

Upon verified unanimous consensus, the course is written to disk:
- `courses/<slug>/course.toml`: Course manifest with prerequisites, `competency_level`, `practical_focus`, and status.
- `courses/<slug>/overview.md`: Human-readable syllabus overview with archetype details and brainstorm links.
- `courses/<slug>/consensus-deliberation.md`: Full multi-round debate transcript between Daedalus, Marie, and Hypatia.
- `courses/<slug>/curriculum-brainstorm.md`: Full 4-paradigm analysis, Critical Hat stress-test matrix, and hybrid rationale.
- `courses/<slug>/memlog.md`: Initialized course pedagogical working memory.
- `courses/<slug>/notes/chapter-XX.md`: Flat chapter textbook scaffolds (distilled upon section completion by `/tc-teach`).
- `courses/<slug>/chapter-*/section-*/lesson-plan.md`: AI instructor lesson plans.

### 4. Present Next Action

Show the syllabus overview, brainstorm synthesis, and deliberation summary to the learner, then recommend:
- Start the first section: `/tc-teach`
