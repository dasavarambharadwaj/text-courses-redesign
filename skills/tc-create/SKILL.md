---
name: tc-create
description: "Architect comprehensive courses across 5 Universal Archetypes reconciled through the Triad Consensus Loop."
---

# `tc-create`: Autonomous Curriculum Architect & Course Scaffolder

`tc-create` acts as the Architect in the Triad Consensus Loop. It translates learner goals, reference URLs, or raw syllabus outlines into pedagogical roadmaps across the **5 Universal Archetypes**, reconciled against documentation ground truth and pre-flight DAG checks.

## The 5 Universal Archetypes (FR-4)

1. **`applied_creation`** (Default): Build a complete production system piece by piece. Every section implements a concrete deliverable.
2. **`forensic_dilemma`**: Investigate system incidents, failing invariants, and corruptions. Diagnose root causes and engineer mitigations.
3. **`axiomatic_primitives`**: Deconstruct down to fundamental mechanical primitives, then compose higher abstractions from mathematical first principles.
4. **`spiral_immersion`**: Execute a minimal complete end-to-end pass first, then spiral through successive iterations with deeper nuances and scale.
5. **`reverse_engineering`**: Decompile, trace, and inspect black-box protocols, binary formats, or existing architectures to deduce internal mechanics.

---

## Conventions

- `{project-root}` is the nearest folder containing `.tc/`, starting at the current working directory and searching upwards (or `.` if not yet initialized).
- `{skill-root}` is this skill's own directory (e.g. `skills/tc-create` or `.agents/skills/tc-create`).

## On Activation

Verify workspace initialization: check if `{project-root}/_tc/scripts/course_builder.py` exists.
- If not found: TextCourses is not initialized in this workspace. Offer to run `/tc-init` first (installing it via `npx skills add <repo> --skill tc-init` if needed), then re-run this command.

---

## Workflow

### 1. Intake Learner Intent

When the learner invokes `/tc-create`:
1. Ask for course topic, domain, or target skill.
2. Present the 5 Universal Archetypes with quick descriptions, or detect from intent.
3. Accept optional reference course links, documentation URLs, or raw syllabus outlines.

### 2. Execute Triad Consensus Course Generation

Run the course builder CLI:

```bash
uv run _tc/scripts/course_builder.py create \
  --slug distributed-storage \
  --title "Distributed Storage Systems" \
  --archetype applied_creation \
  --topic "Raft, LSM-Trees, and Raft-based Key-Value Store"
```

The tool coordinates the Triad Consensus Loop:
- **Scout (`tc-research`)**: Verifies documentation ToC, APIs, and vocabulary.
- **Architect (`tc-create`)**: Scaffolds chapters, sections, and lesson plans.
- **Auditor (`tc-verify-course`)**: Checks DAG acyclicity and vocabulary contracts.
- **Trace Logger**: Records reconciliation attempts to `.tc/cache/consensus-trace.jsonl`.

### 3. Generated Files

Upon successful consensus, the course is written to disk:
- `courses/<slug>/course.toml`: Course manifest with prerequisites and status.
- `courses/<slug>/overview.md`: Human-readable syllabus overview.
- `courses/<slug>/chapter-*/section-*/lesson-plan.md`: AI instructor lesson plans.
*(Note: `notes.md` is strictly generated upon section completion by `/tc-teach`).*

### 4. Present Next Action

Show the syllabus overview to the learner and recommend:
- Start the first section: `/tc-teach`
