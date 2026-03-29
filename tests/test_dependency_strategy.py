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

# §6 maintainer playbook in DEPENDENCY_LOCK_STRATEGY.md — CONTRIBUTING / DEPENDENCY_AUDIT link here.
_PIP_AUDIT_PLAYBOOK_HEADING = (
    "### pip-audit / `supply-chain` job failure triage (maintainer playbook)"
)
_PIP_AUDIT_PLAYBOOK_ANCHOR = "#pip-audit--supply-chain-job-failure-triage-maintainer-playbook"


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
    dev_only = {"pytest", "ruff", "pip-audit", "mypy"}
    runtime_names = {_pep508_name(req) for req in project["dependencies"]}
    assert dev_only.isdisjoint(runtime_names), (
        "runtime dependencies must not list dev-only tools"
    )


def test_pyproject_dev_extra_lists_contributor_tooling():
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    dev = data["project"]["optional-dependencies"]["dev"]
    names = {_pep508_name(req) for req in dev}
    assert {"pytest", "ruff", "pip-audit", "mypy", "langgraph-checkpoint-sqlite"}.issubset(
        names
    )


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


def test_ci_workflow_matrix_includes_python_3_11_through_3_13():
    """Jobs that pin Python must exercise 3.11, 3.12, and 3.13 (BACKLOG_PYTHON_313_CI_MATRIX P2)."""
    ci_path = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
    text = ci_path.read_text(encoding="utf-8")
    blocks = re.findall(r"python-version:\s*\[(.*?)\]", text, flags=re.DOTALL)
    assert blocks, "expected python-version matrix lists in .github/workflows/ci.yml"
    for block in blocks:
        for minor in ("3.11", "3.12", "3.13"):
            quoted = f'"{minor}"'
            assert quoted in block, (
                f"CI matrix block must include {quoted} (got {block.strip()!r})"
            )


def _assert_substrings_in_order(text: str, needles: tuple[str, ...]) -> None:
    pos = 0
    for needle in needles:
        idx = text.find(needle, pos)
        assert idx != -1, f"expected {needle!r} after offset {pos}"
        pos = idx + len(needle)


def test_uv_lock_refresh_workflow_matches_ci_uv_pin_and_pip_audit():
    """BACKLOG_UV_LOCK_REFRESH_WORKFLOW L3/L5: same uv version and pip-audit invocation as ci.yml."""
    ci_path = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
    refresh_path = _REPO_ROOT / ".github" / "workflows" / "uv-lock-refresh.yml"
    assert refresh_path.is_file(), "expected .github/workflows/uv-lock-refresh.yml"
    ci_text = ci_path.read_text(encoding="utf-8")
    refresh_text = refresh_path.read_text(encoding="utf-8")
    uv_pin = 'version: "0.11.2"'
    assert uv_pin in ci_text
    assert uv_pin in refresh_text
    audit = "uv run pip-audit --ignore-vuln CVE-2026-4539 --desc"
    assert f"run: {audit}" in ci_text
    assert f"run: {audit}" in refresh_text


def test_uv_lock_refresh_workflow_validation_order_and_scope():
    """L1–L4, L7, L10: regen → frozen → audit → test trio; schedule + dispatch; no demo extra."""
    refresh_path = _REPO_ROOT / ".github" / "workflows" / "uv-lock-refresh.yml"
    text = refresh_path.read_text(encoding="utf-8")
    assert "schedule:" in text
    assert "cron:" in text
    assert "workflow_dispatch:" in text
    assert "--extra demo" not in text
    assert "--all-extras" not in text
    _assert_substrings_in_order(
        text,
        (
            "uv sync --extra dev",
            "uv sync --frozen --extra dev",
            "uv run pip-audit --ignore-vuln CVE-2026-4539 --desc",
            "uv run pytest",
            "uv run ruff check src tests",
            "uv run mypy -p replayt_langgraph_bridge",
        ),
    )
    assert "permissions:" in text
    assert "pull-requests: write" in text
    assert "contents: write" in text
    assert "add-paths: uv.lock" in text


def test_ci_workflow_installs_dev_without_demo_extra():
    """Primary CI must mirror integrators: [dev] only from lock, never [demo] or --all-extras."""
    ci_path = _REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file(), "expected .github/workflows/ci.yml"
    text = ci_path.read_text(encoding="utf-8")
    assert "uv run mypy -p replayt_langgraph_bridge" in text, (
        "CI must run the same mypy smoke as CONTRIBUTING (PEP 561 backlog A2)"
    )
    assert "uv sync" in text
    assert "--frozen" in text
    assert "--extra dev" in text
    assert "--extra demo" not in text, (
        "CI default jobs must not install the demo extra (credential-free test path per MISSION / "
        "DESIGN_PRINCIPLES S4)"
    )
    assert "--all-extras" not in text, (
        "CI must not use uv --all-extras (that would pull the demo extra into the default path)"
    )
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


def test_dependency_lock_strategy_has_pip_audit_supply_chain_playbook():
    """Lock §6 SLA-style triage section so maintainer links stay valid."""
    path = _REPO_ROOT / "docs" / "DEPENDENCY_LOCK_STRATEGY.md"
    text = path.read_text(encoding="utf-8")
    assert _PIP_AUDIT_PLAYBOOK_HEADING in text, (
        "docs/DEPENDENCY_LOCK_STRATEGY.md must keep the §6 playbook heading "
        "(CONTRIBUTING and DEPENDENCY_AUDIT use this anchor)"
    )
    assert "**Never** add **`--ignore-vuln`**" in text, (
        "playbook must retain the rule: no CI ignore without DEPENDENCY_AUDIT documentation"
    )


def test_contributing_links_pip_audit_playbook_anchor():
    path = _REPO_ROOT / "CONTRIBUTING.md"
    text = path.read_text(encoding="utf-8")
    needle = f"docs/DEPENDENCY_LOCK_STRATEGY.md{_PIP_AUDIT_PLAYBOOK_ANCHOR}"
    assert needle in text, (
        "CONTRIBUTING.md must link maintainers to the playbook with the stable GitHub/MkDocs anchor"
    )


def test_dependency_audit_links_pip_audit_playbook_anchor():
    path = _REPO_ROOT / "docs" / "DEPENDENCY_AUDIT.md"
    text = path.read_text(encoding="utf-8")
    needle = f"DEPENDENCY_LOCK_STRATEGY.md{_PIP_AUDIT_PLAYBOOK_ANCHOR}"
    assert needle in text, (
        "DEPENDENCY_AUDIT.md must reference the playbook anchor for supply-chain triage"
    )


def test_uv_lockfile_committed_for_dev_install():
    lock_path = _REPO_ROOT / "uv.lock"
    assert lock_path.is_file(), "expected uv.lock at repository root for frozen CI installs"
    text = lock_path.read_text(encoding="utf-8")
    assert text.startswith("version = "), "uv.lock should be a uv TOML lockfile"
    assert "requires-python" in text
    assert "replayt-langgraph-bridge" in text
    assert 'name = "pytest"' in text
    assert 'name = "mypy"' in text


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
