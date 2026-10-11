#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""tc.py — Unified CLI entrypoint and runtime dispatcher for TextCourses.

Consolidates invocation across all 20 runtime modules behind a single top-level CLI (FR-38):
- init: Workspace bootstrapping & layout scanning (bootstrapper.py)
- research: 5-hat autonomous deep research (scout.py)
- harvest: Multi-source deep asset harvester (harvester.py)
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
}

COMMAND_DESCRIPTIONS = {
    "init": "Workspace bootstrapping, layout scanning, and status inspection",
    "research": "Autonomous 5-hat deep research and dossier generation",
    "scout": "Universal multi-hat research engine and dossier compiler",
    "harvest": "Autonomous multi-source deep harvester for repos, transcripts, and gold standards",
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
    if subcommand not in SUBCOMMAND_MODULES:
        error_msg = f"Unknown subcommand '{subcommand}'. Available: {', '.join(sorted(SUBCOMMAND_MODULES.keys()))}"
        if "--json" in args:
            print(json.dumps({"ok": False, "error": error_msg}))
        else:
            print(f"Error: {error_msg}\n")
            print_help()
        sys.exit(1)

    module_name = SUBCOMMAND_MODULES[subcommand]

    # Adjust sys.argv for the target module's CLI parser
    target_script = SCRIPT_DIR / f"{module_name}.py"
    sys.argv = [str(target_script)] + args[1:]

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
