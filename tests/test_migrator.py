"""tests/test_migrator.py — Comprehensive test suite for consent-gated schema migrator."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

MIGRATOR_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "migrator.py"
SKILL_FILE = Path(__file__).parent.parent / "skills" / "tc-migrate" / "SKILL.md"


def test_migrator_cli_help():
    """Verify that migrator CLI prints help message and exits 0."""
    res = subprocess.run([sys.executable, str(MIGRATOR_SCRIPT), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "check" in res.stdout
    assert "plan" in res.stdout
    assert "apply" in res.stdout


def test_migrator_pep_723_metadata():
    """Verify script contains valid PEP 723 metadata header."""
    content = MIGRATOR_SCRIPT.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert 'requires-python = ">=3.11"' in content
    assert "tomli-w>=" in content
    assert "# ///" in content


def test_zero_bmad_references():
    """Verify strict zero-BMad references in scripts and skill documentation."""
    for target in [MIGRATOR_SCRIPT, SKILL_FILE]:
        text = target.read_text(encoding="utf-8")
        assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad mention in {target}"


def test_check_health_needs_migration(tmp_path: Path):
    """Verify check identifies outdated or partially initialized workspace."""
    # Create outdated 0.1.0 workspace with missing .tc/cache and portfolio
    tc_dir = tmp_path / ".tc"
    tc_dir.mkdir(parents=True)
    (tc_dir / "config.json").write_text(json.dumps({"version": "0.1.0"}), encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(MIGRATOR_SCRIPT), "check", "--path", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["status"] == "needs_migration"
    assert data["current_version"] == "0.1.0"
    assert data["target_version"] == "0.2.0"
    assert "portfolio" in data["missing_directories"]


def test_dry_run_plan_does_not_mutate_disk(tmp_path: Path):
    """Verify plan outputs report and writes migration-plan.md without creating directories."""
    tc_dir = tmp_path / ".tc"
    tc_dir.mkdir(parents=True)
    (tc_dir / "config.json").write_text(json.dumps({"version": "0.1.0"}), encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(MIGRATOR_SCRIPT), "plan", "--path", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["actions_count"] > 0

    plan_md = tmp_path / "migration-plan.md"
    assert plan_md.is_file()
    report_text = plan_md.read_text(encoding="utf-8")
    assert "Consent Gate Notice" in report_text
    assert "--confirm APPLY" in report_text

    # Disk must NOT have been mutated
    assert not (tmp_path / "portfolio").exists()
    assert not (tmp_path / ".tc" / "cache").exists()


def test_apply_without_confirm_fails_immediately(tmp_path: Path):
    """Verify apply without --confirm fails with exit code 1 and mutates nothing."""
    tc_dir = tmp_path / ".tc"
    tc_dir.mkdir(parents=True)
    (tc_dir / "config.json").write_text(json.dumps({"version": "0.1.0"}), encoding="utf-8")

    res = subprocess.run(
        [sys.executable, str(MIGRATOR_SCRIPT), "apply", "--path", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    err_data = json.loads(res.stderr)
    assert err_data["ok"] is False
    assert "Explicit confirmation required" in err_data["error"]

    # Verify zero mutations
    assert not (tmp_path / "portfolio").exists()


def test_apply_with_wrong_token_fails(tmp_path: Path):
    """Verify apply with wrong token like 'YES' fails with exit code 1."""
    tc_dir = tmp_path / ".tc"
    tc_dir.mkdir(parents=True)
    (tc_dir / "config.json").write_text(json.dumps({"version": "0.1.0"}), encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(MIGRATOR_SCRIPT),
            "apply",
            "--path",
            str(tmp_path),
            "--confirm",
            "YES",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    err_data = json.loads(res.stderr)
    assert "Explicit confirmation required" in err_data["error"]


def test_apply_with_confirm_apply_succeeds(tmp_path: Path):
    """Verify apply with --confirm APPLY executes all planned operations atomically."""
    tc_dir = tmp_path / ".tc"
    tc_dir.mkdir(parents=True)
    (tc_dir / "config.json").write_text(json.dumps({"version": "0.1.0", "settings": {"test": 123}}), encoding="utf-8")

    # Generate plan first
    subprocess.run(
        [sys.executable, str(MIGRATOR_SCRIPT), "plan", "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert (tmp_path / "migration-plan.md").exists()

    # Apply with correct confirmation token
    res = subprocess.run(
        [
            sys.executable,
            str(MIGRATOR_SCRIPT),
            "apply",
            "--path",
            str(tmp_path),
            "--confirm",
            "APPLY",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["migrated"] is True
    assert data["version"] == "0.2.0"

    # Verify mutations
    assert (tmp_path / "portfolio").is_dir()
    assert (tmp_path / ".tc" / "cache").is_dir()
    assert (tmp_path / ".tc" / "research").is_dir()

    # Verify config updated
    updated_config = json.loads((tc_dir / "config.json").read_text(encoding="utf-8"))
    assert updated_config["version"] == "0.2.0"
    assert updated_config["settings"]["test"] == 123

    # Verify temporary migration-plan.md was cleaned up
    assert not (tmp_path / "migration-plan.md").exists()

    # Verify check now reports healthy
    res_check = subprocess.run(
        [sys.executable, str(MIGRATOR_SCRIPT), "check", "--path", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res_check.returncode == 0
    check_data = json.loads(res_check.stdout)
    assert check_data["status"] == "healthy"
