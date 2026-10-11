# TextCourses Universal Interaction Standards (FR-42)

> **Core Invariant**: TextCourses is designed for deep, frictionless learning accessible to everyone—from a 10-year-old curious beginner to a seasoned systems engineer. Every agent, skill, and runtime script MUST adhere to these cognitive lightness rules.

---

## 1. The Strict Single-Question Rule

- **Rule**: In any interactive conversational turn, ask **EXACTLY ONE question or choice**.
- **Execution**: Output the question or scannable menu, stop text generation immediately, and **WAIT** for the learner's response.
- **Forbidden**: Never bundle multiple stages, questionnaires, or menus into a single turn or message. Never ask "What is your name and what do you want to learn and what is your experience?" all together.

---

## 2. The 10-Year-Old Readability Standard

- **Rule**: Formulate all prompts, persona descriptions, and menu options in simple, everyday English that a 10-year-old child can immediately understand.
- **Execution**:
  - Prefer plain words: *"Everyday Explainer"*, *"Step-by-Step Mentor"*, *"Hands-on Builder"*.
  - Ban pretension: Never use terms like *"axiomatic purist"*, *"dialectic inquisitor"*, *"teleological cartographer"*, or *"acyclic prerequisite proofs"* in learner-facing menus.
  - Analogies over abstraction: Use concrete physical examples before formal theory.

---

## 3. Dynamic Recommendation Protocol

- **Rule**: Every numbered menu must highlight the most contextually fitting option with a **`(Recommended)`** label based on the learner's previous answers.
- **Execution**:
  - Turn order matters: Previous turns (such as target domain or background) inform subsequent recommendations.
  - Place recommended choices prominently so learners can simply press Enter or reply with the recommended number.

---

## 4. The Related-Decisions Summary Pattern (Zero Scrolling Fatigue)

- **Rule**: When a workflow addresses multiple related components (for example, refactoring 4 modules, configuring multiple course settings, or presenting the final intake recap), provide a **short, scannable summary at the end** in plain English.
- **Execution**:
  - State clearly what will be done across all related parts in 2–4 concise bullet points.
  - Present a single short prompt: *"Ready to proceed with these changes? [1] Yes (Recommended) / [2] Customize"*.
  - Learners can scroll up if they wish to inspect granular details, but they must **never** be forced to scroll back and forth to understand what they are choosing.

---

## 5. Skills Adherence Matrix

| Skill | Interaction Model | Pacing Rule |
| :--- | :--- | :--- |
| **`tc-init`** | Sequential conversational intake | Strictly 1 question per turn (Name → Domain → Role → Experience → Density → Teacher → Summary). No style preview prompts. |
| **`tc-roadmap`** | Diagnostic placement testing | Strictly 1 diagnostic scenario per turn; evaluate response before presenting next scenario. |
| **`tc-teach`** | Single-concept delivery | Strictly 1 concept per turn; ends with standardized 4-option Next-Action Fork. |
| **`tc-test-me`** | Diagnostic inquiry | Strictly 1 hinge scenario dilemma per turn (`SM-C3: Do not bombard the user`). |
| **`tc-practicals`** | Project brief confirmation | Single scannable prompt with sensible defaults (Medium, 4h sprint) + custom option. |
| **`tc-create`** | Zero-stalling autonomous build | Synthesizes 4-paradigm curriculum autonomously without stalling user with open-ended questions. |
| **`tc-redirect-course`** | Drift triage | Single 3-choice menu for drift resolution. |
| **`tc-migrate`** | Migration plan consent gate | Single typed confirmation (`--confirm APPLY`). |
