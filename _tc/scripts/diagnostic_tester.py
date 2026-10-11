#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""diagnostic_tester.py — Deterministic Diagnostic Assessment Engine for TextCourses.

Coordinates 100% question-based conceptual diagnostic evaluations without code
copy-pasting. Enforces the Cumulative Boundary Rule (strictly tests review/completed
sections, preventing future concept leaks), atomically logs assessment outcomes
to test-ledger.jsonl via POSIX advisory locking, and advances section status from
'review' to 'completed' in course.toml upon passing.
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

# Ensure project root and _tc/scripts are on sys.path for sibling imports
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    import tomli_w
except ImportError:
    tomli_w = None  # Handled gracefully if missing in bare environment


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


def append_course_memlog(
    course_dir: Path,
    entry_type: str,
    text: str,
    by: str | None = None,
) -> None:
    """Append a token-minimal entry directly into courses/<slug>/memlog.md."""
    memlog_file = course_dir / "memlog.md"
    if not memlog_file.exists():
        return

    prefix = f"- ({entry_type} by {by}) " if by else f"- ({entry_type}) "
    clean_text = text.strip()
    line = f"{prefix}{clean_text}\n"
    try:
        with open(memlog_file, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def resolve_course_dir(course_arg: str | None) -> Path:
    """Resolve course directory from slug, path, or current directory."""
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

    if (Path("course.toml")).is_file():
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


def read_notes_summary(notes_path: Path) -> dict[str, Any]:
    """Extract summary information from notes.md without leaking lesson plans."""
    if not notes_path.is_file():
        return {"exists": False, "summary": ""}
    try:
        content = notes_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        recap_lines = []
        capture = False
        for line in lines:
            stripped = line.strip()
            if "3-bullet recap" in stripped.lower() or stripped.lower() in ("## recap", "### recap"):
                capture = True
                continue
            if capture:
                if stripped.startswith("#"):
                    break
                if stripped.startswith("-") or stripped.startswith("*"):
                    recap_lines.append(stripped)
        return {
            "exists": True,
            "summary": "\n".join(recap_lines) if recap_lines else "\n".join(lines[:10]),
        }
    except Exception:
        return {"exists": True, "summary": ""}


def read_misconceptions(ledger_path: Path) -> dict[str, Any]:
    """Read recent misconceptions from test-ledger.jsonl using fcntl.flock."""
    if not ledger_path.is_file():
        return {"total_records": 0, "misconceptions": [], "frequency": {}}

    records = []
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                for line in f:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        record = json.loads(stripped)
                        if isinstance(record, dict):
                            records.append(record)
                    except json.JSONDecodeError:
                        continue
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception:
        return {"total_records": 0, "misconceptions": [], "frequency": {}}

    frequency: dict[str, int] = {}
    misconceptions = []
    for r in records:
        misc = r.get("diagnosed_misconception")
        outcome = str(r.get("outcome", "")).strip().lower()
        if misc and misc != "NONE" and outcome in {"fail", "failed", "incorrect"}:
            misconceptions.append(misc)
            frequency[misc] = frequency.get(misc, 0) + 1

    return {
        "total_records": len(records),
        "misconceptions": misconceptions[-5:],  # Last 5 misconceptions
        "frequency": frequency,
    }


def cmd_prepare(args: argparse.Namespace) -> None:
    """Inspect course and prepare eligible diagnostic test targets (Cumulative Boundary Rule)."""
    try:
        course_dir = resolve_course_dir(args.course)
        manifest = load_course_toml(course_dir)
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    course_data = manifest.get("course", {})
    course_slug = course_data.get("slug", course_dir.name)
    chapters = manifest.get("chapters") or manifest.get("chapter", [])
    if isinstance(chapters, dict):
        chapters = [chapters]

    eligible_sections: list[dict[str, Any]] = []
    excluded_sections_count = 0
    active_test_section: dict[str, Any] | None = None

    for ch in chapters:
        ch_slug = ch.get("slug") or ch.get("id", "")
        ch_title = ch.get("title", "")
        sections = ch.get("sections") or ch.get("section", [])
        if isinstance(sections, dict):
            sections = [sections]

        for sec in sections:
            sec_slug = sec.get("slug") or sec.get("id", "")
            sec_title = sec.get("title", "")
            sec_status = sec.get("status", "not-started")

            # Cumulative Boundary Rule: Only 'review' or 'completed' sections are eligible!
            if sec_status in {"review", "completed"}:
                candidates = [
                    course_dir / ch_slug / sec_slug / "notes.md",
                    course_dir / "chapters" / ch_slug / sec_slug / "notes.md",
                ]
                notes_path = candidates[0]
                for cand in candidates:
                    if cand.is_file():
                        notes_path = cand
                        break
                else:
                    globbed = list(course_dir.glob(f"**/*{sec_slug}*/notes.md"))
                    if globbed:
                        notes_path = globbed[0]

                notes_info = read_notes_summary(notes_path)
                sec_info = {
                    "chapter_slug": ch_slug,
                    "chapter_title": ch_title,
                    "section_slug": sec_slug,
                    "section_title": sec_title,
                    "status": sec_status,
                    "notes_exists": notes_info["exists"],
                    "notes_summary": notes_info["summary"],
                }
                eligible_sections.append(sec_info)

                if sec_status == "review" and active_test_section is None:
                    active_test_section = sec_info
            else:
                excluded_sections_count += 1

    if not eligible_sections:
        output_json({
            "ok": False,
            "eligible_count": 0,
            "excluded_count": excluded_sections_count,
            "error": "No sections are eligible for testing. Complete instructional concepts via /tc-teach first (sections must be in 'review' or 'completed' status).",
        }, exit_code=1)

    # If no section is in 'review', suggest the latest completed section for recall
    if active_test_section is None and eligible_sections:
        active_test_section = eligible_sections[-1]

    ledger_path = course_dir / "test-ledger.jsonl"
    misconceptions_info = read_misconceptions(ledger_path)
    is_beginner = course_data.get("competency_level") == "beginner"

    output_json({
        "ok": True,
        "course": course_slug,
        "eligible_sections_count": len(eligible_sections),
        "excluded_sections_count": excluded_sections_count,
        "eligible_sections": eligible_sections,
        "active_test_section": active_test_section,
        "misconceptions_summary": misconceptions_info,
        "is_beginner": is_beginner,
        "beginner_guidance": (
            "Beginner Focus Active: Probe intuitive mental models and core definitions first using everyday analogies before testing edge-case stress or race conditions."
            if is_beginner else None
        ),
        "zero_code_pasting_rule": "Enforced: Questions must be hinge scenarios, failure-mode trade-offs, or conceptual dilemmas. Never ask learner to paste code into chat.",
        "cumulative_boundary_rule": "Enforced: Future concepts from uncompleted sections are strictly omitted.",
    })


def cmd_record(args: argparse.Namespace) -> None:
    """Record diagnostic assessment outcome and update section status in course.toml on pass."""
    try:
        course_dir = resolve_course_dir(args.course)
        manifest = load_course_toml(course_dir)
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    course_data = manifest.get("course", {})
    course_slug = course_data.get("slug", course_dir.name)

    # Validate section existence and Cumulative Boundary Rule
    target_ch = args.chapter.strip()
    target_sec = args.section.strip()
    found_sec = None
    target_ch_obj = None

    chapters = manifest.get("chapters") or manifest.get("chapter", [])
    if isinstance(chapters, dict):
        chapters = [chapters]

    for ch in chapters:
        ch_matches = target_ch in (ch.get("slug"), ch.get("title"), ch.get("id"))
        if ch_matches:
            target_ch_obj = ch
            sections = ch.get("sections") or ch.get("section", [])
            if isinstance(sections, dict):
                sections = [sections]
            for sec in sections:
                sec_matches = target_sec in (sec.get("slug"), sec.get("title"), sec.get("id"))
                if sec_matches:
                    found_sec = sec
                    break
            if found_sec:
                break

    if not found_sec:
        output_json({
            "ok": False,
            "error": f"Section '{target_sec}' in chapter '{target_ch}' not found in course.toml.",
        }, exit_code=1)

    sec_status = found_sec.get("status", "not-started")
    if sec_status not in {"review", "completed"}:
        output_json({
            "ok": False,
            "error": f"Cumulative Boundary Violation: Section '{target_sec}' status is '{sec_status}'. Only 'review' or 'completed' sections may be tested.",
        }, exit_code=1)

    # Normalize outcome
    outcome = args.outcome.strip().lower()
    if outcome in {"pass", "passed", "correct"}:
        normalized_outcome = "pass"
    elif outcome in {"fail", "failed", "incorrect"}:
        normalized_outcome = "fail"
    else:
        output_json({"ok": False, "error": f"Invalid outcome '{args.outcome}'. Must be 'pass' or 'fail'."}, exit_code=1)

    # Format record
    misconception = args.misconception.strip() if args.misconception else ""
    if normalized_outcome == "pass" and not misconception:
        misconception = "NONE"
    elif normalized_outcome == "fail" and not misconception:
        misconception = "UNSPECIFIED_MISCONCEPTION"

    record: dict[str, Any] = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "course": course_slug,
        "chapter": target_ch_obj.get("slug", target_ch),
        "section": found_sec.get("slug", target_sec),
        "question_type": args.type or "hinge_scenario",
        "prompt": args.prompt,
        "learner_response": args.response,
        "outcome": normalized_outcome,
        "diagnosed_misconception": misconception,
        "remediation_summary": args.remediation or "",
        "confidence_level": args.confidence or "high",
    }

    # Append to test-ledger.jsonl atomically with fcntl.flock
    ledger_path = course_dir / "test-ledger.jsonl"
    record_line = json.dumps(record, ensure_ascii=False) + "\n"
    try:
        with open(ledger_path, "a", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(record_line)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        output_json({"ok": False, "error": f"Failed to append to ledger {ledger_path}: {e}"}, exit_code=1)

    # If pass, update section status in course.toml from 'review' to 'completed'
    section_status_updated = False
    new_status = sec_status
    if normalized_outcome == "pass" and sec_status == "review":
        found_sec["status"] = "completed"
        new_status = "completed"
        section_status_updated = True

        # Check if entire chapter is completed
        sections = target_ch_obj.get("section", [])
        if isinstance(sections, dict):
            sections = [sections]
        if all(s.get("status") == "completed" for s in sections):
            target_ch_obj["status"] = "completed"

        # Check if entire course is completed
        all_completed = True
        for ch in chapters:
            ch_secs = ch.get("section", [])
            if isinstance(ch_secs, dict):
                ch_secs = [ch_secs]
            if not all(s.get("status") == "completed" for s in ch_secs):
                all_completed = False
                break
        if all_completed:
            manifest.get("course", {})["status"] = "completed"

        try:
            atomic_write_toml(course_dir / "course.toml", manifest)
        except Exception as e:
            output_json({
                "ok": False,
                "error": f"Record appended to ledger, but failed to update course.toml: {e}",
            }, exit_code=1)

    # Mirror diagnostic outcome to courses/<slug>/memlog.md in token-minimal format
    if normalized_outcome == "fail":
        misc_clean = re.sub(r"[^a-zA-Z0-9_:-]", "_", misconception.lower())[:40].strip("_")
        sec_clean = re.sub(r"[^a-zA-Z0-9_:-]", "_", target_sec.lower())[:30].strip("_")
        append_course_memlog(course_dir, entry_type="misconception", text=f"misc:{misc_clean}:{sec_clean}")
    elif normalized_outcome == "pass":
        sec_clean = re.sub(r"[^a-zA-Z0-9_:-]", "_", target_sec.lower())[:30].strip("_")
        append_course_memlog(course_dir, entry_type="milestone", text=f"test:passed:{sec_clean}:completed")
        if all_completed:
            append_course_memlog(course_dir, entry_type="milestone", text=f"course:completed:{course_slug}")

    output_json({
        "ok": True,
        "appended": True,
        "outcome": normalized_outcome,
        "diagnosed_misconception": misconception,
        "section_status_updated": section_status_updated,
        "new_section_status": new_status,
        "ledger_path": str(ledger_path),
    })


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TextCourses Diagnostic Assessment Engine"
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # prepare
    p_prep = subparsers.add_parser("prepare", help="Prepare eligible test sections enforcing Cumulative Boundary Rule")
    p_prep.add_argument("--course", help="Course slug or path")
    p_prep.add_argument("--json", action="store_true", help="Output in JSON format")
    p_prep.set_defaults(func=cmd_prepare)

    # record
    p_rec = subparsers.add_parser("record", help="Record diagnostic test outcome and update status on pass")
    p_rec.add_argument("--course", help="Course slug or path")
    p_rec.add_argument("--chapter", required=True, help="Chapter slug or title")
    p_rec.add_argument("--section", required=True, help="Section slug or title")
    p_rec.add_argument("--type", default="hinge_scenario", help="Question type (e.g. hinge_scenario, trade_off)")
    p_rec.add_argument("--prompt", required=True, help="Assessment question prompt")
    p_rec.add_argument("--response", required=True, help="Learner's response")
    p_rec.add_argument("--outcome", required=True, choices=["pass", "fail", "passed", "failed"], help="Assessment outcome")
    p_rec.add_argument("--misconception", default="", help="Diagnosed misconception category (e.g. CONFUSION_MUTATION)")
    p_rec.add_argument("--remediation", default="", help="Remediation explanation or feedback")
    p_rec.add_argument("--confidence", default="high", choices=["high", "medium", "low"], help="Confidence level")
    p_rec.add_argument("--json", action="store_true", help="Output in JSON format")
    p_rec.set_defaults(func=cmd_record)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
