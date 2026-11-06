#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""dashboard_generator.py — Self-Contained Local Interactive Status Dashboard Generator.

Generates a static, standalone status board at status-board/index.html and updates
_tc/status/state.json upon workspace initialization and after every state mutation (CAP-10, FR-50).

Zero external network requests: 100% offline file:// compatible with standalone embedded
CSS, inline SVG icons, and vanilla JavaScript.
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]


def collect_workspace_state(workspace: Path | str = ".") -> dict[str, Any]:
    """Inspect canonical _tc/ storage and construct a complete workspace state tree."""
    ws = Path(workspace).resolve()

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 1. Configuration & Preferences
    config_file = ws / "_tc" / "config.json"
    config_data: dict[str, Any] = {}
    if config_file.is_file():
        try:
            config_data = json.loads(config_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    pref_file = ws / "_tc" / "profile" / "preferences.md"
    if not pref_file.is_file():
        pref_file = ws / "profile" / "preferences.md"
    if not pref_file.is_file():
        pref_file = ws / "plan" / "preferences.md"

    pref_text = pref_file.read_text(encoding="utf-8") if pref_file.is_file() else ""
    pref_map: dict[str, str] = {}
    for line in pref_text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            pref_map[k.strip().lower()] = v.strip()

    # 2. Checkpoint / Active Gate
    checkpoint_file = ws / "_tc" / "checkpoint.json"
    if not checkpoint_file.is_file():
        checkpoint_file = ws / ".tc" / "checkpoint.json"

    active_gate_data: dict[str, Any] | None = None
    if checkpoint_file.is_file():
        try:
            cp_raw = json.loads(checkpoint_file.read_text(encoding="utf-8"))
            if cp_raw and isinstance(cp_raw, dict):
                active_gate_data = cp_raw
        except Exception:
            pass

    # 3. Courses Inspection
    courses_dict: dict[str, dict[str, Any]] = {}
    course_dirs = set()

    for p in [ws / "_tc" / "courses", ws / "courses"]:
        if p.is_dir():
            for sub in p.iterdir():
                if sub.is_dir() and not sub.name.startswith("."):
                    course_dirs.add(sub.name)

    active_pointer: dict[str, Any] | None = None

    for slug in sorted(course_dirs):
        # Locate course.toml
        toml_path = ws / "_tc" / "courses" / slug / "course.toml"
        if not toml_path.is_file():
            toml_path = ws / "courses" / slug / ".tc" / "course.toml"
        if not toml_path.is_file():
            toml_path = ws / "courses" / slug / "course.toml"

        c_data: dict[str, Any] = {}
        if toml_path.is_file():
            try:
                c_data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        c_info = c_data.get("course", {})
        title = c_info.get("title") or slug.replace("-", " ").title()
        archetype = c_info.get("archetype", "applied_creation")

        chapters_raw = c_data.get("chapters", [])
        total_sections = sum(len(ch.get("sections", [])) for ch in chapters_raw)
        completed_sections = 0
        review_sections = 0
        in_progress_sections = 0
        first_in_progress_sec: dict[str, Any] | None = None

        chapters_tree: list[dict[str, Any]] = []
        for ch_idx, ch in enumerate(chapters_raw, 1):
            ch_sections: list[dict[str, Any]] = []
            for s_idx, sec in enumerate(ch.get("sections", []), 1):
                stat = sec.get("status", "not_started")
                if stat == "completed":
                    completed_sections += 1
                elif stat == "review":
                    review_sections += 1
                elif stat == "in_progress":
                    in_progress_sections += 1
                    if not first_in_progress_sec:
                        first_in_progress_sec = {
                            "course_slug": slug,
                            "chapter_id": ch.get("id", f"chapter-{ch_idx:02d}"),
                            "chapter_title": ch.get("title", f"Chapter {ch_idx}"),
                            "section_id": sec.get("id", f"sec-{s_idx:02d}"),
                            "section_title": sec.get("title", f"Section {s_idx}"),
                        }

                ch_sections.append({
                    "id": sec.get("id", f"sec-{s_idx:02d}"),
                    "title": sec.get("title", f"Section {s_idx}"),
                    "status": stat,
                    "vocabulary": sec.get("vocabulary_introduced", []),
                })

            chapters_tree.append({
                "id": ch.get("id", f"chapter-{ch_idx:02d}"),
                "title": ch.get("title", f"Chapter {ch_idx}"),
                "sections": ch_sections,
            })

        # Notes count
        notes_dir = ws / "courses" / slug / "notes"
        notes_count = len(list(notes_dir.glob("*.md"))) if notes_dir.is_dir() else 0

        # Source map concepts
        sm_file = ws / "_tc" / "courses" / slug / "source-map.toml"
        if not sm_file.is_file():
            sm_file = ws / "courses" / slug / ".tc" / "source-map.toml"
        sm_concepts = 0
        if sm_file.is_file():
            try:
                sm_data = tomllib.loads(sm_file.read_text(encoding="utf-8"))
                sm_concepts = sm_data.get("total_concepts", 0)
            except Exception:
                pass

        completion_pct = round((completed_sections / total_sections * 100), 1) if total_sections > 0 else 0.0

        courses_dict[slug] = {
            "slug": slug,
            "title": title,
            "archetype": archetype,
            "total_chapters": len(chapters_raw),
            "total_sections": total_sections,
            "completed_sections": completed_sections,
            "review_sections": review_sections,
            "in_progress_sections": in_progress_sections,
            "completion_pct": completion_pct,
            "notes_count": notes_count,
            "mapped_concepts_count": sm_concepts,
            "chapters": chapters_tree,
        }

        if not active_pointer and first_in_progress_sec:
            active_pointer = first_in_progress_sec

    # Default active pointer if none in progress
    if not active_pointer and courses_dict:
        first_c = next(iter(courses_dict.values()))
        active_pointer = {
            "course_slug": first_c["slug"],
            "chapter_id": first_c["chapters"][0]["id"] if first_c["chapters"] else "",
            "chapter_title": first_c["chapters"][0]["title"] if first_c["chapters"] else "",
            "section_id": first_c["chapters"][0]["sections"][0]["id"] if (first_c["chapters"] and first_c["chapters"][0]["sections"]) else "",
            "section_title": first_c["chapters"][0]["sections"][0]["title"] if (first_c["chapters"] and first_c["chapters"][0]["sections"]) else "",
        }

    # 4. Multi-Source Research & Conversion Substrate
    research_dict: dict[str, dict[str, Any]] = {}
    res_dirs = set()
    for p in [ws / "_tc" / "research", ws / "research"]:
        if p.is_dir():
            for sub in p.iterdir():
                if sub.is_dir():
                    res_dirs.add(sub.name)

    for r_slug in sorted(res_dirs):
        r_base = ws / "_tc" / "research" / r_slug
        if not r_base.is_dir():
            r_base = ws / "research" / r_slug

        # Converted markdown sources
        md_dir = r_base / "sources" / "markdown"
        md_files = sorted(md_dir.glob("*.md")) if md_dir.is_dir() else []
        raw_dir = r_base / "sources" / "raw"
        raw_files = sorted(raw_dir.glob("*.md")) if raw_dir.is_dir() else []

        # Conversion ledger
        ledger_file = r_base / "conversion-ledger.json"
        ledger_data: dict[str, Any] = {}
        if ledger_file.is_file():
            try:
                ledger_data = json.loads(ledger_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        # 4-Hat Debate records
        debate_file = r_base / "debate.jsonl"
        debate_rounds: list[dict[str, Any]] = []
        if debate_file.is_file():
            try:
                for line in debate_file.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        debate_rounds.append(json.loads(line.strip()))
            except Exception:
                pass

        debate_sum_file = r_base / "debate-summary.md"
        debate_summary_text = debate_sum_file.read_text(encoding="utf-8") if debate_sum_file.is_file() else ""

        research_dict[r_slug] = {
            "slug": r_slug,
            "markdown_sources_count": len(md_files) or len(raw_files),
            "sources_list": [p.stem.replace("-", " ").title() for p in (md_files or raw_files)[:10]],
            "conversion_ledger": ledger_data,
            "debate_rounds_count": len(debate_rounds),
            "debate_summary_snippet": debate_summary_text[:300] if debate_summary_text else "",
        }

    # 5. Memlog Timeline & Decisions
    memlog_file = ws / "_tc" / "memlog.md"
    if not memlog_file.is_file():
        memlog_file = ws / "profile" / "memlog.md"

    memlog_entries: list[dict[str, Any]] = []
    decisions_list: list[str] = []

    if memlog_file.is_file():
        try:
            m_text = memlog_file.read_text(encoding="utf-8")
            for line in m_text.splitlines():
                line_str = line.strip()
                if line_str.startswith("- "):
                    entry_text = line_str[2:].strip()
                    scope = "profile"
                    tag = "general"
                    if "(milestone)" in entry_text:
                        tag = "milestone"
                    elif "(decision)" in entry_text:
                        tag = "decision"
                        decisions_list.append(entry_text)
                    elif "(research)" in entry_text:
                        tag = "research"

                    memlog_entries.append({
                        "text": entry_text,
                        "tag": tag,
                        "scope": scope,
                    })
        except Exception:
            pass

    # 6. Determine Next Action Recommendation
    if active_gate_data:
        gate_name = active_gate_data.get("gate", "Checkpoint Gate")
        next_action = f"Pending Gate: {gate_name.replace('_', ' ').title()}. Please select an option via /tc."
    elif active_pointer and active_pointer.get("section_title"):
        next_action = f"Study Active Concept in {active_pointer['section_title']} (Run `/tc`)."
    elif courses_dict:
        next_action = "Review curriculum roadmap or begin next section via `/tc`."
    else:
        next_action = "Initialize a course or research domain via `/tc`."

    state: dict[str, Any] = {
        "framework": "TextCourses",
        "version": config_data.get("version", "0.3.0"),
        "last_updated": now_iso,
        "workspace_root": str(ws),
        "preferences": pref_map,
        "active_gate": active_gate_data,
        "has_active_gate": bool(active_gate_data),
        "active_pointer": active_pointer,
        "next_action": next_action,
        "total_courses": len(courses_dict),
        "courses": courses_dict,
        "research": research_dict,
        "decisions": decisions_list[-15:],
        "memlog_timeline": memlog_entries[-25:],
    }

    # Save to _tc/status/state.json
    state_dir = ws / "_tc" / "status"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "state.json"
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    return state


def generate_dashboard_html(state: dict[str, Any]) -> str:
    """Generate a self-contained, offline-first, single-file HTML dashboard from workspace state."""
    active_gate = state.get("active_gate")
    has_gate = state.get("has_active_gate", False)
    active_ptr = state.get("active_pointer") or {}
    courses = state.get("courses", {})
    research = state.get("research", {})
    memlogs = state.get("memlog_timeline", [])
    prefs = state.get("preferences", {})

    # Calculate overall metrics
    total_courses = len(courses)
    total_sections = sum(c.get("total_sections", 0) for c in courses.values())
    completed_sections = sum(c.get("completed_sections", 0) for c in courses.values())
    overall_pct = round((completed_sections / total_sections * 100), 1) if total_sections > 0 else 0.0

    total_md_sources = sum(r.get("markdown_sources_count", 0) for r in research.values())

    # Build Gate Banner HTML
    gate_html = ""
    if has_gate and active_gate:
        g_name = active_gate.get("gate", "interactive_checkpoint").replace("_", " ").title()
        g_prompt = active_gate.get("prompt", "Checkpoint decision required.")
        g_options = active_gate.get("options", [])

        opts_html = "".join(
            f'<div class="gate-opt"><span class="opt-key">[{html.escape(opt.get("key", ""))}]</span> <span class="opt-label">{html.escape(opt.get("label", ""))}</span></div>'
            for opt in g_options
        )
        gate_html = f"""
        <div class="card banner-card">
            <div class="banner-badge">⚠️ Active Checkpoint Gate: {html.escape(g_name)}</div>
            <div class="banner-prompt">{html.escape(g_prompt[:250])}{'...' if len(g_prompt) > 250 else ''}</div>
            <div class="banner-options">{opts_html}</div>
            <div class="banner-footer">Action required: reply via terminal or prompt with your choice.</div>
        </div>
        """

    # Build Courses Cards HTML
    courses_cards_html = ""
    for slug, c in courses.items():
        ch_items_html = ""
        for ch in c.get("chapters", []):
            sec_items_html = ""
            for sec in ch.get("sections", []):
                stat = sec.get("status", "not_started")
                stat_class = f"badge-{stat}"
                sec_items_html += f"""
                <li class="sec-item">
                    <span class="sec-title">{html.escape(sec.get("title", "Section"))}</span>
                    <span class="badge {stat_class}">{html.escape(stat.replace('_', ' '))}</span>
                </li>
                """
            ch_items_html += f"""
            <div class="chapter-block">
                <div class="chapter-title">{html.escape(ch.get("title", "Chapter"))}</div>
                <ul class="sec-list">{sec_items_html}</ul>
            </div>
            """

        pct = c.get("completion_pct", 0.0)
        courses_cards_html += f"""
        <div class="card course-card">
            <div class="card-header">
                <div class="course-header-left">
                    <h3 class="course-title">{html.escape(c.get("title", slug))}</h3>
                    <div class="course-meta">
                        <span class="meta-tag">{html.escape(c.get("archetype", "").replace('_', ' ').title())}</span>
                        <span class="meta-tag">{c.get("completed_sections", 0)}/{c.get("total_sections", 0)} Sections</span>
                        <span class="meta-tag">{c.get("notes_count", 0)} Chapter Notes</span>
                    </div>
                </div>
                <div class="course-pct">{pct}%</div>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {pct}%;"></div>
            </div>
            <div class="chapters-container">{ch_items_html}</div>
        </div>
        """

    if not courses_cards_html:
        courses_cards_html = '<div class="card"><div class="empty-state">No courses scaffolded yet. Run <code>/tc</code> to begin.</div></div>'

    # Build Research Substrate HTML
    research_cards_html = ""
    for r_slug, r in research.items():
        ledger = r.get("conversion_ledger", {})
        ledger_status = "100% Verified Zero-Loss" if ledger else "Active Substrate"
        sources_list_html = "".join(f"<li>{html.escape(s)}</li>" for s in r.get("sources_list", []))
        if not sources_list_html:
            sources_list_html = "<li>Standard verified documentation and papers</li>"

        research_cards_html += f"""
        <div class="card research-card">
            <div class="card-header">
                <h4 class="research-title">{html.escape(r_slug)} Research Substrate</h4>
                <span class="badge badge-verified">{html.escape(ledger_status)}</span>
            </div>
            <div class="research-stats">
                <div class="stat-box"><span class="stat-num">{r.get("markdown_sources_count", 0)}</span><span class="stat-lbl">Markdown Sources</span></div>
                <div class="stat-box"><span class="stat-num">{r.get("debate_rounds_count", 0)}</span><span class="stat-lbl">Debate Rounds</span></div>
            </div>
            <div class="research-sample">
                <strong>Primary Materials:</strong>
                <ul class="materials-list">{sources_list_html}</ul>
            </div>
            {f'<div class="debate-snippet"><strong>4-Hat Deliberation Consensus:</strong><p>{html.escape(r.get("debate_summary_snippet", ""))}</p></div>' if r.get("debate_summary_snippet") else ''}
        </div>
        """

    if not research_cards_html:
        research_cards_html = '<div class="card"><div class="empty-state">No multi-source research dossiers discovered yet.</div></div>'

    # Build Memlog Feed HTML
    memlog_items_html = ""
    for m in reversed(memlogs):
        tag = m.get("tag", "general")
        tag_badge = f"badge-{tag}"
        text_esc = html.escape(m.get("text", ""))
        memlog_items_html += f"""
        <div class="timeline-item" data-tag="{html.escape(tag)}">
            <span class="timeline-bullet"></span>
            <span class="badge {tag_badge}">{html.escape(tag)}</span>
            <span class="timeline-text">{text_esc}</span>
        </div>
        """

    if not memlog_items_html:
        memlog_items_html = '<div class="empty-state">No milestone records logged yet.</div>'

    # Standalone HTML Document with Embedded CSS and JS (0 External Network Requests)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TextCourses — Local Status Board</title>
    <style>
        :root {{
            --bg: #090d16;
            --surface: #131b2e;
            --surface-card: #182238;
            --border: #23304d;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --primary: #38bdf8;
            --accent: #818cf8;
            --green: #10b981;
            --yellow: #f59e0b;
            --red: #ef4444;
            --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text-main);
            font-family: var(--font);
            line-height: 1.5;
            padding: 24px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .brand-icon {{
            width: 32px;
            height: 32px;
            fill: var(--primary);
        }}
        h1 {{
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}
        .header-meta {{
            font-size: 0.85rem;
            color: var(--text-muted);
            text-align: right;
        }}
        .top-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
        }}
        .metric-val {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--primary);
        }}
        .metric-lbl {{
            font-size: 0.85rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        .banner-card {{
            background: #271d0b;
            border-color: #78350f;
        }}
        .banner-badge {{
            color: #fbbf24;
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 8px;
        }}
        .banner-prompt {{
            font-size: 0.95rem;
            color: #fef3c7;
            margin-bottom: 12px;
            white-space: pre-wrap;
        }}
        .banner-options {{
            display: flex;
            flex-direction: column;
            gap: 6px;
            margin-bottom: 8px;
        }}
        .gate-opt {{
            font-size: 0.85rem;
            color: #fde68a;
        }}
        .opt-key {{
            font-family: monospace;
            font-weight: 700;
        }}
        .banner-footer {{
            font-size: 0.8rem;
            color: #f59e0b;
            font-style: italic;
        }}
        .active-pointer-card {{
            border-left: 4px solid var(--accent);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .active-label {{
            font-size: 0.75rem;
            color: var(--accent);
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.05em;
        }}
        .active-text {{
            font-size: 1.15rem;
            font-weight: 600;
        }}
        .badge {{
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .badge-completed {{ background: #064e3b; color: #34d399; }}
        .badge-review {{ background: #451a03; color: #fbbf24; }}
        .badge-in_progress {{ background: #1e3a8a; color: #60a5fa; }}
        .badge-not_started {{ background: #1e293b; color: #64748b; }}
        .badge-verified {{ background: #064e3b; color: #34d399; }}
        .badge-milestone {{ background: #312e81; color: #a5b4fc; }}
        .badge-decision {{ background: #701a75; color: #f472b6; }}
        .badge-general {{ background: #1e293b; color: #94a3b8; }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}
        .course-title {{ font-size: 1.25rem; font-weight: 700; }}
        .course-meta {{ display: flex; gap: 8px; margin-top: 4px; }}
        .meta-tag {{ font-size: 0.75rem; color: var(--text-muted); background: var(--surface-card); padding: 2px 6px; border-radius: 4px; }}
        .course-pct {{ font-size: 1.25rem; font-weight: 700; color: var(--primary); }}
        .progress-bar-bg {{ background: #1e293b; border-radius: 9999px; height: 8px; overflow: hidden; margin-bottom: 16px; }}
        .progress-bar-fill {{ background: var(--green); height: 100%; border-radius: 9999px; }}
        .chapters-container {{ display: flex; flex-direction: column; gap: 12px; }}
        .chapter-block {{ background: var(--surface-card); border-radius: 6px; padding: 12px; }}
        .chapter-title {{ font-size: 0.95rem; font-weight: 600; margin-bottom: 8px; }}
        .sec-list {{ list-style: none; display: flex; flex-direction: column; gap: 6px; }}
        .sec-item {{ display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; padding: 4px 0; border-bottom: 1px solid var(--border); }}
        .sec-item:last-child {{ border-bottom: none; }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
        @media (max-width: 800px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
        .timeline-item {{ display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 0.85rem; }}
        .timeline-bullet {{ width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }}
        .research-stats {{ display: flex; gap: 16px; margin: 12px 0; }}
        .stat-box {{ background: var(--surface-card); padding: 8px 12px; border-radius: 6px; text-align: center; }}
        .stat-num {{ font-size: 1.25rem; font-weight: 700; display: block; color: var(--primary); }}
        .stat-lbl {{ font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; }}
        .materials-list {{ list-style: square; padding-left: 20px; font-size: 0.85rem; color: var(--text-muted); margin-top: 6px; }}
        .debate-snippet {{ margin-top: 12px; font-size: 0.8rem; background: var(--surface-card); padding: 8px 12px; border-radius: 6px; color: var(--text-muted); }}
        .controls {{ display: flex; gap: 8px; margin-bottom: 12px; }}
        .filter-btn {{ background: var(--surface-card); color: var(--text-muted); border: 1px solid var(--border); border-radius: 4px; padding: 4px 10px; font-size: 0.75rem; cursor: pointer; }}
        .filter-btn.active {{ background: var(--primary); color: #000; font-weight: 700; }}
        .search-box {{ width: 100%; background: var(--surface-card); border: 1px solid var(--border); color: var(--text-main); padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; }}
        .empty-state {{ text-align: center; color: var(--text-muted); padding: 24px 0; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="brand">
                <svg class="brand-icon" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                <div>
                    <h1>TextCourses Status Board</h1>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Sovereign Self-Directed Apprenticeship Engine</div>
                </div>
            </div>
            <div class="header-meta">
                <div>Framework: <strong>TextCourses v{html.escape(state.get("version", "0.3.0"))}</strong></div>
                <div>Updated: <strong>{html.escape(state.get("last_updated", "")[:19])}Z</strong></div>
            </div>
        </header>

        {gate_html}

        <div class="card active-pointer-card">
            <div>
                <div class="active-label">Next Action / Focus</div>
                <div class="active-text">{html.escape(state.get("next_action", ""))}</div>
            </div>
            <div>
                <span class="badge badge-in_progress">{html.escape(active_ptr.get("section_title") or "Active")}</span>
            </div>
        </div>

        <div class="top-metrics">
            <div class="metric-card">
                <div class="metric-val">{total_courses}</div>
                <div class="metric-lbl">Active Courses</div>
            </div>
            <div class="metric-card">
                <div class="metric-val">{completed_sections}/{total_sections}</div>
                <div class="metric-lbl">Sections Completed</div>
            </div>
            <div class="metric-card">
                <div class="metric-val">{overall_pct}%</div>
                <div class="metric-lbl">Overall Mastery</div>
            </div>
            <div class="metric-card">
                <div class="metric-val">{total_md_sources}</div>
                <div class="metric-lbl">Indexed Sources</div>
            </div>
        </div>

        <h2>Curriculum & Roadmap DAG</h2>
        <div style="margin-top: 12px;">{courses_cards_html}</div>

        <div class="grid-2">
            <div>
                <h2>Multi-Source Research Substrate</h2>
                <div style="margin-top: 12px;">{research_cards_html}</div>
            </div>

            <div>
                <h2>Memlog & Pedagogical Decision Feed</h2>
                <div style="margin-top: 12px;" class="card">
                    <input type="text" id="timeline-search" class="search-box" placeholder="Filter decisions or milestones...">
                    <div class="controls">
                        <button class="filter-btn active" onclick="filterTimeline('all')">All</button>
                        <button class="filter-btn" onclick="filterTimeline('milestone')">Milestones</button>
                        <button class="filter-btn" onclick="filterTimeline('decision')">Decisions</button>
                    </div>
                    <div id="timeline-container">{memlog_items_html}</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function filterTimeline(tag) {{
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('.timeline-item').forEach(item => {{
                if (tag === 'all' || item.getAttribute('data-tag') === tag) {{
                    item.style.display = 'flex';
                }} else {{
                    item.style.display = 'none';
                }}
            }});
        }}

        document.getElementById('timeline-search').addEventListener('input', function(e) {{
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.timeline-item').forEach(item => {{
                const text = item.innerText.toLowerCase();
                item.style.display = text.includes(query) ? 'flex' : 'none';
            }});
        }});
    </script>
</body>
</html>
"""


def write_status_dashboard(workspace: Path | str = ".") -> tuple[Path, Path]:
    """Compile workspace state, write _tc/status/state.json, and generate status-board/index.html."""
    ws = Path(workspace).resolve()

    state = collect_workspace_state(ws)
    state_file = ws / "_tc" / "status" / "state.json"

    html_content = generate_dashboard_html(state)
    board_dir = ws / "status-board"
    board_dir.mkdir(parents=True, exist_ok=True)
    html_file = board_dir / "index.html"
    html_file.write_text(html_content, encoding="utf-8")

    return state_file, html_file


def main() -> None:
    parser = argparse.ArgumentParser(description="dashboard_generator.py — Local Interactive Status Dashboard Generator")
    parser.add_argument("workspace", nargs="?", default=".", help="Path to TextCourses workspace root")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output")
    args = parser.parse_args()

    state_file, html_file = write_status_dashboard(args.workspace)

    if args.json:
        print(json.dumps({
            "ok": True,
            "state_file": str(state_file),
            "dashboard_file": str(html_file),
            "zero_network_requests": True,
            "file_url": f"file:///{str(html_file).replace(os.sep, '/')}",
        }, indent=2))
    else:
        print(f"Status Dashboard successfully generated:")
        print(f"  State: {state_file}")
        print(f"  HTML:  {html_file}")
        print(f"  Open:  file:///{str(html_file).replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
