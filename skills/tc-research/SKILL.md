---
name: tc-research
description: "Autonomous pre-course deep research engine led by Marie Curie. Executes multi-round web search, universal multi-hat critical reflection, and generates comprehensive research dossiers in research/<slug>/."
---

# `tc-research`: Autonomous Universal Deep Research Engine

`tc-research` is the autonomous pre-course research engine spearheaded by **🔬 Marie Curie (The Empirical Investigator)**. It harvests, stress-tests, and synthesizes authoritative domain knowledge **BEFORE course creation**, ensuring that every curriculum is built upon verified empirical ground truth rather than LLM assumptions.

Research is stage 1 of course authoring: run `/tc-research` first to produce a visible research dossier, which `/tc-create` then ingests to build a personalized course.

---

## Core Invariants

1. **Pre-Course Research Primacy (FR-30)**: Research is conducted **first**, before course creation. Any learner exploring a new domain invokes `/tc-research "<topic>"`.
2. **Universal Multi-Hat Critical Engine (Tree-of-Thought Dialectic)**: Marie maintains a library of 12+ universal critical hats spanning all human knowledge domains (sciences, humanities, business, arts, philosophy, engineering). She dynamically selects the 5 most appropriate hats for the domain:
   - 🎯 **Applied Practitioner**: Real-world execution, practical workflows, field tools, and operational resilience.
   - 🏛️ **Academic / First-Principles Purist**: Foundational axioms, formal proofs, structural laws, and ontological ground truth.
   - 🧗 **Beginner Friction Hunter**: Cognitive stumbling blocks, hidden assumed knowledge, and confusing terminology.
   - 🔬 **Empirical Skeptic & Stress-Tester**: Counter-examples, boundary limits, common myths/misconceptions, and conditions of invalidity.
   - 🌐 **Contemporary Evolution Reviewer**: Modern consensus, recent breakthroughs, state-of-the-art standards, and obsolete dogmas to unlearn.
   - ⚡ **Edge-Case Systems Engineer**: Concurrency hazards, race conditions, memory pressure, and cascading failure modes.
   - 🔄 **Interdisciplinary Weaver**: Cross-domain analogies, systemic connections, and isomorphic principles bridging fields.
   - ⚖️ **Ethical & Systemic Impact Auditor**: Second-order consequences, societal or organizational externalities, and responsible stewardship.
   - 🎨 **Intuitive Metaphorist**: Visceral mental models, relatable physical analogies, and sticky visual intuition.
   - 📜 **Historical Genealogist**: The problem-solving lineage, origins, and historical dilemmas that forced ideas into existence.
   - 📊 **Pragmatic Resource & Trade-off Optimizer**: Pareto principle (80/20 leverage), time-to-mastery, and prioritization.
3. **Tree-of-Thought Search Branches**: Gaps and edge cases surfaced by the chosen hats trigger iterative follow-up search queries to ensure comprehensive domain coverage.
4. **Root-Level Research Substrate (FR-33)**: All research artifacts are written directly to the visible workspace directory `research/<topic-slug>/`:
   - `dossier.md`: Comprehensive master knowledge map, primitives, mental models, and curriculum blueprint.
   - `multi-hats-critique.md` (and `five-hats-critique.md`): Full multi-perspective dialectic review and follow-up branches.
   - `sources.json`: Provenance citations, URLs, scraped snippets, and retrieval timestamps.
   - `digest.json`: Extracted ToC, symbols/APIs, and prerequisite vocabulary terms for downstream compilation.

---

## Conventions

- `{project-root}` is the nearest folder containing `_tc/` or `.tc/`, starting at the current working directory and searching upwards (or `.` if not yet initialized).
- `{skill-root}` is this skill's own directory (e.g. `skills/tc-research`).

## On Activation

Verify workspace initialization: check if `{project-root}/_tc/scripts/scout.py` exists.
- If not found: TextCourses is not initialized in this workspace. Offer to run `/tc-init` first, then re-run this command.

---

## Workflow

### 1. Execute Autonomous Deep Research

Run the deep research engine on target domain or topic:

```bash
# Research a broad topic autonomously (dynamically selects domain-tailored hats)
uv run _tc/scripts/scout.py scout --slug stoic-philosophy --topic "Stoic Philosophy: Epictetus, Seneca, and Marcus Aurelius"

# Research with custom requested critical hats
uv run _tc/scripts/scout.py scout --slug quantum-mechanics --topic "Quantum Mechanics" --hats "academic_purist,intuitive_metaphorist,empirical_skeptic"

# Research with an official documentation URL anchor
uv run _tc/scripts/scout.py scout --slug tokio-async --url https://docs.rs/tokio/latest/tokio/

# List all available hats in the registry
uv run _tc/scripts/scout.py hats
```

### 2. Inspect Generated Research Dossier

Inspect the synthesized domain knowledge in `research/<topic-slug>/`:

```bash
# Read master research dossier
uv run _tc/scripts/scout.py dossier --slug stoic-philosophy

# Read multi-hat critical reflection
uv run _tc/scripts/scout.py critique --slug stoic-philosophy

# Read machine digest (ToC, symbols, vocabulary)
uv run _tc/scripts/scout.py get --slug stoic-philosophy
```

### 3. Pipeline Hand-off to `/tc-create`

Once research is complete in `research/<topic-slug>/`, proceed directly to course creation. `/tc-create` will ingest this existing dossier without re-crawling:

```text
Research complete! Comprehensive dossier compiled in research/<topic-slug>/dossier.md.

Next Action:
Create your personalized course using this research:
  /tc-create "<topic>"
```
