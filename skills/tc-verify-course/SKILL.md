---
name: tc-verify-course
description: "Audit curriculum DAG acyclicity, prerequisite sequencing, and vocabulary introduction contracts."
---

# `tc-verify-course`: Pre-Flight Curriculum Auditor & Vocabulary Validator

`tc-verify-course` serves as the Auditor in the Triad Consensus Loop. It verifies that proposed courses are pedagogically sound, free of circular prerequisite dependencies, grounded in researched technical ground truth, and strictly adhere to vocabulary introduction contracts before files are written to disk.

## Core Invariants

1. **Acyclic Topological Sequencing (FR-7, AD-4)**: Curriculum chapters and sections must form a valid Directed Acyclic Graph (DAG) with zero cycles.
2. **Vocabulary Contract Enforcement**: A section must never require prerequisite vocabulary terms that have not been introduced by an antecedent section earlier in the topological order.
3. **Factual Grounding Check**: Cross-check topics and vocabulary against `.tc/research/<slug>/digest.json` to prevent hallucinated APIs.
4. **Strict Audit Gating**: If any `CRITICAL` findings exist, the auditor exits with code 1, preventing candidate courses from being committed to the workspace.

---

## Conventions

- `{project-root}` is the nearest folder containing `.tc/`, starting at the current working directory and searching upwards (or `.` if not yet initialized).
- `{skill-root}` is this skill's own directory (e.g. `skills/tc-verify-course` or `.agents/skills/tc-verify-course`).

## On Activation

Verify workspace initialization: check if `{project-root}/_tc/scripts/auditor.py` exists.
- If not found: TextCourses is not initialized in this workspace. Offer to run `/tc-init` first (installing it via `npx skills add <repo> --skill tc-init` if needed), then re-run this command.

---

## Workflow

### 1. Execute Pre-Flight Audit

Audit a proposed `course.toml` manifest or in-memory candidate:

```bash
uv run _tc/scripts/auditor.py audit --manifest courses/distributed-systems/course.toml --research-slug distributed-systems
```

### 2. Audit Findings Classification

The auditor classifies all findings by severity:
- `CRITICAL`: Immediate failure (exit code 1).
  - `DAG_CYCLE`: Circular prerequisite dependencies detected.
  - `MISSING_PREREQUISITE`: Section depends on non-existent prerequisite.
  - `PREMATURE_VOCABULARY`: Section requires technical terms never introduced in ancestor sections.
  - `INVALID_ARCHETYPE`: Manifest does not use one of the 5 Universal Archetypes.
- `WARNING`: Pedagogical warning (exit code 0 if 0 critical).
  - `DUPLICATE_VOCABULARY`: A section re-introduces a term already introduced earlier.
  - `RESEARCH_UNVERIFIED`: Research digest confidence is unverified.
- `INFO`: Noteworthy pedagogical metadata.
  - `UNGROUNDED_TOPIC`: Section introduces vocabulary outside cached documentation digest.

### 3. Triad Reconciliation

When running within the Triad Consensus Loop:
- If `CRITICAL` findings occur: The candidate curriculum is rejected, findings are fed back to `tc-create` (Architect) to regenerate or repair prerequisites, and reconciliation events are logged.
- If `0 CRITICAL` findings: The course is approved for final disk scaffolding.
