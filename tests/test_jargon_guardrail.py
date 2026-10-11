"""tests/test_jargon_guardrail.py — Verification of radical readability and zero-unexplained-jargon guardrail.

Verifies:
1. Textbook notes formatting enforces Plain English Recap, Mental Model/Analogy, and Jargon Demystification.
2. The audit_jargon_and_readability function identifies grounded analogies vs. dense ungrounded jargon.
3. CLI subcommand audit-readability operates via JSON output.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from notes_compiler import (
    audit_jargon_and_readability,
    format_textbook_notes,
)

NOTES_COMPILER_SCRIPT = SCRIPTS_DIR / "notes_compiler.py"


def test_format_textbook_notes_enforces_readability_and_jargon_demystification():
    """Verify notes compilation scaffolds human-friendly analogies and jargon demystification."""
    formatted = format_textbook_notes(
        title="Event Loop Architecture",
        recap_bullets=["Single thread processes tasks from queues without blocking."],
        analogy="Think of a single hyper-efficient waiter serving orders from a revolving kitchen window.",
        jargon_demystified=[
            {
                "term": "Event Loop",
                "definition": "An endless loop waiting for and dispatching events or tasks.",
                "analogy": "Like a revolving carousel that serves passengers one luggage item at a time.",
            }
        ],
        teacher="Hypatia",
    )

    assert "## 3-Bullet Recap (In Plain English)" in formatted
    assert "## Intuitive Mental Model & Analogy" in formatted
    assert "revolving kitchen window" in formatted
    assert "## Jargon Demystified & Everyday Analogies" in formatted
    assert "Radical Readability Rule: No technical jargon without an intuitive real-world explanation." in formatted
    assert "**Event Loop**" in formatted
    assert "Everyday Analogy" in formatted


def test_audit_jargon_and_readability_evaluates_compliance(tmp_path: Path):
    """Verify audit_jargon_and_readability approves plain English notes and flags ungrounded dense jargon."""
    compliant_notes = """# Chapter 01: Foundations

## Recap (in Plain English)
- Everything is built out of simple building blocks.

## Mental Model & Analogy
> Think of variables like labeled glass jars on a kitchen shelf.

## Jargon Demystified & Everyday Analogies
- **Variable**: A named storage location in memory. *Everyday Analogy*: A labeled jar holding one ingredient.

## Core Mechanics & Architecture
Step by step instructions here.
"""

    audit_result = audit_jargon_and_readability(compliant_notes)
    assert audit_result["ok"] is True
    assert audit_result["readability"] == "human_friendly"
    assert audit_result["has_plain_recap"] is True
    assert audit_result["has_analogy"] is True
    assert audit_result["has_demystification"] is True
    assert "Variable" in audit_result["demystified_terms"]
    assert len(audit_result["warnings"]) == 0

    # Non-compliant jargon-heavy notes
    dense_notes = """# Chapter 01: High Performance IPC

Direct DMA buffer allocation through kernel bypass.
CRITICAL: Observe zero copy semantics across user space memory barriers.
"""
    bad_audit = audit_jargon_and_readability(dense_notes)
    assert bad_audit["ok"] is False
    assert bad_audit["readability"] == "dense_unexplained_jargon"
    assert bad_audit["has_plain_recap"] is False
    assert bad_audit["has_analogy"] is False
    assert len(bad_audit["warnings"]) >= 2

    # Test via CLI
    notes_file = tmp_path / "notes.md"
    notes_file.write_text(compliant_notes, encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(NOTES_COMPILER_SCRIPT),
            "audit-readability",
            "--notes-file",
            str(notes_file),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    cli_result = json.loads(res.stdout)
    assert cli_result["ok"] is True
    assert cli_result["readability"] == "human_friendly"
