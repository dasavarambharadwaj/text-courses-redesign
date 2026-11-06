#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""tc.py — Unified CLI entrypoint and runtime dispatcher for TextCourses.

Consolidates invocation across all runtime modules behind a single top-level CLI (FR-38, CAP-1):
- init: Workspace bootstrapping & layout scanning (bootstrapper.py)
- research: 5-hat autonomous deep research (scout.py)
- harvest: Multi-source deep asset harvester (harvester.py)
- extract: Pure-Python verbatim extraction & auto-ingestion (extractor.py)
- toc: Macro TOC alignment & multi-source deduplication (toc_aligner.py)
- source-map: Conveyor-belt symbol table compiler (source_mapper.py)
- index: Potato-proof sovereign SQLite FTS5 RAG indexer (indexer.py)
- create: Multi-path curriculum brainstorming & Triad consensus (course_builder.py)
- teach: Socratic instruction engine & session state machine (teach_engine.py)
- practicals: Hands-on coding challenge evaluation (practical_evaluator.py)
- test: Diagnostic Bloom taxonomy assessment (diagnostic_tester.py)
- notes: Human-first textbook compiler & readability auditor (notes_compiler.py)
- audit: Structural integrity & link verification (auditor.py)
- dag: Course prerequisite graph & cycle detection (dag.py)
- redirect: In-flight curriculum mutations (redirector.py)
- migrate: Legacy format migration (migrator.py)
- memlog: Sovereign memory logging (memlog.py)
- hash: Cryptographic checksum integrity (hash_tracker.py)
- ledger: Immutable assessment records (ledger.py)
- manifest: Course TOML manifest operations (manifest.py)
- context: Pedagogical context generation (context.py)
- tracker: Lesson plan checklist tracking (lesson_tracker.py)
"""

from __future__ import annotations

import importlib
import re
import json
import sys
from pathlib import Path

VERSION = "1.0.0"

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
for p in [str(SCRIPT_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

SUBCOMMAND_MODULES = {
    "init": "bootstrapper",
    "research": "scout",
    "scout": "scout",
    "harvest": "harvester",
    "extractor": "extractor",
    "extract": "extractor",
    "toc": "toc_aligner",
    "source-map": "source_mapper",
    "source_mapper": "source_mapper",
    "index": "indexer",
    "create": "course_builder",
    "teach": "teach_engine",
    "practicals": "practical_evaluator",
    "test": "diagnostic_tester",
    "notes": "notes_compiler",
    "audit": "auditor",
    "dag": "dag",
    "redirect": "redirector",
    "migrate": "migrator",
    "memlog": "memlog",
    "hash": "hash_tracker",
    "ledger": "ledger",
    "manifest": "manifest",
    "context": "context",
    "tracker": "lesson_tracker",
    "checkpoint": "checkpoint_manager",
    "gate": "checkpoint_manager",
    "papers": "paper_fetcher",
    "paper-fetcher": "paper_fetcher",
    "books": "book_scout",
    "book-scout": "book_scout",
}

COMMAND_DESCRIPTIONS = {
    "init": "Workspace bootstrapping, layout scanning, and status inspection",
    "research": "Autonomous 5-hat deep research and dossier generation",
    "scout": "Universal multi-hat research engine and dossier compiler",
    "harvest": "Autonomous multi-source deep harvester for repos, transcripts, and gold standards",
    "papers": "Autonomous academic paper, IETF RFC, and systems documentation fetcher",
    "books": "Canonical landmark textbook discovery and open repository search",
    "extractor": "Pure-Python verbatim document extraction and pre-flight probe",
    "extract": "Pure-Python verbatim document extraction and drop-in auto-ingestion",
    "toc": "Table of Contents alignment, semantic clustering, and deduplication",
    "source-map": "Conveyor-belt symbol table compiler and instant line-slice lookup",
    "source_mapper": "Conveyor-belt symbol table compiler and instant line-slice lookup",
    "index": "Potato-proof sovereign SQLite FTS5 RAG indexer and cross-source catalog synthesizer",
    "create": "Curriculum synthesis, multi-path brainstorming, and Triad consensus",
    "teach": "Conversational Socratic instruction and session state recovery",
    "practicals": "Hands-on coding challenge scaffolding and AI evaluation",
    "test": "Diagnostic conceptual inquiries across Bloom taxonomy levels",
    "notes": "Human-first textbook compilation and zero-jargon readability audit",
    "audit": "Course manifest, file existence, and structural verification",
    "dag": "Prerequisite dependency graph analysis and ASCII rendering",
    "redirect": "Dynamic in-flight course mutations and section insertion",
    "migrate": "Legacy course layout migration to streamlined architecture",
    "memlog": "Two-tier token-minimal pedagogical memory logging",
    "hash": "Cryptographic SHA-256 checksums and tamper detection",
    "ledger": "Immutable diagnostic scores and mastery recording",
    "manifest": "Course manifest parsing, updating, and validation",
    "context": "LLM instruction context compilation for active courses",
    "tracker": "Lesson plan markdown checklist parsing and concept ticking",
    "checkpoint": "Interactive checkpoint gates and pause management",
    "gate": "Interactive checkpoint gates and pause management",
}


def dispatch_conversational_turn(
    user_input: str | None = None,
    workspace: Path | str = ".",
    course_slug: str | None = None,
) -> dict[str, Any]:
    """Conversational state machine and single-door dispatcher for /tc."""
    ws = Path(workspace).resolve()
    inp = user_input.strip() if user_input else ""

    # 1. Check pending interactive checkpoint gate
    try:
        from checkpoint_manager import load_checkpoint, handle_gate_response, clear_checkpoint, create_acquisition_gate, create_approval_gate
    except ImportError:
        from _tc.scripts.checkpoint_manager import load_checkpoint, handle_gate_response, clear_checkpoint, create_acquisition_gate, create_approval_gate

    pending_cp = load_checkpoint(ws)
    if pending_cp and inp:
        res = handle_gate_response(inp, workspace=ws)
        if not res.get("has_active_gate"):
            action = res.get("action")
            if action in {"proceed_open", "files_detected"}:
                slug = pending_cp.get("slug", "active-course")
                topic_title = pending_cp.get("title") or slug.replace("-", " ").title()
                try:
                    from course_builder import create_course
                except ImportError:
                    from _tc.scripts.course_builder import create_course
                res_create = create_course(slug=slug, title=topic_title, workspace=ws)
                gate = create_approval_gate(
                    ws,
                    slug=slug,
                    title=topic_title,
                    course_data=res_create,
                    deliberation_summary=res_create.get("deliberation_summary", ""),
                )
                blueprint_file = ws / "_tc" / "courses" / slug / "blueprint.md"
                if not blueprint_file.is_file():
                    blueprint_file = ws / "courses" / slug / ".tc" / "blueprint.md"
                if not blueprint_file.is_file():
                    blueprint_file = ws / "courses" / slug / "blueprint.md"
                return {
                    "ok": True,
                    "state": "blueprint",
                    "gate": "curriculum_approval",
                    "action": action,
                    "slug": slug,
                    "deliberation_summary": res_create.get("deliberation_summary"),
                    "active_artifact": str(blueprint_file),
                    "prompt": gate["prompt"],
                    "options": gate["options"],
                    "message": f"Checkpoint resolved ({action}). Synthesized curriculum blueprint.",
                }
            elif action == "start_lesson":
                slug = pending_cp.get("slug")
                try:
                    from teach_engine import get_teaching_session
                except ImportError:
                    from _tc.scripts.teach_engine import get_teaching_session
                ctx = get_teaching_session(slug, workspace=ws)
                return {
                    "ok": True,
                    "state": "teaching",
                    "action": "start_lesson",
                    "slug": slug,
                    "context": ctx,
                    "fork_text": ctx.get("fork_text", ""),
                }
        return {
            "ok": True,
            "state": "checkpoint_pending",
            "gate": pending_cp.get("gate"),
            "gate_result": res,
            "prompt": pending_cp.get("prompt"),
        }

    # 2. Check workspace initialization
    pref_file = ws / "_tc" / "profile" / "preferences.md"
    if not pref_file.is_file():
        pref_file = ws / "profile" / "preferences.md"
    if not pref_file.is_file():
        pref_file = ws / "plan" / "preferences.md"
    if not pref_file.is_file():
        intake_prompt = (
            "👋 Welcome to **TextCourses**! Let's personalize your personal AI tutor.\n\n"
            "1. What is your primary learning goal and topic?\n"
            "2. What is your experience level (beginner, intermediate, advanced)?\n"
            "3. Do you prefer hands-on code practicals alongside lessons?\n\n"
            "Reply with your background, or type `1` to use standard software engineer defaults."
        )
        return {
            "ok": True,
            "state": "intake_needed",
            "prompt": intake_prompt,
        }

    # 3. Check for dropped documents
    try:
        from extractor import discover_workspace_documents, auto_ingest_workspace
    except ImportError:
        from _tc.scripts.extractor import discover_workspace_documents, auto_ingest_workspace
    discovered_docs = discover_workspace_documents(ws)

    # 4. Check active courses in courses/
    courses_dir = ws / "courses"
    existing_courses = []
    if courses_dir.is_dir():
        for d in sorted(courses_dir.iterdir()):
            if d.is_dir():
                if (d / ".tc" / "course.toml").is_file() or (d / "course.toml").is_file():
                    existing_courses.append(d.name)

    is_fork_digit = inp in {"1", "2", "3", "4", "next", "test", "deeper", "re-explain"}
    target_course = course_slug or (existing_courses[0] if existing_courses else None)

    if not target_course or (inp and not is_fork_digit and len(inp.split()) >= 2 and not existing_courses):
        topic_title = inp or "New Course"
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic_title.lower()).strip("-") or "course-01"

        if discovered_docs:
            auto_ingest_workspace(ws)

        if not discovered_docs:
            # 1. Execute autonomous research & discovery (find books, download RFCs/papers)
            try:
                from scout import run_scout
            except ImportError:
                from _tc.scripts.scout import run_scout

            try:
                run_scout(slug=slug, topic=topic_title, workspace=ws)
            except Exception:
                pass

            # 2. Extract discovered canonical books and auto-harvested sources
            rec_books = []
            gs_file = ws / "_tc" / "research" / slug / "gold-standards.md"
            if not gs_file.is_file():
                gs_file = ws / "research" / slug / "gold-standards.md"
            if gs_file.is_file():
                for line in gs_file.read_text(encoding="utf-8").splitlines():
                    if "ACQUISITION NEEDED" in line:
                        m = re.search(r"\*\*(.*?)\*\*", line)
                        if m:
                            rec_books.append(m.group(1))

            if not rec_books:
                rec_books = [f"Canonical reference for {topic_title}"]

            found_specs = []
            rfcs_dir = ws / "_tc" / "research" / slug / "sources" / "rfcs"
            if not rfcs_dir.is_dir():
                rfcs_dir = ws / "research" / slug / "sources" / "rfcs"
            if rfcs_dir.is_dir():
                for rf in sorted(rfcs_dir.glob("*.txt")):
                    found_specs.append(f"IETF RFC: {rf.stem.replace('_', ' ').upper()}")
            docs_dir = ws / "_tc" / "research" / slug / "sources" / "docs"
            if not docs_dir.is_dir():
                docs_dir = ws / "research" / slug / "sources" / "docs"
            if docs_dir.is_dir():
                for df in sorted(docs_dir.glob("*.md")):
                    found_specs.append(f"Official Spec: {df.stem.replace('_', ' ').title()}")
            papers_dir = ws / "_tc" / "research" / slug / "sources" / "papers"
            if not papers_dir.is_dir():
                papers_dir = ws / "research" / slug / "sources" / "papers"
            if papers_dir.is_dir():
                for pf in sorted(papers_dir.glob("*.md")):
                    found_specs.append(f"Academic Paper: {pf.stem.replace('_', ' ')}")

            gate = create_acquisition_gate(ws, slug=slug, recommended_books=rec_books, found_sources=found_specs)
            return {
                "ok": True,
                "state": "acquisition_gate",
                "slug": slug,
                "prompt": gate["prompt"],
                "options": gate["options"],
            }

        try:
            from course_builder import create_course
        except ImportError:
            from _tc.scripts.course_builder import create_course
        res_create = create_course(slug=slug, title=topic_title, workspace=ws)
        gate = create_approval_gate(
            ws,
            slug=slug,
            title=topic_title,
            course_data=res_create,
            deliberation_summary=res_create.get("deliberation_summary", ""),
        )
        blueprint_file = ws / "_tc" / "courses" / slug / "blueprint.md"
        if not blueprint_file.is_file():
            blueprint_file = ws / "courses" / slug / ".tc" / "blueprint.md"
        if not blueprint_file.is_file():
            blueprint_file = ws / "courses" / slug / "blueprint.md"
        return {
            "ok": True,
            "state": "blueprint",
            "gate": "curriculum_approval",
            "slug": slug,
            "deliberation_summary": res_create.get("deliberation_summary"),
            "active_artifact": str(blueprint_file),
            "prompt": gate["prompt"],
            "options": gate["options"],
        }

    # 5. Teaching loop on target course
    try:
        from teach_engine import get_teaching_session, advance_lesson_concept
    except ImportError:
        from _tc.scripts.teach_engine import get_teaching_session, advance_lesson_concept

    if inp in {"1", "next"}:
        adv_res = advance_lesson_concept(target_course, workspace=ws)
        ctx = get_teaching_session(target_course, workspace=ws)
        return {
            "ok": True,
            "state": "teaching",
            "action": "next_concept",
            "slug": target_course,
            "advancement": adv_res,
            "context": ctx,
            "fork_text": ctx.get("fork_text", ""),
        }
    elif inp in {"2", "test"}:
        ctx = get_teaching_session(target_course, workspace=ws)
        return {
            "ok": True,
            "state": "testing",
            "action": "test_inquiry",
            "slug": target_course,
            "context": ctx,
            "diagnostic_prompt": f"Diagnostic Inquiry on {ctx.get('active_concept')}: What invariant fails if misused?",
            "fork_text": ctx.get("fork_text", ""),
        }
    elif inp in {"3", "deeper", "re-explain"}:
        ctx = get_teaching_session(target_course, workspace=ws)
        return {
            "ok": True,
            "state": "teaching",
            "action": "deeper_explanation",
            "slug": target_course,
            "context": ctx,
            "fork_text": ctx.get("fork_text", ""),
        }
    else:
        ctx = get_teaching_session(target_course, workspace=ws)
        return {
            "ok": True,
            "state": "teaching",
            "action": "custom_turn",
            "slug": target_course,
            "input": inp,
            "context": ctx,
            "fork_text": ctx.get("fork_text", ""),
        }


def print_help() -> None:
    """Print top-level CLI usage and available subcommands."""
    print(f"TextCourses Unified Dispatcher (tc) v{VERSION}\n")
    print("Usage: uv run _tc/scripts/tc.py <subcommand> [options...]\n")
    print("Available Subcommands:")
    max_len = max(len(cmd) for cmd in SUBCOMMAND_MODULES)
    for cmd, desc in COMMAND_DESCRIPTIONS.items():
        print(f"  {cmd.ljust(max_len + 2)} {desc}")
    print("\nFlags:")
    print("  --help, -h     Show this help message and exit")
    print("  --version, -v  Show TextCourses version and exit")
    print("\nExample:")
    print("  uv run _tc/scripts/tc.py teach session --course async-rust --json")
    print("  uv run _tc/scripts/tc.py practicals evaluate-lesson --course async-rust --section sec-01")


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in {"--help", "-h", "help"}:
        print_help()
        sys.exit(0)

    if args[0] in {"--version", "-v", "version"}:
        print(f"TextCourses Engine v{VERSION}")
        sys.exit(0)

    subcommand = args[0].lower()

    if subcommand == "dispatch":
        input_val = None
        ws_val = "."
        course_val = None
        for i, a in enumerate(args):
            if a in {"--input", "-i"} and i + 1 < len(args):
                input_val = args[i + 1]
            elif a in {"--workspace", "-w"} and i + 1 < len(args):
                ws_val = args[i + 1]
            elif a in {"--course", "-c"} and i + 1 < len(args):
                course_val = args[i + 1]
        res = dispatch_conversational_turn(user_input=input_val, workspace=ws_val, course_slug=course_val)
        if "--json" in args:
            print(json.dumps(res, indent=2))
        else:
            if res.get("prompt"):
                print(res["prompt"])
            elif res.get("fork_text"):
                print(res["fork_text"])
            else:
                print(json.dumps(res, indent=2))
        sys.exit(0)

    if subcommand not in SUBCOMMAND_MODULES:
        # If argument is a conversational turn or fork choice rather than unknown flag
        is_fork_or_turn = subcommand in {"1", "2", "3", "4", "next", "deeper", "re-explain"} or (len(args) > 1 and not any(a.startswith("-") for a in args))
        if is_fork_or_turn and not any(a.startswith("-") for a in args):
            res = dispatch_conversational_turn(user_input=" ".join(args), workspace=".")
            if "--json" in args:
                print(json.dumps(res, indent=2))
            else:
                if res.get("prompt"):
                    print(res["prompt"])
                elif res.get("fork_text"):
                    print(res["fork_text"])
                else:
                    print(json.dumps(res, indent=2))
            sys.exit(0)

        error_msg = f"Unknown subcommand '{subcommand}'. Available: {', '.join(sorted(SUBCOMMAND_MODULES.keys()))}"
        if "--json" in args:
            print(json.dumps({"ok": False, "error": error_msg}))
        else:
            print(f"Error: {error_msg}\n")
            print_help()
        sys.exit(1)

    module_name = SUBCOMMAND_MODULES[subcommand]

    # Convenience default subcommands for modules where the top-level command matches
    forward_args = list(args[1:])
    is_help = any(a in {"--help", "-h"} for a in forward_args)
    if not is_help:
        if subcommand == "init" and (not forward_args or forward_args[0].startswith("-")):
            forward_args.insert(0, "init")
        elif subcommand in {"checkpoint", "gate"} and (not forward_args or forward_args[0].startswith("-")):
            forward_args.insert(0, "status")
        elif subcommand in {"extractor", "extract"} and (not forward_args or forward_args[0].startswith("-")):
            forward_args.insert(0, "auto-ingest")
        elif subcommand == "create" and (not forward_args or forward_args[0].startswith("-")):
            forward_args.insert(0, "create")
        elif subcommand == "index" and (not forward_args or forward_args[0].startswith("-")):
            forward_args.insert(0, "build")
        elif subcommand in {"research", "scout"} and (not forward_args or forward_args[0].startswith("-")):
            forward_args.insert(0, "scout")

    # Adjust sys.argv for the target module's CLI parser
    target_script = SCRIPT_DIR / f"{module_name}.py"
    sys.argv = [str(target_script)] + forward_args

    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError:
        # Fallback to _tc.scripts.<module_name>
        mod = importlib.import_module(f"_tc.scripts.{module_name}")

    if not hasattr(mod, "main"):
        error_msg = f"Module '{module_name}' does not define a main() function."
        if "--json" in args:
            print(json.dumps({"ok": False, "error": error_msg}))
        else:
            print(f"Error: {error_msg}")
        sys.exit(1)

    try:
        mod.main()
    except SystemExit as se:
        raise se
    except Exception as exc:
        if "--json" in args:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"Execution Error in {module_name}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
