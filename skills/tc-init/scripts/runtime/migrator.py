#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""migrator.py — Consent-gated schema migrator and workspace health auditor for TextCourses.

Inspects sovereign TextCourses workspace schemas, evaluates directory layouts and
configuration versions, produces transparent dry-run migration plans, and strictly
enforces explicit user confirmation before applying any file mutations (FR-21, AD-8).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any

CURRENT_SCHEMA_VERSION = "0.3.0"
CONFIRM_TOKEN = "APPLY"

REQUIRED_CANONICAL_DIRS = [
    "_tc",
    "_tc/scripts",
    "_tc/cache",
    "_tc/profile",
    "_tc/roadmap",
    "_tc/research",
    "_tc/courses",
    "_tc/status",
    "courses",
    "portfolio",
    "status-board",
]

LEGACY_DIRS = [
    ".tc",
    "research",
    "sources",
    "plan",
    "profile",
    "roadmap",
]

# Kept for backward compatibility with older tests that check REQUIRED_DIRS
REQUIRED_DIRS = REQUIRED_CANONICAL_DIRS

CANONICAL_SCRIPTS = [
    "manifest.py",
    "ledger.py",
    "dag.py",
    "context.py",
    "hash_tracker.py",
    "bootstrapper.py",
    "redirector.py",
    "migrator.py",
    "scout.py",
    "auditor.py",
    "course_builder.py",
    "lesson_tracker.py",
    "notes_compiler.py",
    "teach_engine.py",
    "diagnostic_tester.py",
    "practical_evaluator.py",
]


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


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


def atomic_write_text(filepath: Path, content: str) -> None:
    """Write text atomically using a temp file, fsync, and os.replace."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic text write failed for {filepath}: {e}") from e


def find_canonical_scripts_dir() -> Path | None:
    """Locate the canonical runtime scripts directory in repository root."""
    curr = Path(__file__).resolve().parent
    for _ in range(4):
        candidate = curr / "_tc" / "scripts"
        if candidate.is_dir() and (candidate / "manifest.py").is_file():
            return candidate
        if (curr / "manifest.py").is_file():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    return None


def verify_and_move_file(src_file: Path, dest_file: Path) -> None:
    """Copy src to dest, verify SHA-256 byte parity, then remove src."""
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    src_hash = hashlib.sha256(src_file.read_bytes()).hexdigest()
    shutil.copy2(src_file, dest_file)
    dest_hash = hashlib.sha256(dest_file.read_bytes()).hexdigest()
    if src_hash != dest_hash:
        raise RuntimeError(
            f"Parity verification failed: SHA-256 mismatch ({src_hash} != {dest_hash}) for {src_file} -> {dest_file}"
        )
    src_file.unlink()


def remove_empty_dir_tree(d: Path) -> None:
    """Recursively remove empty directory tree."""
    if not d.is_dir():
        return
    for child in list(d.iterdir()):
        if child.is_dir():
            remove_empty_dir_tree(child)
    if not any(d.iterdir()):
        try:
            d.rmdir()
        except OSError:
            pass


def check_workspace_health(workspace_path: Path | str) -> dict[str, Any]:
    """Inspect workspace health, layout, and configuration version."""
    ws = Path(workspace_path).resolve()
    if not ws.exists():
        raise FileNotFoundError(f"Target workspace does not exist: {ws}")
    if not ws.is_dir():
        raise NotADirectoryError(f"Target workspace is not a directory: {ws}")

    issues: list[str] = []
    missing_dirs: list[str] = []
    missing_scripts: list[str] = []
    legacy_found: list[str] = []

    # Check required canonical directories
    for rel_dir in REQUIRED_CANONICAL_DIRS:
        target_dir = ws / rel_dir
        if not target_dir.exists():
            missing_dirs.append(rel_dir)
            issues.append(f"Missing required canonical directory: {rel_dir}")
        elif not target_dir.is_dir():
            issues.append(f"Path exists but is not a directory: {rel_dir}")

    # Check for legacy directories that need consolidation
    for leg_dir in LEGACY_DIRS:
        target_dir = ws / leg_dir
        if target_dir.is_dir():
            legacy_found.append(leg_dir)
            issues.append(f"Legacy directory detected for migration: {leg_dir}")

    # Check config.json: check _tc/config.json first, then .tc/config.json
    config_path = ws / "_tc" / "config.json"
    legacy_config_path = ws / ".tc" / "config.json"
    config_version: str | None = None
    config_data: dict[str, Any] = {}

    if config_path.is_file():
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
            config_version = config_data.get("version", "0.0.0")
        except Exception as e:
            issues.append(f"Corrupt _tc/config.json: {e}")
            return {
                "ok": False,
                "workspace": str(ws),
                "status": "corrupt",
                "current_version": None,
                "target_version": CURRENT_SCHEMA_VERSION,
                "missing_directories": missing_dirs,
                "missing_scripts": missing_scripts,
                "issues": issues,
            }
    elif legacy_config_path.is_file():
        try:
            config_data = json.loads(legacy_config_path.read_text(encoding="utf-8"))
            config_version = config_data.get("version", "0.0.0")
            issues.append("Config located at legacy path .tc/config.json; needs migration to _tc/config.json")
        except Exception as e:
            issues.append(f"Corrupt .tc/config.json: {e}")
            return {
                "ok": False,
                "workspace": str(ws),
                "status": "corrupt",
                "current_version": None,
                "target_version": CURRENT_SCHEMA_VERSION,
                "missing_directories": missing_dirs,
                "missing_scripts": missing_scripts,
                "issues": issues,
            }
    else:
        issues.append("Missing configuration file (_tc/config.json)")

    # Check scripts directory
    scripts_dir = ws / "_tc" / "scripts"
    for script_name in CANONICAL_SCRIPTS:
        script_path = scripts_dir / script_name
        if not script_path.exists():
            missing_scripts.append(script_name)
            issues.append(f"Missing runtime script: _tc/scripts/{script_name}")

    # Determine status
    if not issues and config_version == CURRENT_SCHEMA_VERSION and not legacy_found:
        status = "healthy"
    elif config_path.exists() or legacy_config_path.exists() or missing_dirs or legacy_found or (config_version and config_version != CURRENT_SCHEMA_VERSION):
        status = "needs_migration"
    else:
        status = "corrupt"

    return {
        "ok": True,
        "workspace": str(ws),
        "status": status,
        "current_version": config_version,
        "target_version": CURRENT_SCHEMA_VERSION,
        "missing_directories": missing_dirs,
        "missing_scripts": missing_scripts,
        "legacy_directories": legacy_found,
        "issues": issues,
    }


def plan_migration(
    workspace_path: Path | str,
    output_report_path: Path | str | None = None,
) -> dict[str, Any]:
    """Generate non-destructive dry-run migration plan and report without modifying disk."""
    ws = Path(workspace_path).resolve()
    health = check_workspace_health(ws)

    if health["status"] == "corrupt":
        raise ValueError(f"Cannot plan migration for corrupt workspace: {health['issues']}")

    actions: list[dict[str, Any]] = []

    # 1. Directories to create
    for d in health["missing_directories"]:
        actions.append({
            "type": "create_directory",
            "path": d,
            "description": f"Create canonical directory '{d}'",
        })

    # 2. Legacy directory migrations
    legacy_dest_map = {
        ".tc": "_tc",
        "research": "_tc/research",
        "sources": "_tc/sources",
        "plan": "_tc/plan",
        "profile": "_tc/profile",
        "roadmap": "_tc/roadmap",
    }
    for leg_dir in health.get("legacy_directories", []):
        dest = legacy_dest_map.get(leg_dir, f"_tc/{leg_dir}")
        actions.append({
            "type": "migrate_directory",
            "source": leg_dir,
            "destination": dest,
            "description": f"Consolidate legacy '{leg_dir}/' into canonical '{dest}/' with byte-parity verification",
        })

    # 3. Config updates
    curr_v = health["current_version"]
    if curr_v != CURRENT_SCHEMA_VERSION or (ws / ".tc" / "config.json").is_file():
        actions.append({
            "type": "update_config",
            "path": "_tc/config.json",
            "from_version": curr_v or "none",
            "to_version": CURRENT_SCHEMA_VERSION,
            "description": f"Upgrade workspace schema version from {curr_v or 'unversioned'} to {CURRENT_SCHEMA_VERSION}",
        })

    # 4. Scripts to deploy or update
    for script_name in health["missing_scripts"]:
        actions.append({
            "type": "copy_script",
            "path": f"_tc/scripts/{script_name}",
            "description": f"Deploy runtime script '{script_name}' set to executable mode",
        })

    # Generate Markdown migration report
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_lines = [
        "# TextCourses Migration Plan (Dry Run)",
        "",
        f"- **Workspace**: `{ws}`",
        f"- **Generated At**: {now_str}",
        f"- **Current Status**: `{health['status']}`",
        f"- **Current Version**: `{health['current_version'] or 'unversioned'}`",
        f"- **Target Version**: `{CURRENT_SCHEMA_VERSION}`",
        f"- **Total Planned Actions**: {len(actions)}",
        "",
        "## Planned Actions",
        "",
    ]

    if not actions:
        report_lines.append("No actions needed. Workspace is already up to date and healthy.\n")
    else:
        for idx, act in enumerate(actions, 1):
            if act["type"] == "migrate_directory":
                report_lines.append(f"{idx}. **[{act['type']}]** `{act['source']}` -> `{act['destination']}`: {act['description']}")
            else:
                report_lines.append(f"{idx}. **[{act['type']}]** `{act['path']}`: {act['description']}")
        report_lines.append("")
        report_lines.append("> ⚠️ **Consent Gate Notice**")
        report_lines.append("> No filesystem changes have been made.")
        report_lines.append(f"> To apply these changes, execute: `uv run _tc/scripts/migrator.py apply --workspace . --confirm {CONFIRM_TOKEN}`\n")

    report_content = "\n".join(report_lines)

    report_file = Path(output_report_path).resolve() if output_report_path else ws / "migration-plan.md"
    atomic_write_text(report_file, report_content)

    return {
        "ok": True,
        "workspace": str(ws),
        "status": health["status"],
        "plan_file": str(report_file),
        "actions_count": len(actions),
        "actions": actions,
    }


def apply_migration(
    workspace_path: Path | str,
    confirm_token: str | None = None,
) -> dict[str, Any]:
    """Execute migration atomically strictly gated behind typed user confirmation."""
    ws = Path(workspace_path).resolve()

    if confirm_token != CONFIRM_TOKEN:
        raise PermissionError(
            f"Explicit confirmation required. Pass '--confirm {CONFIRM_TOKEN}' to apply mutations."
        )

    health = check_workspace_health(ws)
    if health["status"] == "corrupt":
        raise ValueError(f"Cannot migrate corrupt workspace: {health['issues']}")

    executed_actions: list[str] = []

    # 1. Create missing canonical directories
    for rel_dir in REQUIRED_CANONICAL_DIRS:
        target_dir = ws / rel_dir
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            executed_actions.append(f"Created canonical directory {rel_dir}")

    # 2. Migrate legacy directories with byte-parity verification
    # A. .tc/ -> _tc/
    legacy_tc = ws / ".tc"
    if legacy_tc.is_dir():
        for p in list(legacy_tc.rglob("*")):
            if p.is_file():
                rel = p.relative_to(legacy_tc)
                if rel == Path("config.json"):
                    continue
                dest = ws / "_tc" / rel
                verify_and_move_file(p, dest)
                executed_actions.append(f"Migrated .tc/{rel} -> _tc/{rel} (parity verified)")
        remove_empty_dir_tree(legacy_tc)

    # B. research/ -> _tc/research/
    legacy_res = ws / "research"
    if legacy_res.is_dir():
        for p in list(legacy_res.rglob("*")):
            if p.is_file():
                rel = p.relative_to(legacy_res)
                dest = ws / "_tc" / "research" / rel
                verify_and_move_file(p, dest)
                executed_actions.append(f"Migrated research/{rel} -> _tc/research/{rel} (parity verified)")
        remove_empty_dir_tree(legacy_res)

    # C. sources/ -> _tc/sources/
    legacy_src = ws / "sources"
    if legacy_src.is_dir():
        for p in list(legacy_src.rglob("*")):
            if p.is_file():
                rel = p.relative_to(legacy_src)
                dest = ws / "_tc" / "sources" / rel
                verify_and_move_file(p, dest)
                executed_actions.append(f"Migrated sources/{rel} -> _tc/sources/{rel} (parity verified)")
        remove_empty_dir_tree(legacy_src)

    # D. plan/ -> _tc/
    legacy_plan = ws / "plan"
    if legacy_plan.is_dir():
        for p in list(legacy_plan.rglob("*")):
            if p.is_file():
                rel = p.relative_to(legacy_plan)
                if rel == Path("preferences.md"):
                    dest = ws / "_tc" / "profile" / "preferences.md"
                elif rel == Path("roadmap.toml"):
                    dest = ws / "_tc" / "roadmap" / "roadmap.toml"
                elif str(rel).startswith("sources"):
                    dest = ws / "_tc" / rel
                else:
                    dest = ws / "_tc" / "plan" / rel
                verify_and_move_file(p, dest)
                executed_actions.append(f"Migrated plan/{rel} -> {dest.relative_to(ws)} (parity verified)")
        remove_empty_dir_tree(legacy_plan)

    # E. profile/ -> _tc/profile/
    legacy_prof = ws / "profile"
    if legacy_prof.is_dir():
        for p in list(legacy_prof.rglob("*")):
            if p.is_file():
                rel = p.relative_to(legacy_prof)
                dest = ws / "_tc" / "profile" / rel
                verify_and_move_file(p, dest)
                executed_actions.append(f"Migrated profile/{rel} -> _tc/profile/{rel} (parity verified)")
        remove_empty_dir_tree(legacy_prof)

    # F. roadmap/ -> _tc/roadmap/
    legacy_road = ws / "roadmap"
    if legacy_road.is_dir():
        for p in list(legacy_road.rglob("*")):
            if p.is_file():
                rel = p.relative_to(legacy_road)
                dest = ws / "_tc" / "roadmap" / rel
                verify_and_move_file(p, dest)
                executed_actions.append(f"Migrated roadmap/{rel} -> _tc/roadmap/{rel} (parity verified)")
        remove_empty_dir_tree(legacy_road)

    # 3. Update / write canonical _tc/config.json
    config_path = ws / "_tc" / "config.json"
    legacy_config = ws / ".tc" / "config.json"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    config_data: dict[str, Any] = {}

    if config_path.is_file():
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            config_data = {}
    elif legacy_config.is_file():
        try:
            config_data = json.loads(legacy_config.read_text(encoding="utf-8"))
        except Exception:
            config_data = {}

    if not config_data:
        config_data = {
            "framework": "TextCourses",
            "created_at": now_iso,
            "settings": {
                "default_archetype": "applied_creation",
                "default_style": "direct_technical",
                "density": "example_driven",
            },
        }

    config_data["version"] = CURRENT_SCHEMA_VERSION
    config_data["updated_at"] = now_iso
    atomic_write_json(config_path, config_data)
    executed_actions.append(f"Updated _tc/config.json schema version to {CURRENT_SCHEMA_VERSION}")

    if legacy_config.is_file():
        legacy_config.unlink()
        remove_empty_dir_tree(legacy_tc)

    # 4. Synchronize / deploy missing canonical runtime scripts
    canonical_dir = find_canonical_scripts_dir()
    scripts_dest = ws / "_tc" / "scripts"
    scripts_dest.mkdir(parents=True, exist_ok=True)

    if canonical_dir and canonical_dir.is_dir() and canonical_dir != scripts_dest:
        for script_name in CANONICAL_SCRIPTS:
            src_script = canonical_dir / script_name
            dest_script = scripts_dest / script_name
            if src_script.is_file() and not dest_script.exists():
                shutil.copy2(src_script, dest_script)
                try:
                    dest_script.chmod(dest_script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except OSError:
                    pass
                executed_actions.append(f"Deployed script _tc/scripts/{script_name}")

    # Clean up migration plan file if present
    plan_file = ws / "migration-plan.md"
    if plan_file.is_file():
        plan_file.unlink(missing_ok=True)
        executed_actions.append("Removed temporary migration-plan.md")

    return {
        "ok": True,
        "migrated": True,
        "workspace": str(ws),
        "version": CURRENT_SCHEMA_VERSION,
        "actions_performed": executed_actions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="migrator.py",
        description="TextCourses consent-gated schema migrator and health auditor.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # check
    p_check = subparsers.add_parser("check", help="Audit workspace health and schema versions.")
    p_check.add_argument("--path", "--workspace", dest="path", required=True, help="Path to workspace directory.")
    p_check.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # plan
    p_plan = subparsers.add_parser("plan", help="Generate non-destructive dry-run migration plan.")
    p_plan.add_argument("--path", "--workspace", dest="path", required=True, help="Path to workspace directory.")
    p_plan.add_argument("--output", default=None, help="Optional output path for migration-plan.md.")
    p_plan.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # apply
    p_apply = subparsers.add_parser("apply", help="Apply migrations with explicit typed confirmation.")
    p_apply.add_argument("--path", "--workspace", dest="path", required=True, help="Path to workspace directory.")
    p_apply.add_argument("--confirm", "--token", dest="confirm", default=None, help=f"Confirmation token (must be '{CONFIRM_TOKEN}').")
    p_apply.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args()

    try:
        if args.subcommand == "check":
            result = check_workspace_health(args.path)
            output_json(result, 0)

        elif args.subcommand == "plan":
            result = plan_migration(args.path, output_report_path=args.output)
            output_json(result, 0)

        elif args.subcommand == "apply":
            result = apply_migration(args.path, confirm_token=args.confirm)
            output_json(result, 0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except PermissionError as pe:
        output_json({"error": str(pe), "ok": False}, 1)
    except Exception as e:
        output_json({"error": str(e), "ok": False}, 1)


if __name__ == "__main__":
    main()
