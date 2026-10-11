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
import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any

CURRENT_SCHEMA_VERSION = "0.2.0"
CONFIRM_TOKEN = "APPLY"

REQUIRED_DIRS = [
    ".tc",
    ".tc/cache",
    ".tc/research",
    "_tc/scripts",
    "plan",
    "plan/sources",
    "courses",
    "portfolio",
]

CANONICAL_SCRIPTS = [
    "manifest.py",
    "ledger.py",
    "dag.py",
    "context.py",
    "hash_tracker.py",
    "bootstrapper.py",
    "redirector.py",
    "migrator.py",
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


def check_workspace_health(workspace_path: Path | str) -> dict[str, Any]:
    """Inspect workspace health, layout, and configuration version."""
    ws = Path(workspace_path).resolve()
    if not ws.exists():
        raise FileNotFoundError(f"Target workspace does not exist: {ws}")
    if not ws.is_dir():
        raise NotADirectoryError(f"Target workspace is not a directory: {ws}")

    config_path = ws / ".tc" / "config.json"
    issues: list[str] = []
    missing_dirs: list[str] = []
    missing_scripts: list[str] = []

    # Check required directories
    for rel_dir in REQUIRED_DIRS:
        target_dir = ws / rel_dir
        if not target_dir.exists():
            missing_dirs.append(rel_dir)
            issues.append(f"Missing required directory: {rel_dir}")
        elif not target_dir.is_dir():
            issues.append(f"Path exists but is not a directory: {rel_dir}")

    # Check .tc/config.json
    config_version: str | None = None
    config_data: dict[str, Any] = {}
    if not config_path.exists():
        issues.append("Missing .tc/config.json configuration file")
    else:
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
            config_version = config_data.get("version", "0.0.0")
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

    # Check scripts directory
    scripts_dir = ws / "_tc" / "scripts"
    for script_name in CANONICAL_SCRIPTS:
        script_path = scripts_dir / script_name
        if not script_path.exists():
            missing_scripts.append(script_name)
            issues.append(f"Missing runtime script: _tc/scripts/{script_name}")

    # Determine status
    if not issues and config_version == CURRENT_SCHEMA_VERSION:
        status = "healthy"
    elif config_path.exists() or missing_dirs or (config_version and config_version != CURRENT_SCHEMA_VERSION):
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
            "description": f"Create missing workspace directory '{d}'",
        })

    # 2. Config updates
    curr_v = health["current_version"]
    if curr_v != CURRENT_SCHEMA_VERSION:
        actions.append({
            "type": "update_config",
            "path": ".tc/config.json",
            "from_version": curr_v or "none",
            "to_version": CURRENT_SCHEMA_VERSION,
            "description": f"Upgrade workspace schema version from {curr_v or 'unversioned'} to {CURRENT_SCHEMA_VERSION}",
        })

    # 3. Scripts to deploy or update
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
            report_lines.append(f"{idx}. **[{act['type']}]** `{act['path']}`: {act['description']}")
        report_lines.append("")
        report_lines.append("> ⚠️ **Consent Gate Notice**")
        report_lines.append("> No filesystem changes have been made.")
        report_lines.append(f"> To apply these changes, execute: `uv run _tc/scripts/migrator.py apply --path . --confirm {CONFIRM_TOKEN}`\n")

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

    # 1. Create missing directories
    for rel_dir in health["missing_directories"]:
        target_dir = ws / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        executed_actions.append(f"Created directory {rel_dir}")

    # 2. Update .tc/config.json
    config_path = ws / ".tc" / "config.json"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if config_path.exists():
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            config_data = {}
    else:
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
    executed_actions.append(f"Updated .tc/config.json schema version to {CURRENT_SCHEMA_VERSION}")

    # 3. Synchronize / deploy missing scripts
    canonical_dir = find_canonical_scripts_dir()
    scripts_dest = ws / "_tc" / "scripts"
    scripts_dest.mkdir(parents=True, exist_ok=True)

    if canonical_dir and canonical_dir.is_dir() and canonical_dir != scripts_dest:
        for script_name in CANONICAL_SCRIPTS:
            src_script = canonical_dir / script_name
            dest_script = scripts_dest / script_name
            if src_script.is_file() and not dest_script.exists():
                shutil.copy2(src_script, dest_script)
                dest_script.chmod(dest_script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
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
    p_check.add_argument("--path", required=True, help="Path to workspace directory.")
    p_check.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # plan
    p_plan = subparsers.add_parser("plan", help="Generate non-destructive dry-run migration plan.")
    p_plan.add_argument("--path", required=True, help="Path to workspace directory.")
    p_plan.add_argument("--output", default=None, help="Optional output path for migration-plan.md.")
    p_plan.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # apply
    p_apply = subparsers.add_parser("apply", help="Apply migrations with explicit typed confirmation.")
    p_apply.add_argument("--path", required=True, help="Path to workspace directory.")
    p_apply.add_argument("--confirm", default=None, help=f"Confirmation token (must be '{CONFIRM_TOKEN}').")
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
