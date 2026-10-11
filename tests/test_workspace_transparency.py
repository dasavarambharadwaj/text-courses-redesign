"""tests/test_workspace_transparency.py — Test suite for root research directory and workspace guide."""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP_SCRIPT = REPO_ROOT / "_tc" / "scripts" / "bootstrapper.py"


def test_bootstrap_scaffolds_research_dir_and_guide(tmp_path: Path):
    """Verify bootstrapper scaffolds research/ and WORKSPACE_GUIDE.md."""
    ws = tmp_path / "transparency_ws"
    cmd = [sys.executable, str(BOOTSTRAP_SCRIPT), "bootstrap", "--path", str(ws)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["ok"] is True

    # Check directory structure
    assert (ws / "research").is_dir()
    assert (ws / "sources").is_dir()
    assert (ws / "courses").is_dir()
    assert (ws / "profile").is_dir()
    assert (ws / "roadmap").is_dir()
    assert (ws / "portfolio").is_dir()
    assert (ws / "_tc").is_dir()

    # Check guide
    guide_path = ws / "WORKSPACE_GUIDE.md"
    assert guide_path.is_file()
    guide_text = guide_path.read_text(encoding="utf-8")
    assert "courses/" in guide_text
    assert "research/" in guide_text
    assert "roadmap/" in guide_text
    assert "profile/" in guide_text
    assert "portfolio/" in guide_text
    assert "_tc/" in guide_text
    assert "/tc-init" in guide_text
    assert "/tc-create" in guide_text
    assert "/tc-teach" in guide_text


def test_zero_bmad_references_in_bootstrapper():
    """Verify zero BMad references in bootstrapper script."""
    text = BOOTSTRAP_SCRIPT.read_text(encoding="utf-8")
    assert not re.search(r"\bbmad\b", text, re.IGNORECASE)
