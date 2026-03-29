"""Lock the stable public surface to ``docs/API.md`` and ``__all__``."""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

import replayt_langgraph_bridge as rb

_REPO_ROOT = Path(__file__).resolve().parent.parent
_API_MD = _REPO_ROOT / "docs" / "API.md"

_STABLE_SYMBOLS_HEADING = "## Stable public symbols (integrator-facing)"
_FIRST_COLUMN_SYMBOL = re.compile(r"^`([^`]+)`$")


def parse_stable_public_symbols_from_api_md(api_md_text: str) -> list[str]:
    """Return symbol names from the **Stable public symbols** table in ``docs/API.md``.

    Normative rules: **docs/BACKLOG_SEMVER_API_EXPORT_AUTOMATION.md** §3 **E2**
    (heading ``## Stable public symbols (integrator-facing)``, markdown table, first column
    is a single inline code span per data row; ignore header and separator rows; do not
    harvest from prose outside that table).
    """
    if _STABLE_SYMBOLS_HEADING not in api_md_text:
        msg = (
            "docs/API.md must contain the Stable public symbols heading "
            f"{_STABLE_SYMBOLS_HEADING!r} (public export set / API.md contract, E2)"
        )
        raise ValueError(msg)

    after_heading = api_md_text.split(_STABLE_SYMBOLS_HEADING, 1)[1]
    next_h2 = re.search(r"^## ", after_heading, re.MULTILINE)
    section = after_heading[: next_h2.start()] if next_h2 else after_heading

    lines = section.splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped.startswith("|"):
            i += 1
            continue

        block: list[str] = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            block.append(lines[i].strip())
            i += 1

        if not re.match(r"^\|\s*Symbol\s*\|", block[0]):
            continue

        if len(block) < 3:
            msg = (
                "docs/API.md Stable public symbols table must have a header row, "
                "a separator row, and at least one data row (E2)"
            )
            raise ValueError(msg)

        symbols: list[str] = []
        for row in block[2:]:
            cells = [c.strip() for c in row.split("|")]
            if len(cells) < 3:
                msg = f"docs/API.md Stable public symbols row has no first column: {row!r} (E2)"
                raise ValueError(msg)
            first_cell = cells[1]
            match = _FIRST_COLUMN_SYMBOL.match(first_cell)
            if match is None:
                msg = (
                    "docs/API.md Stable public symbols: each data row's first column must be "
                    f"exactly one backtick-wrapped symbol (E2); got {first_cell!r} in row {row!r}"
                )
                raise ValueError(msg)
            symbols.append(match.group(1))

        return symbols

    msg = (
        "docs/API.md: no markdown table with header | Symbol | under "
        f"{_STABLE_SYMBOLS_HEADING!r} (E2)"
    )
    raise ValueError(msg)


def test_all_matches_docs_api_stable_table():
    """``__all__`` equals the API.md stable table (machine-verified public export set)."""
    api_text = _API_MD.read_text(encoding="utf-8")
    from_table = parse_stable_public_symbols_from_api_md(api_text)
    if len(from_table) != len(set(from_table)):
        dupes = sorted({n for n in from_table if from_table.count(n) > 1})
        pytest.fail(
            "Public export set / API.md stable table: duplicate symbol rows in docs/API.md "
            f"(E2); duplicated: {dupes!r}"
        )

    from_api_md = frozenset(from_table)
    from_all = frozenset(rb.__all__)
    only_in_all = sorted(from_all - from_api_md)
    only_in_api_md = sorted(from_api_md - from_all)

    assert not only_in_all and not only_in_api_md, (
        "Public export set contract: replayt_langgraph_bridge.__all__ must match the "
        "Stable public symbols table in docs/API.md (BACKLOG_SEMVER_API_EXPORT_AUTOMATION "
        "E1 / E2). Update src/replayt_langgraph_bridge/__init__.py __all__ and/or the table.\n"
        f"only_in_all (in __all__ but not API.md table): {only_in_all}\n"
        f"only_in_api_md (in API.md table but not __all__): {only_in_api_md}"
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
