#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""teach_engine.py — Conversational instruction engine and Next-Action Fork orchestrator.

Coordinates single-concept lesson delivery, resolves session recovery states from
lesson-plan.md checklists, renders the standardized Next-Action Fork, and triggers
automated textbook notes compilation upon section completion (FR-9, FR-10, FR-11, AD-5).
"""

from __future__ import annotations

import argparse
import json
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


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def load_preferences(workspace: Path) -> dict[str, Any]:
    """Parse learner preferences from plan/preferences.md if available."""
    pref_file = workspace / "plan" / "preferences.md"
    if not pref_file.is_file():
        return {
            "style_profile": "direct_technical",
            "density": "example_driven",
            "role": "Software Engineer",
        }

    text = pref_file.read_text(encoding="utf-8")
    result: dict[str, Any] = {
        "style_profile": "direct_technical",
        "density": "example_driven",
        "role": "Software Engineer",
    }
    for line in text.splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            k_clean = k.strip().lower()
            v_clean = v.strip().strip('"').strip("'")
            if k_clean in {"style_profile", "density", "role", "explanation_density"}:
                result[k_clean] = v_clean
    return result


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
            s_m = re.search(r"section[-_]?0*(\d+)", sec_path.name, re.IGNORECASE)
            if s_m and sec_num is not None and int(s_m.group(1)) == sec_num:
                return sec_path

    # Fallback to direct name match
    for ch_path in course_dir.glob("*"):
        if ch_path.is_dir():
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
        # Fallback to creating / assuming path
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

    return {
        "ok": True,
        "course_slug": course_slug,
        "active_section": active_info,
        "active_concept": concept_info,
        "preferences": preferences,
        "fork_text": NEXT_ACTION_FORK_TEXT,
        "fork_options": NEXT_ACTION_FORK_OPTIONS,
    }


def advance_lesson_concept(
    course_slug: str,
    workspace: Path | str = ".",
    explicit_section: str | None = None,
    recap: list[str] | None = None,
) -> dict[str, Any]:
    """Tick active concept in lesson-plan.md, compiling notes.md if section is finished."""
    ws = Path(workspace).resolve()
    course_dir = ws / "courses" / course_slug
    if not course_dir.is_dir():
        raise FileNotFoundError(f"Course directory not found: {course_dir}")

    active_info = resolve_active_section(course_dir, explicit_section)
    sec_dir = Path(active_info["section_dir"])

    # Tick active concept
    tick_result = tick_concept(sec_dir)

    is_section_completed = tick_result.get("section_fully_completed", False)
    notes_compilation = None

    if is_section_completed:
        # Final concept completed: automatically compile notes.md
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
        )

    return {
        "ok": True,
        "course_slug": course_slug,
        "section_id": active_info["section_id"],
        "section_title": active_info["section_title"],
        "ticked_concept": tick_result.get("ticked_concept"),
        "remaining_concepts": tick_result.get("remaining_items", 0),
        "section_fully_completed": is_section_completed,
        "notes_compilation": notes_compilation,
        "next_recommendation": "/tc-test-me" if is_section_completed else "/tc-teach",
    }


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
    p_sess.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # advance
    p_adv = subparsers.add_parser("advance", help="Tick concept and trigger notes compilation on completion.")
    p_adv.add_argument("--course", required=True, help="Course slug.")
    p_adv.add_argument("--workspace", default=".", help="Workspace path.")
    p_adv.add_argument("--section", default=None, help="Explicit section ID.")
    p_adv.add_argument("--recap", nargs="*", default=None, help="Optional recap bullets on section completion.")
    p_adv.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # fork
    p_fork = subparsers.add_parser("fork", help="Render standardized Next-Action Fork block.")
    p_fork.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    try:
        if args.subcommand == "session":
            result = get_teaching_session(
                course_slug=args.course,
                workspace=args.workspace,
                explicit_section=args.section,
            )
            output_json(result, 0)

        elif args.subcommand == "advance":
            result = advance_lesson_concept(
                course_slug=args.course,
                workspace=args.workspace,
                explicit_section=args.section,
                recap=args.recap,
            )
            output_json(result, 0)

        elif args.subcommand == "fork":
            if args.json:
                output_json({"ok": True, "text": NEXT_ACTION_FORK_TEXT, "options": NEXT_ACTION_FORK_OPTIONS}, 0)
            else:
                print(NEXT_ACTION_FORK_TEXT)
                sys.exit(0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except Exception as e:
        output_json({"error": str(e), "ok": False}, 1)


if __name__ == "__main__":
    main()
