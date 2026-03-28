"""Contract tests for hosted deployment / authz documentation (backlog acceptance criteria)."""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOSTED_DOC = _REPO_ROOT / "docs" / "HOSTED_DEPLOYMENT_AUTHZ.md"
_README = _REPO_ROOT / "README.md"


def test_hosted_deployment_authz_doc_exists() -> None:
    assert _HOSTED_DOC.is_file()


def test_hosted_deployment_authz_lists_topologies_t1_t5() -> None:
    text = _HOSTED_DOC.read_text(encoding="utf-8")
    for tid in ("T1", "T2", "T3", "T4", "T5"):
        assert re.search(rf"\*\*{re.escape(tid)}\*\*", text), (
            f"expected topology row marker **{tid}** in {_HOSTED_DOC}"
        )
    assert "Required controls" in text or "required controls" in text.lower()


def test_hosted_deployment_authz_upstream_links() -> None:
    text = _HOSTED_DOC.read_text(encoding="utf-8")
    assert "docs.langchain.com/oss/python/langgraph/persistence" in text
    assert "github.com/langchain-ai/langgraph/security" in text
    assert "pypi.org/project/replayt" in text
    assert "GHSA-g48c-2wqr-h844" in text


def test_hosted_deployment_authz_sample_warning_section() -> None:
    text = _HOSTED_DOC.read_text(encoding="utf-8")
    assert "Samples and permissive defaults" in text
    assert "Warning" in text
    assert "Checkpointer" in text or "checkpointer" in text


def test_readme_usage_warns_without_production_checkpointer() -> None:
    readme = _README.read_text(encoding="utf-8")
    assert "HOSTED_DEPLOYMENT_AUTHZ.md" in readme
    assert "Checkpointer" in readme
    assert "production" in readme.lower()
