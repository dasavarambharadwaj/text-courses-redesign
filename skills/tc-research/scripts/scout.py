#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""scout.py — Documentation scout and research caching engine for TextCourses.

Scrapes and extracts documentation ToCs, API symbol indexes, and vocabulary concepts
from URLs, local files, or topic outlines, scoring confidence ratings (high, medium,
low, unverified) and caching structured digests in .tc/research/<slug>/ (FR-6, AD-4).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import tomli_w

VALID_CONFIDENCE_LEVELS = {"high", "medium", "low", "unverified"}


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def atomic_write_json(filepath: Path, data: dict[str, Any]) -> None:
    """Write JSON data atomically using a temp file, fsync, and os.replace."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic JSON write failed for {filepath}: {e}") from e


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


def compute_sha256_text(text: str) -> str:
    """Compute SHA-256 hex digest of string content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_toc_and_symbols(content: str) -> dict[str, Any]:
    """Parse table of contents, API symbols, and technical vocabulary from text."""
    toc: list[dict[str, Any]] = []
    api_index: list[dict[str, Any]] = []
    vocabulary: set[str] = set()

    lines = content.splitlines()

    # 1. Headings (Markdown & RST)
    for line in lines:
        stripped = line.strip()
        # Markdown headings
        m_head = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if m_head:
            level = len(m_head.group(1))
            title = m_head.group(2).strip()
            # Clean anchors or badges
            title_clean = re.sub(r"\[.*?\]|\(.*?\)|<.*?>", "", title).strip()
            if title_clean:
                toc.append({"level": level, "title": title_clean})

        # API signatures: functions
        m_fn = re.search(r"\b(?:def|fn|func|function)\s+([a-zA-Z0-9_]+)\s*\((.*?)\)", line)
        if m_fn:
            name = m_fn.group(1)
            params = m_fn.group(2).strip()
            api_index.append({
                "name": name,
                "type": "function",
                "signature": f"{name}({params})",
            })

        # API signatures: classes / structs / types
        m_cls = re.search(r"\b(?:class|struct|type|interface)\s+([a-zA-Z0-9_]+)", line)
        if m_cls:
            name = m_cls.group(1)
            api_index.append({
                "name": name,
                "type": "type",
                "signature": name,
            })

        # Vocabulary: backticked identifiers
        backticked = re.findall(r"`([a-zA-Z0-9_.:#<-]+)`", line)
        for term in backticked:
            if len(term) >= 3 and not term.isdigit():
                vocabulary.add(term)

        # Vocabulary: strong bold technical terms
        bolded = re.findall(r"\*\*([a-zA-Z0-9_ -]+)\*\*", line)
        for term in bolded:
            t_clean = term.strip().lower()
            if 3 <= len(t_clean) <= 40 and not t_clean.isdigit():
                vocabulary.add(t_clean)

    # Deduplicate API index by signature
    unique_apis: list[dict[str, Any]] = []
    seen_sigs: set[str] = set()
    for item in api_index:
        sig = item["signature"]
        if sig not in seen_sigs:
            seen_sigs.add(sig)
            unique_apis.append(item)

    return {
        "toc": toc,
        "api_index": unique_apis,
        "vocabulary": sorted(list(vocabulary)),
    }


def fetch_url_content(url: str, timeout: int = 8) -> tuple[str, str]:
    """Fetch content from HTTP/HTTPS URL, returning (content, error_msg)."""
    headers = {"User-Agent": "TextCourses-Scout/1.0 (+https://textcourses.com)"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw_data = response.read()
            html = raw_data.decode(charset, errors="replace")

            # Basic clean HTML to text/markdown headings
            cleaned = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r"<style.*?>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
            # Convert h1, h2, h3 to markdown headings
            cleaned = re.sub(r"<h1.*?>(.*?)</h1>", r"# \1\n", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"<h2.*?>(.*?)</h2>", r"## \1\n", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"<h3.*?>(.*?)</h3>", r"### \1\n", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"<code.*?>(.*?)</code>", r"`\1`", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"<.*?>", " ", cleaned)
            return cleaned, ""
    except Exception as e:
        return "", str(e)


def run_scout(
    slug: str,
    workspace: Path | str = ".",
    url: str | None = None,
    source_path: Path | str | None = None,
    topic: str | None = None,
    confidence_override: str | None = None,
) -> dict[str, Any]:
    """Execute research scouting for target slug and write structured cache files."""
    ws = Path(workspace).resolve()
    research_dir = ws / ".tc" / "research" / slug
    research_dir.mkdir(parents=True, exist_ok=True)

    extracted_content = ""
    source_uri = ""
    source_type = ""
    confidence = "unverified"
    notes = []

    # 1. Local path source
    if source_path:
        p = Path(source_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Source path not found: {p}")
        source_uri = str(p)
        if p.is_file():
            source_type = "file"
            extracted_content = p.read_text(encoding="utf-8")
        elif p.is_dir():
            source_type = "directory"
            parts = []
            for f in sorted(p.glob("**/*")):
                if f.is_file() and f.suffix in {".md", ".txt", ".rst", ".py", ".rs", ".ts", ".go"}:
                    parts.append(f"# File: {f.name}\n" + f.read_text(encoding="utf-8"))
            extracted_content = "\n\n".join(parts)
        confidence = "high"

    # 2. Web URL source
    elif url:
        source_uri = url
        source_type = "url"
        content, err = fetch_url_content(url)
        if err:
            notes.append(f"Network fetch warning: {err}")
            extracted_content = f"# Documentation for {slug}\nTopic reference: {url}\n"
            confidence = "unverified"
        else:
            extracted_content = content
            confidence = "high"

    # 3. Topic fallback
    elif topic:
        source_uri = f"topic:{topic}"
        source_type = "topic_fallback"
        extracted_content = (
            f"# {topic.title()}\n\n"
            f"Overview and fundamental concepts for {topic}.\n\n"
            f"## Core Concepts\n- Architecture\n- Primitives\n- Applications\n"
        )
        confidence = "medium"
    else:
        source_uri = f"topic:{slug}"
        source_type = "topic_fallback"
        extracted_content = f"# {slug.title()}\n\nOverview of {slug}.\n"
        confidence = "unverified"

    # Override confidence if explicitly specified
    if confidence_override:
        if confidence_override not in VALID_CONFIDENCE_LEVELS:
            raise ValueError(
                f"Invalid confidence '{confidence_override}'. Must be one of {sorted(VALID_CONFIDENCE_LEVELS)}"
            )
        confidence = confidence_override

    # Parse ToC, APIs, vocabulary
    parsed = extract_toc_and_symbols(extracted_content)

    # Adjust confidence if high was claimed but zero ToC or APIs found
    if confidence == "high" and not parsed["toc"] and not parsed["api_index"]:
        confidence = "medium"

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    content_hash = compute_sha256_text(extracted_content)

    digest = {
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "source": source_uri,
        "source_type": source_type,
        "confidence": confidence,
        "crawled_at": now_iso,
        "content_sha256": content_hash,
        "toc": parsed["toc"],
        "api_index": parsed["api_index"],
        "vocabulary": parsed["vocabulary"],
        "summary": f"Scouted {len(parsed['toc'])} headings, {len(parsed['api_index'])} API symbols, {len(parsed['vocabulary'])} terms from {source_type}.",
        "notes": notes,
    }

    # Write digest.json
    digest_file = research_dir / "digest.json"
    atomic_write_json(digest_file, digest)

    # Write sources.toml
    sources_data = {
        "research": {
            "slug": slug,
            "confidence": confidence,
            "updated_at": now_iso,
        },
        "sources": [
            {
                "uri": source_uri,
                "type": source_type,
                "sha256": content_hash,
                "status": "verified" if confidence in {"high", "medium"} else "unverified",
            }
        ],
    }
    sources_file = research_dir / "sources.toml"
    atomic_write_toml(sources_file, sources_data)

    return {
        "ok": True,
        "slug": slug,
        "confidence": confidence,
        "digest_file": str(digest_file),
        "sources_file": str(sources_file),
        "headings_count": len(parsed["toc"]),
        "apis_count": len(parsed["api_index"]),
        "vocabulary_count": len(parsed["vocabulary"]),
        "digest": digest,
    }


def get_cached_digest(slug: str, workspace: Path | str = ".") -> dict[str, Any]:
    """Retrieve cached research digest for a given slug."""
    ws = Path(workspace).resolve()
    digest_file = ws / ".tc" / "research" / slug / "digest.json"
    if not digest_file.is_file():
        raise FileNotFoundError(f"No research digest cached for slug '{slug}' at {digest_file}")

    return json.loads(digest_file.read_text(encoding="utf-8"))


def list_cached_research(workspace: Path | str = ".") -> dict[str, Any]:
    """List all research digests currently stored in workspace."""
    ws = Path(workspace).resolve()
    base_dir = ws / ".tc" / "research"
    if not base_dir.is_dir():
        return {"ok": True, "workspace": str(ws), "research_topics": []}

    topics: list[dict[str, Any]] = []
    for item in sorted(base_dir.iterdir()):
        if item.is_dir() and (item / "digest.json").is_file():
            try:
                data = json.loads((item / "digest.json").read_text(encoding="utf-8"))
                topics.append({
                    "slug": item.name,
                    "title": data.get("title", item.name),
                    "confidence": data.get("confidence", "unverified"),
                    "source": data.get("source", ""),
                    "crawled_at": data.get("crawled_at", ""),
                })
            except Exception:
                topics.append({
                    "slug": item.name,
                    "title": item.name,
                    "confidence": "unknown",
                })

    return {"ok": True, "workspace": str(ws), "research_topics": topics}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scout.py",
        description="TextCourses documentation scout and research caching engine.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # scout
    p_scout = subparsers.add_parser("scout", help="Scout documentation and cache research digest.")
    p_scout.add_argument("--slug", required=True, help="Course or topic slug (e.g. rust-systems).")
    p_scout.add_argument("--workspace", default=".", help="Path to workspace root.")
    p_scout.add_argument("--url", default=None, help="Documentation web URL to scout.")
    p_scout.add_argument("--source-path", default=None, help="Local file or directory to extract.")
    p_scout.add_argument("--topic", default=None, help="Topic description for fallback scaffolding.")
    p_scout.add_argument("--confidence", default=None, help="Explicit confidence override.")
    p_scout.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # get
    p_get = subparsers.add_parser("get", help="Retrieve cached research digest.")
    p_get.add_argument("--slug", required=True, help="Course or topic slug.")
    p_get.add_argument("--workspace", default=".", help="Path to workspace root.")
    p_get.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # list
    p_list = subparsers.add_parser("list", help="List all cached research topics.")
    p_list.add_argument("--workspace", default=".", help="Path to workspace root.")
    p_list.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    try:
        if args.subcommand == "scout":
            result = run_scout(
                slug=args.slug,
                workspace=args.workspace,
                url=args.url,
                source_path=args.source_path,
                topic=args.topic,
                confidence_override=args.confidence,
            )
            output_json(result, 0)

        elif args.subcommand == "get":
            result = get_cached_digest(args.slug, args.workspace)
            output_json(result, 0)

        elif args.subcommand == "list":
            result = list_cached_research(args.workspace)
            output_json(result, 0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except Exception as e:
        output_json({"error": str(e)}, 1)


if __name__ == "__main__":
    main()
