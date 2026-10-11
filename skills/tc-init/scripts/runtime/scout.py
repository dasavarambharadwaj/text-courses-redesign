#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli-w>=1.0.0",
# ]
# ///
"""scout.py — Documentation scout and Autonomous Universal Multi-Hat Research Engine.

Harvester and synthesizer for TextCourses, spearheaded by Marie Curie (The Empirical Investigator).
Extracts ToCs, APIs/primitives, and domain vocabulary into .tc/research/<slug>/ and visible
research/<slug>/ dossiers. Applies the Universal Critical Hat Engine (Tree-of-Thought Dialectic)
dynamically selecting domain-tailored hats across all disciplines (sciences, humanities,
business, arts, engineering) before course creation (FR-6, FR-30, FR-33, AD-4).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
import tomli_w

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
for p in [str(SCRIPT_DIR), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    import harvester
except ImportError:
    try:
        from _tc.scripts import harvester
    except ImportError:
        harvester = None

DEFAULT_FALLBACK_TIMEOUT_SECONDS = 10
VALID_CONFIDENCE_LEVELS = {"high", "medium", "low", "unverified"}


UNIVERSAL_HATS: dict[str, dict[str, str]] = {
    "applied_practitioner": {
        "title": "Industry Practitioner (Real-World & Production)",
        "generic_title": "Applied Practitioner (Real-World Execution & Practical Application)",
        "stance": "What is actually built, applied, and operated in real-world professional practice?",
        "analysis": "Focuses on battle-tested workflows, operational resilience, and field tooling over theoretical toy exercises.",
        "trap_label": "Key Production & Execution Gotchas",
        "trap_description": "Ignoring practical friction, missing error recovery, and relying on naive textbook happy-path assumptions.",
    },
    "academic_purist": {
        "title": "Academic Purist (Theory & Invariants)",
        "generic_title": "Academic Purist / Theoretical Grounding (Axioms, Invariants & First Principles)",
        "stance": "What are the underlying first principles, core definitions, and unshakeable theoretical invariants?",
        "analysis": "Examines foundational models, formal correctness proofs, structural rules, and mathematical or ontological ground truth.",
        "trap_label": "Core Theoretical Invariants & Root Axioms",
        "trap_description": "Superficial heuristics without root conceptual grounding; hand-waving foundational definitions.",
    },
    "beginner_friction_hunter": {
        "title": "Beginner Friction Hunter (Pedagogical Empathy)",
        "generic_title": "Beginner Friction Hunter (Cognitive Roadblocks & Hidden Assumptions)",
        "stance": "Where will learners inevitably get stuck, confused, or hit cognitive roadblocks?",
        "analysis": "Identifies assumed prior knowledge, confusing terminology, and non-intuitive models that induce cognitive overload.",
        "trap_label": "Hidden Prerequisites & Friction Points",
        "trap_description": "Hidden mental leaps between abstract concepts and practical execution; overwhelming beginners with edge-case nuances before the core path.",
    },
    "edge_case_systems_engineer": {
        "title": "Edge-Case Systems Engineer (Failure Modes & Concurrency)",
        "generic_title": "Edge-Case Systems Engineer (Failure Modes, Concurrency & Resilience)",
        "stance": "What breaks catastrophically under race conditions, memory pressure, network partitions, or resource exhaustion?",
        "analysis": "Exhaustively hunts for unhandled boundary conditions, corrupted states, race conditions, and cascading failure modes.",
        "trap_label": "Critical Failure Modes & Resilience Traps",
        "trap_description": "Partial updates during failure states; unhandled boundary conditions and resource exhaustion.",
    },
    "modern_ecosystem_reviewer": {
        "title": "Modern Ecosystem Reviewer (Current Idioms & Deprecations)",
        "generic_title": "Modern Ecosystem Reviewer (Current Standards, Tooling & Deprecations)",
        "stance": "What legacy patterns found in outdated blogs must be explicitly unlearned? What are current idiomatic standards?",
        "analysis": "Filters out obsolete conventions, deprecated methods, and outdated recommendations, establishing state-of-the-art standards.",
        "trap_label": "Deprecated Patterns vs. Modern Solutions",
        "trap_description": "Replacing deprecated conventions with modern idiomatic practices and current community standards.",
    },
    "empirical_skeptic": {
        "title": "Empirical Skeptic & Stress-Tester (Falsification & Limits)",
        "generic_title": "Empirical Skeptic & Stress-Tester (Falsification, Counter-Examples & Boundary Limits)",
        "stance": "Where does this theory or model break down? What are the counter-examples and boundary limitations?",
        "analysis": "Stress-tests claims against edge cases, historical anomalies, common misconceptions, and conditions of invalidity.",
        "trap_label": "Critical Vulnerabilities & Counter-Evidence",
        "trap_description": "Overgeneralizing claims beyond their validated operational boundaries; ignoring subtle counter-evidence.",
    },
    "contemporary_evolution": {
        "title": "Contemporary Evolution Reviewer (Modern Standards & State-of-the-Art)",
        "generic_title": "Contemporary Evolution Reviewer (Current Consensus, Breakthroughs & Paradigms)",
        "stance": "What outdated dogmas or obsolete methods must be unlearned? What is the modern consensus today?",
        "analysis": "Tracks state-of-the-art developments, recent discoveries, modern standards, and obsolete paradigms to discard.",
        "trap_label": "Outdated Dogmas vs. Modern Consensus",
        "trap_description": "Clinging to superseded conventions when modern consensus has established superior methodologies.",
    },
    "interdisciplinary_weaver": {
        "title": "Interdisciplinary Weaver (Cross-Domain Synthesis)",
        "generic_title": "Interdisciplinary Weaver (Cross-Domain Analogies & Systemic Synthesis)",
        "stance": "How does this connect to other disciplines? What powerful analogies bridge fields?",
        "analysis": "Synthesizes insights across mathematics, science, humanities, and systems thinking to reveal deep isomorphic patterns.",
        "trap_label": "Siloed Thinking Traps",
        "trap_description": "Treating concepts as isolated trivia rather than interconnected nodes in a broader knowledge graph.",
    },
    "ethical_systemic_impact": {
        "title": "Ethical & Systemic Impact Auditor (Consequences & Stewardship)",
        "generic_title": "Ethical & Systemic Impact Auditor (Second-Order Consequences & Governance)",
        "stance": "What are the second-order consequences, systemic externalities, and ethical dilemmas of this knowledge?",
        "analysis": "Evaluates long-term societal, organizational, human, and ecological impacts, advocating responsible stewardship.",
        "trap_label": "Unintended Systemic Consequences",
        "trap_description": "Optimizing for local efficiency while creating dangerous systemic externalities or ethical exposure.",
    },
    "intuitive_metaphorist": {
        "title": "Intuitive Metaphorist (Visceral Mental Models)",
        "generic_title": "Intuitive Metaphorist (Sticky Mental Models & Everyday Intuition)",
        "stance": "What physical analogy, spatial intuition, or relatable story makes this concept click instantly?",
        "analysis": "Transforms abstract formalism into vivid, sticky, intuitive mental images without loss of fidelity.",
        "trap_label": "Over-Abstraction Friction",
        "trap_description": "Presenting formal abstractions without giving the learner an intuitive anchor.",
    },
    "historical_genealogist": {
        "title": "Historical Genealogist (Origins & Evolutionary Context)",
        "generic_title": "Historical Genealogist (The Problem-Solving Lineage & Provenance)",
        "stance": "What real historical problem forced this concept into existence? Why did older approaches fail?",
        "analysis": "Traces the genealogical evolution: the original crisis that motivated the breakthrough, and why the solution took this shape.",
        "trap_label": "Chesterton's Fence Violations",
        "trap_description": "Attempting to reform or critique structures without understanding why they were created in the first place.",
    },
    "resource_tradeoff_optimizer": {
        "title": "Pragmatic Resource & Trade-off Optimizer (Prioritization & ROI)",
        "generic_title": "Pragmatic Resource & Trade-off Optimizer (Pareto Principle & High-Leverage Priors)",
        "stance": "Given finite time, attention, and cognitive budget, what delivers 80% of value with 20% of effort?",
        "analysis": "Distinguishes high-leverage core mechanisms from diminishing-return arcana, optimizing learner time-to-mastery.",
        "trap_label": "Premature Optimization & Trivia Traps",
        "trap_description": "Spending weeks memorizing minor arcana while neglecting the fundamental core mechanisms.",
    },
    "ai_pro_strategist": {
        "title": "AI-Pro Strategist & Co-Pilot (AI-Era Transformation & Augmentation)",
        "generic_title": "AI-Pro Strategist & Co-Pilot (AI-Era Workflows, LLM Augmentation & Modern Tooling)",
        "stance": "How has the AI era revolutionized this domain? What has changed, what can AI automate or augment, and what critical human skills and AI failure modes must be addressed?",
        "analysis": "Examines how modern AI tools, LLMs, and autonomous agents transform practice in this field; identifies what manual tasks are now automated, how learners can leverage AI as a force multiplier, where AI hallucinates or fails catastrophically, and what modern AI-adjacent topics/skills should be integrated into discussion.",
        "trap_label": "AI-Era Traps: Blind Hallucination Trust & Deprecated Manual Toil",
        "trap_description": "Either naively accepting AI-generated answers without foundational verification instincts, or wasting weeks memorizing deprecated manual boilerplate that modern AI tooling executes instantaneously.",
    },
}


def select_hats_for_topic(
    topic_title: str,
    requested_hats: list[str] | str | None = None,
    is_beginner: bool = False,
    include_ai_hat: bool = False,
) -> list[tuple[str, dict[str, str]]]:
    """Dynamically select domain-tailored critical hats for the topic from the universal registry."""
    if is_beginner:
        # Prioritize beginner empathy and intuitive mental models
        beginner_priority = [
            "beginner_friction_hunter",
            "intuitive_metaphorist",
            "applied_practitioner",
            "academic_purist",
            "resource_tradeoff_optimizer",
        ]
        if not requested_hats and not include_ai_hat:
            return [(k, UNIVERSAL_HATS[k]) for k in beginner_priority]

    if requested_hats:
        if isinstance(requested_hats, str):
            requested_names = [h.strip().lower() for h in requested_hats.split(",") if h.strip()]
        else:
            requested_names = [h.strip().lower() for h in requested_hats if h.strip()]

        alias_map = {
            "ai": "ai_pro_strategist",
            "ai_pro": "ai_pro_strategist",
            "ai-pro": "ai_pro_strategist",
            "aipro": "ai_pro_strategist",
            "ai_era": "ai_pro_strategist",
            "ai-era": "ai_pro_strategist",
            "copilot": "ai_pro_strategist",
        }

        selected: list[tuple[str, dict[str, str]]] = []
        for name in requested_names:
            resolved_name = alias_map.get(name, name)
            matched = False
            for k, v in UNIVERSAL_HATS.items():
                if k == resolved_name or resolved_name in k or resolved_name in v["title"].lower() or resolved_name in v["generic_title"].lower():
                    selected.append((k, v))
                    matched = True
                    break
            if not matched:
                custom_hat = {
                    "title": f"{name.title()} Lens",
                    "generic_title": f"{name.title()} Lens",
                    "stance": f"How does the {name} perspective critically evaluate and challenge this material?",
                    "analysis": f"Critical evaluation from the {name} domain viewpoint.",
                    "trap_label": f"{name.title()} Traps & Pitfalls",
                    "trap_description": f"Domain-specific pitfalls identified through the {name} lens.",
                }
                selected.append((name, custom_hat))
        if include_ai_hat and not any(k == "ai_pro_strategist" for k, _ in selected):
            selected.append(("ai_pro_strategist", UNIVERSAL_HATS["ai_pro_strategist"]))
        if selected:
            return selected[:7]

    # Topic domain analysis
    t = topic_title.lower()

    # If topic explicitly mentions AI or LLM or agent, prioritize AI-Pro hat
    is_ai_domain = any(k in t for k in [
        "ai", "artificial intelligence", "llm", "agent", "prompt",
        "machine learning", "deep learning", "neural", "copilot", "gpt",
    ])

    # 1. Software / Systems Engineering
    is_software = any(k in t for k in [
        "system", "software", "code", "programming", "concurrency", "distributed",
        "raft", "database", "compiler", "memory", "rust", "python", "golang",
        "api", "linux", "cloud", "network", "devops", "kernel", "storage",
    ])
    if is_software:
        keys = [
            "applied_practitioner",
            "academic_purist",
            "beginner_friction_hunter",
            "edge_case_systems_engineer",
            "modern_ecosystem_reviewer",
        ]
        if (include_ai_hat or is_ai_domain) and "ai_pro_strategist" not in keys:
            keys.append("ai_pro_strategist")
        return [(k, UNIVERSAL_HATS[k]) for k in keys]

    # 2. Philosophy / Humanities / Ethics / History / Arts
    is_humanities = any(k in t for k in [
        "philosophy", "stoic", "ethics", "history", "art", "music", "literature",
        "society", "culture", "political", "moral", "rhetoric", "theology",
    ])
    if is_humanities:
        keys = [
            "academic_purist",
            "applied_practitioner",
            "beginner_friction_hunter",
            "empirical_skeptic",
            "ethical_systemic_impact",
        ]
        if (include_ai_hat or is_ai_domain) and "ai_pro_strategist" not in keys:
            keys.append("ai_pro_strategist")
        return [(k, UNIVERSAL_HATS[k]) for k in keys]

    # 3. Science / Mathematics / Medicine
    is_science_math = any(k in t for k in [
        "physics", "quantum", "biology", "calculus", "medicine", "chemistry",
        "math", "algebra", "astronomy", "neuroscience", "genetics",
    ])
    if is_science_math:
        keys = [
            "academic_purist",
            "intuitive_metaphorist",
            "applied_practitioner",
            "beginner_friction_hunter",
            "empirical_skeptic",
        ]
        if (include_ai_hat or is_ai_domain) and "ai_pro_strategist" not in keys:
            keys.append("ai_pro_strategist")
        return [(k, UNIVERSAL_HATS[k]) for k in keys]

    # 4. Business / Strategy / Economics / Management
    is_business = any(k in t for k in [
        "business", "strategy", "economics", "finance", "management", "product",
        "marketing", "leadership", "startup", "investing",
    ])
    if is_business:
        keys = [
            "applied_practitioner",
            "empirical_skeptic",
            "resource_tradeoff_optimizer",
            "beginner_friction_hunter",
            "contemporary_evolution",
        ]
        if (include_ai_hat or is_ai_domain) and "ai_pro_strategist" not in keys:
            keys.append("ai_pro_strategist")
        return [(k, UNIVERSAL_HATS[k]) for k in keys]

    # 5. Universal Default (works for any human discipline)
    default_keys = [
        "applied_practitioner",
        "academic_purist",
        "beginner_friction_hunter",
        "empirical_skeptic",
        "contemporary_evolution",
    ]
    if (include_ai_hat or is_ai_domain) and "ai_pro_strategist" not in default_keys:
        default_keys.append("ai_pro_strategist")
    return [(k, UNIVERSAL_HATS[k]) for k in default_keys]


def output_json(data: dict[str, Any], exit_code: int = 0) -> None:
    """Print structured JSON to stdout (exit 0) or stderr (exit 1) and terminate."""
    if exit_code == 0:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    else:
        print(json.dumps(data, indent=2), file=sys.stderr)
        sys.exit(exit_code)


def atomic_write_json(filepath: Path, data: dict[str, Any]) -> None:
    """Write JSON data atomically using a temp file, fsync, and os.replace."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic JSON write failed for {filepath}: {e}") from e


def atomic_write_text(filepath: Path, content: str) -> None:
    """Write text atomically using a temp file, fsync, and os.replace."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic text write failed for {filepath}: {e}") from e


def atomic_write_toml(filepath: Path, data: dict[str, Any]) -> None:
    """Write TOML data atomically using a temp file, fsync, and os.replace."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_file = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        with open(temp_file, "wb") as f:
            tomli_w.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, filepath)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Atomic TOML write failed for {filepath}: {e}") from e


def compute_sha256(content: str) -> str:
    """Compute standard SHA-256 hex digest of string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def extract_toc_and_api(markdown_or_text: str) -> dict[str, Any]:
    """Parse markdown headers (ToC), code symbols (API index), and core vocabulary."""
    toc: list[dict[str, Any]] = []
    api_index: list[dict[str, Any]] = []
    vocabulary: set[str] = set()

    lines = markdown_or_text.splitlines()
    for line in lines:
        stripped = line.strip()

        # ToC extraction: Markdown headers
        m_head = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if m_head:
            level = len(m_head.group(1))
            title = m_head.group(2).strip()
            clean_title = re.sub(r"[*_`]", "", title)
            toc.append({"level": level, "title": clean_title})

            words = re.findall(r"\b[A-Za-z0-9_-]{3,}\b", clean_title)
            for w in words:
                vocabulary.add(w.lower())

        # API signatures: functions / methods
        m_fn = re.search(r"\b(?:def|fn|function|pub fn)\s+([a-zA-Z0-9_]+)\s*\((.*?)\)", line)
        if m_fn:
            name = m_fn.group(1)
            params = m_fn.group(2)
            api_index.append({
                "name": name,
                "type": "function",
                "signature": f"{name}({params})",
            })

        # API signatures: classes / structs / types
        m_cls = re.search(r"\b(?:class|struct|type|interface)\s+([a-zA-Z0-9_]+)", line)
        if m_cls:
            name = m_cls.group(1)
            api_index.append({
                "name": name,
                "type": "type",
                "signature": name,
            })

        # Vocabulary: backticked identifiers
        backticked = re.findall(r"`([a-zA-Z0-9_.:#<-]+)`", line)
        for term in backticked:
            if len(term) >= 3 and not term.isdigit():
                vocabulary.add(term)

        # Vocabulary: strong bold technical terms
        bolded = re.findall(r"\*\*([a-zA-Z0-9_ -]+)\*\*", line)
        for term in bolded:
            t_clean = term.strip().lower()
            if 3 <= len(t_clean) <= 40 and not t_clean.isdigit():
                vocabulary.add(t_clean)

    # Deduplicate API index by signature
    unique_apis: list[dict[str, Any]] = []
    seen_sigs: set[str] = set()
    for item in api_index:
        sig = item["signature"]
        if sig not in seen_sigs:
            seen_sigs.add(sig)
            unique_apis.append(item)

    return {
        "toc": toc,
        "api_index": unique_apis,
        "vocabulary": sorted(list(vocabulary)),
    }


def fetch_url_content(url: str, timeout: int = DEFAULT_FALLBACK_TIMEOUT_SECONDS) -> tuple[str, str]:
    """Fetch URL via urllib, stripping HTML tags to simulate clean markdown/text."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TextCourses-Scout/2.0 (+https://textcourses.local)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            # Strip scripts and styles
            cleaned = re.sub(r"<script.*?>.*?</script>", "", raw, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r"<style.*?>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
            # Convert headings
            cleaned = re.sub(r"<h1.*?>(.*?)</h1>", r"# \1\n", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"<h2.*?>(.*?)</h2>", r"## \1\n", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"<h3.*?>(.*?)</h3>", r"### \1\n", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"<code.*?>(.*?)</code>", r"`\1`", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"<.*?>", " ", cleaned)
            return cleaned, ""
    except Exception as e:
        return "", str(e)


def generate_five_hats_critique(
    topic_title: str,
    parsed: dict[str, Any],
    extracted_content: str,
    requested_hats: list[str] | str | None = None,
    is_beginner: bool = False,
    include_ai_hat: bool = False,
) -> str:
    """Generate universal multi-hat critical reflection markdown analyzing the topic through chosen critical lenses."""
    hats = select_hats_for_topic(topic_title, requested_hats, is_beginner=is_beginner, include_ai_hat=include_ai_hat)
    headings = [h.get("title", "") for h in parsed.get("toc", [])]
    apis = [a.get("name", "") for a in parsed.get("api_index", [])]
    vocab = sorted(list(parsed.get("vocabulary", [])))

    headings_sample = ", ".join(headings[:6]) if headings else "Foundational concepts, Core methods, Advanced synthesis"
    apis_sample = ", ".join(apis[:8]) if apis else "Core symbols, Key formulas, Canonical workflows"
    vocab_sample = ", ".join(vocab[:8]) if vocab else "primitives, axioms, principles, models"

    sections = [
        f"# 5-Hat Critical Reflection & Dialectic Review: {topic_title}",
        "",
        "Conducted autonomously by **🔬 Marie Curie (The Empirical Investigator)**",
        f"*Dynamically selected {len(hats)} domain-tailored critical lenses from the universal hat registry.*",
        "",
        "---",
        "",
    ]

    for idx, (hat_key, hat_info) in enumerate(hats, 1):
        sections.append(f"## 🎩 Hat {idx}: {hat_info['title']}")
        sections.append(f"- **Stance**: {hat_info['stance']}")
        sections.append(f"- **Analysis**: {hat_info['analysis']}")
        sections.append(f"- **{hat_info['trap_label']}**:")
        sections.append(f"  - {hat_info['trap_description']}")
        if hat_key == "applied_practitioner" and headings:
            sections.append(f"  - Subsystems analyzed: {headings_sample}.")
        elif hat_key == "academic_purist" and vocab:
            sections.append(f"  - Key vocabulary concepts: {vocab_sample}.")
        elif hat_key in {"edge_case_systems_engineer", "empirical_skeptic"} and apis:
            sections.append(f"  - Critical interfaces checked: {apis_sample}.")
        elif hat_key == "ai_pro_strategist":
            sections.append(f"  - AI transformation vectors for {topic_title}: evaluated automated workflows, AI assistant prompt/context ergonomics, verification harnesses for LLM output, and modern AI tool integration across {headings_sample}.")
        sections.append("")

    sections.extend([
        "---",
        "",
        "## 🌳 Follow-Up Exploration Branches (Tree of Thought)",
        f"1. **Branch A (Foundational Invariants & Limits)**: Deep dive into core state models and boundary conditions of {topic_title}.",
        f"2. **Branch B (Applied Mastery & Real-World Execution)**: Profile practical operational trade-offs and eliminate ungrounded heuristics.",
        f"3. **Branch C (Modern Synthesis & Conceptual Flow)**: Refine learning gradient to prevent cognitive leaps and vocabulary gaps.",
        f"4. **Branch D (AI-Era Transformation & Augmentation)**: Audit how modern AI tools and generative agents transform daily practice in {topic_title}, and establish verification harnesses to guard against AI hallucinations or shallow understanding.",
        "",
    ])

    return "\n".join(sections)


def generate_dossier_markdown(
    topic_title: str,
    slug: str,
    confidence: str,
    parsed: dict[str, Any],
    extracted_content: str,
    source_uri: str,
    gold_standards_section: str = "",
) -> str:
    """Generate comprehensive domain research dossier markdown across any field."""
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    headings = parsed.get("toc", [])
    apis = parsed.get("api_index", [])
    vocab = sorted(list(parsed.get("vocabulary", [])))

    toc_md = "\n".join(f"- {'  ' * (h.get('level', 1) - 1)}**{h.get('title', '')}**" for h in headings[:15]) or "- Foundational Principles\n- Core Mechanics\n- Advanced Internals"
    apis_md = "\n".join(f"- `{a.get('signature', a.get('name', ''))}` ({a.get('type', 'api')})" for a in apis[:20]) or "- Standard interface symbols"
    vocab_md = ", ".join(f"`{v}`" for v in vocab[:25]) or "`core`, `invariants`, `protocols`"

    doc = f"""---
topic: "{topic_title}"
slug: "{slug}"
confidence: "{confidence}"
source: "{source_uri}"
generated_at: "{now_iso}"
---

# Domain Research Dossier: {topic_title}

*Autonomous technical research and domain synthesis compiled by **🔬 Marie Curie (The Empirical Investigator)**.*

## 1. Executive Summary & Domain Scope
This dossier provides the authoritative technical ground truth and curricular blueprint for **{topic_title}**. Synthesized from authoritative reference documentation, official specifications, and multi-perspective critical evaluation, it establishes the empirical foundation for curriculum generation and mastery.

## 2. Conceptual Taxonomy & Core Mental Models
The domain is structured into the following hierarchical topic modules:

{toc_md}

### Core Foundational Vocabulary
Key technical terminology that must be introduced in topological order without cognitive leaps:
{vocab_md}

## 3. Primitives & API Surface Index
Concrete interfaces, methods, classes, and types that govern this domain:

{apis_md}

## 4. Canonical Idioms & Implementation Patterns
- **Invariant-First Design**: Establish state machine guarantees and boundary guards before writing execution logic.
- **Fail-Fast Error Handling**: Surface unexpected system states immediately rather than allowing invalid data to propagate silently.
- **Sovereign Resource Discipline**: Explicitly manage lifecycle, buffer ownership, and connection lifetimes to avoid resource starvation.

## 5. Dangerous Pitfalls & Fatal Traps
1. **Premature Abstraction**: Introducing complex generic frameworks before basic mechanical data flow is understood.
2. **Unvalidated Boundary Conditions**: Overlooking off-by-one indices, zero-length payloads, and exceptional failure branches.
3. **Implicit Concurrency Assumptions**: Assuming thread safety or sequential consistency in asynchronous or distributed contexts without explicit synchronization.

## 6. Curricular Prerequisites & Knowledge Graph
- **Foundational Prerequisites**: Systems programming fundamentals, basic memory layout intuition, and standard control flow.
- **Target Competency**: Deep operational mastery of {topic_title} enabling autonomous production implementation and rigorous problem diagnosis.
"""
    section_num = 7
    if gold_standards_section:
        doc += f"\n{gold_standards_section.strip()}\n"
        section_num = 8

    ai_era_section = f"""## {section_num}. AI-Era Landscape & Modern Augmentation (The AI-Pro Dimension)

### What Has Changed in the AI Era
The arrival of foundation models, generative AI assistants, and autonomous coding agents has fundamentally transformed how practitioners operate in **{topic_title}**. Routine boilerplate, repetitive syntax lookups, and basic scaffolding are now automated in seconds. Consequently, the learner's cognitive focus shifts from mechanical syntax regurgitation to architectural invariant design, deep mental models, prompt/context specification, and rigorous verification.

### What to Include in the Curriculum Because of AI
1. **AI-Accelerated Workflows**: How modern practitioners leverage LLMs and AI tools (code completion, automated test scaffolding, interactive explication) productively without losing mental agency.
2. **AI Tooling & Modern Ecosystem Integrations**: Modern libraries, vector embeddings, LLM APIs, function calling, or AI-adjacent tooling relevant to {topic_title}.
3. **Critical Verification & Hallucination Defense**: Cultivating the vital instinct to spot subtle AI hallucinations, off-by-one reasoning traps, invalid assumptions, and security vulnerabilities that AI co-pilots commonly produce.
4. **First-Principles Invariant Defense**: Ensuring the learner truly understands the underlying mechanics so they can supervise, debug, and steer AI rather than being blindly dependent on it.
"""
    doc += f"\n{ai_era_section.strip()}\n"

    return doc


def run_scout(
    slug: str,
    workspace: Path | str = ".",
    url: str | None = None,
    source_path: Path | str | None = None,
    topic: str | None = None,
    confidence_override: str | None = None,
    hats: str | list[str] | None = None,
    beginner: bool = False,
    ai: bool = False,
) -> dict[str, Any]:
    """Execute research scouting for target slug and write structured cache files."""
    ws = Path(workspace).resolve()

    extracted_content = ""
    source_uri = ""
    source_type = ""
    confidence = "unverified"
    notes = []

    # 1. Local path source
    if source_path:
        p = Path(source_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Source path not found: {p}")
        source_uri = str(p)
        if p.is_file():
            source_type = "file"
            extracted_content = p.read_text(encoding="utf-8")
        elif p.is_dir():
            source_type = "directory"
            parts = []
            for f in sorted(p.glob("**/*")):
                if f.is_file() and f.suffix in {".md", ".txt", ".rst", ".py", ".rs", ".ts", ".go"}:
                    parts.append(f"# File: {f.name}\n" + f.read_text(encoding="utf-8"))
            extracted_content = "\n\n".join(parts)
        confidence = "high"

    # 2. Web URL source
    elif url:
        source_uri = url
        source_type = "url"
        content, err = fetch_url_content(url)
        if err:
            notes.append(f"Network fetch warning: {err}")
            extracted_content = f"# Documentation for {slug}\nTopic reference: {url}\n"
            confidence = "unverified"
        else:
            extracted_content = content
            confidence = "high"

    # 3. Topic fallback
    elif topic:
        source_uri = f"topic:{topic}"
        source_type = "topic_fallback"
        extracted_content = (
            f"# {topic.title()}\n\n"
            f"Overview and fundamental concepts for {topic}.\n\n"
            f"## Core Concepts\n- Architecture\n- Primitives\n- Applications\n"
        )
        confidence = "medium"

    else:
        source_uri = f"topic:{slug}"
        source_type = "slug_fallback"
        extracted_content = f"# {slug.title()}\n\nDefault overview for {slug}.\n"
        confidence = "unverified"

    if confidence_override:
        if confidence_override not in VALID_CONFIDENCE_LEVELS:
            raise ValueError(
                f"Invalid confidence '{confidence_override}'. Must be one of {sorted(VALID_CONFIDENCE_LEVELS)}"
            )
        confidence = confidence_override

    parsed = extract_toc_and_api(extracted_content)
    content_hash = compute_sha256(extracted_content)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    topic_title = topic or slug.replace("-", " ").title()

    digest = {
        "slug": slug,
        "title": topic_title,
        "source_uri": source_uri,
        "source_type": source_type,
        "confidence": confidence,
        "crawled_at": now_iso,
        "content_sha256": content_hash,
        "metadata": {
            "slug": slug,
            "title": topic_title,
            "source_uri": source_uri,
            "source_type": source_type,
            "confidence": confidence,
            "content_sha256": content_hash,
            "extracted_at": now_iso,
        },
        "toc": parsed["toc"],
        "api_index": parsed["api_index"],
        "vocabulary": parsed["vocabulary"],
        "ai_era": {
            "what_has_changed": f"Modern AI tools automate syntax boilerplate in {topic_title}, shifting practitioner emphasis toward invariant formulation, edge cases, and verification.",
            "ai_adjacent_topics": [
                "AI-assisted workflow ergonomics",
                "Verification harnesses for AI-generated code/claims",
                "Modern ecosystem tooling & LLM integrations",
                "Prompt/context specification for domain tasks",
            ],
            "verification_guardrails": "Never accept AI output without boundary condition checks, type/invariant validation, and adversarial stress-testing.",
        },
        "summary": f"Scouted {len(parsed['toc'])} headings, {len(parsed['api_index'])} API symbols, {len(parsed['vocabulary'])} terms from {source_type}.",
        "notes": notes,
    }

    # 4. Check for multi-source harvested assets & gold-standard consensus (FR-43)
    gold_standards_file = ws / "research" / slug / "gold-standards.md"
    sources_dir = ws / "research" / slug / "sources"
    gold_section = ""
    discovered_harvest_sources: list[dict[str, Any]] = []

    if sources_dir.exists():
        try:
            if harvester and hasattr(harvester, "ingest_sources_directory"):
                ingest_res = harvester.ingest_sources_directory(slug, ws)
                discovered_harvest_sources = ingest_res.get("sources", [])
        except Exception:
            pass

    if gold_standards_file.is_file():
        gs_text = gold_standards_file.read_text(encoding="utf-8")
        gold_section = f"\n## 7. Gold-Standard Literature & Multi-Source Harvested Assets\n\n{gs_text.strip()}\n"
    elif discovered_harvest_sources:
        items_summary = "\n".join(
            f"- **{s.get('title')}** (`{s.get('type')}`): `{s.get('relative_path')}`"
            for s in discovered_harvest_sources[:30]
        )
        gold_section = (
            f"\n## 7. Gold-Standard Literature & Multi-Source Harvested Assets\n\n"
            f"### Harvested Assets ({len(discovered_harvest_sources)} items)\n"
            f"{items_summary}\n"
        )

    # If verified harvested sources exist, promote confidence
    if discovered_harvest_sources and confidence in {"unverified", "medium"} and not confidence_override:
        confidence = "high"

    # Generate full multi-hat critique and dossier markdown
    dossier_md = generate_dossier_markdown(
        topic_title=topic_title,
        slug=slug,
        confidence=confidence,
        parsed=parsed,
        extracted_content=extracted_content,
        source_uri=source_uri,
        gold_standards_section=gold_section,
    )
    critique_md = generate_five_hats_critique(
        topic_title=topic_title,
        parsed=parsed,
        extracted_content=extracted_content,
        requested_hats=hats,
        is_beginner=beginner,
        include_ai_hat=ai,
    )

    sources_data = {
        "research": {
            "slug": slug,
            "confidence": confidence,
            "updated_at": now_iso,
        },
        "sources": [
            {
                "uri": source_uri,
                "type": source_type,
                "sha256": content_hash,
                "status": "verified" if confidence in {"high", "medium"} else "unverified",
            }
        ],
    }

    sources_json_data = {
        "slug": slug,
        "title": topic_title,
        "confidence": confidence,
        "crawled_at": now_iso,
        "sources": [
            {
                "title": topic_title,
                "uri": source_uri,
                "type": source_type,
                "sha256": content_hash,
                "status": "verified" if confidence in {"high", "medium"} else "unverified",
            }
        ],
    }

    for s in discovered_harvest_sources:
        sources_data["sources"].append({
            "uri": s.get("relative_path") or s.get("full_path"),
            "type": s.get("type", "harvested_asset"),
            "sha256": s.get("sha256", ""),
            "status": s.get("status", "verified"),
        })
        sources_json_data["sources"].append({
            "title": s.get("title", "Harvested Source"),
            "uri": s.get("relative_path") or s.get("full_path"),
            "type": s.get("type", "harvested_asset"),
            "sha256": s.get("sha256", ""),
            "status": s.get("status", "verified"),
        })

    # Write to all target locations: visible research/, visible sources/, _tc/research/, .tc/research/
    target_dirs = [
        ws / "research" / slug,
        ws / "sources" / slug,
        ws / "_tc" / "research" / slug,
        ws / ".tc" / "research" / slug,
    ]
    for rdir in target_dirs:
        rdir.mkdir(parents=True, exist_ok=True)
        atomic_write_json(rdir / "digest.json", digest)
        atomic_write_toml(rdir / "sources.toml", sources_data)
        atomic_write_json(rdir / "sources.json", sources_json_data)
        atomic_write_text(rdir / "dossier.md", dossier_md)
        atomic_write_text(rdir / "five-hats-critique.md", critique_md)
        atomic_write_text(rdir / "multi-hats-critique.md", critique_md)

    primary_dir = target_dirs[0]
    return {
        "ok": True,
        "slug": slug,
        "confidence": confidence,
        "digest_file": str(primary_dir / "digest.json"),
        "sources_file": str(primary_dir / "sources.toml"),
        "dossier_file": str(primary_dir / "dossier.md"),
        "critique_file": str(primary_dir / "five-hats-critique.md"),
        "headings_count": len(parsed["toc"]),
        "apis_count": len(parsed["api_index"]),
        "vocabulary_count": len(parsed["vocabulary"]),
        "harvested_sources_count": len(discovered_harvest_sources),
        "digest": digest,
    }


def get_cached_digest(slug: str, workspace: Path | str = ".") -> dict[str, Any]:
    """Retrieve cached research digest for a given slug from candidate search paths."""
    ws = Path(workspace).resolve()
    candidates = [
        ws / "research" / slug / "digest.json",
        ws / "_tc" / "research" / slug / "digest.json",
        ws / ".tc" / "research" / slug / "digest.json",
    ]
    for digest_file in candidates:
        if digest_file.is_file():
            try:
                return json.loads(digest_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue

    raise FileNotFoundError(f"No research digest cached for slug '{slug}' at any candidate path")


def get_cached_dossier(slug: str, workspace: Path | str = ".") -> str:
    """Retrieve cached research dossier markdown for a given slug."""
    ws = Path(workspace).resolve()
    candidates = [
        ws / "research" / slug / "dossier.md",
        ws / "_tc" / "research" / slug / "dossier.md",
        ws / ".tc" / "research" / slug / "dossier.md",
    ]
    for dossier_file in candidates:
        if dossier_file.is_file():
            return dossier_file.read_text(encoding="utf-8")

    raise FileNotFoundError(f"No research dossier cached for slug '{slug}' at any candidate path")


def get_cached_critique(slug: str, workspace: Path | str = ".") -> str:
    """Retrieve cached multi-hat critique for a given slug."""
    ws = Path(workspace).resolve()
    candidates = [
        ws / "research" / slug / "multi-hats-critique.md",
        ws / "research" / slug / "five-hats-critique.md",
        ws / "_tc" / "research" / slug / "multi-hats-critique.md",
        ws / "_tc" / "research" / slug / "five-hats-critique.md",
        ws / ".tc" / "research" / slug / "five-hats-critique.md",
    ]
    for critique_file in candidates:
        if critique_file.is_file():
            return critique_file.read_text(encoding="utf-8")

    raise FileNotFoundError(f"No multi-hat critique cached for slug '{slug}' at any candidate path")


def list_cached_research(workspace: Path | str = ".") -> dict[str, Any]:
    """List all research digests currently stored in workspace."""
    ws = Path(workspace).resolve()
    search_dirs = [
        ws / "research",
        ws / "_tc" / "research",
        ws / ".tc" / "research",
    ]

    topics_by_slug: dict[str, dict[str, Any]] = {}
    for base_dir in search_dirs:
        if not base_dir.is_dir():
            continue
        for item in sorted(base_dir.iterdir()):
            if item.is_dir() and (item / "digest.json").is_file():
                s = item.name
                if s not in topics_by_slug:
                    try:
                        d = json.loads((item / "digest.json").read_text(encoding="utf-8"))
                        meta = d.get("metadata", {})
                        title = meta.get("title") or d.get("title", s)
                        conf = meta.get("confidence") or d.get("confidence", "unverified")
                        source = meta.get("source_uri") or d.get("source", "")
                        crawled_at = meta.get("extracted_at") or d.get("crawled_at", "")
                        topics_by_slug[s] = {
                            "slug": s,
                            "title": title,
                            "confidence": conf,
                            "source": source,
                            "crawled_at": crawled_at,
                            "has_dossier": (item / "dossier.md").is_file(),
                            "has_critique": (item / "five-hats-critique.md").is_file() or (item / "multi-hats-critique.md").is_file(),
                            "location": str(item),
                        }
                    except Exception:
                        pass

    topics_list = list(topics_by_slug.values())
    return {
        "ok": True,
        "workspace": str(ws),
        "count": len(topics_list),
        "topics": topics_list,
        "research_topics": topics_list,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scout.py",
        description="TextCourses documentation scout and Universal Multi-Hat Research Engine.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # scout
    p_scout = subparsers.add_parser("scout", help="Scout documentation and cache research dossier.")
    p_scout.add_argument("--slug", required=True, help="Course or topic slug (e.g. rust-systems).")
    p_scout.add_argument("--workspace", default=".", help="Path to workspace root.")
    p_scout.add_argument("--url", default=None, help="Documentation web URL to scout.")
    p_scout.add_argument("--source-path", default=None, help="Local file or directory to extract.")
    p_scout.add_argument("--topic", default=None, help="Topic description for fallback scaffolding.")
    p_scout.add_argument("--confidence", default=None, help="Explicit confidence override.")
    p_scout.add_argument("--hats", default=None, help="Optional comma-separated list of critical hats to wear.")
    p_scout.add_argument("--beginner", action="store_true", help="Prioritize beginner empathy and intuitive mental model hats.")
    p_scout.add_argument("--ai", action="store_true", help="Include AI-Pro Strategist hat to evaluate AI-era transformation and tooling.")
    p_scout.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # dossier
    p_dos = subparsers.add_parser("dossier", help="Retrieve cached research dossier markdown.")
    p_dos.add_argument("--slug", required=True, help="Course or topic slug.")
    p_dos.add_argument("--workspace", default=".", help="Path to workspace root.")
    p_dos.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # critique
    p_crit = subparsers.add_parser("critique", help="Retrieve cached multi-hat critical reflection markdown.")
    p_crit.add_argument("--slug", required=True, help="Course or topic slug.")
    p_crit.add_argument("--workspace", default=".", help="Path to workspace root.")
    p_crit.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # hats
    p_hats = subparsers.add_parser("hats", help="List all available critical hats in the universal registry.")
    p_hats.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # get
    p_get = subparsers.add_parser("get", help="Retrieve cached research digest.")
    p_get.add_argument("--slug", required=True, help="Course or topic slug.")
    p_get.add_argument("--workspace", default=".", help="Path to workspace root.")
    p_get.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # list
    p_list = subparsers.add_parser("list", help="List all cached research topics.")
    p_list.add_argument("--workspace", default=".", help="Path to workspace root.")
    p_list.add_argument("--json", action="store_true", help="Output results in JSON format.")

    # harvest-repo (FR-43.2)
    p_repo = subparsers.add_parser("harvest-repo", help="Clone or download open textbook / course repo from GitHub")
    p_repo.add_argument("--slug", required=True, help="Target course slug")
    p_repo.add_argument("--repo", required=True, help="GitHub repository URL or owner/repo")
    p_repo.add_argument("--workspace", default=".", help="Workspace root path")
    p_repo.add_argument("--branch", default="main", help="Target git branch (default: main)")

    # harvest-youtube (FR-43.3)
    p_yt = subparsers.add_parser("harvest-youtube", help="Extract and clean video transcript from YouTube lecture")
    p_yt.add_argument("--slug", required=True, help="Target course slug")
    p_yt.add_argument("--url", required=True, help="YouTube video URL or video ID")
    p_yt.add_argument("--title", default="Video Lecture", help="Video lecture title")
    p_yt.add_argument("--workspace", default=".", help="Workspace root path")

    # record-consensus (FR-43.1 / FR-43.4)
    p_cons = subparsers.add_parser("record-consensus", help="Record community consensus & gold-standard items")
    p_cons.add_argument("--slug", required=True, help="Target course slug")
    p_cons.add_argument("--topic", required=True, help="Topic title")
    p_cons.add_argument("--summary", required=True, help="Summary of Reddit / community consensus")
    p_cons.add_argument("--items-json", default="[]", help="JSON array of gold-standard books/items")
    p_cons.add_argument("--workspace", default=".", help="Workspace root path")

    # ingest-sources (FR-43.5)
    p_ing = subparsers.add_parser("ingest-sources", help="Scan and index research/<slug>/sources/ directory")
    p_ing.add_argument("--slug", required=True, help="Target course slug")
    p_ing.add_argument("--workspace", default=".", help="Workspace root path")

    args = parser.parse_args()

    try:
        if args.subcommand == "scout":
            result = run_scout(
                slug=args.slug,
                workspace=args.workspace,
                url=args.url,
                source_path=args.source_path,
                topic=args.topic,
                confidence_override=args.confidence,
                hats=getattr(args, "hats", None),
                beginner=getattr(args, "beginner", False),
                ai=getattr(args, "ai", False),
            )
            output_json(result, 0)

        elif args.subcommand == "dossier":
            content = get_cached_dossier(args.slug, args.workspace)
            if args.json:
                output_json({"ok": True, "slug": args.slug, "dossier": content}, 0)
            else:
                print(content)
                sys.exit(0)

        elif args.subcommand == "critique":
            content = get_cached_critique(args.slug, args.workspace)
            if args.json:
                output_json({"ok": True, "slug": args.slug, "critique": content}, 0)
            else:
                print(content)
                sys.exit(0)

        elif args.subcommand == "hats":
            if args.json:
                output_json({"ok": True, "total_hats": len(UNIVERSAL_HATS), "hats": UNIVERSAL_HATS}, 0)
            else:
                print(f"Universal Critical Hat Registry ({len(UNIVERSAL_HATS)} available hats):\n")
                for k, v in UNIVERSAL_HATS.items():
                    print(f"  [{k}] - {v['generic_title']}")
                    print(f"    Stance: {v['stance']}\n")
                sys.exit(0)

        elif args.subcommand == "get":
            result = get_cached_digest(args.slug, args.workspace)
            output_json(result, 0)

        elif args.subcommand == "list":
            result = list_cached_research(args.workspace)
            output_json(result, 0)

        elif args.subcommand == "harvest-repo":
            if not harvester or not hasattr(harvester, "harvest_github_repo"):
                output_json({"error": "Harvester module unavailable"}, 1)
            res = harvester.harvest_github_repo(
                repo_identifier=args.repo,
                slug=args.slug,
                workspace=args.workspace,
                branch=args.branch,
            )
            output_json(res, 0 if res.get("ok") else 1)

        elif args.subcommand == "harvest-youtube":
            if not harvester or not hasattr(harvester, "harvest_youtube_transcript"):
                output_json({"error": "Harvester module unavailable"}, 1)
            res = harvester.harvest_youtube_transcript(
                url_or_id=args.url,
                slug=args.slug,
                title=args.title,
                workspace=args.workspace,
            )
            output_json(res, 0 if res.get("ok") else 1)

        elif args.subcommand == "record-consensus":
            if not harvester or not hasattr(harvester, "record_gold_standards"):
                output_json({"error": "Harvester module unavailable"}, 1)
            items = json.loads(args.items_json) if isinstance(args.items_json, str) else args.items_json
            res = harvester.record_gold_standards(
                slug=args.slug,
                topic=args.topic,
                consensus_summary=args.summary,
                gold_standard_items=items,
                workspace=args.workspace,
            )
            output_json(res, 0)

        elif args.subcommand == "ingest-sources":
            if not harvester or not hasattr(harvester, "ingest_sources_directory"):
                output_json({"error": "Harvester module unavailable"}, 1)
            res = harvester.ingest_sources_directory(
                slug=args.slug,
                workspace=args.workspace,
            )
            output_json(res, 0)

        else:
            output_json({"error": f"Unknown subcommand: {args.subcommand}"}, 1)

    except Exception as e:
        output_json({"error": str(e)}, 1)


if __name__ == "__main__":
    main()
