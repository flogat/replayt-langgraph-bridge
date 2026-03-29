"""Contract tests for PEP 561 marker packaging (py.typed in tree and wheel)."""

import shutil
import subprocess
import tempfile
import tomllib
import zipfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PACKAGE_DIR = _REPO_ROOT / "src" / "replayt_langgraph_bridge"
_PYPROJECT = _REPO_ROOT / "pyproject.toml"


def test_py_typed_marker_exists():
    marker = _PACKAGE_DIR / "py.typed"
    assert marker.is_file(), "expected src/replayt_langgraph_bridge/py.typed for PEP 561"


def test_pyproject_setuptools_package_data_includes_py_typed():
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    pkg_data = data.get("tool", {}).get("setuptools", {}).get("package-data", {})
    assert pkg_data.get("replayt_langgraph_bridge") == ["py.typed"], (
        "setuptools must list py.typed so wheels/sdists include the PEP 561 marker"
    )


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv not on PATH (install per CONTRIBUTING.md)")
def test_built_wheel_contains_py_typed():
    """A1 wheel inspection: built artifact includes replayt_langgraph_bridge/py.typed."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [
                "uv",
                "build",
                "--wheel",
                "--out-dir",
                tmp,
            ],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        out = Path(tmp)
        wheels = list(out.glob("*.whl"))
        assert len(wheels) == 1, f"expected exactly one wheel in {tmp}, got {wheels}"
        with zipfile.ZipFile(wheels[0]) as zf:
            names = zf.namelist()
        typed_paths = [
            n
            for n in names
            if n.endswith("replayt_langgraph_bridge/py.typed")
            or n.endswith("replayt_langgraph_bridge/py.typed/")
        ]
        assert typed_paths, (
            "wheel must contain replayt_langgraph_bridge/py.typed (PEP 561); "
            f"got archive members ending in py.typed: {[n for n in names if 'py.typed' in n]}"
        )
