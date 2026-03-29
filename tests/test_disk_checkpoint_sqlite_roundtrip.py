"""Disk-backed LangGraph checkpoint round-trip via SQLite (default CI / ``[dev]``).

Traceability: ``docs/CHECKPOINT_PERSISTENCE.md`` §7 (disk checklist) and
``docs/BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP.md``. Uses ``langgraph-checkpoint-sqlite``
(``SqliteSaver``) under a temp file; no network or ``demo`` extra.

**Boundary proof:** This module uses **re-compile** (two ``compile_replayt_workflow`` calls with
the same on-disk ``SqliteSaver`` and ``thread_id``), not a subprocess. Cross-process resume is
omitted to keep CI fast and deterministic; ``BACKLOG_DISK_CHECKPOINT_SQLITE_ROUNDTRIP.md`` §3.2
allows (B) when (A) is skipped with rationale (this docstring).

**Platform:** Linux is the primary CI target. The test is single-threaded and uses ``tmp_path``
(SQLite under pytest’s temp dir). On Windows/WSL, SQLite locking differs from Linux; integrators
should follow upstream saver docs for concurrent access. This test does not use concurrent writers.
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from replayt.persistence import JSONLStore
from replayt.runner import Runner
from replayt.workflow import Workflow

from replayt_langgraph_bridge import compile_replayt_workflow, initial_bridge_state


def test_sqlite_checkpoint_resume_after_fresh_compile(tmp_path: Path) -> None:
    """Second ``compile_replayt_workflow`` + same ``SqliteSaver`` resumes the same ``thread_id``.

    Proves checkpoint bytes on disk survive a new compiled graph object (CHECKPOINT_PERSISTENCE §7).
    """
    db_path = tmp_path / "checkpoints.sqlite"
    store_path = tmp_path / "replayt_events.jsonl"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    try:
        saver = SqliteSaver(conn)

        wf = Workflow("sqlite_recompile_resume")

        @wf.step("first")
        def first(ctx):
            ctx.set("phase", 1)
            return "second"

        @wf.step("second")
        def second(ctx):
            ctx.set("phase", ctx.get("phase", 0) + 10)
            return None

        wf.set_initial("first")
        wf.note_transition("first", "second")

        store = JSONLStore(store_path)
        runner = Runner(wf, store)
        runner.run_id = str(uuid.uuid4())

        cfg = {"configurable": {"thread_id": "sqlite-recompile-thread"}}

        graph_first = compile_replayt_workflow(
            wf, checkpointer=saver, interrupt_before=["second"]
        )
        out1 = graph_first.invoke(
            initial_bridge_state(context={"seed": True}),
            config=cfg,
            context={"runner": runner},
        )
        assert out1["context"]["seed"] is True, (
            "replayt boundary: first invoke must preserve merged LangGraph context in bridge state"
        )
        assert out1["context"]["phase"] == 1, (
            "replayt boundary: first step must persist RunContext.data through checkpoint boundary"
        )
        assert out1["replayt_next"] == "second", (
            "replayt boundary: interrupt_before second must leave replayt_next pointing at next step"
        )
        assert db_path.is_file(), (
            "checkpoint disk contract: SQLite saver must create the database file on disk"
        )
        assert db_path.stat().st_size > 0, (
            "checkpoint disk contract: first invoke must persist checkpoint bytes to the SQLite file"
        )
        assert len(list(saver.list(cfg))) >= 1, (
            "replayt boundary: SqliteSaver must persist at least one checkpoint for resume"
        )

        graph_second = compile_replayt_workflow(
            wf, checkpointer=saver, interrupt_before=["second"]
        )
        out2 = graph_second.invoke(None, config=cfg, context={"runner": runner})
        assert out2["context"]["phase"] == 11, (
            "replayt boundary: resumed invoke must run second step and accumulate RunContext.data"
        )
        assert out2["replayt_next"] == "", (
            "replayt boundary: terminal step must clear replayt_next after resume"
        )
        assert out2["context"]["seed"] is True, (
            "replayt boundary: resumed run must keep original context keys from first invoke"
        )
    finally:
        conn.close()
