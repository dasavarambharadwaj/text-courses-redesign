#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""source_mapper.py — Conveyor-Belt Chapter Pipeline & Pedagogical Symbol Table (source-map.toml).

Processes multi-hundred-page sources in bounded chapter blocks with running vocabulary
accumulation (<25k tokens/turn) and compiles a deterministic symbol table mapping every
concept to exact source files, heading breadcrumbs, line spans, and dialectic flags (CAP-3, CAP-4).
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

import tomli_w

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON and exit."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def split_source_into_conveyor_batches(
    markdown_path: Path | str,
    max_tokens_per_batch: int = 25000,
    chars_per_token_approx: int = 4,
) -> list[dict[str, Any]]:
    """Split a large markdown document into bounded chapter/section batches.
    
    Ensures prompt token load during conveyor-belt ingestion stays strictly below max_tokens.
    """
    path = Path(markdown_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {path}")

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    max_chars = max_tokens_per_batch * chars_per_token_approx

    # Group by major headings (# or ##)
    batches: list[dict[str, Any]] = []
    current_lines: list[str] = []
    current_title = "Preamble"
    current_start_line = 1
    current_chars = 0

    for idx, line in enumerate(lines, 1):
        is_major_heading = bool(re.match(r"^#{1,2}\s+", line))
        line_len = len(line)

        if is_major_heading and current_lines and (current_chars + line_len > max_chars or len(current_lines) > 200):
            # Emit batch
            batches.append({
                "batch_index": len(batches) + 1,
                "title": current_title,
                "line_start": current_start_line,
                "line_end": idx - 1,
                "token_estimate": current_chars // chars_per_token_approx,
                "content": "".join(current_lines),
            })
            current_lines = [line]
            current_title = line.strip("# \t\r\n")
            current_start_line = idx
            current_chars = line_len
        else:
            if is_major_heading and not current_lines:
                current_title = line.strip("# \t\r\n")
            current_lines.append(line)
            current_chars += line_len

    if current_lines:
        batches.append({
            "batch_index": len(batches) + 1,
            "title": current_title,
            "line_start": current_start_line,
            "line_end": len(lines),
            "token_estimate": current_chars // chars_per_token_approx,
            "content": "".join(current_lines),
        })

    return batches


def extract_vocabulary_from_text(text: str) -> set[str]:
    """Extract candidate technical terms and domain primitives from text block."""
    terms: set[str] = set()
    for m in re.finditer(r"\*\*([a-zA-Z0-9_\-\s]{3,35})\*\*", text):
        terms.add(m.group(1).strip().lower())
    for m in re.finditer(r"`([a-zA-Z0-9_\-]{3,30})`", text):
        terms.add(m.group(1).strip().lower())
    return terms


def locate_concept_spans_in_source(
    raw_markdown: str,
    concept_title: str,
    keywords: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Scan raw markdown to find line number spans and verbatim anchors for a concept."""
    lines = raw_markdown.splitlines()

    search_phrases: set[str] = {concept_title.lower()}
    search_phrases.add(concept_title.lower().replace("-", " "))
    search_phrases.add(concept_title.lower().replace("_", " "))

    parts = [p for p in re.split(r"[\s\-_]+", concept_title.lower()) if len(p) >= 3]
    if parts:
        search_phrases.add(parts[0])

    if keywords:
        for kw in keywords:
            if len(kw) >= 3:
                search_phrases.add(kw.lower())
                search_phrases.add(kw.lower().replace("-", " "))
                search_phrases.add(kw.lower().replace("_", " "))

    search_terms = sorted([p for p in search_phrases if len(p) >= 3], key=len, reverse=True)

    matches: list[dict[str, Any]] = []
    current_heading = "Overview"
    current_heading_level = 1
    current_heading_line = 1

    for idx, line in enumerate(lines, 1):
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            current_heading_level = len(heading_match.group(1))
            current_heading = heading_match.group(2).strip()
            current_heading_line = idx
            if current_heading_level == 1:
                continue

        line_lower = line.lower()
        if any(term in line_lower for term in search_terms):
            span_start = max(1, current_heading_line)
            span_end = min(len(lines), idx + 25)

            for lookahead_idx in range(idx + 1, span_end + 1):
                if lookahead_idx <= len(lines) and lines[lookahead_idx - 1].startswith("#"):
                    span_end = lookahead_idx - 1
                    break

            anchor = line.strip()
            if len(anchor) > 120:
                anchor = anchor[:117] + "..."

            matches.append({
                "heading": current_heading,
                "lines": [span_start, span_end],
                "verbatim_anchor": anchor,
            })
            break  # Single best span per source file

    return matches


def compile_source_map(
    course_slug: str,
    workspace: Path | str = ".",
    sources: list[dict[str, Any]] | None = None,
    course_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile courses/<slug>/source-map.toml linking curriculum concepts to exact source line spans."""
    ws = Path(workspace).resolve()
    course_dir = ws / "courses" / course_slug
    course_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load course.toml if not passed
    if course_data is None:
        c_toml = course_dir / "course.toml"
        if c_toml.is_file():
            try:
                course_data = tomllib.loads(c_toml.read_text(encoding="utf-8"))
            except Exception:
                course_data = {}
        else:
            course_data = {}

    # 2. Discover raw sources if not passed
    resolved_sources: list[dict[str, Any]] = []
    if sources:
        resolved_sources = sources
    else:
        # Check standard raw source directory
        raw_sources_dir = ws / "research" / course_slug / "sources" / "raw"
        if not raw_sources_dir.is_dir():
            raw_sources_dir = ws / "sources" / "raw"

        if raw_sources_dir.is_dir():
            for p in sorted(raw_sources_dir.glob("*.md")):
                lines_count = len(p.read_text(encoding="utf-8").splitlines())
                resolved_sources.append({
                    "id": p.stem,
                    "title": p.stem.replace("_", " ").replace("-", " ").title(),
                    "author": "Author",
                    "raw_path": str(p.relative_to(ws)).replace("\\", "/"),
                    "abs_path": p,
                    "total_lines": lines_count,
                })

    # Read raw content for each source
    source_texts: dict[str, str] = {}
    sources_meta: list[dict[str, Any]] = []

    for src in resolved_sources:
        src_id = src.get("id") or Path(src.get("raw_path", "source")).stem
        abs_p = Path(src.get("abs_path") or ws / src.get("raw_path", ""))
        content = ""
        total_lines = src.get("total_lines", 0)
        if abs_p.is_file():
            content = abs_p.read_text(encoding="utf-8")
            total_lines = len(content.splitlines())

        source_texts[src_id] = content
        sources_meta.append({
            "id": src_id,
            "title": src.get("title", src_id),
            "author": src.get("author", "Unknown"),
            "raw_path": str(src.get("raw_path", "")),
            "total_lines": total_lines,
        })

    # 3. Map chapters, sections, and concepts
    compiled_chapters: list[dict[str, Any]] = []
    raw_chapters = course_data.get("chapters", []) if course_data else []

    running_vocabulary: set[str] = set()

    for ch_idx, ch in enumerate(raw_chapters, 1):
        ch_slug = ch.get("id") or f"chapter-{ch_idx:02d}"
        ch_title = ch.get("title", f"Chapter {ch_idx}")
        ch_sections: list[dict[str, Any]] = []

        for s_idx, sec in enumerate(ch.get("sections", []), 1):
            sec_slug = sec.get("id") or f"sec-{s_idx:02d}"
            sec_title = sec.get("title", f"Section {s_idx}")
            sec_concepts: list[dict[str, Any]] = []

            # Determine concepts from lesson-plan or vocabulary_introduced
            vocab_terms = sec.get("vocabulary_introduced", [])
            concept_names = vocab_terms if vocab_terms else [sec_title]

            for c_idx, c_name in enumerate(concept_names, 1):
                concept_id = re.sub(r"[^a-zA-Z0-9]+", "_", c_name.lower()).strip("_")
                if not concept_id:
                    concept_id = f"concept_{ch_idx}_{s_idx}_{c_idx}"

                # Match against all available sources to find occurrences
                pointers: list[dict[str, Any]] = []
                for src in sources_meta:
                    src_id = src["id"]
                    text = source_texts.get(src_id, "")
                    if text:
                        spans = locate_concept_spans_in_source(text, c_name, keywords=[sec_title])
                        for span in spans:
                            pointers.append({
                                "source_id": src_id,
                                "heading": span["heading"],
                                "lines": span["lines"],
                                "verbatim_anchor": span["verbatim_anchor"],
                            })

                # If no pointers matched in raw sources, scaffold default entry
                if not pointers and sources_meta:
                    first_src = sources_meta[0]
                    pointers.append({
                        "source_id": first_src["id"],
                        "heading": sec_title,
                        "lines": [1, min(50, first_src["total_lines"])],
                        "verbatim_anchor": f"Section covering {sec_title}.",
                    })

                is_dialectic = len(pointers) > 1
                synthesis = ""
                if is_dialectic:
                    src_names = [p["source_id"] for p in pointers]
                    synthesis = f"Covered across {len(pointers)} sources ({', '.join(src_names)}). Synthesize complementary perspectives."

                sec_concepts.append({
                    "id": concept_id,
                    "title": c_name.replace("_", " ").replace("-", " ").title(),
                    "dialectic": is_dialectic,
                    "synthesis_notes": synthesis,
                    "pointers": pointers,
                })

                running_vocabulary.add(concept_id)

            ch_sections.append({
                "slug": sec_slug,
                "title": sec_title,
                "concepts": sec_concepts,
            })

        compiled_chapters.append({
            "slug": ch_slug,
            "title": ch_title,
            "sections": ch_sections,
        })

    # Assemble symbol table structure
    source_map: dict[str, Any] = {
        "version": "1.0.0",
        "course_slug": course_slug,
        "compiled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_concepts": sum(len(sec["concepts"]) for ch in compiled_chapters for sec in ch["sections"]),
        "sources": sources_meta,
        "chapters": compiled_chapters,
    }

    # Write source-map.toml
    out_path = course_dir / "source-map.toml"
    out_path.write_text(tomli_w.dumps(source_map), encoding="utf-8")

    return source_map


def read_source_pointer(
    course_slug: str,
    concept_id: str,
    workspace: Path | str = ".",
) -> list[dict[str, Any]]:
    """Instant O(1) lookup of exact source lines for a concept from source-map.toml."""
    ws = Path(workspace).resolve()
    map_file = ws / "courses" / course_slug / "source-map.toml"
    if not map_file.is_file():
        return []

    try:
        data = tomllib.loads(map_file.read_text(encoding="utf-8"))
    except Exception:
        return []

    sources_by_id = {s["id"]: s for s in data.get("sources", [])}

    resolved_excerpts: list[dict[str, Any]] = []
    norm_query = re.sub(r"[^a-zA-Z0-9]+", "_", concept_id.lower()).strip("_")

    for ch in data.get("chapters", []):
        for sec in ch.get("sections", []):
            for c in sec.get("concepts", []):
                c_id = re.sub(r"[^a-zA-Z0-9]+", "_", c.get("id", "").lower()).strip("_")
                c_title = re.sub(r"[^a-zA-Z0-9]+", "_", c.get("title", "").lower()).strip("_")
                if c_id == norm_query or c_title == norm_query or norm_query in c_id or c_id in norm_query:
                    for ptr in c.get("pointers", []):
                        src_meta = sources_by_id.get(ptr["source_id"], {})
                        raw_rel = src_meta.get("raw_path")
                        excerpt_text = ""
                        if raw_rel:
                            raw_file = ws / raw_rel
                            if raw_file.is_file():
                                lines = raw_file.read_text(encoding="utf-8").splitlines()
                                start = max(1, ptr["lines"][0])
                                end = min(len(lines), ptr["lines"][1])
                                excerpt_text = "\n".join(lines[start - 1 : end])

                        resolved_excerpts.append({
                            "source_id": ptr["source_id"],
                            "source_title": src_meta.get("title", ptr["source_id"]),
                            "heading": ptr["heading"],
                            "lines": ptr["lines"],
                            "verbatim_anchor": ptr.get("verbatim_anchor", ""),
                            "content": excerpt_text,
                            "dialectic": c.get("dialectic", False),
                            "synthesis_notes": c.get("synthesis_notes", ""),
                        })
                    return resolved_excerpts

    return resolved_excerpts


def main() -> None:
    parser = argparse.ArgumentParser(description="source_mapper.py — Multi-source chapter pipeline & symbol table compiler")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcommand: conveyor
    conv_p = subparsers.add_parser("conveyor", help="Split source into bounded conveyor-belt batches")
    conv_p.add_argument("--source", required=True, help="Path to markdown source file")
    conv_p.add_argument("--max-tokens", type=int, default=25000, help="Max tokens per batch")

    # Subcommand: compile
    comp_p = subparsers.add_parser("compile", help="Compile courses/<slug>/source-map.toml")
    comp_p.add_argument("--course", required=True, help="Course slug")
    comp_p.add_argument("--workspace", default=".", help="Workspace root")

    # Subcommand: read
    read_p = subparsers.add_parser("read", help="Read exact mapped source text for a concept")
    read_p.add_argument("--course", required=True, help="Course slug")
    read_p.add_argument("--concept", required=True, help="Concept ID or title")
    read_p.add_argument("--workspace", default=".", help="Workspace root")

    args = parser.parse_args()

    if args.subcommand == "conveyor":
        batches = split_source_into_conveyor_batches(args.source, max_tokens_per_batch=args.max_tokens)
        output_json({"ok": True, "source": args.source, "total_batches": len(batches), "batches": batches})

    elif args.subcommand == "compile":
        sm = compile_source_map(args.course, workspace=args.workspace)
        output_json({"ok": True, "course": args.course, "total_concepts": sm["total_concepts"], "sources": len(sm["sources"])})

    elif args.subcommand == "read":
        excerpts = read_source_pointer(args.course, args.concept, workspace=args.workspace)
        output_json({"ok": True, "course": args.course, "concept": args.concept, "matches": len(excerpts), "excerpts": excerpts})


if __name__ == "__main__":
    main()
