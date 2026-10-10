#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""auditor.py — Pre-flight curriculum auditor and vocabulary validator for TextCourses.

Validates curriculum DAG acyclicity, verifies vocabulary introduction contracts across
topological sequences, and cross-checks proposed topic coverage against research digests
before committing courses to disk (FR-7, AD-4).
"""

from __future__ import annotations

import argparse
import graphlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

VALID_ARCHETYPES = {
    "applied_creation",
    "forensic_dilemma",
    "axiomatic_primitives",
    "spiral_immersion",
    "reverse_engineering",
}


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def load_manifest_data(path_or_str: Path | str) -> tuple[dict[str, Any], Path | None]:
    """Load course manifest from file path or raw JSON/TOML string."""
    candidate = Path(path_or_str)
    if candidate.exists():
        if candidate.is_dir():
            target = candidate / "course.toml"
            if not target.exists():
                raise FileNotFoundError(f"No course.toml found in {candidate}")
            candidate = target

        text = candidate.read_text(encoding="utf-8")
        if candidate.suffix.lower() == ".toml":
            return tomllib.loads(text), candidate
        else:
            return json.loads(text), candidate

    # Try parsing string directly as JSON
    try:
        return json.loads(str(path_or_str)), None
    except Exception:
        raise FileNotFoundError(f"Manifest path not found: {path_or_str}")


def audit_curriculum(
    manifest_source: Path | str,
    research_slug: str | None = None,
    workspace: Path | str = ".",
) -> dict[str, Any]:
    """Execute pre-flight audit of course manifest, DAG, vocabulary, and research fidelity."""
    ws = Path(workspace).resolve()
    data, manifest_path = load_manifest_data(manifest_source)

    findings: list[dict[str, Any]] = []

    # 1. Schema & Archetype validation
    course_info = data.get("course", {})
    if not isinstance(course_info, dict):
        findings.append({
            "severity": "CRITICAL",
            "code": "SCHEMA_ERROR",
            "message": "Missing [course] table in manifest",
            "target": "course",
        })
        course_id = "unknown"
        archetype = ""
    else:
        course_id = course_info.get("id", "unknown")
        archetype = course_info.get("archetype", "")
        if archetype and archetype not in VALID_ARCHETYPES:
            findings.append({
                "severity": "CRITICAL",
                "code": "INVALID_ARCHETYPE",
                "message": f"Archetype '{archetype}' is invalid. Must be one of {sorted(VALID_ARCHETYPES)}",
                "target": "course.archetype",
            })

    chapters = data.get("chapters", [])
    if not isinstance(chapters, list) or not chapters:
        findings.append({
            "severity": "CRITICAL",
            "code": "NO_CHAPTERS",
            "message": "Curriculum must declare at least one chapter in [[chapters]]",
            "target": "chapters",
        })

    # Collect sections and index
    all_sections: list[dict[str, Any]] = []
    section_map: dict[str, dict[str, Any]] = {}
    dep_graph: dict[str, list[str]] = {}

    for ch in chapters if isinstance(chapters, list) else []:
        ch_id = str(ch.get("id", ""))
        for sec in ch.get("sections", []):
            sec_id = str(sec.get("id", ""))
            if not sec_id:
                sec_id = f"{ch_id}:{len(all_sections)}"
            sec_record = dict(sec)
            sec_record["_ch_id"] = ch_id
            all_sections.append(sec_record)
            section_map[sec_id] = sec_record

            # Extract prerequisites
            prereqs = sec.get("prerequisites") or sec.get("after") or []
            if isinstance(prereqs, (str, int)):
                prereqs = [str(prereqs)]
            elif isinstance(prereqs, list):
                prereqs = [str(p) for p in prereqs]
            else:
                prereqs = []
            dep_graph[sec_id] = prereqs

    # 2. Prerequisite DAG Cycle & Reference Check
    # Verify antecedent existence
    for sec_id, prereqs in dep_graph.items():
        for p in prereqs:
            if p not in section_map:
                findings.append({
                    "severity": "CRITICAL",
                    "code": "MISSING_PREREQUISITE",
                    "message": f"Section '{sec_id}' depends on non-existent prerequisite '{p}'",
                    "target": sec_id,
                })

    topological_order: list[str] = []
    cycle_detected = False
    ts = graphlib.TopologicalSorter()
    for sec_id, prereqs in dep_graph.items():
        # filter to valid nodes for cycle check
        valid_prereqs = [p for p in prereqs if p in section_map]
        ts.add(sec_id, *valid_prereqs)

    try:
        ts.prepare()
        while ts.is_active():
            ready = ts.get_ready()
            for node in ready:
                topological_order.append(node)
                ts.done(node)
    except graphlib.CycleError as ce:
        cycle_detected = True
        cycle_nodes = list(ce.args[1]) if len(ce.args) > 1 else []
        cycle_path = " -> ".join(str(n) for n in cycle_nodes)
        findings.append({
            "severity": "CRITICAL",
            "code": "DAG_CYCLE",
            "message": f"Prerequisite dependency cycle detected: {cycle_path}",
            "target": str(cycle_nodes[0]) if cycle_nodes else "dag",
        })

    # If no explicit prerequisites were declared, default to linear chapter order
    if not topological_order and not cycle_detected and all_sections:
        topological_order = [str(s.get("id", idx)) for idx, s in enumerate(all_sections)]

    # 3. Vocabulary Contract Audit
    if not cycle_detected:
        cumulative_vocabulary: set[str] = set()

        for sec_id in topological_order:
            sec_data = section_map.get(sec_id, {})
            vocab_prereqs = sec_data.get("vocabulary_prerequisites") or sec_data.get("prereq_vocabulary") or []
            if isinstance(vocab_prereqs, str):
                vocab_prereqs = [vocab_prereqs]

            vocab_introduced = sec_data.get("vocabulary_introduced") or sec_data.get("introduces") or []
            if isinstance(vocab_introduced, str):
                vocab_introduced = [vocab_introduced]

            # Check that required vocabulary has been introduced earlier
            for term in vocab_prereqs:
                norm_term = term.strip().lower()
                if norm_term not in cumulative_vocabulary:
                    findings.append({
                        "severity": "CRITICAL",
                        "code": "PREMATURE_VOCABULARY",
                        "message": f"Section '{sec_id}' requires prerequisite vocabulary '{term}', but it has not been introduced in any prerequisite section.",
                        "target": sec_id,
                    })

            # Check for duplicate introduction
            for term in vocab_introduced:
                norm_term = term.strip().lower()
                if norm_term in cumulative_vocabulary:
                    findings.append({
                        "severity": "WARNING",
                        "code": "DUPLICATE_VOCABULARY",
                        "message": f"Section '{sec_id}' re-introduces vocabulary term '{term}' which was already introduced earlier.",
                        "target": sec_id,
                    })
                cumulative_vocabulary.add(norm_term)

    # 4. Research Digest Cross-Check
    target_slug = research_slug or course_id
    digest_path = ws / ".tc" / "research" / target_slug / "digest.json"
    if digest_path.is_file():
        try:
            digest = json.loads(digest_path.read_text(encoding="utf-8"))
            confidence = digest.get("confidence", "unverified")

            if confidence == "unverified":
                findings.append({
                    "severity": "WARNING",
                    "code": "RESEARCH_UNVERIFIED",
                    "message": f"Research digest for '{target_slug}' has 'unverified' confidence.",
                    "target": target_slug,
                })

            research_headings = {h.get("title", "").lower() for h in digest.get("toc", [])}
            research_apis = {a.get("name", "").lower() for a in digest.get("api_index", [])}
            research_vocab = {v.lower() for v in digest.get("vocabulary", [])}
            all_research_terms = research_headings | research_apis | research_vocab

            # Check for course grounding
            for sec_record in all_sections:
                sec_title = sec_record.get("title", "").lower()
                sec_id = sec_record.get("id", "")
                vocab_introduced = [t.lower() for t in (sec_record.get("vocabulary_introduced") or [])]

                # Check if section title or vocabulary has overlap with research
                matched = any(term in sec_title for term in all_research_terms) or any(
                    v in all_research_terms for v in vocab_introduced
                )
                if all_research_terms and not matched and vocab_introduced:
                    findings.append({
                        "severity": "INFO",
                        "code": "UNGROUNDED_TOPIC",
                        "message": f"Section '{sec_id}' ({sec_record.get('title')}) introduces terms not found in research digest.",
                        "target": sec_id,
                    })
        except Exception as e:
            findings.append({
                "severity": "WARNING",
                "code": "RESEARCH_PARSE_ERROR",
                "message": f"Failed to parse research digest at {digest_path}: {e}",
                "target": target_slug,
            })

    critical_count = sum(1 for f in findings if f["severity"] == "CRITICAL")
    warning_count = sum(1 for f in findings if f["severity"] == "WARNING")
    info_count = sum(1 for f in findings if f["severity"] == "INFO")

    is_ok = (critical_count == 0)

    return {
        "ok": is_ok,
        "course_id": course_id,
        "archetype": archetype,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "findings": findings,
        "topological_order": topological_order,
        "total_sections": len(all_sections),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="auditor.py",
        description="TextCourses pre-flight curriculum auditor and vocabulary contract validator.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_audit = subparsers.add_parser("audit", help="Audit curriculum manifest DAG and vocabulary contracts.")
    p_audit.add_argument("--manifest", required=True, help="Path to course.toml, manifest JSON, or course directory.")
    p_audit.add_argument("--research-slug", default=None, help="Optional research slug to cross-check against.")
    p_audit.add_argument("--workspace", default=".", help="Path to workspace root.")
    p_audit.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    try:
        if args.subcommand == "audit":
            result = audit_curriculum(
                manifest_source=args.manifest,
                research_slug=args.research_slug,
                workspace=args.workspace,
            )
            exit_code = 0 if result["ok"] else 1
            output_json(result, exit_code)
        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except Exception as e:
        output_json({"error": str(e), "ok": False}, 1)


if __name__ == "__main__":
    main()
