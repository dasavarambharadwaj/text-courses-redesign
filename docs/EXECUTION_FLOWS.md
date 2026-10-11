# Step-by-Step Execution Flows & Lifecycles

> **Complete Visual Flowcharts for Developers & Enthusiasts**

This document details every major workflow in TextCourses with exact decision trees, script invocations, file reads/writes, and state changes.

---

## Flow 1: Onboarding & Workspace Initialization (`/tc-init`)

```mermaid
flowchart TD
    User([User runs /tc-init]) --> CheckDir{Does workspace exist?}
    
    CheckDir -- "No" --> CreateDir["Create root directories:<br/>profile/, courses/, research/, roadmap/, _tc/scripts/"]
    CheckDir -- "Yes" --> ScanProfile{Does profile/preferences.md exist?}
    
    CreateDir --> ScanProfile
    
    ScanProfile -- "No" --> PromptIntake["Prompt Learner Intake:<br/>1. Role (Backend, Student, ML...)<br/>2. Experience (Beginner, Experienced...)<br/>3. Density (Minimal, Balanced, Deep-Dive)<br/>4. Faculty Persona (Hypatia, Feynman...)<br/>5. Practicals (true / false)"]
    
    PromptIntake --> WriteProfile["Write profile/preferences.md<br/>Initialize profile/memlog.md"]
    
    ScanProfile -- "Yes" --> ScanCourses["Scan courses/ directory for active manifests"]
    WriteProfile --> ScanCourses
    
    ScanCourses --> DetermineState{"Active course status?"}
    
    DetermineState -- "No courses found" --> RecCreate["Recommend: /tc-research or /tc-create"]
    DetermineState -- "Course in progress" --> RecTeach["Recommend: /tc-teach"]
    DetermineState -- "Section needs review" --> RecTest["Recommend: /tc-test-me"]
    
    RecCreate --> Done([User begins journey])
    RecTeach --> Done
    RecTest --> Done
```

### What Happens in Each Step:
1. **Directory Validation**: Runs `bootstrapper.py ensure --workspace .`. Checks if the directory structure exists; if missing, creates it safely without touching existing files.
2. **Preference Intake**: If `profile/preferences.md` is missing, prompts the user. If the user indicates `beginner`, sets `competency_level = "beginner"` and defaults the faculty persona to **Hypatia**.
3. **Progress Inspection**: Runs `bootstrapper.py status --json`, parsing all `courses/*/course.toml` manifests and checking which section is currently incomplete.
4. **Next Command Recommendation**: Deterministically outputs the single highest-priority next command.

---

## Flow 2: Autonomous 5-Hat Research (`/tc-research`)

```mermaid
flowchart TD
    User([User runs /tc-research &lt;topic&gt;]) --> InitMarie["Marie Curie initializes research session"]
    
    InitMarie --> CheckBeginner{"Is learner beginner?"}
    CheckBeginner -- "Yes" --> SetHats1["Prioritize Hats:<br/>1. Beginner Friction Hunter<br/>2. Intuitive Metaphorist<br/>3. Industry Practitioner<br/>4. Systems Engineer<br/>5. Academic Purist"]
    CheckBeginner -- "No" --> SetHats2["Standard 5-Hat Ensemble:<br/>1. Industry Practitioner<br/>2. Academic Purist<br/>3. Edge-Case Engineer<br/>4. Modern Ecosystem Reviewer<br/>5. Beginner Friction Hunter"]
    
    SetHats1 --> MultiSearch["Multi-Round Search Loop:<br/>Query 1: Official docs & specs<br/>Query 2: Architectural invariants<br/>Query 3: Breaking changes & pitfalls"]
    SetHats2 --> MultiSearch
    
    MultiSearch --> ScrapeSources["Scrape & extract core text from top sources"]
    
    ScrapeSources --> HatDebate["Stress-Test Context through Active Hats:<br/>Identify unstated assumptions,<br/>syntax traps, and performance cliffs"]
    
    HatDebate --> WriteDossier["Atomic Write to research/&lt;topic-slug&gt;/:<br/>- dossier.md (Taxonomy & Core Models)<br/>- sources.json (URLs, Citations, Timestamps)<br/>- five-hats-critique.md (Dialectic Analysis)"]
    
    WriteDossier --> Done([Dossier ready for Course Creation])
```

### What Happens in Each Step:
1. **Hat Calibration**: `scout.py` checks `--beginner` flag or `profile/preferences.md`. If beginner, adjusts evaluation weights to hunt for cognitive traps and real-world analogies.
2. **Multi-Round Search**: Queries search engines for primary documentation, API changelogs, and common bugs.
3. **Tree-of-Thought Dialectic**: The 5 hats critique the extracted information. Gaps trigger secondary searches.
4. **Dossier Persistence**: Writes complete synthesized notes into `research/<topic-slug>/dossier.md` along with sources.

---

## Flow 3: Autonomous Course Creation (`/tc-create`)

```mermaid
flowchart TD
    User([User runs /tc-create &lt;topic&gt;]) --> LoadContext["Load research/&lt;topic&gt;/dossier.md<br/>and profile/preferences.md"]
    
    LoadContext --> GenPaths["Synthesize 4 Pedagogical Paths:<br/>1. Foundational First-Principles Path<br/>2. Hands-on Project-First Path<br/>3. Problem-Driven Diagnostic Path<br/>4. Intuitive Metaphor-First Path"]
    
    GenPaths --> HatCritique["Universal Critical Hats evaluate paths<br/>for depth, friction, and retention"]
    
    HatCritique --> TriadDebate["Adversarial Triad Debate:<br/>- Daedalus proposes chapter outline<br/>- Marie fact-checks APIs & documentation<br/>- Hypatia audits cognitive leaps & prerequisite ordering"]
    
    TriadDebate --> Consensus{"Triad Reaches Full Consensus?"}
    Consensus -- "Dissent / Gap Identified" --> RefineOutline["Daedalus refines chapters & fills gaps"]
    RefineOutline --> TriadDebate
    
    Consensus -- "Strict Agreement" --> ScaffoldCourse["Scaffold Course Files:<br/>1. courses/&lt;slug&gt;/curriculum-brainstorm.md<br/>2. courses/&lt;slug&gt;/course.toml<br/>3. chapter-XX/section-YY/lesson-plan.md checklists<br/>4. Starter practical.md (if practical_focus=true)"]
    
    ScaffoldCourse --> Done([Course Ready to Teach])
```

### What Happens in Each Step:
1. **Autonomous Synthesis**: `course_builder.py` never stalls asking "how do you want this course created?". It immediately generates 4 distinct curriculum paths.
2. **Hat Stress-Testing**: Scores each path against learner profile preferences.
3. **Triad Deliberation**: Daedalus, Marie, and Hypatia argue until every section has valid prerequisites and empirical backing.
4. **Scaffolding**: Writes `curriculum-brainstorm.md` recording the debate, sets up `course.toml`, creates chapter directories, and writes `lesson-plan.md` checklists.

---

## Flow 4: Socratic Teaching & Adaptive Fork (`/tc-teach`)

```mermaid
flowchart TD
    User([User runs /tc-teach]) --> LoadSession["teach_engine.py session:<br/>1. Load course.toml & preferences.md<br/>2. Find first unfinished section<br/>3. Read lesson-plan.md active concept<br/>4. Load recent courses/&lt;slug&gt;/session.jsonl"]
    
    LoadSession --> DeliverConcept["Faculty Persona delivers SINGLE concept:<br/>- Clear bold mechanics<br/>- Visceral everyday analogy<br/>- Code/table worked example<br/>- Fatal anti-pattern to avoid<br/>- ZERO unexplained jargon"]
    
    DeliverConcept --> LogTurn["Log turn to session.jsonl & memlog.md"]
    
    LogTurn --> TickConcept["advance_lesson_concept():<br/>Toggles checkbox - [x] in lesson-plan.md"]
    
    TickConcept --> CheckSection{"Are all concepts in section checked?"}
    
    CheckSection -- "No (More concepts remain)" --> ForkStandard["Render Next-Action Fork (Concept):<br/>[1] Next Concept<br/>[2] Test Me on this concept<br/>[3] Re-explain / Deeper Analogy<br/>[4] Custom Question"]
    
    CheckSection -- "Yes, but practical lab pending" --> ForkPractical["Render Next-Action Fork (Practical):<br/>[1] Submit Practical Solution<br/>[2] View Lab Requirements<br/>[3] Ask Socratic Guidance<br/>[4] Custom Question"]
    
    CheckSection -- "Yes, and practical passed" --> AutoCompile["notes_compiler.py compile:<br/>1. Auto-compile chapter notes.md<br/>2. Run readability & jargon audit<br/>3. Advance section status to 'review'<br/>4. Mirror milestone to memlog.md"]
    
    AutoCompile --> ForkComplete["Render Next-Action Fork (Completed):<br/>[1] Advance to Next Section<br/>[2] Comprehensive Section Test<br/>[3] Review Compiled Notes<br/>[4] Custom Question"]
    
    ForkStandard --> UserChoice([Learner selects option])
    ForkPractical --> UserChoice
    ForkComplete --> UserChoice
```

### What Happens in Each Step:
1. **Session Recovery**: `teach_engine.py session` loads the course state and the last 5 turns from `session.jsonl`.
2. **Single-Concept Delivery**: Explains exactly one concept with zero jargon leakage.
3. **Atomic Checkmarking**: `lesson_tracker.py` flips `- [ ]` to `- [x]`.
4. **Adaptive Next-Action Fork**: If a practical lab is pending, option `[1]` transforms to submit practical code. If all concepts and labs are finished, `notes_compiler.py` compiles `notes.md` automatically and offers section advancement.

---

## Flow 5: In-Loop Practical Lab & AI Validation (`/tc-practicals`)

```mermaid
flowchart TD
    User([Learner reaches practical lab]) --> ViewLab["Learner reads section-XX/practical.md:<br/>Specifications, boundary constraints, starter template"]
    
    ViewLab --> WriteCode["Learner writes solution in workspace"]
    
    WriteCode --> Submit["Submit solution via /tc-practicals or tc.py practicals evaluate-lesson"]
    
    Submit --> AIEval["practical_evaluator.py evaluates code:<br/>1. Syntax & structure check<br/>2. Boundary condition handling<br/>3. Defensive guards & assertions<br/>4. Execution error safety<br/>5. Idiomatic code craft"]
    
    AIEval --> Score{"Score &gt;= 70 and all invariants met?"}
    
    Score -- "No" --> Reject["Write practical-result.json: verdict=NEEDS_WORK<br/>Provide actionable diagnostic feedback"]
    Reject --> WriteCode
    
    Score -- "Yes" --> Pass["Write practical-result.json: verdict=PASS<br/>Log practical milestone to memlog.md"]
    
    Pass --> UnlockSection["Unlock section completion in teach_engine.py"]
    UnlockSection --> NextStep([Ready to compile notes & test])
```

### What Happens in Each Step:
1. **Lab Scaffolding**: `practical_evaluator.py` creates `practical.md` with explicit functional requirements.
2. **AI Invariant Evaluation**: Checks student code against safety rules (boundary checks, null checks, error handling).
3. **Result Gating**: Writes `practical-result.json`. A `PASS` verdict is required before the section can lock as complete.

---

## Flow 6: Diagnostic Testing & Mastery Ledger (`/tc-test-me`)

```mermaid
flowchart TD
    User([User runs /tc-test-me]) --> LoadSection["diagnostic_tester.py probe:<br/>Loads active section & compiled notes.md"]
    
    LoadSection --> FormulateQuestion["Generate Bloom Scenario Dilemma:<br/>- Level 2: Comprehension (Mental Model)<br/>- Level 4: Analysis (Mechanism Trade-off)<br/>- Level 5: Evaluation (Failure Mode Debugging)<br/>ZERO code copy-pasting requested!"]
    
    FormulateQuestion --> LearnerAnswers["Learner explains reasoning in chat"]
    
    LearnerAnswers --> GradeResponse["diagnostic_tester.py evaluate:<br/>Inspects causal logic, mechanisms, and common pitfalls"]
    
    GradeResponse --> Result{"Mastery Demonstrated?"}
    
    Result -- "Misconception Detected" --> Remediation["Provide Socratic correction<br/>Log misconception to memlog.md<br/>Schedule spaced review"]
    
    Result -- "Mastered" --> LogLedger["Record passing score to ledger.toml:<br/>- Timestamp<br/>- Bloom level<br/>- Question prompt & score<br/>Update section status to 'mastered'"]
    
    LogLedger --> Done([Section Mastered & Verified])
```

### What Happens in Each Step:
1. **Question Formulation**: `diagnostic_tester.py` creates a scenario question targeting causal understanding.
2. **Evaluation**: Grades reasoning without requiring code pasting.
3. **Tamper-Evident Ledger**: Appends the test result to `courses/<slug>/ledger.toml` with advisory file locking.
