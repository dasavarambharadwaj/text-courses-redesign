---
type: change-proposal
title: "Course Correction: Streamline Intake Protocol & Enable Hybrid Master Teacher Personas"
initiative: initiative-textcourses
trigger: "User audit identified cognitive overload in Stage 5 Explanation Density and semantic overlap / lack of combination support in Master Teacher selection"
status: drafted
date: "2026-11-01"
---

# Sprint Change Proposal: Intake Protocol Streamlining & Hybrid Teacher Engine

## 1. Issue Summary

### 1.1 Trigger & Discovery Context
During verification and user review of the TextCourses onboarding flow (`/tc-init`), two critical UX and technical flaws were identified:
1. **Unnecessary Stage 5 Intake Question (Explanation Density)**: The prompt *"How detailed would you like each lesson to be?"* asks learners to choose between word counts (`~60–100` vs `~150–200` vs `~250–350` words) in the abstract before experiencing a single lesson. This introduces unnecessary cognitive friction and violates FR-42 (Zero-Cognitive-Overload). Furthermore, explanation density is already derived automatically by the underlying engine based on the learner's experience level (`beginner` $\rightarrow$ `balanced`, `practitioner` $\rightarrow$ `deep_dive`).
2. **Faculty Persona Semantic Blur & Lack of Multi-Select Combinations**:
   - **Semantic Overlap**: Personas [2] (Hypatia: *"builds step-by-step from first principles without skipping anything"*) and [3] (Turing: *"logical, hands-on, focuses on system internals, how things work under the hood"*) feel functionally identical to technical learners. Both read as deep, rigorous engineering breakdown.
   - **Broken Combinations (`1, 2` / `1, 3`)**: Software engineers frequently want a hybrid pedagogy—e.g. Feynman's intuitive real-world analogy first, immediately followed by Turing's working code and runtime execution traces. However, `bootstrapper.py:313` evaluated teachers with an exclusive `if/elif` string match that discarded the second teacher, and fell back to generic defaults if numbers (`"1, 2"`) were entered.
   - **Legacy Involuntary Override**: `course_builder.py:185` and `teach_engine.py:172` forcibly overwrote `feynman` to `hypatia` whenever the learner was marked beginner, overriding user intent.
3. **Lifecycle Recommendation Disconnect (`tc-init` -> `/tc-create` skipping `/tc-research`)**:
   - `skills/tc-init/SKILL.md` and `bootstrapper.py scan` directly advised running `/tc-create "<subject>"` after initialization.
   - This bypasses the pre-course research phase (`tc-research`), which runs 5-Hat reflection and compiles `research/<slug>/dossier.md` before curriculum scaffolding.
   - `VALID_RECOMMENDATIONS` in `bootstrapper.py` omitted `"/tc-research"`.
4. **Superficial Domain Elicitation in Stage 2**:
   - Stage 2 asked a bare single line (*"What specific subject, skill, or topic do you want to learn?"*), leading to generic one-word answers ("rust", "distributed systems") that starve `tc-research` and `tc-create` of critical context (focus areas, target projects, emphasis/skip lists).
   - `profile/preferences.md` lacked frontmatter fields for `target_subject` and `learning_goals`.
5. **Memory, Session Continuity & Decision Storage Gaps**:
   - `skills/tc-teach/SKILL.md` never commands the agent to call `teach_engine.py log-turn`, leaving conversational dialogue and re-explanations unrecorded in `session.jsonl`.
   - `profile/memlog.md` is initialized on `/tc-init`, but macro milestones (course creation, course completion) are never mirrored to it.
   - `practical_evaluator.py` approves capstone deliverables in `portfolio/`, but does not log completion milestones into `courses/<slug>/memlog.md` or `profile/memlog.md`.
6. **Roadmap Skill Awkwardness & Lack of Scope Awareness**:
   - `tc-roadmap` was exposed as a standalone public slash skill, confusing users about whether to invoke `/tc-init`, `/tc-roadmap`, or `/tc-create`.
   - Roadmaps were treated as an all-or-nothing step rather than being automatically generated only when a domain is broad (e.g. Software Architecture) vs skipped when focused (e.g. Raft Consensus).
   - Internal Triad and maintenance skills (`tc-roadmap`, `tc-verify-course`, `tc-redirect-course`, `tc-migrate`) were erroneously exposed as public interactive commands.
7. **Domain-Specific Tight Coupling (Anti-Software Bias Violation)**:
   - `practical_evaluator.py:510` hardcoded checks for programming syntax keywords (`def`, `class`, `fn`, `struct`, `impl`), penalizing non-software learners (law, medicine, finance, design).
   - `skills/tc-teach/SKILL.md` hardcoded "Code Walkthrough / Table" instead of universal worked applications / case studies.
   - Roadmaps were conceived as sub-topics rather than true, independent academic/professional subjects with sovereign textbooks and reference literature.
8. **RAG Disconnect in Teaching & Missing Hallucination Verification**:
   - `_tc/scripts/indexer.py` built sovereign SQLite FTS5 RAG databases (`rag-db/index.db`), but `tc-teach` never queried it, teaching purely from LLM weights rather than grounding in retrieved source excerpts.
   - No automated verification verified whether syllabus concepts were corroborated by source citations in `index.db`.

### 1.2 Evidence & Current Limitations
- **`skills/tc-init/SKILL.md:97-104`**: Explicitly pauses execution for Stage 5 word-count density selection.
- **`_tc/scripts/bootstrapper.py:313-321`**:
  ```python
  t_clean = (teacher or "").lower()
  if "feynman" in t_clean:
      derived_styles = ["analogy"]
  elif "turing" in t_clean:
      derived_styles = ["code_first", "direct_technical"]
  elif "hypatia" in t_clean:
      derived_styles = ["direct_technical", "analogy"]
  ```
  Entering `"feynman, turing"` or `"1, 2"` fails to compose both styles.
- **`_tc/scripts/course_builder.py:184-185`**:
  ```python
  if "teacher" not in result or result["teacher"] == "feynman":
      result["teacher"] = "hypatia"
  ```
  Forces beginner learners off Feynman into Hypatia.

---

## 2. Impact Analysis

### 2.1 Epic Impact
- **Affected Epic**: `epic-onboarding-lifecycle` (`_bmad-output/initiative-textcourses/epic-onboarding-lifecycle/epic-onboarding-lifecycle.md`)
  - Story 2.1 (`story-implement-workspace-bootstrapper-and-scanner-tc-init-plan.md`) scope updated to reflect 5-stage frictionless intake and hybrid persona parsing.
- **Downstream Epics**:
  - `epic-curriculum-creation` (`tc-create` / `course_builder.py`): Cleaned of involuntary teacher mutation.
  - `epic-instruction-delivery` (`tc-teach` / `teach_engine.py`): Receives composed compound directives (e.g. `Analogy + Code-First`).

### 2.2 Artifact Impact
| Artifact | Impact Type | Nature of Modification |
| :--- | :--- | :--- |
| `prd-textcourses.md` | Minor Refinement | Update FR-1 and FR-24 to specify 5-stage zero-overload intake and multi-teacher hybrid support. |
| `_tc/INTERACTION_STANDARDS.md` | Direct Edit | Update Section 5 skills adherence matrix for `tc-init` from 6 stages to 5 stages. |
| `skills/tc-init/SKILL.md` | Direct Edit | Remove Stage 5 (Explanation Density). Sharpen Stage 5 (Teacher Menu) with orthogonal archetypes and combo support (`1, 2`, `1, 3`). |
| `_tc/scripts/bootstrapper.py` | Implementation | Support multi-select teacher inputs, combine style arrays and directives, and auto-infer density from experience level. |
| `_tc/scripts/course_builder.py` | Bug Fix | Remove involuntary beginner teacher reassignment. |
| `_tc/scripts/teach_engine.py` | Bug Fix | Remove involuntary beginner teacher reassignment. |
| `skills/tc-init/scripts/runtime/` | Synchronization | Mirror updated engine scripts into skill runtime directory. |

---

## 3. Recommended Approach

### 3.1 Direct Adjustment Strategy
We execute a **Direct Adjustment** to the onboarding protocol and runtime substrate:
1. **Eliminate Cognitive Waste**: Remove Stage 5 (Explanation Density) from the interactive intake. Density is automatically inferred from Experience Level (`beginner` $\rightarrow$ `balanced`, `practitioner` $\rightarrow$ `deep_dive`), or can be overridden via write-in or during `/tc-teach`.
2. **Sharpen Faculty Archetypes into Orthogonal Dimensions**:
   - **[1] Feynman (Intuitive / Analogy-First) ⚡**: Everyday metaphors, intuitive mental models, zero unexplained jargon before intuition clicks.
   - **[2] Turing (Code-First / Builder) 💻**: Jump straight into working code, runnable snippets, runtime internals, and edge-case execution.
   - **[3] Hypatia (First-Principles / Deep Rigor) 🦉**: Step-by-step logical derivation, core axioms, formal proofs, and architectural design trade-offs.
   - **[4] Other (write-in)**
3. **Native Multi-Select & Hybrid Composition**:
   - Support `1, 2`, `1, 3`, `2, 3`, `1+2`, `all`, and comma-separated names.
   - Compose underlying style keys:
     - `1, 2` $\rightarrow$ **The Intuitive Builder** (`analogy` + `code_first`)
     - `1, 3` $\rightarrow$ **The Conceptual Master** (`analogy` + `math`)
     - `2, 3` $\rightarrow$ **The Systems Architect** (`code_first` + `math`)
     - `1, 2, 3` $\rightarrow$ **The Polymath** (`analogy` + `code_first` + `math`)
4. **Preserve Substrate Immutability**: All compiled preferences remain deterministic markdown frontmatter in `profile/preferences.md` with explicit `styles_selected` YAML arrays.

### 3.2 Risk & Timeline
- **Risk Level**: Minimal. No breaking schema changes; `explanation_density` frontmatter key remains populated via automatic inference.
- **Effort**: Low (4 files modified, runtime scripts mirrored, unit tests updated).
- **Status**: **ON HOLD FOR USER FEEDBACK** (holding execution until user provides additional identified issues).

---

## 4. Detailed Change Proposals

### 4.1 `skills/tc-init/SKILL.md`
```markdown
<<<< OLD (Lines 97-115)
### Stage 5: Explanation Density (FR-1)
Present the density menu with the dynamic `(Recommended)` tag (wait for response):
```text
How detailed would you like each lesson to be?
[1] Short & Sweet (Quick summary, minimal words) (~60–100 words per concept)
[2] Balanced with Examples (Practical explanations with clear examples) (~150–200 words per concept) (Recommended)
[3] Deep-Dive Detailed (Comprehensive, deep exploration of internals) (~250–350 words per concept)
```

### Stage 6: Primary Master Teacher (FR-24)
Present the 3 kid-friendly primary teaching personas with the dynamic `(Recommended)` tag (wait for response):
```text
Who would you like as your primary master teacher?
[1] Feynman (The Everyday Explainer) ⚡ — Fun, simple, uses everyday stories and real-world analogies, zero confusing jargon (Recommended)
[2] Hypatia (The Step-by-Step Mentor) 🦉 — Patient, gentle, guides you step-by-step from zero without skipping anything
[3] Turing (The Practical Builder) 💻 — Logical, hands-on, focuses on building things, how it works under the hood, and real code
[4] Other (write-in)
```
==== NEW
### Stage 5: Primary Master Teacher / Pedagogical Style (FR-24)
Present the 3 distinct primary teaching personas with combo support and dynamic `(Recommended)` tag (wait for response):
```text
Who would you like as your master teacher? (Choose one, or combine like 1,2):
• [1] Feynman (Intuitive / Analogy-First) ⚡
      Fun, everyday metaphors, simple mental models, zero unexplained jargon before intuition clicks. (Recommended)
• [2] Turing (Code-First / Builder) 💻
      Straight into working code, runnable snippets, runtime internals, and edge-case debugging.
• [3] Hypatia (First-Principles / Deep Rigor) 🦉
      Step-by-step logical derivation, core axioms, architectural design trade-offs, and why things work.
• [4] Other (write-in)

💡 Tip: You can choose a combo (e.g. "1, 2" for Intuitive Analogies + Hands-on Code)!
```
>>>>
```

### 4.2 `_tc/scripts/bootstrapper.py`
```python
<<<< OLD (Lines 312-325)
    if styles is None:
        t_clean = (teacher or "").lower()
        if "feynman" in t_clean:
            derived_styles = ["analogy"]
        elif "turing" in t_clean:
            derived_styles = ["code_first", "direct_technical"]
        elif "hypatia" in t_clean:
            derived_styles = ["direct_technical", "analogy"]
        else:
            derived_styles = ["direct_technical", "code_first"]
        norm_styles = normalize_style_keys(derived_styles)
    else:
        norm_styles = normalize_style_keys(styles)
==== NEW
    if styles is None:
        t_clean = (teacher or "").lower()
        derived_styles: list[str] = []
        tokens = [t.strip() for t in re.split(r"[,+/\s&]+", t_clean) if t.strip()]
        for tok in tokens:
            if tok in {"1", "feynman", "everyday", "analogy"}:
                derived_styles.append("analogy")
            elif tok in {"2", "turing", "builder", "code", "code_first"}:
                derived_styles.extend(["code_first", "direct_technical"])
            elif tok in {"3", "hypatia", "socrates", "first_principles", "math", "rigor"}:
                derived_styles.extend(["math", "direct_technical"])
            elif tok in {"all", "polymath"}:
                derived_styles.extend(["analogy", "code_first", "math"])
        if not derived_styles:
            derived_styles = ["direct_technical", "code_first"]
        norm_styles = normalize_style_keys(derived_styles)
    else:
        norm_styles = normalize_style_keys(styles)
>>>>
```

### 4.3 `_tc/scripts/course_builder.py` & `_tc/scripts/teach_engine.py`
```python
<<<< OLD
    # Involuntary override of feynman to hypatia for beginners
    role_lower = str(result.get("role", "")).lower()
    if "beginner" in role_lower or result.get("competency_level") == "beginner":
        result["competency_level"] = "beginner"
        if "teacher" not in result or result["teacher"] == "feynman":
            result["teacher"] = "hypatia"
==== NEW
    role_lower = str(result.get("role", "")).lower()
    if "beginner" in role_lower or result.get("competency_level") == "beginner":
        result["competency_level"] = "beginner"
        if "teacher" not in result:
            result["teacher"] = "hypatia"
>>>>
```

---

## 5. Implementation Handoff & Extensibility

- **Classification**: Minor / Targeted Course Correction.
- **Handoff Action**:
  - The plan is fully documented and structured above.
  - **EXECUTION IS CURRENTLY PAUSED**: As requested by the user, no code changes or script builds will commence until the user shares their additional issues and feedback.
  - When the user provides the remaining issues, they will be appended to this Change Proposal so all changes can be reviewed and executed coherently in one unified batch.
