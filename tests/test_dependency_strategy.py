"""Tests for dependency strategy and version constraints."""

import re
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PYPROJECT = _REPO_ROOT / "pyproject.toml"


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


def test_compatibility_update_issue_template_present():
    path = _REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "compatibility_update.md"
    assert path.is_file()
    assert "Compatibility Update" in path.read_text(encoding="utf-8")


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
        assert version_parts >= (0, 4, 0), f"replayt {replayt_version} is below minimum 0.4.0"
        
        # Check upper bound (< 0.5.0)
        assert version_parts < (0, 5, 0), f"replayt {replayt_version} exceeds upper bound < 0.5.0"
    except ImportError:
        pytest.skip("replayt not installed")


def test_langgraph_version_constraint():
    """Test that langgraph version meets specified constraints."""
    try:
        langgraph_version = version("langgraph")
        # Parse version string (e.g., "1.1.3" -> (1, 1, 3))
        version_parts = tuple(map(int, langgraph_version.split(".")[:3]))
        
        # Check minimum version (>= 1.1.0)
        assert version_parts >= (1, 1, 0), f"langgraph {langgraph_version} is below minimum 1.1.0"
        
        # Check upper bound (< 1.2.0)
        assert version_parts < (1, 2, 0), f"langgraph {langgraph_version} exceeds upper bound < 1.2.0"
    except ImportError:
        pytest.skip("langgraph not installed")


def test_dev_dependencies_available():
    """Test that development dependencies are available for testing."""
    # This test ensures pytest is available (listed in dev dependencies)
    import pytest as pytest_module
    assert pytest_module is not None
