#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""memlog.py — Append-only pedagogical memory log for TextCourses 2.0.

Provides deterministic, chronological working memory across learning sessions (FR-28).
Maintains global learner milestones (profile/memlog.md) and turn-by-turn course
instruction memory (courses/<slug>/memlog.md) with structured tags: concept,
question, insight, misconception, analogy, handoff, milestone, decision.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any

DEFAULT_MEMLOG_NAME = "memlog.md"


def now_iso() -> str:
    """Return ISO 8601 UTC timestamp."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def resolve_memlog_path(args: argparse.Namespace) -> Path:
    """Resolve target memlog file path from explicit --path or --workspace."""
    if getattr(args, "path", None):
        p = Path(args.path)
        if p.is_dir():
            return p / DEFAULT_MEMLOG_NAME
        return p
    if getattr(args, "workspace", None):
        return Path(args.workspace) / DEFAULT_MEMLOG_NAME
    raise ValueError("Neither --path nor --workspace was provided")


def split_memlog(content: str) -> tuple[dict[str, str], list[str]]:
    """Parse frontmatter key-value pairs and raw entry lines."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, lines

    frontmatter: dict[str, str] = {}
    body_start_idx = 1
    closing_fence_found = False

    for idx in range(1, len(lines)):
        line = lines[idx]
        if line.strip() == "---":
            closing_fence_found = True
            body_start_idx = idx + 1
            break
        if ":" in line:
            k, v = line.split(":", 1)
            frontmatter[k.strip()] = v.strip().strip('"').strip("'")

    if not closing_fence_found:
        return {}, lines

    body_lines = [l for l in lines[body_start_idx:] if l.strip()]
    return frontmatter, body_lines


def atomic_write_memlog(filepath: Path, frontmatter: dict[str, str], body_lines: list[str]) -> None:
    """Atomically rewrite memlog frontmatter and body preserving all content."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")

    lines = ["---"]
    for k, v in frontmatter.items():
        lines.append(f'{k}: "{v}"' if " " in v or ":" in v else f"{k}: {v}")
    lines.append("---")
    lines.append("")
    for b in body_lines:
        lines.append(b)
    lines.append("")

    content = "\n".join(lines)
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic memlog write failed for {filepath}: {e}") from e


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new pedagogical memlog file."""
    memlog_path = resolve_memlog_path(args)
    if memlog_path.exists() and not getattr(args, "force", False):
        output_json({
            "ok": False,
            "error": f"Memlog already exists at {memlog_path}. Use --force to overwrite.",
        }, exit_code=1)

    now = now_iso()
    frontmatter: dict[str, str] = {
        "topic": args.topic or "TextCourses Learning Session",
        "created": now,
        "updated": now,
    }
    if getattr(args, "goal", None):
        frontmatter["goal"] = args.goal
    if getattr(args, "teacher", None):
        frontmatter["teacher"] = args.teacher
    if getattr(args, "mode", None):
        frontmatter["mode"] = args.mode

    atomic_write_memlog(memlog_path, frontmatter, [])
    output_json({
        "ok": True,
        "message": f"Initialized pedagogical memlog at {memlog_path}",
        "path": str(memlog_path),
        "topic": frontmatter["topic"],
    })


def cmd_append(args: argparse.Namespace) -> None:
    """Append a single chronological entry to the end of the memlog."""
    memlog_path = resolve_memlog_path(args)
    if not memlog_path.exists():
        # Auto-initialize if not existing
        now = now_iso()
        init_fm = {
            "topic": "TextCourses Session",
            "created": now,
            "updated": now,
        }
        atomic_write_memlog(memlog_path, init_fm, [])

    entry_type = getattr(args, "type", None)
    entry_by = getattr(args, "by", None)
    text = args.text.strip()

    if entry_type and entry_by:
        prefix = f"- ({entry_type} by {entry_by}) "
    elif entry_type:
        prefix = f"- ({entry_type}) "
    elif entry_by:
        prefix = f"- (by {entry_by}) "
    else:
        prefix = "- "

    entry_line = f"{prefix}{text}\n"

    # OS-level append write
    with open(memlog_path, "a", encoding="utf-8") as f:
        f.write(entry_line)
        f.flush()
        os.fsync(f.fileno())

    output_json({
        "ok": True,
        "message": "Appended entry to memlog",
        "path": str(memlog_path),
        "entry": entry_line.strip(),
    })


def cmd_set(args: argparse.Namespace) -> None:
    """Set or update a frontmatter key in the memlog."""
    memlog_path = resolve_memlog_path(args)
    if not memlog_path.exists():
        output_json({"ok": False, "error": f"Memlog not found at {memlog_path}"}, exit_code=1)

    content = memlog_path.read_text(encoding="utf-8")
    fm, body = split_memlog(content)
    fm[args.key] = args.value
    fm["updated"] = now_iso()

    atomic_write_memlog(memlog_path, fm, body)
    output_json({
        "ok": True,
        "message": f"Updated frontmatter {args.key}={args.value}",
        "path": str(memlog_path),
        "key": args.key,
        "value": args.value,
    })


def cmd_tail(args: argparse.Namespace) -> None:
    """Return the trailing N entries formatted for LLM context injection."""
    memlog_path = resolve_memlog_path(args)
    if not memlog_path.exists():
        output_json({"ok": True, "entries": [], "count": 0, "path": str(memlog_path)})

    content = memlog_path.read_text(encoding="utf-8")
    fm, body = split_memlog(content)
    n = getattr(args, "n", 15)
    trailing_entries = body[-n:] if len(body) > n else body

    output_json({
        "ok": True,
        "path": str(memlog_path),
        "frontmatter": fm,
        "entries": trailing_entries,
        "count": len(trailing_entries),
        "total_entries": len(body),
    })


def cmd_inspect(args: argparse.Namespace) -> None:
    """Inspect full memlog state and parsed entries."""
    memlog_path = resolve_memlog_path(args)
    if not memlog_path.exists():
        output_json({"ok": False, "error": f"Memlog not found at {memlog_path}"}, exit_code=1)

    content = memlog_path.read_text(encoding="utf-8")
    fm, body = split_memlog(content)
    output_json({
        "ok": True,
        "path": str(memlog_path),
        "frontmatter": fm,
        "entries": body,
        "total_entries": len(body),
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="TextCourses Pedagogical Memory Log Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Initialize a new memlog")
    p_init.add_argument("--path", help="Explicit memlog file or directory path")
    p_init.add_argument("--workspace", help="Target workspace root")
    p_init.add_argument("--topic", help="Session or course topic name")
    p_init.add_argument("--goal", help="Learning goal")
    p_init.add_argument("--teacher", help="Primary teacher persona")
    p_init.add_argument("--mode", help="Session mode")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing memlog")
    p_init.set_defaults(func=cmd_init)

    # append
    p_app = subparsers.add_parser("append", help="Append an entry to memlog")
    p_app.add_argument("--path", help="Explicit memlog file or directory path")
    p_app.add_argument("--workspace", help="Target workspace root")
    p_app.add_argument("--text", required=True, help="Entry text")
    p_app.add_argument("--type", help="Entry tag: concept, question, insight, misconception, analogy, handoff, milestone, decision")
    p_app.add_argument("--by", help="Origin author: user, teacher, coach, examiner")
    p_app.set_defaults(func=cmd_append)

    # set
    p_set = subparsers.add_parser("set", help="Update frontmatter field")
    p_set.add_argument("--path", help="Explicit memlog file or directory path")
    p_set.add_argument("--workspace", help="Target workspace root")
    p_set.add_argument("--key", required=True, help="Frontmatter key")
    p_set.add_argument("--value", required=True, help="Frontmatter value")
    p_set.set_defaults(func=cmd_set)

    # tail
    p_tail = subparsers.add_parser("tail", help="Get trailing entries for turn injection")
    p_tail.add_argument("--path", help="Explicit memlog file or directory path")
    p_tail.add_argument("--workspace", help="Target workspace root")
    p_tail.add_argument("--n", type=int, default=15, help="Number of trailing entries to return")
    p_tail.set_defaults(func=cmd_tail)

    # inspect
    p_insp = subparsers.add_parser("inspect", help="Inspect full memlog contents")
    p_insp.add_argument("--path", help="Explicit memlog file or directory path")
    p_insp.add_argument("--workspace", help="Target workspace root")
    p_insp.set_defaults(func=cmd_inspect)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
