"""Contract tests for `.gitignore` vs **docs/GITIGNORE_AND_LOCAL_ARTIFACTS.md** (G1–G5, §2–§3).

Uses `git check-ignore` so behavior matches Git, not a second parser.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CONTRIBUTING = _REPO_ROOT / "CONTRIBUTING.md"
_GITIGNORE_SPEC = _REPO_ROOT / "docs" / "GITIGNORE_AND_LOCAL_ARTIFACTS.md"


def _check_ignore(relative_path: str) -> tuple[bool, str]:
    """Return (is_ignored, verbose_line_or_stderr)."""
    proc = subprocess.run(
        ["git", "check-ignore", "-v", relative_path],
        cwd=_REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode == 0:
        line = (proc.stdout or proc.stderr).strip().splitlines()
        return True, line[0] if line else ""
    if proc.returncode == 1:
        return False, ""
    raise AssertionError(
        f"git check-ignore failed for {relative_path!r}: "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_gitignore_blocks_env_and_secret_filenames() -> None:
    """§2.A: common env and key material paths are ignored."""
    for rel in (
        ".env",
        ".env.local",
        ".envrc",
        ".netrc",
        "secrets.pem",
        "bundle.p12",
        "bundle.pfx",
        "id_rsa",
        "id_ed25519",
        "tls.key",
    ):
        ignored, detail = _check_ignore(rel)
        assert ignored, f"expected {rel!r} ignored, got {detail!r}"


def test_gitignore_blocks_direnv_and_local_dev_trees() -> None:
    """§2.A / §2.C: direnv + dev checkpoint dirs."""
    for rel in (".direnv/flake-profile", "local_checkpoints/run.sqlite3", "scratch/out.jsonl"):
        ignored, detail = _check_ignore(rel)
        assert ignored, f"expected {rel!r} ignored, got {detail!r}"


def test_gitignore_blocks_dev_sqlite_suffix() -> None:
    ignored, _ = _check_ignore("my_store.dev.sqlite3")
    assert ignored


def test_gitignore_blocks_orchestration_and_agent_scratch() -> None:
    """§2.B."""
    for rel in (
        ".orchestrator/handoff.md",
        ".cursor/skills/foo/SKILL.md",
        ".aider.conf.yml",
        "alignment_result.json",
        ".alignment_result.json",
    ):
        ignored, detail = _check_ignore(rel)
        assert ignored, f"expected {rel!r} ignored, got {detail!r}"


def test_gitignore_blocks_placeholder_path_tree() -> None:
    """§2.E: literal ``path/`` trees from documentation examples."""
    ignored, detail = _check_ignore("path/to/mistaken_file.txt")
    assert ignored, f"expected placeholder path ignored, got {detail!r}"


def test_gitignore_does_not_hide_packaging_and_ci_paths() -> None:
    """§3: reproducible build + CI files stay visible to Git."""
    for rel in (
        "pyproject.toml",
        "uv.lock",
        ".env.example",
        "src/replayt_langgraph_bridge/__init__.py",
        "tests/test_gitignore_contract.py",
        "docs/GITIGNORE_AND_LOCAL_ARTIFACTS.md",
        ".github/workflows/ci.yml",
        ".github/workflows/uv-lock-refresh.yml",
        "README.md",
        "CONTRIBUTING.md",
    ):
        ignored, detail = _check_ignore(rel)
        assert not ignored, f"expected {rel!r} not ignored, but: {detail!r}"


def test_contributing_links_gitignore_spec() -> None:
    """G3: short checklist points at normative spec."""
    text = _CONTRIBUTING.read_text(encoding="utf-8")
    assert "## What must never be committed" in text
    assert "GITIGNORE_AND_LOCAL_ARTIFACTS.md" in text
    assert "tests/test_gitignore_contract.py" in text


def test_spec_lists_builder_acceptance_g1_through_g5() -> None:
    """Maps to backlog verification table (G5: contract-test drift control)."""
    text = _GITIGNORE_SPEC.read_text(encoding="utf-8")
    for marker in ("**G1**", "**G2**", "**G3**", "**G4**", "**G5**"):
        assert marker in text, f"expected {marker} in GITIGNORE_AND_LOCAL_ARTIFACTS"
