"""tests/test_deliberation_summary.py — Verification of Token-Bounded Triad Deliberation Summarizer (CAP-5)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from course_builder import create_course, generate_bounded_deliberation_summary


def test_generate_bounded_deliberation_summary_under_40_words():
    """Verify deliberation summaries are concise and strictly under 40 words."""
    # Case 1: Standard synthesis with deduplicated topics
    summary_dedup = generate_bounded_deliberation_summary(
        slug="dist-storage",
        title="Distributed Storage",
        total_chapters=4,
        total_sections=12,
        dedup_count=3,
        coverage_pct=100.0,
        max_words=40,
    )
    word_count_1 = len(summary_dedup.split())
    assert word_count_1 <= 40
    assert "Daedalus" in summary_dedup
    assert "Marie" in summary_dedup
    assert "Hypatia" in summary_dedup
    assert "deduplicating 3 overlapping topics" in summary_dedup
    assert "100%" in summary_dedup

    # Case 2: Clean synthesis without duplicates
    summary_clean = generate_bounded_deliberation_summary(
        slug="async-rust",
        title="Async Rust",
        total_chapters=3,
        total_sections=8,
        dedup_count=0,
        coverage_pct=100.0,
        max_words=40,
    )
    word_count_2 = len(summary_clean.split())
    assert word_count_2 <= 40
    assert "100%" in summary_clean


def test_generate_bounded_deliberation_summary_hard_truncation():
    """Verify hard truncation guardrail enforces max_words limit."""
    short_summary = generate_bounded_deliberation_summary(
        slug="test",
        title="Test Course",
        total_chapters=5,
        total_sections=20,
        dedup_count=4,
        coverage_pct=100.0,
        max_words=10,
    )
    assert len(short_summary.split()) <= 10
    assert short_summary.endswith("...")


def test_create_course_returns_deliberation_summary(tmp_path: Path):
    """Verify create_course embeds <= 40-word summary and saves full debate trace to .tc/."""
    slug = "token-test"
    res = create_course(
        slug=slug,
        title="Token Minimal Course",
        archetype="applied_creation",
        workspace=tmp_path,
    )
    assert res["ok"] is True
    assert "deliberation_summary" in res
    assert res["deliberation_summary_words"] <= 40
    assert len(res["deliberation_summary"].split()) <= 40

    # Verify full debate transcript exists silently on disk in .tc/
    course_dir = tmp_path / "courses" / slug
    delib_file = course_dir / ".tc" / "consensus-deliberation.md"
    assert delib_file.is_file()
    trace_text = delib_file.read_text(encoding="utf-8")
    assert "Triad Consensus Deliberation" in trace_text


def test_course_builder_deliberation_cli_on_encapsulated_trace(tmp_path: Path):
    """Verify course_builder.py deliberation CLI resolves trace from .tc/."""
    slug = "cli-trace-test"
    create_course(
        slug=slug,
        title="CLI Trace Test",
        archetype="applied_creation",
        workspace=tmp_path,
    )

    cb_script = SCRIPTS_DIR / "course_builder.py"
    cmd = [
        sys.executable,
        str(cb_script),
        "deliberation",
        "--slug",
        slug,
        "--workspace",
        str(tmp_path),
        "--json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert "Triad Consensus Deliberation" in data["content"]
