"""tests/test_storage_contract.py — Comprehensive test suite for root _tc/ storage contract and migration.

Validates:
- Fresh workspace bootstrap enforces clean canvas: only _tc/, courses/, portfolio/, and status-board/
  exist at root, with ZERO root .tc/, sources/, plan/, research/, profile/, or roadmap/ directories.
- Canonical _tc/ tree contains scripts, cache, profile, roadmap, research, courses, status, and config.json (0.3.0).
- Visible study material contract: outside _tc/, only courses/<slug>/notes/chapter-XX.md exists for study.
- Consent-gated migration: dry-run inspection plan emits JSON without disk mutations.
- Consent gate enforcement: migrator.py apply strictly aborts without 'APPLY' confirmation.
- Legacy workspace migration: moves legacy .tc/, research/, sources/, plan/, profile/, roadmap/ into
  canonical _tc/ with cryptographic SHA-256 byte parity verification, cleaning up empty legacy folders.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAPPER_SCRIPT = REPO_ROOT / "_tc" / "scripts" / "bootstrapper.py"
MIGRATOR_SCRIPT = REPO_ROOT / "_tc" / "scripts" / "migrator.py"


def sha256_file(path: Path) -> str:
    """Compute sha256 hex digest of file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fresh_bootstrap_canonical_directory_layout(tmp_path: Path):
    """Verify fresh bootstrap creates solely canonical root directories."""
    ws = tmp_path / "fresh_workspace"
    cmd = [sys.executable, str(BOOTSTRAPPER_SCRIPT), "bootstrap", "--target", str(ws)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Bootstrap failed: {res.stderr}"

    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["status"] == "bootstrapped"

    # Invariant 1: Root directory canvas check
    root_dirs = sorted([d.name for d in ws.iterdir() if d.is_dir()])
    assert root_dirs == ["_tc", "courses", "portfolio", "status-board"], (
        f"Unexpected root directories: {root_dirs}"
    )

    # Invariant 2: Zero occurrences of forbidden legacy directories at root
    forbidden_roots = [".tc", "research", "sources", "plan", "profile", "roadmap"]
    for forbidden in forbidden_roots:
        assert not (ws / forbidden).exists(), f"Forbidden legacy directory found at root: {forbidden}"

    # Invariant 3: Canonical _tc/ internal machine tree
    tc_dir = ws / "_tc"
    expected_tc_subdirs = ["cache", "courses", "profile", "research", "roadmap", "scripts", "status"]
    for sub in expected_tc_subdirs:
        assert (tc_dir / sub).is_dir(), f"Missing canonical subdirectory: _tc/{sub}"

    # Invariant 4: Schema version 0.3.0 in _tc/config.json
    config_file = tc_dir / "config.json"
    assert config_file.is_file(), "Missing _tc/config.json"
    config = json.loads(config_file.read_text(encoding="utf-8"))
    assert config["version"] == "0.3.0"
    assert config["framework"] == "TextCourses"

    # Invariant 5: Canonical profile and roadmap memlogs inside _tc/
    assert (tc_dir / "profile" / "preferences.md").is_file()
    assert (tc_dir / "profile" / "memlog.md").is_file()
    assert (tc_dir / "roadmap" / "memlog.md").is_file()

    # Invariant 6: Deployed canonical scripts exist
    assert (tc_dir / "scripts" / "bootstrapper.py").is_file()
    assert (tc_dir / "scripts" / "migrator.py").is_file()
    assert (tc_dir / "scripts" / "memlog.py").is_file()


def test_clean_canvas_study_material_invariants(tmp_path: Path):
    """Verify that only notes/chapter-XX.md exists as study material outside _tc/."""
    ws = tmp_path / "study_workspace"
    subprocess.run([sys.executable, str(BOOTSTRAPPER_SCRIPT), "bootstrap", "--target", str(ws)], check=True)

    # Simulate course creation with notes in visible path
    slug = "dist-consensus"
    course_notes_dir = ws / "courses" / slug / "notes"
    course_notes_dir.mkdir(parents=True, exist_ok=True)
    ch1_notes = course_notes_dir / "chapter-01.md"
    ch1_notes.write_text("# Chapter 1: Consensus Primitives\n\nNotes content.\n", encoding="utf-8")

    # Internal course machine state lives in _tc/courses/<slug>/
    tc_course = ws / "_tc" / "courses" / slug
    tc_course.mkdir(parents=True, exist_ok=True)
    (tc_course / "course.toml").write_text('[course]\nslug = "dist-consensus"\n', encoding="utf-8")
    (tc_course / "memlog.md").write_text("# Course Memlog\n", encoding="utf-8")

    # Verify visible directory for course only contains notes/
    course_visible_items = set(p.name for p in (ws / "courses" / slug).iterdir())
    assert course_visible_items == {"notes"}
    assert (course_notes_dir / "chapter-01.md").is_file()

    # Verify no machine state leaked into visible courses/<slug>/
    assert not (ws / "courses" / slug / "course.toml").exists()
    assert not (ws / "courses" / slug / "memlog.md").exists()
    assert not (ws / "courses" / slug / ".tc").exists()


def test_legacy_migration_dry_run_plan_non_destructive(tmp_path: Path):
    """Verify migrator.py plan inspects legacy directories and emits plan without mutating disk."""
    ws = tmp_path / "legacy_ws"
    ws.mkdir()

    # Populate legacy layout
    legacy_tc = ws / ".tc"
    legacy_tc.mkdir(parents=True)
    (legacy_tc / "config.json").write_text(json.dumps({"version": "0.1.0"}), encoding="utf-8")

    legacy_res = ws / "research" / "systems"
    legacy_res.mkdir(parents=True)
    dossier = legacy_res / "dossier.md"
    dossier.write_text("# Systems Research Dossier\n", encoding="utf-8")

    legacy_src = ws / "sources" / "raw"
    legacy_src.mkdir(parents=True)
    raw_spec = legacy_src / "raft-spec.txt"
    raw_spec.write_text("Raft protocol RFC text\n", encoding="utf-8")

    legacy_plan = ws / "plan"
    legacy_plan.mkdir(parents=True)
    pref = legacy_plan / "preferences.md"
    pref.write_text("---\nrole: 'Kernel Hacker'\n---\n", encoding="utf-8")

    # Run dry-run plan
    cmd = [sys.executable, str(MIGRATOR_SCRIPT), "plan", "--workspace", str(ws), "--json"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Plan failed: {res.stderr}"

    plan_data = json.loads(res.stdout)
    assert plan_data["ok"] is True
    assert plan_data["status"] == "needs_migration"
    assert plan_data["actions_count"] > 0

    # Ensure plan markdown was generated
    plan_file = Path(plan_data["plan_file"])
    assert plan_file.is_file()
    plan_text = plan_file.read_text(encoding="utf-8")
    assert "Consent Gate Notice" in plan_text
    assert "--confirm APPLY" in plan_text

    # CRITICAL: Verify ZERO disk mutations during plan
    assert legacy_tc.is_dir()
    assert dossier.is_file()
    assert raw_spec.is_file()
    assert pref.is_file()
    assert not (ws / "_tc" / "research" / "systems" / "dossier.md").exists()
    assert not (ws / "_tc" / "sources" / "raw" / "raft-spec.txt").exists()


def test_legacy_migration_consent_gate_enforcement(tmp_path: Path):
    """Verify apply strictly aborts without confirmation token and leaves files intact."""
    ws = tmp_path / "unconfirmed_ws"
    ws.mkdir()
    (ws / ".tc").mkdir()
    (ws / ".tc" / "config.json").write_text(json.dumps({"version": "0.2.0"}), encoding="utf-8")
    (ws / "research").mkdir()
    (ws / "research" / "notes.txt").write_text("precious research\n", encoding="utf-8")

    # 1. Apply with no confirm token -> fails
    cmd_no_token = [sys.executable, str(MIGRATOR_SCRIPT), "apply", "--workspace", str(ws), "--json"]
    res = subprocess.run(cmd_no_token, capture_output=True, text=True)
    assert res.returncode == 1
    err_json = json.loads(res.stderr)
    assert "Explicit confirmation required" in err_json["error"]

    # 2. Apply with incorrect token -> fails
    cmd_wrong_token = [
        sys.executable,
        str(MIGRATOR_SCRIPT),
        "apply",
        "--workspace",
        str(ws),
        "--token",
        "CONFIRM",
        "--json",
    ]
    res_wrong = subprocess.run(cmd_wrong_token, capture_output=True, text=True)
    assert res_wrong.returncode == 1

    # Verify no mutation occurred
    assert (ws / "research" / "notes.txt").is_file()
    assert not (ws / "_tc" / "research" / "notes.txt").exists()


def test_legacy_migration_apply_parity_verification_and_cleanup(tmp_path: Path):
    """Verify apply migrates legacy directories to _tc/, verifies parity, and removes legacy folders."""
    ws = tmp_path / "migrating_ws"
    ws.mkdir()

    # 1. Setup legacy folders and files
    (ws / ".tc").mkdir(parents=True)
    (ws / ".tc" / "config.json").write_text(json.dumps({"version": "0.2.0", "custom_setting": 42}), encoding="utf-8")
    (ws / ".tc" / "cache").mkdir(parents=True)
    (ws / ".tc" / "cache" / "trace.jsonl").write_text('{"event": "init"}\n', encoding="utf-8")

    (ws / "research" / "os-kernel").mkdir(parents=True)
    res_file = ws / "research" / "os-kernel" / "dossier.md"
    res_content = "# Operating System Internals\n\nPage tables and virtual memory.\n"
    res_file.write_text(res_content, encoding="utf-8")
    res_hash = sha256_file(res_file)

    (ws / "sources" / "raw").mkdir(parents=True)
    src_file = ws / "sources" / "raw" / "intel-manual.pdf"
    src_content = "Binary PDF mock content 101010101"
    src_file.write_text(src_content, encoding="utf-8")
    src_hash = sha256_file(src_file)

    (ws / "plan").mkdir(parents=True)
    pref_file = ws / "plan" / "preferences.md"
    pref_content = "---\nrole: 'Systems Architect'\nteacher: 'feynman'\n---\n"
    pref_file.write_text(pref_content, encoding="utf-8")
    pref_hash = sha256_file(pref_file)

    (ws / "profile").mkdir(parents=True)
    old_memlog = ws / "profile" / "memlog.md"
    old_memlog.write_text("- (milestone) Old milestone.\n", encoding="utf-8")
    memlog_hash = sha256_file(old_memlog)

    (ws / "roadmap").mkdir(parents=True)
    old_roadmap = ws / "roadmap" / "roadmap.toml"
    old_roadmap.write_text('[roadmap]\ntitle = "Systems Track"\n', encoding="utf-8")
    roadmap_hash = sha256_file(old_roadmap)

    # 2. Run apply with APPLY token
    cmd_apply = [
        sys.executable,
        str(MIGRATOR_SCRIPT),
        "apply",
        "--workspace",
        str(ws),
        "--token",
        "APPLY",
        "--json",
    ]
    res_apply = subprocess.run(cmd_apply, capture_output=True, text=True)
    assert res_apply.returncode == 0, f"Apply failed: {res_apply.stderr}"

    apply_data = json.loads(res_apply.stdout)
    assert apply_data["ok"] is True
    assert apply_data["migrated"] is True
    assert apply_data["version"] == "0.3.0"

    # 3. Verify cryptographic SHA-256 byte parity of all migrated files
    dest_res = ws / "_tc" / "research" / "os-kernel" / "dossier.md"
    assert dest_res.is_file()
    assert sha256_file(dest_res) == res_hash

    dest_src = ws / "_tc" / "sources" / "raw" / "intel-manual.pdf"
    assert dest_src.is_file()
    assert sha256_file(dest_src) == src_hash

    dest_pref = ws / "_tc" / "profile" / "preferences.md"
    assert dest_pref.is_file()
    assert sha256_file(dest_pref) == pref_hash

    dest_memlog = ws / "_tc" / "profile" / "memlog.md"
    assert dest_memlog.is_file()
    assert sha256_file(dest_memlog) == memlog_hash

    dest_roadmap = ws / "_tc" / "roadmap" / "roadmap.toml"
    assert dest_roadmap.is_file()
    assert sha256_file(dest_roadmap) == roadmap_hash

    # 4. Verify updated canonical config schema 0.3.0
    config_file = ws / "_tc" / "config.json"
    assert config_file.is_file()
    config = json.loads(config_file.read_text(encoding="utf-8"))
    assert config["version"] == "0.3.0"
    assert config.get("custom_setting") == 42

    # 5. Verify empty legacy folders were safely removed
    for legacy_dir in [".tc", "research", "sources", "plan", "profile", "roadmap"]:
        assert not (ws / legacy_dir).exists(), f"Legacy directory was not removed after migration: {legacy_dir}"

    # 6. Verify health check now reports healthy
    cmd_check = [sys.executable, str(MIGRATOR_SCRIPT), "check", "--workspace", str(ws), "--json"]
    res_check = subprocess.run(cmd_check, capture_output=True, text=True)
    assert res_check.returncode == 0
    health = json.loads(res_check.stdout)
    assert health["status"] == "healthy"
