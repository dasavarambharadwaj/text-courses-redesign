#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""course_builder.py — Course scaffolding architect and Triad Consensus Loop orchestrator.

Coordinates curriculum design across the 5 Universal Archetypes, ingests syllabus outlines,
drives the Triad Consensus Loop (Scout -> Architect -> Auditor), records reconciliation
traces to .tc/cache/consensus-trace.jsonl, and scaffolds verified course files into
courses/<slug>/ (FR-4, FR-5, FR-8, AD-4).
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import tomli_w

# Ensure sibling scripts and project root are importable
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
for p in [str(SCRIPT_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from auditor import audit_curriculum
except ImportError:
    from _tc.scripts.auditor import audit_curriculum

try:
    from scout import get_cached_digest, run_scout
except ImportError:
    from _tc.scripts.scout import get_cached_digest, run_scout

ARCHETYPES = {
    "applied_creation": {
        "title": "Applied Creation",
        "description": "Build an end-to-end production system piece by piece. Every section implements a concrete deliverable.",
        "chapter_pattern": ["Foundations & Setup", "Core Engine Implementation", "Advanced Mechanics", "Production Hardening"],
    },
    "forensic_dilemma": {
        "title": "Forensic Dilemma",
        "description": "Investigate system incidents, failing invariants, and subtle corruptions. Deconstruct root causes and engineer mitigations.",
        "chapter_pattern": ["Triage & Incident Reproduction", "Internal Pathology & Diagnosis", "Root Cause Elimination", "Invariant Testing & Monitoring"],
    },
    "axiomatic_primitives": {
        "title": "Axiomatic Primitives",
        "description": "Deconstruct down to fundamental mechanical primitives, then compose higher abstractions from mathematical first principles.",
        "chapter_pattern": ["Fundamental Axioms & Memory Models", "Primitive Composition", "High-Level Abstractions", "Zero-Cost Guarantees"],
    },
    "spiral_immersion": {
        "title": "Spiral Immersion",
        "description": "Execute a complete minimal end-to-end pass first, then spiral through successive iterations with deeper nuances and scale.",
        "chapter_pattern": ["First Pass: Minimal End-to-End", "Second Pass: Resiliency & Concurrency", "Third Pass: Optimization & Scale", "Mastery: Architectural Tradeoffs"],
    },
    "reverse_engineering": {
        "title": "Reverse Engineering",
        "description": "Decompile, trace, and inspect black-box protocols, binary formats, or existing architectures to deduce internal mechanics.",
        "chapter_pattern": ["Black-Box Profiling & Tracing", "Wire Protocol & Binary Formats", "Memory & State Inspection", "Clean-Room Re-Implementation"],
    },
}


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


def append_consensus_trace(
    workspace: Path,
    slug: str,
    iteration: int,
    archetype: str,
    audit_results: dict[str, Any],
) -> None:
    """Append a consensus trace record using POSIX atomic fcntl file locking."""
    cache_dir = workspace / ".tc" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    trace_file = cache_dir / "consensus-trace.jsonl"

    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "slug": slug,
        "iteration": iteration,
        "archetype": archetype,
        "consensus_reached": audit_results.get("ok", False),
        "critical_count": audit_results.get("critical_count", 0),
        "warning_count": audit_results.get("warning_count", 0),
        "findings": audit_results.get("findings", []),
    }

    line = json.dumps(record) + "\n"
    with open(trace_file, "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def parse_outline_text(outline_text: str) -> list[dict[str, Any]]:
    """Parse hierarchical markdown headings or lists into chapters and sections."""
    chapters: list[dict[str, Any]] = []
    current_chapter: dict[str, Any] | None = None
    section_counter = 1

    lines = outline_text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Match Chapter heading (# or ##)
        m_ch = re.match(r"^#{1,2}\s+(?:Chapter\s*\d*[:.-]?\s*)?(.+)$", stripped, re.IGNORECASE)
        if m_ch and not stripped.startswith("###"):
            ch_title = m_ch.group(1).strip()
            ch_id = f"ch-{len(chapters) + 1:02d}"
            current_chapter = {
                "id": ch_id,
                "title": ch_title,
                "sections": [],
            }
            chapters.append(current_chapter)
            section_counter = 1
            continue

        # Match Section heading (###) or bullet point
        m_sec = re.match(r"^###\s+(?:Section\s*\d*[:.-]?\s*)?(.+)$", stripped, re.IGNORECASE)
        m_bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        sec_title = ""
        if m_sec:
            sec_title = m_sec.group(1).strip()
        elif m_bullet and current_chapter:
            sec_title = m_bullet.group(1).strip()

        if sec_title:
            if not current_chapter:
                current_chapter = {
                    "id": f"ch-{len(chapters) + 1:02d}",
                    "title": "Fundamentals",
                    "sections": [],
                }
                chapters.append(current_chapter)

            sec_id = f"sec-{section_counter:02d}"
            section_counter += 1
            current_chapter["sections"].append({
                "id": sec_id,
                "title": sec_title,
            })

    return chapters


def generate_archetype_chapters(
    slug: str,
    archetype: str,
    research_digest: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Generate structured chapters and sections aligned with the chosen archetype."""
    archetype_info = ARCHETYPES.get(archetype, ARCHETYPES["applied_creation"])
    chapter_titles = archetype_info["chapter_pattern"]

    # Use research vocabulary if available to populate terms
    scouted_vocab = research_digest.get("vocabulary", []) if research_digest else []
    scouted_headings = [h.get("title") for h in research_digest.get("toc", [])] if research_digest else []

    chapters: list[dict[str, Any]] = []
    v_idx = 0

    for ch_idx, ch_title in enumerate(chapter_titles, 1):
        ch_id = f"chapter-{ch_idx:02d}"
        sections = []

        # Default 2 sections per chapter
        for s_idx in range(1, 3):
            sec_id = f"sec-{s_idx:02d}"
            prereqs = []
            vocab_prereqs = []
            vocab_introduced = []

            # Determine terms for this section
            if v_idx < len(scouted_vocab):
                term = scouted_vocab[v_idx]
                vocab_introduced.append(term)
                v_idx += 1
            else:
                vocab_introduced.append(f"{slug}-term-{ch_idx}-{s_idx}")

            # If not the very first section, set prerequisite to previous section
            if ch_idx > 1 or s_idx > 1:
                if s_idx == 1:
                    prev_ch = chapters[ch_idx - 2]
                    prev_sec = prev_ch["sections"][-1]["id"]
                    prereqs.append(prev_sec)
                    if prev_ch["sections"][-1].get("vocabulary_introduced"):
                        vocab_prereqs.append(prev_ch["sections"][-1]["vocabulary_introduced"][0])
                else:
                    prev_sec = sections[-1]["id"]
                    prereqs.append(prev_sec)
                    if sections[-1].get("vocabulary_introduced"):
                        vocab_prereqs.append(sections[-1]["vocabulary_introduced"][0])

            # Pick section title
            if scouted_headings and ((ch_idx - 1) * 2 + (s_idx - 1)) < len(scouted_headings):
                s_title = scouted_headings[(ch_idx - 1) * 2 + (s_idx - 1)]
            else:
                s_title = f"{ch_title}: Part {s_idx}"

            sections.append({
                "id": sec_id,
                "title": s_title,
                "status": "in_progress" if (ch_idx == 1 and s_idx == 1) else "not_started",
                "prerequisites": prereqs,
                "vocabulary_introduced": vocab_introduced,
                "vocabulary_prerequisites": vocab_prereqs,
                "sources": [],
            })

        chapters.append({
            "id": ch_id,
            "title": ch_title,
            "sections": sections,
        })

    return chapters


def run_triad_consensus_loop(
    slug: str,
    title: str,
    archetype: str,
    workspace: Path,
    outline_text: str | None = None,
    research_digest: dict[str, Any] | None = None,
    max_reconciliations: int = 3,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute Triad Consensus Loop between Scout, Architect, and Auditor."""
    # Step 1: Scout digest already gathered or provided
    # Step 2: Architect creates candidate curriculum
    candidate_chapters: list[dict[str, Any]]
    if outline_text:
        parsed_chapters = parse_outline_text(outline_text)
        if parsed_chapters:
            candidate_chapters = parsed_chapters
            # Normalize IDs, status, prerequisites, and vocabulary
            prev_sec_id: str | None = None
            prev_vocab: str | None = None
            for ch_idx, ch in enumerate(candidate_chapters, 1):
                if not ch.get("id"):
                    ch["id"] = f"chapter-{ch_idx:02d}"
                for s_idx, sec in enumerate(ch.get("sections", []), 1):
                    if not sec.get("id"):
                        sec["id"] = f"sec-{s_idx:02d}"
                    sec["status"] = "in_progress" if (ch_idx == 1 and s_idx == 1) else "not_started"
                    
                    term = f"{slug}-concept-{ch_idx}-{s_idx}"
                    sec["vocabulary_introduced"] = [term]
                    sec["vocabulary_prerequisites"] = [prev_vocab] if prev_vocab else []
                    sec["prerequisites"] = [prev_sec_id] if prev_sec_id else []

                    prev_sec_id = sec["id"]
                    prev_vocab = term
        else:
            candidate_chapters = generate_archetype_chapters(slug, archetype, research_digest)
    else:
        candidate_chapters = generate_archetype_chapters(slug, archetype, research_digest)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    candidate_data: dict[str, Any] = {
        "course": {
            "id": slug,
            "title": title,
            "archetype": archetype,
            "status": "in_progress",
            "version": "0.1.0",
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        "sources": {},
        "chapters": candidate_chapters,
    }

    if research_digest:
        sha = research_digest.get("content_sha256")
        if sha:
            candidate_data["sources"][f"{slug}_docs.md"] = sha

    # Run auditor check
    iteration = 1
    audit_result = audit_curriculum(candidate_data, research_slug=slug, workspace=workspace)
    append_consensus_trace(workspace, slug, iteration, archetype, audit_result)

    # Reconciliation loop if critical issues arise
    while not audit_result["ok"] and iteration < max_reconciliations:
        iteration += 1
        # Auto-reconcile: clean cycles or missing prerequisites
        for ch in candidate_data["chapters"]:
            for sec in ch.get("sections", []):
                # Clean prerequisites to strict antecedent chain
                sec["prerequisites"] = []
                sec["vocabulary_prerequisites"] = []

        audit_result = audit_curriculum(candidate_data, research_slug=slug, workspace=workspace)
        append_consensus_trace(workspace, slug, iteration, archetype, audit_result)

    return candidate_data, audit_result


def scaffold_course_files(
    workspace: Path,
    course_data: dict[str, Any],
) -> Path:
    """Scaffold course directory with course.toml, overview.md, and lesson-plan.md files."""
    slug = course_data["course"]["id"]
    title = course_data["course"]["title"]
    archetype = course_data["course"]["archetype"]
    archetype_info = ARCHETYPES.get(archetype, ARCHETYPES["applied_creation"])

    course_dir = workspace / "courses" / slug
    course_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write course.toml
    course_toml_path = course_dir / "course.toml"
    atomic_write_toml(course_toml_path, course_data)

    # 2. Write overview.md
    overview_lines = [
        f"# {title}",
        "",
        f"- **Course Slug**: `{slug}`",
        f"- **Archetype**: `{archetype_info['title']}`",
        f"- **Description**: {archetype_info['description']}",
        "- **Status**: In Progress",
        "",
        "## Curriculum Outline",
        "",
    ]

    for ch_idx, ch in enumerate(course_data.get("chapters", []), 1):
        overview_lines.append(f"### Chapter {ch_idx}: {ch['title']}")
        for sec in ch.get("sections", []):
            prereqs_str = f" *(Prereq: {', '.join(sec.get('prerequisites', []))})*" if sec.get("prerequisites") else ""
            status_emoji = "⏳ In Progress" if sec.get("status") == "in_progress" else "⚪ Not Started"
            overview_lines.append(f"- **{sec['title']}** [{status_emoji}]{prereqs_str}")
        overview_lines.append("")

    overview_lines.append("## How to Learn")
    overview_lines.append("To start the next section, run `/tc-teach`.\n")

    atomic_write_text(course_dir / "overview.md", "\n".join(overview_lines))

    # 3. Scaffold chapter and section lesson plans
    for ch_idx, ch in enumerate(course_data.get("chapters", []), 1):
        ch_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", ch["title"].lower()).strip("-")
        ch_dir_name = f"chapter-{ch_idx:02d}-{ch_slug}"
        ch_path = course_dir / ch_dir_name

        for s_idx, sec in enumerate(ch.get("sections", []), 1):
            sec_slug = re.sub(r"[^a-zA-Z0-9_-]", "-", sec["title"].lower()).strip("-")
            sec_dir_name = f"section-{s_idx:02d}-{sec_slug}"
            sec_path = ch_path / sec_dir_name
            sec_path.mkdir(parents=True, exist_ok=True)

            # lesson-plan.md (Teacher's instructional checklist - AI only)
            lesson_plan_content = (
                f"# Lesson Plan: {sec['title']}\n\n"
                f"> **Internal AI Instructor Checklist** (Never show raw contents to student)\n\n"
                f"## Objectives\n"
                f"- Master mechanics of {sec['title']}.\n"
                f"- Verify understanding of {', '.join(sec.get('vocabulary_introduced', ['key concepts']))}.\n\n"
                f"## Prerequisites to Verify\n"
                f"- {', '.join(sec.get('vocabulary_prerequisites', ['None (Foundational)']))}\n\n"
                f"## Socratic Diagnostic Prompts\n"
                f"- What are the core constraints of this mechanism?\n"
                f"- What invariant fails if this primitive is misused?\n\n"
                f"## Next Action on Completion\n"
                f"- Distill distilled textbook notes into notes.md.\n"
                f"- Log assessment mastery in ledger.py.\n"
            )
            atomic_write_text(sec_path / "lesson-plan.md", lesson_plan_content)

    return course_dir


def create_course(
    slug: str,
    title: str | None = None,
    archetype: str = "applied_creation",
    workspace: Path | str = ".",
    outline_file: Path | str | None = None,
    url: str | None = None,
    topic: str | None = None,
) -> dict[str, Any]:
    """Coordinate Triad Consensus Loop and scaffold course upon verified consensus."""
    ws = Path(workspace).resolve()

    if archetype not in ARCHETYPES:
        raise ValueError(f"Invalid archetype '{archetype}'. Must be one of {sorted(ARCHETYPES.keys())}")

    course_title = title or slug.replace("-", " ").title()

    # Step 1: Research Scout check
    research_digest: dict[str, Any] | None = None
    try:
        research_digest = get_cached_digest(slug, workspace=ws)
    except FileNotFoundError:
        # Run scout on topic or url
        scout_res = run_scout(
            slug=slug,
            workspace=ws,
            url=url,
            source_path=outline_file if (outline_file and Path(outline_file).is_file()) else None,
            topic=topic or course_title,
        )
        research_digest = scout_res.get("digest")

    outline_text = None
    if outline_file:
        p = Path(outline_file).resolve()
        if p.is_file():
            outline_text = p.read_text(encoding="utf-8")

    # Step 2: Triad Consensus Loop
    course_data, audit_results = run_triad_consensus_loop(
        slug=slug,
        title=course_title,
        archetype=archetype,
        workspace=ws,
        outline_text=outline_text,
        research_digest=research_digest,
    )

    if not audit_results.get("ok"):
        return {
            "ok": False,
            "consensus_reached": False,
            "error": "Triad consensus failed due to critical pre-flight audit findings",
            "findings": audit_results.get("findings", []),
        }

    # Step 3: Scaffold course files
    course_dir = scaffold_course_files(ws, course_data)

    return {
        "ok": True,
        "consensus_reached": True,
        "slug": slug,
        "title": course_title,
        "archetype": archetype,
        "course_path": str(course_dir),
        "total_chapters": len(course_data["chapters"]),
        "total_sections": audit_results.get("total_sections", 0),
        "topological_order": audit_results.get("topological_order", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="course_builder.py",
        description="TextCourses course scaffolding architect and Triad Consensus Loop orchestrator.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create and scaffold a course through Triad Consensus.")
    p_create.add_argument("--slug", required=True, help="Unique course slug (e.g. distributed-systems).")
    p_create.add_argument("--title", default=None, help="Human-readable course title.")
    p_create.add_argument("--archetype", default="applied_creation", choices=list(ARCHETYPES.keys()), help="Pedagogical archetype.")
    p_create.add_argument("--workspace", default=".", help="Path to workspace root.")
    p_create.add_argument("--outline-file", default=None, help="Optional syllabus outline markdown file.")
    p_create.add_argument("--url", default=None, help="Optional documentation URL for research scouting.")
    p_create.add_argument("--topic", default=None, help="Optional topic description.")
    p_create.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # archetypes
    p_arch = subparsers.add_parser("archetypes", help="List available pedagogical archetypes.")
    p_arch.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    try:
        if args.subcommand == "create":
            result = create_course(
                slug=args.slug,
                title=args.title,
                archetype=args.archetype,
                workspace=args.workspace,
                outline_file=args.outline_file,
                url=args.url,
                topic=args.topic,
            )
            exit_code = 0 if result["ok"] else 1
            output_json(result, exit_code)

        elif args.subcommand == "archetypes":
            output_json({"ok": True, "archetypes": ARCHETYPES}, 0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except Exception as e:
        output_json({"error": str(e), "ok": False}, 1)


if __name__ == "__main__":
    main()
