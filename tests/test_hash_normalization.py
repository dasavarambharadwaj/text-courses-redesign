"""tests/test_hash_normalization.py — Unit tests for cross-platform hash checksum normalization (FR-41).

Verifies:
1. normalize_content_for_hashing transforms CRLF, CR, and trailing whitespace to canonical LF bytes.
2. compute_file_hash produces identical SHA-256 digests for CRLF vs LF versions of identical text files.
3. Binary files (.bin) bypass text normalization and preserve raw byte digests.
4. Snapshot and verification remain consistent across operating system line-ending variations.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "_tc" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from hash_tracker import (
    compute_file_hash,
    diff_hashes,
    normalize_content_for_hashing,
    snapshot_directory,
)


def test_normalize_content_for_hashing_crlf_and_whitespace():
    """Verify normalize_content_for_hashing harmonizes CRLF, CR, and trailing whitespace."""
    # Empty
    assert normalize_content_for_hashing(b"") == b""

    # CRLF with trailing spaces vs clean LF
    raw_crlf = b"# Chapter 01: Concurrency  \r\n- First point   \r\n- Second point\r\n"
    raw_lf = b"# Chapter 01: Concurrency\n- First point\n- Second point\n"

    norm_crlf = normalize_content_for_hashing(raw_crlf)
    norm_lf = normalize_content_for_hashing(raw_lf)

    assert norm_crlf == norm_lf
    assert norm_crlf == b"# Chapter 01: Concurrency\n- First point\n- Second point\n"


def test_compute_file_hash_identical_for_crlf_and_lf(tmp_path: Path):
    """Verify compute_file_hash yields identical SHA-256 for text files with different line endings."""
    lf_file = tmp_path / "notes_linux.md"
    crlf_file = tmp_path / "notes_windows.md"

    content_text = "# Textbook Notes\n\n- Concept 1\n- Concept 2\n"
    lf_file.write_bytes(content_text.encode("utf-8"))
    crlf_file.write_bytes(content_text.replace("\n", "\r\n").encode("utf-8"))

    hash_lf = compute_file_hash(lf_file)
    hash_crlf = compute_file_hash(crlf_file)

    assert hash_lf == hash_crlf


def test_binary_files_bypass_normalization(tmp_path: Path):
    """Verify binary files (.bin) retain exact raw byte streaming without text alteration."""
    raw_binary = b"\x00\r\n\xff\xfe\r\x00\xaa"
    bin_file = tmp_path / "payload.bin"
    bin_file.write_bytes(raw_binary)

    expected_hash = hashlib.sha256(raw_binary).hexdigest()
    assert compute_file_hash(bin_file) == expected_hash


def test_snapshot_directory_cross_platform_consistency(tmp_path: Path):
    """Verify snapshot_directory detects zero drift between CRLF and LF copies of a course tree."""
    dir_a = tmp_path / "tree_linux"
    dir_b = tmp_path / "tree_windows"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_a / "course.toml").write_bytes(b"[course]\nid = 'sample'\ntitle = 'Sample'\n")
    (dir_b / "course.toml").write_bytes(b"[course]\r\nid = 'sample'  \r\ntitle = 'Sample'\r\n")

    (dir_a / "notes.md").write_bytes(b"# Notes\n- Item\n")
    (dir_b / "notes.md").write_bytes(b"# Notes  \r\n- Item   \r\n")

    snap_a = snapshot_directory(dir_a)
    snap_b = snapshot_directory(dir_b)

    assert snap_a["course.toml"] == snap_b["course.toml"]
    assert snap_a["notes.md"] == snap_b["notes.md"]

    diff = diff_hashes(snap_a, snap_b)
    assert not diff["added"]
    assert not diff["deleted"]
    assert not diff["modified"]
