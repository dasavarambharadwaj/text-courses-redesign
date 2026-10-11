#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""dag.py — Deterministic prerequisite DAG validator and cycle checker for TextCourses.

Validates curriculum prerequisite dependency graphs using standard library
graphlib.TopologicalSorter to detect cycles (CycleError) and missing antecedent
references at zero token cost (AD-4, FR-7, FR-8).
"""

from __future__ import annotations

import argparse
import graphlib
import json
import sys
import tomllib
from pathlib import Path
from typing import Any


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def resolve_manifest_path(path_arg: str | Path) -> Path:
    """Resolve course manifest file from path argument."""
    p = Path(path_arg)
    if p.is_dir():
        manifest = p / "course.toml"
        if manifest.exists():
            return manifest
        return p / "course.toml"
    return p


def load_manifest(path: Path) -> dict[str, Any]:
    """Safely load and parse TOML manifest."""
    if not path.exists():
        output_json({
            "ok": False,
            "error": f"Manifest not found: {path}",
        }, exit_code=1)
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        output_json({
            "ok": False,
            "error": f"Malformed TOML in {path}: {e}",
        }, exit_code=1)
    except Exception as e:
        output_json({
            "ok": False,
            "error": f"Failed to read manifest {path}: {e}",
        }, exit_code=1)
    return {}


def extract_prereqs(entity: dict[str, Any]) -> list[Any]:
    """Extract list of prerequisites from an entity dict."""
    for key in ("prerequisites", "prereqs", "dependencies", "after"):
        val = entity.get(key)
        if val is not None:
            if isinstance(val, list):
                return list(val)
            if isinstance(val, (str, int)):
                return [val]
    return []


def build_graph(data: dict[str, Any]) -> tuple[dict[Any, list[Any]], str | None]:
    """Build directed dependency graph mapping node -> list of dependencies.
    
    Returns (graph, missing_prereq_id_if_any).
    If an antecedent is referenced that does not exist, returns (graph, missing_id).
    """
    # 1. Direct DAG / prerequisites table at top level
    for key in ("dag", "prerequisites", "dependencies"):
        if key in data and isinstance(data[key], dict):
            raw_table: dict[Any, Any] = data[key]
            # Verify all keys and dependencies
            all_defined = set(raw_table.keys())
            graph: dict[Any, list[Any]] = {}
            for node, deps in raw_table.items():
                deps_list = deps if isinstance(deps, list) else [deps]
                for d in deps_list:
                    if d not in all_defined:
                        return {}, str(d)
                graph[node] = list(deps_list)
            return graph, None

    chapters = data.get("chapters", [])
    if not isinstance(chapters, list):
        return {}, None

    # Check if any sections have prerequisites declared
    has_section_prereqs = False
    all_sections: list[tuple[dict[str, Any], dict[str, Any]]] = []  # (ch, sec)
    for ch in chapters:
        for sec in ch.get("sections", []):
            all_sections.append((ch, sec))
            if extract_prereqs(sec):
                has_section_prereqs = True

    # Check if any chapters have prerequisites declared
    has_chapter_prereqs = any(extract_prereqs(ch) for ch in chapters)

    # CASE A: Section-level graph
    if has_section_prereqs or (all_sections and not has_chapter_prereqs):
        # Inspect types of prerequisites used to choose canonical node identifier
        sample_prereq: Any = None
        for _, sec in all_sections:
            pr = extract_prereqs(sec)
            if pr:
                sample_prereq = pr[0]
                break

        use_int_id = isinstance(sample_prereq, int)
        use_slug = isinstance(sample_prereq, str) and not (sample_prereq.isdigit() or "." in sample_prereq)

        # Build alias map -> canonical node
        alias_map: dict[Any, Any] = {}
        canonical_nodes: list[Any] = []
        graph = {}

        for ch, sec in all_sections:
            sec_id = sec.get("id")
            sec_slug = sec.get("slug")
            ch_id = ch.get("id")
            ch_slug = ch.get("slug")

            # Determine canonical node representation
            if use_int_id and sec_id is not None:
                canon = sec_id
            elif use_slug and sec_slug:
                canon = sec_slug
            elif sec_slug:
                canon = sec_slug
            elif sec_id is not None:
                canon = sec_id
            else:
                canon = f"{ch_id}.{sec_id}"

            canonical_nodes.append(canon)
            graph[canon] = []

            # Register aliases
            if sec_id is not None:
                alias_map[sec_id] = canon
                alias_map[str(sec_id)] = canon
            if sec_slug:
                alias_map[sec_slug] = canon
            if ch_id is not None and sec_id is not None:
                alias_map[f"{ch_id}.{sec_id}"] = canon
                alias_map[f"{ch_id}:{sec_id}"] = canon
            if ch_slug and sec_slug:
                alias_map[f"{ch_slug}/{sec_slug}"] = canon
            if ch_slug and sec_id is not None:
                alias_map[f"{ch_slug}/{sec_id}"] = canon

        # Resolve prerequisites for each section
        for ch, sec in all_sections:
            sec_id = sec.get("id")
            sec_slug = sec.get("slug")
            canon = alias_map.get(sec_slug) or alias_map.get(sec_id)
            if canon is None:
                continue

            prereqs = extract_prereqs(sec)
            for p in prereqs:
                if p not in alias_map:
                    return {}, str(p)
                resolved = alias_map[p]
                graph[canon].append(resolved)

        return graph, None

    # CASE B: Chapter-level graph
    sample_ch_prereq: Any = None
    for ch in chapters:
        pr = extract_prereqs(ch)
        if pr:
            sample_ch_prereq = pr[0]
            break

    use_ch_int = isinstance(sample_ch_prereq, int)
    use_ch_slug = isinstance(sample_ch_prereq, str) and not sample_ch_prereq.isdigit()

    alias_map = {}
    graph = {}

    for ch in chapters:
        ch_id = ch.get("id")
        ch_slug = ch.get("slug")

        if use_ch_int and ch_id is not None:
            canon = ch_id
        elif use_ch_slug and ch_slug:
            canon = ch_slug
        elif ch_slug:
            canon = ch_slug
        elif ch_id is not None:
            canon = ch_id
        else:
            canon = str(len(graph) + 1)

        graph[canon] = []

        if ch_id is not None:
            alias_map[ch_id] = canon
            alias_map[str(ch_id)] = canon
            alias_map[f"chapter-{ch_id}"] = canon
            alias_map[f"ch-{ch_id}"] = canon
        if ch_slug:
            alias_map[ch_slug] = canon

    for ch in chapters:
        ch_id = ch.get("id")
        ch_slug = ch.get("slug")
        canon = alias_map.get(ch_slug) or alias_map.get(ch_id)
        if canon is None:
            continue

        prereqs = extract_prereqs(ch)
        for p in prereqs:
            if p not in alias_map:
                return {}, str(p)
            resolved = alias_map[p]
            graph[canon].append(resolved)

    return graph, None


def validate_dag(path: Path) -> dict[str, Any]:
    """Validate prerequisite DAG and return topological build order."""
    data = load_manifest(path)
    graph, missing = build_graph(data)

    if missing is not None:
        output_json({
            "ok": False,
            "error": f"Missing prerequisite: '{missing}' does not exist in curriculum",
            "missing": missing,
        }, exit_code=1)

    try:
        ts = graphlib.TopologicalSorter(graph)
        order = list(ts.static_order())
    except graphlib.CycleError as e:
        cycle_nodes = list(e.args[1]) if len(e.args) > 1 else []
        output_json({
            "ok": False,
            "error": "Circular dependency detected",
            "cycle": cycle_nodes,
        }, exit_code=1)

    return {
        "ok": True,
        "valid": True,
        "order": order,
        "total_nodes": len(order),
        "path": str(path),
    }


def cmd_validate(args: argparse.Namespace) -> None:
    """Handle validate subcommand."""
    manifest_path = resolve_manifest_path(args.path)
    result = validate_dag(manifest_path)
    output_json(result, exit_code=0)


def cmd_order(args: argparse.Namespace) -> None:
    """Handle order subcommand."""
    manifest_path = resolve_manifest_path(args.path)
    result = validate_dag(manifest_path)
    output_json({
        "ok": True,
        "order": result["order"],
        "total_nodes": result["total_nodes"],
        "path": result["path"],
    }, exit_code=0)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TextCourses deterministic prerequisite DAG validator and cycle checker"
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate prerequisite DAG for cycles and missing antecedents")
    p_validate.add_argument("--path", required=True, help="Path to course.toml manifest or course directory")
    p_validate.set_defaults(func=cmd_validate)

    # order
    p_order = subparsers.add_parser("order", help="Output topological build order for curriculum nodes")
    p_order.add_argument("--path", required=True, help="Path to course.toml manifest or course directory")
    p_order.set_defaults(func=cmd_order)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
