# TextCourses (`textcourses.com`)

> **The Sovereign, Local-First AI Apprenticeship Engine**  
> *Transform passive video feeds and amnesic chat into interactive, turn-by-turn AI mastery.*

---

## What is TextCourses?

TextCourses is an open-source, filesystem-native learning framework designed for deep, active mastery. Unlike online courses where you passively watch videos or chat windows that forget everything after a few turns, TextCourses gives you:

1. **A Personal Socratic Tutor**: Learn concept by concept with a faculty of distinct personas (Hypatia, Feynman, Turing, Daedalus, Marie Curie).
2. **Autonomous Multi-Path Curriculum**: Never get stalled answering "how do you want this course created?". TextCourses automatically brainstorms 4 curriculum paths, stress-tests them with critical hats, and debates tradeoffs before building.
3. **In-Loop Hands-On Practicals**: Solve real coding challenges in your workspace. AI evaluates your code against boundary safety and correctness before unlocking the next chapter.
4. **Radical Readability & Zero-Unexplained-Jargon**: Explanations use plain English and physical everyday analogies. Jargon is demystified before you ever encounter it.
5. **100% Local-First & Sovereign**: Your courses, textbook notes, and code live in your local files or git repo. Zero cloud accounts, zero lock-in, zero telemetry.

---

## Quickstart: Zero to First Lesson in 60 Seconds

### 1. Install TextCourses Skills
Install all 10 TextCourses skills into your AI coding agent (Antigravity, Claude Code, Cursor, Codex, OpenCode, Amp, etc.):
```bash
# Install all skills into your AI agent in this project
npx skills add dasavarambharadwaj/text-courses-redesign --all

# Or globally across all workspaces (-g)
npx skills add dasavarambharadwaj/text-courses-redesign --all -g

# Or explicitly using the GitHub repository URL:
npx skills add https://github.com/dasavarambharadwaj/text-courses-redesign --skill '*' --agent '*'
```

### 2. Prerequisites
- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) (Fast Python package runner)
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### 3. Initialize Your Workspace
In your AI coding agent chat or terminal:
```bash
# Via Slash Command in Chat
/tc-init

# Or directly via CLI
uv run _tc/scripts/tc.py init --workspace .
```
This sets up your `profile/preferences.md` (role, experience level, preferred tutor, and hands-on practical focus).

### 4. Research Any Topic Autonomously
Before creating a course, let **Marie Curie** research official docs, specifications, and modern practices:
```bash
/tc-research distributed-systems
```
This generates an authoritative dossier in `research/distributed-systems/dossier.md` stress-tested through 5 critical hats.

### 5. Create Your Personalized Course
Let the Faculty Triad (Daedalus, Marie, Hypatia) autonomously debate and scaffold your curriculum:
```bash
/tc-create "Distributed Consensus & Raft"
```
TextCourses synthesizes 4 distinct curricular paradigms and scaffolds `courses/distributed-consensus/` with zero stalling.

### 6. Begin Conversational Socratic Learning
```bash
/tc-teach
```
Your faculty tutor will deliver one concept at a time, check off concepts in `lesson-plan.md`, log conversational turns to `session.jsonl`, and provide the dynamic **Next-Action Fork** at the end of every message!

---

## The 10 TextCourses Skills

Installed via `npx skills add dasavarambharadwaj/text-courses-redesign --all` and ready to trigger directly in chat:

| Skill Command | Lead Persona | What It Does |
| :--- | :--- | :--- |
| **`/tc-init`** | Workspace Bootstrapper | Scans workspace progress, interviews your goals, and tells you what to do next. |
| **`/tc-research`** | 🔬 Marie Curie | Autonomously searches the web, analyzes 5 critical hats, and writes topic dossiers. |
| **`/tc-create`** | 🛠️ Daedalus | Synthesizes 4 curriculum paths, debates Triad consensus, and scaffolds course files. |
| **`/tc-teach`** | 🦉 Hypatia / ⚡ Feynman | Teaches single concepts conversationally with analogies, logging turns to `session.jsonl`. |
| **`/tc-practicals`** | 🛠️ Daedalus | Scaffolds hands-on coding challenges (`practical.md`) and validates code via AI. |
| **`/tc-test-me`** | 📐 Alan Turing | 100% question-based diagnostic inquiries across Bloom's Taxonomy (Zero code-pasting!). |
| **`/tc-roadmap`** | Macro Architect | Computes prerequisite DAGs, renders ASCII dependency trees, and guides your path. |
| **`/tc-redirect-course`** | Curriculum Editor | Dynamically adds, skips, or reorganizes sections in-flight without losing past notes. |
| **`/tc-verify-course`** | System Auditor | Audits broken markdown links, missing files, and verifies cross-platform SHA-256 hashes. |
| **`/tc-migrate`** | Schema Migrator | Safely migrates legacy course formats to the modern streamlined layout with your consent. |

---

## The Faculty Personas

Choose who teaches you, or let them tag-team when you need a different perspective:

- 🦉 **Hypatia (The Empathetic Tutor)**: Gentle Socratic stepping stones, real-world physical analogies, radical readability, and zero unexplained jargon. *(Default for beginners!)*
- ⚡ **Richard Feynman (The Intuitionist)**: Vivid everyday mental models, simplifying hard problems, and cutting through academic jargon.
- 📐 **Alan Turing (The Formalist)**: Mathematical precision, state machine invariants, formal correctness, and concurrency boundaries.
- 🛠️ **Daedalus (The Master Craftsman)**: Pragmatic code craft, defensive assertions, hands-on lab challenges, and execution safety.
- 🔬 **Marie Curie (The Empirical Investigator)**: Official documentation, RFCs, empirical verification, and 5-hat research.

---

## Unified CLI Reference (`tc.py`)

All engine functionality can be invoked directly from your command line:

```bash
# Workspace inspection
uv run _tc/scripts/tc.py init --workspace .

# Autonomous research
uv run _tc/scripts/tc.py research scout --slug async-rust --topic "Async Rust & Tokio"

# Course creation
uv run _tc/scripts/tc.py create create --slug async-rust --title "Async Rust" --topic "Tokio internals"

# Teaching session & concept advance
uv run _tc/scripts/tc.py teach session --course async-rust --json
uv run _tc/scripts/tc.py teach advance --course async-rust --json

# Practical evaluation
uv run _tc/scripts/tc.py practicals evaluate-lesson --course async-rust --section sec-01 --submission "..."

# Diagnostic testing
uv run _tc/scripts/tc.py test probe --course async-rust

# Readability & jargon audit
uv run _tc/scripts/tc.py notes audit-readability --notes-file courses/async-rust/chapter-01/section-01/notes.md --json

# Prerequisite DAG inspection
uv run _tc/scripts/tc.py dag inspect
```

---

## In-Depth Documentation

For developers, contributors, and technical enthusiasts, explore our comprehensive technical guides:

- 🏗️ **[System Architecture](docs/ARCHITECTURE.md)**: Three-tier architecture, hybrid deterministic substrate, sovereign filesystem layout, and core invariants.
- 🎭 **[Agents, Personas & Skills Guide](docs/AGENTS_AND_SKILLS.md)**: Deep dive into all 10 skills, the 5 faculty personas, and how they collaborate.
- 🔄 **[Execution Flows & Lifecycles](docs/EXECUTION_FLOWS.md)**: Step-by-step visual Mermaid flowcharts for every interaction and decision gate.
- 🧠 **[Memory, Persistence & State Architecture](docs/MEMORY_AND_STORAGE.md)**: What every file remembers, when it remembers it, and the dual-register knowledge model (`notes.md` vs `memlog.md`).
- 💻 **[Codebase Internals & Runtime Reference](docs/CODEBASE_INTERNALS.md)**: Script contracts, function signatures, data schemas, and the 230-test regression suite.

---

## Verification & Automated Test Suite

TextCourses maintains a 100% green, zero-mock regression test suite verifying all 18 scripts and skills:

```bash
uv run pytest
```
*Current test status: **230 passed** across all test suites.*

---

## License

TextCourses is open-source software licensed under the MIT License.
