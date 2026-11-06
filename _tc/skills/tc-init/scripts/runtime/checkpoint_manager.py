#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""checkpoint_manager.py — Interactive Checkpoint Gates & Material Acquisition Pause.

Enforces step-by-step interactive human checkpoints during course lifecycle (CAP-2):
1. Material Acquisition Gate: Pauses when landmark/gold-standard textbooks are missing,
   giving learner the choice to drop PDF/EPUB or proceed with open docs.
2. Curriculum Approval Gate: Pauses after multi-source synthesis to review the syllabus
   and deliberation summary before scaffolding/starting lesson 1.
3. Action Fork Gate: Preserves fast-decision control bar at every teaching turn.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

CHECKPOINT_FILE = ".tc/checkpoint.json"

GATE_ACQUISITION = "acquisition_gate"
GATE_SOURCE_PROPOSAL = "source_proposal"
GATE_APPROVAL = "approval_gate"
GATE_ACTION_FORK = "action_fork"


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print dictionary as formatted JSON and exit."""
    print(json.dumps(data, indent=2, ensure_ascii=False))
    sys.exit(exit_code)


def get_checkpoint_path(workspace: Path | str) -> Path:
    """Return path to checkpoint file in workspace root."""
    ws = Path(workspace).resolve()
    return ws / CHECKPOINT_FILE


def load_checkpoint(workspace: Path | str) -> dict[str, Any] | None:
    """Load active checkpoint if pending in workspace."""
    cp_path = get_checkpoint_path(workspace)
    if not cp_path.is_file():
        return None
    try:
        return json.loads(cp_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_checkpoint(workspace: Path | str, checkpoint_data: dict[str, Any]) -> None:
    """Persist checkpoint state to .tc/checkpoint.json."""
    cp_path = get_checkpoint_path(workspace)
    cp_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cp_path.write_text(json.dumps(checkpoint_data, indent=2), encoding="utf-8")


def clear_checkpoint(workspace: Path | str) -> None:
    """Clear active checkpoint from workspace."""
    cp_path = get_checkpoint_path(workspace)
    if cp_path.is_file():
        try:
            cp_path.unlink()
        except Exception:
            pass


def create_acquisition_gate(
    workspace: Path | str,
    slug: str,
    recommended_books: list[str],
    found_sources: list[str] | None = None,
) -> dict[str, Any]:
    """Create Material Acquisition Gate checkpoint when gold-standard materials are missing."""
    found = found_sources or []
    books_str = ", ".join(f"**{b}**" for b in recommended_books) if recommended_books else "canonical domain textbooks"

    prompt_lines = [
        f"📚 **Gold Standard Material Found**: Research recommends {books_str} as the landmark authority for this topic.",
    ]

    if found:
        prompt_lines.append("")
        prompt_lines.append("### Auto-Harvested Official Specifications (Already Downloaded):")
        for s in found[:8]:
            prompt_lines.append(f"- ✅ {s}")

    prompt_lines.extend([
        "",
        "If you have a copy (PDF or EPUB), drop it anywhere into this workspace, and I will compile it directly into your course.",
        "Or simply choose an option below to proceed:",
        "",
        "- `[1]` **Proceed with Open Docs**: Build curriculum using official documentation, academic papers, and lecture transcripts.",
        "- `[2]` **I'll Drop Files**: Pause and wait for me to drop a PDF or EPUB into the workspace.",
    ])
    prompt_text = "\n".join(prompt_lines)

    gate_data = {
        "gate": GATE_ACQUISITION,
        "slug": slug,
        "recommended_books": recommended_books,
        "found_sources": found,
        "prompt": prompt_text,
        "options": [
            {"key": "1", "label": "Proceed with open docs", "action": "proceed_open"},
            {"key": "2", "label": "Wait for drop-in file", "action": "wait_files"},
        ],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    save_checkpoint(workspace, gate_data)
    return gate_data


def create_source_proposal_gate(
    workspace: Path | str,
    slug: str,
    topic: str,
    proposal_path: Path | str | None = None,
    recommended_books: list[str] | None = None,
    found_sources: list[str] | None = None,
) -> dict[str, Any]:
    """Create Interactive Source Proposal checkpoint gate across 6 channels (FR-43, CAP-8)."""
    rec_books = recommended_books or []
    found = found_sources or []
    books_str = ", ".join(f"**{b}**" for b in rec_books) if rec_books else f"canonical authority on {topic}"

    prompt_lines = [
        f"📋 **Multi-Source Research Proposal**: Discovered materials for **{topic}**.",
    ]
    if proposal_path:
        prompt_lines.append(f"📄 Proposal dossier: `{proposal_path}`")
    prompt_lines.extend([
        "",
        f"📚 **Gold Standard Material Found**: Research recommends {books_str}.",
    ])
    if found:
        prompt_lines.append("\n### Auto-Harvested Official Specs & Papers (Available Now):")
        for s in found[:8]:
            prompt_lines.append(f"- ✅ {s}")

    prompt_lines.extend([
        "",
        "Review the proposed sources and choose your next action:",
        "- `[1]` **Approve Sources & Fetch All** (or **Proceed with Open Docs**): Harvest and compile syllabus.",
        "- `[2]` **Request More Research** (or **I'll Drop Files**): Search for more materials or wait for drop-in.",
        "- `[3]` **Add Custom Source**: Add URL, paper, or repo to proposal.",
        "- `[4]` **Remove Source**: Exclude a source from proposal.",
        "- `[5]` **Stop**: Cancel research and exit.",
    ])
    prompt_text = "\n".join(prompt_lines)

    gate_data = {
        "gate": GATE_SOURCE_PROPOSAL,
        "slug": slug,
        "topic": topic,
        "proposal_path": str(proposal_path) if proposal_path else "",
        "recommended_books": rec_books,
        "found_sources": found,
        "prompt": prompt_text,
        "options": [
            {"key": "1", "label": "Approve Sources & Fetch All", "action": "proceed_open"},
            {"key": "2", "label": "Request More Research", "action": "more_research"},
            {"key": "3", "label": "Add Custom Source", "action": "add_source"},
            {"key": "4", "label": "Remove Source", "action": "remove_source"},
            {"key": "5", "label": "Stop", "action": "stop"},
        ],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    save_checkpoint(workspace, gate_data)
    return gate_data


def create_approval_gate(
    workspace: Path | str,
    slug: str,
    title: str,
    course_data: dict[str, Any],
    deliberation_summary: str,
) -> dict[str, Any]:
    """Create Curriculum Approval Gate checkpoint before beginning lessons."""
    chapters = course_data.get("chapters", [])
    total_sections = sum(len(ch.get("sections", [])) for ch in chapters)

    outline_lines = [
        f"🏛️ **Curriculum Roadmap**: {title} ({len(chapters)} Chapters • {total_sections} Sections)",
        "",
        f"> {deliberation_summary}",
        "",
    ]
    for ch_idx, ch in enumerate(chapters, 1):
        outline_lines.append(f"### Chapter {ch_idx}: {ch.get('title', 'Untitled')}")
        for sec in ch.get("sections", []):
            outline_lines.append(f"- {sec.get('title', 'Section')}")
        outline_lines.append("")

    outline_lines.extend([
        "---",
        "Ready to begin Lesson 1? Choose an option:",
        "- `[1]` **Start Lesson 1**: Begin your first interactive lesson.",
        "- `[2]` **Adjust Roadmap**: Suggest modifications, add topics, or change pacing.",
    ])
    prompt_text = "\n".join(outline_lines)

    gate_data = {
        "gate": GATE_APPROVAL,
        "slug": slug,
        "title": title,
        "total_chapters": len(chapters),
        "total_sections": total_sections,
        "prompt": prompt_text,
        "options": [
            {"key": "1", "label": "Start Lesson 1", "action": "start_lesson"},
            {"key": "2", "label": "Adjust Roadmap", "action": "adjust"},
        ],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    save_checkpoint(workspace, gate_data)
    return gate_data


def handle_gate_response(
    response: str,
    workspace: Path | str,
) -> dict[str, Any]:
    """Parse user choice or natural language response against active checkpoint."""
    active_cp = load_checkpoint(workspace)
    if not active_cp:
        return {
            "ok": True,
            "has_active_gate": False,
            "action": "none",
            "message": "No active checkpoint gate pending.",
        }

    gate = active_cp.get("gate")
    resp_clean = response.strip().lower()

    if gate in {GATE_ACQUISITION, GATE_SOURCE_PROPOSAL}:
        # Check if user dropped a file in the meantime
        try:
            from extractor import discover_workspace_documents
        except ImportError:
            try:
                from _tc.scripts.extractor import discover_workspace_documents
            except ImportError:
                discover_workspace_documents = lambda ws: []
        discovered = discover_workspace_documents(workspace)
        if len(discovered) > len(active_cp.get("found_sources", [])):
            clear_checkpoint(workspace)
            return {
                "ok": True,
                "has_active_gate": False,
                "gate": gate,
                "slug": active_cp.get("slug"),
                "action": "files_detected",
                "new_files": [str(p) for p in discovered],
                "message": f"Found {len(discovered)} textbook documents in workspace. Proceeding to compilation.",
            }

        # Check options: '1', 'proceed', 'open', 'yes', 'approve', 'approve sources'
        if resp_clean in {"1", "proceed", "open", "continue", "yes", "proceed with open docs", "approve", "approve sources", "approve sources & fetch all"}:
            clear_checkpoint(workspace)
            return {
                "ok": True,
                "has_active_gate": False,
                "gate": gate,
                "slug": active_cp.get("slug"),
                "action": "proceed_open",
                "message": "Proceeding with open docs, transcripts, and official repositories.",
            }
        elif (resp_clean in {"2", "more", "research", "more research", "do more research", "request more research"} or "more research" in resp_clean) and (gate == GATE_SOURCE_PROPOSAL or any(opt.get("action") == "more_research" for opt in active_cp.get("options", []))):
            return {
                "ok": True,
                "has_active_gate": True,
                "gate": gate,
                "slug": active_cp.get("slug"),
                "action": "more_research",
                "message": "Conducting deeper multi-source research for candidate topic.",
            }
        elif resp_clean in {"2", "wait", "drop", "pause", "wait for drop-in file", "i'll drop files"}:
            return {
                "ok": True,
                "has_active_gate": True,
                "gate": gate,
                "slug": active_cp.get("slug"),
                "action": "waiting_files",
                "message": "Waiting for PDF or EPUB files to be added to workspace. Re-run /tc once dropped.",
            }
        elif resp_clean == "3" or resp_clean.startswith("add ") or resp_clean.startswith("add:"):
            custom = response.split(":", 1)[-1].strip() if ":" in response else (response[4:].strip() if response.lower().startswith("add ") else response.lstrip("3").strip())
            return {
                "ok": True,
                "has_active_gate": True,
                "gate": gate,
                "slug": active_cp.get("slug"),
                "action": "add_source",
                "custom_source": custom or response,
                "message": f"Added custom source to proposal: '{custom or response}'.",
            }
        elif resp_clean == "4" or resp_clean.startswith("remove ") or resp_clean.startswith("remove:"):
            removed = response.split(":", 1)[-1].strip() if ":" in response else (response[7:].strip() if response.lower().startswith("remove ") else response.lstrip("4").strip())
            return {
                "ok": True,
                "has_active_gate": True,
                "gate": gate,
                "slug": active_cp.get("slug"),
                "action": "remove_source",
                "removed_source": removed or response,
                "message": f"Removed source from proposal: '{removed or response}'.",
            }
        elif resp_clean in {"5", "stop", "cancel", "abort", "exit"}:
            clear_checkpoint(workspace)
            return {
                "ok": True,
                "has_active_gate": False,
                "gate": gate,
                "slug": active_cp.get("slug"),
                "action": "stop",
                "message": "Research and course creation cancelled.",
            }
        else:
            # Custom input or query
            return {
                "ok": True,
                "has_active_gate": True,
                "gate": gate,
                "slug": active_cp.get("slug"),
                "action": "custom_inquiry",
                "response_text": response,
                "message": f"Recorded custom preference: '{response}'. You may select [1] Approve, [2] More Research, [3] Add Source, [4] Remove Source, [5] Stop.",
            }

    elif gate == GATE_APPROVAL:
        if resp_clean in {"1", "start", "proceed", "yes", "begin", "start lesson 1"}:
            clear_checkpoint(workspace)
            return {
                "ok": True,
                "has_active_gate": False,
                "gate": gate,
                "action": "start_lesson",
                "slug": active_cp.get("slug"),
                "message": "Curriculum approved! Launching Lesson 1.",
            }
        elif resp_clean in {"2", "adjust", "modify", "change", "adjust roadmap"}:
            return {
                "ok": True,
                "has_active_gate": True,
                "gate": gate,
                "action": "await_adjustment",
                "slug": active_cp.get("slug"),
                "message": "What adjustments would you like to make to the roadmap?",
            }
        else:
            # Freeform adjustment request
            return {
                "ok": True,
                "has_active_gate": False,
                "gate": gate,
                "action": "reconcile_adjustment",
                "adjustment": response,
                "slug": active_cp.get("slug"),
                "message": f"Reconciling roadmap with your adjustment: '{response}'.",
            }

    return {
        "ok": True,
        "has_active_gate": False,
        "action": "unknown",
        "gate": gate,
        "message": f"Processed response for gate '{gate}'.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="checkpoint_manager.py — Interactive Checkpoint Gates")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # status
    p_stat = subparsers.add_parser("status", help="Get current pending checkpoint gate")
    p_stat.add_argument("--workspace", "-w", default=".", help="Workspace path")
    p_stat.add_argument("--json", action="store_true", help="Output in JSON format")

    # respond
    p_resp = subparsers.add_parser("respond", help="Submit response to active checkpoint gate")
    p_resp.add_argument("--response", "-r", required=True, help="User input response")
    p_resp.add_argument("--workspace", "-w", default=".", help="Workspace path")
    p_resp.add_argument("--json", action="store_true", help="Output in JSON format")

    # clear
    p_clear = subparsers.add_parser("clear", help="Clear active checkpoint")
    p_clear.add_argument("--workspace", "-w", default=".", help="Workspace path")
    p_clear.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    if args.subcommand == "status":
        cp = load_checkpoint(args.workspace)
        if args.json:
            output_json({"ok": True, "active_checkpoint": cp}, 0)
        else:
            if cp:
                print(f"Active Checkpoint: {cp.get('gate')}\n")
                print(cp.get("prompt", ""))
            else:
                print("No active checkpoint gate pending.")

    elif args.subcommand == "respond":
        res = handle_gate_response(args.response, workspace=args.workspace)
        if args.json:
            output_json(res, 0)
        else:
            print(res.get("message", ""))

    elif args.subcommand == "clear":
        clear_checkpoint(args.workspace)
        if args.json:
            output_json({"ok": True, "message": "Checkpoint cleared."}, 0)
        else:
            print("Checkpoint cleared.")


if __name__ == "__main__":
    main()
