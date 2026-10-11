# Story 1: Zero-Cognitive-Overload Pacing & Centralized Interaction Standards

**Status**: completed  
**Covers**: FR-42, AD-9  
**Prerequisites**: None  

## Context & Objectives
Ensure all TextCourses skills and conversational flows are radically simple and cognitively lightweight for learners of any background (including 10-year-olds):
- Enforce strictly ONE question or menu choice per turn.
- Strip all complex academic jargon and comparative preview tables.
- Expand learner background options to 10 diverse roles (software engineer, product manager, student/researcher, lawyer, doctor, accountant, designer/creative, data analyst, teacher/educator, business executive).
- Support custom free-form domain experience descriptions.
- Condense teacher faculty down to 3 kid-friendly archetypes: Feynman (The Simplifier), Socrates (The Questioner), and Turing (The Builder).
- Show dynamic `(Recommended)` indicators based on prior answers.
- Centralize interaction standards into `_tc/INTERACTION_STANDARDS.md`.

## Implementation Steps
1. Create `_tc/INTERACTION_STANDARDS.md` defining the 5 Cardinal Interaction Rules.
2. Update `_tc/scripts/bootstrapper.py` interactive intake:
   - One question per turn loop.
   - 10 learner roles with custom entry option.
   - Free-form domain experience input.
   - Streamlined 3-teacher persona list.
   - Dynamic recommendation calculations based on prior responses.
   - Final scannable summary with short selection codes before saving.
3. Update `skills/tc-init/SKILL.md` to reference `_tc/INTERACTION_STANDARDS.md`.
4. Verify with automated test suite in `tests/test_beginner_adaptation.py` and `tests/test_faculty_personas.py`.
