#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""redirector.py — Course evolution, source drift analysis, and notes deprecator for TextCourses.

Inspects documentation drift in ingested reference sources using SHA-256
cryptographic digests, identifies affected unstarted/in-progress chapters,
and manages non-destructive deprecation alerts in completed learner notes
without modifying historical note bodies bit-for-bit (FR-19, FR-20, AD-7).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

CHUNK_SIZE = 64 * 1024  # 64KB chunks for streaming hash calculation


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


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 byte digest of a file in 64KB chunks."""
    filepath = Path(filepath)
    if not filepath.is_file():
        raise FileNotFoundError(f"Source file not found: {filepath}")
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()


def snapshot_sources_directory(sources_dir: Path) -> dict[str, str]:
    """Recursively calculate SHA-256 hashes of all files in sources directory."""
    sources_dir = Path(sources_dir)
    if not sources_dir.exists():
        raise FileNotFoundError(f"Sources directory not found: {sources_dir}")
    if not sources_dir.is_dir():
        raise NotADirectoryError(f"Sources path is not a directory: {sources_dir}")

    hashes: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(sources_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__"]
        for filename in filenames:
            if filename.startswith(".") or filename.endswith(".tmp") or filename.endswith(".bak"):
                continue
            fpath = Path(dirpath) / filename
            rel_path = fpath.relative_to(sources_dir).as_posix()
            hashes[rel_path] = compute_file_hash(fpath)
    return {k: hashes[k] for k in sorted(hashes.keys())}


DEPRECATION_PATTERN = re.compile(
    r"^>\s*⚠️\s*\*\*Deprecation Notice\*\*",
    re.MULTILINE,
)


def has_deprecation_notice(content: str) -> bool:
    """Check if markdown content already contains a deprecation alert block."""
    return bool(DEPRECATION_PATTERN.search(content[:1000]))


def deprecate_notes_file(
    notes_path: Path | str,
    reason: str,
    redirect_to: str | None = None,
    effective_date: str | None = None,
) -> dict[str, Any]:
    """Prepend a deprecation alert block to a notes.md file, strictly preserving body content."""
    notes_file = Path(notes_path).resolve()
    if not notes_file.exists():
        raise FileNotFoundError(f"Target notes file does not exist: {notes_file}")
    if not notes_file.is_file():
        raise ValueError(f"Target notes path is not a file: {notes_file}")

    original_content = notes_file.read_text(encoding="utf-8")

    if has_deprecation_notice(original_content):
        return {
            "ok": True,
            "deprecated": True,
            "already_present": True,
            "path": str(notes_file),
            "message": "Deprecation notice already present at top of file",
        }

    date_str = effective_date or datetime.date.today().isoformat()
    lines = [
        "> ⚠️ **Deprecation Notice**",
        f"> This material was superseded on {date_str}.",
        f"> **Reason:** {reason.strip()}",
    ]
    if redirect_to:
        lines.append(f"> **Redirect:** {redirect_to.strip()}")

    header = "\n".join(lines) + "\n\n"
    new_content = header + original_content

    atomic_write_text(notes_file, new_content)

    return {
        "ok": True,
        "deprecated": True,
        "already_present": False,
        "path": str(notes_file),
        "reason": reason.strip(),
        "effective_date": date_str,
        "redirect_to": redirect_to.strip() if redirect_to else None,
    }


def find_course_manifest(course_dir: Path) -> Path | None:
    """Locate course.toml within given course directory."""
    manifest = course_dir / "course.toml"
    if manifest.is_file():
        return manifest
    # Search one level deep if given courses/ folder
    for child in course_dir.iterdir():
        if child.is_dir() and (child / "course.toml").is_file():
            return child / "course.toml"
    return None


def resolve_sources_directory(course_dir: Path, explicit_sources: str | None = None) -> Path | None:
    """Resolve sources directory for a given course."""
    if explicit_sources:
        p = Path(explicit_sources)
        if p.is_dir():
            return p
        return None

    # Check course-local sources
    if (course_dir / "sources").is_dir():
        return course_dir / "sources"
    if (course_dir / "plan" / "sources").is_dir():
        return course_dir / "plan" / "sources"

    # Check workspace-level plan/sources
    curr = course_dir.resolve()
    for _ in range(4):
        candidate = curr / "plan" / "sources"
        if candidate.is_dir():
            return candidate
        if curr.parent == curr:
            break
        curr = curr.parent

    # Current working directory fallback
    cwd_candidate = Path("plan/sources")
    if cwd_candidate.is_dir():
        return cwd_candidate

    return None


def diff_course_sources(
    course_path: Path | str,
    sources_path: Path | str | None = None,
) -> dict[str, Any]:
    """Compare current reference sources against stored hash manifest and identify affected chapters."""
    course_dir = Path(course_path).resolve()
    if not course_dir.exists():
        raise FileNotFoundError(f"Course directory not found: {course_dir}")

    manifest_file = find_course_manifest(course_dir)
    if not manifest_file:
        raise FileNotFoundError(f"No course.toml found in {course_dir}")

    course_data = tomllib.loads(manifest_file.read_text(encoding="utf-8"))
    sources_dir = resolve_sources_directory(course_dir, str(sources_path) if sources_path else None)

    if not sources_dir or not sources_dir.is_dir():
        raise FileNotFoundError(f"No sources directory found for course at {course_dir}")

    current_hashes = snapshot_sources_directory(sources_dir)

    # Stored hashes can be in course.toml [sources] table, or a sources_ledger.toml file
    stored_hashes: dict[str, str] = {}
    sources_table = course_data.get("sources", {})
    if isinstance(sources_table, dict):
        if "hashes" in sources_table and isinstance(sources_table["hashes"], dict):
            stored_hashes = {k: str(v) for k, v in sources_table["hashes"].items()}
        elif "files" in sources_table and isinstance(sources_table["files"], dict):
            stored_hashes = {k: str(v) for k, v in sources_table["files"].items()}
        else:
            for k, v in sources_table.items():
                if isinstance(v, str) and len(v) == 64:
                    stored_hashes[k] = v

    ledger_file = sources_dir / "ledger.toml"
    if not stored_hashes and ledger_file.is_file():
        ledger_data = tomllib.loads(ledger_file.read_text(encoding="utf-8"))
        if "sources" in ledger_data and isinstance(ledger_data["sources"], dict):
            for k, v in ledger_data["sources"].items():
                if isinstance(v, dict) and "sha256" in v:
                    stored_hashes[k] = v["sha256"]
                elif isinstance(v, str):
                    stored_hashes[k] = v

    # Diff calculation
    current_keys = set(current_hashes.keys())
    stored_keys = set(stored_hashes.keys())

    added = sorted(list(current_keys - stored_keys))
    deleted = sorted(list(stored_keys - current_keys))
    common = current_keys & stored_keys
    modified = sorted([k for k in common if current_hashes[k] != stored_hashes[k]])
    unchanged = sorted([k for k in common if current_hashes[k] == stored_hashes[k]])

    drift_detected = bool(added or modified or deleted)

    # Inspect course chapters and sections
    completed_sections: list[dict[str, Any]] = []
    affected_sections: list[dict[str, Any]] = []

    chapters = course_data.get("chapters", [])
    for ch in chapters:
        ch_id = ch.get("id", "")
        ch_title = ch.get("title", "")
        for sec in ch.get("sections", []):
            sec_id = sec.get("id", "")
            sec_title = sec.get("title", "")
            sec_status = sec.get("status", "not_started")
            sec_sources = sec.get("sources", [])

            sec_info = {
                "chapter_id": ch_id,
                "chapter_title": ch_title,
                "section_id": sec_id,
                "section_title": sec_title,
                "status": sec_status,
                "sources": sec_sources,
            }

            if sec_status == "completed":
                completed_sections.append(sec_info)
            else:
                has_changed_source = any(s in modified or s in added or s in deleted for s in sec_sources)
                if drift_detected and (not sec_sources or has_changed_source):
                    sec_info["affected"] = True
                    affected_sections.append(sec_info)

    return {
        "ok": True,
        "course_path": str(course_dir),
        "sources_dir": str(sources_dir),
        "drift_detected": drift_detected,
        "changes": {
            "added": added,
            "modified": modified,
            "deleted": deleted,
            "unchanged": unchanged,
        },
        "affected_sections": affected_sections,
        "completed_sections_safe": completed_sections,
    }


def inspect_course_state(course_path: Path | str) -> dict[str, Any]:
    """Inspect deprecation status and note health for a given course directory."""
    course_dir = Path(course_path).resolve()
    if not course_dir.exists():
        raise FileNotFoundError(f"Course directory not found: {course_dir}")

    manifest_file = find_course_manifest(course_dir)
    if not manifest_file:
        raise FileNotFoundError(f"No course.toml found in {course_dir}")

    course_data = tomllib.loads(manifest_file.read_text(encoding="utf-8"))
    course_actual_dir = manifest_file.parent

    notes_found: list[dict[str, Any]] = []
    deprecated_count = 0
    clean_count = 0

    for note_path in course_actual_dir.glob("**/notes.md"):
        content = note_path.read_text(encoding="utf-8")
        is_dep = has_deprecation_notice(content)
        if is_dep:
            deprecated_count += 1
        else:
            clean_count += 1

        notes_found.append({
            "path": str(note_path.relative_to(course_actual_dir)),
            "deprecated": is_dep,
            "size_bytes": len(content.encode("utf-8")),
        })

    return {
        "ok": True,
        "course_id": course_data.get("course", {}).get("id", course_actual_dir.name),
        "course_title": course_data.get("course", {}).get("title", ""),
        "total_notes": len(notes_found),
        "deprecated_notes_count": deprecated_count,
        "clean_notes_count": clean_count,
        "notes": sorted(notes_found, key=lambda x: x["path"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="redirector.py",
        description="TextCourses course evolution, source drift analysis, and notes deprecator.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # diff-sources
    p_diff = subparsers.add_parser("diff-sources", help="Detect documentation drift and affected sections.")
    p_diff.add_argument("--path", required=True, help="Path to course directory or workspace.")
    p_diff.add_argument("--sources", default=None, help="Optional explicit path to reference sources directory.")
    p_diff.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # deprecate
    p_dep = subparsers.add_parser("deprecate", help="Prepend non-destructive deprecation notice to notes.md.")
    p_dep.add_argument("--path", required=True, help="Path to notes.md file to deprecate.")
    p_dep.add_argument("--reason", required=True, help="Reason for deprecation / supersession.")
    p_dep.add_argument("--redirect-to", default=None, help="Optional target section, chapter, or URL.")
    p_dep.add_argument("--effective-date", default=None, help="Effective date (YYYY-MM-DD). Defaults to today.")
    p_dep.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # inspect
    p_insp = subparsers.add_parser("inspect", help="Inspect course notes and deprecation state.")
    p_insp.add_argument("--path", required=True, help="Path to course directory.")
    p_insp.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    try:
        if args.subcommand == "diff-sources":
            result = diff_course_sources(args.path, args.sources)
            output_json(result, 0)

        elif args.subcommand == "deprecate":
            result = deprecate_notes_file(
                args.path,
                reason=args.reason,
                redirect_to=args.redirect_to,
                effective_date=args.effective_date,
            )
            output_json(result, 0)

        elif args.subcommand == "inspect":
            result = inspect_course_state(args.path)
            output_json(result, 0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except Exception as e:
        output_json({"error": str(e)}, 1)


if __name__ == "__main__":
    main()
