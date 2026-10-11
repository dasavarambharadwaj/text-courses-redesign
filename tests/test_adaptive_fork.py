"""tests/test_adaptive_fork.py — Unit tests for context-adaptive Next-Action Fork (FR-40).

Verifies:
1. render_fork dynamically generates appropriate options for:
   - standard concept progression
   - tag-team faculty handoff
   - pending practical lab completion
   - section fully mastered & ready for chapter advancement
2. teach_engine.py session surfaces dynamic fork text and options based on course state.
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

from teach_engine import render_fork

TEACH_ENGINE_SCRIPT = SCRIPTS_DIR / "teach_engine.py"
COURSE_BUILDER_SCRIPT = SCRIPTS_DIR / "course_builder.py"


def test_render_fork_standard_and_tag_team():
    """Verify render_fork outputs default actions and tag-team actions."""
    # Default fork
    text_default, opts_default = render_fork()
    assert "`[1]` **Next Concept**" in text_default
    assert "`[2]` **Test Me**" in text_default
    assert opts_default[0]["action"] == "advance"

    # Tag team fork
    text_tag, opts_tag = render_fork(tag_team="Alan Turing")
    assert "Tag-in Alan Turing" in text_tag
    assert opts_tag[2]["action"] == "tag_team"
    assert opts_tag[2]["teacher"] == "Alan Turing"


def test_render_fork_practical_pending():
    """Verify render_fork adapts to practical pending state."""
    text_p, opts_p = render_fork(practical_pending=True)
    assert "`[1]` **Submit Practical Solution**" in text_p
    assert "Daedalus" in text_p
    assert "`[2]` **View Lab Requirements**" in text_p
    assert opts_p[0]["action"] == "submit_practical"
    assert opts_p[1]["action"] == "view_practical"
    assert opts_p[2]["action"] == "socratic_hint"


def test_render_fork_section_completed():
    """Verify render_fork adapts when all section concepts are completed."""
    text_comp, opts_comp = render_fork(section_completed=True)
    assert "`[1]` **Advance to Next Section**" in text_comp
    assert "`[2]` **Comprehensive Section Test**" in text_comp
    assert "`[3]` **Review Compiled Notes**" in text_comp
    assert opts_comp[0]["action"] == "advance_section"
    assert opts_comp[1]["action"] == "test_section"
    assert opts_comp[2]["action"] == "review_notes"


def test_session_adaptive_fork_integration(tmp_path: Path):
    """Verify get_teaching_session reflects adaptive fork when practical challenge is pending."""
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "preferences.md").write_text("practical_focus: true\n", encoding="utf-8")

    # 1. Create practical-focused course
    res_build = subprocess.run(
        [
            sys.executable,
            str(COURSE_BUILDER_SCRIPT),
            "create",
            "--slug",
            "practical-fork-test",
            "--workspace",
            str(tmp_path),
            "--title",
            "Practical Fork Test",
            "--topic",
            "Memory safety",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_build.returncode == 0

    # 2. Advance all concepts in section 1
    # Check session: before all concepts ticked, fork is concept progression
    res_sess1 = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "session",
            "--course",
            "practical-fork-test",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_sess1.returncode == 0
    data1 = json.loads(res_sess1.stdout)
    assert data1["fork_options"][0]["action"] == "advance"

    # Advance concept 1 and concept 2
    subprocess.run([sys.executable, str(TEACH_ENGINE_SCRIPT), "advance", "--course", "practical-fork-test", "--workspace", str(tmp_path)], capture_output=True)
    subprocess.run([sys.executable, str(TEACH_ENGINE_SCRIPT), "advance", "--course", "practical-fork-test", "--workspace", str(tmp_path)], capture_output=True)

    # Now with all concepts ticked and practical pending, session surfaces practical fork!
    res_sess2 = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "session",
            "--course",
            "practical-fork-test",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_sess2.returncode == 0
    data2 = json.loads(res_sess2.stdout)
    assert data2["fork_options"][0]["action"] == "submit_practical"
    assert "Submit Practical Solution" in data2["fork_text"]
