---
title: "Canonical 4-Hat Adversarial Research Debate & Decision Log"
ticket: 12
status: done
epic: epic-consumer-ux-and-unified-tc
covers: [CAP-5, FR-30, FR-31]
completed_at: "2026-11-06T20:56:00+05:30"
---

# Story 12.12: Canonical 4-Hat Adversarial Research Debate & Decision Log (CAP-5, FR-30, FR-31)

## Summary
Replaced the prior templated critique with the canonical 4-Hat Adversarial Dialectic Debate Protocol. Conducts genuine adversarial challenge rounds across 4 voting archetypes (Industry Practitioner, Academic Purist, Beginner Friction Hunter, Edge-Case Systems Engineer) with non-voting AI-Era Specialist advisory. Writes full decision logs with stances, cross-examination challenges, and resolution votes to `_tc/research/<slug>/debate.jsonl` and renders readable summaries to `_tc/research/<slug>/debate-summary.md`.

## Architectural Changes & Implementation Details
1. **Canonical 4-Hat Registry & Dialectic Protocol (`_tc/scripts/scout.py`)**:
   - Defined `FOUR_VOTING_HATS` (`applied_practitioner`, `academic_purist`, `beginner_friction_hunter`, `edge_case_systems_engineer`) and `SPECIALIST_HAT` (`ai_era_strategist`).
   - Implemented `conduct_four_hat_debate(slug, topic, parsed, workspace)`.
   - Executes multi-round adversarial debates across 3 essential pedagogical decisions:
     1. Invariant model vs immediate runnable execution (Dual-Register Anchor).
     2. Domain vocabulary introduction (Zero-Unearned-Jargon with Just-In-Time Precision).
     3. Boundary failure injection depth (Mandatory End-of-Section Invariant Stress-Testing).
2. **Artifact Generation & Decision Persistence (`_tc/scripts/scout.py`)**:
   - Generates `_tc/research/<slug>/debate.jsonl` (one JSON line per decision record containing positions, specialist advice, challenge-round exchanges, resolution rationale, confidence, and votes).
   - Generates `_tc/research/<slug>/debate-summary.md` detailing the faculty, tensions, challenges, and resolved verdicts.
   - Dual-mirrors to legacy `research/<slug>/` and `.tc/research/<slug>/`.
   - Updated `run_scout` to execute the debate automatically and record debate file paths in `digest.json`.
3. **CLI & Cache Access (`_tc/scripts/scout.py`)**:
   - Implemented `get_cached_debate` and `get_cached_debate_summary`.
   - Added CLI subcommand `scout.py debate` supporting `--slug`, `--topic`, and `--json`.

## Verification
- Created `tests/test_four_hat_debate.py` (3 tests, 100% passed):
  - `test_conduct_four_hat_debate_protocol`
  - `test_scout_run_generates_debate_artifacts`
  - `test_scout_cli_debate_subcommand`
- Verified regression suite (`tests/test_five_hat_research.py`): 5 passed.
