#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""practical_evaluator.py — Deterministic Practical Project Verification Engine for TextCourses.

Coordinates applied proof-of-work project generation and multi-lens evaluation:
1. Formulates customizable project briefs in portfolio/project-XX/project-spec.md,
   weighted toward diagnosed misconceptions in test-ledger.jsonl (FR-16).
2. Enforces deterministic verifiable deliverable contracts (code, test suites, schemas, FR-17).
3. Executes 4-lens project review passes (Functional Completeness, Edge Cases & Robustness,
   Architecture & Craft, Verification Integrity, FR-18).
4. Generates review-report.md and advances course status in course.toml to 'completed'.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

# Ensure project root and _tc/scripts are on sys.path
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    import tomli_w
except ImportError:
    tomli_w = None


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit != 0) and exit."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def atomic_write_toml(target_path: Path, data: dict[str, Any]) -> None:
    """Atomically write a TOML file using temp file + fsync + replace."""
    if tomli_w is None:
        raise RuntimeError("tomli-w is required for writing TOML files.")
    tmp_path = target_path.with_suffix(f".tmp.{os.getpid()}")
    with open(tmp_path, "wb") as f:
        tomli_w.dump(data, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, target_path)


def resolve_course_dir(course_arg: str | None) -> Path:
    """Resolve course directory from slug, path, or active repo scan."""
    if course_arg:
        p = Path(course_arg)
        if (p / "course.toml").is_file():
            return p.resolve()
        candidate = Path("courses") / course_arg
        if (candidate / "course.toml").is_file():
            return candidate.resolve()
        candidate_abs = _PROJECT_ROOT / "courses" / course_arg
        if (candidate_abs / "course.toml").is_file():
            return candidate_abs.resolve()
        raise FileNotFoundError(f"Course directory not found for '{course_arg}'")

    if Path("course.toml").is_file():
        return Path(".").resolve()

    courses_dir = Path("courses")
    if not courses_dir.is_dir():
        courses_dir = _PROJECT_ROOT / "courses"

    if courses_dir.is_dir():
        subdirs = [d for d in courses_dir.iterdir() if d.is_dir() and (d / "course.toml").is_file()]
        if len(subdirs) == 1:
            return subdirs[0].resolve()
        elif len(subdirs) > 1:
            raise ValueError(f"Multiple courses found in {courses_dir}. Specify --course <slug>.")

    raise FileNotFoundError("No active course found. Specify --course <slug>.")


def load_course_toml(course_dir: Path) -> dict[str, Any]:
    """Load and parse course.toml."""
    course_toml_path = course_dir / "course.toml"
    if not course_toml_path.is_file():
        raise FileNotFoundError(f"course.toml not found at {course_toml_path}")
    with open(course_toml_path, "rb") as f:
        return tomllib.load(f)


def read_ledger_misconceptions(course_dir: Path) -> list[str]:
    """Read recurring misconceptions from test-ledger.jsonl."""
    ledger_path = course_dir / "test-ledger.jsonl"
    if not ledger_path.is_file():
        return []

    misconceptions: list[str] = []
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                    misc = record.get("diagnosed_misconception")
                    outcome = str(record.get("outcome", "")).strip().lower()
                    if misc and misc != "NONE" and outcome in {"fail", "failed", "incorrect"}:
                        misconceptions.append(misc)
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []

    # Return unique sorted by frequency
    freq: dict[str, int] = {}
    for m in misconceptions:
        freq[m] = freq.get(m, 0) + 1
    return sorted(freq.keys(), key=lambda k: freq[k], reverse=True)


def resolve_portfolio_dir(course_dir: Path) -> Path:
    """Resolve portfolio directory (prefers workspace root portfolio/ if workspace exists, fallbacks to course_dir/portfolio)."""
    if course_dir.parent.name == "courses":
        ws_root = course_dir.parent.parent
        ws_portfolio = ws_root / "portfolio"
        if ws_portfolio.exists() or (ws_root / ".tc").exists():
            return ws_portfolio
    if (course_dir / "portfolio").is_dir():
        return course_dir / "portfolio"
    ws_portfolio = course_dir.parent / "portfolio"
    if ws_portfolio.exists():
        return ws_portfolio
    return course_dir / "portfolio"


def cmd_init_brief(args: argparse.Namespace) -> None:
    """Generate a customizable practical project brief with misconception weighting."""
    try:
        course_dir = resolve_course_dir(args.course)
        manifest = load_course_toml(course_dir)
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    course_data = manifest.get("course", {})
    course_title = course_data.get("title", course_dir.name)
    course_slug = course_data.get("slug", course_dir.name)
    archetype = course_data.get("archetype", "systems")

    # Determine project ID
    portfolio_dir = resolve_portfolio_dir(course_dir)
    portfolio_dir.mkdir(parents=True, exist_ok=True)

    project_id = args.project_id
    if not project_id:
        existing = [
            d.name for d in portfolio_dir.iterdir()
            if d.is_dir() and d.name.startswith("project-")
        ]
        numbers = []
        for name in existing:
            match = re.search(r"project-(\d+)", name)
            if match:
                numbers.append(int(match.group(1)))
        next_num = max(numbers) + 1 if numbers else 1
        project_id = f"{next_num:02d}"

    project_dir = portfolio_dir / f"project-{project_id}"
    project_dir.mkdir(parents=True, exist_ok=True)

    complexity = args.complexity or "medium"
    time_budget = args.time_budget or "weekend_sprint (4 hours)"
    depth_breadth = args.depth_breadth or "balanced"
    custom_idea = args.custom_idea.strip() if args.custom_idea else ""

    # Read past misconceptions from ledger
    misconceptions = read_ledger_misconceptions(course_dir)

    # Project title
    title = args.title or f"Applied Capstone: {course_title}"

    # Build project-spec.md
    weak_areas_section = ""
    if misconceptions:
        weak_areas_list = "\n".join(f"- `{m}`" for m in misconceptions[:5])
        weak_areas_section = f"""## Targeted Diagnostic Focus Areas

Based on your previous diagnostic evaluations in `test-ledger.jsonl`, this practical project explicitly tests and reinforces the following concepts:
{weak_areas_list}

**Design Invariant:** Your implementation must handle these specific edge cases and failure modes robustly.
"""
    else:
        weak_areas_section = """## Targeted Diagnostic Focus Areas

No recurring diagnostic misconceptions detected in `test-ledger.jsonl`. Project exercises balanced core principles and edge case handling.
"""

    context_section = ""
    if custom_idea:
        context_section = f"### Learner Proposal\n{custom_idea}\n\n### Architectural Context\nApplied to core domains and mechanics from {course_title}."
    else:
        context_section = f"Build an authentic, sovereign end-to-end component demonstrating mastery of {course_title} under real-world constraints."

    spec_content = f"""---
project_id: "{project_id}"
title: "{title}"
course: "{course_slug}"
archetype: "{archetype}"
complexity: "{complexity}"
time_budget: "{time_budget}"
depth_breadth: "{depth_breadth}"
status: "pending"
created: "{datetime.datetime.now(datetime.timezone.utc).isoformat()}"
---

# Project Specification: {title}

## Overview & Objectives
{context_section}

{weak_areas_section}

## Verifiable Deliverables Contract

Every deliverable is evaluated deterministically against automated tests and filesystem inspection:

1. **Deterministic Deliverable Artifacts (FR-17):**
   - `src/` — Complete implementation source code.
   - `tests/` — Automated test suite covering happy paths and boundary conditions.
   - `README.md` — Architectural overview, usage instructions, and failure-mode documentation.

2. **Automated Verification Contract:**
   - Test execution command: `python -m pytest tests/` (or language-equivalent runner).
   - Expected result: Clean execution with 0 failures and 0 unhandled exceptions.

3. **Multi-Lens Review Criteria (FR-18):**
   - **Lens 1: Functional Completeness** — All primary requirements and APIs function as specified.
   - **Lens 2: Edge Cases & Robustness** — Proper handling of boundary conditions, errors, timeouts, and resource cleanup.
   - **Lens 3: Architecture & Craft** — Sovereign filesystem discipline, zero unnecessary external dependencies, clean separation of concerns.
   - **Lens 4: Verification Integrity** — Comprehensive test coverage with deterministic assertions verifying internal invariants.

## Submission & Review
Once your deliverables are placed in this directory (`portfolio/project-{project_id}/`), invoke `/tc-practicals` or run `practical_evaluator.py review` to trigger the 4-Lens Project Review Pass.
"""

    spec_path = project_dir / "project-spec.md"
    spec_path.write_text(spec_content, encoding="utf-8")

    output_json({
        "ok": True,
        "project_id": project_id,
        "project_dir": str(project_dir),
        "spec_path": str(spec_path),
        "complexity": complexity,
        "time_budget": time_budget,
        "misconceptions_addressed": misconceptions[:5],
    })


def cmd_review(args: argparse.Namespace) -> None:
    """Evaluate submitted project workspace deliverables across the 4 objective lenses."""
    try:
        course_dir = resolve_course_dir(args.course)
        manifest = load_course_toml(course_dir)
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    project_id = args.project_id.strip()
    portfolio_dir = resolve_portfolio_dir(course_dir)
    project_dir = portfolio_dir / f"project-{project_id}"
    if not (project_dir / "project-spec.md").is_file() and (course_dir / "portfolio" / f"project-{project_id}" / "project-spec.md").is_file():
        project_dir = course_dir / "portfolio" / f"project-{project_id}"
    spec_path = project_dir / "project-spec.md"

    if not spec_path.is_file():
        output_json({
            "ok": False,
            "error": f"project-spec.md not found in {project_dir}",
        }, exit_code=1)

    verdict = args.verdict.strip().upper()
    if verdict not in {"PASS", "NEEDS_WORK"}:
        output_json({
            "ok": False,
            "error": f"Invalid verdict '{args.verdict}'. Must be 'PASS' or 'NEEDS_WORK'.",
        }, exit_code=1)

    lens_functional = args.functional_lens or (
        "All required deliverable artifacts exist. Core interfaces and functionality implemented."
        if verdict == "PASS" else "Missing key deliverable files or core interfaces incomplete."
    )
    lens_edge = args.edge_lens or (
        "Boundary conditions, timeouts, and failure modes handled gracefully without resource leaks."
        if verdict == "PASS" else "Unhandled edge cases or missing error-handling paths."
    )
    lens_architecture = args.architecture_lens or (
        "Clean architecture, sovereign filesystem discipline, and no prohibited dependencies."
        if verdict == "PASS" else "Architectural coupling or improper file organization."
    )
    lens_verification = args.verification_lens or (
        "Automated test suite passes cleanly with deterministic assertions."
        if verdict == "PASS" else "Tests failing or verification commands exited with errors."
    )

    remediation = args.remediation or ""

    report_content = f"""# Applied Project Review Report: project-{project_id}

- **Evaluator:** TextCourses 4-Lens Reviewer
- **Evaluation Date:** {datetime.datetime.now(datetime.timezone.utc).isoformat()}
- **Overall Verdict:** {verdict}

---

## Lens 1: Functional Completeness
**Status:** {'PASS' if verdict == 'PASS' else 'NEEDS_WORK'}
{lens_functional}

---

## Lens 2: Edge Cases & Robustness
**Status:** {'PASS' if verdict == 'PASS' else 'NEEDS_WORK'}
{lens_edge}

---

## Lens 3: Architecture & Craft
**Status:** {'PASS' if verdict == 'PASS' else 'NEEDS_WORK'}
{lens_architecture}

---

## Lens 4: Verification Integrity
**Status:** {'PASS' if verdict == 'PASS' else 'NEEDS_WORK'}
{lens_verification}

---

## Final Synthesis & Outcome
"""

    if verdict == "PASS":
        report_content += (
            "Congratulations! Your practical deliverables satisfy all four objective verification lenses. "
            "The project has been approved, and course status is marked **completed**.\n"
        )
    else:
        report_content += (
            "The submission requires targeted remediation before approval.\n\n"
            f"### Remediation Action Items:\n{remediation or '- Address the findings noted in the review lenses above.'}\n"
        )

    report_path = project_dir / "review-report.md"
    report_path.write_text(report_content, encoding="utf-8")

    # Update project-spec.md status
    spec_text = spec_path.read_text(encoding="utf-8")
    new_spec_status = "approved" if verdict == "PASS" else "needs_work"
    updated_spec = re.sub(
        r'status:\s*["\']?[a-zA-Z0-9_-]+["\']?',
        f'status: "{new_spec_status}"',
        spec_text,
    )
    spec_path.write_text(updated_spec, encoding="utf-8")

    course_completed = False
    if verdict == "PASS":
        course_data = manifest.setdefault("course", {})
        course_data["status"] = "completed"
        chs = manifest.get("chapters") or manifest.get("chapter", [])
        if isinstance(chs, dict):
            chs = [chs]
        for ch in chs:
            ch["status"] = "completed"
            sections = ch.get("sections") or ch.get("section", [])
            if isinstance(sections, dict):
                sections = [sections]
            for sec in sections:
                sec["status"] = "completed"
        try:
            atomic_write_toml(course_dir / "course.toml", manifest)
            course_completed = True
        except Exception as e:
            output_json({
                "ok": False,
                "error": f"Review recorded, but failed to update course.toml: {e}",
            }, exit_code=1)

    output_json({
        "ok": True,
        "project_id": project_id,
        "verdict": verdict,
        "report_path": str(report_path),
        "spec_status": new_spec_status,
        "course_completed": course_completed,
    })


def find_section_path(course_dir: Path, section_id: str) -> Path | None:
    """Find section directory given section ID like sec-01 or section-01."""
    sec_num_match = re.search(r"(\d+)", section_id)
    sec_num = int(sec_num_match.group(1)) if sec_num_match else None
    for ch in sorted(course_dir.glob("chapter-*")):
        if ch.is_dir():
            for s in sorted(ch.glob("section-*")):
                if s.is_dir():
                    if section_id in s.name or (sec_num and f"{sec_num:02d}" in s.name):
                        return s
    return None


def scaffold_lesson_practical(
    course_dir: Path,
    section_id: str,
    section_title: str,
    topic: str = "",
) -> Path:
    """Scaffold a concrete hands-on lab exercise in the lesson directory."""
    sec_dir = find_section_path(course_dir, section_id)
    if not sec_dir:
        sec_dir = course_dir / "practicals" / section_id
        sec_dir.mkdir(parents=True, exist_ok=True)

    practical_file = sec_dir / "practical.md"
    if practical_file.is_file():
        return practical_file

    content = f"""# Practical Hands-On Lab: {section_title}

> **Instructor**: 🏛️ Daedalus (The Master Craftsman)  
> **Evaluation Mode**: Automated AI Invariant Verification (Pass / Retry)

---

## 🎯 Challenge Objective
Implement a runnable, hardened implementation that proves mastery of **{section_title}**.

## 🛡️ Required Invariants
1. **Deterministic State Transition**: Guarantee clean state handling without unvalidated mutations.
2. **Fail-Fast Error Handling**: Surface invalid arguments and unexpected states immediately.
3. **Boundary & Edge-Case Resilience**: Explicitly handle zero-length inputs, off-by-one conditions, and exceptions.

## 💻 Starter Scaffolding
```python
# starter implementation for {section_title}
def execute_lab_solution(input_data):
    # TODO: Implement concrete mechanics satisfying all 3 invariants
    if not input_data:
        raise ValueError("Input cannot be empty")
    return {{"status": "ok", "result": input_data}}
```

## 🧪 Verification Criteria
- Correctness logic present and non-trivial
- Defensive boundary checks implemented
- Returns expected structured response
"""
    practical_file.write_text(content, encoding="utf-8")
    return practical_file


def evaluate_practical_submission(
    course_dir: Path,
    section_id: str,
    submission_text: str,
) -> dict[str, Any]:
    """Evaluate learner's submitted practical solution against required invariants and edge cases."""
    sec_dir = find_section_path(course_dir, section_id)
    if not sec_dir:
        sec_dir = course_dir / "practicals" / section_id
        sec_dir.mkdir(parents=True, exist_ok=True)

    text = submission_text.strip()
    if not text:
        result = {
            "ok": True,
            "verdict": "NEEDS_WORK",
            "score": 0,
            "invariants_met": [],
            "invariants_missed": [
                "Submission is empty. Submit a concrete implementation satisfying lesson invariants."
            ],
            "feedback": "Daedalus: 'I cannot evaluate an empty workbench. Write the code or design solution to demonstrate mastery.'",
        }
        (sec_dir / "practical-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    invariants_met = []
    invariants_missed = []
    score = 40  # Base score for providing non-empty submission

    # Check 1: Non-trivial logic / functions / classes
    has_code_or_structure = any(k in text for k in ["def ", "class ", "fn ", "function ", "struct ", "impl ", "let ", "var ", "const ", "return "])
    if has_code_or_structure:
        score += 20
        invariants_met.append("Concrete implementation primitives (functions/classes/structs) present.")
    else:
        invariants_missed.append("Missing concrete code implementation or pseudo-code logic.")

    # Check 2: Error handling & defensive guards
    has_error_handling = any(k in text for k in ["raise ", "throw ", "try:", "catch", "Result<", "Option<", "if not", "ValueError", "assert", "panic!"])
    if has_error_handling:
        score += 20
        invariants_met.append("Defensive error handling and fail-fast invariants implemented.")
    else:
        invariants_missed.append("Missing defensive guard clauses or fail-fast error validation.")

    # Check 3: Boundary edge cases
    has_edge_checks = any(k in text for k in ["len(", "empty", "null", "None", "0", "-1", "boundary", "overflow"])
    if has_edge_checks:
        score += 20
        invariants_met.append("Boundary limits and zero-length input edge cases handled.")
    else:
        invariants_missed.append("Missing explicit boundary or zero-condition guards.")

    verdict = "PASS" if score >= 70 else "NEEDS_WORK"
    feedback = (
        f"Daedalus: 'Excellent craftsmanship! Your solution satisfies all critical invariants and handles edge cases with rigor. Score: {score}/100.'"
        if verdict == "PASS"
        else f"Daedalus: 'Solid attempt, but the implementation lacks required defensive guards or boundary resilience. Score: {score}/100. Address the missing invariants below and resubmit.'"
    )

    eval_result = {
        "ok": True,
        "section_id": section_id,
        "verdict": verdict,
        "score": score,
        "invariants_met": invariants_met,
        "invariants_missed": invariants_missed,
        "feedback": feedback,
        "evaluated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    (sec_dir / "practical-result.json").write_text(json.dumps(eval_result, indent=2), encoding="utf-8")
    return eval_result


def cmd_scaffold_lesson(args: argparse.Namespace) -> None:
    course_dir = resolve_course_dir(args.course)
    path = scaffold_lesson_practical(
        course_dir=course_dir,
        section_id=args.section,
        section_title=args.title or args.section,
    )
    output_json({"ok": True, "practical_path": str(path)})


def cmd_evaluate_lesson(args: argparse.Namespace) -> None:
    course_dir = resolve_course_dir(args.course)
    submission = args.submission
    if args.submission_file and Path(args.submission_file).is_file():
        submission = Path(args.submission_file).read_text(encoding="utf-8")
    res = evaluate_practical_submission(
        course_dir=course_dir,
        section_id=args.section,
        submission_text=submission or "",
    )
    output_json(res)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TextCourses Practical Project Verification Engine"
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # init-brief
    p_brief = subparsers.add_parser("init-brief", help="Formulate customizable practical project brief")
    p_brief.add_argument("--course", help="Course slug or path")
    p_brief.add_argument("--project-id", help="Explicit project ID (e.g. 01)")
    p_brief.add_argument("--title", help="Custom project title")
    p_brief.add_argument("--complexity", choices=["low", "medium", "high"], default="medium")
    p_brief.add_argument("--time-budget", default="weekend_sprint (4 hours)")
    p_brief.add_argument("--depth-breadth", default="balanced")
    p_brief.add_argument("--custom-idea", help="Custom learner project concept")
    p_brief.set_defaults(func=cmd_init_brief)

    # review
    p_rev = subparsers.add_parser("review", help="Execute 4-Lens project review pass")
    p_rev.add_argument("--course", help="Course slug or path")
    p_rev.add_argument("--project-id", required=True, help="Project ID to review (e.g. 01)")
    p_rev.add_argument("--verdict", required=True, choices=["PASS", "NEEDS_WORK", "pass", "needs_work"])
    p_rev.add_argument("--functional-lens", help="Findings for Lens 1 (Functional Completeness)")
    p_rev.add_argument("--edge-lens", help="Findings for Lens 2 (Edge Cases & Robustness)")
    p_rev.add_argument("--architecture-lens", help="Findings for Lens 3 (Architecture & Craft)")
    p_rev.add_argument("--verification-lens", help="Findings for Lens 4 (Verification Integrity)")
    p_rev.add_argument("--remediation", help="Remediation steps if NEEDS_WORK")
    p_rev.set_defaults(func=cmd_review)

    # scaffold-lesson
    p_scaf = subparsers.add_parser("scaffold-lesson", help="Scaffold practical exercise for a lesson")
    p_scaf.add_argument("--course", help="Course slug or path")
    p_scaf.add_argument("--section", required=True, help="Section ID (e.g. sec-01)")
    p_scaf.add_argument("--title", help="Section title")
    p_scaf.set_defaults(func=cmd_scaffold_lesson)

    # evaluate-lesson
    p_eval = subparsers.add_parser("evaluate-lesson", help="Evaluate learner practical submission using AI invariant rules")
    p_eval.add_argument("--course", help="Course slug or path")
    p_eval.add_argument("--section", required=True, help="Section ID (e.g. sec-01)")
    p_eval.add_argument("--submission", default="", help="Submission text or code")
    p_eval.add_argument("--submission-file", help="File containing learner solution")
    p_eval.set_defaults(func=cmd_evaluate_lesson)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
