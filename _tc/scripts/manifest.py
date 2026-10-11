#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""manifest.py — Deterministic TOML manifest manager for TextCourses.

Handles atomic reading, schema validation, and safe state mutations for
course.toml and roadmap.toml without LLM formatting hallucinations or
partial-write corruptions.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

VALID_STATUSES = {"not_started", "in_progress", "review", "completed"}
ROADMAP_COURSE_STATUSES = {"not_started", "active", "in_progress", "completed", "waived"}


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (or stderr on error) and exit."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


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
        raise RuntimeError(f"Atomic write failed for {filepath}: {e}") from e


def load_toml(filepath: Path) -> dict[str, Any]:
    """Read and parse a TOML file safely."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Manifest not found: {filepath}")
    with open(filepath, "rb") as f:
        return tomllib.load(f)


def cmd_init_course(args: argparse.Namespace) -> None:
    """Initialize a canonical course.toml manifest."""
    target_path = Path(args.path)
    if target_path.suffix == ".toml":
        manifest_path = target_path
    else:
        manifest_path = target_path / "course.toml"

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest_data: dict[str, Any] = {
        "course": {
            "slug": args.slug,
            "title": args.title,
            "status": "not_started",
            "created": now_iso,
            "updated": now_iso,
            "archetype": getattr(args, "archetype", "applied_creation"),
        },
        "chapters": [],
    }

    atomic_write_toml(manifest_path, manifest_data)
    output_json({
        "ok": True,
        "message": f"Initialized course manifest at {manifest_path}",
        "path": str(manifest_path),
        "slug": args.slug,
        "title": args.title,
    })


def cmd_init_roadmap(args: argparse.Namespace) -> None:
    """Initialize a canonical roadmap.toml manifest."""
    target_path = Path(args.path)
    if target_path.suffix == ".toml":
        manifest_path = target_path
    else:
        manifest_path = target_path / "roadmap.toml"

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest_data: dict[str, Any] = {
        "roadmap": {
            "title": args.title,
            "status": "not_started",
            "created": now_iso,
            "updated": now_iso,
            "courses": [],
        }
    }

    atomic_write_toml(manifest_path, manifest_data)
    output_json({
        "ok": True,
        "message": f"Initialized roadmap manifest at {manifest_path}",
        "path": str(manifest_path),
        "title": args.title,
    })


def cmd_get_status(args: argparse.Namespace) -> None:
    """Read progress state from course.toml or roadmap.toml."""
    target_path = Path(args.path)
    manifest_path = (
        target_path / "course.toml" if (target_path / "course.toml").exists()
        else target_path / "roadmap.toml" if (target_path / "roadmap.toml").exists()
        else target_path
    )

    try:
        data = load_toml(manifest_path)
    except FileNotFoundError as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)
    except Exception as e:
        output_json({"ok": False, "error": f"Failed to parse manifest: {e}"}, exit_code=1)

    if "course" in data:
        course = data["course"]
        chapters = data.get("chapters", [])
        total_sections = 0
        completed_sections = 0
        active_chapter = None
        active_section = None

        for ch in chapters:
            sections = ch.get("sections", [])
            total_sections += len(sections)
            for sec in sections:
                if sec.get("status") == "completed":
                    completed_sections += 1
                elif sec.get("status") in {"in_progress", "review"} and active_section is None:
                    active_chapter = {"id": ch.get("id"), "slug": ch.get("slug")}
                    active_section = sec

        output_json({
            "ok": True,
            "type": "course",
            "slug": course.get("slug"),
            "title": course.get("title"),
            "status": course.get("status"),
            "total_chapters": len(chapters),
            "total_sections": total_sections,
            "completed_sections": completed_sections,
            "active_chapter": active_chapter,
            "active_section": active_section,
        })
    elif "roadmap" in data:
        roadmap = data["roadmap"]
        courses = roadmap.get("courses", [])
        output_json({
            "ok": True,
            "type": "roadmap",
            "title": roadmap.get("title"),
            "status": roadmap.get("status"),
            "total_courses": len(courses),
            "courses": courses,
        })
    else:
        output_json({"ok": False, "error": "Unrecognized manifest format"}, exit_code=1)


def cmd_advance(args: argparse.Namespace) -> None:
    """Atomically update section status in course.toml."""
    target_path = Path(args.path)
    manifest_path = target_path / "course.toml" if target_path.is_dir() else target_path

    if args.status not in VALID_STATUSES:
        output_json({
            "ok": False,
            "error": f"Invalid status '{args.status}'. Must be one of {sorted(VALID_STATUSES)}",
        }, exit_code=1)

    try:
        data = load_toml(manifest_path)
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    chapters = data.get("chapters", [])
    found_section = False

    for ch in chapters:
        if ch.get("id") == args.chapter:
            for sec in ch.get("sections", []):
                if sec.get("id") == args.section:
                    sec["status"] = args.status
                    sec["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    found_section = True
                    break

    if not found_section:
        output_json({
            "ok": False,
            "error": f"Section id={args.section} in chapter id={args.chapter} not found",
        }, exit_code=1)

    data["course"]["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # If any section is in_progress or review, mark course in_progress
    all_sections = [
        sec for ch in chapters for sec in ch.get("sections", [])
    ]
    if all(s.get("status") == "completed" for s in all_sections) and all_sections:
        data["course"]["status"] = "completed"
    elif any(s.get("status") in {"in_progress", "review", "completed"} for s in all_sections):
        data["course"]["status"] = "in_progress"

    try:
        atomic_write_toml(manifest_path, data)
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    output_json({
        "ok": True,
        "message": f"Updated chapter {args.chapter} section {args.section} to status '{args.status}'",
        "chapter": args.chapter,
        "section": args.section,
        "status": args.status,
        "course_status": data["course"]["status"],
    })


def cmd_add_course(args: argparse.Namespace) -> None:
    """Add a course table to roadmap.toml manifest."""
    target_path = Path(args.path)
    if target_path.is_dir():
        for cand in [
            target_path / "roadmap.toml",
            target_path / "roadmap" / "roadmap.toml",
            target_path / "plan" / "roadmap.toml",
        ]:
            if cand.is_file():
                manifest_path = cand
                break
        else:
            manifest_path = target_path / "roadmap.toml"
    else:
        manifest_path = target_path

    try:
        data = load_toml(manifest_path)
    except Exception as e:
        output_json({"ok": False, "error": f"Failed to load roadmap: {e}"}, exit_code=1)

    if "roadmap" not in data:
        output_json({"ok": False, "error": f"Not a roadmap manifest: {manifest_path}"}, exit_code=1)

    courses = data["roadmap"].setdefault("courses", [])
    if any(c.get("slug") == args.slug for c in courses if isinstance(c, dict)):
        output_json({"ok": False, "error": f"Course with slug '{args.slug}' already exists in roadmap"}, exit_code=1)

    status = getattr(args, "status", "not_started")
    raw_prereqs = getattr(args, "prerequisites", None) or []
    if isinstance(raw_prereqs, str):
        prereqs = [p.strip() for p in raw_prereqs.split(",") if p.strip()]
    elif isinstance(raw_prereqs, list):
        prereqs = raw_prereqs
    else:
        prereqs = []

    new_course: dict[str, Any] = {
        "slug": args.slug,
        "title": args.title,
        "status": status,
        "prerequisites": prereqs,
    }
    if getattr(args, "archetype", None):
        new_course["archetype"] = args.archetype

    courses.append(new_course)
    data["roadmap"]["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        atomic_write_toml(manifest_path, data)
    except Exception as e:
        output_json({"ok": False, "error": f"Failed to write roadmap: {e}"}, exit_code=1)

    output_json({
        "ok": True,
        "message": f"Added course '{args.slug}' to roadmap {manifest_path}",
        "slug": args.slug,
        "title": args.title,
        "status": status,
        "prerequisites": prereqs,
        "total_courses": len(courses),
    })


def cmd_advance_course(args: argparse.Namespace) -> None:
    """Update course status in roadmap.toml."""
    target_path = Path(args.path)
    if target_path.is_dir():
        for cand in [
            target_path / "roadmap.toml",
            target_path / "roadmap" / "roadmap.toml",
            target_path / "plan" / "roadmap.toml",
        ]:
            if cand.is_file():
                manifest_path = cand
                break
        else:
            manifest_path = target_path / "roadmap.toml"
    else:
        manifest_path = target_path

    new_status = args.status
    if new_status not in ROADMAP_COURSE_STATUSES:
        output_json({
            "ok": False,
            "error": f"Invalid status '{new_status}'. Must be one of {sorted(ROADMAP_COURSE_STATUSES)}",
        }, exit_code=1)

    try:
        data = load_toml(manifest_path)
    except Exception as e:
        output_json({"ok": False, "error": f"Failed to load roadmap: {e}"}, exit_code=1)

    if "roadmap" not in data:
        output_json({"ok": False, "error": f"Not a roadmap manifest: {manifest_path}"}, exit_code=1)

    courses = data["roadmap"].get("courses", [])
    target_course = None
    for c in courses:
        if isinstance(c, dict) and (c.get("slug") == args.slug or c.get("title") == args.slug):
            target_course = c
            break

    if not target_course:
        output_json({"ok": False, "error": f"Course '{args.slug}' not found in roadmap"}, exit_code=1)

    target_course["status"] = new_status
    target_course["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    data["roadmap"]["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Update overall roadmap status
    if all(isinstance(c, dict) and c.get("status") in {"completed", "waived"} for c in courses) and courses:
        data["roadmap"]["status"] = "completed"
    elif any(isinstance(c, dict) and c.get("status") in {"active", "in_progress", "completed", "waived"} for c in courses):
        if data["roadmap"].get("status") == "not_started":
            data["roadmap"]["status"] = "active"

    try:
        atomic_write_toml(manifest_path, data)
    except Exception as e:
        output_json({"ok": False, "error": f"Failed to write roadmap: {e}"}, exit_code=1)

    output_json({
        "ok": True,
        "message": f"Updated course '{args.slug}' to status '{new_status}' in roadmap",
        "slug": args.slug,
        "status": new_status,
        "roadmap_status": data["roadmap"]["status"],
    })


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate schema integrity of a course.toml or roadmap.toml manifest."""
    manifest_path = Path(args.path)

    try:
        data = load_toml(manifest_path)
    except Exception as e:
        output_json({"ok": False, "error": f"Invalid TOML: {e}"}, exit_code=1)

    errors: list[str] = []

    if "course" in data:
        course = data["course"]
        for key in ("slug", "title", "status"):
            if key not in course:
                errors.append(f"Missing required key 'course.{key}'")
        if course.get("status") not in VALID_STATUSES:
            errors.append(f"Invalid 'course.status': {course.get('status')}")

        chapters = data.get("chapters", [])
        if not isinstance(chapters, list):
            errors.append("'chapters' must be a list of tables")
        for idx, ch in enumerate(chapters):
            for key in ("id", "slug", "title"):
                if key not in ch:
                    errors.append(f"Chapter at index {idx} missing required key '{key}'")
            for s_idx, sec in enumerate(ch.get("sections", [])):
                for s_key in ("id", "slug", "title", "status"):
                    if s_key not in sec:
                        errors.append(f"Section {s_idx} in chapter {idx} missing '{s_key}'")
                if sec.get("status") not in VALID_STATUSES:
                    errors.append(f"Invalid section status '{sec.get('status')}' in section {s_idx}")

    elif "roadmap" in data:
        roadmap = data["roadmap"]
        for key in ("title", "status"):
            if key not in roadmap:
                errors.append(f"Missing required key 'roadmap.{key}'")
        courses = roadmap.get("courses", [])
        if not isinstance(courses, list):
            errors.append("'roadmap.courses' must be a list of course tables")
        else:
            known_slugs = set()
            for idx, c in enumerate(courses):
                if not isinstance(c, dict):
                    errors.append(f"Course at index {idx} must be a table")
                    continue
                for key in ("slug", "title"):
                    if key not in c:
                        errors.append(f"Course at index {idx} missing required key '{key}'")
                st = c.get("status", "not_started")
                if st not in ROADMAP_COURSE_STATUSES:
                    errors.append(f"Invalid course status '{st}' at index {idx}")
                if c.get("slug"):
                    known_slugs.add(c["slug"])
            for idx, c in enumerate(courses):
                if isinstance(c, dict):
                    prereqs = c.get("prerequisites", [])
                    if isinstance(prereqs, list):
                        for p in prereqs:
                            if p not in known_slugs:
                                errors.append(f"Course '{c.get('slug')}' references unknown prerequisite '{p}'")
    else:
        errors.append("Manifest must contain either '[course]' or '[roadmap]' root table")

    if errors:
        output_json({"ok": False, "valid": False, "errors": errors}, exit_code=1)

    output_json({"ok": True, "valid": True, "path": str(manifest_path)})


def main() -> None:
    parser = argparse.ArgumentParser(description="TextCourses atomic manifest manager")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # init-course
    p_init_c = subparsers.add_parser("init-course", help="Initialize course.toml")
    p_init_c.add_argument("--path", required=True, help="Directory or file path")
    p_init_c.add_argument("--slug", required=True, help="Course slug")
    p_init_c.add_argument("--title", required=True, help="Course title")
    p_init_c.add_argument("--archetype", default="applied_creation", help="Curriculum archetype")
    p_init_c.set_defaults(func=cmd_init_course)

    # init-roadmap
    p_init_r = subparsers.add_parser("init-roadmap", help="Initialize roadmap.toml")
    p_init_r.add_argument("--path", required=True, help="Directory or file path")
    p_init_r.add_argument("--title", required=True, help="Roadmap title")
    p_init_r.set_defaults(func=cmd_init_roadmap)

    # add-course
    p_add_c = subparsers.add_parser("add-course", help="Add a course to roadmap.toml")
    p_add_c.add_argument("--path", required=True, help="Roadmap directory or file path")
    p_add_c.add_argument("--slug", required=True, help="Course slug")
    p_add_c.add_argument("--title", required=True, help="Course title")
    p_add_c.add_argument("--status", default="not_started", choices=list(ROADMAP_COURSE_STATUSES), help="Initial course status")
    p_add_c.add_argument("--prerequisites", nargs="*", default=[], help="Prerequisite course slugs")
    p_add_c.add_argument("--archetype", default="applied_creation", help="Curriculum archetype")
    p_add_c.set_defaults(func=cmd_add_course)

    # advance-course
    p_adv_c = subparsers.add_parser("advance-course", help="Advance course status in roadmap.toml")
    p_adv_c.add_argument("--path", required=True, help="Roadmap directory or file path")
    p_adv_c.add_argument("--slug", required=True, help="Course slug")
    p_adv_c.add_argument("--status", required=True, choices=list(ROADMAP_COURSE_STATUSES), help="New status")
    p_adv_c.set_defaults(func=cmd_advance_course)

    # get-status
    p_status = subparsers.add_parser("get-status", help="Get course or roadmap progress")
    p_status.add_argument("--path", required=True, help="Directory or file path")
    p_status.set_defaults(func=cmd_get_status)

    # advance
    p_adv = subparsers.add_parser("advance", help="Advance section status")
    p_adv.add_argument("--path", required=True, help="Course directory or file path")
    p_adv.add_argument("--chapter", type=int, required=True, help="Chapter ID")
    p_adv.add_argument("--section", type=int, required=True, help="Section ID")
    p_adv.add_argument("--status", required=True, choices=list(VALID_STATUSES), help="New status")
    p_adv.set_defaults(func=cmd_advance)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate manifest schema")
    p_val.add_argument("--path", required=True, help="Manifest file path")
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
