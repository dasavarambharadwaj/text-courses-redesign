---
name: tc-teach
description: "Deliver conversational, single-concept deep dives concluding with the standardized 4-option Next-Action Fork."
---

# `tc-teach`: Conversational Single-Concept Instruction

`tc-teach` delivers conceptually dense, high-velocity teaching bounded strictly to one concept per turn, tailored to the learner's active Style Profile from `plan/preferences.md`, and concluding every turn with the standardized Next-Action Fork.

## Core Invariants

1. **Strict Single-Concept Bounding (FR-9)**: Never teach multiple concepts in one turn. Focus on one mechanism, its invariant, a concrete code example, and a fatal mistake to avoid.
2. **Style Profile Adherence**:
   - `direct_technical`: High density, systems internals, zero fluff.
   - `analogy_intuition`: Relatable physical or mechanical metaphors before code.
   - `code_first`: Start directly with executable code, explain mechanisms after.
   - `first_principles`: Mathematical proofs, memory layouts, mechanical axioms.
3. **Mandatory Next-Action Fork (FR-10)**: Every instructional turn MUST conclude with the standardized 4-option fork:
   ```markdown
   ---
   ### Next Action Fork
   - `[1]` **Next Concept**: Advance to the next concept in the lesson plan.
   - `[2]` **Test Me**: Challenge me with a diagnostic inquiry on this concept.
   - `[3]` **Re-explain / Deeper**: Provide an alternate angle, analogy, or edge case breakdown.
   - `[4]` **Custom**: Ask a specific question or explore a custom edge case.
   ```
4. **Automated Notes Compilation (FR-11)**: When the final concept in a section is ticked off via `[1]`, the system automatically compiles `notes.md` with a 3-bullet recap and marks the section as `review` in `course.toml`.
5. **Session Hygiene (FR-12)**: Checkmarks in `lesson-plan.md` ensure interruption recovery without lost continuity.

---

## Conventions

- `{project-root}` is the nearest folder containing `.tc/`, starting at the current working directory and searching upwards (or `.` if not yet initialized).
- `{skill-root}` is this skill's own directory (e.g. `skills/tc-teach` or `.agents/skills/tc-teach`).

## On Activation

Verify workspace initialization: check if `{project-root}/_tc/scripts/teach_engine.py` exists.
- If not found: TextCourses is not initialized in this workspace. Offer to run `/tc-init` first (installing it via `npx skills add <repo> --skill tc-init` if needed), then re-run this command.

---

## Workflow

### 1. Initialize Active Teaching Context

Run the teach engine to retrieve the active section and current concept:

```bash
uv run _tc/scripts/teach_engine.py session --course <course_slug>
```

The output indicates:
- `active_section`: Target chapter and section.
- `active_concept`: The exact next concept to teach from `lesson-plan.md`.
- `preferences`: Active style profile and density.

### 2. Deliver Single-Concept Turn

Teach the concept adhering strictly to the learner's style profile and density:
- **Bold Mechanics**: Explicit terminology.
- **Mental Model / Invariant**: Why it exists and what breaks if violated.
- **Code Walkthrough / Table**: Concrete implementation.
- **Fatal Mistake**: The most common real-world trap or bug.
- Conclude with the **Next-Action Fork**.

### 3. Handle Learner Response

- **If Learner picks `[1]` (Next Concept)**:
  Execute concept advancement:
  ```bash
  uv run _tc/scripts/teach_engine.py advance --course <course_slug>
  ```
  - If more concepts remain: deliver the next concept.
  - If section completed: announce section completion, present the 3-bullet recap from compiled `notes.md`, and recommend `/tc-test-me` (chapter review).
- **If Learner picks `[2]` (Test Me)**:
  Switch to diagnostic inquiry mode: ask an active recall inquiry on the concept just taught.
- **If Learner picks `[3]` (Re-explain / Deeper)**:
  Re-explain using an alternate angle or deeper failure mode without ticking the concept.
- **If Learner picks `[4]` (Custom)**:
  Answer the learner's specific query while maintaining focus on the current topic.
