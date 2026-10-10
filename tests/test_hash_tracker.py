"""test_hash_tracker.py — Unit tests for TextCourses SHA-256 delta tracker (hash_tracker.py).

Verifies chunked 64KB hashing, deterministic byte digests, relative path preservation,
manifest generation (TOML & JSON), drift detection (added, modified, deleted),
and error handling (AD-1, AD-2, FR-19).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "_tc" / "scripts"))
from hash_tracker import (
    CHUNK_SIZE,
    compute_file_hash,
    diff_hashes,
    load_manifest,
    snapshot_directory,
)

HASH_TRACKER_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "hash_tracker.py"


def run_hash_tracker(*args: str) -> subprocess.CompletedProcess[str]:
    """Helper to run hash_tracker.py CLI and capture stdout/stderr."""
    cmd = [sys.executable, str(HASH_TRACKER_SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_hash_tracker_help():
    """Verify help subcommand displays usage and available subcommands."""
    result = run_hash_tracker("--help")
    assert result.returncode == 0
    assert "TextCourses SHA-256 cryptographic source delta tracker" in result.stdout
    assert "snapshot" in result.stdout
    assert "diff" in result.stdout
    assert "verify" in result.stdout


def test_subcommand_helps():
    """Verify each subcommand provides helpful usage instructions."""
    for subcmd in ["snapshot", "diff", "verify"]:
        result = run_hash_tracker(subcmd, "--help")
        assert result.returncode == 0
        assert f"usage: hash_tracker.py {subcmd}" in result.stdout


def test_compute_file_hash_empty_and_known_digest(tmp_path: Path):
    """Verify compute_file_hash correctly digests empty files and known text."""
    # Empty file has well-known SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")
    empty_digest = compute_file_hash(empty_file)
    assert empty_digest == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    sample_file = tmp_path / "sample.txt"
    content = b"Deterministic SHA-256 content for TextCourses runtime."
    sample_file.write_bytes(content)
    expected_digest = hashlib.sha256(content).hexdigest()
    assert compute_file_hash(sample_file) == expected_digest


def test_chunked_hashing_large_file(tmp_path: Path):
    """Verify streaming hash calculation processes large files (>64KB) in CHUNK_SIZE pieces."""
    large_file = tmp_path / "large_payload.bin"
    # Create payload spanning multiple 64KB chunks (e.g. 200KB)
    payload_size = CHUNK_SIZE * 3 + 1234
    data = bytes((i % 256 for i in range(payload_size)))
    large_file.write_bytes(data)

    expected_hash = hashlib.sha256(data).hexdigest()
    computed_hash = compute_file_hash(large_file)
    assert computed_hash == expected_hash


def test_snapshot_empty_directory(tmp_path: Path):
    """Verify snapshot on an empty directory returns an empty manifest with exit code 0."""
    empty_dir = tmp_path / "sources"
    empty_dir.mkdir()

    result = run_hash_tracker("snapshot", "--path", str(empty_dir))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["files"] == {}
    assert data["count"] == 0


def test_snapshot_nonexistent_directory(tmp_path: Path):
    """Verify snapshot on a non-existent path exits 1 with structured error."""
    missing_dir = tmp_path / "does_not_exist"

    result = run_hash_tracker("snapshot", "--path", str(missing_dir))
    assert result.returncode == 1
    err = json.loads(result.stderr)
    assert err["ok"] is False
    assert "does not exist" in err["error"]


def test_snapshot_with_toml_output(tmp_path: Path):
    """Verify snapshot writes valid TOML manifest atomically and excludes the manifest itself."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()

    file1 = sources_dir / "syllabus.md"
    file1.write_text("# Syllabus\nTopic A\n", encoding="utf-8")
    file2 = sources_dir / "guide.md"
    file2.write_text("# Guide\nReference 1\n", encoding="utf-8")

    manifest_file = sources_dir / "ledger.toml"

    result = run_hash_tracker(
        "snapshot",
        "--path", str(sources_dir),
        "--output", str(manifest_file),
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["count"] == 2
    assert "syllabus.md" in data["files"]
    assert "guide.md" in data["files"]
    # Manifest itself must not be in the file list
    assert "ledger.toml" not in data["files"]

    assert manifest_file.exists()
    with open(manifest_file, "rb") as f:
        toml_data = tomllib.load(f)
    assert "sources" in toml_data
    assert "syllabus.md" in toml_data["sources"]
    assert "guide.md" in toml_data["sources"]
    assert "ledger.toml" not in toml_data["sources"]


def test_snapshot_with_json_output(tmp_path: Path):
    """Verify snapshot writes valid JSON manifest atomically."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()

    doc = sources_dir / "reference.txt"
    doc.write_text("Reference content", encoding="utf-8")
    manifest_file = tmp_path / "manifest.json"

    result = run_hash_tracker(
        "snapshot",
        "--path", str(sources_dir),
        "--output", str(manifest_file),
    )
    assert result.returncode == 0
    assert manifest_file.exists()

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_json = json.load(f)
    assert "files" in manifest_json
    assert "reference.txt" in manifest_json["files"]


def test_snapshot_nested_directories_relative_paths(tmp_path: Path):
    """Verify paths are recorded relative to scanned root in POSIX forward-slash format."""
    root_dir = tmp_path / "root"
    nested_dir = root_dir / "sub" / "deep"
    nested_dir.mkdir(parents=True)

    nested_file = nested_dir / "doc.md"
    nested_file.write_text("Nested document", encoding="utf-8")
    root_file = root_dir / "top.md"
    root_file.write_text("Top document", encoding="utf-8")

    result = run_hash_tracker("snapshot", "--path", str(root_dir))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert "sub/deep/doc.md" in data["files"]
    assert "top.md" in data["files"]


def test_snapshot_ignores_temporary_and_cache_files(tmp_path: Path):
    """Verify temporary files (.tmp, .bak) and cache directories are excluded."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()

    valid_file = sources_dir / "real.md"
    valid_file.write_text("Legitimate file", encoding="utf-8")

    tmp_file = sources_dir / "real.md.tmp"
    tmp_file.write_text("Temporary swap", encoding="utf-8")

    bak_file = sources_dir / "old.bak"
    bak_file.write_text("Backup file", encoding="utf-8")

    cache_dir = sources_dir / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "bytecode.pyc").write_bytes(b"bytecode")

    result = run_hash_tracker("snapshot", "--path", str(sources_dir))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert list(data["files"].keys()) == ["real.md"]


def test_diff_untouched_directory(tmp_path: Path):
    """Verify diff on untouched directory reports zero added/modified/deleted files."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    (sources_dir / "f1.txt").write_text("Alpha", encoding="utf-8")
    (sources_dir / "f2.txt").write_text("Beta", encoding="utf-8")

    manifest = tmp_path / "ledger.toml"
    run_hash_tracker("snapshot", "--path", str(sources_dir), "--output", str(manifest))

    result = run_hash_tracker("diff", "--path", str(sources_dir), "--manifest", str(manifest))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["added"] == []
    assert data["modified"] == []
    assert data["deleted"] == []
    assert sorted(data["unchanged"]) == ["f1.txt", "f2.txt"]
    assert data["has_changes"] is False
    assert data["total_changes"] == 0


def test_diff_detects_additions_modifications_and_deletions(tmp_path: Path):
    """Verify diff accurately categorizes added, modified, and deleted files simultaneously."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()

    stay_file = sources_dir / "stay.txt"
    stay_file.write_text("Unchanged content", encoding="utf-8")

    mod_file = sources_dir / "modify.txt"
    mod_file.write_text("Original content", encoding="utf-8")

    del_file = sources_dir / "delete.txt"
    del_file.write_text("To be deleted", encoding="utf-8")

    manifest = tmp_path / "ledger.toml"
    run_hash_tracker("snapshot", "--path", str(sources_dir), "--output", str(manifest))

    # Apply changes:
    # 1. Modify modify.txt
    mod_file.write_text("Updated content!", encoding="utf-8")
    # 2. Delete delete.txt
    del_file.unlink()
    # 3. Add new.txt
    new_file = sources_dir / "new.txt"
    new_file.write_text("Brand new file", encoding="utf-8")

    result = run_hash_tracker("diff", "--path", str(sources_dir), "--manifest", str(manifest))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["added"] == ["new.txt"]
    assert data["modified"] == ["modify.txt"]
    assert data["deleted"] == ["delete.txt"]
    assert data["unchanged"] == ["stay.txt"]
    assert data["has_changes"] is True
    assert data["total_changes"] == 3


def test_diff_missing_manifest_fails(tmp_path: Path):
    """Verify diff exits 1 when manifest file does not exist."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    nonexistent_manifest = tmp_path / "missing.toml"

    result = run_hash_tracker("diff", "--path", str(sources_dir), "--manifest", str(nonexistent_manifest))
    assert result.returncode == 1
    err = json.loads(result.stderr)
    assert err["ok"] is False
    assert "Manifest file not found" in err["error"]


def test_verify_clean_directory_succeeds(tmp_path: Path):
    """Verify verify subcommand exits 0 when all files match manifest without drift."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    (sources_dir / "doc1.md").write_text("Lesson 1", encoding="utf-8")
    (sources_dir / "doc2.md").write_text("Lesson 2", encoding="utf-8")

    manifest = sources_dir / "ledger.toml"
    run_hash_tracker("snapshot", "--path", str(sources_dir), "--output", str(manifest))

    result = run_hash_tracker("verify", "--path", str(sources_dir), "--manifest", str(manifest))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert data["verified"] is True
    assert sorted(data["verified_files"]) == ["doc1.md", "doc2.md"]


def test_verify_drift_modified_file_fails(tmp_path: Path):
    """Verify verify subcommand detects modified file drift and exits 1 with details."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    doc = sources_dir / "doc1.md"
    doc.write_text("Initial text", encoding="utf-8")

    manifest = tmp_path / "ledger.toml"
    run_hash_tracker("snapshot", "--path", str(sources_dir), "--output", str(manifest))

    # Tamper with file
    doc.write_text("Tampered text", encoding="utf-8")

    result = run_hash_tracker("verify", "--path", str(sources_dir), "--manifest", str(manifest))
    assert result.returncode == 1
    err = json.loads(result.stderr)
    assert err["ok"] is False
    assert "drift detected" in err["error"].lower()
    assert err["drift"]["modified"] == ["doc1.md"]
    assert err["drift"]["added"] == []
    assert err["drift"]["deleted"] == []


def test_verify_drift_added_file_fails(tmp_path: Path):
    """Verify verify subcommand detects unexpected added files as drift and exits 1."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    (sources_dir / "doc.md").write_text("Clean", encoding="utf-8")

    manifest = tmp_path / "ledger.toml"
    run_hash_tracker("snapshot", "--path", str(sources_dir), "--output", str(manifest))

    # Add extra file
    (sources_dir / "intruder.txt").write_text("Unexpected addition", encoding="utf-8")

    result = run_hash_tracker("verify", "--path", str(sources_dir), "--manifest", str(manifest))
    assert result.returncode == 1
    err = json.loads(result.stderr)
    assert err["ok"] is False
    assert err["drift"]["added"] == ["intruder.txt"]


def test_verify_drift_deleted_file_fails(tmp_path: Path):
    """Verify verify subcommand detects missing files as drift and exits 1."""
    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()
    f1 = sources_dir / "f1.txt"
    f1.write_text("F1", encoding="utf-8")

    manifest = tmp_path / "ledger.toml"
    run_hash_tracker("snapshot", "--path", str(sources_dir), "--output", str(manifest))

    # Delete f1.txt
    f1.unlink()

    result = run_hash_tracker("verify", "--path", str(sources_dir), "--manifest", str(manifest))
    assert result.returncode == 1
    err = json.loads(result.stderr)
    assert err["ok"] is False
    assert err["drift"]["deleted"] == ["f1.txt"]


def test_python_api_functions(tmp_path: Path):
    """Verify Python library functions work directly when imported."""
    src = tmp_path / "lib_src"
    src.mkdir()
    f = src / "code.py"
    f.write_text("print('hello')", encoding="utf-8")

    snaps = snapshot_directory(src)
    assert "code.py" in snaps
    assert len(snaps["code.py"]) == 64  # SHA-256 hexdigest length

    deltas = diff_hashes(snaps, {"code.py": "different_hash"})
    assert deltas["modified"] == ["code.py"]
    assert deltas["added"] == []
    assert deltas["deleted"] == []
    assert deltas["unchanged"] == []
