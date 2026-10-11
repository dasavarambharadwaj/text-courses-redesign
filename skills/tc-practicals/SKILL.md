---
name: tc-practicals
description: Formulates verifiable practical project briefs weighted toward diagnosed misconceptions in test-ledger.jsonl and executes 4-lens project reviews in portfolio/.
---

# Applied Verification Skill (`tc-practicals`)

Guides the learner through authentic proof-of-work project creation. Formulates customizable project briefs with deterministic deliverable contracts, weights project tasks toward historical misconceptions, and reviews submitted deliverables across four rigorous objective lenses.

## Core Rules & Invariants

### 1. Customizable Project Brief Intake (FR-16)
- Default intake parameters:
  - **Complexity:** Medium (robust real-world constraints)
  - **Time Budget:** Weekend Sprint (~4 hours)
  - **Depth/Breadth:** Balanced
- Allows learner to provide a custom project idea or choose the tailored course capstone.
- Weights project challenges toward diagnosed misconceptions logged in `test-ledger.jsonl`.

### 2. Verifiable Deliverables Contract (FR-17)
- Required deliverables MUST be deterministic artifacts: source code (`src/`), automated tests (`tests/`), configuration schemas, or formatted technical memos.
- NEVER request subjective, un-evaluable submissions (e.g. video demos, vague essays).
- Every project spec specifies explicit file paths, test commands, and pass/fail criteria.

### 3. Multi-Lens Project Review Pass (FR-18)
- Every project review evaluates submissions against 4 parallel objective lenses:
  1. **Functional Completeness** — Do deliverable files exist? Are primary requirements and interfaces fully operational?
  2. **Edge Cases & Robustness** — Are boundary conditions, error paths, timeouts, and resource cleanups defended?
  3. **Architecture & Craft** — Sovereign filesystem discipline, zero prohibited dependencies, clear modular separation.
  4. **Verification Integrity** — Does the automated test suite execute cleanly with zero failures and meaningful assertions?
- Generates `portfolio/project-XX/review-report.md`.
- Passing review marks `course.toml` course status as `completed`.

---

## Conventions

- `{project-root}` is the nearest folder containing `.tc/`, starting at the current working directory and searching upwards (or `.` if not yet initialized).
- `{skill-root}` is this skill's own directory (e.g. `skills/tc-practicals` or `.agents/skills/tc-practicals`).

## On Activation

Verify workspace initialization: check if `{project-root}/_tc/scripts/practical_evaluator.py` exists.
- If not found: TextCourses is not initialized in this workspace. Offer to run `/tc-init` first (installing it via `npx skills add <repo> --skill tc-init` if needed), then re-run this command.

---

## Execution Workflow

### Step 1: Intake & Brief Initialization
Prompt the learner to confirm project preferences or propose a custom scenario:

1. Confirm preferences (default: Medium complexity, 4h budget, balanced scope) or accept custom idea.
2. Initialize the project brief on disk:

```bash
uv run _tc/scripts/practical_evaluator.py init-brief \
  --course "<slug>" \
  --complexity "medium" \
  --time-budget "weekend_sprint" \
  --custom-idea "<optional_learner_idea>"
```

- Inspect output JSON. Present the generated `portfolio/project-XX/project-spec.md` to the learner, emphasizing:
  - Deliverables layout (`src/`, `tests/`, `README.md`)
  - Automated test command
  - Any historical misconception focus areas incorporated into the spec.

### Step 2: Autonomous Learner Build Phase
The learner implements their project in `portfolio/project-XX/`. Provide Socratic architectural feedback if asked, but let the learner write their implementation and test suites.

### Step 3: Review Execution (4-Lens Pass)
When the learner indicates they are ready for review:

1. Inspect the deliverables in `portfolio/project-XX/`.
2. Run automated test suites (e.g. `pytest portfolio/project-XX/tests/`).
3. Formulate detailed findings for each of the 4 lenses:
   - Lens 1: Functional Completeness
   - Lens 2: Edge Cases & Robustness
   - Lens 3: Architecture & Craft
   - Lens 4: Verification Integrity
4. Record the review report and transition course status:

```bash
uv run _tc/scripts/practical_evaluator.py review \
  --course "<slug>" \
  --project-id "01" \
  --verdict "<PASS|NEEDS_WORK>" \
  --functional-lens "<Lens 1 findings>" \
  --edge-lens "<Lens 2 findings>" \
  --architecture-lens "<Lens 3 findings>" \
  --verification-lens "<Lens 4 findings>" \
  --remediation "<Remediation items if NEEDS_WORK>"
```

### Step 4: Outcome & Next Steps
- If **PASS**:
  - Congratulate the learner on successfully graduating and completing the course!
  - Point to `portfolio/project-XX/review-report.md` as proof of competence.
  - Recommend creating another course or exploring advanced topics via `/tc-init`.
- If **NEEDS_WORK**:
  - Present the specific remediation tasks from `review-report.md`.
  - Guide the learner on how to address each finding.
