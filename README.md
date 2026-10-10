# TextCourses (`textcourses.com`)

> **Autonomous Apprenticeship Engine** — An open, sovereign, filesystem-native learning framework replacing passive video courses and amnesic chat feeds with interactive, turn-by-turn AI apprenticeship.

---

## Architecture Overview

TextCourses couples an LLM Socratic tutor with a deterministic, local-first filesystem substrate:
- **Zero Heavy Infrastructure**: Runs entirely on the learner's local machine or git repo. No databases, Docker daemons, cloud dependencies, or telemetry.
- **Hybrid Deterministic Substrate**: State mutation, progress tracking, assessment ledgers, DAG validation, and source hashing are performed by standalone Python scripts via `uv run`. AI agents govern pedagogical delivery, conversation, and evaluation.
- **Atomic Operations**: All state writes use POSIX atomic file replacement (`.tmp` write &rarr; `os.fsync` &rarr; `os.replace`) to prevent file corruption during interrupted turns, and `fcntl.flock` on append-only ledgers.
- **Enforceable Context Budget (AD-5)**: Stage Loading Matrix strictly controls file reads per skill, keeping turn budgets under 4,000 tokens and preventing out-of-order concept leaks.
- **Zero Code-Pasting in Chat (FR-13)**: Diagnostic testing is 100% question-based (hinge dilemmas, mechanism trade-offs, and failure mode probing); hands-on code lives strictly in verifiable local portfolio workspaces.

---

## Directory Structure

```text
.
├── _tc/
│   └── scripts/                  # Canonical deterministic runtime engine scripts
│       ├── auditor.py            # Pre-flight curriculum auditor & vocabulary validator
│       ├── bootstrapper.py       # Workspace bootstrapper & repo scanner
│       ├── context.py            # Stage-aware context manifest engine
│       ├── course_builder.py     # Course scaffolding architect & Triad consensus
│       ├── dag.py                # Prerequisite DAG validator & topological sorter
│       ├── diagnostic_tester.py  # 100% question-based diagnostic tester
│       ├── hash_tracker.py       # SHA-256 source delta & integrity tracker
│       ├── ledger.py             # Atomic append-only assessment ledger & summarizer
│       ├── lesson_tracker.py     # Session hygiene & lesson-plan progress tracker
│       ├── manifest.py           # Atomic TOML manifest manager (course & roadmap)
│       ├── migrator.py           # Consent-gated schema migrator
│       ├── notes_compiler.py     # Flow-preserving textbook notes compiler
│       ├── practical_evaluator.py# Portfolio project generator & 4-lens reviewer
│       ├── redirector.py         # Course evolution & non-destructive deprecation
│       ├── scout.py              # Documentation scout & research cache manager
│       └── teach_engine.py       # Conversational single-concept teach orchestrator
├── skills/                       # The 9 TextCourses skill packages
│   ├── tc-init/                  # Workspace initialization & repo scanner
│   ├── tc-redirect-course/       # Course evolution & source delta updater
│   ├── tc-migrate/               # Consent-gated workspace schema migrator
│   ├── tc-research/              # Documentation research scout & Tier 1/2 caching
│   ├── tc-verify-course/         # Pre-flight curriculum auditor & vocabulary checks
│   ├── tc-create/                # 5-archetype scaffolding & Triad consensus loop
│   ├── tc-teach/                 # Single-concept instruction & Next-Action Fork
│   ├── tc-test-me/               # Pure question-based diagnostic assessment engine
│   └── tc-practicals/            # Hands-on portfolio project generator & 4-lens reviewer
├── courses/                      # Generated course workspaces
├── tests/                        # Comprehensive pytest test suite (167 passing tests)
├── pyproject.toml                # Project configuration & test dependencies
└── README.md                     # Engine documentation & CLI reference
```

---

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (Fast Python package and tool runner)

Install `uv` (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## The 9 TextCourses Skills

| Skill | Command | Role & Responsibility | Core Invariant |
|-------|---------|-----------------------|----------------|
| **tc-init** | `/tc-init` | Workspace initialization & repository scanner | Detects tech stack, inspects `.gitignore`, initializes `tc.toml` and `roadmap.toml`. |
| **tc-redirect-course** | `/tc-redirect-course` | Course evolution & deprecation manager | Cryptographic SHA-256 delta tracking; completed `notes.md` are 100% immutable. |
| **tc-migrate** | `/tc-migrate` | Consent-gated workspace schema migrator | Generates `migration-plan.md`; zero disk writes without typed confirmation. |
| **tc-research** | `/tc-research` | Documentation scout & knowledge caching | Tier 1 official docs scrape + Tier 2 LLM fallback; confidence-weighted sources. |
| **tc-verify-course** | `/tc-verify-course` | Pre-flight curriculum auditor & vocabulary validator | Strict DAG cycle detection, vocabulary prerequisite check, <6 concepts per section. |
| **tc-create** | `/tc-create` | Course scaffolding architect & Triad consensus | 5 pedagogical archetypes; automated Architect-Auditor-Pedagogue consensus. |
| **tc-teach** | `/tc-teach` | Single-concept conversational instruction | Strictly 1 concept per turn; Next-Action Fork; automated `notes.md` compilation. |
| **tc-test-me** | `/tc-test-me` | 100% question-based conceptual diagnostic testing | Zero code-pasting in chat; Cumulative Boundary Rule; atomic `test-ledger.jsonl`. |
| **tc-practicals** | `/tc-practicals` | Applied portfolio project generator & 4-lens reviewer | Deterministic deliverable contracts; misconception weighting; 4-lens review pass. |

---

## Deterministic Runtime Engine CLI Reference

All scripts declare PEP 723 metadata and execute via `uv run _tc/scripts/<script>.py`.

### 1. Workspace Bootstrapper (`bootstrapper.py`)
```bash
# Scan repository and initialize sovereign workspace
uv run _tc/scripts/bootstrapper.py init --workspace .
```

### 2. Manifest Manager (`manifest.py`)
```bash
# Initialize course manifest
uv run _tc/scripts/manifest.py init-course --path ./courses/my-course --slug my-course --title "My Course" --archetype systems

# Advance section status
uv run _tc/scripts/manifest.py advance --path ./courses/my-course --chapter 1 --section 1 --status review

# Validate manifest schema
uv run _tc/scripts/manifest.py validate --path ./courses/my-course/course.toml
```

### 3. Assessment Ledger Engine (`ledger.py`)
```bash
# Atomically append assessment outcome with POSIX file lock
uv run _tc/scripts/ledger.py append --path ./courses/my-course --record '{
  "course": "my-course",
  "chapter": "01-core",
  "section": "01-basics",
  "question_type": "hinge_scenario",
  "prompt": "Evaluate concurrency boundary condition",
  "learner_response": "Mutex held across await point causes deadlock",
  "outcome": "pass"
}'

# Compact misconception summary (<100 tokens)
uv run _tc/scripts/ledger.py summarize --path ./courses/my-course
```

### 4. DAG Validator (`dag.py`)
```bash
# Validate dependency graph for cycles and missing prerequisites
uv run _tc/scripts/dag.py validate --path ./courses/my-course/course.toml

# Generate topological build order
uv run _tc/scripts/dag.py order --path ./courses/my-course/course.toml
```

### 5. Context Manifest Engine (`context.py`)
```bash
# Enforce Stage Loading Matrix for a skill
uv run _tc/scripts/context.py get-manifest --skill tc-teach --path ./courses/my-course
```

### 6. Source Hash Tracker (`hash_tracker.py`)
```bash
# Create cryptographic SHA-256 snapshot of source references
uv run _tc/scripts/hash_tracker.py snapshot --path ./courses/my-course/plan/sources --output ./courses/my-course/plan/sources/ledger.toml

# Detect delta changes (added, modified, deleted)
uv run _tc/scripts/hash_tracker.py diff --path ./courses/my-course/plan/sources --manifest ./courses/my-course/plan/sources/ledger.toml
```

### 7. Course Scaffolding Architect (`course_builder.py`)
```bash
# Scaffold full course tree from approved manifest
uv run _tc/scripts/course_builder.py scaffold --manifest-data '{"course": {"slug": "demo", "title": "Demo Course", "archetype": "systems"}}'
```

### 8. Pre-Flight Auditor (`auditor.py`)
```bash
# Audit course manifest for structural and vocabulary consistency
uv run _tc/scripts/auditor.py audit --manifest ./courses/my-course/course.toml
```

### 9. Research Scout (`scout.py`)
```bash
# Scrape or cache documentation sources with confidence scoring
uv run _tc/scripts/scout.py scrape --url https://docs.python.org/3/ --output ./courses/my-course/plan/sources/cache/
```

### 10. Session Hygiene & Lesson Tracker (`lesson_tracker.py`)
```bash
# Inspect concept progress and resolve next uncompleted concept
uv run _tc/scripts/lesson_tracker.py inspect --plan ./courses/my-course/chapters/01-core/01-basics/lesson-plan.md

# Tick concept checkmark atomically
uv run _tc/scripts/lesson_tracker.py tick --plan ./courses/my-course/chapters/01-core/01-basics/lesson-plan.md --concept 1
```

### 11. Textbook Notes Compiler (`notes_compiler.py`)
```bash
# Compile completed section into notes.md textbook and update status to review
uv run _tc/scripts/notes_compiler.py compile \
  --course ./courses/my-course \
  --chapter 01-core \
  --section 01-basics \
  --recap "State machine transitions" --recap "Channel backpressure" --recap "Graceful cancellation" \
  --body "Full compiled textbook notes body..."
```

### 12. Conversational Teaching Engine (`teach_engine.py`)
```bash
# Discover active session concept
uv run _tc/scripts/teach_engine.py session --course my-course

# Advance concept and auto-trigger notes compilation on section completion
uv run _tc/scripts/teach_engine.py advance --course my-course

# Render standardized 4-option Next-Action Fork
uv run _tc/scripts/teach_engine.py fork
```

### 13. Diagnostic Assessment Engine (`diagnostic_tester.py`)
```bash
# Prepare eligible test sections enforcing Cumulative Boundary Rule
uv run _tc/scripts/diagnostic_tester.py prepare --course my-course

# Record diagnostic outcome and advance review section to completed
uv run _tc/scripts/diagnostic_tester.py record \
  --course my-course \
  --chapter 01-core \
  --section 01-basics \
  --type hinge_scenario \
  --prompt "What invariant breaks when mutex is unlocked before flush?" \
  --response "Dirty data can be read by concurrent readers." \
  --outcome pass
```

### 14. Practical Project Evaluator (`practical_evaluator.py`)
```bash
# Initialize customizable project brief weighted by test-ledger misconceptions
uv run _tc/scripts/practical_evaluator.py init-brief \
  --course my-course \
  --complexity medium \
  --time-budget "weekend_sprint (4 hours)"

# Execute 4-Lens Project Review Pass and complete course on PASS
uv run _tc/scripts/practical_evaluator.py review \
  --course my-course \
  --project-id 01 \
  --verdict PASS \
  --functional-lens "All deliverables present and operational." \
  --edge-lens "Handles network disconnects and edge cases." \
  --architecture-lens "Clean separation, zero unneeded dependencies." \
  --verification-lens "All unit and integration tests passing."
```

---

## Running the Automated Test Suite

Every capability across the runtime engine, onboarding lifecycle, curriculum generation, instruction delivery, and assessment layers is verified by comprehensive automated unit and integration tests:

```bash
# Run the entire test suite
uv run pytest

# Run tests with verbose summary
uv run pytest -v
```

Currently, **167 tests pass cleanly (100% pass rate)**.

---

## Invariants & Design Principles

1. **Zero External Daemon/Database Dependencies**: Everything runs through standard POSIX file operations and `uv run`.
2. **Deterministic Mutation**: State changes are executed by audited Python scripts, never by unvalidated AI file rewrites.
3. **Completed Notes Immutability**: Once notes are compiled and sections completed, their content is frozen bit-for-bit to protect learner trust and knowledge retention.
4. **Pure Question-Based Testing**: Diagnostic checks evaluate boundary mental models without forcing learners to copy-paste code in chat.
5. **Applied Proof-of-Work**: Competence is demonstrated through authentic project code built in sovereign local repositories and verified across 4 objective review lenses.
