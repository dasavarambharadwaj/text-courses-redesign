"""tests/test_status_dashboard.py — Tests for Self-Contained Local Interactive Status Dashboard Generator (CAP-10, FR-50)."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from dashboard_generator import collect_workspace_state, generate_dashboard_html, write_status_dashboard
from bootstrapper import bootstrap_workspace
from course_builder import scaffold_course_files
from checkpoint_manager import create_section_close_gate


def test_write_status_dashboard_outputs_state_and_html(tmp_path: Path):
    """Verify write_status_dashboard generates _tc/status/state.json and status-board/index.html."""
    state_file, html_file = write_status_dashboard(tmp_path)

    assert state_file.is_file(), "_tc/status/state.json must be generated"
    assert html_file.is_file(), "status-board/index.html must be generated"

    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["framework"] == "TextCourses"
    assert "version" in data
    assert "last_updated" in data
    assert "next_action" in data
    assert "courses" in data


def test_status_dashboard_zero_external_network_requests(tmp_path: Path):
    """Verify status-board/index.html contains zero external network requests (strict offline file:// compatibility)."""
    # Create sample course and state
    slug = "dist-systems"
    course_data = {
        "course": {"id": slug, "title": "Distributed Systems", "archetype": "applied_creation"},
        "chapters": [
            {
                "id": "chapter-01",
                "title": "Consensus & State",
                "sections": [{"id": "sec-01", "title": "Paxos Basics", "status": "completed"}],
            }
        ],
    }
    scaffold_course_files(tmp_path, course_data)

    state_file, html_file = write_status_dashboard(tmp_path)
    html_content = html_file.read_text(encoding="utf-8")

    # Invariant: Zero external CDN, script, font, or stylesheet requests
    # Scan for external URLs in src, href, @import, url(...)
    external_refs = re.findall(r'(?:src|href|url)\s*=\s*["\'](https?://[^"\']+)["\']', html_content, re.IGNORECASE)
    css_imports = re.findall(r'@import\s+["\']?(https?://[^"\'\)\s]+)', html_content, re.IGNORECASE)

    assert len(external_refs) == 0, f"Found external URL references in HTML: {external_refs}"
    assert len(css_imports) == 0, f"Found external CSS imports in HTML: {css_imports}"

    # Verify inline CSS and JavaScript exist
    assert "<style>" in html_content
    assert "</style>" in html_content
    assert "<script>" in html_content
    assert "</script>" in html_content
    assert "TextCourses Status Board" in html_content


def test_status_dashboard_renders_active_checkpoint_gate_banner(tmp_path: Path):
    """Verify that when a checkpoint gate is pending, status-board/index.html renders the gate callout banner."""
    slug = "compiler-theory"
    create_section_close_gate(
        workspace=tmp_path,
        slug=slug,
        chapter_id=1,
        section_id="sec-01",
        section_title="Intermediate Representation",
        recap=["SSA form invariant", "Basic block dominators"],
    )

    state_file, html_file = write_status_dashboard(tmp_path)
    state_data = json.loads(state_file.read_text(encoding="utf-8"))

    assert state_data["has_active_gate"] is True
    assert state_data["active_gate"]["gate"] == "section_close"

    html_content = html_file.read_text(encoding="utf-8")
    assert "Active Checkpoint Gate" in html_content
    assert "Intermediate Representation" in html_content
    assert "Approve &amp; Close Section" in html_content or "Approve & Close Section" in html_content


def test_bootstrap_workspace_automatically_generates_dashboard(tmp_path: Path):
    """Verify that running bootstrap_workspace immediately generates status-board/index.html."""
    ws = tmp_path / "fresh_ws"
    bootstrap_workspace(path=ws)

    state_file = ws / "_tc" / "status" / "state.json"
    html_file = ws / "status-board" / "index.html"

    assert state_file.is_file(), "Bootstrap must initialize _tc/status/state.json"
    assert html_file.is_file(), "Bootstrap must initialize status-board/index.html"
    assert "TextCourses Status Board" in html_file.read_text(encoding="utf-8")


def test_dashboard_cli(tmp_path: Path):
    """Verify dashboard_generator CLI execution."""
    dash_script = SCRIPTS_DIR / "dashboard_generator.py"
    res = subprocess.run(
        [sys.executable, str(dash_script), str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["zero_network_requests"] is True
    assert "file:///" in data["file_url"]
