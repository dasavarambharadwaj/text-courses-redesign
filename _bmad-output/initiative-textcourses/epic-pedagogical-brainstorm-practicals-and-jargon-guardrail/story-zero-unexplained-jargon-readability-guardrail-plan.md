# Story Plan: Zero-Unexplained-Jargon & Human-First Readability Guardrail

**Story ID**: 4  
**Epic**: `epic-pedagogical-brainstorm-practicals-and-jargon-guardrail`  
**Status**: in-progress  
**Covers**: FR-37  

## Context & Objectives
All text intended for human learners (textbook notes, teaching dialogs, exercise instructions) must be radically accessible, engaging, and clear. Technical gatekeeping and ungrounded jargon are strictly forbidden:
- **No Unexplained Jargon Rule**: Any domain term or technical acronym must either:
  1. Have been thoroughly explained and mastered in an earlier chapter, OR
  2. Be introduced with an explicit, plain-English "Intuitive Mental Model / Everyday Analogy" breakdown box right where it appears.
- **Notes Compiler Enforcement**: `notes_compiler.py` includes a readability and jargon audit (`audit_jargon_and_readability`) verifying that terms appearing in notes are demystified.
- **Teaching Prompt Enforcement**: `teach_engine.py` instructs faculty personas to lead with visceral real-world analogies before formal technical definitions.

## Acceptance Criteria
1. `notes_compiler.py` enforces a jargon and readability auditor that checks for unexplained jargon and demystification sections.
2. `teach_engine.py` embeds strict anti-jargon / analogy-first prompt rules for all faculty personas.
3. Notes generation includes a dedicated `## Jargon Demystified & Everyday Analogies` breakdown for newly introduced terms.
4. Unit tests verify that jargon auditing correctly flags unexplained terms and approves demystified notes.
