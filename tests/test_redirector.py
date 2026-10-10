"""tests/test_redirector.py — Comprehensive test suite for course evolution and notes deprecation."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import tomli_w

REDIRECTOR_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "redirector.py"
SKILL_FILE = Path(__file__).parent.parent / "skills" / "tc-redirect-course" / "SKILL.md"


def test_redirector_cli_help():
    """Verify that redirector CLI prints help message and exits 0."""
    res = subprocess.run([sys.executable, str(REDIRECTOR_SCRIPT), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "diff-sources" in res.stdout
    assert "deprecate" in res.stdout
    assert "inspect" in res.stdout


def test_redirector_pep_723_metadata():
    """Verify script contains valid PEP 723 metadata header."""
    content = REDIRECTOR_SCRIPT.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert 'requires-python = ">=3.11"' in content
    assert "tomli-w>=" in content
    assert "# ///" in content


def test_zero_bmad_references():
    """Verify strict zero-BMad references in scripts and skill documentation."""
    for target in [REDIRECTOR_SCRIPT, SKILL_FILE]:
        text = target.read_text(encoding="utf-8")
        assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad mention in {target}"


def test_deprecate_notes_preserves_body_bit_for_bit(tmp_path: Path):
    """Verify deprecate prepends markdown alert while preserving original body exactly."""
    notes_file = tmp_path / "notes.md"
    original_text = (
        "# Rust Lifetimes\n\n"
        "Lifetimes ensure references do not outlive referenced data.\n\n"
        "```rust\nfn longest<'a>(x: &'a str, y: &'a str) -> &'a str { x }\n```\n"
    )
    notes_file.write_text(original_text, encoding="utf-8")

    res = subprocess.run(
        [
            sys.executable,
            str(REDIRECTOR_SCRIPT),
            "deprecate",
            "--path",
            str(notes_file),
            "--reason",
            "Non-lexical lifetimes (NLL) update in Rust 2018",
            "--redirect-to",
            "courses/rust-deep-dive/ch-02/sec-01",
            "--effective-date",
            "2026-10-10",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["deprecated"] is True
    assert data["already_present"] is False

    updated_content = notes_file.read_text(encoding="utf-8")
    assert "> ⚠️ **Deprecation Notice**" in updated_content
    assert "Non-lexical lifetimes (NLL) update in Rust 2018" in updated_content
    assert "courses/rust-deep-dive/ch-02/sec-01" in updated_content
    assert "2026-10-10" in updated_content

    # Strict bit-for-bit check: original content must be an exact suffix
    assert updated_content.endswith(original_text)


def test_deprecate_idempotency(tmp_path: Path):
    """Verify running deprecate twice does not duplicate header or alter body."""
    notes_file = tmp_path / "notes.md"
    notes_file.write_text("# Chapter 1 Notes\nSample content here.\n", encoding="utf-8")

    # First deprecate
    res1 = subprocess.run(
        [
            sys.executable,
            str(REDIRECTOR_SCRIPT),
            "deprecate",
            "--path",
            str(notes_file),
            "--reason",
            "Initial deprecation",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res1.returncode == 0
    data1 = json.loads(res1.stdout)
    assert data1["already_present"] is False
    content_after_first = notes_file.read_text(encoding="utf-8")

    # Second deprecate
    res2 = subprocess.run(
        [
            sys.executable,
            str(REDIRECTOR_SCRIPT),
            "deprecate",
            "--path",
            str(notes_file),
            "--reason",
            "Second attempt should no-op",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 0
    data2 = json.loads(res2.stdout)
    assert data2["already_present"] is True

    content_after_second = notes_file.read_text(encoding="utf-8")
    assert content_after_second == content_after_first


def test_deprecate_nonexistent_file_fails(tmp_path: Path):
    """Verify deprecate exits 1 when target file does not exist."""
    missing_file = tmp_path / "nonexistent.md"
    res = subprocess.run(
        [
            sys.executable,
            str(REDIRECTOR_SCRIPT),
            "deprecate",
            "--path",
            str(missing_file),
            "--reason",
            "Should fail",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    err_data = json.loads(res.stderr)
    assert "error" in err_data


def test_diff_sources_clean_and_drift(tmp_path: Path):
    """Verify diff-sources detects clean vs drifted reference documentation."""
    course_dir = tmp_path / "courses" / "async-python"
    course_dir.mkdir(parents=True)
    sources_dir = tmp_path / "plan" / "sources"
    sources_dir.mkdir(parents=True)

    src_file1 = sources_dir / "asyncio_spec.md"
    src_file1.write_text("Asyncio TaskGroup documentation v1\n", encoding="utf-8")

    # Calculate initial hash
    import hashlib
    h1 = hashlib.sha256(b"Asyncio TaskGroup documentation v1\n").hexdigest()

    course_data = {
        "course": {"id": "async-python", "title": "Advanced Async Python"},
        "sources": {
            "asyncio_spec.md": h1,
        },
        "chapters": [
            {
                "id": "ch-01",
                "title": "Coroutines",
                "sections": [
                    {
                        "id": "sec-01",
                        "title": "Event Loops",
                        "status": "completed",
                        "sources": ["asyncio_spec.md"],
                    },
                    {
                        "id": "sec-02",
                        "title": "TaskGroups",
                        "status": "not_started",
                        "sources": ["asyncio_spec.md"],
                    },
                ],
            }
        ],
    }

    course_toml = course_dir / "course.toml"
    with open(course_toml, "wb") as f:
        tomli_w.dump(course_data, f)

    # 1. Clean check: no drift
    res_clean = subprocess.run(
        [
            sys.executable,
            str(REDIRECTOR_SCRIPT),
            "diff-sources",
            "--path",
            str(course_dir),
            "--sources",
            str(sources_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_clean.returncode == 0
    clean_json = json.loads(res_clean.stdout)
    assert clean_json["drift_detected"] is False
    assert len(clean_json["affected_sections"]) == 0
    assert len(clean_json["completed_sections_safe"]) == 1

    # 2. Modify source: drift detected
    src_file1.write_text("Asyncio TaskGroup documentation v2 with ExceptionGroups\n", encoding="utf-8")

    res_drift = subprocess.run(
        [
            sys.executable,
            str(REDIRECTOR_SCRIPT),
            "diff-sources",
            "--path",
            str(course_dir),
            "--sources",
            str(sources_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res_drift.returncode == 0
    drift_json = json.loads(res_drift.stdout)
    assert drift_json["drift_detected"] is True
    assert "asyncio_spec.md" in drift_json["changes"]["modified"]
    assert len(drift_json["affected_sections"]) == 1
    assert drift_json["affected_sections"][0]["section_id"] == "sec-02"
    assert len(drift_json["completed_sections_safe"]) == 1


def test_inspect_course_state(tmp_path: Path):
    """Verify inspect reports notes count, clean notes, and deprecated notes."""
    course_dir = tmp_path / "courses" / "db-internals"
    sec1 = course_dir / "ch-01" / "sec-01"
    sec2 = course_dir / "ch-01" / "sec-02"
    sec1.mkdir(parents=True)
    sec2.mkdir(parents=True)

    course_toml = course_dir / "course.toml"
    with open(course_toml, "wb") as f:
        tomli_w.dump({"course": {"id": "db-internals", "title": "Database Internals"}}, f)

    (sec1 / "notes.md").write_text("# Section 1 Notes\nNormal clean notes.\n", encoding="utf-8")
    (sec2 / "notes.md").write_text(
        "> ⚠️ **Deprecation Notice**\n> Superseded\n\n# Section 2 Notes\nDeprecated notes.\n",
        encoding="utf-8",
    )

    res = subprocess.run(
        [
            sys.executable,
            str(REDIRECTOR_SCRIPT),
            "inspect",
            "--path",
            str(course_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["total_notes"] == 2
    assert data["clean_notes_count"] == 1
    assert data["deprecated_notes_count"] == 1
