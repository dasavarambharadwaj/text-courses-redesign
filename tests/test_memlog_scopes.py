"""tests/test_memlog_scopes.py — Comprehensive test suite for scoped hierarchical memlog engine.

Validates:
- Hierarchical memlog scopes: workspace/profile, roadmap, research, course, chapter, section.
- Auto-creation of parent directory trees and frontmatter headers for scoped paths.
- Granular scoped logging: append targets specific active scope without cluttering upper tiers.
- Milestone roll-up: milestone events in a section propagate structured summary roll-ups
  to chapter, course, and global profile memlogs.
- Chapter roll-up: milestone events in a chapter propagate to course and global profile memlogs.
- Scoped inspection and tail extraction for turn context injection.
- Error handling on missing scope parameters (e.g. scope chapter without --chapter).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MEMLOG_SCRIPT = REPO_ROOT / "_tc" / "scripts" / "memlog.py"


def run_memlog_cli(*args: str) -> tuple[int, dict]:
    """Execute memlog.py CLI and parse stdout/stderr JSON."""
    cmd = [sys.executable, str(MEMLOG_SCRIPT), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout.strip() or proc.stderr.strip()
    try:
        data = json.loads(out)
    except Exception:
        data = {"raw": out, "exit_code": proc.returncode}
    return proc.returncode, data


def test_scoped_memlog_path_resolution(tmp_path: Path):
    """Verify that --scope correctly resolves canonical paths under _tc/ for all scopes."""
    ws = tmp_path / "workspace"
    ws.mkdir()

    # 1. Profile / Workspace Scope
    code, res = run_memlog_cli(
        "append",
        "--workspace", str(ws),
        "--scope", "profile",
        "--tag", "milestone",
        "--content", "Learner onboarded",
    )
    assert code == 0, res
    expected_prof = ws / "_tc" / "profile" / "memlog.md"
    assert expected_prof.is_file()
    assert "- (milestone) Learner onboarded" in expected_prof.read_text(encoding="utf-8")

    # 2. Roadmap Scope
    code, res = run_memlog_cli(
        "append",
        "--workspace", str(ws),
        "--scope", "roadmap",
        "--tag", "decision",
        "--content", "Selected Distributed Systems Track",
    )
    assert code == 0, res
    expected_roadmap = ws / "_tc" / "roadmap" / "memlog.md"
    assert expected_roadmap.is_file()
    assert "- (decision) Selected Distributed Systems Track" in expected_roadmap.read_text(encoding="utf-8")

    # 3. Research Scope
    code, res = run_memlog_cli(
        "append",
        "--workspace", str(ws),
        "--scope", "research",
        "--course", "distributed-consensus",
        "--tag", "insight",
        "--content", "Found Raft paper and TLA+ specs",
    )
    assert code == 0, res
    expected_res = ws / "_tc" / "research" / "distributed-consensus" / "memlog.md"
    assert expected_res.is_file()
    assert "- (insight) Found Raft paper and TLA+ specs" in expected_res.read_text(encoding="utf-8")

    # 4. Course Scope
    code, res = run_memlog_cli(
        "append",
        "--workspace", str(ws),
        "--scope", "course",
        "--course", "distributed-consensus",
        "--tag", "milestone",
        "--content", "Course syllabus initialized",
    )
    assert code == 0, res
    expected_course = ws / "_tc" / "courses" / "distributed-consensus" / "memlog.md"
    assert expected_course.is_file()
    assert "- (milestone) Course syllabus initialized" in expected_course.read_text(encoding="utf-8")

    # 5. Chapter Scope
    code, res = run_memlog_cli(
        "append",
        "--workspace", str(ws),
        "--scope", "chapter",
        "--course", "distributed-consensus",
        "--chapter", "01",
        "--tag", "concept",
        "--content", "Leader election state machine",
    )
    assert code == 0, res
    expected_ch = ws / "_tc" / "courses" / "distributed-consensus" / "chapters" / "chapter-01" / "memlog.md"
    assert expected_ch.is_file()
    assert "- (concept) Leader election state machine" in expected_ch.read_text(encoding="utf-8")

    # 6. Section Scope
    code, res = run_memlog_cli(
        "append",
        "--workspace", str(ws),
        "--scope", "section",
        "--course", "distributed-consensus",
        "--chapter", "01",
        "--section", "02",
        "--tag", "misconception",
        "--content", "Heartbeats prevent split-brain on network partition",
    )
    assert code == 0, res
    expected_sec = (
        ws / "_tc" / "courses" / "distributed-consensus" / "chapters" / "chapter-01" / "sections" / "section-02" / "memlog.md"
    )
    assert expected_sec.is_file()
    assert "- (misconception) Heartbeats prevent split-brain on network partition" in expected_sec.read_text(encoding="utf-8")


def test_milestone_roll_up_from_section_to_all_tiers(tmp_path: Path):
    """Verify that a section milestone roll-up atomically logs to section, chapter, course, and global memlogs."""
    ws = tmp_path / "workspace_rollup"
    ws.mkdir()

    course_slug = "linux-internals"
    chapter_id = "01"
    section_id = "02"
    milestone_text = "Mastered epoll and edge-triggered event demultiplexing"

    code, res = run_memlog_cli(
        "append",
        "--workspace", str(ws),
        "--scope", "section",
        "--course", course_slug,
        "--chapter", chapter_id,
        "--section", section_id,
        "--tag", "milestone",
        "--content", milestone_text,
        "--roll-up",
    )
    assert code == 0, res
    assert res["ok"] is True
    assert res["rolled_up"] is True
    assert len(res["rolled_up_paths"]) == 3

    # Tier 1: Section Memlog (direct entry)
    sec_file = (
        ws / "_tc" / "courses" / course_slug / "chapters" / "chapter-01" / "sections" / "section-02" / "memlog.md"
    )
    assert sec_file.is_file()
    sec_content = sec_file.read_text(encoding="utf-8")
    assert f"- (milestone) {milestone_text}" in sec_content

    # Tier 2: Chapter Memlog (roll-up with section reference)
    ch_file = ws / "_tc" / "courses" / course_slug / "chapters" / "chapter-01" / "memlog.md"
    assert ch_file.is_file()
    ch_content = ch_file.read_text(encoding="utf-8")
    assert milestone_text in ch_content
    assert "(milestone)" in ch_content
    assert "section-02" in ch_content

    # Tier 3: Course Memlog (roll-up with chapter/section reference)
    course_file = ws / "_tc" / "courses" / course_slug / "memlog.md"
    assert course_file.is_file()
    course_content = course_file.read_text(encoding="utf-8")
    assert milestone_text in course_content
    assert "chapter-01/section-02" in course_content

    # Tier 4: Global Profile Memlog (roll-up with full course/chapter/section context)
    global_file = ws / "_tc" / "profile" / "memlog.md"
    assert global_file.is_file()
    global_content = global_file.read_text(encoding="utf-8")
    assert milestone_text in global_content
    assert f"{course_slug}/chapter-01/section-02" in global_content


def test_milestone_roll_up_from_chapter(tmp_path: Path):
    """Verify that chapter-level milestone rolls up to course and global memlogs."""
    ws = tmp_path / "workspace_ch_rollup"
    ws.mkdir()

    course_slug = "distributed-tracing"
    ch_id = "03"
    milestone_text = "Completed Chapter 3 on B3 Propagation and OpenTelemetry"

    code, res = run_memlog_cli(
        "append",
        "--workspace", str(ws),
        "--scope", "chapter",
        "--course", course_slug,
        "--chapter", ch_id,
        "--tag", "milestone",
        "--content", milestone_text,
        "--roll-up",
    )
    assert code == 0, res
    assert res["rolled_up"] is True

    # Chapter has direct entry
    ch_file = ws / "_tc" / "courses" / course_slug / "chapters" / "chapter-03" / "memlog.md"
    assert f"- (milestone) {milestone_text}" in ch_file.read_text(encoding="utf-8")

    # Course has roll-up
    course_file = ws / "_tc" / "courses" / course_slug / "memlog.md"
    assert milestone_text in course_file.read_text(encoding="utf-8")

    # Global has roll-up
    global_file = ws / "_tc" / "profile" / "memlog.md"
    assert milestone_text in global_file.read_text(encoding="utf-8")


def test_scoped_inspect_and_tail(tmp_path: Path):
    """Verify inspecting and tailing scoped memlogs returns expected structured JSON."""
    ws = tmp_path / "inspect_ws"
    ws.mkdir()

    # Append 5 entries to section memlog
    for i in range(1, 6):
        run_memlog_cli(
            "append",
            "--workspace", str(ws),
            "--scope", "section",
            "--course", "raft",
            "--chapter", "01",
            "--section", "01",
            "--tag", "concept",
            "--content", f"Concept tick {i}",
        )

    # Tail last 2 entries
    code_tail, res_tail = run_memlog_cli(
        "tail",
        "--workspace", str(ws),
        "--scope", "section",
        "--course", "raft",
        "--chapter", "01",
        "--section", "01",
        "--n", "2",
    )
    assert code_tail == 0
    assert res_tail["ok"] is True
    assert res_tail["count"] == 2
    assert res_tail["total_entries"] == 5
    assert "Concept tick 5" in res_tail["entries"][-1]

    # Inspect full memlog
    code_insp, res_insp = run_memlog_cli(
        "inspect",
        "--workspace", str(ws),
        "--scope", "section",
        "--course", "raft",
        "--chapter", "01",
        "--section", "01",
    )
    assert code_insp == 0
    assert res_insp["ok"] is True
    assert len(res_insp["entries"]) == 5


def test_missing_scope_parameters_fails_gracefully(tmp_path: Path):
    """Verify omitting required scope parameters produces clean error exit 1."""
    ws = tmp_path / "err_ws"
    ws.mkdir()

    # Scope chapter without --chapter
    code, res = run_memlog_cli(
        "append",
        "--workspace", str(ws),
        "--scope", "chapter",
        "--course", "test-course",
        "--content", "Missing chapter flag",
    )
    assert code == 1
    assert res["ok"] is False
    assert "required" in res["error"].lower()

    # Scope section without --section
    code, res = run_memlog_cli(
        "append",
        "--workspace", str(ws),
        "--scope", "section",
        "--course", "test-course",
        "--chapter", "01",
        "--content", "Missing section flag",
    )
    assert code == 1
    assert res["ok"] is False
    assert "required" in res["error"].lower()
