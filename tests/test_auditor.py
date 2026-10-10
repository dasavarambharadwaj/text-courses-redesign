"""tests/test_auditor.py — Comprehensive test suite for curriculum pre-flight auditor."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import tomli_w

AUDITOR_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "auditor.py"
SKILL_FILE = Path(__file__).parent.parent / "skills" / "tc-verify-course" / "SKILL.md"


def test_auditor_cli_help():
    """Verify auditor CLI prints help message and exits 0."""
    res = subprocess.run([sys.executable, str(AUDITOR_SCRIPT), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "audit" in res.stdout


def test_auditor_pep_723_metadata():
    """Verify script contains valid PEP 723 metadata header."""
    content = AUDITOR_SCRIPT.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert 'requires-python = ">=3.11"' in content
    assert "tomli-w>=" in content
    assert "# ///" in content


def test_zero_bmad_references():
    """Verify strict zero-BMad references in scripts and skill documentation."""
    for target in [AUDITOR_SCRIPT, SKILL_FILE]:
        text = target.read_text(encoding="utf-8")
        assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad mention in {target}"


def test_audit_valid_curriculum(tmp_path: Path):
    """Verify valid curriculum passes audit with exit code 0 and 0 critical findings."""
    manifest_data = {
        "course": {
            "id": "concurrent-go",
            "title": "Concurrent Go Systems",
            "archetype": "applied_creation",
        },
        "chapters": [
            {
                "id": "ch-01",
                "title": "Primitives",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Goroutines and Channels",
                        "vocabulary_introduced": ["goroutine", "channel"],
                    },
                    {
                        "id": "sec-02",
                        "title": "Select Multiplexing",
                        "prerequisites": ["sec-01"],
                        "vocabulary_prerequisites": ["channel"],
                        "vocabulary_introduced": ["select"],
                    },
                ],
            }
        ],
    }

    manifest_file = tmp_path / "course.toml"
    with open(manifest_file, "wb") as f:
        tomli_w.dump(manifest_data, f)

    res = subprocess.run(
        [sys.executable, str(AUDITOR_SCRIPT), "audit", "--manifest", str(manifest_file), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["critical_count"] == 0
    assert data["total_sections"] == 2
    assert data["topological_order"] == ["sec-01", "sec-02"]


def test_audit_cyclic_prerequisites_fails(tmp_path: Path):
    """Verify cyclic prerequisites produce CRITICAL finding and exit code 1."""
    manifest_data = {
        "course": {
            "id": "cyclic-course",
            "title": "Cycle Test",
            "archetype": "forensic_dilemma",
        },
        "chapters": [
            {
                "id": "ch-01",
                "title": "Loop",
                "sections": [
                    {"id": "sec-a", "title": "Section A", "prerequisites": ["sec-b"]},
                    {"id": "sec-b", "title": "Section B", "prerequisites": ["sec-a"]},
                ],
            }
        ],
    }

    manifest_file = tmp_path / "course.toml"
    with open(manifest_file, "wb") as f:
        tomli_w.dump(manifest_data, f)

    res = subprocess.run(
        [sys.executable, str(AUDITOR_SCRIPT), "audit", "--manifest", str(manifest_file), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    data = json.loads(res.stderr)
    assert data["ok"] is False
    assert data["critical_count"] >= 1
    codes = [f["code"] for f in data["findings"]]
    assert "DAG_CYCLE" in codes


def test_audit_missing_prerequisite_fails(tmp_path: Path):
    """Verify missing antecedent prerequisite produces CRITICAL finding and exit code 1."""
    manifest_data = {
        "course": {
            "id": "missing-prereq-course",
            "title": "Missing Prereq Test",
            "archetype": "axiomatic_primitives",
        },
        "chapters": [
            {
                "id": "ch-01",
                "title": "Start",
                "sections": [
                    {"id": "sec-01", "title": "Only Section", "prerequisites": ["ghost-section"]},
                ],
            }
        ],
    }

    manifest_file = tmp_path / "course.toml"
    with open(manifest_file, "wb") as f:
        tomli_w.dump(manifest_data, f)

    res = subprocess.run(
        [sys.executable, str(AUDITOR_SCRIPT), "audit", "--manifest", str(manifest_file), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    data = json.loads(res.stderr)
    assert data["ok"] is False
    codes = [f["code"] for f in data["findings"]]
    assert "MISSING_PREREQUISITE" in codes


def test_audit_premature_vocabulary_fails(tmp_path: Path):
    """Verify requiring vocabulary without antecedent introduction produces CRITICAL finding."""
    manifest_data = {
        "course": {
            "id": "premature-vocab-course",
            "title": "Vocab Test",
            "archetype": "spiral_immersion",
        },
        "chapters": [
            {
                "id": "ch-01",
                "title": "Chapter",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "First Step",
                        # Requires term that was never introduced!
                        "vocabulary_prerequisites": ["quantum_entanglement"],
                        "vocabulary_introduced": ["basics"],
                    }
                ],
            }
        ],
    }

    manifest_file = tmp_path / "course.toml"
    with open(manifest_file, "wb") as f:
        tomli_w.dump(manifest_data, f)

    res = subprocess.run(
        [sys.executable, str(AUDITOR_SCRIPT), "audit", "--manifest", str(manifest_file), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    data = json.loads(res.stderr)
    assert data["ok"] is False
    codes = [f["code"] for f in data["findings"]]
    assert "PREMATURE_VOCABULARY" in codes


def test_audit_duplicate_vocabulary_warning(tmp_path: Path):
    """Verify duplicate vocabulary produces WARNING but passes with exit 0."""
    manifest_data = {
        "course": {
            "id": "dup-vocab-course",
            "title": "Dup Vocab Test",
            "archetype": "reverse_engineering",
        },
        "chapters": [
            {
                "id": "ch-01",
                "title": "Chapter",
                "sections": [
                    {"id": "sec-01", "title": "Intro", "vocabulary_introduced": ["heap_dump"]},
                    {
                        "id": "sec-02",
                        "title": "Analysis",
                        "prerequisites": ["sec-01"],
                        "vocabulary_introduced": ["heap_dump"],  # Duplicate!
                    },
                ],
            }
        ],
    }

    manifest_file = tmp_path / "course.toml"
    with open(manifest_file, "wb") as f:
        tomli_w.dump(manifest_data, f)

    res = subprocess.run(
        [sys.executable, str(AUDITOR_SCRIPT), "audit", "--manifest", str(manifest_file), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["warning_count"] >= 1
    codes = [f["code"] for f in data["findings"]]
    assert "DUPLICATE_VOCABULARY" in codes


def test_audit_with_research_cross_check(tmp_path: Path):
    """Verify auditor cross-checks topics against cached research digest."""
    # Create research digest
    research_dir = tmp_path / ".tc" / "research" / "rust-memory"
    research_dir.mkdir(parents=True)
    digest_data = {
        "slug": "rust-memory",
        "confidence": "high",
        "toc": [{"level": 1, "title": "Ownership and Borrowing"}],
        "api_index": [{"name": "drop", "type": "function"}],
        "vocabulary": ["ownership", "borrow_checker", "lifetimes"],
    }
    (research_dir / "digest.json").write_text(json.dumps(digest_data), encoding="utf-8")

    manifest_data = {
        "course": {
            "id": "rust-memory",
            "title": "Rust Memory Safety",
            "archetype": "applied_creation",
        },
        "chapters": [
            {
                "id": "ch-01",
                "title": "Ownership",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Ownership and Borrowing",
                        "vocabulary_introduced": ["ownership"],
                    }
                ],
            }
        ],
    }
    manifest_file = tmp_path / "course.toml"
    with open(manifest_file, "wb") as f:
        tomli_w.dump(manifest_data, f)

    res = subprocess.run(
        [
            sys.executable,
            str(AUDITOR_SCRIPT),
            "audit",
            "--manifest",
            str(manifest_file),
            "--workspace",
            str(tmp_path),
            "--research-slug",
            "rust-memory",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["critical_count"] == 0
