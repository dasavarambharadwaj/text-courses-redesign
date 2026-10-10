---
type: epic
title: "Diagnostic Assessment & Applied Verification"
parent: initiative-textcourses
covers: [FR-13, FR-15, FR-16, FR-17, FR-18]
after: [epic-runtime-engine, epic-instruction-delivery]
assignee: ""
risk: medium
---

# Diagnostic Assessment & Applied Verification

## Description

Implements the two complementary evaluation layers of TextCourses: **pure question-based diagnostic testing (`tc-test-me`)** and **hands-on practical project verification (`tc-practicals`)**. Testing evaluates learner mental models without code copy-pasting, logging all misconceptions to `test-ledger.jsonl`. Practicals formulate verifiable project briefs and evaluate deliverables across four objective review lenses in `portfolio/`.

## Outcome

Learners evaluate and reinforce their mental models through targeted diagnostic scenarios, and demonstrate genuine competence by building authentic portfolio artifacts verified against rigorous technical criteria.

## Requirements

- `FR-13`: 100% question-based conceptual diagnostic testing without code copy-pasting into chat.
- `FR-15`: Cumulative boundary rule strictly testing only completed sections.
- `FR-16`: Customizable practical project brief generation with diagnostic-informed weighting based on past misconceptions in `test-ledger.jsonl`.
- `FR-17`: Verifiable deliverable contracts restricted to deterministic artifacts (code, tests, schemas, memos).
- `FR-18`: Multi-Lens Project Review Pass evaluating Functional Completeness, Edge Cases, Architecture & Craft, and Verification Integrity.

## Done when

1. `/tc-test-me` generates diagnostic hinge scenario questions based on completed `notes.md` without leaking upcoming concepts.
2. Learner responses are analyzed, misconceptions categorized (e.g. `CONFUSION_*`), and records appended atomically to `test-ledger.jsonl`.
3. `/tc-practicals` inspects `test-ledger.jsonl` misconception summaries and weights project challenges toward past weak areas.
4. `/tc-practicals` generates `portfolio/project-XX/project-spec.md` with explicit testable deliverables.
5. Evaluating a submitted project workspace produces `portfolio/project-XX/review-report.md` across the 4 lenses and marks the course `completed`.

## Boundaries

The evaluation skills (`skills/tc-test-me/`, `skills/tc-practicals/`). Not lesson delivery (Epic 4).

## References

- prd — `_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md`, sections 4.4, 4.5
- architecture — `_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md`, sections AD-3, AD-5

## Notes

- Decision: Zero code pasting in chat during testing; practical code lives in local portfolio workspaces (2026-10-10).
