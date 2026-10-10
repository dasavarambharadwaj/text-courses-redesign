---
type: epic
title: "Deterministic Engine Runtime"
parent: initiative-textcourses
covers: [FR-14, FR-19, FR-22]
after: []
assignee: ""
risk: medium
---

# Deterministic Engine Runtime

## Description

Implements the core Python 3.11+ deterministic substrate deployed in `_tc/scripts/` that all TextCourses skills rely on. This layer guarantees that all manifest updates (`course.toml`, `roadmap.toml`), atomic assessment logging (`test-ledger.jsonl`), prerequisite DAG cycle validation, context budget manifests, and SHA-256 source hash comparisons occur deterministically with zero risk of LLM syntax corruption.

## Outcome

All machine-readable filesystem mutations and schema validations are executed by atomic, standalone Python scripts with PEP 723 metadata via `uv run`, passing 100% of unit tests.

## Requirements

- `FR-14`: Atomic JSONL assessment ledger logger and compact misconception query summarizer (`ledger.py`).
- `FR-19`: Cryptographic SHA-256 source delta tracking (`hash_tracker.py`).
- `FR-22`: Stage-aware Context Loading Manifest engine enforcing file read boundaries (`context.py`).
- `AD-1, AD-2, AD-3`: Atomic write-and-replace for TOML manifests, file locks for JSONL appends, and standalone CLI interfaces (`manifest.py`, `dag.py`).

## Done when

1. `_tc/scripts/manifest.py` reads, updates, and validates `course.toml` and `roadmap.toml` with atomic write-and-replace (`os.fsync` + `os.replace`).
2. `_tc/scripts/ledger.py` appends validated JSONL records with file locks and provides a `--summarize` command returning compact JSON misconception digests.
3. `_tc/scripts/dag.py` builds prerequisite graphs and reliably catches cycles and missing antecedent references using `graphlib.TopologicalSorter`.
4. `_tc/scripts/context.py` enforces stage loading manifests for all 9 skills.
5. `_tc/scripts/hash_tracker.py` computes SHA-256 hashes and outputs modified/added deltas for `plan/sources/`.
6. Full test suite under `tests/` passes cleanly via `pytest`.

## Boundaries

The deterministic Python engine under `_tc/scripts/` and test runners in `tests/`. Not the skill prompts (`SKILL.md`) or human-facing instruction generation.

## References

- architecture — `_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md`, sections Invariants AD-1, AD-2, AD-3
- prd — `_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md`, sections 4.4, 4.6, 4.7

## Notes

- Decision: Inline PEP 723 metadata on every script (`# /// script ... # ///`) so users run with `uv run` without virtualenv management (2026-10-10).
- Decision: `ledger.py summarize` returns JSON under 100 tokens to protect context windows (2026-10-10).
