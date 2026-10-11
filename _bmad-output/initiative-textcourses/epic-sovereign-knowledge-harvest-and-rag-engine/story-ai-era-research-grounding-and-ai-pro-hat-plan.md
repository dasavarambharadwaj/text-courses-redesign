# Story 3: AI-Era Research Grounding & Dedicated AI-Pro Hat Engine

**Status**: completed  
**Covers**: FR-44, AD-11  
**Prerequisites**: Story 1, Story 2  

## Context & Objectives
Ensure that all deep domain research explicitly analyzes and reflects modern AI-era realities, preventing courses from teaching deprecated idioms or omitting modern AI-assisted workflows:
- Mandate an AI-Era landscape analysis section in all research dossiers (`dossier.md`) and digests (`digest.json`).
- Detail what has changed because of AI (routine boilerplate automation vs. core system invariants).
- Identify AI-adjacent tools, libraries, models, and APIs to include in discussions.
- Document AI hallucination failure modes and adversarial verification guardrails.
- Introduce `ai_pro_strategist` into the Universal Hat Registry in `scout.py`.

## Implementation Steps
1. Add `ai_pro_strategist` critical lens to `CRITICAL_HATS` registry in `_tc/scripts/scout.py`.
2. Add `--ai` CLI flag to `scout.py` / `tc.py research` to automatically activate the AI-Pro Strategist hat.
3. Update `generate_research_dossier()` to include the mandatory Section 5: "AI-Era Evolution & Co-Pilot Landscape Analysis".
4. Update `skills/tc-research/SKILL.md` documenting AI-era research requirements and the AI-Pro hat.
5. Verify with automated tests in `tests/test_five_hat_research.py`.
