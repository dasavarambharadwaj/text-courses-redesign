#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""teach_engine.py — Conversational instruction engine and Next-Action Fork orchestrator.

Coordinates single-concept lesson delivery, resolves session recovery states from
lesson-plan.md checklists, renders the standardized Next-Action Fork, triggers
automated textbook notes compilation upon section completion, and mirrors token-minimal
instruction events to courses/<slug>/memlog.md (FR-9, FR-10, FR-11, FR-32, AD-5).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

# Ensure sibling scripts and project root are importable
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
for p in [str(SCRIPT_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from lesson_tracker import get_current_concept, tick_concept
except ImportError:
    from _tc.scripts.lesson_tracker import get_current_concept, tick_concept

try:
    from notes_compiler import compile_notes
except ImportError:
    from _tc.scripts.notes_compiler import compile_notes


NEXT_ACTION_FORK_TEXT = """---
### Next Action Fork
- `[1]` **Next Concept**: Advance to the next concept in the lesson plan.
- `[2]` **Test Me**: Challenge me with a diagnostic inquiry on this concept.
- `[3]` **Re-explain / Deeper**: Provide an alternate angle, analogy, or edge case breakdown.
- `[4]` **Custom**: Ask a specific question or explore a custom edge case.
"""

NEXT_ACTION_FORK_OPTIONS = [
    {"key": "1", "label": "Next Concept", "action": "advance"},
    {"key": "2", "label": "Test Me", "action": "test_inquiry"},
    {"key": "3", "label": "Re-explain / Deeper", "action": "deep_dive"},
    {"key": "4", "label": "Custom", "action": "write_in"},
]


def render_fork(tag_team: str | None = None) -> tuple[str, list[dict[str, Any]]]:
    """Render Next-Action Fork text and option array, optionally surfacing a tag-team handoff."""
    if not tag_team:
        return NEXT_ACTION_FORK_TEXT, NEXT_ACTION_FORK_OPTIONS

    tag_team_clean = tag_team.strip()
    fork_text = f"""---
### Next Action Fork
- `[1]` **Next Concept**: Advance to the next concept in the lesson plan.
- `[2]` **Test Me**: Challenge me with a diagnostic inquiry on this concept.
- `[3]` **Tag-in {tag_team_clean}**: Bring in {tag_team_clean} for an alternate perspective / mental model.
- `[4]` **Custom**: Ask a specific question or explore a custom edge case.
"""
    options = [
        {"key": "1", "label": "Next Concept", "action": "advance"},
        {"key": "2", "label": "Test Me", "action": "test_inquiry"},
        {"key": "3", "label": f"Tag-in {tag_team_clean}", "action": "tag_team", "teacher": tag_team_clean, "faculty": tag_team_clean},
        {"key": "4", "label": "Custom", "action": "write_in"},
    ]
    return fork_text, options


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def load_preferences(workspace: Path) -> dict[str, Any]:
    """Parse learner preferences from profile/preferences.md or plan/preferences.md if available."""
    pref_file = workspace / "profile" / "preferences.md"
    if not pref_file.is_file():
        pref_file = workspace / "plan" / "preferences.md"
    if not pref_file.is_file():
        return {
            "style_profile": "direct_technical",
            "density": "example_driven",
            "role": "Software Engineer",
            "teacher": "feynman",
        }

    text = pref_file.read_text(encoding="utf-8")
    result: dict[str, Any] = {
        "style_profile": "direct_technical",
        "density": "example_driven",
        "role": "Software Engineer",
        "teacher": "feynman",
    }
    for line in text.splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            k_clean = k.strip().lower()
            v_clean = v.strip().strip('"').strip("'")
            if k_clean in {
                "style_profile", "density", "role", "explanation_density", "teacher", "faculty",
                "competency_level", "competency", "experience_level", "practical_focus", "practicals", "hands_on",
            }:
                result[k_clean] = v_clean
                if k_clean in {"teacher", "faculty"}:
                    result["teacher"] = v_clean
                if k_clean in {"competency", "experience_level"}:
                    result["competency_level"] = v_clean
                if k_clean in {"practicals", "hands_on"}:
                    result["practical_focus"] = v_clean

    role_lower = str(result.get("role", "")).lower()
    if "beginner" in role_lower or result.get("competency_level") == "beginner":
        result["competency_level"] = "beginner"
        if "teacher" not in result or result["teacher"] == "feynman":
            result["teacher"] = "hypatia"
    if str(result.get("practical_focus", "")).lower() in {"true", "yes", "1"}:
        result["practical_focus"] = "true"

    return result


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


def find_section_directory(course_dir: Path, chapter_id: Any, section_id: Any) -> Path | None:
    """Locate the actual section directory on disk for given chapter and section IDs."""
    ch_id_str = str(chapter_id) if chapter_id is not None else ""
    sec_id_str = str(section_id) if section_id is not None else ""
    ch_num_m = re.search(r"(\d+)", ch_id_str)
    sec_num_m = re.search(r"(\d+)", sec_id_str)
    ch_num = int(ch_num_m.group(1)) if ch_num_m else None
    sec_num = int(sec_num_m.group(1)) if sec_num_m else None

    for ch_path in sorted(course_dir.glob("chapter-*")):
        if not ch_path.is_dir():
            continue
        c_m = re.search(r"chapter[-_]?0*(\d+)", ch_path.name, re.IGNORECASE)
        if c_m and ch_num is not None and int(c_m.group(1)) != ch_num:
            continue

        for sec_path in sorted(ch_path.glob("section-*")):
            if not sec_path.is_dir():
                continue
            s_m = re.search(r"sec(?:tion)?[-_]?0*(\d+)", sec_path.name, re.IGNORECASE)
            if s_m and sec_num is not None and int(s_m.group(1)) == sec_num:
                return sec_path

        # Subdirectory fallback without section- prefix
        if sec_id_str:
            for sec_path in ch_path.glob("*"):
                if sec_path.is_dir() and sec_id_str.lower() in sec_path.name.lower():
                    return sec_path

    return None


def resolve_active_section(course_dir: Path, explicit_section: str | None = None) -> dict[str, Any]:
    """Find active in-progress or next uncompleted section in course.toml."""
    manifest_path = course_dir / "course.toml"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"No course.toml found in {course_dir}")

    course_data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    chapters = course_data.get("chapters", [])
    if not chapters:
        raise ValueError(f"No chapters found in course manifest at {manifest_path}")

    target_sec: dict[str, Any] | None = None
    target_ch: dict[str, Any] | None = None

    # 1. Check explicit section
    if explicit_section:
        for ch in chapters:
            for sec in ch.get("sections", []):
                if str(sec.get("id")) == str(explicit_section):
                    target_sec = sec
                    target_ch = ch
                    break
            if target_sec:
                break

    # 2. Find in_progress section
    if not target_sec:
        for ch in chapters:
            for sec in ch.get("sections", []):
                if sec.get("status") == "in_progress":
                    target_sec = sec
                    target_ch = ch
                    break
            if target_sec:
                break

    # 3. Find first not_started section
    if not target_sec:
        for ch in chapters:
            for sec in ch.get("sections", []):
                if sec.get("status") == "not_started":
                    target_sec = sec
                    target_ch = ch
                    break
            if target_sec:
                break

    # 4. Fallback to review sections if no not_started sections remain
    if not target_sec:
        for ch in chapters:
            for sec in ch.get("sections", []):
                if sec.get("status") == "review":
                    target_sec = sec
                    target_ch = ch
                    break
            if target_sec:
                break

    # Default to very first section
    if not target_sec:
        target_ch = chapters[0]
        target_sec = target_ch["sections"][0]

    ch_id = target_ch.get("id", "chapter-01")
    sec_id = target_sec.get("id", "sec-01")

    sec_dir = find_section_directory(course_dir, ch_id, sec_id)
    if not sec_dir:
        sec_dir = course_dir / "chapter-01" / "section-01"

    return {
        "chapter_id": ch_id,
        "chapter_title": target_ch.get("title", ""),
        "section_id": sec_id,
        "section_title": target_sec.get("title", ""),
        "section_status": target_sec.get("status", "not_started"),
        "section_dir": str(sec_dir),
    }


def get_teaching_session(
    course_slug: str,
    workspace: Path | str = ".",
    explicit_section: str | None = None,
    tag_team: str | None = None,
) -> dict[str, Any]:
    """Retrieve full teaching context, active concept, and preferences for current turn."""
    ws = Path(workspace).resolve()
    course_dir = ws / "courses" / course_slug
    if not course_dir.is_dir():
        raise FileNotFoundError(f"Course directory not found: {course_dir}")

    active_info = resolve_active_section(course_dir, explicit_section)
    sec_dir = Path(active_info["section_dir"])

    concept_info: dict[str, Any]
    try:
        concept_info = get_current_concept(sec_dir)
    except FileNotFoundError:
        concept_info = {
            "has_active_concept": False,
            "concept": "Introduction & Objectives",
            "index": 0,
            "remaining_items": 1,
            "total_items": 1,
        }

    preferences = load_preferences(ws)
    fork_text, fork_options = render_fork(tag_team)

    # Check course manifest for beginner or practical flags
    course_toml_path = course_dir / "course.toml"
    course_data: dict[str, Any] = {}
    if course_toml_path.is_file():
        try:
            course_data = tomllib.loads(course_toml_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    is_beginner = (
        preferences.get("competency_level") == "beginner"
        or course_data.get("course", {}).get("competency_level") == "beginner"
    )
    is_practical = (
        preferences.get("practical_focus") == "true"
        or course_data.get("course", {}).get("practical_focus") is True
    )

    practical_info = None
    if is_practical:
        try:
            from practical_evaluator import scaffold_lesson_practical
            p_path = scaffold_lesson_practical(course_dir, active_info["section_id"], active_info["section_title"])
            res_file = sec_dir / "practical-result.json"
            p_status = "pending"
            p_score = None
            if res_file.is_file():
                try:
                    res_data = json.loads(res_file.read_text(encoding="utf-8"))
                    p_status = "passed" if res_data.get("verdict") == "PASS" else "needs_work"
                    p_score = res_data.get("score")
                except Exception:
                    pass
            practical_info = {
                "required": True,
                "status": p_status,
                "score": p_score,
                "file": str(p_path),
                "evaluator": "Daedalus (The Master Craftsman)",
            }
        except Exception:
            pass

    guidance = (
        "Lead with Hypatia (The Empathetic Tutor). Use gentle Socratic stepping stones. Strictly zero unexplained jargon. Anchor in visceral real-world analogies."
        if is_beginner
        else "Deliver clear, idiom-driven instruction with concrete invariants."
    )

    return {
        "ok": True,
        "course_slug": course_slug,
        "active_section": active_info,
        "active_concept": concept_info,
        "preferences": preferences,
        "is_beginner": is_beginner,
        "is_practical": is_practical,
        "practical": practical_info,
        "pedagogical_guidance": guidance,
        "fork_text": fork_text,
        "fork_options": fork_options,
    }


def advance_lesson_concept(
    course_slug: str,
    workspace: Path | str = ".",
    explicit_section: str | None = None,
    recap: list[str] | None = None,
    analogy: str | None = None,
) -> dict[str, Any]:
    """Tick active concept in lesson-plan.md, compiling human-first notes and logging to memlog."""
    ws = Path(workspace).resolve()
    course_dir = ws / "courses" / course_slug
    if not course_dir.is_dir():
        raise FileNotFoundError(f"Course directory not found: {course_dir}")

    active_info = resolve_active_section(course_dir, explicit_section)
    sec_dir = Path(active_info["section_dir"])
    preferences = load_preferences(ws)
    teacher = preferences.get("teacher", "feynman").title()

    # Tick active concept
    tick_result = tick_concept(sec_dir)
    ticked = tick_result.get("ticked_concept")

    # Mirror taught concept to course memlog in token-minimal format
    if ticked:
        sec_token = active_info["section_id"]
        concept_token = re.sub(r"[^a-zA-Z0-9_:]", "_", re.sub(r"[\s-]+", "_", ticked.lower()))[:40].strip("_")
        append_course_memlog(
            course_dir,
            entry_type="concept",
            by=teacher,
            text=f"{sec_token}:{concept_token}:mastered",
        )

    is_section_completed = (
        tick_result.get("section_fully_completed", False)
        or tick_result.get("already_all_completed", False)
    )
    notes_compilation = None

    # Check practical gate if practical focus is enabled
    course_toml_path = course_dir / "course.toml"
    course_data: dict[str, Any] = {}
    if course_toml_path.is_file():
        try:
            course_data = tomllib.loads(course_toml_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    is_practical = (
        preferences.get("practical_focus") == "true"
        or course_data.get("course", {}).get("practical_focus") is True
    )

    if is_section_completed and is_practical:
        res_file = sec_dir / "practical-result.json"
        has_passed = False
        if res_file.is_file():
            try:
                res_data = json.loads(res_file.read_text(encoding="utf-8"))
                if res_data.get("verdict") == "PASS":
                    has_passed = True
            except Exception:
                pass
        if not has_passed:
            return {
                "ok": True,
                "course_slug": course_slug,
                "section_id": active_info["section_id"],
                "section_title": active_info["section_title"],
                "ticked_concept": ticked,
                "remaining_concepts": 0,
                "section_fully_completed": False,
                "practical_pending": True,
                "message": "All lesson concepts covered! Awaiting passing practical validation by Daedalus. Submit your solution for evaluation before section completion is locked.",
                "notes_compiled": False,
                "teacher": teacher,
                "next_recommendation": f"Run practical evaluation: uv run _tc/scripts/practical_evaluator.py evaluate-lesson --course {course_slug} --section {active_info['section_id']}",
            }

    if is_section_completed:
        # Final concept completed: automatically compile human-first notes.md
        recap_bullets = recap or [
            f"Mastered core mechanics of {active_info['section_title']}.",
            "Enforced key architectural constraints and memory invariants.",
            "Verified edge cases and completed all milestones.",
        ]
        notes_compilation = compile_notes(
            section_dir=sec_dir,
            title=active_info["section_title"],
            recap=recap_bullets,
            target_status="review",
            teacher=teacher,
            analogy=analogy,
        )
        append_course_memlog(
            course_dir,
            entry_type="milestone",
            text=f"sec:{active_info['section_id']}:all_concepts_mastered",
        )

    return {
        "ok": True,
        "course_slug": course_slug,
        "section_id": active_info["section_id"],
        "section_title": active_info["section_title"],
        "ticked_concept": ticked,
        "remaining_concepts": tick_result.get("remaining_items", 0),
        "section_fully_completed": is_section_completed,
        "notes_compilation": notes_compilation,
        "teacher": teacher,
        "next_recommendation": "/tc-test-me" if is_section_completed else "/tc-teach",
    }


def log_question(course_slug: str, text: str, workspace: Path | str = ".") -> dict[str, Any]:
    """Log learner question to course memlog in token-minimal format."""
    ws = Path(workspace).resolve()
    course_dir = ws / "courses" / course_slug
    if not course_dir.is_dir():
        raise FileNotFoundError(f"Course directory not found: {course_dir}")

    compact_q = re.sub(r"\s+", " ", text).strip()[:100]
    append_course_memlog(course_dir, entry_type="question", text=f"q:{compact_q}")
    return {"ok": True, "course": course_slug, "logged": f"q:{compact_q}"}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="teach_engine.py",
        description="TextCourses conversational instruction engine and Next-Action Fork orchestrator.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # session
    p_sess = subparsers.add_parser("session", help="Retrieve active teaching session and current concept.")
    p_sess.add_argument("--course", required=True, help="Course slug.")
    p_sess.add_argument("--workspace", default=".", help="Workspace path.")
    p_sess.add_argument("--section", default=None, help="Explicit section ID.")
    p_sess.add_argument("--tag-team", default=None, help="Alternate faculty persona to surface in Next-Action Fork.")
    p_sess.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # advance
    p_adv = subparsers.add_parser("advance", help="Tick concept and trigger notes compilation on completion.")
    p_adv.add_argument("--course", required=True, help="Course slug.")
    p_adv.add_argument("--workspace", default=".", help="Workspace path.")
    p_adv.add_argument("--section", default=None, help="Explicit section ID.")
    p_adv.add_argument("--recap", nargs="*", default=None, help="Optional recap bullets on section completion.")
    p_adv.add_argument("--analogy", default=None, help="Optional plain-English analogy for compiled notes.")
    p_adv.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # fork
    p_fork = subparsers.add_parser("fork", help="Render standardized Next-Action Fork block.")
    p_fork.add_argument("--tag-team", default=None, help="Alternate faculty persona to surface in Next-Action Fork.")
    p_fork.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # log-question
    p_q = subparsers.add_parser("log-question", help="Log learner question to course memlog.")
    p_q.add_argument("--course", required=True, help="Course slug.")
    p_q.add_argument("--text", required=True, help="Question text.")
    p_q.add_argument("--workspace", default=".", help="Workspace path.")
    p_q.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    try:
        if args.subcommand == "session":
            result = get_teaching_session(
                course_slug=args.course,
                workspace=args.workspace,
                explicit_section=args.section,
                tag_team=getattr(args, "tag_team", None),
            )
            output_json(result, 0)

        elif args.subcommand == "advance":
            result = advance_lesson_concept(
                course_slug=args.course,
                workspace=args.workspace,
                explicit_section=args.section,
                recap=args.recap,
                analogy=getattr(args, "analogy", None),
            )
            output_json(result, 0)

        elif args.subcommand == "fork":
            fork_text, fork_options = render_fork(getattr(args, "tag_team", None))
            if args.json:
                output_json({"ok": True, "text": fork_text, "options": fork_options}, 0)
            else:
                print(fork_text)
                sys.exit(0)

        elif args.subcommand == "log-question":
            result = log_question(
                course_slug=args.course,
                text=args.text,
                workspace=args.workspace,
            )
            output_json(result, 0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except Exception as e:
        output_json({"error": str(e), "ok": False}, 1)


if __name__ == "__main__":
    main()
