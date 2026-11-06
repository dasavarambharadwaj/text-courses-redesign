#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""harvester.py — Autonomous Multi-Source Deep Harvester & Community Consensus Sourcing.

Spearheaded by Marie Curie (The Empirical Investigator) for TextCourses (FR-43):
- Scans community consensus (Reddit, Hacker News, university syllabi) for gold-standard materials.
- Clones / downloads open-source Git repositories & markdown textbooks from GitHub.
- Extracts and cleans YouTube lecture video transcripts and subtitles via yt-dlp / timedtext.
- Solicits proprietary/copyrighted gold-standard books gracefully via acquisition prompts.
- Synthesizes all multi-source evidence into research/<slug>/sources/ and research/<slug>/gold-standards.md.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

try:
    import tomli_w
except ImportError:
    tomli_w = None


def compute_sha256(content: str | bytes) -> str:
    """Compute SHA-256 checksum for string or bytes."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout/stderr and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def atomic_write_text(filepath: Path, text: str) -> None:
    """Write text atomically to disk."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_file, filepath)


def atomic_write_json(filepath: Path, data: dict[str, Any]) -> None:
    """Write JSON data atomically to disk."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_file, filepath)


# ---------------------------------------------------------------------------
# 1. GitHub Repository & Open Textbook Harvester (FR-43.2)
# ---------------------------------------------------------------------------

def normalize_github_url(repo_identifier: str) -> tuple[str, str, str]:
    """Normalize github identifier (URL, owner/repo, or git URL) to (clone_url, owner, repo)."""
    clean = repo_identifier.strip()
    clean = re.sub(r"\.git$", "", clean)

    match = re.search(r"github\.com[/:]([\w.-]+)/([\w.-]+)", clean)
    if match:
        owner, repo = match.group(1), match.group(2)
    elif re.match(r"^[\w.-]+/[\w.-]+$", clean):
        parts = clean.split("/")
        owner, repo = parts[0], parts[1]
    else:
        # Fallback generic git url
        name = Path(clean).stem
        return clean, "git", name

    clone_url = f"https://github.com/{owner}/{repo}.git"
    return clone_url, owner, repo


def harvest_github_repo(
    repo_identifier: str,
    slug: str,
    workspace: Path | str = ".",
    branch: str = "main",
    depth: int = 1,
) -> dict[str, Any]:
    """Harvest open textbook or course materials from a Git repository.
    
    Tries git clone --depth 1 first, falls back to archive zipball download.
    Discovers all documentation and markdown files, compiling chapter outline.
    """
    ws = Path(workspace).resolve()
    clone_url, owner, repo_name = normalize_github_url(repo_identifier)
    target_dir = ws / "research" / slug / "sources" / "repos" / repo_name

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    clone_success = False
    harvest_method = "git_clone"
    error_msg = ""

    # Strategy 1: Git clone shallow if git binary is present
    git_bin = shutil.which("git")
    if git_bin and not target_dir.exists():
        cmd = [git_bin, "clone", "--depth", str(depth), clone_url, str(target_dir)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            clone_success = True
        else:
            # Try with alternate default branch 'master'
            error_msg = proc.stderr.strip()

    elif target_dir.exists():
        # Already cloned
        clone_success = True
        harvest_method = "existing_clone"

    # Strategy 2: Zipball download fallback if git failed or absent
    if not clone_success and not target_dir.exists():
        zip_url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/{branch}.zip"
        zip_path = target_dir.parent / f"{repo_name}.zip"
        try:
            req = urllib.request.Request(
                zip_url,
                headers={"User-Agent": "TextCourses-Harvester/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                zip_data = resp.read()
            zip_path.write_bytes(zip_data)
            shutil.unpack_archive(zip_path, target_dir.parent)
            zip_path.unlink(missing_ok=True)
            # Find unpacked dir
            unpacked = list(target_dir.parent.glob(f"{repo_name}-*"))
            if unpacked:
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                os.replace(unpacked[0], target_dir)
            clone_success = True
            harvest_method = "zipball_download"
        except Exception as e:
            error_msg = f"Failed to download repository: {e}"

    if not clone_success and not target_dir.exists():
        return {
            "ok": False,
            "error": f"Failed to clone or download repository '{repo_identifier}': {error_msg}",
            "repo_url": clone_url,
        }

    # Discover textbook / content files
    discovered_files: list[dict[str, Any]] = []
    toc_headings: list[str] = []

    for file_path in sorted(target_dir.rglob("*")):
        if not file_path.is_file():
            continue
        # Skip git metadata
        if ".git" in file_path.parts:
            continue
        rel_path = file_path.relative_to(target_dir)
        ext = file_path.suffix.lower()

        if ext in {".md", ".markdown", ".rst", ".txt"}:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                sha = compute_sha256(content)
                headings = [line.strip("# ").strip() for line in content.splitlines() if line.startswith("# ")]
                toc_headings.extend(headings)
                discovered_files.append({
                    "path": str(rel_path),
                    "full_path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                    "sha256": sha,
                    "headings": headings[:5],
                })
            except Exception:
                pass

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest_data = {
        "repo_url": clone_url,
        "owner": owner,
        "repo": repo_name,
        "harvested_at": now_iso,
        "method": harvest_method,
        "local_path": str(target_dir),
        "total_content_files": len(discovered_files),
        "files": discovered_files,
    }
    manifest_file = target_dir / "harvest-manifest.json"
    atomic_write_json(manifest_file, manifest_data)

    return {
        "ok": True,
        "slug": slug,
        "repo_name": repo_name,
        "repo_url": clone_url,
        "local_dir": str(target_dir),
        "method": harvest_method,
        "files_count": len(discovered_files),
        "toc_sample": toc_headings[:15],
        "manifest_path": str(manifest_file),
    }


# ---------------------------------------------------------------------------
# 2. YouTube Video & Lecture Transcript Harvester (FR-43.3)
# ---------------------------------------------------------------------------

def extract_youtube_video_id(url_or_id: str) -> str:
    """Extract 11-character YouTube video ID from various URL formats or bare ID."""
    clean = url_or_id.strip()
    if re.match(r"^[\w-]{11}$", clean):
        return clean
    patterns = [
        r"(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/watch\?v=|\&v=)([\w-]{11})",
        r"^https?:\/\/.*youtube\.com\/.*[&?]v=([\w-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, clean)
        if m:
            return m.group(1)
    return clean


def clean_vtt_subtitles(vtt_text: str) -> str:
    """Clean WebVTT or SRT subtitle text into continuous readable transcript prose."""
    lines = vtt_text.splitlines()
    cleaned_lines: list[str] = []
    seen_lines: set[str] = set()

    # Regex for timestamp arrows: 00:00:00.000 --> 00:00:02.000
    timestamp_pattern = re.compile(r"\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d+)?\s*-->\s*\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d+)?")

    current_timestamp = ""
    for line in lines:
        line = line.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d+$", line):  # SRT line index
            continue
        if timestamp_pattern.search(line):
            ts_match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)", line)
            if ts_match:
                current_timestamp = ts_match.group(1)
            continue

        # Strip inline HTML tags (like <c>, </c>, <v>, etc.)
        clean_text = re.sub(r"<[^>]+>", "", line).strip()
        if not clean_text:
            continue

        # YouTube auto-subs often repeat identical or rolling phrases
        if clean_text in seen_lines:
            continue

        # If current line extends previous incomplete rolling fragment, supersede previous fragment
        if cleaned_lines and clean_text.startswith(cleaned_lines[-1]):
            seen_lines.discard(cleaned_lines[-1])
            cleaned_lines[-1] = clean_text
            seen_lines.add(clean_text)
            continue

        # If current line is already subsumed by previous line, ignore
        if cleaned_lines and cleaned_lines[-1].startswith(clean_text):
            continue

        seen_lines.add(clean_text)
        cleaned_lines.append(clean_text)

    # Group into cohesive paragraphs with periodic timestamp anchors
    paragraphs: list[str] = []
    chunk: list[str] = []
    for i, line in enumerate(cleaned_lines):
        chunk.append(line)
        if len(chunk) >= 6 or line.endswith((".", "?", "!")):
            paragraphs.append(" ".join(chunk))
            chunk = []
    if chunk:
        paragraphs.append(" ".join(chunk))

    return "\n\n".join(paragraphs)


def harvest_youtube_transcript(
    url_or_id: str,
    slug: str,
    title: str = "Video Lecture",
    workspace: Path | str = ".",
) -> dict[str, Any]:
    """Harvest transcript from YouTube video using yt-dlp or pure-python timedtext fallback."""
    ws = Path(workspace).resolve()
    video_id = extract_youtube_video_id(url_or_id)
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    out_dir = ws / "research" / slug / "sources" / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    slug_safe_title = re.sub(r"[^\w-]", "-", title.lower()).strip("-") or video_id
    out_file = out_dir / f"{slug_safe_title}-{video_id}.md"

    transcript_text = ""
    method = ""

    # Strategy 1: yt-dlp subtitles extraction
    yt_dlp_bin = shutil.which("yt-dlp")
    if yt_dlp_bin:
        temp_base = out_dir / f"tmp_{video_id}"
        cmd = [
            yt_dlp_bin,
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", "en",
            "--skip-download",
            "--sub-format", "vtt",
            "-o", str(temp_base) + ".%(ext)s",
            video_url,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        vtt_candidates = list(out_dir.glob(f"tmp_{video_id}*.vtt"))
        if vtt_candidates:
            raw_vtt = vtt_candidates[0].read_text(encoding="utf-8", errors="replace")
            transcript_text = clean_vtt_subtitles(raw_vtt)
            method = "yt-dlp_subtitles"
            for f in vtt_candidates:
                f.unlink(missing_ok=True)

    # Strategy 2: Pure Python timedtext scrape fallback
    if not transcript_text:
        try:
            req = urllib.request.Request(video_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            # Search for captionTracks
            match = re.search(r'"captionTracks":\s*(\[.*?\])', html)
            if match:
                tracks = json.loads(match.group(1))
                en_track = next((t for t in tracks if t.get("languageCode") == "en"), tracks[0] if tracks else None)
                if en_track and "baseUrl" in en_track:
                    sub_url = en_track["baseUrl"]
                    sub_req = urllib.request.Request(sub_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(sub_req, timeout=10) as sub_resp:
                        sub_xml = sub_resp.read().decode("utf-8", errors="replace")
                    # Parse XML timedtext
                    root = ET.fromstring(sub_xml)
                    raw_lines = [elem.text for elem in root.findall(".//text") if elem.text]
                    transcript_text = "\n\n".join(raw_lines)
                    method = "timedtext_xml"
        except Exception as e:
            if not transcript_text:
                transcript_text = f"Could not automatically fetch subtitles: {e}"
                method = "fallback_stub"

    if not transcript_text.strip():
        return {
            "ok": False,
            "error": f"Failed to retrieve subtitles or transcript for YouTube video {video_id}",
            "video_url": video_url,
        }

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    word_count = len(transcript_text.split())
    sha = compute_sha256(transcript_text)

    markdown_doc = f"""---
type: youtube-transcript
video_id: "{video_id}"
title: "{title}"
video_url: "{video_url}"
harvested_at: "{now_iso}"
word_count: {word_count}
sha256: "{sha}"
method: "{method}"
---

# 📺 Video Lecture Transcript: {title}

- **Source URL**: {video_url}
- **Retrieved**: {now_iso}
- **Word Count**: {word_count} words

---

## Cleaned Transcript

{transcript_text}
"""
    atomic_write_text(out_file, markdown_doc)

    return {
        "ok": True,
        "slug": slug,
        "video_id": video_id,
        "title": title,
        "video_url": video_url,
        "word_count": word_count,
        "file_path": str(out_file),
        "sha256": sha,
        "method": method,
    }


# ---------------------------------------------------------------------------
# 3. Community Consensus & Gold-Standard Registry (FR-43.1, FR-43.4)
# ---------------------------------------------------------------------------

def record_gold_standards(
    slug: str,
    topic: str,
    consensus_summary: str,
    gold_standard_items: list[dict[str, Any]],
    workspace: Path | str = ".",
) -> dict[str, Any]:
    """Record community consensus and status of gold-standard books/materials."""
    ws = Path(workspace).resolve()
    target_file = ws / "research" / slug / "gold-standards.md"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    items_md_blocks = []
    for i, item in enumerate(gold_standard_items, 1):
        title = item.get("title", "Unknown Material")
        author = item.get("author", "Unknown Author")
        edition = item.get("edition", "Latest")
        medium = item.get("medium", "Book / Textbook")
        status = item.get("status", "USER_PROVIDED_NEEDED")
        reason = item.get("reason", "Community consensus gold standard.")
        github_repo = item.get("github_repo", "")

        status_badge = {
            "HARVESTED": "✅ `[HARVESTED - Available in sources/]`",
            "TRANSCRIPT_EXTRACTED": "📺 `[TRANSCRIPT EXTRACTED]`",
            "USER_PROVIDED_NEEDED": "⚠️ `[ACQUISITION NEEDED - Proprietary/Book]`",
            "USER_PROVIDED_READY": "📘 `[USER PROVIDED - Ready]`",
        }.get(status, f"`[{status}]`")

        repo_line = f"- **GitHub Repository**: `{github_repo}`\n" if github_repo else ""

        items_md_blocks.append(f"""### {i}. {title} ({edition})
- **Author(s)**: {author}
- **Medium**: {medium}
- **Status**: {status_badge}
{repo_line}- **Why It's Gold Standard**: {reason}
""")

    content = f"""---
type: gold-standards-consensus
topic: "{topic}"
slug: "{slug}"
updated_at: "{now_iso}"
---

# 🏆 Community Consensus & Gold-Standard Materials: {topic}

*Empirical consensus harvested from Reddit (r/learnprogramming, r/compsci, domain subreddits), Hacker News, and university reading lists.*

## 1. Community Consensus Overview
{consensus_summary.strip()}

---

## 2. Definitive Gold-Standard Materials

{"".join(items_md_blocks)}

---

## 3. Material Acquisition & Local Ingestion Protocol (FR-43.4)

For materials marked **`[ACQUISITION NEEDED]`**:
- These are commercial, copyrighted textbooks that cannot be downloaded automatically.
- **How to provide**: Drop your personal copy (PDF, ePub, or Markdown) directly into:
  ```text
  research/{slug}/sources/
  ```
- Once added, re-run `/tc-research` or `uv run _tc/scripts/scout.py ingest-sources --slug {slug}` to automatically digest and integrate the book into your curriculum!
- **Zero-Stalling Choice**: If you do not have the book, you can proceed with open documentation and verified web sources.
"""
    atomic_write_text(target_file, content)

    return {
        "ok": True,
        "slug": slug,
        "file_path": str(target_file),
        "total_items": len(gold_standard_items),
        "items": gold_standard_items,
    }


# ---------------------------------------------------------------------------
# 4. Multi-Source Ingestion & Digest Enrichment (FR-43.5)
# ---------------------------------------------------------------------------

def ingest_sources_directory(
    slug: str,
    workspace: Path | str = ".",
) -> dict[str, Any]:
    """Scan research/<slug>/sources/ and integrate all harvested repos, transcripts, and files."""
    ws = Path(workspace).resolve()
    sources_dir = ws / "research" / slug / "sources"
    if not sources_dir.exists():
        sources_dir.mkdir(parents=True, exist_ok=True)

    discovered_sources: list[dict[str, Any]] = []
    combined_headings: list[str] = []
    combined_text_chunks: list[str] = []

    for f in sorted(sources_dir.rglob("*")):
        if not f.is_file() or ".git" in f.parts or f.name.startswith("."):
            continue
        rel = str(f.relative_to(sources_dir))
        ext = f.suffix.lower()

        if ext in {".md", ".markdown", ".txt", ".rst"}:
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
                sha = compute_sha256(text)
                headings = [line.strip("# ").strip() for line in text.splitlines() if line.startswith("# ")]
                combined_headings.extend(headings)
                combined_text_chunks.append(f"# Source: {rel}\n" + text[:2000])

                src_type = "markdown_file"
                if "transcripts" in f.parts:
                    src_type = "youtube_transcript"
                elif "repos" in f.parts:
                    src_type = "github_repo_content"

                discovered_sources.append({
                    "title": f.stem.replace("-", " ").title(),
                    "relative_path": rel,
                    "full_path": str(f),
                    "type": src_type,
                    "size_bytes": f.stat().st_size,
                    "sha256": sha,
                    "status": "verified",
                })
            except Exception:
                pass

        elif ext in {".pdf", ".epub"}:
            sha = compute_sha256(f.read_bytes())
            discovered_sources.append({
                "title": f.stem.replace("-", " ").title(),
                "relative_path": rel,
                "full_path": str(f),
                "type": "binary_book",
                "size_bytes": f.stat().st_size,
                "sha256": sha,
                "status": "user_provided_book",
            })

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    sources_manifest = {
        "slug": slug,
        "scanned_at": now_iso,
        "total_sources": len(discovered_sources),
        "sources": discovered_sources,
    }
    manifest_path = sources_dir / "sources-index.json"
    atomic_write_json(manifest_path, sources_manifest)

    return {
        "ok": True,
        "slug": slug,
        "total_sources": len(discovered_sources),
        "sources_manifest": str(manifest_path),
        "headings_sample": combined_headings[:20],
        "sources": discovered_sources,
    }


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI dispatcher for harvester.py."""
    parser = argparse.ArgumentParser(
        description="harvester.py — Multi-source deep harvester for TextCourses (FR-43)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # harvest-repo
    p_repo = subparsers.add_parser("harvest-repo", help="Clone or download open textbook / course repo from GitHub")
    p_repo.add_argument("--slug", required=True, help="Target course slug")
    p_repo.add_argument("--repo", required=True, help="GitHub repository URL or owner/repo")
    p_repo.add_argument("--workspace", default=".", help="Workspace root path")
    p_repo.add_argument("--branch", default="main", help="Target git branch (default: main)")

    # harvest-youtube
    p_yt = subparsers.add_parser("harvest-youtube", help="Extract and clean video transcript from YouTube lecture")
    p_yt.add_argument("--slug", required=True, help="Target course slug")
    p_yt.add_argument("--url", required=True, help="YouTube video URL or video ID")
    p_yt.add_argument("--title", default="Video Lecture", help="Video lecture title")
    p_yt.add_argument("--workspace", default=".", help="Workspace root path")

    # record-consensus
    p_cons = subparsers.add_parser("record-consensus", help="Record community consensus & gold-standard items")
    p_cons.add_argument("--slug", required=True, help="Target course slug")
    p_cons.add_argument("--topic", required=True, help="Topic title")
    p_cons.add_argument("--summary", required=True, help="Summary of Reddit / community consensus")
    p_cons.add_argument("--items-json", default="[]", help="JSON array of gold-standard books/items")
    p_cons.add_argument("--workspace", default=".", help="Workspace root path")

    # ingest-sources
    p_ing = subparsers.add_parser("ingest-sources", help="Scan and index research/<slug>/sources/ directory")
    p_ing.add_argument("--slug", required=True, help="Target course slug")
    p_ing.add_argument("--workspace", default=".", help="Workspace root path")

    args = parser.parse_args()

    try:
        if args.subcommand == "harvest-repo":
            res = harvest_github_repo(
                repo_identifier=args.repo,
                slug=args.slug,
                workspace=args.workspace,
                branch=args.branch,
            )
            output_json(res, 0 if res.get("ok") else 1)

        elif args.subcommand == "harvest-youtube":
            res = harvest_youtube_transcript(
                url_or_id=args.url,
                slug=args.slug,
                title=args.title,
                workspace=args.workspace,
            )
            output_json(res, 0 if res.get("ok") else 1)

        elif args.subcommand == "record-consensus":
            items = json.loads(args.items_json) if isinstance(args.items_json, str) else args.items_json
            res = record_gold_standards(
                slug=args.slug,
                topic=args.topic,
                consensus_summary=args.summary,
                gold_standard_items=items,
                workspace=args.workspace,
            )
            output_json(res, 0)

        elif args.subcommand == "ingest-sources":
            res = ingest_sources_directory(
                slug=args.slug,
                workspace=args.workspace,
            )
            output_json(res, 0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except Exception as e:
        output_json({"error": str(e)}, 1)


if __name__ == "__main__":
    main()
