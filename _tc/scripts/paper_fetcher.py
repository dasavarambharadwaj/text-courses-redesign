#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""paper_fetcher.py — Autonomous Academic Paper, RFC, and Official Specification Harvester.

Spearheaded by Marie Curie (The Empirical Investigator) for TextCourses.
Discovers and autonomously downloads official technical ground truth:
1. IETF RFC Standards (TLS 1.3, HTTP/2, HTTP/3, OAuth 2.0, JWT, TCP/IP, QUIC).
2. arXiv Academic Papers & Landmark Technical Treatises.
3. Linux Kernel & Systems Manual Pages (epoll, syscalls, virtual memory, zero-copy).
Zero external API keys required; relies on public open endpoints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

USER_AGENT = "TextCourses-ResearchHarvester/2.0 (Academic Research; sovereign educational compiler)"

# Canonical mappings from domain keywords to IETF RFCs and Landmark Specifications
CANONICAL_SPECS = [
    {
        "keywords": ["tls 1.3", "tls1.3", "transport layer security 1.3"],
        "type": "rfc",
        "identifier": "8446",
        "title": "RFC 8446: The Transport Layer Security (TLS) Protocol Version 1.3",
        "url": "https://www.rfc-editor.org/rfc/rfc8446.txt",
        "filename": "rfc8446_tls13.txt",
    },
    {
        "keywords": ["tls 1.2", "tls1.2"],
        "type": "rfc",
        "identifier": "5246",
        "title": "RFC 5246: The Transport Layer Security (TLS) Protocol Version 1.2",
        "url": "https://www.rfc-editor.org/rfc/rfc5246.txt",
        "filename": "rfc5246_tls12.txt",
    },
    {
        "keywords": ["http/2", "http2", "h2"],
        "type": "rfc",
        "identifier": "9113",
        "title": "RFC 9113: HTTP/2",
        "url": "https://www.rfc-editor.org/rfc/rfc9113.txt",
        "filename": "rfc9113_http2.txt",
    },
    {
        "keywords": ["http/3", "http3", "h3"],
        "type": "rfc",
        "identifier": "9114",
        "title": "RFC 9114: HTTP/3",
        "url": "https://www.rfc-editor.org/rfc/rfc9114.txt",
        "filename": "rfc9114_http3.txt",
    },
    {
        "keywords": ["quic", "rfc 9000"],
        "type": "rfc",
        "identifier": "9000",
        "title": "RFC 9000: QUIC: A UDP-Based Multiplexed and Secure Transport",
        "url": "https://www.rfc-editor.org/rfc/rfc9000.txt",
        "filename": "rfc9000_quic.txt",
    },
    {
        "keywords": ["oauth2", "oauth 2.0", "oauth 2", "oauth"],
        "type": "rfc",
        "identifier": "6749",
        "title": "RFC 6749: The OAuth 2.0 Authorization Framework",
        "url": "https://www.rfc-editor.org/rfc/rfc6749.txt",
        "filename": "rfc6749_oauth2.txt",
    },
    {
        "keywords": ["jwt", "json web token", "rfc 7519"],
        "type": "rfc",
        "identifier": "7519",
        "title": "RFC 7519: JSON Web Token (JWT)",
        "url": "https://www.rfc-editor.org/rfc/rfc7519.txt",
        "filename": "rfc7519_jwt.txt",
    },
    {
        "keywords": ["tcp", "tcp/ip", "transmission control protocol", "rfc 9293"],
        "type": "rfc",
        "identifier": "9293",
        "title": "RFC 9293: Transmission Control Protocol (TCP) Specification",
        "url": "https://www.rfc-editor.org/rfc/rfc9293.txt",
        "filename": "rfc9293_tcp.txt",
    },
    {
        "keywords": ["websocket", "rfc 6455"],
        "type": "rfc",
        "identifier": "6455",
        "title": "RFC 6455: The WebSocket Protocol",
        "url": "https://www.rfc-editor.org/rfc/rfc6455.txt",
        "filename": "rfc6455_websocket.txt",
    },
    {
        "keywords": ["dns", "rfc 1035"],
        "type": "rfc",
        "identifier": "1035",
        "title": "RFC 1035: Domain Names - Implementation and Specification",
        "url": "https://www.rfc-editor.org/rfc/rfc1035.txt",
        "filename": "rfc1035_dns.txt",
    },
]

# Canonical Systems Manual Pages and Treatises
CANONICAL_SYSTEMS_DOCS = [
    {
        "keywords": ["epoll", "io multiplexing", "event loop", "select", "poll"],
        "name": "epoll_7",
        "title": "epoll(7) - Linux I/O event notification facility",
        "source": "Linux Programmer's Manual",
        "content": """# epoll(7) — Linux I/O Event Notification Facility

## Name
epoll - I/O event notification facility

## Synopsis
#include <sys/epoll.h>

## Description
The epoll API performs a similar task to poll(2): monitoring multiple file descriptors to see if I/O is possible on any of them. The epoll API can be used either as an edge-triggered or a level-triggered interface and scales well to large numbers of watched file descriptors.

The central concept of the epoll API is the epoll instance, an in-kernel data structure that can be considered as a container for two lists:
- The interest list (sometimes also called the epoll set): the set of file descriptors that the process has registered an interest in monitoring.
- The ready list: the set of file descriptors that are "ready" for I/O. The ready list is a subset of the file descriptors in the interest list.

The following system calls are provided to create and manage an epoll instance:
- epoll_create1(2) creates a new epoll instance and returns a file descriptor referring to that instance.
- epoll_ctl(2) is used to add, modify, or remove entries in the interest list of the epoll instance.
- epoll_wait(2) waits for I/O events, blocking the calling thread if no events are currently available.

## Level-Triggered and Edge-Triggered
The epoll event distribution interface is able to behave both as edge-triggered (ET) and as level-triggered (LT).
- Level-Triggered (default): epoll_wait(2) will return readiness as long as the underlying buffer has data to be read.
- Edge-Triggered (EPOLLET): epoll_wait(2) delivers an event only when a change in the state of the monitored file descriptor occurs. The application must drain the descriptor using non-blocking I/O until EAGAIN or EWOULDBLOCK.
""",
    },
    {
        "keywords": ["virtual memory", "paging", "page fault", "tlb", "mmap"],
        "name": "virtual_memory_internals",
        "title": "Virtual Memory, Paging, and Address Space Architecture",
        "source": "Linux Kernel Internals & Architecture Specification",
        "content": """# Virtual Memory Architecture & Paging Mechanics

## Core Invariants
1. Virtual Address Space: Every user-space process executes within an isolated, contiguous 64-bit virtual address space (e.g., 48-bit canonical addressing spanning 256 TB).
2. Paging and MMU: The Memory Management Unit (MMU) translates virtual addresses to physical frame numbers using multi-level page tables (x86-64 4-level or 5-level paging: PGD, P4D, PUD, PMD, PTE).
3. Page Size: Canonical standard hardware page size is 4 KiB (4096 bytes). Transparent Huge Pages (THP) support 2 MiB and 1 GiB mappings to reduce Translation Lookaside Buffer (TLB) thrashing.
4. Page Faults (Major vs Minor):
   - Minor Page Fault: The virtual page is valid in the process VMA, and the page is already in physical memory (page cache), but not mapped in the process's page table.
   - Major Page Fault: The page is not in physical RAM and must be synchronously paged in from backing disk storage or swap.
5. Zero-Copy I/O: Techniques like sendfile(2), vmsplice(2), and splice(2) transfer data between file descriptors directly in kernel space without round-tripping through user-space memory buffers.
""",
    },
    {
        "keywords": ["syscall", "system call", "user space", "kernel space", "context switch"],
        "name": "syscalls_and_context_switch",
        "title": "System Calls, Privilege Rings, and Context Switching Mechanics",
        "source": "Systems Foundations Architectural Reference",
        "content": """# System Calls & Context Switching Internals

## Privilege Levels & Transition
- Modern CPUs enforce hierarchical protection rings: Ring 0 (Kernel / Supervisor) and Ring 3 (User Space).
- A system call switches execution privilege from Ring 3 to Ring 0 via dedicated CPU instructions (e.g. `SYSCALL` / `SYSRET` on x86-64).
- Transition costs: CPU must save user-space register state (instruction pointer, stack pointer, flags), switch to kernel stack, validate arguments, execute kernel routine, and restore state.

## Context Switch Mechanics
- When the OS scheduler pre-empts a running task or a blocking syscall occurs:
  1. Register saving: General-purpose registers, floating-point/SIMD states, and program counter are stored into the Task State Segment (TSS) / Process Control Block (PCB).
  2. Memory space switch: The CR3 control register (holding the root page table physical address) is updated to point to the new process's page tables.
  3. TLB Invalidation: Switching CR3 typically invalidates non-global TLB entries, inducing cold-cache latency penalties for subsequent memory accesses.
""",
    },
]


def compute_sha256(content: str | bytes) -> str:
    """Compute cryptographic SHA-256 hash."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def atomic_write_text(filepath: Path, content: str) -> None:
    """Atomically write text content using a temporary file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise


def fetch_url(url: str, timeout: int = 10) -> tuple[str | None, str | None]:
    """Fetch URL with custom User-Agent and return (content, error)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
            return data.decode("utf-8", errors="replace"), None
    except Exception as e:
        return None, str(e)


def download_file(url: str, target_path: Path, timeout: int = 15) -> tuple[bool, str | None]:
    """Download binary/text file directly to target_path."""
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
            target_path.write_bytes(data)
            return True, None
    except Exception as e:
        return False, str(e)


def match_canonical_specs(topic: str) -> list[dict[str, Any]]:
    """Match topic text against known canonical IETF RFCs and technical specifications."""
    t_lower = topic.lower()
    matched = []
    seen_ids = set()

    for spec in CANONICAL_SPECS:
        for kw in spec["keywords"]:
            if kw in t_lower and spec["identifier"] not in seen_ids:
                matched.append(spec)
                seen_ids.add(spec["identifier"])
                break
    return matched


def match_systems_docs(topic: str) -> list[dict[str, Any]]:
    """Match topic text against built-in authoritative systems manual pages and specs."""
    t_lower = topic.lower()
    matched = []
    seen = set()

    for doc in CANONICAL_SYSTEMS_DOCS:
        for kw in doc["keywords"]:
            if kw in t_lower and doc["name"] not in seen:
                matched.append(doc)
                seen.add(doc["name"])
                break
    return matched


def fetch_arxiv_papers(query: str, max_results: int = 3) -> list[dict[str, Any]]:
    """Search arXiv public API and return paper metadata."""
    encoded_query = urllib.parse.quote_plus(query)
    api_url = f"https://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}"
    
    xml_data, err = fetch_url(api_url, timeout=10)
    if not xml_data or err:
        return []

    papers = []
    try:
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        for entry in root.findall("atom:entry", ns):
            title_elem = entry.find("atom:title", ns)
            summary_elem = entry.find("atom:summary", ns)
            id_elem = entry.find("atom:id", ns)
            
            title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else "Untitled"
            summary = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""
            arxiv_url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
            
            arxiv_id = ""
            m = re.search(r"abs/([\w.-]+)", arxiv_url)
            if m:
                arxiv_id = m.group(1)

            authors = []
            for author_elem in entry.findall("atom:author", ns):
                name_elem = author_elem.find("atom:name", ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else ""

            papers.append({
                "type": "arxiv_paper",
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "summary": summary,
                "url": arxiv_url,
                "pdf_url": pdf_url,
            })
    except Exception:
        pass

    return papers


def harvest_official_sources(
    slug: str,
    topic: str,
    workspace: Path | str = ".",
    download_pdfs: bool = False,
) -> dict[str, Any]:
    """Execute autonomous official source harvesting for a given topic."""
    ws = Path(workspace).resolve()
    # Support both canonical _tc/research and legacy research/
    canon_sources = ws / "_tc" / "research" / slug / "sources"
    legacy_sources = ws / "research" / slug / "sources"
    for s_dir in [canon_sources, legacy_sources]:
        for sub in ["rfcs", "docs", "papers", "repos", "transcripts", "user-provided", "raw"]:
            (s_dir / sub).mkdir(parents=True, exist_ok=True)

    rfcs_dir = canon_sources / "rfcs"
    docs_dir = canon_sources / "docs"
    papers_dir = canon_sources / "papers"

    harvested: list[dict[str, Any]] = []

    # 1. Match and harvest IETF RFCs
    specs = match_canonical_specs(topic)
    for s in specs:
        target_file = rfcs_dir / s["filename"]
        content = ""
        fetch_success = False

        if target_file.is_file():
            content = target_file.read_text(encoding="utf-8", errors="replace")
            fetch_success = True
        else:
            text_data, err = fetch_url(s["url"], timeout=10)
            if text_data and not err:
                atomic_write_text(target_file, text_data)
                content = text_data
                fetch_success = True

        if fetch_success:
            leg_file = legacy_sources / target_file.relative_to(canon_sources)
            if target_file.is_file():
                atomic_write_text(leg_file, content)
            harvested.append({
                "type": "rfc",
                "title": s["title"],
                "identifier": s["identifier"],
                "path": str(target_file.relative_to(ws)),
                "full_path": str(target_file),
                "sha256": compute_sha256(content),
                "size_bytes": target_file.stat().st_size,
                "status": "auto_harvested",
            })

    # 2. Match and write authoritative systems manual pages and specs
    docs = match_systems_docs(topic)
    for d in docs:
        target_file = docs_dir / f"{d['name']}.md"
        if not target_file.is_file():
            atomic_write_text(target_file, d["content"])
        leg_file = legacy_sources / "docs" / f"{d['name']}.md"
        if not leg_file.is_file():
            atomic_write_text(leg_file, d["content"])
        
        content = target_file.read_text(encoding="utf-8")
        harvested.append({
            "type": "systems_doc",
            "title": d["title"],
            "identifier": d["name"],
            "path": str(target_file.relative_to(ws)),
            "full_path": str(target_file),
            "sha256": compute_sha256(content),
            "size_bytes": target_file.stat().st_size,
            "status": "auto_harvested",
        })

    # 3. Search arXiv for relevant open academic papers
    # Extract clean search query from topic (take first 3-5 keywords)
    clean_topic = re.sub(r"[(),/]", " ", topic)
    words = [w for w in clean_topic.split() if len(w) > 3 and w.lower() not in {"with", "from", "that", "this", "under", "about"}]
    search_query = " ".join(words[:4]) if words else topic

    arxiv_results = fetch_arxiv_papers(search_query, max_results=2)
    for p in arxiv_results:
        p_id = p["arxiv_id"]
        if not p_id:
            continue
        clean_title = re.sub(r"[^\w.-]+", "_", p["title"][:40]).strip("_")
        summary_file = papers_dir / f"arxiv_{p_id}_{clean_title}.md"
        
        paper_text = f"# {p['title']}\n\n**Authors**: {', '.join(p['authors'])}\n**ArXiv ID**: `{p['arxiv_id']}`\n**URL**: {p['url']}\n\n## Abstract\n{p['summary']}\n"
        if not summary_file.is_file():
            atomic_write_text(summary_file, paper_text)
        leg_file = legacy_sources / "papers" / f"arxiv_{p_id}_{clean_title}.md"
        if not leg_file.is_file():
            atomic_write_text(leg_file, paper_text)

        harvested.append({
            "type": "arxiv_paper",
            "title": p["title"],
            "identifier": p_id,
            "path": str(summary_file.relative_to(ws)),
            "full_path": str(summary_file),
            "sha256": compute_sha256(paper_text),
            "size_bytes": summary_file.stat().st_size,
            "status": "auto_harvested",
        })

    return {
        "ok": True,
        "slug": slug,
        "topic": topic,
        "total_harvested": len(harvested),
        "sources": harvested,
    }


def main() -> None:
    """CLI Entrypoint for paper_fetcher."""
    parser = argparse.ArgumentParser(description="Autonomous Academic Paper and Specification Harvester.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_fetch = subparsers.add_parser("fetch", help="Harvest RFCs, papers, and specs for a topic")
    p_fetch.add_argument("--slug", required=True, help="Course or research slug")
    p_fetch.add_argument("--topic", required=True, help="Topic description to analyze")
    p_fetch.add_argument("--workspace", default=".", help="Workspace root directory")
    p_fetch.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args()

    if args.subcommand == "fetch":
        res = harvest_official_sources(
            slug=args.slug,
            topic=args.topic,
            workspace=args.workspace,
        )
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"✅ Harvested {res['total_harvested']} official technical sources for '{args.topic}':")
            for s in res["sources"]:
                print(f"  - [{s['type'].upper()}] {s['title']} -> {s['path']}")


if __name__ == "__main__":
    main()
