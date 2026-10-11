#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""notes_compiler.py — Human-first textbook notes compiler and section transition manager for TextCourses.

Distills completed section concepts into permanent, human-first notes.md with 3-bullet recap,
plain English intuitive mental models, step-by-step mechanics, concrete examples, and common traps.
Atomically transitions section status in course.toml to 'review', updates flat chapter textbook
notes/chapter-XX.md, and mirrors token-minimal milestones to courses/<slug>/memlog.md (FR-11, FR-32, AD-3).
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

import tomli_w


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


def atomic_write_toml(filepath: Path, data: dict[str, Any]) -> None:
    """Write TOML data atomically using a temp file, fsync, and os.replace."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, "wb") as f:
            tomli_w.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic TOML write failed for {filepath}: {e}") from e


def find_enclosing_manifest(start_dir: Path) -> Path | None:
    """Find course.toml by walking up directory tree from section dir."""
    curr = start_dir.resolve()
    for _ in range(5):
        manifest = curr / "course.toml"
        if manifest.is_file():
            return manifest
        if curr.parent == curr:
            break
        curr = curr.parent
    return None


def format_textbook_notes(
    title: str,
    recap_bullets: list[str],
    content: str = "",
    examples: str = "",
    pitfalls: str = "",
    teacher: str | None = None,
    analogy: str | None = None,
) -> str:
    """Format structured, human-first textbook markdown in accessible plain English."""
    lines = [
        f"# {title.strip()}",
        "",
    ]
    if teacher:
        lines.extend([
            f"*Distilled by {teacher.strip()}*",
            "",
        ])

    lines.extend([
        "## 3-Bullet Recap (In Plain English)",
    ])
    for bullet in recap_bullets:
        clean_bullet = bullet.strip().lstrip("-* ").strip()
        lines.append(f"- {clean_bullet}")

    if analogy:
        lines.extend([
            "",
            "## Intuitive Mental Model & Analogy",
            analogy.strip(),
        ])

    lines.extend([
        "",
        "## Core Mechanics & Architecture",
        content.strip() or "Foundational mechanics, constraints, and system design principles explained step-by-step.",
        "",
        "## Worked Examples & Concrete Implementation",
        examples.strip() or "Standard idioms, implementation patterns, and code walkthroughs.",
        "",
        "## Common Pitfalls & Fatal Mistakes",
        pitfalls.strip() or "Crucial invariants, edge cases, and architectural anti-patterns to avoid.",
        "",
    ])

    return "\n".join(lines)


def update_course_manifest_section_status(
    manifest_path: Path,
    section_dir_name: str,
    new_status: str = "review",
    chapter_dir_name: str | None = None,
) -> tuple[bool, str | None]:
    """Atomically update section status in course.toml matching section directory name and optional chapter."""
    try:
        data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, str(e)

    chapters = data.get("chapters", [])
    found = False

    # Extract clean section id token, e.g. "sec-01" from "section-01-intro"
    sec_id_match = re.search(r"sec(?:tion)?[-_]?0*(\d+)", section_dir_name, re.IGNORECASE)
    expected_sec_num = int(sec_id_match.group(1)) if sec_id_match else None

    # Determine candidate chapters if chapter_dir_name is provided
    candidate_chapters = chapters
    if chapter_dir_name:
        ch_id_match = re.search(r"ch(?:apter)?[-_]?0*(\d+)", chapter_dir_name, re.IGNORECASE)
        expected_ch_num = int(ch_id_match.group(1)) if ch_id_match else None

        matching_chapters = []
        for ch_idx, ch in enumerate(chapters, 1):
            ch_id = str(ch.get("id", ""))
            ch_slug = str(ch.get("slug", ""))
            ch_id_num = None
            m_c = re.search(r"ch(?:apter)?[-_]?0*(\d+)", ch_id, re.IGNORECASE)
            if m_c:
                ch_id_num = int(m_c.group(1))

            if (
                ch_id == chapter_dir_name
                or ch_slug == chapter_dir_name
                or chapter_dir_name.lower() in ch_slug.lower()
                or (expected_ch_num is not None and (ch_id_num == expected_ch_num or ch_idx == expected_ch_num))
            ):
                matching_chapters.append(ch)

        if matching_chapters:
            candidate_chapters = matching_chapters

    def search_chapters(chs: list[dict[str, Any]]) -> bool:
        for ch in chs:
            for idx, sec in enumerate(ch.get("sections", []), 1):
                sec_id = str(sec.get("id", ""))
                sec_slug = str(sec.get("slug", ""))
                sec_id_num = None
                m_s = re.search(r"sec(?:tion)?[-_]?0*(\d+)", sec_id, re.IGNORECASE)
                if m_s:
                    sec_id_num = int(m_s.group(1))

                if (
                    sec_id == section_dir_name
                    or sec_slug == section_dir_name
                    or (expected_sec_num is not None and (sec_id_num == expected_sec_num or idx == expected_sec_num))
                ):
                    sec["status"] = new_status
                    sec["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    return True
        return False

    found = search_chapters(candidate_chapters)
    if not found and candidate_chapters is not chapters:
        found = search_chapters(chapters)

    if found:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if "course" in data:
            data["course"]["updated_at"] = now_iso
        atomic_write_toml(manifest_path, data)
        return True, None

    return False, f"Could not match section '{section_dir_name}' in {manifest_path}"


def append_memlog_milestone(course_dir: Path, sec_name: str, status: str) -> None:
    """Mirror token-minimal milestone entry into course memlog.md."""
    memlog_path = course_dir / "memlog.md"
    if not memlog_path.exists():
        return

    sec_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", sec_name.lower()).strip("-")
    entry_line = f"- (milestone) sec:{sec_slug}:status={status}:notes_compiled\n"
    try:
        with open(memlog_path, "a", encoding="utf-8") as f:
            f.write(entry_line)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def compile_notes(
    section_dir: Path | str,
    title: str,
    recap: list[str],
    content: str = "",
    examples: str = "",
    pitfalls: str = "",
    force: bool = False,
    target_status: str = "review",
    chapter_dir_name: str | None = None,
    teacher: str | None = None,
    analogy: str | None = None,
) -> dict[str, Any]:
    """Compile human-first section notes into notes.md, update chapter textbook, and mirror to memlog."""
    sec_path = Path(section_dir).resolve()
    if not sec_path.is_dir():
        raise NotADirectoryError(f"Target section path is not a directory: {sec_path}")

    notes_file = sec_path / "notes.md"
    if notes_file.exists() and not force:
        raise FileExistsError(
            f"notes.md already exists in {sec_path}. Completed notes are permanent and immutable. Pass --force to overwrite."
        )

    if not recap:
        raise ValueError("At least one recap bullet point is required for notes compilation.")

    notes_text = format_textbook_notes(
        title=title,
        recap_bullets=recap,
        content=content,
        examples=examples,
        pitfalls=pitfalls,
        teacher=teacher,
        analogy=analogy,
    )

    # Atomically write section notes.md
    atomic_write_text(notes_file, notes_text)

    # Locate and update course.toml, flat chapter textbook, and memlog
    manifest_file = find_enclosing_manifest(sec_path)
    manifest_updated = False
    warning = None
    effective_chapter = chapter_dir_name or sec_path.parent.name
    chapter_notes_file = None

    if manifest_file:
        ok, err = update_course_manifest_section_status(
            manifest_path=manifest_file,
            section_dir_name=sec_path.name,
            new_status=target_status,
            chapter_dir_name=effective_chapter,
        )
        if ok:
            manifest_updated = True
        else:
            warning = err

        course_dir = manifest_file.parent

        # 1. Update flat chapter textbook notes at courses/<slug>/notes/chapter-XX.md
        notes_dir = course_dir / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)

        ch_num = 1
        m_c = re.search(r"ch(?:apter)?[-_]?0*(\d+)", effective_chapter, re.IGNORECASE)
        if m_c:
            ch_num = int(m_c.group(1))

        ch_notes_path = notes_dir / f"chapter-{ch_num:02d}.md"
        chapter_notes_file = str(ch_notes_path)
        if not ch_notes_path.exists():
            header = f"# Chapter {ch_num:02d} Notes\n\n"
            atomic_write_text(ch_notes_path, header + notes_text + "\n")
        else:
            existing = ch_notes_path.read_text(encoding="utf-8")
            if f"# {title.strip()}" not in existing:
                atomic_write_text(ch_notes_path, existing.rstrip() + f"\n\n---\n\n{notes_text}\n")

        # 2. Mirror token-minimal milestone to courses/<slug>/memlog.md
        append_memlog_milestone(course_dir, sec_path.name, target_status)
    else:
        warning = f"No enclosing course.toml found above {sec_path}"

    return {
        "ok": True,
        "notes_file": str(notes_file),
        "chapter_notes_file": chapter_notes_file,
        "title": title,
        "recap_bullets": len(recap),
        "size_bytes": len(notes_text.encode("utf-8")),
        "course_manifest_updated": manifest_updated,
        "manifest_path": str(manifest_file) if manifest_file else None,
        "section_status": target_status,
        "teacher": teacher,
        "warning": warning,
    }


def inspect_notes(section_dir: Path | str) -> dict[str, Any]:
    """Inspect notes compilation status for target section directory."""
    sec_path = Path(section_dir).resolve()
    if not sec_path.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {sec_path}")

    notes_file = sec_path / "notes.md"
    manifest_file = find_enclosing_manifest(sec_path)

    if not notes_file.is_file():
        return {
            "ok": True,
            "section_dir": str(sec_path),
            "compiled": False,
            "notes_file": None,
            "manifest_file": str(manifest_file) if manifest_file else None,
        }

    text = notes_file.read_text(encoding="utf-8")
    recap_items = re.findall(r"^-\s+(.+)$", text, re.MULTILINE)

    return {
        "ok": True,
        "section_dir": str(sec_path),
        "compiled": True,
        "notes_file": str(notes_file),
        "size_bytes": len(text.encode("utf-8")),
        "recap_bullets_count": len(recap_items),
        "manifest_file": str(manifest_file) if manifest_file else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="notes_compiler.py",
        description="TextCourses human-first textbook notes compiler and section transition manager.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # compile
    p_comp = subparsers.add_parser("compile", help="Compile section notes and advance status in course.toml.")
    p_comp.add_argument("--section-dir", required=True, help="Path to section directory.")
    p_comp.add_argument("--title", required=True, help="Section title.")
    p_comp.add_argument("--recap", nargs="+", required=True, help="3-bullet recap items.")
    p_comp.add_argument("--content", default="", help="Detailed technical mechanics content.")
    p_comp.add_argument("--examples", default="", help="Worked examples content.")
    p_comp.add_argument("--pitfalls", default="", help="Common pitfalls content.")
    p_comp.add_argument("--chapter", default=None, help="Optional chapter identifier or directory name.")
    p_comp.add_argument("--status", default="review", help="Target status for section in course.toml (default: review).")
    p_comp.add_argument("--teacher", default=None, help="Active teacher persona attribution.")
    p_comp.add_argument("--analogy", default=None, help="Intuitive plain-English mental model or analogy.")
    p_comp.add_argument("--force", action="store_true", help="Force overwrite existing notes.")
    p_comp.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # inspect
    p_insp = subparsers.add_parser("inspect", help="Inspect notes status for section.")
    p_insp.add_argument("--section-dir", required=True, help="Path to section directory.")
    p_insp.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    try:
        if args.subcommand == "compile":
            result = compile_notes(
                section_dir=args.section_dir,
                title=args.title,
                recap=args.recap,
                content=args.content,
                examples=args.examples,
                pitfalls=args.pitfalls,
                force=args.force,
                target_status=args.status,
                chapter_dir_name=args.chapter,
                teacher=args.teacher,
                analogy=args.analogy,
            )
            output_json(result, 0)

        elif args.subcommand == "inspect":
            result = inspect_notes(args.section_dir)
            output_json(result, 0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except FileExistsError as fee:
        output_json({"error": str(fee), "already_exists": True, "ok": False}, 1)
    except Exception as e:
        output_json({"error": str(e), "ok": False}, 1)


if __name__ == "__main__":
    main()
