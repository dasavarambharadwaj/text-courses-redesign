---
type: epic
title: "Conversational Instruction & Notes Compilation"
parent: initiative-textcourses
covers: [FR-9, FR-10, FR-11, FR-12]
after: [epic-runtime-engine, epic-curriculum-creation]
assignee: ""
risk: medium
status: done
---

# Conversational Instruction & Notes Compilation

## Description

Delivers the core teaching experience through `tc-teach`. It provides conversational single-concept deep dives according to the learner's chosen style profile, maintains live checkmark progress in `lesson-plan.md`, closes every turn with the standardized Next-Action Fork, and automatically distills discussions into a permanent `notes.md` textbook upon section completion without breaking flow.

## Outcome

Learners experience high-velocity, intellectually rewarding instruction bounded to single concepts, advancing seamlessly through lessons while accumulating an authoritative, personalized reference textbook on their disk.

## Requirements

- `FR-9`: Substantial single-concept delivery strictly bounded to one topic per turn with bold mechanics, formatted code/tables, and worked-example/fatal-mistake pairs.
- `FR-10`: Standardized 4-option Next-Action Fork concluding every instructional turn (`[1] Next Topic`, `[2] Test Me`, `[3] Re-explain`, `[4] Custom`).
- `FR-11`: Automated flow-preserving background distillation of `notes.md` upon section completion with 3-bullet recap.
- `FR-12`: Session hygiene with live checkmarks in `lesson-plan.md` enabling interruption recovery.

## Done when

1. `/tc-teach` delivers conceptually dense explanations matching the active Style Profile from `plan/preferences.md`.
2. Selecting `[1]` in the Next-Action Fork immediately ticks the concept in `lesson-plan.md` and proceeds to the next concept.
3. Completing the final concept in a section automatically compiles and writes `notes.md` to disk, updates `course.toml` to `status: review`, and presents the next section fork.
4. Interrupting a session mid-section and restarting `/tc-teach` seamlessly resumes from the last unchecked concept.
5. Average turn token consumption remains under 4,000 tokens via `context.py` manifest enforcement.

## Boundaries

The teaching skill package (`skills/tc-teach/`). Not diagnostic testing or project reviews (Epic 5).

## References

- prd — `_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md`, section 4.3
- architecture — `_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md`, sections AD-3, AD-5

## Notes

- Decision: Automated background notes compilation preserves flow state without blocking approval bureaucracy (2026-10-10).
