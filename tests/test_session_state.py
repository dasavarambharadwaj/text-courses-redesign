"""tests/test_session_state.py — Unit tests for Socratic session state machine (FR-39).

Verifies:
1. append_session_event and load_session_history operate on session.jsonl.
2. CLI subcommands 'log-turn' and 'history' in teach_engine.py.
3. get_teaching_session includes recent_session_history.
4. Concept advance automatically records events in session.jsonl.
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

from teach_engine import (
    append_session_event,
    get_teaching_session,
    load_session_history,
)

TEACH_ENGINE_SCRIPT = SCRIPTS_DIR / "teach_engine.py"
COURSE_BUILDER_SCRIPT = SCRIPTS_DIR / "course_builder.py"


def test_session_state_file_operations(tmp_path: Path):
    """Verify append_session_event and load_session_history write and parse JSON lines correctly."""
    course_dir = tmp_path / "courses" / "async-rust"
    course_dir.mkdir(parents=True, exist_ok=True)

    # Initially empty
    assert load_session_history(course_dir) == []

    # Append 3 events
    append_session_event(
        course_dir,
        {
            "section_id": "sec-01",
            "concept": "Event Loop",
            "teacher": "Hypatia",
            "turn_type": "concept_delivery",
            "summary": "Taught event loop with kitchen carousel analogy",
        },
    )
    append_session_event(
        course_dir,
        {
            "section_id": "sec-01",
            "concept": "Event Loop",
            "teacher": "Hypatia",
            "turn_type": "student_response",
            "summary": "Learner asked about thread starvation",
        },
    )
    append_session_event(
        course_dir,
        {
            "section_id": "sec-01",
            "concept": "Event Loop",
            "teacher": "Hypatia",
            "turn_type": "socratic_probe",
            "summary": "Posed cooperative yielding dilemma",
        },
    )

    history = load_session_history(course_dir, limit=2)
    assert len(history) == 2
    assert history[0]["turn_type"] == "student_response"
    assert history[1]["turn_type"] == "socratic_probe"

    all_history = load_session_history(course_dir, limit=10)
    assert len(all_history) == 3


def test_cli_log_turn_and_history(tmp_path: Path):
    """Verify CLI subcommands log-turn and history record and output events."""
    course_dir = tmp_path / "courses" / "concurrency-core"
    course_dir.mkdir(parents=True, exist_ok=True)

    # 1. Log turn via CLI
    res_log = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "log-turn",
            "--course",
            "concurrency-core",
            "--section",
            "sec-02",
            "--concept",
            "Channel Buffering",
            "--teacher",
            "Daedalus",
            "--turn-type",
            "socratic_probe",
            "--summary",
            "Challenged learner on unbuffered channel deadlock",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_log.returncode == 0
    log_data = json.loads(res_log.stdout)
    assert log_data["ok"] is True
    assert log_data["logged_event"]["concept"] == "Channel Buffering"

    # 2. Retrieve history via CLI
    res_hist = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "history",
            "--course",
            "concurrency-core",
            "--limit",
            "5",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_hist.returncode == 0
    hist_data = json.loads(res_hist.stdout)
    assert hist_data["ok"] is True
    assert len(hist_data["history"]) == 1
    assert hist_data["history"][0]["teacher"] == "Daedalus"
    assert "deadlock" in hist_data["history"][0]["summary"]


def test_session_state_integration_with_advance(tmp_path: Path):
    """Verify concept advance automatically logs to session.jsonl and reflects in session retrieval."""
    # 1. Scaffold course
    res_build = subprocess.run(
        [
            sys.executable,
            str(COURSE_BUILDER_SCRIPT),
            "create",
            "--slug",
            "state-test",
            "--workspace",
            str(tmp_path),
            "--title",
            "State Machine Test",
            "--topic",
            "State machines",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_build.returncode == 0

    # 2. Advance concept
    res_adv = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "advance",
            "--course",
            "state-test",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_adv.returncode == 0

    # 3. Check session output includes recent_session_history
    res_sess = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "session",
            "--course",
            "state-test",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_sess.returncode == 0
    sess_data = json.loads(res_sess.stdout)
    assert "recent_session_history" in sess_data
    assert len(sess_data["recent_session_history"]) >= 1
    assert sess_data["recent_session_history"][0]["turn_type"] == "concept_mastered"
