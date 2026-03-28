"""Tests for dependency strategy and version constraints."""

import re
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PYPROJECT = _REPO_ROOT / "pyproject.toml"

# PEP 503-normalized PyPI names whose primary purpose is vendor LLM HTTP/API clients.
# Keep aligned with [project.optional-dependencies] demo and DESIGN_PRINCIPLES; never in core or dev.
_LLM_VENDOR_CLIENT_DENYLIST: frozenset[str] = frozenset(
    {
        "openai",
        "anthropic",
        "langchain-openai",
        "langchain-anthropic",
    }
)

# Expected members of the demo extra (must match pyproject.toml demo list).
_DEMO_EXTRA_EXPECTED_NAMES: frozenset[str] = frozenset(_LLM_VENDOR_CLIENT_DENYLIST)


def _pep508_name(requirement: str) -> str:
    m = re.match(r"^\s*([A-Za-z0-9_.-]+)", requirement)
    assert m is not None, f"unparseable requirement: {requirement!r}"
    return m.group(1).lower()


def test_pyproject_matches_documented_runtime_contract():
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    project = data["project"]
    assert project["requires-python"] == ">=3.11"
    assert project["dependencies"] == [
        "replayt>=0.4.0,<0.5",
        "langgraph>=1.1.0,<1.2",
    ]
    dev_only = {"pytest", "ruff", "pip-audit"}
    runtime_names = {_pep508_name(req) for req in project["dependencies"]}
    assert dev_only.isdisjoint(runtime_names), (
        "runtime dependencies must not list dev-only tools"
    )


def test_pyproject_dev_extra_lists_contributor_tooling():
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    dev = data["project"]["optional-dependencies"]["dev"]
    names = {_pep508_name(req) for req in dev}
    assert {"pytest", "ruff", "pip-audit"}.issubset(names)


def test_core_dependencies_exclude_llm_vendor_clients():
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    core = {_pep508_name(req) for req in data["project"]["dependencies"]}
    blocked = sorted(core & _LLM_VENDOR_CLIENT_DENYLIST)
    assert not blocked, (
        "LLM vendor client packages must not appear in [project.dependencies]; "
        f"use [project.optional-dependencies] demo instead: {blocked}"
    )


def test_dev_extra_excludes_llm_vendor_clients():
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    dev = {_pep508_name(req) for req in data["project"]["optional-dependencies"]["dev"]}
    blocked = sorted(dev & _LLM_VENDOR_CLIENT_DENYLIST)
    assert not blocked, (
        "LLM vendor client packages belong in the demo extra, not dev: " + ", ".join(blocked)
    )


def test_demo_extra_lists_only_expected_llm_vendor_clients():
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    demo = data["project"]["optional-dependencies"]["demo"]
    names = {_pep508_name(req) for req in demo}
    assert names == _DEMO_EXTRA_EXPECTED_NAMES, (
        "demo extra must match _DEMO_EXTRA_EXPECTED_NAMES in test_dependency_strategy.py "
        f"(got {sorted(names)}, expected {sorted(_DEMO_EXTRA_EXPECTED_NAMES)})"
    )
    unknown = names - _LLM_VENDOR_CLIENT_DENYLIST
    assert not unknown, (
        "Add new demo LLM packages to _LLM_VENDOR_CLIENT_DENYLIST or they bypass the denylist contract: "
        + ", ".join(sorted(unknown))
    )


def test_compatibility_update_issue_template_present():
    path = _REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "compatibility_update.md"
    assert path.is_file()
    assert "Compatibility Update" in path.read_text(encoding="utf-8")


def test_ci_workflow_installs_dev_without_demo_extra():
    """Primary CI must mirror integrators: editable install uses [dev] only, never [demo]."""
    ci_path = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file(), "expected .github/workflows/ci.yml"
    text = ci_path.read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("pip install"):
            continue
        assert "[demo]" not in line, (
            "CI must not install the demo extra by default (no live LLM client deps in the "
            f"default test path): {line!r}"
        )
        if "-e" in line and ".[" in line:
            assert "[dev]" in line, (
                "Editable project installs in CI must use the dev extra: " + line
            )


def test_python_version_requirement():
    """Test that Python version meets minimum requirement."""
    python_version = sys.version_info
    assert python_version >= (3, 11), "Python 3.11+ is required"


def test_replayt_version_constraint():
    """Test that replayt version meets specified constraints."""
    try:
        replayt_version = version("replayt")
        # Parse version string (e.g., "0.4.2" -> (0, 4, 2))
        version_parts = tuple(map(int, replayt_version.split(".")[:3]))

        # Check minimum version (>= 0.4.0)
        assert version_parts >= (0, 4, 0), (
            f"replayt {replayt_version} is below minimum 0.4.0"
        )

        # Check upper bound (< 0.5.0)
        assert version_parts < (0, 5, 0), (
            f"replayt {replayt_version} exceeds upper bound < 0.5.0"
        )
    except ImportError:
        pytest.skip("replayt not installed")


def test_langgraph_version_constraint():
    """Test that langgraph version meets specified constraints."""
    try:
        langgraph_version = version("langgraph")
        # Parse version string (e.g., "1.1.3" -> (1, 1, 3))
        version_parts = tuple(map(int, langgraph_version.split(".")[:3]))

        # Check minimum version (>= 1.1.0)
        assert version_parts >= (1, 1, 0), (
            f"langgraph {langgraph_version} is below minimum 1.1.0"
        )

        # Check upper bound (< 1.2.0)
        assert version_parts < (1, 2, 0), (
            f"langgraph {langgraph_version} exceeds upper bound < 1.2.0"
        )
    except ImportError:
        pytest.skip("langgraph not installed")


def test_dev_dependencies_available():
    """Test that development dependencies are available for testing."""
    # This test ensures pytest is available (listed in dev dependencies)
    import pytest as pytest_module

    assert pytest_module is not None
