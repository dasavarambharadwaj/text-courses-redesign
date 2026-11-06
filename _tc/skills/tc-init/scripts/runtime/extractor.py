#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pypdf>=5.0.0"]
# ///
"""extractor.py — Pure-Python Verbatim Ingestion & Pre-Flight Probe.

Extracts raw prose, code blocks, tables, and headers from PDFs and EPUBs into
verbatim markdown with zero LLM rewriting, and includes a pre-flight character
density check to fail-fast on scanned bitmap PDFs.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

try:
    import pypdf
except ImportError:
    pypdf = None


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print dictionary as formatted JSON and exit."""
    print(json.dumps(data, indent=2, ensure_ascii=False))
    sys.exit(exit_code)


def probe_pdf(pdf_path: Path | str, density_threshold: int = 50) -> dict[str, Any]:
    """Run pre-flight check to verify PDF contains extractable digital text and is not a scanned image."""
    p = Path(pdf_path).resolve()
    if not p.is_file():
        return {
            "ok": False,
            "error": f"File not found: {p}",
            "is_scanned_image": False,
            "status": "file_not_found",
        }

    if pypdf is None:
        return {
            "ok": False,
            "error": "pypdf library is not installed",
            "is_scanned_image": False,
            "status": "missing_dependency",
        }

    try:
        reader = pypdf.PdfReader(str(p))
        page_count = len(reader.pages)
        if page_count == 0:
            return {
                "ok": False,
                "pdf_path": str(p),
                "page_count": 0,
                "total_characters": 0,
                "avg_chars_per_page": 0.0,
                "is_scanned_image": True,
                "status": "failed_probe",
                "message": "⚠️ PDF contains zero pages.",
            }

        total_chars = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            total_chars += len(text.strip())

        avg_chars = total_chars / page_count

        if avg_chars < density_threshold:
            return {
                "ok": False,
                "pdf_path": str(p),
                "page_count": page_count,
                "total_characters": total_chars,
                "avg_chars_per_page": round(avg_chars, 2),
                "density_threshold": density_threshold,
                "is_scanned_image": True,
                "status": "failed_probe",
                "message": (
                    f"⚠️ This PDF appears to be a scanned bitmap image without a digital text layer "
                    f"({round(avg_chars, 1)} chars/page < threshold {density_threshold}). "
                    f"Please provide a searchable digital PDF, EPUB, or Markdown file."
                ),
            }

        return {
            "ok": True,
            "pdf_path": str(p),
            "page_count": page_count,
            "total_characters": total_chars,
            "avg_chars_per_page": round(avg_chars, 2),
            "density_threshold": density_threshold,
            "is_scanned_image": False,
            "status": "passed_probe",
            "message": "PDF contains searchable digital text layer.",
        }

    except Exception as e:
        return {
            "ok": False,
            "error": f"Failed to parse PDF: {e}",
            "is_scanned_image": False,
            "status": "parse_error",
        }


def extract_outline_bookmarks(reader: Any) -> list[dict[str, Any]]:
    """Extract table of contents bookmarks from PDF outline if available."""
    bookmarks: list[dict[str, Any]] = []
    try:
        outline = reader.outline
        if not outline:
            return bookmarks

        def _traverse(node: Any, depth: int = 1) -> None:
            if isinstance(node, list):
                for item in node:
                    _traverse(item, depth)
            elif hasattr(node, "title"):
                title = str(getattr(node, "title", "")).strip()
                page_num = None
                try:
                    if hasattr(node, "page"):
                        page_num = reader.get_destination_page_number(node)
                except Exception:
                    pass
                if title:
                    bookmarks.append({"title": title, "depth": depth, "page": page_num})

        _traverse(outline, 1)
    except Exception:
        pass
    return bookmarks


def extract_pdf_to_markdown(
    pdf_path: Path | str,
    output_path: Path | str | None = None,
    density_threshold: int = 50,
) -> dict[str, Any]:
    """Extract raw verbatim text, tables, and code snippets from a PDF into Markdown."""
    probe = probe_pdf(pdf_path, density_threshold=density_threshold)
    if not probe.get("ok"):
        return {
            "ok": False,
            "error": probe.get("message") or probe.get("error", "PDF probe failed"),
            "code": "SCANNED_PDF" if probe.get("is_scanned_image") else "PROBE_FAILED",
            "probe_details": probe,
        }

    p = Path(pdf_path).resolve()
    try:
        reader = pypdf.PdfReader(str(p))
        bookmarks = extract_outline_bookmarks(reader)

        md_parts: list[str] = []
        md_parts.append(f"# {p.stem}\n")

        if bookmarks:
            md_parts.append("## Table of Contents (Extracted)\n")
            for bm in bookmarks:
                indent = "  " * (bm["depth"] - 1)
                page_str = f" (p. {bm['page'] + 1})" if bm.get("page") is not None else ""
                md_parts.append(f"{indent}- {bm['title']}{page_str}")
            md_parts.append("\n---\n")

        total_extracted_chars = 0
        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            total_extracted_chars += len(text)
            md_parts.append(f"\n<!-- page: {idx} -->\n")
            # Preserve raw text exactly without LLM rewriting
            md_parts.append(text.strip())

        full_markdown = "\n".join(md_parts)

        out_file = None
        if output_path:
            out_p = Path(output_path).resolve()
            if out_p.is_dir() or not out_p.suffix:
                out_p.mkdir(parents=True, exist_ok=True)
                out_file = out_p / f"{p.stem}.md"
            else:
                out_p.parent.mkdir(parents=True, exist_ok=True)
                out_file = out_p

            out_file.write_text(full_markdown, encoding="utf-8")

        return {
            "ok": True,
            "input_file": str(p),
            "output_file": str(out_file) if out_file else None,
            "page_count": len(reader.pages),
            "total_characters": total_extracted_chars,
            "toc_entries_count": len(bookmarks),
            "markdown": full_markdown if not out_file else None,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": f"Error extracting PDF: {e}",
            "code": "EXTRACTION_ERROR",
        }


def extract_epub_to_markdown(epub_path: Path | str, output_path: Path | str | None = None) -> dict[str, Any]:
    """Extract text from an EPUB (ZIP archive of XHTML chapters) into markdown."""
    p = Path(epub_path).resolve()
    if not p.is_file():
        return {"ok": False, "error": f"File not found: {p}", "code": "NOT_FOUND"}

    try:
        md_chapters: list[str] = [f"# {p.stem}\n"]
        total_chars = 0

        with zipfile.ZipFile(p, "r") as z:
            # Sort files to find HTML/XHTML chapters
            html_files = [f for f in z.namelist() if f.lower().endswith((".xhtml", ".html", ".htm")) and not "toc" in f.lower()]
            html_files.sort()

            for hf in html_files:
                raw_bytes = z.read(hf)
                text = raw_bytes.decode("utf-8", errors="replace")
                # Basic HTML tag stripping while preserving paragraphs and headers
                text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL)
                text = re.sub(r"<h([1-6])[^>]*>(.*?)</h\1>", r"\n\n#\1 \2\n\n", text, flags=re.DOTALL)
                text = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", text, flags=re.DOTALL)
                text = re.sub(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", r"\n```\n\1\n```\n", text, flags=re.DOTALL)
                text = re.sub(r"<br\s*/?>", "\n", text)
                text = re.sub(r"<[^>]+>", "", text)
                text = html.unescape(text)
                text = re.sub(r"\n{3,}", "\n\n", text).strip()

                if text:
                    total_chars += len(text)
                    md_chapters.append(f"\n<!-- chapter: {hf} -->\n")
                    md_chapters.append(text)

        full_md = "\n".join(md_chapters)

        out_file = None
        if output_path:
            out_p = Path(output_path).resolve()
            if out_p.is_dir() or not out_p.suffix:
                out_p.mkdir(parents=True, exist_ok=True)
                out_file = out_p / f"{p.stem}.md"
            else:
                out_p.parent.mkdir(parents=True, exist_ok=True)
                out_file = out_p

            out_file.write_text(full_md, encoding="utf-8")

        return {
            "ok": True,
            "input_file": str(p),
            "output_file": str(out_file) if out_file else None,
            "total_characters": total_chars,
            "markdown": full_md if not out_file else None,
        }

    except Exception as e:
        return {"ok": False, "error": f"Failed to extract EPUB: {e}", "code": "EPUB_ERROR"}


def extract_document(
    input_path: Path | str,
    output_path: Path | str | None = None,
    density_threshold: int = 50,
) -> dict[str, Any]:
    """Universal document extractor: routes PDF, EPUB, and Markdown/TXT."""
    p = Path(input_path).resolve()
    if not p.is_file():
        return {"ok": False, "error": f"File not found: {p}", "code": "NOT_FOUND"}

    ext = p.suffix.lower()
    if ext == ".pdf":
        return extract_pdf_to_markdown(p, output_path=output_path, density_threshold=density_threshold)
    elif ext == ".epub":
        return extract_epub_to_markdown(p, output_path=output_path)
    elif ext in [".md", ".markdown", ".txt"]:
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            out_file = None
            if output_path:
                out_p = Path(output_path).resolve()
                if out_p.is_dir() or not out_p.suffix:
                    out_p.mkdir(parents=True, exist_ok=True)
                    out_file = out_p / p.name
                else:
                    out_p.parent.mkdir(parents=True, exist_ok=True)
                    out_file = out_p
                out_file.write_text(content, encoding="utf-8")

            return {
                "ok": True,
                "input_file": str(p),
                "output_file": str(out_file) if out_file else None,
                "total_characters": len(content),
                "markdown": content if not out_file else None,
            }
        except Exception as e:
            return {"ok": False, "error": f"Failed to read file: {e}", "code": "READ_ERROR"}
    else:
        return {
            "ok": False,
            "error": f"Unsupported file extension '{ext}'. Supported: .pdf, .epub, .md, .txt",
            "code": "UNSUPPORTED_FORMAT",
        }


DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".tc",
    "_tc",
    "tests",
    "node_modules",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "target",
    "build",
    "dist",
}


def discover_workspace_documents(
    workspace_root: Path | str,
    search_dirs: list[str] | None = None,
    exclude_dirs: set[str] | None = None,
    supported_extensions: tuple[str, ...] = (".pdf", ".epub"),
) -> list[Path]:
    """Scan workspace root and standard drop-in directories for books/documents.

    Discovers PDFs and EPUBs in:
    - workspace root
    - books/
    - sources/ (excluding sources/extracted and sources/raw)
    - research/
    - docs/
    """
    root = Path(workspace_root).resolve()
    if not root.exists():
        return []

    excludes = exclude_dirs or DEFAULT_EXCLUDE_DIRS
    if search_dirs is None:
        search_dirs = [".", "books", "sources", "research", "docs"]

    found: list[Path] = []
    seen_paths: set[Path] = set()

    for s_dir in search_dirs:
        target = (root / s_dir).resolve() if s_dir != "." else root
        if not target.exists():
            continue

        if target == root:
            # Check immediate children of root (do not recurse root indefinitely)
            for item in target.iterdir():
                if item.is_file() and item.suffix.lower() in supported_extensions:
                    p = item.resolve()
                    if p not in seen_paths:
                        seen_paths.add(p)
                        found.append(p)
        else:
            # For specific directories (books, sources, research, docs), walk recursively
            for current_root, dirs, files in os.walk(target):
                current_path = Path(current_root)
                # Filter out excluded directory names
                dirs[:] = [
                    d for d in dirs
                    if d not in excludes and d != "extracted" and d != "raw" and not d.startswith(".")
                ]
                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext in supported_extensions:
                        p = (current_path / f).resolve()
                        if p not in seen_paths:
                            seen_paths.add(p)
                            found.append(p)

    return sorted(found, key=lambda p: str(p).lower())


def auto_ingest_workspace(
    workspace_root: Path | str,
    target_dir: Path | str | None = None,
    density_threshold: int = 50,
) -> dict[str, Any]:
    """Automatically discover dropped PDFs/EPUBs and extract them to markdown.

    Returns structured summary with extracted files and empathetic guidance for scanned images.
    """
    root = Path(workspace_root).resolve()
    if target_dir is None:
        target_dir = root / "sources" / "extracted"
    else:
        target_dir = Path(target_dir).resolve()

    discovered = discover_workspace_documents(root)
    extracted: list[dict[str, Any]] = []
    scanned: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for doc_path in discovered:
        # Pre-flight probe for PDF
        if doc_path.suffix.lower() == ".pdf":
            probe = probe_pdf(doc_path, density_threshold=density_threshold)
            if not probe.get("ok") and probe.get("is_scanned_image"):
                scanned.append({
                    "path": str(doc_path),
                    "filename": doc_path.name,
                    "avg_chars_per_page": probe.get("avg_chars_per_page", 0.0),
                    "density_threshold": density_threshold,
                    "guidance": (
                        f"⚠️ '{doc_path.name}' appears to be a scanned bitmap image without a digital text layer. "
                        f"TextCourses requires searchable digital text to compile your lesson plans and deterministic "
                        f"symbol table. Please provide a digital text PDF, EPUB, or Markdown file."
                    ),
                })
                continue

        # Extract document
        out_file = target_dir / f"{doc_path.stem}.md"
        res = extract_document(doc_path, output_path=out_file, density_threshold=density_threshold)
        if res.get("ok"):
            extracted.append({
                "source_file": str(doc_path),
                "filename": doc_path.name,
                "output_file": str(out_file),
                "total_characters": res.get("total_characters", 0),
                "page_count": res.get("page_count"),
            })
        else:
            errors.append({
                "source_file": str(doc_path),
                "filename": doc_path.name,
                "error": res.get("error", "Unknown extraction error"),
                "code": res.get("code", "EXTRACTION_ERROR"),
            })

    return {
        "ok": len(errors) == 0,
        "total_discovered": len(discovered),
        "total_extracted": len(extracted),
        "total_scanned": len(scanned),
        "has_scanned_warnings": len(scanned) > 0,
        "extracted": extracted,
        "scanned": scanned,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="extractor.py — Pure-Python Verbatim Ingestion & Pre-Flight Probe")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # probe
    p_probe = subparsers.add_parser("probe", help="Run pre-flight text density check on a PDF")
    p_probe.add_argument("--input", "-i", required=True, help="Path to PDF file")
    p_probe.add_argument("--threshold", type=int, default=50, help="Minimum average characters per page (default: 50)")
    p_probe.add_argument("--json", action="store_true", help="Output results in JSON format")

    # extract
    p_ext = subparsers.add_parser("extract", help="Extract verbatim text from PDF/EPUB/MD")
    p_ext.add_argument("--input", "-i", required=True, help="Input document path")
    p_ext.add_argument("--output", "-o", help="Output directory or markdown file path")
    p_ext.add_argument("--threshold", type=int, default=50, help="Minimum characters per page for PDF probe")
    p_ext.add_argument("--json", action="store_true", help="Output results in JSON format")

    # auto-ingest
    p_auto = subparsers.add_parser("auto-ingest", help="Auto-discover and extract dropped PDFs/EPUBs in workspace")
    p_auto.add_argument("--workspace", "-w", default=".", help="Workspace root path (default: current directory)")
    p_auto.add_argument("--output", "-o", help="Target directory for extracted markdown (default: sources/extracted)")
    p_auto.add_argument("--threshold", type=int, default=50, help="Minimum average characters per page (default: 50)")
    p_auto.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    if args.subcommand == "probe":
        res = probe_pdf(args.input, density_threshold=args.threshold)
        if args.json:
            output_json(res, 0 if res.get("ok") else 1)
        else:
            if res.get("ok"):
                print(f"✅ Probe PASSED: {res.get('avg_chars_per_page')} chars/page (Pages: {res.get('page_count')})")
            else:
                print(f"❌ Probe FAILED: {res.get('message') or res.get('error')}")
                sys.exit(1)

    elif args.subcommand == "extract":
        res = extract_document(args.input, output_path=args.output, density_threshold=args.threshold)
        if args.json:
            output_json(res, 0 if res.get("ok") else 1)
        else:
            if res.get("ok"):
                out = res.get("output_file") or "(memory)"
                print(f"✅ Extracted successfully to: {out} ({res.get('total_characters')} characters)")
            else:
                print(f"❌ Extraction FAILED: {res.get('error')}")
                sys.exit(1)

    elif args.subcommand == "auto-ingest":
        res = auto_ingest_workspace(args.workspace, target_dir=args.output, density_threshold=args.threshold)
        if args.json:
            output_json(res, 0 if res.get("ok") else 1)
        else:
            print(f"📦 Discovered {res['total_discovered']} documents.")
            for ext_item in res.get("extracted", []):
                print(f"  ✅ Extracted: {ext_item['filename']} -> {ext_item['output_file']}")
            for scan_item in res.get("scanned", []):
                print(f"  {scan_item['guidance']}")
            for err_item in res.get("errors", []):
                print(f"  ❌ Error with {err_item['filename']}: {err_item['error']}")
            if not res.get("ok"):
                sys.exit(1)



if __name__ == "__main__":
    main()
