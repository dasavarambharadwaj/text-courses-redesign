---
type: epic
title: "Autonomous 5-Hat Research, Triad Dialectic & Dual-Register Knowledge Synthesis"
parent: initiative-textcourses
covers: [FR-30, FR-31, FR-32, FR-33]
after: [epic-curriculum-creation, epic-instruction-delivery, epic-faculty-roadmap-memlog]
assignee: ""
risk: high
status: done
---

# Epic 7: Autonomous 5-Hat Research, Triad Dialectic & Dual-Register Knowledge Synthesis

## Overview
Epic 7 elevates TextCourses into a world-class autonomous research and knowledge engineering engine:
1. **Autonomous 5-Hat Deep Research Engine (`tc-research` / `scout.py`)**: Pre-course deep research spearheaded by 🔬 Marie Curie, searching the web, synthesizing authoritative documentation, and stress-testing findings through 5 critical hats (Industry Practitioner, Academic Purist, Beginner Friction Hunter, Edge-Case Systems Engineer, Modern Ecosystem Reviewer) to produce comprehensive dossiers in `research/<topic-slug>/`.
2. **Adversarial Triad Consensus Dialectic (`tc-create` / `course_builder.py`)**: Genuine adversarial debate where Daedalus, Marie, and Hypatia debate chapter structure, verify facts via live online search, challenge cognitive leaps, and achieve strict consensus before any course files are committed to disk. Daedalus personalizes curriculum to the learner's profile, filling any gaps left by the broad research.
3. **Dual-Register Linguistic Separation (Human-First Notes vs AI-First Memlog)**: Notes in `courses/<slug>/notes/chapter-XX.md` are written strictly for human learners in clear, accessible, intuitive English with clear analogies and faculty attribution. Memlog in `courses/<slug>/memlog.md` and `profile/memlog.md` is formatted in ultra-dense, token-minimal notation for AI models.
4. **Root-Level Research Substrate & Workspace Transparency**: Establishes visible `research/` at workspace root and automatically deploys `WORKSPACE_GUIDE.md` / `README.md` orienting learners to their complete filesystem layout.

## Requirements Covered
- `FR-30`: Autonomous 5-Hat Deep Research Engine (`tc-research` / `scout.py`)
- `FR-31`: Adversarial Triad Consensus Dialectic with Live Fact-Checking (`tc-create`)
- `FR-32`: Human-First Textbook Notes vs AI-First Token-Minimal Memlog Engine
- `FR-33`: Root-Level Research Substrate & Workspace Transparency

## Sliced Stories
1. `story-root-level-research-substrate-and-workspace-transparency`: Scaffold visible `research/` and auto-deploy `WORKSPACE_GUIDE.md` on bootstrap.
2. `story-autonomous-five-hat-deep-research-engine`: Implement 5-hat Tree-of-Thought autonomous research, multi-round search, and `research/<slug>/` dossiers in `scout.py` and `skills/tc-research/`.
3. `story-adversarial-triad-consensus-dialectic-with-live-fact-checking`: Implement multi-round adversarial consensus with live web search fact-checking and gap coverage in `course_builder.py` and `skills/tc-create/`.
4. `story-human-first-notes-and-token-minimal-ai-memlog-engine`: Implement dual-register writing (human-first notes in `notes_compiler.py`, token-minimal AI memlog in `memlog.py` / `teach_engine.py` / `diagnostic_tester.py`), closing the conversation tracing loop.
