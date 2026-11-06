#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""toc_aligner.py — Macro Semantic TOC Alignment & Multi-Source Deduplication.

Extracts Table of Contents ASTs across heterogeneous peer sources (PDFs, EPUBs, Markdown),
clusters overlapping domain primitives, preserves source-unique niche topics, and constructs
a unified topological master DAG where common concepts are taught exactly once.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print dictionary as formatted JSON and exit."""
    print(json.dumps(data, indent=2, ensure_ascii=False))
    sys.exit(exit_code)


def extract_toc_from_markdown(md_path: Path | str) -> list[dict[str, Any]]:
    """Extract hierarchical Table of Contents with line ranges from a markdown file."""
    p = Path(md_path).resolve()
    if not p.is_file():
        return []

    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    entries: list[dict[str, Any]] = []

    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

    current_entry: dict[str, Any] | None = None

    for idx, line in enumerate(lines, start=1):
        m = heading_pattern.match(line.strip())
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()

            if current_entry:
                current_entry["line_end"] = idx - 1
                entries.append(current_entry)

            current_entry = {
                "title": title,
                "level": level,
                "line_start": idx,
                "line_end": len(lines),  # provisional
            }

    if current_entry:
        current_entry["line_end"] = len(lines)
        entries.append(current_entry)

    return entries


SYNONYM_CLUSTERS: dict[str, list[str]] = {
    "bw_trees": ["bw-tree", "bw tree", "bwtree"],
    "lsm_trees": ["lsm", "log-structured merge", "sstable", "compaction", "memtable"],
    "b_trees": ["b-tree", "btree", "b+ tree", "page-based storage", "b-trees"],
    "leader_election": ["leader election", "primary election", "master election", "requestvote", "split-vote"],
    "log_replication": ["log replication", "appendentries", "replicated log", "state machine replication"],
    "distributed_transactions": ["two-phase commit", "2pc", "three-phase commit", "distributed transaction", "consensus commit"],
    "quorum_consensus": ["quorum", "majority voting", "read quorum", "write quorum", "paxos", "raft"],
    "data_partitioning": ["sharding", "partitioning", "consistent hashing", "hash partitioning", "range partitioning"],
    "clock_synchronization": ["vector clock", "lamport timestamp", "logical clock", "trueclock", "ntp"],
    "isolation_levels": ["acid", "serializability", "snapshot isolation", "read committed", "repeatable read"],
}


def normalize_topic_key(title: str) -> str:
    """Normalize a section title into a semantic canonical key."""
    clean = re.sub(r"^[0-9IVXLCDM\.\-\s]+", "", title).lower()
    clean = re.sub(r"[^\w\s\-]", "", clean)

    for canonical, keywords in SYNONYM_CLUSTERS.items():
        for kw in keywords:
            if kw in clean:
                return canonical

    # Fallback to alphanumeric slug
    slug = re.sub(r"[\s\-]+", "_", clean).strip("_")
    return slug[:40] if slug else "general_topic"


def cluster_multi_source_tocs(sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Cluster TOC trees across multiple sources, identifying common vs niche topics."""
    topic_map: dict[str, dict[str, Any]] = {}

    for src in sources:
        src_id = src.get("id") or Path(src.get("file", "unknown")).stem
        toc = src.get("toc") or []

        for item in toc:
            title = item["title"]
            if item.get("level", 1) == 1 and ("table of contents" in title.lower() or "preface" in title.lower()):
                continue

            canon_key = normalize_topic_key(title)

            if canon_key not in topic_map:
                topic_map[canon_key] = {
                    "canonical_id": canon_key,
                    "representative_title": title,
                    "occurrences": [],
                    "is_common": False,
                }

            topic_map[canon_key]["occurrences"].append({
                "source_id": src_id,
                "source_file": src.get("file"),
                "section_title": title,
                "level": item.get("level", 2),
                "line_start": item.get("line_start", 1),
                "line_end": item.get("line_end", 1),
            })

    common_topics: list[dict[str, Any]] = []
    niche_topics: list[dict[str, Any]] = []

    for key, data in topic_map.items():
        unique_sources = {occ["source_id"] for occ in data["occurrences"]}
        if len(unique_sources) > 1:
            data["is_common"] = True
            data["dialectic_potential"] = True
            common_topics.append(data)
        else:
            data["is_common"] = False
            data["dialectic_potential"] = False
            niche_topics.append(data)

    return {
        "total_canonical_topics": len(topic_map),
        "common_topics_count": len(common_topics),
        "niche_topics_count": len(niche_topics),
        "common_topics": common_topics,
        "niche_topics": niche_topics,
        "all_topics": list(topic_map.values()),
    }


def build_unified_dag(sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Synthesize a unified, deduplicated DAG curriculum outline across all peer sources."""
    clustered = cluster_multi_source_tocs(sources)
    all_topics = clustered["all_topics"]

    # Topological sequencing heuristics:
    # Foundations (storage, single-node) -> Replication & Consensus -> Partitions & Scale -> Advanced & Niche
    tier_priorities: dict[str, int] = {
        "b_trees": 1,
        "lsm_trees": 1,
        "isolation_levels": 2,
        "log_replication": 2,
        "quorum_consensus": 3,
        "leader_election": 3,
        "clock_synchronization": 4,
        "data_partitioning": 4,
        "distributed_transactions": 5,
    }

    def _sort_key(topic: dict[str, Any]) -> tuple[int, int, str]:
        cid = topic["canonical_id"]
        priority = tier_priorities.get(cid, 10)
        # Common topics prioritized before niche within same tier
        common_weight = 0 if topic.get("is_common") else 1
        return (priority, common_weight, topic["representative_title"])

    sorted_topics = sorted(all_topics, key=_sort_key)

    # Group into chapters
    chapters: list[dict[str, Any]] = []
    chunk_size = 3  # 3-4 sections per chapter
    for i in range(0, len(sorted_topics), chunk_size):
        ch_topics = sorted_topics[i : i + chunk_size]
        ch_num = (i // chunk_size) + 1
        ch_title = f"Module {ch_num:02d}: " + " & ".join(t["representative_title"][:25] for t in ch_topics[:2])
        chapters.append({
            "chapter_id": f"module-{ch_num:02d}",
            "title": ch_title,
            "sections": [
                {
                    "section_id": t["canonical_id"],
                    "title": t["representative_title"],
                    "is_common_across_sources": t["is_common"],
                    "dialectic": t.get("dialectic_potential", False),
                    "sources": t["occurrences"],
                }
                for t in ch_topics
            ],
        })

    return {
        "ok": True,
        "total_sources_ingested": len(sources),
        "total_deduplicated_sections": len(sorted_topics),
        "common_sections_count": clustered["common_topics_count"],
        "niche_sections_count": clustered["niche_topics_count"],
        "curriculum_dag": chapters,
    }


def align_sources_in_directory(source_dir: Path | str) -> dict[str, Any]:
    """Scan directory of raw markdown sources and construct unified DAG."""
    sdir = Path(source_dir).resolve()
    if not sdir.is_dir():
        return {"ok": False, "error": f"Sources directory not found: {sdir}"}

    md_files = list(sdir.glob("*.md"))
    if not md_files:
        return {"ok": False, "error": f"No markdown source files found in {sdir}"}

    sources_data: list[dict[str, Any]] = []
    for mf in md_files:
        toc = extract_toc_from_markdown(mf)
        sources_data.append({
            "id": mf.stem,
            "file": str(mf),
            "toc": toc,
        })

    dag_result = build_unified_dag(sources_data)
    dag_result["sources_directory"] = str(sdir)
    return dag_result


def main() -> None:
    parser = argparse.ArgumentParser(description="toc_aligner.py — Macro Semantic TOC Alignment & Multi-Source Deduplication")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_align = subparsers.add_parser("align", help="Align and deduplicate multiple sources in a directory")
    p_align.add_argument("--sources", "-s", required=True, help="Path to directory containing extracted markdown sources")
    p_align.add_argument("--output", "-o", help="Optional output JSON path for curriculum DAG")
    p_align.add_argument("--json", action="store_true", help="Output JSON to stdout")

    args = parser.parse_args()

    if args.subcommand == "align":
        res = align_sources_in_directory(args.sources)
        if args.output and res.get("ok"):
            out_p = Path(args.output).resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

        if args.json or not args.output:
            output_json(res, 0 if res.get("ok") else 1)
        else:
            print(f"✅ Aligned {res.get('total_sources_ingested')} sources into {res.get('total_deduplicated_sections')} deduplicated sections.")


if __name__ == "__main__":
    main()
