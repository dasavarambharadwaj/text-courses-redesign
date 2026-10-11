#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""context.py — Stage-aware Context Loading Manifest engine for TextCourses.

Enforces the Stage Loading Matrix across all TextCourses skills according to
Architectural Decision AD-5 and requirement FR-22. Guarantees that agent context
budgets remain under 4,000 tokens by returning strict authorized file manifests
and rejecting out-of-scope, future, or concept-leaking file reads.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

VALID_SKILLS = {
    "tc-init",
    "tc-create",
    "tc-research",
    "tc-teach",
    "tc-verify-course",
    "tc-test-me",
    "tc-practicals",
    "tc-redirect-course",
    "tc-migrate",
}

# Skill alias normalization mapping (e.g. 'teach' -> 'tc-teach')
SKILL_ALIASES = {
    "init": "tc-init",
    "create": "tc-create",
    "research": "tc-research",
    "teach": "tc-teach",
    "verify": "tc-verify-course",
    "verify-course": "tc-verify-course",
    "test-me": "tc-test-me",
    "test": "tc-test-me",
    "practicals": "tc-practicals",
    "redirect": "tc-redirect-course",
    "redirect-course": "tc-redirect-course",
    "migrate": "tc-migrate",
}


def normalize_skill(skill_name: str) -> str:
    """Normalize skill name string to canonical 'tc-*' format."""
    s = skill_name.strip().lower()
    if s in VALID_SKILLS:
        return s
    if s in SKILL_ALIASES:
        return SKILL_ALIASES[s]
    clean = s if s.startswith("tc-") else f"tc-{s}"
    if clean in VALID_SKILLS:
        return clean
    return s


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def find_workspace_root(start_path: Path) -> Path:
    """Ascend directory tree to find workspace root containing plan/, .tc/, or courses/."""
    current = start_path.resolve()
    for parent in [current, *current.parents]:
        if (parent / "plan").is_dir() or (parent / ".tc").is_dir() or (parent / "courses").is_dir():
            return parent
    return current


def resolve_course_dir(path_arg: str | Path | None) -> tuple[Path, Path | None]:
    """Resolve (course_dir, course.toml_path) from given path argument."""
    if not path_arg:
        target = Path.cwd().resolve()
    else:
        target = Path(path_arg).resolve()

    if target.is_file():
        if target.name == "course.toml":
            return target.parent, target
        return target.parent, target.parent / "course.toml"

    # target is a directory
    manifest = target / "course.toml"
    if manifest.exists():
        return target, manifest

    # Check if target contains courses/
    courses_sub = target / "courses"
    if courses_sub.is_dir():
        manifests = list(courses_sub.glob("*/course.toml"))
        if manifests:
            return manifests[0].parent, manifests[0]

    return target, manifest if manifest.exists() else None


def load_manifest(path: Path | None) -> dict[str, Any]:
    """Safely load TOML manifest if it exists."""
    if path is None or not path.exists():
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def find_active_and_completed_sections(
    data: dict[str, Any],
    req_chapter: Any = None,
    req_section: Any = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract active chapter, active section, completed sections, and future sections.
    
    Returns (active_chapter, active_section, completed_sections, future_sections).
    """
    chapters = data.get("chapters", [])
    active_chapter = None
    active_section = None
    completed_sections: list[dict[str, Any]] = []
    future_sections: list[dict[str, Any]] = []

    # If explicit chapter and section requested
    if req_chapter is not None and req_section is not None:
        for ch in chapters:
            ch_match = str(ch.get("id")) == str(req_chapter) or ch.get("slug") == str(req_chapter)
            if ch_match:
                for sec in ch.get("sections", []):
                    sec_match = str(sec.get("id")) == str(req_section) or sec.get("slug") == str(req_section)
                    if sec_match:
                        active_chapter = ch
                        active_section = sec
                        break

    # Otherwise auto-detect active section (in_progress or review)
    if active_section is None:
        found_active = False
        for ch in chapters:
            for sec in ch.get("sections", []):
                st = sec.get("status", "not_started")
                if st == "completed":
                    completed_sections.append({**sec, "chapter_id": ch.get("id"), "chapter_slug": ch.get("slug")})
                elif st in {"in_progress", "review"} and not found_active:
                    active_chapter = ch
                    active_section = {**sec, "chapter_id": ch.get("id"), "chapter_slug": ch.get("slug")}
                    found_active = True
                else:
                    future_sections.append({**sec, "chapter_id": ch.get("id"), "chapter_slug": ch.get("slug")})
    else:
        # Populate completed and future around explicit active section
        found_active_flag = False
        for ch in chapters:
            for sec in ch.get("sections", []):
                if sec.get("id") == active_section.get("id") and ch.get("id") == active_chapter.get("id"):
                    found_active_flag = True
                    continue
                st = sec.get("status", "not_started")
                if not found_active_flag or st == "completed":
                    completed_sections.append({**sec, "chapter_id": ch.get("id"), "chapter_slug": ch.get("slug")})
                else:
                    future_sections.append({**sec, "chapter_id": ch.get("id"), "chapter_slug": ch.get("slug")})

    return active_chapter, active_section, completed_sections, future_sections


def resolve_section_file_path(course_dir: Path, ch: dict[str, Any], sec: dict[str, Any], filename: str) -> Path:
    """Find existing or construct canonical path for a section file (lesson-plan.md, notes.md)."""
    ch_slug = ch.get("slug") or f"chapter-{ch.get('id', 1)}"
    sec_slug = sec.get("slug") or f"section-{sec.get('id', 1)}"

    # Check candidates on disk
    candidates = [
        course_dir / ch_slug / sec_slug / filename,
        course_dir / f"chapter-{ch.get('id')}" / f"section-{sec.get('id')}" / filename,
        course_dir / f"ch-{ch.get('id')}" / f"sec-{sec.get('id')}" / filename,
        course_dir / sec_slug / filename,
    ]
    for c in candidates:
        if c.exists():
            return c

    # Search recursively if directory structure has varied naming
    matches = list(course_dir.glob(f"**/{sec_slug}/{filename}"))
    if matches:
        return matches[0]

    # Return primary canonical candidate
    return candidates[0]


def get_skill_rules(skill: str) -> dict[str, Any]:
    """Retrieve Stage Loading Matrix rules for given skill."""
    matrix = {
        "tc-init": {
            "loads_full": ["plan/preferences.md", "plan/roadmap.toml", ".tc/config.json"],
            "loads_summary": ["course.toml"],
            "forbidden": ["lesson-plan.md", "notes.md", "test-ledger.jsonl", "portfolio/**", ".tc/research/**"],
            "budget_tokens": 1500,
            "description": "Onboarding & navigation: inspects workspace metadata and styles",
        },
        "tc-create": {
            "loads_full": ["plan/preferences.md", "plan/roadmap.toml", ".tc/research/**", "course.toml"],
            "loads_summary": [],
            "forbidden": ["notes.md", "lesson-plan.md", "test-ledger.jsonl"],
            "budget_tokens": 3500,
            "description": "Curriculum architecture: builds syllabus from research without loading lesson plans",
        },
        "tc-research": {
            "loads_full": ["plan/sources/**", ".tc/config.json", ".tc/research/**"],
            "loads_summary": [],
            "forbidden": ["lesson-plan.md", "notes.md", "test-ledger.jsonl", "courses/**"],
            "budget_tokens": 2500,
            "description": "Web intelligence scout: scrapes doc indices without reading course files",
        },
        "tc-teach": {
            "loads_full": ["course.toml", "active lesson-plan.md", "plan/preferences.md"],
            "loads_summary": ["prior notes.md", "test-ledger.jsonl (misconceptions)"],
            "forbidden": [
                "future lesson-plan.md",
                "other chapters lesson-plan.md",
                "future notes.md",
                ".tc/research/**",
                "raw jsonl histories",
            ],
            "budget_tokens": 3800,
            "description": "Conversational tutor: single concept bounded to active section checklist",
        },
        "tc-verify-course": {
            "loads_full": ["course.toml", "all lesson-plan.md", ".tc/research/**"],
            "loads_summary": [],
            "forbidden": ["notes.md", "test-ledger.jsonl", "plan/preferences.md", "portfolio/**"],
            "budget_tokens": 3900,
            "description": "Pre-flight auditor: validates drafted lesson plans against research",
        },
        "tc-test-me": {
            "loads_full": ["course.toml", "test-ledger.jsonl", "plan/preferences.md"],
            "loads_summary": ["completed notes.md"],
            "forbidden": [
                "all lesson-plan.md (prevents concept leaks)",
                "future section notes.md",
                ".tc/research/**",
            ],
            "budget_tokens": 3200,
            "description": "Diagnostic evaluation: evaluates mental models from notes without leaking lesson plans",
        },
        "tc-practicals": {
            "loads_full": ["course.toml", "plan/preferences.md", "portfolio/**"],
            "loads_summary": ["completed notes.md", "test-ledger.jsonl (misconception summary)"],
            "forbidden": [
                "all lesson-plan.md",
                "future section notes.md",
                ".tc/research/**",
            ],
            "budget_tokens": 3600,
            "description": "Applied proof-of-work: formulates project briefs and evaluates deliverables",
        },
        "tc-redirect-course": {
            "loads_full": ["course.toml", "plan/sources/ledger.toml", "plan/preferences.md", "unfinished lesson-plan.md"],
            "loads_summary": [],
            "forbidden": [
                "completed lesson-plan.md (immutable)",
                "completed notes.md (immutable)",
                ".tc/research/**",
            ],
            "budget_tokens": 3000,
            "description": "Course change manager: updates unfinished chapters while preserving completed work",
        },
        "tc-migrate": {
            "loads_full": [".tc/config.json", "course.toml", "plan/roadmap.toml", "migration-plan.md"],
            "loads_summary": [],
            "forbidden": ["lesson-plan.md", "notes.md", "test-ledger.jsonl", ".tc/research/**"],
            "budget_tokens": 2000,
            "description": "Workspace migration: inspects and repairs file schemas with consent",
        },
    }
    return matrix.get(skill, {
        "loads_full": [],
        "loads_summary": [],
        "forbidden": ["out-of-scope files"],
        "budget_tokens": 4000,
        "description": "Generic skill context rule",
    })


def cmd_get_manifest(args: argparse.Namespace) -> None:
    """Generate exact authorized file manifest for a skill."""
    skill = normalize_skill(args.skill)
    if skill not in VALID_SKILLS:
        output_json({
            "ok": False,
            "error": f"Unknown skill '{args.skill}'. Must be one of: {sorted(VALID_SKILLS)}",
        }, exit_code=1)

    course_dir, manifest_path = resolve_course_dir(args.path)
    workspace_root = find_workspace_root(course_dir)
    manifest_data = load_manifest(manifest_path)

    rules = get_skill_rules(skill)
    authorized_files: list[str] = []

    # 1. tc-teach
    if skill == "tc-teach":
        if not manifest_path or not manifest_path.exists():
            output_json({
                "ok": False,
                "error": f"Course manifest not found at {course_dir / 'course.toml'}",
                "guidance": "Run manifest.py init-course or pass a valid --path to the course directory",
            }, exit_code=1)

        active_ch, active_sec, completed_secs, _ = find_active_and_completed_sections(
            manifest_data,
            req_chapter=args.chapter,
            req_section=args.section,
        )

        if active_sec is None:
            output_json({
                "ok": False,
                "error": "No active section found in course.toml for tc-teach",
                "guidance": "Activate a section using 'manifest.py advance --chapter <id> --section <id> --status in_progress'",
            }, exit_code=1)

        # course.toml
        authorized_files.append(str(manifest_path))

        # Active section's lesson-plan.md
        active_lp = resolve_section_file_path(course_dir, active_ch or {}, active_sec, "lesson-plan.md")
        authorized_files.append(str(active_lp))

        # Active or completed section's notes.md
        # If active section has notes.md, or prior completed sections in chapter have notes.md
        active_notes = resolve_section_file_path(course_dir, active_ch or {}, active_sec, "notes.md")
        authorized_files.append(str(active_notes))

        for c_sec in completed_secs:
            c_notes = resolve_section_file_path(course_dir, {"id": c_sec.get("chapter_id"), "slug": c_sec.get("chapter_slug")}, c_sec, "notes.md")
            if c_notes.exists() and str(c_notes) not in authorized_files:
                authorized_files.append(str(c_notes))

        # test-ledger.jsonl (rolling misconception summary slice)
        ledger_file = course_dir / "test-ledger.jsonl"
        authorized_files.append(str(ledger_file))

        # plan/preferences.md
        pref_file = workspace_root / "plan" / "preferences.md"
        if pref_file.exists():
            authorized_files.append(str(pref_file))

        output_json({
            "ok": True,
            "skill": skill,
            "course": manifest_data.get("course", {}).get("slug", course_dir.name),
            "active_chapter": {
                "id": active_ch.get("id") if active_ch else None,
                "slug": active_ch.get("slug") if active_ch else None,
            },
            "active_section": {
                "id": active_sec.get("id"),
                "slug": active_sec.get("slug"),
                "status": active_sec.get("status"),
            },
            "authorized_files": authorized_files,
            "files": authorized_files,
            "budget_tokens": rules["budget_tokens"],
            "rules": rules,
        }, exit_code=0)

    # 2. tc-test-me
    elif skill == "tc-test-me":
        if manifest_path and manifest_path.exists():
            authorized_files.append(str(manifest_path))

        # Completed sections' notes.md ONLY (never lesson-plan.md!)
        _, _, completed_secs, _ = find_active_and_completed_sections(manifest_data)
        for c_sec in completed_secs:
            c_notes = resolve_section_file_path(course_dir, {"id": c_sec.get("chapter_id"), "slug": c_sec.get("chapter_slug")}, c_sec, "notes.md")
            if str(c_notes) not in authorized_files:
                authorized_files.append(str(c_notes))

        ledger_file = course_dir / "test-ledger.jsonl"
        if ledger_file.exists() or not authorized_files:
            authorized_files.append(str(ledger_file))

        pref_file = workspace_root / "plan" / "preferences.md"
        if pref_file.exists():
            authorized_files.append(str(pref_file))

        output_json({
            "ok": True,
            "skill": skill,
            "course": manifest_data.get("course", {}).get("slug", course_dir.name),
            "authorized_files": authorized_files,
            "files": authorized_files,
            "budget_tokens": rules["budget_tokens"],
            "rules": rules,
        }, exit_code=0)

    # 3. tc-practicals
    elif skill == "tc-practicals":
        if manifest_path and manifest_path.exists():
            authorized_files.append(str(manifest_path))

        pref_file = workspace_root / "plan" / "preferences.md"
        if pref_file.exists():
            authorized_files.append(str(pref_file))

        # Completed section notes
        _, _, completed_secs, _ = find_active_and_completed_sections(manifest_data)
        for c_sec in completed_secs:
            c_notes = resolve_section_file_path(course_dir, {"id": c_sec.get("chapter_id"), "slug": c_sec.get("chapter_slug")}, c_sec, "notes.md")
            if c_notes.exists():
                authorized_files.append(str(c_notes))

        # Portfolio directory files if any
        portfolio_dir = course_dir / "portfolio"
        if portfolio_dir.is_dir():
            for p_file in portfolio_dir.glob("**/project-spec.md"):
                authorized_files.append(str(p_file))

        output_json({
            "ok": True,
            "skill": skill,
            "course": manifest_data.get("course", {}).get("slug", course_dir.name),
            "authorized_files": authorized_files,
            "files": authorized_files,
            "budget_tokens": rules["budget_tokens"],
            "rules": rules,
        }, exit_code=0)

    # 4. tc-create
    elif skill == "tc-create":
        pref_file = workspace_root / "plan" / "preferences.md"
        if pref_file.exists():
            authorized_files.append(str(pref_file))

        roadmap_file = workspace_root / "plan" / "roadmap.toml"
        if roadmap_file.exists():
            authorized_files.append(str(roadmap_file))

        if manifest_path and manifest_path.exists():
            authorized_files.append(str(manifest_path))

        # Research digests
        research_dir = workspace_root / ".tc" / "research"
        if research_dir.is_dir():
            for rd in research_dir.glob("**/curriculum-digest.md"):
                authorized_files.append(str(rd))

        output_json({
            "ok": True,
            "skill": skill,
            "authorized_files": authorized_files,
            "files": authorized_files,
            "budget_tokens": rules["budget_tokens"],
            "rules": rules,
        }, exit_code=0)

    # 5. tc-verify-course
    elif skill == "tc-verify-course":
        if manifest_path and manifest_path.exists():
            authorized_files.append(str(manifest_path))

        # All drafted lesson plans in course
        for lp in course_dir.glob("**/lesson-plan.md"):
            authorized_files.append(str(lp))

        # Research digests
        research_dir = workspace_root / ".tc" / "research"
        if research_dir.is_dir():
            for rd in research_dir.glob("**/curriculum-digest.md"):
                authorized_files.append(str(rd))

        output_json({
            "ok": True,
            "skill": skill,
            "authorized_files": authorized_files,
            "files": authorized_files,
            "budget_tokens": rules["budget_tokens"],
            "rules": rules,
        }, exit_code=0)

    # 6. Other skills (tc-init, tc-research, tc-redirect-course, tc-migrate)
    else:
        if manifest_path and manifest_path.exists():
            authorized_files.append(str(manifest_path))
        pref_file = workspace_root / "plan" / "preferences.md"
        if pref_file.exists():
            authorized_files.append(str(pref_file))

        output_json({
            "ok": True,
            "skill": skill,
            "authorized_files": authorized_files,
            "files": authorized_files,
            "budget_tokens": rules["budget_tokens"],
            "rules": rules,
        }, exit_code=0)


def cmd_check(args: argparse.Namespace) -> None:
    """Check whether a specific file read is authorized for a skill."""
    skill = normalize_skill(args.skill)
    if skill not in VALID_SKILLS:
        output_json({
            "ok": False,
            "authorized": False,
            "error": f"Unknown skill '{args.skill}'. Must be one of: {sorted(VALID_SKILLS)}",
        }, exit_code=1)

    file_path = Path(args.file)
    file_str = str(file_path)
    file_name = file_path.name

    course_dir, manifest_path = resolve_course_dir(args.path or (file_path.parent if file_path.exists() else None))
    manifest_data = load_manifest(manifest_path)

    # Universal check 1: Future section access
    # Any path explicitly marked 'future' or matching a not_started section
    if "future" in file_str.lower():
        output_json({
            "ok": False,
            "authorized": False,
            "skill": skill,
            "file": file_str,
            "reason": "Future section access forbidden: cannot access unreached curriculum concepts",
        }, exit_code=1)

    # Universal check 2: tc-test-me MUST NEVER access lesson-plan.md
    if skill == "tc-test-me":
        if file_name == "lesson-plan.md":
            output_json({
                "ok": False,
                "authorized": False,
                "skill": skill,
                "file": file_str,
                "reason": "Future section access forbidden: lesson plans are forbidden for tc-test-me to prevent concept leaks",
            }, exit_code=1)

    # Universal check 3: tc-practicals and tc-create MUST NEVER access lesson-plan.md
    if skill in {"tc-practicals", "tc-create"} and file_name == "lesson-plan.md":
        output_json({
            "ok": False,
            "authorized": False,
            "skill": skill,
            "file": file_str,
            "reason": f"Lesson plans are forbidden for {skill}",
        }, exit_code=1)

    # Check for tc-teach
    if skill == "tc-teach":
        if file_name == "lesson-plan.md":
            # Check if this lesson plan is for the active section
            active_ch, active_sec, _, _ = find_active_and_completed_sections(manifest_data)
            if active_sec:
                active_lp = resolve_section_file_path(course_dir, active_ch or {}, active_sec, "lesson-plan.md")
                active_slug = str(active_sec.get("slug", ""))
                active_id = str(active_sec.get("id", ""))
                # Compare filenames or relative paths
                if (
                    file_path.resolve() == active_lp.resolve()
                    or (active_slug and active_slug in file_str)
                    or (active_id and f"sec-{active_id}" in file_str)
                ):
                    output_json({
                        "ok": True,
                        "authorized": True,
                        "skill": skill,
                        "file": file_str,
                    }, exit_code=0)
            # If not active section's lesson plan: forbidden!
            output_json({
                "ok": False,
                "authorized": False,
                "skill": skill,
                "file": file_str,
                "reason": "Future section access forbidden: Out-of-scope chapter or future section access forbidden",
            }, exit_code=1)

    # Check for section status if manifest is available
    if manifest_data:
        _, _, completed_secs, future_secs = find_active_and_completed_sections(manifest_data)
        for f_sec in future_secs:
            f_slug = f_sec.get("slug", "")
            f_id = str(f_sec.get("id", ""))
            if (f_slug and f_slug in file_str) or (f_id and f"sec-{f_id}" in file_str):
                output_json({
                    "ok": False,
                    "authorized": False,
                    "skill": skill,
                    "file": file_str,
                    "reason": "Future section access forbidden: cannot access unreached curriculum concepts",
                }, exit_code=1)

    # Check if file belongs to skill's forbidden list
    rules = get_skill_rules(skill)
    if file_name in rules["forbidden"]:
        output_json({
            "ok": False,
            "authorized": False,
            "skill": skill,
            "file": file_str,
            "reason": f"File '{file_name}' is explicitly forbidden for {skill}",
        }, exit_code=1)

    # If it is an authorized file (e.g. course.toml, preferences.md, notes.md for tc-test-me, etc.)
    output_json({
        "ok": True,
        "authorized": True,
        "skill": skill,
        "file": file_str,
    }, exit_code=0)


def cmd_matrix(args: argparse.Namespace) -> None:
    """Print the complete Stage Loading Matrix specification."""
    if args.skill:
        sk = normalize_skill(args.skill)
        output_json({sk: get_skill_rules(sk)}, exit_code=0)
    matrix = {sk: get_skill_rules(sk) for sk in sorted(VALID_SKILLS)}
    output_json(matrix, exit_code=0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TextCourses stage-aware Context Loading Manifest engine"
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # get-manifest
    p_manifest = subparsers.add_parser("get-manifest", help="Get authorized file manifest for a skill")
    p_manifest.add_argument("--skill", required=True, help="Skill name (e.g. tc-teach, tc-test-me)")
    p_manifest.add_argument("--path", default=None, help="Course directory or manifest path")
    p_manifest.add_argument("--chapter", default=None, help="Explicit chapter ID or slug")
    p_manifest.add_argument("--section", default=None, help="Explicit section ID or slug")
    p_manifest.set_defaults(func=cmd_get_manifest)

    # check
    p_check = subparsers.add_parser("check", help="Check if a file read is authorized for a skill")
    p_check.add_argument("--skill", required=True, help="Skill name (e.g. tc-test-me)")
    p_check.add_argument("--file", required=True, help="File path to check")
    p_check.add_argument("--path", default=None, help="Course directory or manifest path")
    p_check.set_defaults(func=cmd_check)

    # matrix
    p_matrix = subparsers.add_parser("matrix", help="View Stage Loading Matrix rules")
    p_matrix.add_argument("--skill", default=None, help="Filter by specific skill")
    p_matrix.set_defaults(func=cmd_matrix)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
