"""Contract tests for documented LLM demo scope, shipped sample pointers, and CI defaults.

Maps to **docs/DESIGN_PRINCIPLES.md** — *Product acceptance criteria (verbatim backlog: LLM and secrets posture)* (**S1**, **S2**, **S4**).
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MISSION = _REPO_ROOT / "docs" / "MISSION.md"
_DESIGN_PRINCIPLES = _REPO_ROOT / "docs" / "DESIGN_PRINCIPLES.md"
_README = _REPO_ROOT / "README.md"


def test_mission_states_llm_demo_scope() -> None:
    """S1: MISSION states whether LLM demos are in package scope."""
    text = _MISSION.read_text(encoding="utf-8")
    assert "## LLM demos and optional samples" in text
    assert "outbound vendor LLM API calls" in text
    assert "replayt-langgraph-bridge[demo]" in text


def test_mission_documents_shipped_llm_sample_and_future_work() -> None:
    """S2: committed sample path, ecosystem pointer, and demo packaging."""
    text = _MISSION.read_text(encoding="utf-8")
    assert "examples/llm_node_graph.py" in text
    assert "examples/" in text
    assert "REPLAYT_ECOSYSTEM_IDEA.md" in text
    assert "optional-vendor-llm-samples" in text
    assert "pyproject.toml" in text and "demo" in text


def test_mission_covers_secrets_and_redaction_for_live_model_paths() -> None:
    text = _MISSION.read_text(encoding="utf-8")
    assert "Secrets and redaction" in text
    assert "environment variables" in text
    assert "LOG_REDACTION.md" in text
    assert "DESIGN_PRINCIPLES.md#secrets-policy" in text


def test_design_principles_has_product_acceptance_s1_through_s4() -> None:
    text = _DESIGN_PRINCIPLES.read_text(encoding="utf-8")
    for marker in ("**S1**", "**S2**", "**S3**", "**S4**"):
        assert marker in text, f"expected {marker} in DESIGN_PRINCIPLES LLM posture table"
    assert "credential-free" in text


def test_readme_llm_demos_section_links_normative_docs() -> None:
    text = _README.read_text(encoding="utf-8")
    assert "### LLM demos" in text
    assert "MISSION.md#llm-demos-and-optional-samples-scope" in text
    assert "DESIGN_PRINCIPLES.md#llm-and-demos" in text
    assert "examples/llm_node_graph.py" in text
    assert "BACKLOG_FIRST_PARTY_LLM_SAMPLE.md" in text
