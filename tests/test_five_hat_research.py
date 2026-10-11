"""tests/test_five_hat_research.py — Test suite for Autonomous 5-Hat Deep Research Engine."""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCOUT_SCRIPT = REPO_ROOT / "_tc" / "scripts" / "scout.py"
SKILL_FILE = REPO_ROOT / "skills" / "tc-research" / "SKILL.md"


def test_scout_generates_five_hats_and_dossier(tmp_path: Path):
    """Verify scout generates full 5-hat reflection, dossier, and sources in research/."""
    cmd = [
        sys.executable,
        str(SCOUT_SCRIPT),
        "scout",
        "--slug",
        "distributed-consensus",
        "--workspace",
        str(tmp_path),
        "--topic",
        "Distributed Consensus and Raft Leader Election",
        "--json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert data["slug"] == "distributed-consensus"

    # Check visible research/ artifacts
    research_dir = tmp_path / "research" / "distributed-consensus"
    assert research_dir.is_dir()

    dossier_file = research_dir / "dossier.md"
    assert dossier_file.is_file()
    dossier_text = dossier_file.read_text(encoding="utf-8")
    assert "Domain Research Dossier: Distributed Consensus" in dossier_text
    assert "Executive Summary & Domain Scope" in dossier_text
    assert "Conceptual Taxonomy & Core Mental Models" in dossier_text
    assert "Primitives & API Surface Index" in dossier_text
    assert "Dangerous Pitfalls & Fatal Traps" in dossier_text

    critique_file = research_dir / "five-hats-critique.md"
    assert critique_file.is_file()
    critique_text = critique_file.read_text(encoding="utf-8")
    assert "5-Hat Critical Reflection" in critique_text
    assert "Hat 1: Industry Practitioner" in critique_text
    assert "Hat 2: Academic Purist" in critique_text
    assert "Hat 3: Beginner Friction Hunter" in critique_text
    assert "Hat 4: Edge-Case Systems Engineer" in critique_text
    assert "Hat 5: Modern Ecosystem Reviewer" in critique_text
    assert "Tree of Thought" in critique_text

    sources_json_file = research_dir / "sources.json"
    assert sources_json_file.is_file()
    sources_data = json.loads(sources_json_file.read_text(encoding="utf-8"))
    assert sources_data["slug"] == "distributed-consensus"
    assert len(sources_data["sources"]) >= 1

    digest_file = research_dir / "digest.json"
    assert digest_file.is_file()

    # Test CLI dossier and critique subcommands
    cmd_dos = [
        sys.executable,
        str(SCOUT_SCRIPT),
        "dossier",
        "--slug",
        "distributed-consensus",
        "--workspace",
        str(tmp_path),
    ]
    res_dos = subprocess.run(cmd_dos, capture_output=True, text=True)
    assert res_dos.returncode == 0
    assert "Domain Research Dossier" in res_dos.stdout
    assert "AI-Era Landscape & Modern Augmentation" in res_dos.stdout

    cmd_crit = [
        sys.executable,
        str(SCOUT_SCRIPT),
        "critique",
        "--slug",
        "distributed-consensus",
        "--workspace",
        str(tmp_path),
    ]
    res_crit = subprocess.run(cmd_crit, capture_output=True, text=True)
    assert res_crit.returncode == 0
    assert "5-Hat Critical Reflection" in res_crit.stdout


def test_ai_pro_hat_registration():
    """Verify ai_pro_strategist is registered in universal hat registry and listed via CLI."""
    res = subprocess.run([sys.executable, str(SCOUT_SCRIPT), "hats", "--json"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert "ai_pro_strategist" in data["hats"]
    ai_hat = data["hats"]["ai_pro_strategist"]
    assert "AI-Pro" in ai_hat["title"]
    assert "AI era" in ai_hat["stance"]


def test_scout_with_ai_flag(tmp_path: Path):
    """Verify scout --ai activates AI-Pro Strategist hat in multi-hat critique."""
    cmd = [
        sys.executable,
        str(SCOUT_SCRIPT),
        "scout",
        "--slug",
        "tokio-async",
        "--workspace",
        str(tmp_path),
        "--topic",
        "Tokio Async Runtime in Rust",
        "--ai",
        "--json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True
    assert "ai_era" in data["digest"]
    assert "what_has_changed" in data["digest"]["ai_era"]

    critique_file = tmp_path / "research" / "tokio-async" / "five-hats-critique.md"
    assert critique_file.is_file()
    critique_text = critique_file.read_text(encoding="utf-8")
    assert "AI-Pro Strategist & Co-Pilot" in critique_text
    assert "Branch D (AI-Era Transformation & Augmentation)" in critique_text

    dossier_file = tmp_path / "research" / "tokio-async" / "dossier.md"
    assert dossier_file.is_file()
    dossier_text = dossier_file.read_text(encoding="utf-8")
    assert "AI-Era Landscape & Modern Augmentation (The AI-Pro Dimension)" in dossier_text
    assert "What Has Changed in the AI Era" in dossier_text
    assert "Critical Verification & Hallucination Defense" in dossier_text


def test_scout_with_ai_pro_alias(tmp_path: Path):
    """Verify alias --hats ai_pro resolves to ai_pro_strategist lens."""
    cmd = [
        sys.executable,
        str(SCOUT_SCRIPT),
        "scout",
        "--slug",
        "data-structures",
        "--workspace",
        str(tmp_path),
        "--topic",
        "Algorithms & Data Structures",
        "--hats",
        "applied_practitioner,ai_pro",
        "--json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0

    critique_file = tmp_path / "research" / "data-structures" / "five-hats-critique.md"
    assert critique_file.is_file()
    critique_text = critique_file.read_text(encoding="utf-8")
    assert "Hat 2: AI-Pro Strategist & Co-Pilot" in critique_text


def test_zero_bmad_references_in_tc_research():
    """Verify zero BMad references across scout script and tc-research skill prompt."""
    for path in [SCOUT_SCRIPT, SKILL_FILE]:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\bbmad\b", text, re.IGNORECASE), f"Found BMad in {path}"
