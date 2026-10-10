# TextCourses (`textcourses.com`)

> **Autonomous Apprenticeship Engine** — An open, sovereign, filesystem-native learning framework replacing passive video courses and amnesic chat feeds with interactive, turn-by-turn AI apprenticeship.

---

## Architecture Overview

TextCourses couples an LLM Socratic tutor with a deterministic filesystem substrate:
- **Zero Heavy Infrastructure**: Runs entirely on the learner's local machine or git repo. No databases, Docker daemons, or cloud lock-in required.
- **Hybrid Deterministic Substrate**: State mutation, progress tracking, assessment ledgers, and DAG validation are performed by standalone Python scripts via `uv run`. AI agents govern pedagogical delivery, conversation, and evaluation.
- **Atomic Operations**: All state writes use POSIX atomic file replacement (`.tmp` write &rarr; `os.fsync` &rarr; `os.replace`) to prevent file corruption during interrupted turns.

---

## Directory Structure

```text
├── _tc/
│   └── scripts/             # Canonical deterministic runtime engine scripts
│       └── manifest.py      # TOML manifest manager (course & roadmap state)
├── skills/                  # Skill packages for agent runtime environments
│   ├── tc-init/             # Workspace initialization & onboarding
│   ├── tc-author/           # Curriculum & syllabus generation
│   ├── tc-teach/            # Interactive instructional delivery
│   ├── tc-test-me/          # Question-based assessment & evaluation
│   ├── tc-practicals/       # Portfolio project execution & verification
│   └── tc-audit/            # Curriculum validation & linting
├── tests/                   # Automated unit & integration test suite
│   └── test_manifest.py     # Manifest engine verification tests
├── pyproject.toml           # Project metadata & test configuration
└── README.md                # Developer documentation
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

## Developer Workflow: Change Implementation Protocol

Whenever you implement or modify any feature, fix, or script, follow this checklist immediately:

### 1. Code Standards
- **PEP 723 Metadata**: Every standalone script in `_tc/scripts/` must declare inline script dependencies at the top:
  ```python
  #!/usr/bin/env python3
  # /// script
  # requires-python = ">=3.11"
  # dependencies = [
  #     "tomli-w>=1.0.0",
  # ]
  # ///
  ```
- **Atomic Writes**: Never write to manifest or state files directly in-place. Always write to a temporary file, flush and sync (`os.fsync`), and atomically replace (`os.replace`).
- **Structured I/O Contract**:
  - Exit `0` on success with valid JSON on `stdout`.
  - Exit `1` on failure with `{"ok": false, "error": "<message>"}` on `stderr`.
- **Pure Self-Containment**: Do not introduce heavy third-party framework dependencies or external database drivers into runtime scripts.

### 2. Test Requirement
- **Write Tests for Every Change**: Any new function, command, or bug fix must have corresponding tests added under `tests/test_<module>.py`.
- Tests must cover:
  - Happy path invocations.
  - Edge cases (missing files, malformed schema, out-of-bounds inputs).
  - Atomic replacement mechanics (ensuring temporary files are cleaned up).

### 3. Immediate Verification
Run the verification steps in order:

```bash
# Step 1: Verify the modified script directly via uv run
uv run _tc/scripts/<script_name>.py --help

# Step 2: Run the full test suite
uv run pytest

# Step 3: Check git status to ensure no stray .tmp files or cache artifacts
git status
```

---

## Running Tests

All automated tests are executed via `uv run pytest`.

### Run All Tests
```bash
uv run pytest
```

### Run a Specific Test File
```bash
uv run pytest tests/test_manifest.py
```

### Run Tests with Verbose Output
```bash
uv run pytest -v
```

### Run a Specific Test Function
```bash
uv run pytest tests/test_manifest.py -k "test_init_course_success"
```

---

## Runtime Scripts CLI Reference

### Manifest Manager (`_tc/scripts/manifest.py`)

Handles reading, validating, and mutating `course.toml` and `roadmap.toml` manifests.

#### Display Help
```bash
uv run _tc/scripts/manifest.py --help
```

#### Initialize a Course Manifest
```bash
uv run _tc/scripts/manifest.py init-course \
  --path ./my-course \
  --slug rust-basics \
  --title "Rust Basics" \
  --archetype applied_creation
```

#### Initialize a Track Roadmap Manifest
```bash
uv run _tc/scripts/manifest.py init-roadmap \
  --path ./my-track \
  --title "Systems Programming Track"
```

#### Get Current Course or Roadmap Status
```bash
uv run _tc/scripts/manifest.py get-status --path ./my-course
```
*Output:*
```json
{
  "ok": true,
  "type": "course",
  "slug": "rust-basics",
  "title": "Rust Basics",
  "status": "not_started",
  "total_chapters": 0,
  "total_sections": 0,
  "completed_sections": 0,
  "active_chapter": null,
  "active_section": null
}
```

#### Advance a Section Status
```bash
uv run _tc/scripts/manifest.py advance \
  --path ./my-course \
  --chapter 1 \
  --section 1 \
  --status in_progress
```
*Valid statuses:* `not_started`, `in_progress`, `review`, `completed`.

#### Validate Manifest Schema
```bash
uv run _tc/scripts/manifest.py validate --path ./my-course/course.toml
```

---

## Verification & Pre-Commit Checklist

Before committing or pushing any change:

- [ ] Script runs independently with `uv run _tc/scripts/<script>.py`.
- [ ] Unit tests pass cleanly (`uv run pytest` exits 0).
- [ ] No temporary files (`*.tmp`), `.pyc`, or `__pycache__` lingering on disk.
- [ ] Error paths return exit code 1 and structured JSON on `stderr`.
- [ ] Manifest changes preserve atomic write guarantees.
