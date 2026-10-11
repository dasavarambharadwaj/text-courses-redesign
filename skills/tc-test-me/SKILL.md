---
name: tc-test-me
description: Pure question-based diagnostic testing of learner mental models without code copy-pasting into chat. Enforces Cumulative Boundary Rule, logs results atomically to test-ledger.jsonl, and updates section completion status.
---

# Diagnostic Assessment Skill (`tc-test-me`)

Conducts targeted, 100% question-based conceptual diagnostic evaluations of learner mental models without requiring code copy-pasting into chat. Evaluates boundary conditions, failure modes, and architectural implications, logging outcomes to a persistent ledger.

## Core Rules & Invariants

### 1. 100% Question-Based Testing (Zero Code Pasting) (FR-13)
- Evaluate mastery **strictly** through scenario-based diagnostic questions, hinge dilemmas, and mechanism trade-offs.
- **NEVER** ask or prompt the learner to paste code into chat.
- Learners respond via concise conceptual explanation or numbered trade-off selection.

### 2. Cumulative Boundary Rule (FR-15)
- Test **only** concepts that exist in sections marked `review` or `completed` in `course.toml`.
- **STRICTLY FORBIDDEN:** Leaking or introducing terminology, mechanics, or APIs from upcoming `not-started` or `in-progress` sections.
- Stage Loading Matrix: Never read `lesson-plan.md` during testing. Rely on `notes.md` summaries provided by `diagnostic_tester.py prepare`.

### 3. Persistent Diagnostic Logging (FR-14)
- Every diagnostic evaluation must be logged atomically to `courses/<slug>/test-ledger.jsonl`.
- Categorize identified misconceptions (e.g., `CONFUSION_MUTATION_TIMING`, `CONFUSION_OWNERSHIP_LIFETIME`, `CONFUSION_CONCURRENCY_ORDERING`).
- Passing a section test automatically marks its status as `completed` in `course.toml`.

---

## Conventions

- `{project-root}` is the nearest folder containing `.tc/`, starting at the current working directory and searching upwards (or `.` if not yet initialized).
- `{skill-root}` is this skill's own directory (e.g. `skills/tc-test-me` or `.agents/skills/tc-test-me`).

## On Activation

Verify workspace initialization: check if `{project-root}/_tc/scripts/diagnostic_tester.py` exists.
- If not found: TextCourses is not initialized in this workspace. Offer to run `/tc-init` first (installing it via `npx skills add <repo> --skill tc-init` if needed), then re-run this command.

---

## Execution Workflow

### Step 1: Prepare Context & Verify Eligible Boundaries
Run the diagnostic tester engine to verify cumulative boundaries and load the misconception digest:

```bash
uv run _tc/scripts/diagnostic_tester.py prepare --course <slug>
```

- Inspect the JSON response:
  - If `ok` is `false`, notify the learner that no sections are eligible yet, and instruct them to complete lessons via `/tc-teach`.
  - Review `eligible_sections` and `active_test_section`.
  - Review `misconceptions_summary` to probe known historical weak spots.

### Step 2: Formulate Hinge Diagnostic Question
Pose a single, intellectually stimulating scenario question:
- **Scenario / Dilemma:** Describe a concrete production bug, boundary condition, or design trade-off relevant to the active section.
- **Options or Mechanism Probe:** Ask the learner to explain the root cause or choose between concrete trade-offs:
  - Option A vs. Option B trade-offs
  - Failure-mode prediction: What happens when X condition occurs?
  - Invariant analysis: Which system guarantee breaks under concurrent or exceptional conditions?
- **Format:**
  ```markdown
  ### Diagnostic Scenario: [Concept Name]
  
  [Concrete architectural or operational scenario with specific boundary constraints]
  
  **Question:** [Targeted hinge dilemma or mechanism probe]
  
  *Respond with your analysis or select the appropriate trade-off.*
  ```

### Step 3: Evaluate Response & Socratic Drill-Down
- If the learner is **correct**:
  - Validate their mental model concisely.
  - Highlight the subtle mechanical nuance that confirms their mastery.
  - Determine outcome: `pass`.
- If the learner exhibits a **misconception**:
  - Do not give away the answer immediately.
  - Ask a short Socratic drill-down question isolating the exact false premise.
  - Identify the category: `CONFUSION_<TOPIC>`.
  - Determine outcome: `fail`.

### Step 4: Record Outcome Atomically
Execute `diagnostic_tester.py record` to persist the result to `test-ledger.jsonl` and update `course.toml`:

```bash
uv run _tc/scripts/diagnostic_tester.py record \
  --course "<slug>" \
  --chapter "<chapter_slug>" \
  --section "<section_slug>" \
  --type "hinge_scenario" \
  --prompt "<question_text>" \
  --response "<learner_response>" \
  --outcome "<pass|fail>" \
  --misconception "<misconception_tag>" \
  --remediation "<feedback_or_summary>"
```

### Step 5: Present Next-Action Fork
Conclude the assessment turn with the standard Next-Action Fork:

```markdown
---
### Next-Action Fork
- `[1]` Continue to next lesson (/tc-teach)
- `[2]` Take another diagnostic question on this section
- `[3]` Practical exercise / project work (/tc-practicals)
- `[4]` Review section textbook notes
---
```
