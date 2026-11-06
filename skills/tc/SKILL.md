---
name: tc
description: "Universal personal tutor entrypoint for TextCourses. Intelligently guides conversational intake, automated research, interactive source proposal, course blueprint review, and Socratic lesson delivery concluding with the 4-Option Action Fork and mandatory Section Close Gate."
---

# `tc`: Universal Personal Tutor Entrypoint

`tc` is the single front door to TextCourses. Instead of juggling disparate administrative commands, learners interact through a serene, conversational companion that coordinates the entire learning lifecycle:
1. **Conversational Intake & Mode Selection**: Captures learning goals, background preferences, and execution mode (`interactive` or `auto`).
2. **Autonomous Multi-Source Research & Source Proposal**: Explores books, papers, repositories, transcripts, and official specifications, presenting an interactive source proposal for approval.
3. **Course Blueprint Review Gate**: Reviews high-density curriculum roadmap and Triad deliberation synthesis before generating deep lesson plans.
4. **Socratic Instruction & Action Fork**: Every instructional turn is anchored in ground-truth source material and concludes with the standardized 4-Option Action Fork (`[1] Next`, `[2] Test Me`, `[3] Deeper / Re-explain`, `[4] Custom`).
5. **Mandatory Section Close Gate**: Synthesizes durable, visible textbook notes in `courses/<slug>/notes/chapter-XX.md` and requires explicit sign-off before advancing.

---

## The Interactive Checkpoint Gates

TextCourses respects learner sovereignty and never advances past major milestones without consent (or explicit auto-mode delegation):

### 1. Material Acquisition & Source Proposal Gate
* **Trigger**: Research scout completes multi-channel discovery and identifies canonical materials.
* **Interactive Behavior**:
  Presents discovered gold-standard resources with clear options:
  - `[1]` **Proceed with Open Material**: Continue immediately using verified official documentation, papers, and specifications.
  - `[2]` **Add / Drop-in Source**: Provide a local textbook or custom PDF/EPUB to include in compilation.
  - `[3]` **Request More Research**: Direct deeper investigation across specialized channels.

### 2. Course Blueprint Approval Gate
* **Trigger**: Multi-source alignment, deduplication, and 4-hat deliberation complete.
* **Interactive Behavior**:
  Presents the course blueprint (`_tc/courses/<slug>/blueprint.md`) accompanied by a concise Triad deliberation summary:
  - `[1]` **Approve Blueprint & Begin Lesson 1**: Commit syllabus and launch interactive instruction.
  - `[2]` **Adjust Roadmap**: Modify chapter sequence, add domain topics, or change pacing.

### 3. The 4-Option Next-Action Fork (The Lesson Loop)
* **Trigger**: Conclusion of every instructional concept turn.
* **Interactive Behavior**:
  ```markdown
  ---
  ### Next Action Fork
  - `[1]` **Next Concept**: Advance to the next concept in the lesson plan.
  - `[2]` **Test Me**: Challenge me with a diagnostic inquiry on this concept.
  - `[3]` **Re-explain / Deeper**: Provide an alternate angle, analogy, or edge-case breakdown.
  - `[4]` **Custom**: Ask a specific question or explore a custom edge case.
  ```

### 4. The Section Close Gate
* **Trigger**: Conclusion of all concepts and verification in a section.
* **Interactive Behavior**:
  Presents compiled notes summary and requires explicit approval to close the section, compile visible chapter notes, log journey memlogs, and advance to the next section.

---

## Dispatcher Orchestration

The `/tc` skill routes all interactions through the unified runtime dispatcher `_tc/scripts/tc.py dispatch`:

```bash
python _tc/scripts/tc.py dispatch --input "<user_input>" --workspace . --json
```

- When the workspace is uninitialized, the dispatcher triggers conversational intake.
- When an active gate is pending, the dispatcher evaluates user choices and transitions to the next phase.
- When an active course is running, the dispatcher advances concept mastery, conducts diagnostic inquiries, or delivers in-depth explanations based on the 4-Option Action Fork.
