#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""ledger.py — Deterministic diagnostic assessment ledger engine for TextCourses.

Handles atomic, append-only logging of diagnostic assessments to test-ledger.jsonl
with POSIX advisory file locking (fcntl.flock), strict schema validation, and
ultra-compact (<100 tokens) misconception summarization to protect AI context budgets.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any

VALID_OUTCOMES = {"pass", "fail", "correct", "incorrect", "passed", "failed"}

# Core fields required when appending a new diagnostic record
REQUIRED_RECORD_FIELDS = [
    "course",
    "chapter",
    "section",
    "question_type",
    "prompt",
    "learner_response",
    "outcome",
]

# Fields required in persistent test-ledger.jsonl records
REQUIRED_LEDGER_FIELDS = [
    "timestamp",
    *REQUIRED_RECORD_FIELDS,
]


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (or stderr on error) and exit."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def resolve_ledger_path(path_arg: str | None, course_slug: str | None = None) -> Path:
    """Resolve target test-ledger.jsonl path from --path or --course arguments."""
    if path_arg:
        p = Path(path_arg)
        if p.suffix == ".jsonl":
            return p
        if p.is_file():
            return p
        return p / "test-ledger.jsonl"
    elif course_slug:
        return Path("courses") / course_slug / "test-ledger.jsonl"
    else:
        raise ValueError("Either --path or --course must be provided")


def cmd_append(args: argparse.Namespace) -> None:
    """Atomically append a validated diagnostic record to test-ledger.jsonl."""
    try:
        ledger_path = resolve_ledger_path(args.path)
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    # Read record JSON from argument or stdin
    record_raw = args.record
    if record_raw == "-":
        record_raw = sys.stdin.read()

    try:
        record_data = json.loads(record_raw)
    except json.JSONDecodeError as e:
        output_json({
            "ok": False,
            "error": f"Invalid JSON in --record: {e}",
        }, exit_code=1)

    if not isinstance(record_data, dict):
        output_json({
            "ok": False,
            "error": "Record must be a JSON object",
        }, exit_code=1)

    # Validate required fields
    missing_fields = [f for f in REQUIRED_RECORD_FIELDS if f not in record_data]
    if missing_fields:
        output_json({
            "ok": False,
            "error": f"Record missing required keys: {', '.join(missing_fields)}",
            "missing_keys": missing_fields,
        }, exit_code=1)

    # Validate outcome
    outcome = str(record_data.get("outcome", "")).strip().lower()
    if outcome not in VALID_OUTCOMES:
        output_json({
            "ok": False,
            "error": f"Invalid outcome '{record_data.get('outcome')}'. Must be one of {sorted(VALID_OUTCOMES)}",
        }, exit_code=1)

    # Ensure timestamp
    timestamp = record_data.get("timestamp")
    if not timestamp or not isinstance(timestamp, str):
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Construct canonical record
    canonical_record: dict[str, Any] = {
        "timestamp": timestamp,
        "course": str(record_data["course"]),
        "chapter": record_data["chapter"],
        "section": record_data["section"],
        "question_type": str(record_data["question_type"]),
        "prompt": str(record_data["prompt"]),
        "learner_response": str(record_data["learner_response"]),
        "outcome": outcome,
        "diagnosed_misconception": record_data.get("diagnosed_misconception"),
        "remediation_summary": record_data.get("remediation_summary"),
        "confidence_level": record_data.get("confidence_level", "medium"),
    }

    # Retain any extra keys
    for k, v in record_data.items():
        if k not in canonical_record:
            canonical_record[k] = v

    json_line = json.dumps(canonical_record, ensure_ascii=False)

    # Append under POSIX advisory lock (fcntl.flock)
    try:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        import fcntl
        with open(ledger_path, "a", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(json_line + "\n")
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        output_json({
            "ok": False,
            "error": f"Failed to append record to {ledger_path}: {e}",
        }, exit_code=1)

    output_json({
        "ok": True,
        "message": f"Appended record to {ledger_path}",
        "path": str(ledger_path),
        "record": canonical_record,
    })


def cmd_summarize(args: argparse.Namespace) -> None:
    """Summarize active misconceptions, weak sections, and pass rate under 100 tokens."""
    try:
        ledger_path = resolve_ledger_path(args.path, getattr(args, "course", None))
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    empty_digest: dict[str, Any] = {
        "ok": True,
        "total_tests": 0,
        "pass_rate": 0.0,
        "weak_sections": [],
        "active_misconceptions": [],
    }

    if not ledger_path.exists() or ledger_path.stat().st_size == 0:
        output_json(empty_digest)

    total_tests = 0
    passed_tests = 0
    section_stats: dict[str, dict[str, int]] = {}
    misconceptions: list[str] = []

    try:
        import fcntl
        with open(ledger_path, "r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        record = json.loads(line_str)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(record, dict):
                        continue

                    total_tests += 1
                    outcome = str(record.get("outcome", "")).strip().lower()
                    is_pass = outcome in {"pass", "correct", "passed"}
                    if is_pass:
                        passed_tests += 1

                    sec = str(record.get("section", "")).strip()
                    if sec:
                        if sec not in section_stats:
                            section_stats[sec] = {"total": 0, "passed": 0, "failed": 0}
                        section_stats[sec]["total"] += 1
                        if is_pass:
                            section_stats[sec]["passed"] += 1
                        else:
                            section_stats[sec]["failed"] += 1

                    misc = record.get("diagnosed_misconception")
                    if misc is not None:
                        misc_str = str(misc).strip()
                        if misc_str and misc_str.lower() not in {"null", "none"}:
                            misconceptions.append(misc_str)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        output_json({"ok": False, "error": f"Failed to read ledger: {e}"}, exit_code=1)

    if total_tests == 0:
        output_json(empty_digest)

    pass_rate = round(passed_tests / total_tests, 2)

    # Weak sections: sections with failures and pass rate < 0.8, sorted weakest first
    weak_candidates: list[tuple[str, float, int]] = []
    for sec, stats in section_stats.items():
        rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0.0
        if stats["failed"] > 0 and rate < 0.8:
            weak_candidates.append((sec, rate, stats["failed"]))

    # Sort weakest first (lowest pass rate, highest failures)
    weak_candidates.sort(key=lambda x: (x[1], -x[2]))
    weak_sections = [w[0] for w in weak_candidates]

    # Deduplicate misconceptions preserving order
    deduped_misconceptions = list(dict.fromkeys(misconceptions))

    digest: dict[str, Any] = {
        "ok": True,
        "total_tests": total_tests,
        "pass_rate": pass_rate,
        "weak_sections": weak_sections[:5],
        "active_misconceptions": deduped_misconceptions[:5],
    }

    # Strict compaction invariant: must remain < 100 tokens (< 400 characters)
    # 1 token ≈ 4 characters; keeping JSON strictly < 380 chars ensures < 100 tokens.
    while len(json.dumps(digest, indent=2)) >= 380 and (digest["active_misconceptions"] or digest["weak_sections"]):
        if len(digest["active_misconceptions"]) > len(digest["weak_sections"]):
            digest["active_misconceptions"].pop()
        else:
            digest["weak_sections"].pop()

    output_json(digest)


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate schema compliance and integrity of all records in test-ledger.jsonl."""
    try:
        ledger_path = resolve_ledger_path(args.path)
    except Exception as e:
        output_json({"ok": False, "error": str(e)}, exit_code=1)

    if not ledger_path.exists():
        output_json({
            "ok": False,
            "valid": False,
            "error": f"Ledger file not found: {ledger_path}",
        }, exit_code=1)

    errors: list[str] = []
    total_records = 0

    try:
        import fcntl
        with open(ledger_path, "r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                for line_num, line in enumerate(f, start=1):
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        record = json.loads(line_str)
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {line_num}: Invalid JSON - {e}")
                        continue

                    if not isinstance(record, dict):
                        errors.append(f"Line {line_num}: Record must be a JSON object")
                        continue

                    missing = [f for f in REQUIRED_LEDGER_FIELDS if f not in record]
                    if missing:
                        errors.append(f"Line {line_num}: Missing required field(s): {', '.join(missing)}")
                        continue

                    outcome = str(record.get("outcome", "")).strip().lower()
                    if outcome not in VALID_OUTCOMES:
                        errors.append(f"Line {line_num}: Invalid outcome '{record.get('outcome')}'")

                    if not isinstance(record.get("timestamp"), str):
                        errors.append(f"Line {line_num}: 'timestamp' must be a string")

                    total_records += 1
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        output_json({
            "ok": False,
            "valid": False,
            "error": f"Failed to read ledger {ledger_path}: {e}",
        }, exit_code=1)

    if errors:
        output_json({
            "ok": False,
            "valid": False,
            "error": f"Ledger validation failed with {len(errors)} error(s)",
            "errors": errors,
            "path": str(ledger_path),
        }, exit_code=1)

    output_json({
        "ok": True,
        "valid": True,
        "total_records": total_records,
        "path": str(ledger_path),
    })


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TextCourses deterministic assessment ledger engine"
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # append
    p_append = subparsers.add_parser("append", help="Atomically append a diagnostic record")
    p_append.add_argument("--path", required=True, help="Course directory or test-ledger.jsonl path")
    p_append.add_argument("--record", required=True, help="JSON record string or '-' for stdin")
    p_append.set_defaults(func=cmd_append)

    # summarize
    p_sum = subparsers.add_parser("summarize", help="Summarize ledger into compact (<100 tokens) JSON digest")
    p_sum.add_argument("--path", help="Course directory or test-ledger.jsonl path")
    p_sum.add_argument("--course", help="Course slug (alternative to --path)")
    p_sum.set_defaults(func=cmd_summarize)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate schema integrity of test-ledger.jsonl")
    p_val.add_argument("--path", required=True, help="Course directory or test-ledger.jsonl path")
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
