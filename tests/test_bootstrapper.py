"""test_bootstrapper.py — Unit tests for TextCourses bootstrapper and scanner (bootstrapper.py).

Validates:
- PEP 723 inline script metadata (Python >= 3.11)
- Workspace bootstrapping layout (.tc/, plan/, courses/, portfolio/, _tc/scripts/)
- Canonical runtime script deployment
- Non-destructive updates (preserves existing config.json, preferences.md, manifests)
- Scanner recommendations (/tc-create, /tc-teach, /tc-test-me, /tc-practicals)
- Preferences management (get/set frontmatter and directives)
- Zero BMad references across skill files and scripts (AD-6, FR-1, FR-2, FR-3)
"""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "_tc" / "scripts"))
from bootstrapper import (
    bootstrap_workspace,
    compile_preferences_content,
    parse_preferences_file,
    scan_workspace,
)

BOOTSTRAPPER_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "bootstrapper.py"
SKILL_BOOTSTRAPPER_SCRIPT = Path(__file__).parent.parent / "skills" / "tc-init" / "scripts" / "bootstrapper.py"


def run_bootstrapper(*args: str) -> subprocess.CompletedProcess[str]:
    """Helper to run bootstrapper.py CLI and capture stdout/stderr."""
    cmd = [sys.executable, str(BOOTSTRAPPER_SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_bootstrapper_help():
    """Verify help subcommand displays usage and available subcommands."""
    result = run_bootstrapper("--help")
    assert result.returncode == 0
    assert "bootstrapper.py" in result.stdout
    assert "bootstrap" in result.stdout
    assert "init" in result.stdout
    assert "scan" in result.stdout
    assert "status" in result.stdout
    assert "preferences" in result.stdout
    assert "set-preferences" in result.stdout


def test_pep_723_metadata():
    """Verify bootstrapper.py contains valid PEP 723 metadata with Python >=3.11."""
    content = BOOTSTRAPPER_SCRIPT.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert 'requires-python = ">=3.11"' in content
    assert "# ///" in content


def test_bootstrap_empty_workspace(tmp_path: Path):
    """Verify bootstrap creates required layout and copies runtime scripts."""
    ws = tmp_path / "new_workspace"
    result = run_bootstrapper("bootstrap", "--path", str(ws))
    assert result.returncode == 0

    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["status"] == "bootstrapped"
    assert ws.exists()

    # Required directory layout
    assert (ws / ".tc").is_dir()
    assert (ws / ".tc" / "cache").is_dir()
    assert (ws / ".tc" / "research").is_dir()
    assert (ws / "plan").is_dir()
    assert (ws / "plan" / "sources").is_dir()
    assert (ws / "courses").is_dir()
    assert (ws / "portfolio").is_dir()
    assert (ws / "_tc" / "scripts").is_dir()

    # .tc/config.json
    config_file = ws / ".tc" / "config.json"
    assert config_file.is_file()
    config_data = json.loads(config_file.read_text(encoding="utf-8"))
    assert config_data["framework"] == "TextCourses"
    assert config_data["version"] == "0.1.0"
    assert "created_at" in config_data

    # plan/preferences.md
    pref_file = ws / "plan" / "preferences.md"
    assert pref_file.is_file()
    pref_content = pref_file.read_text(encoding="utf-8")
    assert pref_content.startswith("---")
    assert "role:" in pref_content
    assert "domain_experience:" in pref_content
    assert "explanation_density:" in pref_content
    assert "style_profile:" in pref_content

    # Deployed runtime scripts in _tc/scripts/
    scripts_dir = ws / "_tc" / "scripts"
    assert (scripts_dir / "manifest.py").is_file()
    assert (scripts_dir / "ledger.py").is_file()
    assert (scripts_dir / "dag.py").is_file()
    assert (scripts_dir / "context.py").is_file()
    assert (scripts_dir / "hash_tracker.py").is_file()
    assert (scripts_dir / "bootstrapper.py").is_file()


def test_init_alias_command(tmp_path: Path):
    """Verify 'init' acts as an exact alias for 'bootstrap'."""
    ws = tmp_path / "init_ws"
    result = run_bootstrapper("init", "--path", str(ws))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert (ws / ".tc" / "config.json").is_file()
    assert (ws / "plan" / "preferences.md").is_file()


def test_bootstrap_does_not_overwrite_existing(tmp_path: Path):
    """Verify running bootstrap does not overwrite existing config, preferences, or notes."""
    ws = tmp_path / "existing_ws"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / ".tc").mkdir(parents=True, exist_ok=True)
    (ws / "plan").mkdir(parents=True, exist_ok=True)

    custom_config = {"version": "9.9.9", "framework": "TextCourses", "custom": True}
    (ws / ".tc" / "config.json").write_text(json.dumps(custom_config), encoding="utf-8")

    custom_pref = "---\nrole: 'Custom Architect'\n---\n# Custom Notes\nDo not overwrite me!\n"
    (ws / "plan" / "preferences.md").write_text(custom_pref, encoding="utf-8")

    result = run_bootstrapper("bootstrap", "--path", str(ws))
    assert result.returncode == 0

    # Ensure config and preferences were preserved
    saved_config = json.loads((ws / ".tc" / "config.json").read_text(encoding="utf-8"))
    assert saved_config.get("version") == "9.9.9"
    assert saved_config.get("custom") is True

    saved_pref = (ws / "plan" / "preferences.md").read_text(encoding="utf-8")
    assert "Custom Architect" in saved_pref
    assert "Do not overwrite me!" in saved_pref


def test_scan_empty_workspace(tmp_path: Path):
    """Verify scanning an empty workspace returns status empty and recommendation /tc-create."""
    ws = tmp_path / "empty_ws"
    run_bootstrapper("bootstrap", "--path", str(ws))

    result = run_bootstrapper("scan", "--path", str(ws))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["status"] == "empty"
    assert data["recommendation"] == "/tc-create"


def test_scan_nonexistent_directory(tmp_path: Path):
    """Verify scanning a non-existent directory exits 1 with error JSON."""
    nonexistent = tmp_path / "no_such_dir"
    result = run_bootstrapper("scan", "--path", str(nonexistent))
    assert result.returncode == 1
    data = json.loads(result.stderr)
    assert data["ok"] is False
    assert "does not exist" in data["error"].lower()


def test_scan_in_progress_course(tmp_path: Path):
    """Verify scanning a course with an in_progress section recommends /tc-teach."""
    ws = tmp_path / "teach_ws"
    run_bootstrapper("bootstrap", "--path", str(ws))

    course_dir = ws / "courses" / "course-01-raft"
    course_dir.mkdir(parents=True, exist_ok=True)
    manifest = """
[course]
slug = "course-01-raft"
title = "Distributed Systems with Raft"
status = "in_progress"

[[chapters]]
id = 1
slug = "ch-01-basics"
title = "Basics"

[[chapters.sections]]
id = 1
slug = "sec-01-election"
title = "Leader Election"
status = "completed"

[[chapters.sections]]
id = 2
slug = "sec-02-replication"
title = "Log Replication"
status = "in_progress"
"""
    (course_dir / "course.toml").write_text(manifest.strip(), encoding="utf-8")

    result = run_bootstrapper("scan", "--path", str(ws))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["status"] == "in_progress"
    assert data["recommendation"] == "/tc-teach"
    assert data["active_course"] == "course-01-raft"
    assert data["active_section"]["section_id"] == 2


def test_scan_review_chapter(tmp_path: Path):
    """Verify scanning when all chapter sections are in review recommends /tc-test-me."""
    ws = tmp_path / "test_me_ws"
    run_bootstrapper("bootstrap", "--path", str(ws))

    course_dir = ws / "courses" / "course-01-concurrency"
    course_dir.mkdir(parents=True, exist_ok=True)
    manifest = """
[course]
slug = "course-01-concurrency"
title = "Lock-Free Concurrency"
status = "in_progress"

[[chapters]]
id = 1
slug = "ch-01-atomics"
title = "Atomics"

[[chapters.sections]]
id = 1
slug = "sec-01-cas"
title = "Compare and Swap"
status = "review"

[[chapters.sections]]
id = 2
slug = "sec-02-fences"
title = "Memory Fences"
status = "review"
"""
    (course_dir / "course.toml").write_text(manifest.strip(), encoding="utf-8")

    result = run_bootstrapper("scan", "--path", str(ws))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["status"] == "review"
    assert data["recommendation"] == "/tc-test-me"
    assert data["active_course"] == "course-01-concurrency"


def test_scan_completed_course(tmp_path: Path):
    """Verify scanning a completed course recommends /tc-practicals."""
    ws = tmp_path / "practicals_ws"
    run_bootstrapper("bootstrap", "--path", str(ws))

    course_dir = ws / "courses" / "course-01-rust"
    course_dir.mkdir(parents=True, exist_ok=True)
    manifest = """
[course]
slug = "course-01-rust"
title = "Rust Systems"
status = "completed"

[[chapters]]
id = 1
slug = "ch-01-lifetimes"
title = "Lifetimes"

[[chapters.sections]]
id = 1
slug = "sec-01-borrowing"
title = "Borrowing"
status = "completed"
"""
    (course_dir / "course.toml").write_text(manifest.strip(), encoding="utf-8")

    result = run_bootstrapper("scan", "--path", str(ws))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["status"] == "completed"
    assert data["recommendation"] == "/tc-practicals"


def test_scan_single_course_folder(tmp_path: Path):
    """Verify scanning works directly when target path points to a course directory."""
    course_dir = tmp_path / "course-direct"
    course_dir.mkdir(parents=True, exist_ok=True)
    manifest = """
[course]
slug = "course-direct"
title = "Direct Course"
status = "in_progress"

[[chapters]]
id = 1
slug = "ch-01"
title = "Ch 1"

[[chapters.sections]]
id = 1
slug = "sec-01"
title = "Sec 1"
status = "in_progress"
"""
    (course_dir / "course.toml").write_text(manifest.strip(), encoding="utf-8")

    result = run_bootstrapper("scan", "--path", str(course_dir))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["status"] == "in_progress"
    assert data["recommendation"] == "/tc-teach"


def test_status_command(tmp_path: Path):
    """Verify status command returns comprehensive workspace state."""
    ws = tmp_path / "status_ws"
    run_bootstrapper("bootstrap", "--path", str(ws))

    result = run_bootstrapper("status", "--path", str(ws))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["is_bootstrapped"] is True
    assert data["status"] == "empty"
    assert data["recommendation"] == "/tc-create"
    assert "preferences" in data
    assert data["preferences"]["role"] == "Software Engineer (Backend / Systems / DevOps)"


def test_preferences_get_and_set(tmp_path: Path):
    """Verify reading and updating preferences via CLI subcommands."""
    ws = tmp_path / "pref_ws"
    run_bootstrapper("bootstrap", "--path", str(ws))

    # Get preferences
    res_get = run_bootstrapper("preferences", "--path", str(ws))
    assert res_get.returncode == 0
    data_get = json.loads(res_get.stdout)
    assert data_get["ok"] is True
    assert "role" in data_get["preferences"]

    # Set custom preferences
    res_set = run_bootstrapper(
        "set-preferences",
        "--path", str(ws),
        "--role", "Data Scientist / ML Engineer / Quant",
        "--experience", "Experienced Practitioner",
        "--density", "Deep-Dive Technical (Comprehensive & Academic) (~250–350 words per concept)",
        "--styles", "direct_technical,math",
    )
    assert res_set.returncode == 0

    # Verify updated
    res_get2 = run_bootstrapper("preferences", "--path", str(ws))
    data_get2 = json.loads(res_get2.stdout)
    assert data_get2["preferences"]["role"] == "Data Scientist / ML Engineer / Quant"
    assert "Direct Technical & Internals + First-Principles & Math" in data_get2["preferences"]["style_profile"]


def test_zero_bmad_references():
    """Verify STRICT zero BMad references across tc-init skill, scripts, and assets."""
    files_to_check = [
        Path(__file__).parent.parent / "skills" / "tc-init" / "SKILL.md",
        Path(__file__).parent.parent / "skills" / "tc-init" / "customize.toml",
        Path(__file__).parent.parent / "skills" / "tc-init" / "assets" / "style-previews.md",
        BOOTSTRAPPER_SCRIPT,
        SKILL_BOOTSTRAPPER_SCRIPT,
    ]
    bmad_patterns = ["bmad", "_bmad", "bmad-build", "render_skill.py"]

    for f in files_to_check:
        assert f.is_file(), f"Expected file {f} to exist"
        text = f.read_text(encoding="utf-8").lower()
        for pattern in bmad_patterns:
            assert pattern not in text, f"Found forbidden BMad reference '{pattern}' in {f}"


def test_python_api_functions(tmp_path: Path):
    """Verify programmatic Python API functions work as expected."""
    ws = tmp_path / "py_api_ws"
    boot_res = bootstrap_workspace(ws)
    assert boot_res["ok"] is True
    assert boot_res["status"] == "bootstrapped"

    scan_res = scan_workspace(ws)
    assert scan_res["ok"] is True
    assert scan_res["status"] == "empty"
    assert scan_res["recommendation"] == "/tc-create"

    # Test compile_preferences_content
    pref_text = compile_preferences_content(
        role="Frontend / Full-Stack Developer",
        domain_experience="Familiar with Basics",
        explanation_density="Example-Driven",
        styles=["code_first", "analogy"],
    )
    assert "Frontend / Full-Stack Developer" in pref_text
    assert "Code & Case-First + Analogy & Intuition" in pref_text


def test_bootstrap_from_skill_bundled_runtime(tmp_path: Path):
    """Verify bootstrapping via skills/tc-init/scripts/bootstrapper.py deploys all 16 runtime scripts."""
    ws = tmp_path / "standalone_ws"
    cmd = [sys.executable, str(SKILL_BOOTSTRAPPER_SCRIPT), "bootstrap", "--path", str(ws)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["status"] == "bootstrapped"

    expected_scripts = [
        "auditor.py",
        "bootstrapper.py",
        "context.py",
        "course_builder.py",
        "dag.py",
        "diagnostic_tester.py",
        "hash_tracker.py",
        "ledger.py",
        "lesson_tracker.py",
        "manifest.py",
        "migrator.py",
        "notes_compiler.py",
        "practical_evaluator.py",
        "redirector.py",
        "scout.py",
        "teach_engine.py",
    ]
    scripts_dir = ws / "_tc" / "scripts"
    assert scripts_dir.is_dir()
    for s in expected_scripts:
        assert (scripts_dir / s).is_file(), f"Missing deployed script: {s}"

