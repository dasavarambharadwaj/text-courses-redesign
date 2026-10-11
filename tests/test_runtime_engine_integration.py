"""test_runtime_engine_integration.py — End-to-end integration test suite for TextCourses deterministic engine.

Validates that all five Epic 1 deterministic runtime scripts operate harmoniously:
- manifest.py (atomic TOML manifest manager)
- dag.py (prerequisite DAG validator & cycle checker)
- hash_tracker.py (SHA-256 source delta tracker)
- context.py (stage-aware context loading manifest engine)
- ledger.py (atomic assessment logger & compact query summarizer)
"""

from __future__ import annotations

import concurrent.futures
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import tomli_w

SCRIPTS_DIR = Path(__file__).parent.parent / "_tc" / "scripts"
MANIFEST_SCRIPT = SCRIPTS_DIR / "manifest.py"
DAG_SCRIPT = SCRIPTS_DIR / "dag.py"
HASH_TRACKER_SCRIPT = SCRIPTS_DIR / "hash_tracker.py"
CONTEXT_SCRIPT = SCRIPTS_DIR / "context.py"
LEDGER_SCRIPT = SCRIPTS_DIR / "ledger.py"
COURSE_BUILDER_SCRIPT = SCRIPTS_DIR / "course_builder.py"
TEACH_ENGINE_SCRIPT = SCRIPTS_DIR / "teach_engine.py"
NOTES_COMPILER_SCRIPT = SCRIPTS_DIR / "notes_compiler.py"
DIAGNOSTIC_TESTER_SCRIPT = SCRIPTS_DIR / "diagnostic_tester.py"
PRACTICAL_EVALUATOR_SCRIPT = SCRIPTS_DIR / "practical_evaluator.py"


def run_script(script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Helper to run any runtime script via python CLI and capture output."""
    cmd = [sys.executable, str(script_path), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_full_curriculum_lifecycle_integration(tmp_path: Path):
    """End-to-end test simulating a full workspace lifecycle across all 5 engine scripts.

    Workflow:
    1. Ingest sources in plan/sources/ and snapshot with hash_tracker.py
    2. Initialize course with manifest.py
    3. Validate prerequisite graph with dag.py and compute topological order
    4. Enforce stage context boundaries with context.py
    5. Log diagnostic assessments and query compact summaries with ledger.py
    6. Advance sections and course status with manifest.py
    7. Detect source file updates via hash_tracker.py diff and verify drift
    """
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    # Step 1: Initialize Sources and Snapshot with hash_tracker.py
    sources_dir = workspace_root / "plan" / "sources"
    sources_dir.mkdir(parents=True)
    syllabus_file = sources_dir / "async_python_syllabus.md"
    syllabus_file.write_text("# Async Python Mastery\n- Coroutines\n- Event Loop\n- Tasks\n", encoding="utf-8")
    ref_file = sources_dir / "pep_492.txt"
    ref_file.write_text("PEP 492 Coroutines with async and await syntax\n", encoding="utf-8")

    manifest_output = sources_dir / "ledger.toml"
    snap_res = run_script(
        HASH_TRACKER_SCRIPT,
        "snapshot",
        "--path", str(sources_dir),
        "--output", str(manifest_output),
    )
    assert snap_res.returncode == 0
    snap_data = json.loads(snap_res.stdout)
    assert snap_data["ok"] is True
    assert snap_data["count"] == 2
    assert "async_python_syllabus.md" in snap_data["files"]
    assert "pep_492.txt" in snap_data["files"]
    assert manifest_output.exists()

    # Verify initial source integrity
    ver_res = run_script(
        HASH_TRACKER_SCRIPT,
        "verify",
        "--path", str(sources_dir),
        "--manifest", str(manifest_output),
    )
    assert ver_res.returncode == 0
    ver_data = json.loads(ver_res.stdout)
    assert ver_data["ok"] is True
    assert ver_data["verified"] is True

    # Step 2: Initialize Course Manifest with manifest.py
    course_dir = workspace_root / "courses" / "course-01-async-python"
    course_dir.mkdir(parents=True)

    init_res = run_script(
        MANIFEST_SCRIPT,
        "init-course",
        "--path", str(course_dir),
        "--slug", "async-python",
        "--title", "Async Python Mastery",
        "--archetype", "deep_dive",
    )
    assert init_res.returncode == 0
    course_toml_path = course_dir / "course.toml"
    assert course_toml_path.exists()

    # Populate course with chapters, sections, and prerequisite dependencies
    course_structure = {
        "course": {
            "slug": "async-python",
            "title": "Async Python Mastery",
            "archetype": "deep_dive",
            "status": "not_started",
        },
        "chapters": [
            {
                "id": 1,
                "slug": "ch-01-event-loop",
                "title": "Event Loop Foundations",
                "prerequisites": [],
                "sections": [
                    {
                        "id": 1,
                        "slug": "sec-01-coroutines",
                        "title": "Coroutines and Futures",
                        "status": "not_started",
                        "prerequisites": [],
                    },
                    {
                        "id": 2,
                        "slug": "sec-02-event-loop-internals",
                        "title": "Event Loop Internals",
                        "status": "not_started",
                        "prerequisites": [1],
                    },
                ],
            },
            {
                "id": 2,
                "slug": "ch-02-concurrency-patterns",
                "title": "Concurrency Patterns",
                "prerequisites": [1],
                "sections": [
                    {
                        "id": 3,
                        "slug": "sec-03-task-groups",
                        "title": "TaskGroups and Cancellation",
                        "status": "not_started",
                        "prerequisites": [2],
                    },
                ],
            },
        ],
    }
    # Atomic write to course.toml
    temp_file = course_toml_path.with_suffix(".tmp")
    with open(temp_file, "wb") as f:
        tomli_w.dump(course_structure, f)
    temp_file.replace(course_toml_path)

    # Step 3: Validate DAG with dag.py
    dag_val = run_script(DAG_SCRIPT, "validate", "--path", str(course_dir))
    assert dag_val.returncode == 0
    dag_data = json.loads(dag_val.stdout)
    assert dag_data["ok"] is True
    assert dag_data["valid"] is True

    dag_order = run_script(DAG_SCRIPT, "order", "--path", str(course_dir))
    assert dag_order.returncode == 0
    order_data = json.loads(dag_order.stdout)
    assert order_data["ok"] is True
    assert order_data["order"] == [1, 2, 3]

    # Create section files on disk
    sec1_dir = course_dir / "ch-01-event-loop" / "sec-01-coroutines"
    sec1_dir.mkdir(parents=True)
    sec1_lp = sec1_dir / "lesson-plan.md"
    sec1_lp.write_text("# Coroutines Lesson Plan\n- [ ] Generator to Coroutine\n- [ ] Awaitables\n", encoding="utf-8")
    sec1_notes = sec1_dir / "notes.md"
    sec1_notes.write_text("# Coroutines Notes\nSummary of coroutines\n", encoding="utf-8")

    sec2_dir = course_dir / "ch-01-event-loop" / "sec-02-event-loop-internals"
    sec2_dir.mkdir(parents=True)
    sec2_lp = sec2_dir / "lesson-plan.md"
    sec2_lp.write_text("# Event Loop Internals Plan\n- [ ] Callbacks\n- [ ] Selectors\n", encoding="utf-8")
    sec2_notes = sec2_dir / "notes.md"
    sec2_notes.write_text("# Event Loop Notes\n", encoding="utf-8")

    # Step 4: Advance Section 1 to in_progress with manifest.py
    adv_res = run_script(
        MANIFEST_SCRIPT,
        "advance",
        "--path", str(course_dir),
        "--chapter", "1",
        "--section", "1",
        "--status", "in_progress",
    )
    assert adv_res.returncode == 0
    adv_data = json.loads(adv_res.stdout)
    assert adv_data["ok"] is True
    assert adv_data["status"] == "in_progress"
    assert adv_data["course_status"] == "in_progress"

    # Step 5: Verify Context Loading Manifest with context.py
    ctx_res = run_script(
        CONTEXT_SCRIPT,
        "get-manifest",
        "--skill", "tc-teach",
        "--path", str(course_dir),
    )
    assert ctx_res.returncode == 0
    ctx_data = json.loads(ctx_res.stdout)
    assert ctx_data["ok"] is True
    assert ctx_data["active_section"]["id"] == 1
    assert any("course.toml" in f for f in ctx_data["authorized_files"])
    assert any("sec-01-coroutines/lesson-plan.md" in f or "lesson-plan.md" in f for f in ctx_data["authorized_files"])

    # Verify context read authorization check
    chk_res = run_script(
        CONTEXT_SCRIPT,
        "check",
        "--skill", "tc-teach",
        "--file", str(sec1_lp),
        "--path", str(course_dir),
    )
    assert chk_res.returncode == 0
    chk_data = json.loads(chk_res.stdout)
    assert chk_data["ok"] is True
    assert chk_data["authorized"] is True

    # Step 6: Log Diagnostic Assessments with ledger.py
    ledger_file = course_dir / "test-ledger.jsonl"
    record1 = json.dumps({
        "course": "async-python",
        "chapter": "ch-01-event-loop",
        "section": "sec-01-coroutines",
        "question_type": "hinge_dilemma",
        "prompt": "What happens when you call a coroutine function without awaiting it?",
        "learner_response": "It executes immediately in background.",
        "outcome": "fail",
        "diagnosed_misconception": "MISCONCEPTION_COROUTINE_IMMEDIATE_EXECUTION",
        "remediation_summary": "Coroutines return an unawaited coroutine object; nothing executes until scheduled.",
        "confidence_level": "high",
    })
    app_res1 = run_script(
        LEDGER_SCRIPT,
        "append",
        "--path", str(ledger_file),
        "--record", record1,
    )
    assert app_res1.returncode == 0
    assert ledger_file.exists()

    record2 = json.dumps({
        "course": "async-python",
        "chapter": "ch-01-event-loop",
        "section": "sec-01-coroutines",
        "question_type": "trade_off",
        "prompt": "How do you schedule a coroutine onto the running event loop?",
        "learner_response": "Use asyncio.create_task()",
        "outcome": "pass",
        "confidence_level": "high",
    })
    app_res2 = run_script(
        LEDGER_SCRIPT,
        "append",
        "--path", str(ledger_file),
        "--record", record2,
    )
    assert app_res2.returncode == 0

    # Query compact misconception summary from ledger.py (<100 tokens)
    sum_res = run_script(
        LEDGER_SCRIPT,
        "summarize",
        "--path", str(ledger_file),
        "--course", "async-python",
    )
    assert sum_res.returncode == 0
    sum_data = json.loads(sum_res.stdout)
    assert sum_data["ok"] is True
    assert sum_data["active_misconceptions"] == ["MISCONCEPTION_COROUTINE_IMMEDIATE_EXECUTION"]
    assert sum_data["total_tests"] == 2
    assert sum_data["pass_rate"] == 0.5

    # Step 7: Advance Section 1 to completed
    adv_res2 = run_script(
        MANIFEST_SCRIPT,
        "advance",
        "--path", str(course_dir),
        "--chapter", "1",
        "--section", "1",
        "--status", "completed",
    )
    assert adv_res2.returncode == 0

    # Step 8: Source Delta Detection via hash_tracker.py
    # Learner edits reference doc in plan/sources/
    syllabus_file.write_text("# Async Python Mastery (Updated)\n- Added AnyIO section\n", encoding="utf-8")
    # And adds a new reference
    (sources_dir / "new_tutorial.md").write_text("# Trio & AnyIO\n", encoding="utf-8")

    diff_res = run_script(
        HASH_TRACKER_SCRIPT,
        "diff",
        "--path", str(sources_dir),
        "--manifest", str(manifest_output),
    )
    assert diff_res.returncode == 0
    diff_data = json.loads(diff_res.stdout)
    assert diff_data["ok"] is True
    assert diff_data["has_changes"] is True
    assert diff_data["modified"] == ["async_python_syllabus.md"]
    assert diff_data["added"] == ["new_tutorial.md"]
    assert diff_data["deleted"] == []
    assert diff_data["unchanged"] == ["pep_492.txt"]

    # Verify fails due to detected drift
    ver_drift_res = run_script(
        HASH_TRACKER_SCRIPT,
        "verify",
        "--path", str(sources_dir),
        "--manifest", str(manifest_output),
    )
    assert ver_drift_res.returncode == 1
    ver_drift_data = json.loads(ver_drift_res.stderr)
    assert ver_drift_data["ok"] is False
    assert ver_drift_data["drift"]["modified"] == ["async_python_syllabus.md"]
    assert ver_drift_data["drift"]["added"] == ["new_tutorial.md"]

    # Re-snapshot updates ledger.toml and restores integrity
    resnap = run_script(
        HASH_TRACKER_SCRIPT,
        "snapshot",
        "--path", str(sources_dir),
        "--output", str(manifest_output),
    )
    assert resnap.returncode == 0

    rever = run_script(
        HASH_TRACKER_SCRIPT,
        "verify",
        "--path", str(sources_dir),
        "--manifest", str(manifest_output),
    )
    assert rever.returncode == 0
    assert json.loads(rever.stdout)["ok"] is True


def test_dag_cycle_rejection_in_triad_preflight(tmp_path: Path):
    """Verify that dag.py rejects circular prerequisite graphs deterministically."""
    course_dir = tmp_path / "course-cycle"
    course_dir.mkdir()
    course_toml = course_dir / "course.toml"

    cyclic_manifest = """
[course]
slug = "cyclic-course"
title = "Cyclic Course"
status = "not_started"

[[chapters]]
id = 1
slug = "ch-01"
title = "Chapter 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Section 1"
prerequisites = [2]

[[chapters.sections]]
id = 2
slug = "sec-02"
title = "Section 2"
prerequisites = [1]
"""
    course_toml.write_text(cyclic_manifest.strip(), encoding="utf-8")

    result = run_script(DAG_SCRIPT, "validate", "--path", str(course_dir))
    assert result.returncode == 1
    err_data = json.loads(result.stderr)
    assert err_data["ok"] is False
    assert "cycle" in err_data
    assert set(err_data["cycle"]) == {1, 2}


def test_context_matrix_rejection_boundaries():
    """Verify that context.py strictly prevents concept leaks across skills."""
    # Attempting to load lesson-plan.md during diagnostic testing (tc-test-me) must be rejected
    res = run_script(
        CONTEXT_SCRIPT,
        "check",
        "--skill", "tc-test-me",
        "--file", "courses/rust/ch-01/sec-01/lesson-plan.md",
    )
    assert res.returncode == 1
    data = json.loads(res.stderr)
    assert data["authorized"] is False

    # Attempting to access future section notes must be rejected
    res_future = run_script(
        CONTEXT_SCRIPT,
        "check",
        "--skill", "tc-teach",
        "--file", "future/section-05/notes.md",
    )
    assert res_future.returncode == 1
    data_fut = json.loads(res_future.stderr)
    assert data_fut["authorized"] is False

    # Attempting to access lesson-plan.md in practicals must be rejected
    res_practicals = run_script(
        CONTEXT_SCRIPT,
        "check",
        "--skill", "tc-practicals",
        "--file", "courses/rust/ch-01/sec-01/lesson-plan.md",
    )
    assert res_practicals.returncode == 1
    data_prac = json.loads(res_practicals.stderr)
    assert data_prac["authorized"] is False


def test_concurrent_ledger_append_locking(tmp_path: Path):
    """Stress test atomic ledger appends using multiple concurrent processes."""
    ledger_path = tmp_path / "concurrent-ledger.jsonl"
    num_records = 20

    def append_worker(i: int) -> int:
        record = json.dumps({
            "course": "stress-test",
            "chapter": f"ch-{i % 3}",
            "section": f"sec-{i}",
            "question_type": "hinge",
            "prompt": f"Prompt {i}",
            "learner_response": f"Response {i}",
            "outcome": "pass" if i % 2 == 0 else "fail",
            "worker_id": i,
        })
        res = run_script(LEDGER_SCRIPT, "append", "--path", str(ledger_path), "--record", record)
        return res.returncode

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(append_worker, i) for i in range(num_records)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Every concurrent write must succeed
    assert all(code == 0 for code in results)

    # File must contain exactly num_records valid JSON lines
    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == num_records
    for line in lines:
        parsed = json.loads(line)
        assert "timestamp" in parsed
        assert "worker_id" in parsed


def test_full_apprenticeship_pipeline_e2e(tmp_path: Path):
    """End-to-end test verifying the complete autonomous apprenticeship pipeline:
    1. course_builder.py create scaffolds curriculum filesystem with lesson plan checkboxes
    2. teach_engine.py session inspects active teaching turn and concept
    3. teach_engine.py advance ticks off checklist items in lesson-plan.md and compiles notes
    4. diagnostic_tester.py prepare analyzes cumulative boundary and extracts recap questions
    5. diagnostic_tester.py record logs response in test-ledger.jsonl and promotes section to 'completed'
    6. practical_evaluator.py init-brief generates 4-lens capstone project brief
    7. practical_evaluator.py review grades capstone submission across 4 lenses and marks course completed
    """
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    # Step 1: course_builder.py create
    build_res = run_script(
        COURSE_BUILDER_SCRIPT,
        "create",
        "--slug", "systems-craft",
        "--title", "Systems Craft",
        "--archetype", "applied_creation",
        "--workspace", str(workspace_root),
        "--json",
    )
    assert build_res.returncode == 0, build_res.stderr
    build_data = json.loads(build_res.stdout)
    assert build_data["ok"] is True
    assert build_data["slug"] == "systems-craft"

    course_dir = workspace_root / "courses" / "systems-craft"
    assert course_dir.is_dir()
    manifest_file = course_dir / "course.toml"
    assert manifest_file.is_file()

    # Step 2: teach_engine.py session
    sess_res = run_script(
        TEACH_ENGINE_SCRIPT,
        "session",
        "--course", "systems-craft",
        "--workspace", str(workspace_root),
        "--json",
    )
    assert sess_res.returncode == 0, sess_res.stderr
    sess_data = json.loads(sess_res.stdout)
    assert sess_data["ok"] is True
    active_sec = sess_data["active_section"]
    sec_dir = Path(active_sec["section_dir"])
    assert sec_dir.is_dir()

    lesson_plan_file = sec_dir / "lesson-plan.md"
    assert lesson_plan_file.is_file()
    lp_content = lesson_plan_file.read_text(encoding="utf-8")
    assert "- [ ]" in lp_content  # Markdown checkboxes must be present!

    # Step 3: teach_engine.py advance to completion
    # Count checklist items
    import re
    unchecked = re.findall(r"^-\s*\[\s*\]\s+(.+)$", lp_content, re.MULTILINE)
    assert len(unchecked) >= 1

    # Advance until last concept
    for _ in range(len(unchecked) - 1):
        adv_res = run_script(
            TEACH_ENGINE_SCRIPT,
            "advance",
            "--course", "systems-craft",
            "--workspace", str(workspace_root),
            "--json",
        )
        assert adv_res.returncode == 0, adv_res.stderr

    # Advance final concept with recap
    recap_bullets = [
        "Primitives compose into higher-order abstractions.",
        "Deterministic states prevent race conditions.",
        "Bounded memory layouts guarantee predictable latency.",
    ]
    adv_final = run_script(
        TEACH_ENGINE_SCRIPT,
        "advance",
        "--course", "systems-craft",
        "--workspace", str(workspace_root),
        "--recap", *recap_bullets,
        "--json",
    )
    assert adv_final.returncode == 0, adv_final.stderr
    adv_data = json.loads(adv_final.stdout)
    assert adv_data["ok"] is True
    assert adv_data["section_fully_completed"] is True

    # Verify notes.md was created and section transitioned to review
    notes_file = sec_dir / "notes.md"
    assert notes_file.is_file()
    assert "3-Bullet Recap" in notes_file.read_text(encoding="utf-8")

    with open(manifest_file, "rb") as f:
        course_manifest = tomllib.load(f)
    assert course_manifest["chapters"][0]["sections"][0]["status"] == "review"

    # Step 4: diagnostic_tester.py prepare
    diag_prep = run_script(
        DIAGNOSTIC_TESTER_SCRIPT,
        "prepare",
        "--course", str(course_dir),
    )
    assert diag_prep.returncode == 0, diag_prep.stderr
    prep_data = json.loads(diag_prep.stdout)
    assert prep_data["ok"] is True
    assert prep_data["eligible_sections_count"] >= 1
    assert "active_test_section" in prep_data

    # Step 5: diagnostic_tester.py record
    diag_rec = run_script(
        DIAGNOSTIC_TESTER_SCRIPT,
        "record",
        "--course", str(course_dir),
        "--chapter", active_sec["chapter_id"],
        "--section", active_sec["section_id"],
        "--type", "hinge_scenario",
        "--prompt", "Why do bounded memory layouts eliminate unexpected GC pauses?",
        "--response", "Memory allocations are pre-allocated or statically bounded on the stack.",
        "--outcome", "pass",
    )
    assert diag_rec.returncode == 0, diag_rec.stderr
    rec_data = json.loads(diag_rec.stdout)
    assert rec_data["ok"] is True
    assert rec_data["section_status_updated"] is True
    assert rec_data["new_section_status"] == "completed"

    # Verify section transitioned to completed
    with open(manifest_file, "rb") as f:
        course_manifest = tomllib.load(f)
    assert course_manifest["chapters"][0]["sections"][0]["status"] == "completed"

    # Step 6: practical_evaluator.py init-brief
    init_brief_res = run_script(
        PRACTICAL_EVALUATOR_SCRIPT,
        "init-brief",
        "--course", str(course_dir),
        "--project-id", "01",
    )
    assert init_brief_res.returncode == 0, init_brief_res.stderr
    brief_data = json.loads(init_brief_res.stdout)
    assert brief_data["ok"] is True
    spec_path = Path(brief_data["spec_path"])
    assert spec_path.is_file()

    # Step 7: practical_evaluator.py review
    rev_res = run_script(
        PRACTICAL_EVALUATOR_SCRIPT,
        "review",
        "--course", str(course_dir),
        "--project-id", "01",
        "--verdict", "PASS",
        "--functional-lens", "Full protocol compliance verified with automated tests.",
        "--edge-lens", "Tested boundary conditions, network disconnections, and corrupt frames.",
        "--architecture-lens", "Adheres to sovereignty invariants with zero external daemon requirements.",
        "--verification-lens", "100% test pass rate across unit and stress test suites.",
    )
    assert rev_res.returncode == 0, rev_res.stderr
    rev_data = json.loads(rev_res.stdout)
    assert rev_data["ok"] is True
    assert rev_data["verdict"] == "PASS"

    # Verify final course completion status
    with open(manifest_file, "rb") as f:
        final_manifest = tomllib.load(f)
    assert final_manifest["course"]["status"] == "completed"

