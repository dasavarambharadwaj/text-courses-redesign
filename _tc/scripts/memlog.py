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
import re
import sys
from pathlib import Path
from typing import Any

DEFAULT_MEMLOG_NAME = "memlog.md"


def compress_to_token_minimal(text: str) -> str:
    """Format text into token-minimal, compact representation for AI context efficiency."""
    clean = re.sub(r"\s+", " ", text).strip()
    return clean


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


def normalize_chapter_name(ch: str) -> str:
    """Normalize chapter identifier to canonical directory name (e.g. '01' -> 'chapter-01')."""
    ch = str(ch).strip()
    if ch.isdigit():
        return f"chapter-{int(ch):02d}"
    if ch.startswith("ch-") or ch.startswith("chapter-"):
        parts = ch.split("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return f"chapter-{int(parts[1]):02d}"
        return ch
    return ch


def normalize_section_name(sec: str) -> str:
    """Normalize section identifier to canonical directory name (e.g. '01' -> 'section-01')."""
    sec = str(sec).strip()
    if sec.isdigit():
        return f"section-{int(sec):02d}"
    if sec.startswith("sec-") or sec.startswith("section-"):
        parts = sec.split("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return f"section-{int(parts[1]):02d}"
        return sec
    return sec


def resolve_scoped_memlog_path(
    workspace: Path,
    scope: str,
    course: str | None = None,
    chapter: str | None = None,
    section: str | None = None,
) -> Path:
    """Resolve hierarchical memlog path based on scope."""
    ws = Path(workspace).resolve()
    s = scope.lower().strip()
    if s in {"global", "profile", "workspace"}:
        return ws / "_tc" / "profile" / DEFAULT_MEMLOG_NAME
    elif s == "roadmap":
        return ws / "_tc" / "roadmap" / DEFAULT_MEMLOG_NAME
    elif s == "research":
        if not course:
            raise ValueError("--course or topic slug is required for research scope")
        return ws / "_tc" / "research" / course / DEFAULT_MEMLOG_NAME
    elif s == "course":
        if not course:
            raise ValueError("--course slug is required for course scope")
        return ws / "_tc" / "courses" / course / DEFAULT_MEMLOG_NAME
    elif s == "chapter":
        if not course or not chapter:
            raise ValueError("--course and --chapter are required for chapter scope")
        ch_dir = normalize_chapter_name(chapter)
        return ws / "_tc" / "courses" / course / "chapters" / ch_dir / DEFAULT_MEMLOG_NAME
    elif s == "section":
        if not course or not chapter or not section:
            raise ValueError("--course, --chapter, and --section are required for section scope")
        ch_dir = normalize_chapter_name(chapter)
        sec_dir = normalize_section_name(section)
        return ws / "_tc" / "courses" / course / "chapters" / ch_dir / "sections" / sec_dir / DEFAULT_MEMLOG_NAME
    else:
        raise ValueError(
            f"Unknown memlog scope '{scope}'. Supported scopes: global/profile, roadmap, research, course, chapter, section"
        )


def resolve_memlog_path(args: argparse.Namespace) -> Path:
    """Resolve target memlog file path from explicit --path, --workspace, or hierarchical --scope."""
    scope = getattr(args, "scope", None)
    if scope:
        ws = getattr(args, "workspace", None) or getattr(args, "path", None) or "."
        course = getattr(args, "course", None) or getattr(args, "slug", None)
        chapter = getattr(args, "chapter", None)
        section = getattr(args, "section", None)
        return resolve_scoped_memlog_path(Path(ws), scope, course, chapter, section)

    if getattr(args, "path", None):
        p = Path(args.path)
        if p.is_dir():
            tc_m = p / "_tc" / "profile" / DEFAULT_MEMLOG_NAME
            if tc_m.is_file():
                return tc_m
            tc_legacy = p / ".tc" / DEFAULT_MEMLOG_NAME
            if tc_legacy.is_file():
                return tc_legacy
            return p / DEFAULT_MEMLOG_NAME
        return p
    if getattr(args, "workspace", None):
        ws = Path(args.workspace)
        if (ws / "_tc" / "profile" / DEFAULT_MEMLOG_NAME).is_file():
            return ws / "_tc" / "profile" / DEFAULT_MEMLOG_NAME
        return ws / DEFAULT_MEMLOG_NAME
    raise ValueError("Neither --path, --workspace, nor --scope was provided")


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


def append_entry_to_file(
    filepath: Path,
    entry_line: str,
    default_topic: str = "TextCourses Memlog",
    default_type: str = "memlog",
) -> None:
    """Ensure directory and file exist, initializing frontmatter if necessary, and atomically append entry."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if not filepath.exists():
        now = now_iso()
        init_fm = {
            "type": default_type,
            "topic": default_topic,
            "created": now,
            "updated": now,
        }
        atomic_write_memlog(filepath, init_fm, [])

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(entry_line + "\n")
        f.flush()
        os.fsync(f.fileno())


def append_entry(
    workspace: Path | str,
    text: str,
    scope: str = "profile",
    course_slug: str | None = None,
    chapter: str | None = None,
    section: str | None = None,
    tag: str = "decision",
    by: str | None = None,
    roll_up: bool = False,
) -> Path:
    """Convenience Python API to append an entry to a scoped memlog."""
    ws = Path(workspace).resolve()
    target_path = resolve_scoped_memlog_path(
        ws,
        scope=scope,
        course=course_slug,
        chapter=chapter,
        section=section,
    )
    prefix = f"- ({tag}) " if tag else "- "
    if tag and by:
        prefix = f"- ({tag} by {by}) "
    entry_line = f"{prefix}{text}"
    default_topic = f"{scope.capitalize()} Memlog" if scope else "TextCourses Session"
    append_entry_to_file(target_path, entry_line, default_topic=default_topic)

    if roll_up and scope in {"section", "chapter", "course", "research"}:
        global_path = ws / "_tc" / "profile" / DEFAULT_MEMLOG_NAME
        append_entry_to_file(global_path, f"- (milestone) [{course_slug or scope}] {text}", default_topic="Learner Journey")

    return target_path


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new pedagogical memlog file."""
    memlog_path = resolve_memlog_path(args)
    if memlog_path.exists() and not getattr(args, "force", False):
        output_json({
            "ok": False,
            "error": f"Memlog already exists at {memlog_path}. Use --force to overwrite.",
        }, exit_code=1)

    now = now_iso()
    scope = getattr(args, "scope", None)
    frontmatter: dict[str, str] = {
        "type": f"{scope}-memlog" if scope else "memlog",
        "topic": args.topic or (f"{scope.capitalize()} Memlog" if scope else "TextCourses Learning Session"),
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
    """Append a single chronological entry to the end of the memlog, with optional hierarchical roll-up."""
    try:
        memlog_path = resolve_memlog_path(args)
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    text = (getattr(args, "content", None) or getattr(args, "text", None) or "").strip()
    if not text:
        output_json({"ok": False, "error": "No entry content/text provided"}, exit_code=1)

    if getattr(args, "compact", False) or getattr(args, "token_minimal", False):
        text = compress_to_token_minimal(text)

    entry_type = getattr(args, "tag", None) or getattr(args, "type", None)
    entry_by = getattr(args, "by", None)

    if entry_type and entry_by:
        prefix = f"- ({entry_type} by {entry_by}) "
    elif entry_type:
        prefix = f"- ({entry_type}) "
    elif entry_by:
        prefix = f"- (by {entry_by}) "
    else:
        prefix = "- "

    entry_line = f"{prefix}{text}"

    scope = getattr(args, "scope", None)
    default_topic = f"{scope.capitalize()} Memlog" if scope else "TextCourses Session"
    append_entry_to_file(memlog_path, entry_line, default_topic=default_topic)

    rolled_up_paths: list[str] = []
    is_rollup = getattr(args, "roll_up", False) or getattr(args, "rollup", False)

    if is_rollup and scope:
        ws = Path(getattr(args, "workspace", None) or getattr(args, "path", None) or ".").resolve()
        course = getattr(args, "course", None) or getattr(args, "slug", None)
        chapter = getattr(args, "chapter", None)
        section = getattr(args, "section", None)
        tag = entry_type or "milestone"

        ch_dir = normalize_chapter_name(chapter) if chapter else ""
        sec_dir = normalize_section_name(section) if section else ""

        if scope == "section":
            # 1. Roll-up to Chapter
            ch_path = ws / "_tc" / "courses" / course / "chapters" / ch_dir / DEFAULT_MEMLOG_NAME
            ch_entry = f"- ({tag}) [{sec_dir}] {text}"
            append_entry_to_file(ch_path, ch_entry, default_topic=f"Chapter {ch_dir} Memlog", default_type="chapter-memlog")
            rolled_up_paths.append(str(ch_path))

            # 2. Roll-up to Course
            course_path = ws / "_tc" / "courses" / course / DEFAULT_MEMLOG_NAME
            course_entry = f"- ({tag}) [{ch_dir}/{sec_dir}] {text}"
            append_entry_to_file(course_path, course_entry, default_topic=f"Course {course} Memlog", default_type="course-memlog")
            rolled_up_paths.append(str(course_path))

            # 3. Roll-up to Global Profile
            global_path = ws / "_tc" / "profile" / DEFAULT_MEMLOG_NAME
            global_entry = f"- ({tag}) [{course}/{ch_dir}/{sec_dir}] {text}"
            append_entry_to_file(global_path, global_entry, default_topic="Global Learning Memlog", default_type="global-memlog")
            rolled_up_paths.append(str(global_path))

        elif scope == "chapter":
            # 1. Roll-up to Course
            course_path = ws / "_tc" / "courses" / course / DEFAULT_MEMLOG_NAME
            course_entry = f"- ({tag}) [{ch_dir}] {text}"
            append_entry_to_file(course_path, course_entry, default_topic=f"Course {course} Memlog", default_type="course-memlog")
            rolled_up_paths.append(str(course_path))

            # 2. Roll-up to Global Profile
            global_path = ws / "_tc" / "profile" / DEFAULT_MEMLOG_NAME
            global_entry = f"- ({tag}) [{course}/{ch_dir}] {text}"
            append_entry_to_file(global_path, global_entry, default_topic="Global Learning Memlog", default_type="global-memlog")
            rolled_up_paths.append(str(global_path))

        elif scope in {"course", "research", "roadmap"}:
            global_path = ws / "_tc" / "profile" / DEFAULT_MEMLOG_NAME
            label = f"{scope}/{course}" if course else scope
            global_entry = f"- ({tag}) [{label}] {text}"
            append_entry_to_file(global_path, global_entry, default_topic="Global Learning Memlog", default_type="global-memlog")
            rolled_up_paths.append(str(global_path))

    output_json({
        "ok": True,
        "message": "Appended entry to memlog" + (" with milestone roll-up" if rolled_up_paths else ""),
        "path": str(memlog_path),
        "scope": scope,
        "entry": entry_line,
        "rolled_up": bool(rolled_up_paths),
        "rolled_up_paths": rolled_up_paths,
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
    p_init.add_argument("--scope", choices=["workspace", "global", "profile", "roadmap", "research", "course", "chapter", "section"], help="Memlog hierarchical scope")
    p_init.add_argument("--course", "--slug", dest="course", help="Course or research domain slug")
    p_init.add_argument("--chapter", help="Chapter identifier")
    p_init.add_argument("--section", help="Section identifier")
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
    p_app.add_argument("--scope", choices=["workspace", "global", "profile", "roadmap", "research", "course", "chapter", "section"], help="Memlog hierarchical scope")
    p_app.add_argument("--course", "--slug", dest="course", help="Course or research domain slug")
    p_app.add_argument("--chapter", help="Chapter identifier (e.g. 01, chapter-01)")
    p_app.add_argument("--section", help="Section identifier (e.g. 01, section-01)")
    p_app.add_argument("--text", default=None, help="Entry text")
    p_app.add_argument("--content", default=None, help="Entry content text (alias for --text)")
    p_app.add_argument("--type", help="Entry tag: concept, question, insight, misconception, analogy, handoff, milestone, decision")
    p_app.add_argument("--tag", help="Entry tag: alias for --type")
    p_app.add_argument("--by", help="Origin author: user, teacher, coach, examiner")
    p_app.add_argument("--roll-up", "--rollup", dest="roll_up", action="store_true", help="Propagate milestone summaries up the hierarchy")
    p_app.add_argument("--compact", action="store_true", help="Compress entry to token-minimal format")
    p_app.add_argument("--token-minimal", action="store_true", help="Compress entry to token-minimal format")
    p_app.set_defaults(func=cmd_append)

    # set
    p_set = subparsers.add_parser("set", help="Update frontmatter field")
    p_set.add_argument("--path", help="Explicit memlog file or directory path")
    p_set.add_argument("--workspace", help="Target workspace root")
    p_set.add_argument("--scope", choices=["workspace", "global", "profile", "roadmap", "research", "course", "chapter", "section"], help="Memlog hierarchical scope")
    p_set.add_argument("--course", "--slug", dest="course", help="Course or research domain slug")
    p_set.add_argument("--chapter", help="Chapter identifier")
    p_set.add_argument("--section", help="Section identifier")
    p_set.add_argument("--key", required=True, help="Frontmatter key")
    p_set.add_argument("--value", required=True, help="Frontmatter value")
    p_set.set_defaults(func=cmd_set)

    # tail
    p_tail = subparsers.add_parser("tail", help="Get trailing entries for turn injection")
    p_tail.add_argument("--path", help="Explicit memlog file or directory path")
    p_tail.add_argument("--workspace", help="Target workspace root")
    p_tail.add_argument("--scope", choices=["workspace", "global", "profile", "roadmap", "research", "course", "chapter", "section"], help="Memlog hierarchical scope")
    p_tail.add_argument("--course", "--slug", dest="course", help="Course or research domain slug")
    p_tail.add_argument("--chapter", help="Chapter identifier")
    p_tail.add_argument("--section", help="Section identifier")
    p_tail.add_argument("--n", type=int, default=15, help="Number of trailing entries to return")
    p_tail.set_defaults(func=cmd_tail)

    # inspect
    p_insp = subparsers.add_parser("inspect", help="Inspect full memlog contents")
    p_insp.add_argument("--path", help="Explicit memlog file or directory path")
    p_insp.add_argument("--workspace", help="Target workspace root")
    p_insp.add_argument("--scope", choices=["workspace", "global", "profile", "roadmap", "research", "course", "chapter", "section"], help="Memlog hierarchical scope")
    p_insp.add_argument("--course", "--slug", dest="course", help="Course or research domain slug")
    p_insp.add_argument("--chapter", help="Chapter identifier")
    p_insp.add_argument("--section", help="Section identifier")
    p_insp.set_defaults(func=cmd_inspect)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
