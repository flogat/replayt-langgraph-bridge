"""Lock the stable public surface to ``docs/API.md`` and ``__all__``."""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

import replayt_langgraph_bridge as rb

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Stable table in docs/API.md (integrator-facing); keep sets equal on change.
_STABLE_PUBLIC_NAMES: frozenset[str] = frozenset(
    {
        "BridgeStateValidationError",
        "RedactorHook",
        "ReplaytBridgeState",
        "__version__",
        "compile_replayt_workflow",
        "get_bridge_logger",
        "initial_bridge_state",
        "redact_log_attachment",
    }
)


def test_all_matches_docs_api_stable_table():
    assert set(rb.__all__) == _STABLE_PUBLIC_NAMES, (
        "replayt_langgraph_bridge.__all__ must match the stable table in docs/API.md "
        f"(expected {_STABLE_PUBLIC_NAMES!r}, got {set(rb.__all__)!r})"
    )
    assert len(rb.__all__) == len(set(rb.__all__)), "__all__ must not list duplicates"


def test_each_export_is_defined_on_package():
    for name in rb.__all__:
        assert hasattr(rb, name), f"missing export {name!r} on replayt_langgraph_bridge"


@pytest.mark.parametrize("name", sorted(rb.__all__))
def test_each_stable_export_has_documentation(name: str):
    obj = getattr(rb, name)
    if name == "__version__":
        assert isinstance(obj, str) and obj.strip(), "__version__ must be a non-empty str"
        return
    if name == "RedactorHook":
        mod_doc = inspect.getdoc(rb.redaction) or ""
        assert "RedactorHook" in mod_doc, (
            "docs/API.md requires module-level documentation for RedactorHook "
            "(see replayt_langgraph_bridge.redaction module docstring)"
        )
        return
    doc = inspect.getdoc(obj)
    assert doc, f"{name} must have a docstring per docs/API.md builder checklist"


def test_readme_usage_does_not_import_bridge_submodules():
    text = (_REPO_ROOT / "README.md").read_text(encoding="utf-8")
    usage = text.split("## Usage", 1)[1]
    fence = re.search(r"```python\n(.*?)```", usage, re.DOTALL)
    assert fence is not None, "README must have a python code block under ## Usage"
    body = fence.group(1)
    assert re.search(
        r"^\s*from\s+replayt_langgraph_bridge\s+import\b", body, re.MULTILINE
    ), "README Usage must import the bridge from the package root"
    assert not re.search(
        r"replayt_langgraph_bridge\.(graph|state_validation|redaction|bridge_log)\b",
        body,
    ), "README Usage must not import replayt_langgraph_bridge submodules"
