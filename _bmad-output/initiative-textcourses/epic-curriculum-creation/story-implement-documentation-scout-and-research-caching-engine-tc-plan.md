---
title: "Implement documentation scout and research caching engine (tc-research)"
type: "feature"
ticket: 1
created: "2026-10-10"
status: done
baseline_revision: "3b48f3a"
route: "full"
route_source: "auto"
risk: "medium"
review: "quick"
review_source: "pinned"
lenses_ran: []
review_loop_iteration: 0
context:
  - "_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md"
  - "_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md"
  - "_bmad-output/initiative-textcourses/epic-curriculum-creation/epic-curriculum-creation.md"
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Curriculum generation without grounded technical documentation leads to hallucinated APIs, deprecated syntax, and inaccurate prerequisites.
**Approach:** Implement `skills/tc-research/SKILL.md` and `skills/tc-research/scripts/scout.py` (and canonical `_tc/scripts/scout.py`). The scout scrapes or extracts documentation ToC, API indexes, and vocabulary concepts into `.tc/research/<slug>/digest.json` and `sources.toml` with confidence scoring (`high`, `medium`, `low`, `unverified`).

## Boundaries & Constraints

**Always:**
- Include PEP 723 inline script header (`requires-python = ">=3.11"`, `tomli-w>=1.0.0`).
- Cache research artifacts deterministically in `.tc/research/<slug>/digest.json` and `.tc/research/<slug>/sources.toml` (FR-6, AD-4).
- Assign confidence ratings: `high` (authoritative documentation), `medium` (secondary/partial), `low` (fragmented), `unverified` (pure fallback/zero sources).
- Support offline scraping and local file extraction as well as URL scraping.
- Output structured JSON to stdout on exit 0, stderr on exit 1.
- Strict zero BMad references in user-facing prompts, templates, and scripts.

**Never:**
- Never proceed silently with low confidence without explicit flagging.
- Never write directly to `courses/` directory from the research scout.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Local File Ingestion | `scout.py scout --slug rust --source-path doc.md` | Extracts ToC, API items, vocabulary; writes `.tc/research/rust/digest.json`; exits 0 | If file missing, exits 1 |
| Web URL Ingestion | `scout.py scout --slug react --url https://...` | Fetches/parses page ToC and APIs, marks confidence, writes digest, exits 0 | If network error, falls back with warning and exits 0/1 |
| Unverified Topic | `scout.py scout --slug unknown --topic "obscure lib"` | Produces fallback digest with `confidence: "unverified"`, exits 0 | Flags unverified state clearly |
| Query Cached Digest | `scout.py get --slug rust` | Outputs cached digest JSON to stdout, exits 0 | If not found, exits 1 |
| List Research Cache | `scout.py list` | Lists all cached research slugs and confidence scores, exits 0 | Empty list if none |

</frozen-after-approval>

## Code Map

- `skills/tc-research/SKILL.md` -- Autonomous documentation scout skill prompt and research guidelines.
- `skills/tc-research/scripts/scout.py` & `_tc/scripts/scout.py` -- Deterministic scout substrate for documentation ToC, API indexing, and confidence scoring.
- `tests/test_scout.py` -- Pytest test suite covering local extraction, confidence scoring, cache writing, retrieval, and zero BMad references.

## Tasks & Acceptance

**Execution:**
- [x] `_tc/scripts/scout.py` & `skills/tc-research/scripts/scout.py` -- Implement scout CLI with `scout`, `get`, and `list` subcommands (FR-6, AD-4).
- [x] `skills/tc-research/SKILL.md` -- Implement autonomous documentation scout prompt for curriculum research (FR-6).
- [x] `tests/test_scout.py` -- Unit tests validating ToC extraction, API symbol parsing, confidence scoring, cache persistence, and zero-BMad invariant.

**Acceptance Criteria:**
- Given a documentation file or URL, `scout.py scout` generates `.tc/research/<slug>/digest.json` containing ToC, API symbols, and vocabulary with a valid confidence level.
- `scout.py get` retrieves the cached digest.
- `scout.py list` lists all cached research topics.
- All tests pass cleanly with `uv run pytest`.

## Implementation Notes

Implemented `scout.py` in `_tc/scripts/` and `skills/tc-research/scripts/` with PEP 723 metadata, regex-based symbol and heading extractors, confidence classification, and atomic cache persistence. Implemented `skills/tc-research/SKILL.md`.

## Plan Change Log

## Review Triage Log

- Verified 7/7 unit tests in `tests/test_scout.py` pass cleanly.
- Verified 118/118 full test suite pass cleanly.
- Verified zero BMad references across scripts, skills, and tests.
- Verified deterministic caching in `.tc/research/<slug>/digest.json` and `sources.toml`.

## Verification

**Commands:**
- `uv run _tc/scripts/scout.py --help` -- expected: Displays available subcommands with exit code 0.
- `uv run pytest tests/test_scout.py` -- expected: All unit tests pass with exit code 0.
