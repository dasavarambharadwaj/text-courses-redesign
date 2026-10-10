import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pytest

LEDGER_SCRIPT = Path(__file__).parent.parent / "_tc" / "scripts" / "ledger.py"


def run_ledger(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    """Helper to run ledger.py CLI and capture stdout/stderr."""
    cmd = [sys.executable, str(LEDGER_SCRIPT), *args]
    return subprocess.run(cmd, capture_output=True, text=True, input=input_text)


def _worker_append(args_tuple: tuple[str, str, int]) -> int:
    """Worker function for concurrent append test."""
    ledger_path_str, script_path_str, index = args_tuple
    record = {
        "course": "rust-primer",
        "chapter": "chapter-01",
        "section": f"section-{index:02d}",
        "question_type": "hinge",
        "prompt": f"Test prompt {index}",
        "learner_response": f"Response {index}",
        "outcome": "pass" if index % 2 == 0 else "fail",
        "diagnosed_misconception": None if index % 2 == 0 else f"CONFUSION_{index}",
    }
    cmd = [
        sys.executable,
        script_path_str,
        "append",
        "--path",
        ledger_path_str,
        "--record",
        json.dumps(record),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode


def test_ledger_help():
    """Verify help subcommand displays usage and expected subcommands."""
    result = run_ledger("--help")
    assert result.returncode == 0
    assert "TextCourses deterministic assessment ledger engine" in result.stdout
    assert "append" in result.stdout
    assert "summarize" in result.stdout
    assert "validate" in result.stdout


def test_append_creates_ledger_and_records(tmp_path: Path):
    """Verify append creates parent directory and test-ledger.jsonl with schema fields."""
    course_dir = tmp_path / "deep" / "nested" / "course-rust"
    record = {
        "course": "rust-primer",
        "chapter": "chapter-01",
        "section": "section-01",
        "question_type": "scenario",
        "prompt": "What is the lifetime of a temporary value?",
        "learner_response": "It lives until end of statement.",
        "outcome": "pass",
    }
    result = run_ledger("append", "--path", str(course_dir), "--record", json.dumps(record))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["ok"] is True
    assert "Appended record" in data["message"]

    ledger_file = course_dir / "test-ledger.jsonl"
    assert ledger_file.exists()

    lines = ledger_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    saved_record = json.loads(lines[0])
    assert saved_record["course"] == "rust-primer"
    assert saved_record["chapter"] == "chapter-01"
    assert saved_record["section"] == "section-01"
    assert saved_record["outcome"] == "pass"
    assert "timestamp" in saved_record
    assert saved_record["diagnosed_misconception"] is None
    assert saved_record["confidence_level"] == "medium"


def test_append_preserves_custom_timestamp_and_extras(tmp_path: Path):
    """Verify custom timestamp and additional metadata fields are preserved."""
    ledger_file = tmp_path / "test-ledger.jsonl"
    custom_ts = "2026-10-10T12:00:00Z"
    record = {
        "timestamp": custom_ts,
        "course": "distributed-systems",
        "chapter": 2,
        "section": 3,
        "question_type": "tradeoff",
        "prompt": "Evaluate linearizability vs sequential consistency.",
        "learner_response": "Linearizability requires real-time ordering.",
        "outcome": "correct",
        "diagnosed_misconception": None,
        "remediation_summary": "Accurate distinction.",
        "confidence_level": "high",
        "extra_tags": ["consensus", "safety"],
    }
    result = run_ledger("append", "--path", str(ledger_file), "--record", json.dumps(record))
    assert result.returncode == 0

    lines = ledger_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    saved = json.loads(lines[0])
    assert saved["timestamp"] == custom_ts
    assert saved["extra_tags"] == ["consensus", "safety"]
    assert saved["outcome"] == "correct"


def test_append_multiple_records_sequential(tmp_path: Path):
    """Verify repeated appends accumulate lines without overwriting or truncating."""
    ledger_file = tmp_path / "test-ledger.jsonl"
    for i in range(3):
        rec = {
            "course": "course-1",
            "chapter": "ch1",
            "section": "sec1",
            "question_type": "hinge",
            "prompt": f"Question {i}",
            "learner_response": f"Answer {i}",
            "outcome": "pass" if i % 2 == 0 else "fail",
            "diagnosed_misconception": f"MISCONCEPTION_{i}" if i % 2 != 0 else None,
        }
        res = run_ledger("append", "--path", str(ledger_file), "--record", json.dumps(rec))
        assert res.returncode == 0

    lines = ledger_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    for i, line in enumerate(lines):
        item = json.loads(line)
        assert item["prompt"] == f"Question {i}"


def test_append_invalid_json(tmp_path: Path):
    """Verify passing invalid JSON exits with code 1 and error on stderr."""
    res = run_ledger("append", "--path", str(tmp_path), "--record", "{malformed-json")
    assert res.returncode == 1
    err_data = json.loads(res.stderr)
    assert err_data["ok"] is False
    assert "Invalid JSON" in err_data["error"]


def test_append_non_dict_json(tmp_path: Path):
    """Verify passing non-dict JSON exits with code 1."""
    res = run_ledger("append", "--path", str(tmp_path), "--record", "[1, 2, 3]")
    assert res.returncode == 1
    err_data = json.loads(res.stderr)
    assert err_data["ok"] is False
    assert "Record must be a JSON object" in err_data["error"]


def test_append_missing_required_keys(tmp_path: Path):
    """Verify schema rejects incomplete record with specific missing field names."""
    res = run_ledger("append", "--path", str(tmp_path), "--record", '{"score": 1}')
    assert res.returncode == 1
    err_data = json.loads(res.stderr)
    assert err_data["ok"] is False
    assert "missing_keys" in err_data
    assert "course" in err_data["missing_keys"]
    assert "chapter" in err_data["missing_keys"]
    assert "section" in err_data["missing_keys"]
    assert "question_type" in err_data["missing_keys"]
    assert "prompt" in err_data["missing_keys"]
    assert "learner_response" in err_data["missing_keys"]
    assert "outcome" in err_data["missing_keys"]
    assert "Record missing required keys" in err_data["error"]


def test_append_invalid_outcome(tmp_path: Path):
    """Verify invalid outcome value is rejected."""
    record = {
        "course": "c1",
        "chapter": "ch1",
        "section": "sec1",
        "question_type": "hinge",
        "prompt": "q",
        "learner_response": "a",
        "outcome": "undecided",
    }
    res = run_ledger("append", "--path", str(tmp_path), "--record", json.dumps(record))
    assert res.returncode == 1
    err_data = json.loads(res.stderr)
    assert err_data["ok"] is False
    assert "Invalid outcome 'undecided'" in err_data["error"]


def test_append_via_stdin(tmp_path: Path):
    """Verify reading record from stdin when '--record -' is passed."""
    record = {
        "course": "stdin-course",
        "chapter": "ch1",
        "section": "sec1",
        "question_type": "hinge",
        "prompt": "Stdin test prompt",
        "learner_response": "Stdin response",
        "outcome": "pass",
    }
    res = run_ledger("append", "--path", str(tmp_path), "--record", "-", input_text=json.dumps(record))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True

    ledger_file = tmp_path / "test-ledger.jsonl"
    assert ledger_file.exists()
    content = json.loads(ledger_file.read_text(encoding="utf-8").strip())
    assert content["course"] == "stdin-course"


def test_validate_clean_ledger(tmp_path: Path):
    """Verify validate reports clean status on a valid ledger."""
    course_dir = tmp_path / "course"
    for i in range(3):
        rec = {
            "course": "c1",
            "chapter": "ch1",
            "section": "sec1",
            "question_type": "hinge",
            "prompt": f"p{i}",
            "learner_response": f"r{i}",
            "outcome": "pass",
        }
        run_ledger("append", "--path", str(course_dir), "--record", json.dumps(rec))

    res = run_ledger("validate", "--path", str(course_dir))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["valid"] is True
    assert data["total_records"] == 3


def test_validate_empty_ledger(tmp_path: Path):
    """Verify validate succeeds on an empty test-ledger.jsonl file."""
    ledger_file = tmp_path / "test-ledger.jsonl"
    ledger_file.write_text("", encoding="utf-8")
    res = run_ledger("validate", "--path", str(ledger_file))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["valid"] is True
    assert data["total_records"] == 0


def test_validate_missing_file(tmp_path: Path):
    """Verify validate fails with exit code 1 when ledger does not exist."""
    res = run_ledger("validate", "--path", str(tmp_path / "nonexistent"))
    assert res.returncode == 1
    err_data = json.loads(res.stderr)
    assert err_data["ok"] is False
    assert "Ledger file not found" in err_data["error"]


def test_validate_corrupt_lines(tmp_path: Path):
    """Verify validate identifies corrupted line numbers and schema discrepancies."""
    ledger_file = tmp_path / "test-ledger.jsonl"
    # Line 1: valid
    l1 = json.dumps({
        "timestamp": "2026-10-10T00:00:00Z",
        "course": "c1",
        "chapter": "ch1",
        "section": "sec1",
        "question_type": "hinge",
        "prompt": "p",
        "learner_response": "r",
        "outcome": "pass",
    })
    # Line 2: invalid json syntax
    l2 = "{broken json here"
    # Line 3: valid json but missing required fields
    l3 = json.dumps({"timestamp": "2026-10-10T00:00:00Z", "score": 99})
    # Line 4: invalid outcome
    l4 = json.dumps({
        "timestamp": "2026-10-10T00:00:00Z",
        "course": "c1",
        "chapter": "ch1",
        "section": "sec1",
        "question_type": "hinge",
        "prompt": "p",
        "learner_response": "r",
        "outcome": "not_an_outcome",
    })

    ledger_file.write_text("\n".join([l1, l2, l3, l4]), encoding="utf-8")

    res = run_ledger("validate", "--path", str(ledger_file))
    assert res.returncode == 1
    err_data = json.loads(res.stderr)
    assert err_data["ok"] is False
    assert err_data["valid"] is False
    errors = err_data["errors"]
    assert any("Line 2: Invalid JSON" in e for e in errors)
    assert any("Line 3: Missing required field(s)" in e for e in errors)
    assert any("Line 4: Invalid outcome" in e for e in errors)


def test_summarize_missing_or_empty(tmp_path: Path):
    """Verify summarize returns zeroed digest with exit 0 for missing or empty ledger."""
    empty_dir = tmp_path / "empty-course"
    empty_dir.mkdir()
    res = run_ledger("summarize", "--path", str(empty_dir))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["total_tests"] == 0
    assert data["pass_rate"] == 0.0
    assert data["weak_sections"] == []
    assert data["active_misconceptions"] == []


def test_summarize_populated_ledger(tmp_path: Path):
    """Verify summarize computes pass rate, deduplicates misconceptions, and identifies weak sections."""
    course_dir = tmp_path / "course-sample"
    records = [
        # section-01: 2 fails -> weak section, misconceptions
        {
            "course": "sample",
            "chapter": "ch1",
            "section": "section-01",
            "question_type": "hinge",
            "prompt": "p1",
            "learner_response": "r1",
            "outcome": "fail",
            "diagnosed_misconception": "CONFUSION_ASYNC_BLOCKING",
        },
        {
            "course": "sample",
            "chapter": "ch1",
            "section": "section-01",
            "question_type": "hinge",
            "prompt": "p2",
            "learner_response": "r2",
            "outcome": "fail",
            "diagnosed_misconception": "CONFUSION_ASYNC_BLOCKING",  # duplicate misconception
        },
        # section-02: 1 fail, 1 pass (pass rate = 0.5 < 0.8) -> weak section
        {
            "course": "sample",
            "chapter": "ch1",
            "section": "section-02",
            "question_type": "hinge",
            "prompt": "p3",
            "learner_response": "r3",
            "outcome": "fail",
            "diagnosed_misconception": "CONFUSION_EVENT_LOOP_STARVATION",
        },
        {
            "course": "sample",
            "chapter": "ch1",
            "section": "section-02",
            "question_type": "hinge",
            "prompt": "p4",
            "learner_response": "r4",
            "outcome": "pass",
        },
        # section-03: 2 passes -> strong section (not in weak_sections)
        {
            "course": "sample",
            "chapter": "ch1",
            "section": "section-03",
            "question_type": "hinge",
            "prompt": "p5",
            "learner_response": "r5",
            "outcome": "pass",
        },
        {
            "course": "sample",
            "chapter": "ch1",
            "section": "section-03",
            "question_type": "hinge",
            "prompt": "p6",
            "learner_response": "r6",
            "outcome": "pass",
        },
    ]

    for rec in records:
        run_ledger("append", "--path", str(course_dir), "--record", json.dumps(rec))

    res = run_ledger("summarize", "--path", str(course_dir))
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["total_tests"] == 6
    # 3 passes out of 6 tests = 0.5 pass_rate
    assert data["pass_rate"] == 0.5

    # section-01 (pass rate 0.0) and section-02 (pass rate 0.5) are weak; section-03 is not
    assert "section-01" in data["weak_sections"]
    assert "section-02" in data["weak_sections"]
    assert "section-03" not in data["weak_sections"]

    # Misconceptions deduplicated: CONFUSION_ASYNC_BLOCKING appears once
    assert data["active_misconceptions"] == [
        "CONFUSION_ASYNC_BLOCKING",
        "CONFUSION_EVENT_LOOP_STARVATION",
    ]


def test_summarize_token_budget_compactness(tmp_path: Path):
    """Verify summarize output strictly adheres to <100 tokens (<400 characters) budget."""
    course_dir = tmp_path / "course-large"
    # Generate 40 diverse attempts with long misconceptions
    for i in range(40):
        rec = {
            "course": "huge-domain",
            "chapter": f"ch{i % 5}",
            "section": f"section-{i:02d}",
            "question_type": "hinge",
            "prompt": f"Deep diagnostic question regarding architectural mechanism {i}",
            "learner_response": f"Learner elaborate conceptual response {i}",
            "outcome": "fail" if i % 2 == 0 else "pass",
            "diagnosed_misconception": f"LONG_CONFUSION_IDENTIFIER_REGARDING_SUBSYSTEM_{i}",
        }
        run_ledger("append", "--path", str(course_dir), "--record", json.dumps(rec))

    res = run_ledger("summarize", "--path", str(course_dir))
    assert res.returncode == 0
    # Check that raw output text is strictly < 400 characters (< 100 tokens)
    raw_output = res.stdout.strip()
    assert len(raw_output) < 400, f"Summary exceeded token budget: {len(raw_output)} chars"

    data = json.loads(raw_output)
    assert data["ok"] is True
    assert data["total_tests"] == 40


def test_summarize_course_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify summarize resolves courses/<slug>/test-ledger.jsonl when --course is used."""
    monkeypatch.chdir(tmp_path)
    course_dir = tmp_path / "courses" / "my-course"
    rec = {
        "course": "my-course",
        "chapter": "ch1",
        "section": "sec1",
        "question_type": "hinge",
        "prompt": "q",
        "learner_response": "r",
        "outcome": "pass",
    }
    run_ledger("append", "--path", str(course_dir), "--record", json.dumps(rec))

    res = run_ledger("summarize", "--course", "my-course")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["total_tests"] == 1
    assert data["pass_rate"] == 1.0


def test_concurrent_appends(tmp_path: Path):
    """Verify simultaneous appends with fcntl.flock serialize cleanly without corruption."""
    ledger_file = tmp_path / "test-ledger.jsonl"
    concurrency_count = 20

    worker_args = [
        (str(ledger_file), str(LEDGER_SCRIPT), i)
        for i in range(concurrency_count)
    ]

    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(_worker_append, worker_args))

    # All workers must succeed
    assert all(code == 0 for code in results), f"Worker failure detected: {results}"

    # Verify line count matches exactly
    lines = ledger_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == concurrency_count, f"Expected {concurrency_count} lines, found {len(lines)}"

    # Verify every line is valid JSON without any interleaving or truncation
    for line in lines:
        record = json.loads(line)
        assert record["course"] == "rust-primer"
        assert "section" in record
        assert "timestamp" in record

    # Validate entire ledger using CLI validate command
    val_res = run_ledger("validate", "--path", str(ledger_file))
    assert val_res.returncode == 0
    val_data = json.loads(val_res.stdout)
    assert val_data["ok"] is True
    assert val_data["valid"] is True
    assert val_data["total_records"] == concurrency_count
