"""test_in_loop_practicals.py — Verification for FR-36 In-Loop Practical Instruction & AI Practical Evaluation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

COURSE_BUILDER_SCRIPT = Path("_tc/scripts/course_builder.py").resolve()
TEACH_ENGINE_SCRIPT = Path("_tc/scripts/teach_engine.py").resolve()
PRACTICAL_EVALUATOR_SCRIPT = Path("_tc/scripts/practical_evaluator.py").resolve()


def test_in_loop_practical_scaffolding_and_ai_evaluation(tmp_path: Path):
    """Verify practicals are scaffolded and evaluated via AI invariant rules."""
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "preferences.md").write_text(
        "practical_focus: true\nrole: Systems Engineer\n",
        encoding="utf-8",
    )

    # 1. Create practical-focused course
    res_create = subprocess.run(
        [
            sys.executable,
            str(COURSE_BUILDER_SCRIPT),
            "create",
            "--slug",
            "practical-concurrency",
            "--workspace",
            str(tmp_path),
            "--title",
            "Concurrent Systems",
            "--topic",
            "Mutexes and channel synchronizers",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_create.returncode == 0

    # 2. Start teaching session
    res_session = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "session",
            "--course",
            "practical-concurrency",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_session.returncode == 0
    s_data = json.loads(res_session.stdout)
    assert s_data["is_practical"] is True
    assert s_data["practical"] is not None
    assert s_data["practical"]["status"] == "pending"
    assert "Daedalus" in s_data["practical"]["evaluator"]

    practical_file = Path(s_data["practical"]["file"])
    assert practical_file.is_file()
    assert "Practical Hands-On Lab" in practical_file.read_text(encoding="utf-8")

    # 3. Test empty submission evaluation
    res_eval_empty = subprocess.run(
        [
            sys.executable,
            str(PRACTICAL_EVALUATOR_SCRIPT),
            "evaluate-lesson",
            "--course",
            str(tmp_path / "courses" / "practical-concurrency"),
            "--section",
            s_data["active_section"]["section_id"],
            "--submission",
            "",
        ],
        capture_output=True,
        text=True,
    )
    assert res_eval_empty.returncode == 0
    empty_result = json.loads(res_eval_empty.stdout)
    assert empty_result["verdict"] == "NEEDS_WORK"
    assert empty_result["score"] == 0

    # 4. Advance concept (first concept of section)
    res_adv1 = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "advance",
            "--course",
            "practical-concurrency",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_adv1.returncode == 0

    # 5. Advance second concept: should be gated by practical
    res_adv2 = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "advance",
            "--course",
            "practical-concurrency",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_adv2.returncode == 0
    adv2_data = json.loads(res_adv2.stdout)
    assert adv2_data["practical_pending"] is True
    assert adv2_data["section_fully_completed"] is False

    # 6. Submit compliant implementation to Daedalus
    good_code = """
def execute_lab_solution(input_data):
    # Validate boundary conditions
    if input_data is None or len(input_data) == 0:
        raise ValueError("Cannot process empty payload")
    
    # Transform safely with defensive state guard
    return {"status": "ok", "processed": [x * 2 for x in input_data]}
"""
    res_eval_good = subprocess.run(
        [
            sys.executable,
            str(PRACTICAL_EVALUATOR_SCRIPT),
            "evaluate-lesson",
            "--course",
            str(tmp_path / "courses" / "practical-concurrency"),
            "--section",
            s_data["active_section"]["section_id"],
            "--submission",
            good_code,
        ],
        capture_output=True,
        text=True,
    )
    assert res_eval_good.returncode == 0
    good_result = json.loads(res_eval_good.stdout)
    assert good_result["verdict"] == "PASS"
    assert good_result["score"] >= 70

    # 7. Now retry advance: practical passes, section completes and notes are compiled!
    res_adv_final = subprocess.run(
        [
            sys.executable,
            str(TEACH_ENGINE_SCRIPT),
            "advance",
            "--course",
            "practical-concurrency",
            "--workspace",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_adv_final.returncode == 0
    final_data = json.loads(res_adv_final.stdout)
    assert final_data["section_fully_completed"] is True
    assert final_data["notes_compilation"] is not None
