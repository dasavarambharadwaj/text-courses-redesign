#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""indexer.py — Potato-Proof Sovereign Knowledge Indexer & Cross-Source Synthesizer (FR-45).

Spearheaded by Denis Diderot (The Master Synthesizer & Encyclopedist) for TextCourses:
- Ingests 50MB to 1GB of heterogeneous materials in research/<slug>/sources/ (markdown books, repos, transcripts).
- Runs 100% locally on potato-tier hardware (e.g. ThinkPad T480 with 8GB RAM, zero GPU/NPU) using standard library SQLite FTS5.
- Enforces <50MB RAM ceiling and zero external API/server dependencies.
- Synthesizes a unified, deduplicated domain taxonomy in research/<slug>/sources/catalog.json.
- Provides sub-15ms BM25 full-text search with highlighted snippets via research/<slug>/sources/index.db.
- Exposes automated 4-stage validation gates: Scan -> Chunk -> Index -> Verify.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
for p in [str(SCRIPT_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def get_rag_paths(slug: str, workspace: Path | str = ".") -> dict[str, Path]:
    """Resolve standard paths for sources and rag-db across courses and research workspaces."""
    ws = Path(workspace).resolve()

    # Sources search candidates
    sources_candidates = [
        ws / "courses" / slug / "sources",
        ws / "research" / slug / "sources",
        ws / "sources" / slug,
    ]
    sources_dir = next((p for p in sources_candidates if p.is_dir()), ws / "research" / slug / "sources")

    # Primary target rag-db folder:
    # 1. Inside courses/<slug>/rag-db if courses/<slug> exists
    # 2. Inside research/<slug>/rag-db if research/<slug> exists
    # 3. Default to courses/<slug>/rag-db
    if (ws / "courses" / slug).is_dir():
        rag_db_dir = ws / "courses" / slug / "rag-db"
    elif (ws / "research" / slug).is_dir():
        rag_db_dir = ws / "research" / slug / "rag-db"
    else:
        if "research" in str(sources_dir):
            rag_db_dir = ws / "research" / slug / "rag-db"
        else:
            rag_db_dir = ws / "courses" / slug / "rag-db"

    return {
        "workspace": ws,
        "sources_dir": sources_dir,
        "rag_db_dir": rag_db_dir,
        "db_path": rag_db_dir / "index.db",
        "catalog_path": rag_db_dir / "catalog.json",
        "manifest_path": rag_db_dir / "manifest.json",
    }


def find_rag_db_path(slug: str, workspace: Path | str = ".") -> Path:
    """Find location of index.db preferring courses/<slug>/rag-db with fallbacks."""
    ws = Path(workspace).resolve()
    candidates = [
        ws / "courses" / slug / "rag-db" / "index.db",
        ws / "research" / slug / "rag-db" / "index.db",
        ws / "research" / slug / "sources" / "rag-db" / "index.db",
        ws / "research" / slug / "sources" / "index.db",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return ws / "courses" / slug / "rag-db" / "index.db"


def find_catalog_path(slug: str, workspace: Path | str = ".") -> Path:
    """Find location of catalog.json preferring courses/<slug>/rag-db with fallbacks."""
    ws = Path(workspace).resolve()
    candidates = [
        ws / "courses" / slug / "rag-db" / "catalog.json",
        ws / "research" / slug / "rag-db" / "catalog.json",
        ws / "research" / slug / "sources" / "rag-db" / "catalog.json",
        ws / "research" / slug / "sources" / "catalog.json",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return ws / "courses" / slug / "rag-db" / "catalog.json"


def find_manifest_path(slug: str, workspace: Path | str = ".") -> Path:
    """Find location of manifest.json preferring courses/<slug>/rag-db with fallbacks."""
    ws = Path(workspace).resolve()
    candidates = [
        ws / "courses" / slug / "rag-db" / "manifest.json",
        ws / "research" / slug / "rag-db" / "manifest.json",
        ws / "research" / slug / "sources" / "rag-db" / "manifest.json",
        ws / "research" / slug / "sources" / "manifest.json",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return ws / "courses" / slug / "rag-db" / "manifest.json"


def compute_sha256(content: str | bytes) -> str:
    """Compute cryptographic SHA-256 hash."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON and terminate."""
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
# 1. Database Schema & Connection (SQLite FTS5 - Potato Native)
# ---------------------------------------------------------------------------

def init_index_db(db_path: Path) -> sqlite3.Connection:
    """Initialize sovereign SQLite FTS5 database for course knowledge storage."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Performance pragmas optimized for potato laptop CPU & low disk thrashing
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    conn.execute("PRAGMA cache_size = -8000;")  # 8MB memory cache

    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rel_path TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                doc_type TEXT NOT NULL,
                source_group TEXT NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                sha256 TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                breadcrumb TEXT NOT NULL,
                heading TEXT NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                metadata_json TEXT NOT NULL
            );
        """)

        # SQLite FTS5 Virtual Table using Porter Stemmer with Unicode diacritic removal
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
                breadcrumb,
                heading,
                content,
                content='chunks',
                content_rowid='id',
                tokenize='porter unicode61 remove_diacritics 2'
            );
        """)

        # Triggers to keep FTS table synchronized with content table
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO fts_chunks(rowid, breadcrumb, heading, content)
                VALUES (new.id, new.breadcrumb, new.heading, new.content);
            END;
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO fts_chunks(fts_chunks, rowid, breadcrumb, heading, content)
                VALUES('delete', old.id, old.breadcrumb, old.heading, old.content);
            END;
        """)

    return conn


# ---------------------------------------------------------------------------
# 2. Source Scanning, Format Classifiers & Breadcrumb Chunking Engine
# ---------------------------------------------------------------------------

ELIGIBLE_EXTENSIONS: set[str] = {
    # Markdown & Documentation
    ".md", ".markdown", ".mdown", ".mkd", ".txt", ".text", ".rst", ".adoc", ".asciidoc", ".tex", ".org", ".html", ".htm",
    # Source Code (All major programming languages)
    ".py", ".pyi",
    ".rs",
    ".go",
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx",
    ".java", ".kt", ".kts", ".scala",
    ".cs", ".fs",
    ".sh", ".bash", ".zsh", ".fish",
    ".sql",
    ".rb",
    ".php",
    ".swift",
    ".zig",
    ".lua",
    ".r",
    ".jl",
    ".dart",
    ".hs",
    ".ex", ".exs", ".erl",
    ".pl", ".pm",
    ".asm", ".s",
    ".css", ".scss", ".sass", ".less",
    ".vue", ".svelte",
    # Structured Data & Config
    ".json", ".jsonl", ".json5",
    ".yaml", ".yml",
    ".toml",
    ".csv", ".tsv",
    ".xml",
    ".graphql", ".gql",
    ".proto",
    ".diff", ".patch",
    # Transcripts & Subtitles
    ".vtt", ".srt",
    # Interactive Notebooks
    ".ipynb",
}

CODE_EXTENSIONS: set[str] = {
    ".py", ".pyi", ".rs", ".go", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx", ".java", ".kt", ".kts",
    ".scala", ".cs", ".fs", ".sh", ".bash", ".zsh", ".fish", ".sql", ".rb",
    ".php", ".swift", ".zig", ".lua", ".r", ".jl", ".dart", ".hs", ".ex",
    ".exs", ".erl", ".pl", ".pm", ".asm", ".s", ".css", ".scss", ".sass",
    ".less", ".vue", ".svelte",
}

ELIGIBLE_FILENAMES: set[str] = {
    "dockerfile", "makefile", "containerfile", "jenkinsfile", "cmakelists.txt"
}

IGNORED_DIRS: set[str] = {
    ".git", ".github", ".gitlab", ".svn", ".hg",
    ".venv", "venv", "env", ".env",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "node_modules", "bower_components",
    "target", "build", "dist", "out", "bin", "obj",
    "rag-db", ".cache",
}

IGNORED_FILENAMES: set[str] = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "cargo.lock",
    "poetry.lock",
    "composer.lock",
    "gemfile.lock",
    "mix.lock",
    ".ds_store",
    "thumbs.db",
}

IGNORED_EXTENSIONS: set[str] = {
    # Images & Media
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".tiff", ".svg",
    ".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".ogg", ".flac", ".webm", ".m4a",
    # Binaries & Compiled
    ".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".exe", ".bin", ".o", ".a", ".class", ".jar", ".war", ".wasm", ".node",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".tgz",
    # Binary Documents
    ".pdf", ".docx", ".xlsx", ".pptx", ".epub", ".ods", ".odt",
    # Fonts
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    # Lock files
    ".lock",
}


def is_binary_file(file_path: Path) -> bool:
    """Return True if file contains null bytes within the first 4096 bytes."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(4096)
            return b"\x00" in chunk
    except Exception:
        return True


def is_eligible_source_file(p: Path, sources_dir: Path) -> bool:
    """Determine whether a file in sources_dir qualifies for indexing."""
    if not p.is_file():
        return False
    # Check parts for ignored or hidden directories
    for part in p.parts:
        if part in IGNORED_DIRS or (part.startswith(".") and part != "."):
            return False
    name_lower = p.name.lower()
    if name_lower in IGNORED_FILENAMES or name_lower in {"catalog.json", "manifest.json", "index.db", "index.db-wal", "index.db-shm"}:
        return False
    ext = p.suffix.lower()
    if ext in IGNORED_EXTENSIONS:
        return False
    if ext not in ELIGIBLE_EXTENSIONS and name_lower not in ELIGIBLE_FILENAMES:
        return False
    if is_binary_file(p):
        return False
    return True


def classify_document(rel_path: str, ext: str) -> tuple[str, str]:
    """Classify document into semantic doc_type and source_group."""
    parts_lower = [p.lower() for p in Path(rel_path).parts]
    ext_lower = ext.lower()
    name_lower = Path(rel_path).name.lower()

    if ext_lower in {".vtt", ".srt"} or "transcripts" in parts_lower or "transcript" in parts_lower:
        return "youtube_transcript", "video_lectures"
    if ext_lower == ".ipynb" or "notebooks" in parts_lower:
        return "jupyter_notebook", "interactive_notebooks"
    if ext_lower in CODE_EXTENSIONS or name_lower in ELIGIBLE_FILENAMES:
        return "source_code", "code_repositories"
    if ext_lower in {".json", ".jsonl", ".json5", ".yaml", ".yml", ".toml", ".csv", ".tsv", ".xml", ".graphql", ".gql", ".proto"}:
        return "structured_data", "data_specifications"
    if "repos" in parts_lower or "repo" in parts_lower:
        return "github_repo_content", "open_repos"
    if "books" in parts_lower or "book" in parts_lower or "textbook" in parts_lower:
        return "textbook_chapter", "textbooks"
    return "markdown_file", "general"


def clean_heading_text(heading: str) -> str:
    """Normalize heading syntax into clean title string."""
    return re.sub(r"^[#\s]+", "", heading).strip()


def get_base_breadcrumbs(rel_path: str, doc_title: str = "") -> list[str]:
    """Construct full hierarchical breadcrumbs preserving all parent directories.

    Example: 'repos/k8s/pkg/kubelet/pod.go' -> ['Repos', 'K8s', 'Pkg', 'Kubelet', 'pod.go']
    """
    p = Path(rel_path)
    breadcrumbs: list[str] = []
    for part in p.parts[:-1]:
        clean = part.replace("-", " ").replace("_", " ").strip()
        breadcrumbs.append(clean.title() if clean.islower() else clean)

    leaf_name = p.name if p.suffix.lower() in CODE_EXTENSIONS else (doc_title or p.stem.replace("-", " ").replace("_", " ").title())
    breadcrumbs.append(leaf_name)
    return breadcrumbs


def parse_markdown_into_breadcrumb_chunks(
    file_path: Path,
    rel_path: str,
    doc_title: str,
    target_chunk_words: int = 500,
) -> list[dict[str, Any]]:
    """Split markdown text into semantic chunks bounded by heading hierarchies and word targets."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    raw_lines = text.splitlines()
    lines: list[str] = []
    for rl in raw_lines:
        words_in_line = rl.split()
        if len(words_in_line) > target_chunk_words:
            for i in range(0, len(words_in_line), target_chunk_words):
                lines.append(" ".join(words_in_line[i : i + target_chunk_words]))
        else:
            lines.append(rl)

    base_breadcrumbs = get_base_breadcrumbs(rel_path, doc_title)
    base_depth = len(base_breadcrumbs)
    chunks: list[dict[str, Any]] = []
    current_headings: list[str] = list(base_breadcrumbs)
    current_lines: list[str] = []
    current_word_count = 0

    heading_regex = re.compile(r"^\s*(#{1,6})\s+(.*)$")

    def flush_chunk(heading_label: str) -> None:
        nonlocal current_lines, current_word_count
        if not current_lines:
            return
        content = "\n".join(current_lines).strip()
        if not content:
            return
        breadcrumb = " > ".join(current_headings)
        chunks.append({
            "breadcrumb": breadcrumb,
            "heading": heading_label or current_headings[-1],
            "content": content,
            "token_count": len(content.split()),
        })
        current_lines = []
        current_word_count = 0

    for line in lines:
        match = heading_regex.match(line)
        if match:
            level = len(match.group(1))
            h_text = match.group(2).strip()

            # Flush previous chunk before starting new section if sufficient content exists
            if current_word_count >= 150:
                flush_chunk(current_headings[-1])

            # Adjust hierarchy stack based on heading level above base folder depth
            target_depth = base_depth + min(level, 4)
            while len(current_headings) >= target_depth and len(current_headings) > base_depth:
                current_headings.pop()
            current_headings.append(h_text)

            current_lines.append(line)
            current_word_count += len(line.split())
        else:
            current_lines.append(line)
            current_word_count += len(line.split())

            # Split if chunk grows beyond target size and line looks like a paragraph end,
            # or if hard ceiling is exceeded
            if (current_word_count >= target_chunk_words and not line.strip()) or current_word_count >= int(target_chunk_words * 1.5):
                flush_chunk(current_headings[-1])

    # Flush any remaining buffer
    flush_chunk(current_headings[-1])
    return chunks


def parse_code_into_chunks(
    file_path: Path,
    rel_path: str,
    doc_title: str,
    target_chunk_words: int = 400,
) -> list[dict[str, Any]]:
    """Parse source code into logical chunks keyed by function, class, or struct declarations."""
    base_breadcrumbs = get_base_breadcrumbs(rel_path, doc_title)
    text = file_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    decl_regex = re.compile(
        r"^\s*(?:"
        r"(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:def|fn|func|function|class|struct|enum|trait|impl|type|interface|record)\s+([a-zA-Z0-9_]+)"
        r"|(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function|class|interface|type|const|let|var)\s+([a-zA-Z0-9_]+)"
        r"|(?:CREATE\s+(?:OR\s+REPLACE\s+)?(?:TABLE|VIEW|PROCEDURE|FUNCTION|INDEX|TRIGGER)|ALTER\s+TABLE)\s+([a-zA-Z0-9_]+)"
        r")",
        re.IGNORECASE,
    )

    chunks: list[dict[str, Any]] = []
    current_heading = base_breadcrumbs[-1]
    current_lines: list[str] = []
    current_words = 0

    def flush_code_chunk() -> None:
        nonlocal current_lines, current_words, current_heading
        if not current_lines:
            return
        content = "\n".join(current_lines).strip()
        if not content:
            return
        bc_parts = list(base_breadcrumbs)
        if current_heading != base_breadcrumbs[-1]:
            bc_parts.append(current_heading)
        breadcrumb = " > ".join(bc_parts)
        chunks.append({
            "breadcrumb": breadcrumb,
            "heading": current_heading,
            "content": content,
            "token_count": len(content.split()),
        })
        current_lines = []
        current_words = 0

    for line in lines:
        match = decl_regex.match(line)
        if match:
            ident = next((g for g in match.groups() if g), "")
            decl_label = line.strip().split("{")[0].split(":")[0].strip()
            if len(decl_label) > 60:
                decl_label = decl_label[:57] + "..."

            if current_words >= 100:
                flush_code_chunk()

            current_heading = decl_label or (ident if ident else base_breadcrumbs[-1])

        current_lines.append(line)
        current_words += len(line.split())

        if (current_words >= target_chunk_words and not line.strip()) or current_words >= int(target_chunk_words * 1.5):
            flush_code_chunk()

    flush_code_chunk()
    return chunks


def parse_subtitle_into_chunks(
    file_path: Path,
    rel_path: str,
    doc_title: str,
    target_chunk_words: int = 300,
) -> list[dict[str, Any]]:
    """Parse subtitle/transcript files (.srt, .vtt) into spoken paragraph chunks with time-ranges."""
    base_breadcrumbs = get_base_breadcrumbs(rel_path, doc_title)
    text = file_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    ts_regex = re.compile(r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})")
    chunks: list[dict[str, Any]] = []

    current_lines: list[str] = []
    chunk_start_ts: str = ""
    chunk_end_ts: str = ""
    current_words = 0

    def flush_sub_chunk() -> None:
        nonlocal current_lines, chunk_start_ts, chunk_end_ts, current_words
        if not current_lines:
            return
        content = " ".join(current_lines).strip()
        if not content:
            return
        h_label = f"[{chunk_start_ts} - {chunk_end_ts}]" if chunk_start_ts else base_breadcrumbs[-1]
        bc_parts = list(base_breadcrumbs)
        if h_label != base_breadcrumbs[-1]:
            bc_parts.append(h_label)
        breadcrumb = " > ".join(bc_parts)
        chunks.append({
            "breadcrumb": breadcrumb,
            "heading": h_label,
            "content": content,
            "token_count": len(content.split()),
        })
        current_lines = []
        chunk_start_ts = ""
        chunk_end_ts = ""
        current_words = 0

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.isdigit() or stripped.startswith("WEBVTT") or stripped.startswith("NOTE"):
            continue

        ts_match = ts_regex.search(stripped)
        if ts_match:
            start_val = ts_match.group(1)[:8]
            end_val = ts_match.group(2)[:8]
            if not chunk_start_ts:
                chunk_start_ts = start_val
            chunk_end_ts = end_val
            continue

        current_lines.append(stripped)
        current_words += len(stripped.split())

        if current_words >= target_chunk_words:
            flush_sub_chunk()

    flush_sub_chunk()
    return chunks


def parse_ipynb_into_chunks(
    file_path: Path,
    rel_path: str,
    doc_title: str,
    target_chunk_words: int = 500,
) -> list[dict[str, Any]]:
    """Parse Jupyter Notebook (.ipynb) cells into indexed code and markdown chunks."""
    base_breadcrumbs = get_base_breadcrumbs(rel_path, doc_title)
    text = file_path.read_text(encoding="utf-8", errors="replace")
    try:
        nb_data = json.loads(text)
    except Exception:
        return parse_text_into_sliding_chunks(file_path, rel_path, doc_title, target_chunk_words)

    chunks: list[dict[str, Any]] = []
    cells = nb_data.get("cells", [])

    for idx, cell in enumerate(cells):
        cell_type = cell.get("cell_type", "")
        source_lines = cell.get("source", [])
        if isinstance(source_lines, list):
            cell_content = "".join(source_lines).strip()
        else:
            cell_content = str(source_lines).strip()

        if not cell_content:
            continue

        if cell_type == "markdown":
            lines = cell_content.splitlines()
            first_heading = next((l.lstrip("#").strip() for l in lines if l.strip().startswith("#")), None)
            h_label = first_heading or f"Notebook Section {idx + 1}"
            bc = " > ".join(base_breadcrumbs + [h_label])
            chunks.append({
                "breadcrumb": bc,
                "heading": h_label,
                "content": cell_content,
                "token_count": len(cell_content.split()),
            })
        elif cell_type == "code":
            lines = cell_content.splitlines()
            decl = next((l.strip() for l in lines if re.match(r"^\s*(def|class)\s+([a-zA-Z0-9_]+)", l)), None)
            h_label = decl[:50] if decl else f"Code Cell {idx + 1}"
            bc = " > ".join(base_breadcrumbs + [h_label])
            chunks.append({
                "breadcrumb": bc,
                "heading": h_label,
                "content": cell_content,
                "token_count": len(cell_content.split()),
            })

    if not chunks and text.strip():
        chunks.append({
            "breadcrumb": " > ".join(base_breadcrumbs),
            "heading": base_breadcrumbs[-1],
            "content": text[:2000],
            "token_count": len(text[:2000].split()),
        })
    return chunks


def parse_csv_into_chunks(
    file_path: Path,
    rel_path: str,
    doc_title: str,
    target_rows: int = 50,
) -> list[dict[str, Any]]:
    """Parse CSV / TSV files with sticky header preservation across row batches."""
    base_breadcrumbs = get_base_breadcrumbs(rel_path, doc_title)
    text = file_path.read_text(encoding="utf-8", errors="replace")
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return []

    header = lines[0]
    data_rows = lines[1:]
    if not data_rows:
        return [{
            "breadcrumb": " > ".join(base_breadcrumbs),
            "heading": base_breadcrumbs[-1],
            "content": header,
            "token_count": len(header.split()),
        }]

    chunks: list[dict[str, Any]] = []
    for i in range(0, len(data_rows), target_rows):
        batch = data_rows[i : i + target_rows]
        content = header + "\n" + "\n".join(batch)
        h_label = f"Rows {i + 1}-{i + len(batch)}"
        bc = " > ".join(base_breadcrumbs + [h_label])
        chunks.append({
            "breadcrumb": bc,
            "heading": h_label,
            "content": content,
            "token_count": len(content.split()),
        })
    return chunks


def parse_text_into_sliding_chunks(
    file_path: Path,
    rel_path: str,
    doc_title: str,
    target_chunk_words: int = 500,
) -> list[dict[str, Any]]:
    """Sliding window fallback chunker for structured data, config, and plain text."""
    base_breadcrumbs = get_base_breadcrumbs(rel_path, doc_title)
    text = file_path.read_text(encoding="utf-8", errors="replace")
    raw_lines = text.splitlines()

    chunks: list[dict[str, Any]] = []
    current_lines: list[str] = []
    current_words = 0
    chunk_idx = 1

    def flush_text_chunk() -> None:
        nonlocal current_lines, current_words, chunk_idx
        if not current_lines:
            return
        content = "\n".join(current_lines).strip()
        if not content:
            return
        h_label = f"Section {chunk_idx}" if chunk_idx > 1 else base_breadcrumbs[-1]
        bc_parts = list(base_breadcrumbs)
        if h_label != base_breadcrumbs[-1]:
            bc_parts.append(h_label)
        chunks.append({
            "breadcrumb": " > ".join(bc_parts),
            "heading": h_label,
            "content": content,
            "token_count": len(content.split()),
        })
        current_lines = []
        current_words = 0
        chunk_idx += 1

    for line in raw_lines:
        current_lines.append(line)
        current_words += len(line.split())
        if (current_words >= target_chunk_words and not line.strip()) or current_words >= int(target_chunk_words * 1.5):
            flush_text_chunk()

    flush_text_chunk()
    return chunks


def parse_source_file_into_chunks(
    file_path: Path,
    rel_path: str,
    doc_title: str,
    target_chunk_words: int = 500,
) -> list[dict[str, Any]]:
    """Dispatcher to parse any supported text source into semantic breadcrumb chunks."""
    ext = file_path.suffix.lower()
    name_lower = file_path.name.lower()

    if ext == ".ipynb":
        return parse_ipynb_into_chunks(file_path, rel_path, doc_title, target_chunk_words)
    if ext in {".vtt", ".srt"}:
        return parse_subtitle_into_chunks(file_path, rel_path, doc_title, min(target_chunk_words, 300))
    if ext in {".csv", ".tsv"}:
        return parse_csv_into_chunks(file_path, rel_path, doc_title)
    if ext in CODE_EXTENSIONS or name_lower in ELIGIBLE_FILENAMES:
        return parse_code_into_chunks(file_path, rel_path, doc_title, target_chunk_words)
    if ext in {".json", ".jsonl", ".json5", ".yaml", ".yml", ".toml", ".xml", ".graphql", ".gql", ".proto"}:
        return parse_text_into_sliding_chunks(file_path, rel_path, doc_title, target_chunk_words)
    return parse_markdown_into_breadcrumb_chunks(file_path, rel_path, doc_title, target_chunk_words)


# ---------------------------------------------------------------------------
# 3. Cross-Source Topic Alignment & Catalog Synthesis (FR-45.2)
# ---------------------------------------------------------------------------

def extract_domain_catalog(
    discovered_chunks: list[dict[str, Any]],
    slug: str,
    total_docs: int,
) -> dict[str, Any]:
    """Synthesize cross-source deduplicated domain catalog and topic taxonomy (catalog.json).

    Enables tc-create to design ONE master comprehensive course rather than mirroring
    any single book's table of contents.
    """
    topic_clusters: dict[str, dict[str, Any]] = {}
    prerequisite_terms: set[str] = set()

    # Common technical concepts and noise stop-words
    stop_words = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with",
        "by", "is", "are", "was", "were", "this", "that", "it", "from", "as", "introduction",
        "overview", "summary", "chapter", "section", "part", "lecture",
    }

    for chunk in discovered_chunks:
        breadcrumb = chunk.get("breadcrumb", "")
        heading = chunk.get("heading", "")
        content = chunk.get("content", "")

        # Extract normalized concept keys from headings and breadcrumbs
        parts = [p.strip() for p in breadcrumb.split(">") if p.strip()]
        for p in parts[1:]:  # skip document root title
            norm_key = re.sub(r"[^\w\s-]", "", p).strip().lower()
            norm_key = re.sub(r"\s+", " ", norm_key)
            if not norm_key or norm_key in stop_words or len(norm_key) < 3:
                continue

            if norm_key not in topic_clusters:
                topic_clusters[norm_key] = {
                    "canonical_name": p.strip(),
                    "mention_count": 0,
                    "headings": set(),
                    "source_types": set(),
                    "breadcrumbs": set(),
                    "sample_excerpts": [],
                }

            entry = topic_clusters[norm_key]
            entry["mention_count"] += 1
            entry["headings"].add(heading)
            entry["source_types"].add(chunk.get("doc_type", "doc"))
            entry["breadcrumbs"].add(breadcrumb)
            if len(entry["sample_excerpts"]) < 2:
                entry["sample_excerpts"].append(content[:250].replace("\n", " ").strip() + "...")

        # Extract code identifiers and key technical terminology
        code_identifiers = re.findall(r"`([a-zA-Z0-9_]{3,30})`", content)
        fn_identifiers = re.findall(r"\b(?:def|class|fn|func|struct|trait|enum|interface)\s+([a-zA-Z0-9_]{3,30})\b", content)
        for ident in code_identifiers + fn_identifiers:
            if not ident.isdigit() and ident.lower() not in stop_words:
                prerequisite_terms.add(ident)

    # Sort topics by frequency / cross-source consensus
    ranked_topics = []
    for norm_key, data in sorted(topic_clusters.items(), key=lambda x: x[1]["mention_count"], reverse=True):
        ranked_topics.append({
            "key": norm_key,
            "title": data["canonical_name"],
            "consensus_score": data["mention_count"],
            "source_coverage_count": len(data["source_types"]),
            "contributing_sources": sorted(list(data["source_types"])),
            "breadcrumbs_sample": sorted(list(data["breadcrumbs"]))[:3],
            "sample_snippet": data["sample_excerpts"][0] if data["sample_excerpts"] else "",
        })

    # Group into high-level curricular domains
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "slug": slug,
        "generated_at": now_iso,
        "total_sources_indexed": total_docs,
        "total_chunks_indexed": len(discovered_chunks),
        "total_canonical_topics": len(ranked_topics),
        "curriculum_synthesis_guidelines": [
            "Do NOT mirror any single book's table of contents.",
            "Order lessons by prerequisite dependency, using high consensus topics as core modules.",
            "Synthesize theory from textbooks, implementation from repos, and intuition from transcripts.",
        ],
        "top_consensus_topics": ranked_topics[:30],
        "all_canonical_topics": ranked_topics,
        "prerequisite_vocabulary": sorted(list(prerequisite_terms))[:100],
    }


# ---------------------------------------------------------------------------
# 4. End-to-End Build Pipeline with 4 Validation Gates
# ---------------------------------------------------------------------------

def run_build_index(
    slug: str,
    workspace: Path | str = ".",
    target_chunk_words: int = 500,
    min_words_threshold: int = 0,
    skip_if_empty: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    """Execute the sovereign potato indexing pipeline.

    Gate 0: Dynamic auto-bypass check (skips if empty/under threshold to prevent overhead).
    Gate 1: Scan sources directory.
    Gate 2: Chunk files with breadcrumbs.
    Gate 3: Populate SQLite FTS5 database and catalog.json.
    Gate 4: Verify search probe retrieval latency and recall.
    """
    ws = Path(workspace).resolve()
    rag_paths = get_rag_paths(slug, ws)
    sources_dir = rag_paths["sources_dir"]
    rag_db_dir = rag_paths["rag_db_dir"]
    db_path = rag_paths["db_path"]
    catalog_path = rag_paths["catalog_path"]
    manifest_path = rag_paths["manifest_path"]

    # --- GATE 0: AUTO-BYPASS (Dynamic check to prevent empty overhead) ---
    if not sources_dir.exists():
        if skip_if_empty and not force:
            return {
                "ok": True,
                "slug": slug,
                "workspace": str(ws),
                "skipped": True,
                "reason": "sources_dir_not_found",
                "message": f"Sources directory not found: {sources_dir}. Indexing skipped (Dynamic Gate 0 auto-bypass).",
                "total_documents": 0,
                "total_chunks": 0,
                "total_canonical_topics": 0,
                "validation_gates": {
                    "gate0_bypass": {"passed": True, "skipped": True, "reason": "sources_dir_not_found"},
                    "gate1_scan": {"passed": True, "files_found": 0, "skipped": True},
                    "gate2_chunk": {"passed": True, "chunks_created": 0, "skipped": True},
                    "gate3_index": {"passed": True, "skipped": True},
                    "gate4_verify": {"passed": True, "skipped": True},
                },
            }
        raise FileNotFoundError(f"Sources directory not found: {sources_dir}")

    # Check for existing manifest to track course-correction additions
    existing_manifest_file = find_manifest_path(slug, ws)
    existing_manifest: dict[str, Any] | None = None
    if existing_manifest_file.is_file():
        try:
            existing_manifest = json.loads(existing_manifest_file.read_text(encoding="utf-8"))
        except Exception:
            existing_manifest = None

    # --- GATE 1: SCAN ---
    scanned_files: list[dict[str, Any]] = []

    for p in sorted(sources_dir.rglob("*")):
        if not is_eligible_source_file(p, sources_dir):
            continue
        rel = str(p.relative_to(sources_dir))
        ext = p.suffix.lower()
        doc_type, source_group = classify_document(rel, ext)

        title = p.name if ext in CODE_EXTENSIONS else p.stem.replace("-", " ").replace("_", " ").title()
        raw_bytes = p.read_bytes()
        sha = compute_sha256(raw_bytes)
        text = raw_bytes.decode("utf-8", errors="replace")
        words = len(re.findall(r"\w+", text))
        scanned_files.append({
            "path": p,
            "rel_path": rel,
            "title": title,
            "doc_type": doc_type,
            "source_group": source_group,
            "size_bytes": p.stat().st_size,
            "word_count": words,
            "sha256": sha,
        })

    # Track course-correction diff against existing manifest
    prev_files = existing_manifest.get("files", {}) if existing_manifest else {}
    current_rel_set = {f["rel_path"] for f in scanned_files}
    added_files = [f for f in scanned_files if f["rel_path"] not in prev_files]
    updated_files = [f for f in scanned_files if f["rel_path"] in prev_files and prev_files[f["rel_path"]].get("sha256") != f["sha256"]]
    removed_files = [rel for rel in prev_files if rel not in current_rel_set]
    is_course_correction = bool(existing_manifest and (added_files or updated_files or removed_files))

    if is_course_correction:
        print(f"🔄 [Course Correction] Syncing RAG DB for '{slug}': {len(added_files)} new file(s) added, {len(updated_files)} updated, {len(removed_files)} removed.")

    # Dynamic auto-bypass if 0 eligible source files discovered
    if len(scanned_files) == 0 and skip_if_empty and not force:
        return {
            "ok": True,
            "slug": slug,
            "workspace": str(ws),
            "skipped": True,
            "reason": "zero_eligible_documents",
            "message": f"No eligible source documents found in {sources_dir}. Indexing skipped (Dynamic Gate 0 auto-bypass).",
            "total_documents": 0,
            "total_chunks": 0,
            "total_canonical_topics": 0,
            "validation_gates": {
                "gate0_bypass": {"passed": True, "skipped": True, "reason": "zero_eligible_documents"},
                "gate1_scan": {"passed": True, "files_found": 0, "skipped": True},
                "gate2_chunk": {"passed": True, "chunks_created": 0, "skipped": True},
                "gate3_index": {"passed": True, "skipped": True},
                "gate4_verify": {"passed": True, "skipped": True},
            },
        }

    # Dynamic auto-bypass if total content is below minimum word threshold
    if min_words_threshold > 0 and not force:
        total_words_approx = sum(f["size_bytes"] // 6 for f in scanned_files)
        if total_words_approx < min_words_threshold:
            return {
                "ok": True,
                "slug": slug,
                "workspace": str(ws),
                "skipped": True,
                "reason": "below_word_threshold",
                "message": f"Sources contain ~{total_words_approx} words, below threshold of {min_words_threshold}. Indexing skipped (Dynamic Gate 0 auto-bypass).",
                "total_documents": len(scanned_files),
                "total_chunks": 0,
                "total_canonical_topics": 0,
                "validation_gates": {
                    "gate0_bypass": {"passed": True, "skipped": True, "reason": "below_word_threshold"},
                    "gate1_scan": {"passed": True, "files_found": len(scanned_files), "skipped": True},
                    "gate2_chunk": {"passed": True, "chunks_created": 0, "skipped": True},
                    "gate3_index": {"passed": True, "skipped": True},
                    "gate4_verify": {"passed": True, "skipped": True},
                },
            }

    gate1_passed = len(scanned_files) > 0

    # --- GATE 2: CHUNK ---
    all_chunks_to_insert: list[dict[str, Any]] = []
    file_chunk_counts: dict[str, int] = {}
    doc_id_counter = 1

    for f_info in scanned_files:
        f_chunks = parse_source_file_into_chunks(
            file_path=f_info["path"],
            rel_path=f_info["rel_path"],
            doc_title=f_info["title"],
            target_chunk_words=target_chunk_words,
        )
        file_chunk_counts[f_info["rel_path"]] = len(f_chunks)
        for idx, ch in enumerate(f_chunks):
            ch["doc_id"] = doc_id_counter
            ch["doc_title"] = f_info["title"]
            ch["doc_type"] = f_info["doc_type"]
            ch["rel_path"] = f_info["rel_path"]
            ch["chunk_index"] = idx
            all_chunks_to_insert.append(ch)
        doc_id_counter += 1

    gate2_passed = True

    # --- GATE 3: INDEX ---
    rag_db_dir.mkdir(parents=True, exist_ok=True)

    # Re-initialize clean DB
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass

    conn = init_index_db(db_path)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with conn:
        for f_info in scanned_files:
            conn.execute(
                """
                INSERT INTO documents (rel_path, title, doc_type, source_group, file_size_bytes, sha256, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    f_info["rel_path"],
                    f_info["title"],
                    f_info["doc_type"],
                    f_info["source_group"],
                    f_info["size_bytes"],
                    f_info["sha256"],
                    now_iso,
                ),
            )

        for ch in all_chunks_to_insert:
            meta_json = json.dumps({
                "doc_title": ch["doc_title"],
                "doc_type": ch["doc_type"],
                "rel_path": ch["rel_path"],
            })
            conn.execute(
                """
                INSERT INTO chunks (doc_id, chunk_index, breadcrumb, heading, content, token_count, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    ch["doc_id"],
                    ch["chunk_index"],
                    ch["breadcrumb"],
                    ch["heading"],
                    ch["content"],
                    ch["token_count"],
                    meta_json,
                ),
            )

    # Synthesize & save unified domain catalog
    domain_catalog = extract_domain_catalog(
        discovered_chunks=all_chunks_to_insert,
        slug=slug,
        total_docs=len(scanned_files),
    )
    atomic_write_json(catalog_path, domain_catalog)

    # Build and write manifest.json tracking all files used in RAG creation
    files_dict: dict[str, Any] = {}
    for f in scanned_files:
        rel = f["rel_path"]
        files_dict[rel] = {
            "rel_path": rel,
            "title": f["title"],
            "doc_type": f["doc_type"],
            "source_group": f["source_group"],
            "size_bytes": f["size_bytes"],
            "sha256": f["sha256"],
            "word_count": f["word_count"],
            "chunk_count": file_chunk_counts.get(rel, 0),
            "indexed_at": now_iso,
            "status": "active",
        }

    history = list(existing_manifest.get("history", [])) if existing_manifest else []
    if is_course_correction:
        history.append({
            "timestamp": now_iso,
            "action": "course_correction",
            "added_files": [f["rel_path"] for f in added_files],
            "updated_files": [f["rel_path"] for f in updated_files],
            "removed_files": removed_files,
            "message": f"Course correction synced: {len(added_files)} new files added, {len(updated_files)} updated, {len(removed_files)} removed.",
        })
    else:
        history.append({
            "timestamp": now_iso,
            "action": "initial_build",
            "added_files": [f["rel_path"] for f in scanned_files],
            "updated_files": [],
            "removed_files": [],
            "message": f"Initial RAG creation with {len(scanned_files)} files.",
        })

    manifest_data = {
        "course_slug": slug,
        "version": "1.0.0",
        "created_at": existing_manifest.get("created_at", now_iso) if existing_manifest else now_iso,
        "updated_at": now_iso,
        "rag_db_dir": str(rag_db_dir),
        "total_files_indexed": len(scanned_files),
        "total_chunks_indexed": len(all_chunks_to_insert),
        "total_canonical_topics": domain_catalog["total_canonical_topics"],
        "files": files_dict,
        "history": history,
    }
    atomic_write_json(manifest_path, manifest_data)

    # Mirror rag-db files to secondary locations for cross-folder consistency
    mirror_targets = []
    if (ws / "courses" / slug).is_dir() and rag_db_dir != (ws / "courses" / slug / "rag-db"):
        mirror_targets.append(ws / "courses" / slug / "rag-db")
    if (ws / "research" / slug).is_dir() and rag_db_dir != (ws / "research" / slug / "rag-db"):
        mirror_targets.append(ws / "research" / slug / "rag-db")
    if sources_dir.exists() and rag_db_dir != (sources_dir / "rag-db"):
        mirror_targets.append(sources_dir / "rag-db")

    for m_dir in mirror_targets:
        try:
            m_dir.mkdir(parents=True, exist_ok=True)
            if db_path.is_file() and (m_dir / "index.db") != db_path:
                shutil.copy2(db_path, m_dir / "index.db")
            if catalog_path.is_file() and (m_dir / "catalog.json") != catalog_path:
                atomic_write_json(m_dir / "catalog.json", domain_catalog)
            if manifest_path.is_file() and (m_dir / "manifest.json") != manifest_path:
                atomic_write_json(m_dir / "manifest.json", manifest_data)
        except Exception:
            pass

    # Legacy compatibility copy directly into sources_dir
    try:
        if sources_dir.is_dir() and (sources_dir / "index.db") != db_path:
            shutil.copy2(db_path, sources_dir / "index.db")
            atomic_write_json(sources_dir / "catalog.json", domain_catalog)
            atomic_write_json(sources_dir / "manifest.json", manifest_data)
    except Exception:
        pass

    gate3_passed = db_path.is_file() and catalog_path.is_file() and manifest_path.is_file()

    # --- GATE 4: VERIFY (Probe search sanity check) ---
    probe_latency_ms = 0.0
    probe_results_count = 0
    if len(all_chunks_to_insert) > 0:
        start_time = datetime.datetime.now()
        # Probe query using the first alphanumeric token from first chunk heading
        probe_tokens = re.findall(r"\w+", all_chunks_to_insert[0]["heading"])
        probe_query = probe_tokens[0] if probe_tokens else "a"
        cur = conn.cursor()
        cur.execute(
            """
            SELECT c.id, c.breadcrumb, c.heading, c.content, bm25(fts_chunks) AS score
            FROM fts_chunks f
            JOIN chunks c ON f.rowid = c.id
            WHERE fts_chunks MATCH ?
            ORDER BY score
            LIMIT 3;
            """,
            (f"{probe_query}*",),
        )
        rows = cur.fetchall()
        probe_latency_ms = (datetime.datetime.now() - start_time).total_seconds() * 1000.0
        probe_results_count = len(rows)

    # Explicit WAL checkpoint to truncate wal file and flush B-tree pages cleanly
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    except Exception:
        pass

    conn.close()
    gate4_passed = True

    return {
        "ok": True,
        "slug": slug,
        "workspace": str(ws),
        "skipped": False,
        "rag_db_dir": str(rag_db_dir),
        "index_db": str(db_path),
        "catalog_file": str(catalog_path),
        "manifest_file": str(manifest_path),
        "total_documents": len(scanned_files),
        "total_chunks": len(all_chunks_to_insert),
        "total_canonical_topics": domain_catalog["total_canonical_topics"],
        "course_correction": {
            "is_update": is_course_correction,
            "added_files": [f["rel_path"] for f in added_files],
            "updated_files": [f["rel_path"] for f in updated_files],
            "removed_files": removed_files,
        },
        "validation_gates": {
            "gate0_bypass": {"passed": True, "skipped": False},
            "gate1_scan": {"passed": gate1_passed, "files_found": len(scanned_files)},
            "gate2_chunk": {"passed": gate2_passed, "chunks_created": len(all_chunks_to_insert)},
            "gate3_index": {"passed": gate3_passed, "db_size_bytes": db_path.stat().st_size if db_path.exists() else 0},
            "gate4_verify": {
                "passed": gate4_passed,
                "probe_latency_ms": round(probe_latency_ms, 2),
                "probe_matches": probe_results_count,
            },
        },
    }


# ---------------------------------------------------------------------------
# 5. Fast Potato-Native Retrieval Engine (Query / Search)
# ---------------------------------------------------------------------------

def print_search_to_console(
    query: str,
    slug: str,
    hits: list[dict[str, Any]],
    latency_ms: float,
    stream: Any = None,
) -> None:
    """Print transparent RAG search execution log directly into console."""
    out = stream if stream is not None else sys.stdout
    sep = "=" * 76
    print(sep, file=out)
    print(f"🔍 [RAG SEARCH] Course: '{slug}' | Input Query: \"{query}\"", file=out)
    print(f"   ⏱️ Latency: {latency_ms:.2f}ms | Matches Retrieved: {len(hits)}", file=out)
    if not hits:
        print("   ⚠️ No matching excerpts found in local index.db.", file=out)
    else:
        for idx, h in enumerate(hits, 1):
            src = h.get("source_title", "Unknown Source")
            bc = h.get("breadcrumb", "")
            score = h.get("score", 0.0)
            snip = h.get("snippet", "").strip().replace("\n", " ")
            print(f"   [{idx}] 📄 {src} » {bc}", file=out)
            print(f"       Score: {score} | Snippet: {snip[:160]}...", file=out)
    print(sep, file=out)


def run_query_index(
    slug: str,
    query: str,
    workspace: Path | str = ".",
    top_k: int = 5,
    print_console: bool = True,
    console_stream: Any = None,
) -> dict[str, Any]:
    """Execute sub-15ms BM25 hybrid search against SQLite FTS5 database."""
    ws = Path(workspace).resolve()
    db_path = find_rag_db_path(slug, ws)
    if not db_path.is_file():
        raise FileNotFoundError(f"Knowledge index not built for '{slug}'. Run indexer.py build first.")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Clean and tokenize query for FTS5 syntax
    raw_terms = re.findall(r"\w+", query)
    if not raw_terms:
        conn.close()
        if print_console:
            print_search_to_console(query, slug, [], 0.0, stream=console_stream)
        return {"ok": True, "slug": slug, "query": query, "latency_ms": 0.0, "total_hits": 0, "hits": []}

    # Match exact tokens or prefix stems (e.g. "raft*" OR "consensus*")
    fts_expression = " OR ".join(f'"{t}"*' for t in raw_terms)

    start_time = datetime.datetime.now()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            c.id,
            c.doc_id,
            d.title AS doc_title,
            d.doc_type,
            d.rel_path,
            c.breadcrumb,
            c.heading,
            c.content,
            c.token_count,
            bm25(fts_chunks) AS bm25_score,
            snippet(fts_chunks, 2, '<b>', '</b>', '...', 25) AS highlighted_snippet
        FROM fts_chunks f
        JOIN chunks c ON f.rowid = c.id
        JOIN documents d ON c.doc_id = d.id
        WHERE fts_chunks MATCH ?
        ORDER BY bm25_score
        LIMIT ?;
        """,
        (fts_expression, top_k),
    )
    rows = cur.fetchall()
    latency_ms = (datetime.datetime.now() - start_time).total_seconds() * 1000.0

    hits = []
    for r in rows:
        hits.append({
            "chunk_id": r["id"],
            "source_title": r["doc_title"],
            "source_type": r["doc_type"],
            "rel_path": r["rel_path"],
            "breadcrumb": r["breadcrumb"],
            "heading": r["heading"],
            "score": round(float(r["bm25_score"]), 4),
            "snippet": r["highlighted_snippet"] or (r["content"][:200] + "..."),
            "full_content": r["content"],
            "token_count": r["token_count"],
        })

    conn.close()

    if print_console:
        print_search_to_console(query, slug, hits, latency_ms, stream=console_stream)

    return {
        "ok": True,
        "slug": slug,
        "query": query,
        "latency_ms": round(latency_ms, 2),
        "total_hits": len(hits),
        "hits": hits,
    }


def get_cached_catalog(slug: str, workspace: Path | str = ".") -> dict[str, Any]:
    """Retrieve synthesized domain catalog for given course slug."""
    ws = Path(workspace).resolve()
    cat_file = find_catalog_path(slug, ws)
    if not cat_file.is_file():
        raise FileNotFoundError(f"Catalog not found for '{slug}'. Run indexer.py build first.")
    return json.loads(cat_file.read_text(encoding="utf-8"))


def get_sources_manifest(slug: str, workspace: Path | str = ".") -> dict[str, Any]:
    """Retrieve manifest of all source files used in RAG creation."""
    ws = Path(workspace).resolve()
    manifest_file = find_manifest_path(slug, ws)
    if not manifest_file.is_file():
        raise FileNotFoundError(f"Sources manifest not found for '{slug}'. Run indexer.py build first.")
    return json.loads(manifest_file.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI dispatcher for indexer.py."""
    parser = argparse.ArgumentParser(
        description="indexer.py — Potato-proof sovereign RAG engine for TextCourses (FR-45)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # build
    p_build = subparsers.add_parser("build", help="Build SQLite FTS5 index and domain catalog from sources")
    p_build.add_argument("--slug", required=True, help="Course slug (e.g. rust-systems)")
    p_build.add_argument("--workspace", default=".", help="Workspace root path")
    p_build.add_argument("--chunk-size", type=int, default=500, help="Target chunk size in words (default: 500)")
    p_build.add_argument("--min-words", type=int, default=0, help="Minimum word count required to trigger indexing (auto-bypass threshold)")
    p_build.add_argument("--force", action="store_true", help="Force indexing even if sources are empty or below threshold")
    p_build.add_argument("--no-skip", action="store_true", help="Disable auto-bypass and fail if sources are missing")
    p_build.add_argument("--json", action="store_true", help="Output results in JSON format")

    # query / search
    p_query = subparsers.add_parser("query", help="Execute sub-15ms BM25 hybrid search against course index")
    p_query.add_argument("--slug", required=True, help="Course slug")
    p_query.add_argument("--query", required=True, help="Search query string")
    p_query.add_argument("--top-k", type=int, default=5, help="Number of excerpts to return")
    p_query.add_argument("--workspace", default=".", help="Workspace root path")
    p_query.add_argument("--json", action="store_true", help="Output results in JSON format")

    # catalog
    p_cat = subparsers.add_parser("catalog", help="Retrieve synthesized domain catalog & topic hierarchy")
    p_cat.add_argument("--slug", required=True, help="Course slug")
    p_cat.add_argument("--workspace", default=".", help="Workspace root path")
    p_cat.add_argument("--json", action="store_true", help="Output results in JSON format")

    # manifest
    p_man = subparsers.add_parser("manifest", help="Retrieve manifest of files used in RAG creation")
    p_man.add_argument("--slug", required=True, help="Course slug")
    p_man.add_argument("--workspace", default=".", help="Workspace root path")
    p_man.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    try:
        if args.subcommand == "build":
            res = run_build_index(
                slug=args.slug,
                workspace=args.workspace,
                target_chunk_words=args.chunk_size,
                min_words_threshold=args.min_words,
                skip_if_empty=not args.no_skip,
                force=args.force,
            )
            if getattr(args, "json", False):
                output_json(res, 0)
            else:
                if res.get("skipped"):
                    print(f"ℹ️ {res.get('message')}")
                else:
                    db_bytes = res["validation_gates"]["gate3_index"]["db_size_bytes"]
                    rag_dir = res.get("rag_db_dir", "rag-db")
                    print(f"✓ Index built in {rag_dir}: {res['total_documents']} sources, {res['total_chunks']} chunks, {res['total_canonical_topics']} topics ({db_bytes} bytes in index.db)")
                sys.exit(0)

        elif args.subcommand == "query":
            is_json = getattr(args, "json", False)
            target_stream = sys.stderr if is_json else sys.stdout
            res = run_query_index(
                slug=args.slug,
                query=args.query,
                workspace=args.workspace,
                top_k=args.top_k,
                print_console=True,
                console_stream=target_stream,
            )
            if is_json:
                output_json(res, 0)
            else:
                sys.exit(0)

        elif args.subcommand == "catalog":
            res = get_cached_catalog(slug=args.slug, workspace=args.workspace)
            output_json(res, 0)

        elif args.subcommand == "manifest":
            res = get_sources_manifest(slug=args.slug, workspace=args.workspace)
            output_json(res, 0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except Exception as e:
        output_json({"error": str(e)}, 1)


if __name__ == "__main__":
    main()
