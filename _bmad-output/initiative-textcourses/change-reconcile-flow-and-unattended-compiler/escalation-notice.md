# Escalation Notice: Major Sprint Change

**Initiative:** `initiative-textcourses`  
**Change:** `change-reconcile-flow-and-unattended-compiler`  
**Date:** 2026-11-06  
**Scope:** **Major** — fundamental replan  
**Approved proposal:** `change-reconcile-flow-and-unattended-compiler.md`  
**Decision owner:** Product Manager / Solution Architect

---

## Why this is escalated

The approved proposal is a **Major** change because the runtime does not implement the product contract the completed epics claim to deliver:

- **0 of 12** learner-vision points are fully evidenced.
- Epic 12 and its stories are marked `done` while auto mode, source approval, the section-close gate, session scrubbing, and the status dashboard do not exist.
- The topic-only "proceed with open docs" branch returns `state: creating_course` without creating a course.
- Notes compile to a hidden `.tc/notes/` path instead of the visible course notes path.
- The PRD, architecture, UX spec, and companions disagree on `.tc/`, `_tc/`, `research/`, `sources/`, and `plan/sources/`.
- The 326-test suite is green but does not cover the missing behavior; one test asserts the dead end as expected.

## Decision requested

Approve the following before any implementation begins:

1. **Storage contract:** root `_tc/` is the single research, source, course-state, decision, profile, roadmap, and learning-history root. The only visible study material is `courses/<slug>/notes/chapter-XX.md`.
2. **Scope expansion:** the MVP now includes execution modes, interactive source approval, zero-loss conversion coverage, the 4-hat research debate, the mandatory section-close gate, and the generated status dashboard.
3. **Planning rollback:** Epics 2–12 are reopened where their `done` criteria are contradicted; Epic 1 receives path/test updates only.
4. **Public surface:** exactly one exported skill, `tc`; all other capabilities become internal packages under `_tc/skills/`.
5. **Sequencing:** storage contract → public surface/dispatcher → modes/research → conversion/debate → blueprint/section plans → teaching close → dashboard → vision-contract E2E.

## Required receiving lanes

| Lane | Responsibility | Exit condition |
|---|---|---|
| Product Manager / Solution Architect | Accept the storage, MVP, mode, and close-gate contracts; apply PRD/architecture/spec edits described in §4 of the proposal. | Artifacts agree with the canonical contract. |
| Product Owner / `bmad-ticket` | Reopen contradicted epics, add the ten new stories, update dependencies, resequence `tickets.toml`. | Backlog reflects the approved sequencing. |
| Developer agent | Implement the approved stories after the two lanes above complete. | Runtime behavior matches each success criterion. |
| Reviewer | Verify the 12-point contract against runtime evidence and the vision-contract suite. | 13/13 criteria in §5.3 evidenced. |

## Constraints

- No runtime code, tests, skill packages, or tickets were modified by the correction workflow.
- No implementation starts until this notice is accepted and the backlog is resequenced.
- Documentation claims, static badges, and green tests that do not exercise the contract are not acceptance evidence.

## Estimate

15–25 engineer-days for one developer; 3–5 sprints for a small team; roughly 3–4 weeks of calendar impact. Risk is **High** because the storage migration touches every engine and the close gate changes teaching semantics.
