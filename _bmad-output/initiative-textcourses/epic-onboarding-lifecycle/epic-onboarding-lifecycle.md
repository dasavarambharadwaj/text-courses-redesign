---
type: epic
title: "Workspace Onboarding & Lifecycle Management"
parent: initiative-textcourses
covers: [FR-1, FR-2, FR-3, FR-20, FR-21]
after: [epic-runtime-engine]
assignee: ""
risk: medium
status: done
---

# Workspace Onboarding & Lifecycle Management

## Description

Delivers the user intake, style selection, workspace bootstrapping, active state scanning, course redirection, and safe schema migration skills (`tc-init`, `tc-redirect-course`, `tc-migrate`). This epic ensures frictionless onboarding into a sovereign workspace and non-destructive evolution of living courses.

## Outcome

Learners initialize new workspaces in under 60 seconds with personalized style profiles, easily scan next actions, and safely update or migrate course schemas without risking loss of completed notes.

## Requirements

- `FR-1`: Structured intake capturing identity, role taxonomy, domain experience, and density preferences into `plan/preferences.md`.
- `FR-2`: Interactive style preview and evolvable profile picker (Direct Technical, Analogy, Code-First, Math).
- `FR-3`: Workspace state scanner inspecting manifests and recommending exact next action commands.
- `FR-20`: Completed lesson immutability with non-destructive deprecation markers.
- `FR-21`: Safe schema migration engine with transparent dry-run plans and mandatory typed user consent.

## Done when

1. Running `/tc-init` in an empty directory bootstraps `.tc/`, `plan/`, `courses/`, deploys `_tc/scripts/`, and generates `plan/preferences.md`.
2. Running `/tc-init` in an existing workspace scans manifests and prints current progress and recommended next command.
3. `/tc-redirect-course` detects newly added source files via `hash_tracker.py`, checks impact on unfinished chapters, and prepends deprecation headers to completed notes without rewriting content.
4. `/tc-migrate` previews `migration-plan.md` and strictly requires explicit user confirmation before modifying any files.

## Boundaries

The onboarding and lifecycle skill packages (`skills/tc-init/`, `skills/tc-redirect-course/`, `skills/tc-migrate/`). Not curriculum creation (Epic 3) or teaching loops (Epic 4).

## References

- prd — `_bmad-output/initiative-textcourses/prd-textcourses/prd-textcourses.md`, sections 4.1, 4.6
- architecture — `_bmad-output/initiative-textcourses/architecture-textcourses/architecture-textcourses.md`, sections AD-6, AD-7

## Notes

- Decision: Completed notes are bitwise immutable; deprecations are non-destructive header markers only (2026-10-10).
