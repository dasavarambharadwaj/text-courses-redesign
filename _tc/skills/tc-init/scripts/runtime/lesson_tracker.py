#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""lesson_tracker.py — Session hygiene and lesson-plan progress tracker for TextCourses.

Inspects lesson-plan.md checklists, parses live concept checkmarks ([ ] vs [x]),
resolves the active concept for instant interruption recovery, and updates checkmarks
atomically as learners progress (FR-12, AD-5).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

CHECKLIST_RE = re.compile(r"^(\s*[-*]\s*\[)([ xX])(\]\s*)(.*)$")


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def atomic_write_text(filepath: Path, content: str) -> None:
    """Write text atomically using a temp file, fsync, and os.replace."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic text write failed for {filepath}: {e}") from e


def resolve_lesson_plan(target_path: Path | str) -> Path:
    """Resolve lesson-plan.md path from file or section directory."""
    p = Path(target_path).resolve()
    if p.is_dir():
        candidate = p / "lesson-plan.md"
        if candidate.is_file():
            return candidate
        # Look one level down for section directories
        for sub in p.glob("**/lesson-plan.md"):
            if sub.is_file():
                return sub
        raise FileNotFoundError(f"No lesson-plan.md found in {p}")
    if not p.is_file():
        raise FileNotFoundError(f"Target lesson plan file does not exist: {p}")
    return p


def parse_checklist_items(content: str) -> list[dict[str, Any]]:
    """Parse all checklist items from markdown content."""
    items: list[dict[str, Any]] = []
    lines = content.splitlines()

    item_idx = 0
    for line_idx, line in enumerate(lines):
        m = CHECKLIST_RE.match(line)
        if m:
            is_completed = m.group(2).strip().lower() == "x"
            item_text = m.group(4).strip()
            items.append({
                "index": item_idx,
                "line_no": line_idx + 1,
                "completed": is_completed,
                "text": item_text,
                "raw_line": line,
            })
            item_idx += 1

    return items


def get_status(target_path: Path | str) -> dict[str, Any]:
    """Retrieve full status of checklist items in lesson plan."""
    plan_file = resolve_lesson_plan(target_path)
    content = plan_file.read_text(encoding="utf-8")
    items = parse_checklist_items(content)

    total = len(items)
    completed = sum(1 for it in items if it["completed"])
    remaining = total - completed
    pct = round((completed / total * 100), 1) if total > 0 else 0.0

    return {
        "ok": True,
        "plan_file": str(plan_file),
        "total_items": total,
        "completed_items": completed,
        "remaining_items": remaining,
        "percent_complete": pct,
        "all_completed": (total > 0 and remaining == 0),
        "items": items,
    }


def get_current_concept(target_path: Path | str) -> dict[str, Any]:
    """Find the current active unfinished concept for interruption recovery."""
    plan_file = resolve_lesson_plan(target_path)
    content = plan_file.read_text(encoding="utf-8")
    items = parse_checklist_items(content)

    for it in items:
        if not it["completed"]:
            return {
                "ok": True,
                "plan_file": str(plan_file),
                "has_active_concept": True,
                "index": it["index"],
                "line_no": it["line_no"],
                "concept": it["text"],
                "remaining_items": sum(1 for x in items if not x["completed"]),
                "total_items": len(items),
            }

    return {
        "ok": True,
        "plan_file": str(plan_file),
        "has_active_concept": False,
        "index": None,
        "concept": None,
        "remaining_items": 0,
        "total_items": len(items),
        "message": "All concepts in this lesson plan are completed.",
    }


def tick_concept(
    target_path: Path | str,
    index: int | None = None,
    concept_query: str | None = None,
) -> dict[str, Any]:
    """Mark a concept as completed ([x]) atomically in lesson-plan.md."""
    plan_file = resolve_lesson_plan(target_path)
    content = plan_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    items = parse_checklist_items(content)

    if not items:
        raise ValueError(f"No checklist items found in {plan_file}")

    target_item: dict[str, Any] | None = None

    if index is not None:
        for it in items:
            if it["index"] == index:
                target_item = it
                break
        if not target_item:
            raise IndexError(f"Checklist item index {index} out of range (0..{len(items)-1})")
    elif concept_query:
        query_norm = concept_query.strip().lower()
        for it in items:
            if not it["completed"] and query_norm in it["text"].lower():
                target_item = it
                break
        if not target_item:
            raise ValueError(f"No uncompleted checklist item matching '{concept_query}'")
    else:
        # Default: first uncompleted item
        for it in items:
            if not it["completed"]:
                target_item = it
                break
        if not target_item:
            return {
                "ok": True,
                "plan_file": str(plan_file),
                "already_all_completed": True,
                "message": "All checklist items are already completed.",
            }

    # Replace line
    line_no_0based = target_item["line_no"] - 1
    orig_line = lines[line_no_0based]
    updated_line = CHECKLIST_RE.sub(r"\g<1>x\g<3>\4", orig_line)
    lines[line_no_0based] = updated_line

    new_content = "\n".join(lines) + "\n"
    atomic_write_text(plan_file, new_content)

    # Re-evaluate remaining
    remaining = sum(1 for it in items if not it["completed"] and it["index"] != target_item["index"])

    return {
        "ok": True,
        "plan_file": str(plan_file),
        "ticked_index": target_item["index"],
        "ticked_concept": target_item["text"],
        "remaining_items": remaining,
        "section_fully_completed": (remaining == 0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lesson_tracker.py",
        description="TextCourses session hygiene and lesson-plan progress tracker.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # status
    p_stat = subparsers.add_parser("status", help="Inspect completion status of lesson-plan.md.")
    p_stat.add_argument("--path", required=True, help="Path to section directory or lesson-plan.md.")
    p_stat.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # current
    p_curr = subparsers.add_parser("current", help="Get active concept for interruption recovery.")
    p_curr.add_argument("--path", required=True, help="Path to section directory or lesson-plan.md.")
    p_curr.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # tick
    p_tick = subparsers.add_parser("tick", help="Tick off completed concept in lesson-plan.md.")
    p_tick.add_argument("--path", required=True, help="Path to section directory or lesson-plan.md.")
    p_tick.add_argument("--index", type=int, default=None, help="Checklist item index to tick.")
    p_tick.add_argument("--concept", default=None, help="Substring match of concept to tick.")
    p_tick.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    try:
        if args.subcommand == "status":
            result = get_status(args.path)
            output_json(result, 0)

        elif args.subcommand == "current":
            result = get_current_concept(args.path)
            output_json(result, 0)

        elif args.subcommand == "tick":
            result = tick_concept(args.path, index=args.index, concept_query=args.concept)
            output_json(result, 0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except Exception as e:
        output_json({"error": str(e), "ok": False}, 1)


if __name__ == "__main__":
    main()
