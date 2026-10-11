#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""hash_tracker.py — SHA-256 cryptographic source delta tracker for TextCourses.

Tracks ingested reference materials, documentation files, and syllabi in plan/sources/
using deterministic SHA-256 cryptographic digests (AD-1, AD-2, FR-19).
Streams files in 64KB chunks, stores relative paths, and provides snapshot, diff,
and verify subcommands with atomic state updates.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

CHUNK_SIZE = 64 * 1024  # 64KB chunks for streaming hash calculation


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def atomic_write_toml(filepath: Path, data: dict[str, Any]) -> None:
    """Write TOML data atomically using a temp file, fsync, and os.replace."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, "wb") as f:
            tomli_w.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic TOML write failed for {filepath}: {e}") from e


def atomic_write_json(filepath: Path, data: dict[str, Any]) -> None:
    """Write JSON data atomically using a temp file, fsync, and os.replace."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic JSON write failed for {filepath}: {e}") from e


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 byte digest of a file, streaming in 64KB chunks."""
    filepath = Path(filepath)
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()


def snapshot_directory(
    root_dir: Path,
    exclude_files: list[Path] | None = None,
) -> dict[str, str]:
    """Recursively compute SHA-256 digests of all files relative to root_dir.

    Excludes temporary files (*.tmp), directories (.git, __pycache__), and any
    explicitly excluded file paths (e.g. the manifest itself).
    """
    root_dir = Path(root_dir)
    if not root_dir.exists():
        raise FileNotFoundError(f"Target path does not exist: {root_dir}")
    if not root_dir.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {root_dir}")

    resolved_excludes: set[Path] = set()
    if exclude_files:
        for ef in exclude_files:
            try:
                resolved_excludes.add(Path(ef).resolve())
            except Exception:
                pass

    hashes: dict[str, str] = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude hidden and cache directories in-place to avoid descending
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__"} and not d.startswith(".tc")]

        for filename in filenames:
            # Skip temporary swap/backup files
            if filename.endswith(".tmp") or filename.endswith(".bak") or filename.endswith("~"):
                continue

            file_path = Path(dirpath) / filename
            try:
                resolved_file = file_path.resolve()
            except Exception:
                resolved_file = file_path

            if resolved_file in resolved_excludes:
                continue

            # Also check if this file is the default ledger.toml tracker itself
            if filename == "ledger.toml" and resolved_file in resolved_excludes:
                continue

            try:
                rel_path = file_path.relative_to(root_dir).as_posix()
            except ValueError:
                rel_path = filename

            hashes[rel_path] = compute_file_hash(file_path)

    # Return deterministically sorted mapping
    return {k: hashes[k] for k in sorted(hashes.keys())}


def load_manifest(manifest_path: Path) -> dict[str, str]:
    """Load and parse a manifest file (TOML or JSON) into a {rel_path: sha256} mapping."""
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    if manifest_path.stat().st_size == 0:
        return {}

    content_text = manifest_path.read_text(encoding="utf-8").strip()
    if not content_text:
        return {}

    data: dict[str, Any] = {}
    if manifest_path.suffix.lower() == ".toml":
        try:
            data = tomllib.loads(content_text)
        except Exception:
            data = json.loads(content_text)
    else:
        try:
            data = json.loads(content_text)
        except Exception:
            data = tomllib.loads(content_text)

    # Extract hashes mapping from supported structures
    raw_hashes: dict[str, Any] = {}
    if "files" in data and isinstance(data["files"], dict):
        raw_hashes = data["files"]
    elif "sources" in data and isinstance(data["sources"], dict):
        raw_hashes = data["sources"]
    elif "hashes" in data and isinstance(data["hashes"], dict):
        raw_hashes = data["hashes"]
    else:
        # Flat dictionary mapping
        raw_hashes = {
            k: v for k, v in data.items()
            if k not in {"manifest", "version", "ok", "path", "count", "generated_at", "algorithm"}
        }

    result: dict[str, str] = {}
    for path_str, val in raw_hashes.items():
        if isinstance(val, str):
            result[path_str] = val
        elif isinstance(val, dict):
            digest = val.get("sha256") or val.get("hash") or val.get("digest")
            if digest and isinstance(digest, str):
                result[path_str] = digest
            else:
                result[path_str] = str(val)
    return result


def diff_hashes(
    current_hashes: dict[str, str],
    manifest_hashes: dict[str, str],
) -> dict[str, list[str]]:
    """Compare current directory hashes against manifest hashes.

    Returns dictionary with sorted lists: 'added', 'modified', 'deleted', 'unchanged'.
    """
    current_keys = set(current_hashes.keys())
    manifest_keys = set(manifest_hashes.keys())

    added = sorted(list(current_keys - manifest_keys))
    deleted = sorted(list(manifest_keys - current_keys))

    common_keys = current_keys & manifest_keys
    modified = sorted([k for k in common_keys if current_hashes[k] != manifest_hashes[k]])
    unchanged = sorted([k for k in common_keys if current_hashes[k] == manifest_hashes[k]])

    return {
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "unchanged": unchanged,
    }


def resolve_manifest_path(manifest_arg: str | None, base_path: Path) -> Path | None:
    """Resolve manifest path from CLI argument or default locations."""
    if manifest_arg:
        m = Path(manifest_arg)
        if m.is_dir():
            if (m / "ledger.toml").exists():
                return m / "ledger.toml"
            if (m / "manifest.json").exists():
                return m / "manifest.json"
            return m / "ledger.toml"
        return m

    # Check common default locations
    if (base_path / "ledger.toml").exists():
        return base_path / "ledger.toml"
    if (base_path / "manifest.json").exists():
        return base_path / "manifest.json"
    if Path("plan/sources/ledger.toml").exists():
        return Path("plan/sources/ledger.toml")
    return None


def cmd_snapshot(args: argparse.Namespace) -> None:
    """Compute cryptographic SHA-256 snapshot of directory and optionally write manifest."""
    path_arg = args.path or ("plan/sources" if Path("plan/sources").exists() else ".")
    target_path = Path(path_arg)

    if not target_path.exists():
        output_json({"ok": False, "error": f"Target path does not exist: {target_path}"}, exit_code=1)

    output_path = Path(args.output) if args.output else None
    excludes = [output_path] if output_path else []

    try:
        file_hashes = snapshot_directory(target_path, exclude_files=excludes)
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    if output_path:
        manifest_payload = {
            "manifest": {
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "algorithm": "sha256",
                "file_count": len(file_hashes),
            },
            "sources": file_hashes,
            "files": file_hashes,
        }
        try:
            if output_path.suffix.lower() == ".toml":
                atomic_write_toml(output_path, manifest_payload)
            else:
                atomic_write_json(output_path, manifest_payload)
        except Exception as e:
            output_json({"ok": False, "error": f"Failed to write manifest: {e}"}, exit_code=1)

    response: dict[str, Any] = {
        "ok": True,
        "path": str(target_path),
        "files": file_hashes,
        "hashes": file_hashes,
        "count": len(file_hashes),
    }
    if output_path:
        response["output"] = str(output_path)
        response["manifest"] = str(output_path)

    output_json(response, exit_code=0)


def cmd_diff(args: argparse.Namespace) -> None:
    """Detect file additions, modifications, and deletions against a manifest."""
    path_arg = args.path or ("plan/sources" if Path("plan/sources").exists() else ".")
    target_path = Path(path_arg)

    if not target_path.exists():
        output_json({"ok": False, "error": f"Target path does not exist: {target_path}"}, exit_code=1)

    manifest_path = resolve_manifest_path(args.manifest, target_path)
    if not manifest_path or not manifest_path.exists():
        err_msg = f"Manifest file not found: {manifest_path if manifest_path else args.manifest}"
        output_json({"ok": False, "error": err_msg}, exit_code=1)

    try:
        manifest_hashes = load_manifest(manifest_path)
        current_hashes = snapshot_directory(target_path, exclude_files=[manifest_path])
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    deltas = diff_hashes(current_hashes, manifest_hashes)
    has_changes = bool(deltas["added"] or deltas["modified"] or deltas["deleted"])
    total_changes = len(deltas["added"]) + len(deltas["modified"]) + len(deltas["deleted"])

    output_json({
        "ok": True,
        "path": str(target_path),
        "manifest": str(manifest_path),
        "added": deltas["added"],
        "modified": deltas["modified"],
        "deleted": deltas["deleted"],
        "unchanged": deltas["unchanged"],
        "has_changes": has_changes,
        "total_changes": total_changes,
    }, exit_code=0)


def cmd_verify(args: argparse.Namespace) -> None:
    """Verify that all files in directory strictly match manifest hashes without drift."""
    path_arg = args.path or ("plan/sources" if Path("plan/sources").exists() else ".")
    target_path = Path(path_arg)

    if not target_path.exists():
        output_json({"ok": False, "error": f"Target path does not exist: {target_path}"}, exit_code=1)

    manifest_path = resolve_manifest_path(args.manifest, target_path)
    if not manifest_path or not manifest_path.exists():
        err_msg = f"Manifest file not found: {manifest_path if manifest_path else args.manifest}"
        output_json({"ok": False, "error": err_msg}, exit_code=1)

    try:
        manifest_hashes = load_manifest(manifest_path)
        current_hashes = snapshot_directory(target_path, exclude_files=[manifest_path])
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    deltas = diff_hashes(current_hashes, manifest_hashes)
    has_drift = bool(deltas["added"] or deltas["modified"] or deltas["deleted"])

    if has_drift:
        output_json({
            "ok": False,
            "error": "File integrity drift detected",
            "path": str(target_path),
            "manifest": str(manifest_path),
            "drift": {
                "added": deltas["added"],
                "modified": deltas["modified"],
                "deleted": deltas["deleted"],
            },
            "added": deltas["added"],
            "modified": deltas["modified"],
            "deleted": deltas["deleted"],
            "unchanged": deltas["unchanged"],
        }, exit_code=1)
    else:
        output_json({
            "ok": True,
            "message": "Integrity verified: all files match manifest digests without drift",
            "verified": True,
            "path": str(target_path),
            "manifest": str(manifest_path),
            "verified_files": deltas["unchanged"],
            "unchanged": deltas["unchanged"],
            "count": len(deltas["unchanged"]),
        }, exit_code=0)


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser for hash_tracker.py."""
    parser = argparse.ArgumentParser(
        description="TextCourses SHA-256 cryptographic source delta tracker.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # snapshot subcommand
    snap_parser = subparsers.add_parser(
        "snapshot",
        help="Compute SHA-256 digests of all files in directory and generate manifest",
    )
    snap_parser.add_argument(
        "--path", "-p",
        help="Path to directory to snapshot (defaults to plan/sources or current directory)",
    )
    snap_parser.add_argument(
        "--output", "-o",
        help="Optional path to output manifest file (e.g. ledger.toml or manifest.json)",
    )
    snap_parser.set_defaults(func=cmd_snapshot)

    # diff subcommand
    diff_parser = subparsers.add_parser(
        "diff",
        help="Detect added, modified, and deleted files against a manifest",
    )
    diff_parser.add_argument(
        "--path", "-p",
        help="Path to directory to inspect (defaults to plan/sources or current directory)",
    )
    diff_parser.add_argument(
        "--manifest", "-m",
        required=True,
        help="Path to manifest file to compare against",
    )
    diff_parser.set_defaults(func=cmd_diff)

    # verify subcommand
    ver_parser = subparsers.add_parser(
        "verify",
        help="Verify file integrity against manifest and detect drift",
    )
    ver_parser.add_argument(
        "--path", "-p",
        help="Path to directory to verify (defaults to plan/sources or current directory)",
    )
    ver_parser.add_argument(
        "--manifest", "-m",
        required=True,
        help="Path to manifest file to verify against",
    )
    ver_parser.set_defaults(func=cmd_verify)

    return parser


def main() -> None:
    """Main CLI entrypoint."""
    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
