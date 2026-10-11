# Story 2: Autonomous Multi-Source Deep Harvester & Community Consensus Sourcing

**Status**: completed  
**Covers**: FR-43, AD-10  
**Prerequisites**: Story 1  

## Context & Objectives
Empower the research engine led by **🔬 Marie Curie** to autonomously acquire high-quality, authoritative courseware and textbooks from multiple channels prior to course creation:
- Mine community consensus discussions (Reddit, Hacker News, university reading lists) for the 2–3 undisputed gold standards.
- Automatically clone or download open GitHub courseware and markdown textbooks into `research/<slug>/sources/repos/<repo_name>/`.
- Extract and clean timestamped lecture transcripts from landmark YouTube videos via `harvest-youtube` into `research/<slug>/sources/transcripts/`.
- Provide a graceful acquisition gate for commercial or proprietary textbooks in `research/<slug>/gold-standards.md`.
- Compile structured multi-source manifest in `research/<slug>/sources/sources-index.json`.

## Implementation Steps
1. Create `_tc/scripts/harvester.py` with CLI subcommands:
   - `record-consensus`: records community consensus into `gold-standards.md` with status badges.
   - `harvest-repo`: clones/downloads GitHub repositories and indexes markdown files.
   - `harvest-youtube`: extracts, deduplicates, and cleans WebVTT subtitles into readable transcript markdown.
   - `index-sources`: scans `research/<slug>/sources/` and compiles `sources-index.json`.
2. Wire `harvester.py` into unified dispatcher `tc.py` (`tc harvest ...`).
3. Update `_tc/scripts/scout.py` to invoke harvester routines and integrate multi-source evidence into `dossier.md` and `digest.json`.
4. Update `skills/tc-research/SKILL.md` to document harvesting workflows and commands.
5. Verify with automated tests in `tests/test_harvester.py`.
