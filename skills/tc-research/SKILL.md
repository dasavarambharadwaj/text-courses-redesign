---
name: tc-research
description: "Autonomous pre-course deep research engine led by Marie Curie. Executes community consensus sourcing, GitHub repo & YouTube transcript harvesting, universal multi-hat reflection, and generates comprehensive research dossiers in research/<slug>/."
---

# `tc-research`: Autonomous Universal Deep Research Engine

`tc-research` is the autonomous pre-course research engine spearheaded by **🔬 Marie Curie (The Empirical Investigator)**. It discovers community consensus, harvests open textbook repositories and landmark lecture transcripts, stress-tests knowledge with critical hats, and synthesizes authoritative domain knowledge **BEFORE course creation**, ensuring that every curriculum is built upon verified empirical ground truth rather than LLM assumptions.

Research is stage 1 of course authoring: run `/tc-research` first to produce a visible research dossier, which `/tc-create` then ingests to build a personalized course.

---

## Core Invariants

1. **Pre-Course Research Primacy (FR-30)**: Research is conducted **first**, before course creation. Any learner exploring a new domain invokes `/tc-research "<topic>"`.
2. **Community Consensus & Gold Standard Sourcing (FR-43.1)**: Marie searches community discussions (Reddit, Hacker News, university syllabi) to identify the 2–3 undisputed gold-standard textbooks, canonical courses, and landmark lectures.
3. **Automated GitHub & Open Textbook Harvesting (FR-43.2)**: For any gold-standard or high-quality course material hosted openly on GitHub, Marie automatically downloads or shallow-clones the repository directly into `research/<slug>/sources/repos/<repo_name>/` and indexes its chapters and markdown files.
4. **YouTube Lecture Transcript Extraction (FR-43.3)**: When landmark university or industry lectures are identified, Marie extracts and cleans the subtitles/transcripts using `harvest-youtube`, saving deduplicated, readable markdown into `research/<slug>/sources/transcripts/`.
5. **Graceful Material Acquisition Gate (FR-43.4)**: If an essential gold-standard book is proprietary or copyrighted and unavailable on GitHub, Marie records its exact title, author, and edition in `research/<slug>/gold-standards.md` with status `[ACQUISITION NEEDED]`. Following `_tc/INTERACTION_STANDARDS.md`, she presents a single, simple question to the learner with clear options:
   - Drop the book file (PDF, EPUB, or markdown) into `research/<slug>/sources/`.
   - Or proceed immediately using open documentation, harvested repos, and lecture transcripts.
6. **Universal Multi-Hat Critical Engine (Tree-of-Thought Dialectic)**: Marie maintains a library of 13 universal critical hats spanning all human knowledge domains (sciences, humanities, business, arts, philosophy, engineering, and artificial intelligence). She dynamically selects domain-tailored critical lenses:
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
   - 🤖 **AI-Pro Strategist & Co-Pilot (FR-44.2)**: AI-era transformation, automated workflows, AI co-pilot prompt/context ergonomics, verification harnesses for LLM output, and modern AI tool integration.
7. **Mandatory AI-Era Research Grounding (FR-44.1)**: Every research dossier explicitly analyzes what has changed in the AI era for the domain:
   - Routine boilerplate and tasks now automated by AI tooling.
   - What new AI-adjacent topics, APIs, models, and workflows should be integrated into discussion and course design.
   - Where AI commonly hallucinates or fails in this field, and the verification instincts every learner must acquire.
8. **Root-Level Research Substrate (FR-33, FR-43.5, FR-44.3)**: All research artifacts are written directly to the visible workspace directory `research/<topic-slug>/`:
   - `gold-standards.md`: Community consensus summary, gold-standard books, status badges (`[HARVESTED]`, `[TRANSCRIPT_EXTRACTED]`, `[ACQUISITION NEEDED]`), and acquisition instructions.
   - `sources/`: Harvested git repositories (`sources/repos/`), lecture transcripts (`sources/transcripts/`), and `sources/sources-index.json`.
   - `dossier.md`: Comprehensive master knowledge map, primitives, mental models, curriculum blueprint, gold-standard literature, and AI-Era landscape analysis.
   - `multi-hats-critique.md` (and `five-hats-critique.md`): Full multi-perspective dialectic review and follow-up branches.
   - `sources.json`: Provenance citations, URLs, scraped snippets, harvested repos, and retrieval timestamps.
   - `digest.json`: Extracted ToC, symbols/APIs, prerequisite vocabulary terms, and AI-era transformation metadata.

---

## Conventions

- `{project-root}` is the nearest folder containing `_tc/` or `.tc/`, starting at the current working directory and searching upwards (or `.` if not yet initialized).
- `{skill-root}` is this skill's own directory (e.g. `skills/tc-research`).

## On Activation

Verify workspace initialization: check if `{project-root}/_tc/scripts/scout.py` exists.
- If not found: TextCourses is not initialized in this workspace. Offer to run `/tc-init` first, then re-run this command.

---

## Workflow

### 1. Mine Community Consensus & Record Gold Standards

Search community discussions (Reddit, Hacker News, course syllabi) for the topic's undisputed best books and landmark lectures. Record the consensus:

```bash
uv run _tc/scripts/scout.py record-consensus \
  --slug rust-systems \
  --topic "Rust Systems Programming" \
  --summary "The Rust community overwhelmingly recommends The Rust Programming Language (TRPL), Programming Rust (Blandy et al.), and Jon Gjengset's Crust of Rust video series." \
  --items-json '[
    {"title": "The Rust Programming Language", "author": "Steve Klabnik & Carol Nichols", "type": "open_book", "status": "harvested", "location": "sources/repos/book"},
    {"title": "Programming Rust (2nd Edition)", "author": "Jim Blandy, Jason Orendorff, Leonora Tindall", "type": "commercial_book", "status": "acquisition_needed", "location": "sources/programming-rust.pdf"},
    {"title": "Crust of Rust: Lifetime Annotations", "author": "Jon Gjengset", "type": "video_lecture", "status": "transcript_extracted", "location": "sources/transcripts/crust-of-rust-lifetimes.md"}
  ]'
```

### 2. Harvest Open GitHub Repositories & Markdown Books

If an open textbook or repository is found on GitHub, clone or download it directly:

```bash
uv run _tc/scripts/scout.py harvest-repo \
  --slug rust-systems \
  --repo rust-lang/book \
  --branch main
```

### 3. Harvest YouTube Lecture Transcripts

Extract clean, timestamped transcripts from landmark lecture videos:

```bash
uv run _tc/scripts/scout.py harvest-youtube \
  --slug rust-systems \
  --url "https://www.youtube.com/watch?v=rAl-9HwD858" \
  --title "Crust of Rust: Lifetime Annotations"
```

### 4. Material Acquisition Gate (If Proprietary Books Exist)

If commercial books were identified and could not be downloaded via GitHub:
1. Marie presents a friendly prompt adhering to `_tc/INTERACTION_STANDARDS.md` (Single-Question Rule, 10-year-old language):
   > "I found that **Programming Rust (2nd Edition)** is the gold-standard book for this topic.
   > 
   > If you own a copy (PDF or EPUB), you can drop it into:
   > `research/rust-systems/sources/`
   > 
   > Would you like to add your book now, or should we build the course using official open docs and video transcripts?"
   > - Option A: "I'll add the book file now, let's wait"
   > - Option B: "(Recommended) Proceed with open documentation and transcripts"

### 5. Execute Autonomous Multi-Hat Deep Research & Synthesis

Run the deep research engine. It automatically indexes `research/<slug>/sources/`, embeds gold standards, runs the critical hats (including the AI-Pro Strategist lens), and writes the complete dossier:

```bash
# Scout documentation, compile multi-source dossier, and activate AI-Pro Strategist hat
uv run _tc/scripts/scout.py scout \
  --slug rust-systems \
  --topic "Rust Systems Programming" \
  --url https://doc.rust-lang.org/book/ \
  --ai

# Alternatively, request explicit hats including AI-Pro
uv run _tc/scripts/scout.py scout \
  --slug rust-systems \
  --topic "Rust Systems Programming" \
  --hats "applied_practitioner,academic_purist,ai_pro"
```

### 6. Inspect Generated Research Dossier

Inspect the synthesized domain knowledge in `research/<topic-slug>/`:

```bash
# Read master research dossier
uv run _tc/scripts/scout.py dossier --slug rust-systems

# Read multi-hat critical reflection
uv run _tc/scripts/scout.py critique --slug rust-systems

# Read machine digest (ToC, symbols, vocabulary)
uv run _tc/scripts/scout.py get --slug rust-systems
```

### 7. Pipeline Hand-off to `/tc-create`

Once research is complete in `research/<topic-slug>/`, proceed directly to course creation. `/tc-create` will ingest this existing dossier without re-crawling:

```text
Research complete! Comprehensive dossier compiled in research/<topic-slug>/dossier.md.

Next Action:
Create your personalized course using this research:
  /tc-create "<topic>"
```
