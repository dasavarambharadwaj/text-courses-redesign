---
type: initiative
title: "TextCourses Framework"
parent: none
covers: [FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-10, FR-11, FR-12, FR-13, FR-14, FR-15, FR-16, FR-17, FR-18, FR-19, FR-20, FR-21, FR-22, FR-23]
assignee: ""
risk: medium
---

# TextCourses Framework
**The Sovereign, Open-Source Autonomous Apprenticeship Engine**

## Description

TextCourses transforms any local workspace into an interactive, self-paced, AI-tutored digital academy. It pairs lightweight AI skills with a customizable, learner-configured curriculum and a deterministic Python substrate to enable deep, active mastery of any technical or non-technical domain. The PRD and Architecture Spine own the functional requirements, architectural invariants, and non-goals; this initiative delivers the complete 9-skill framework, shared deterministic engine runtime, and tests.

## Outcome

Learners transition from passive video watching and amnesic AI chat feeds to a sovereign, filesystem-native learning loop, completing rigorous courses at $>45\%$ completion rate with a permanent, personalized reference textbook (`notes.md`) and verified human proof of work (`portfolio/`).

## Requirements

The initiative delivers all 23 Functional Requirements from the PRD:
- Onboarding & Navigation: `FR-1`, `FR-2`, `FR-3`
- Curriculum Architecture & Triad Consensus: `FR-4`, `FR-5`, `FR-6`, `FR-7`, `FR-8`
- Pedagogical Delivery & Notes Distillation: `FR-9`, `FR-10`, `FR-11`, `FR-12`
- Diagnostic Testing & Assessment Ledger: `FR-13`, `FR-14`, `FR-15`
- Applied Proof of Work & Multi-Lens Review: `FR-16`, `FR-17`, `FR-18`
- Lifecycle Management & Safe Migration: `FR-19`, `FR-20`, `FR-21`
- Context Engineering & Harness Agnosticism: `FR-22`, `FR-23`

## Done when

1. All 5 core deterministic scripts in `_tc/scripts/` (`manifest.py`, `ledger.py`, `dag.py`, `context.py`, `hash_tracker.py`) pass unit tests in `tests/`.
2. All 9 canonical skills are packaged under `skills/tc-*/` with valid `SKILL.md`, `customize.toml`, and runtime hooks.
3. The vertical tracer path succeeds end-to-end: `/tc-init` sets up a workspace, `/tc-create` generates a prerequisite-verified course via the Triad Loop, `/tc-teach` teaches Section 1 and compiles `notes.md`, and `/tc-test-me` records diagnostic results to `test-ledger.jsonl`.
4. The 4-Lens Review pass in `tc-practicals` verifies sample project deliverables in `portfolio/`.
5. Universal safety guardrails refuse forbidden topics across all skills.

## Boundaries

The open-source core framework, its 9 skills, the shared deterministic runtime, and standard workspace filesystem layouts. Not a cloud SaaS web platform, not a video/audio streaming service, not a proctored exam engine.

- Touch point: Agent skill lockfile — `skills-lock.json` updated with new skill entries; owner: epic-runtime-engine.
- Touch point: Root workspace config — `_tc/` canonical template deployed on init; owner: epic-onboarding-lifecycle.

## References

- prd — `_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md`
- architecture — `_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md`
- brief — `_bmad-output/initiative-textcourses/product-brief/product-brief.md`

## Notes

- Decision: Hybrid Deterministic Substrate adopted (AD-1) — Python scripts own state mutations, prompts own pedagogy (2026-10-10).
- Decision: Strict no-mention invariant in public docs; sovereign standard design (2026-10-10).
- Decision: 5-epic build sequence agreed (2026-10-10).
