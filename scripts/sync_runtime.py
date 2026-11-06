#!/usr/bin/env python3
"""sync_runtime.py — Master synchronization script for TextCourses runtime scripts.

Ensures that _tc/scripts/ (the canonical source of truth) is replicated with 100% SHA-256
fidelity into skills/tc-init/scripts/runtime/ and individual skill directories.
Eliminates code divergence and triple-maintenance traps.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DIR = REPO_ROOT / "_tc" / "scripts"
RUNTIME_DIR = REPO_ROOT / "skills" / "tc-init" / "scripts" / "runtime"

SKILL_SCRIPT_MAP = {
    "bootstrapper.py": REPO_ROOT / "skills" / "tc-init" / "scripts" / "bootstrapper.py",
    "scout.py": REPO_ROOT / "skills" / "tc-research" / "scripts" / "scout.py",
    "harvester.py": REPO_ROOT / "skills" / "tc-research" / "scripts" / "harvester.py",
    "paper_fetcher.py": REPO_ROOT / "skills" / "tc-research" / "scripts" / "paper_fetcher.py",
    "book_scout.py": REPO_ROOT / "skills" / "tc-research" / "scripts" / "book_scout.py",
    "course_builder.py": REPO_ROOT / "skills" / "tc-create" / "scripts" / "course_builder.py",
    "source_mapper.py": REPO_ROOT / "skills" / "tc-create" / "scripts" / "source_mapper.py",
    "teach_engine.py": REPO_ROOT / "skills" / "tc-teach" / "scripts" / "teach_engine.py",
    "diagnostic_tester.py": REPO_ROOT / "skills" / "tc-test-me" / "scripts" / "diagnostic_tester.py",
    "practical_evaluator.py": REPO_ROOT / "skills" / "tc-practicals" / "scripts" / "practical_evaluator.py",
    "auditor.py": REPO_ROOT / "skills" / "tc-verify-course" / "scripts" / "auditor.py",
    "redirector.py": REPO_ROOT / "skills" / "tc-redirect-course" / "scripts" / "redirector.py",
    "migrator.py": REPO_ROOT / "skills" / "tc-migrate" / "scripts" / "migrator.py",
    "indexer.py": REPO_ROOT / "skills" / "tc-index" / "scripts" / "indexer.py",
}


def sha256(path: Path) -> str:
    """Compute sha256 checksum of a file."""
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync() -> int:
    """Sync all canonical scripts to runtime directory and skill directories."""
    if not CANONICAL_DIR.is_dir():
        print(f"Error: Canonical directory '{CANONICAL_DIR}' not found.", file=sys.stderr)
        return 1

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    synced_runtime = 0
    synced_skills = 0

    # 1. Sync _tc/scripts/*.py to skills/tc-init/scripts/runtime/
    for py_file in sorted(CANONICAL_DIR.glob("*.py")):
        target = RUNTIME_DIR / py_file.name
        if sha256(py_file) != sha256(target):
            shutil.copy2(py_file, target)
            synced_runtime += 1

    # 2. Sync to individual skill script destinations
    for script_name, target_path in SKILL_SCRIPT_MAP.items():
        src = CANONICAL_DIR / script_name
        if src.is_file():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if sha256(src) != sha256(target_path):
                shutil.copy2(src, target_path)
                synced_skills += 1

    print(f"✅ Synchronization complete: {synced_runtime} files updated in runtime/, {synced_skills} files updated in skills/.")
    return 0


if __name__ == "__main__":
    sys.exit(sync())
