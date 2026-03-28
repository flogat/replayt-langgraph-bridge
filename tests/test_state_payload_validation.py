"""Tests for inbound bridge state validation (STATE_PAYLOAD_VALIDATION.md §7).

Graph + ``MemorySaver`` cases also trace checkpoint behavior to ``docs/CHECKPOINT_PERSISTENCE.md`` §6.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver
from replayt.persistence import JSONLStore
from replayt.runner import Runner
from replayt.workflow import Workflow

from replayt_langgraph_bridge import (
    BridgeStateValidationError,
    compile_replayt_workflow,
    initial_bridge_state,
)
from replayt_langgraph_bridge.state_validation import (
    MAX_CONTEXT_STRING_BYTES,
    validate_inbound_bridge_state,
    validate_input_checkpoint_channel_values,
)


def _deep_nest_dict(levels: int) -> dict:
    root: dict = {}
    cur = root
    for _ in range(levels - 1):
        nxt: dict = {}
        cur["k"] = nxt
        cur = nxt
    cur["k"] = 0
    return root


def test_rejects_excessive_nesting() -> None:
    with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
        validate_inbound_bridge_state(
            {"context": {"a": _deep_nest_dict(33)}, "replayt_next": ""}
        )


def test_rejects_oversized_total_string_bytes() -> None:
    s = "x" * (MAX_CONTEXT_STRING_BYTES + 1)
    with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
        validate_inbound_bridge_state({"context": {"s": s}, "replayt_next": ""})


def test_rejects_unknown_schema_version() -> None:
    with pytest.raises(
        BridgeStateValidationError, match="Unsupported bridge state schema version"
    ):
        validate_inbound_bridge_state(
            {
                "context": {},
                "replayt_next": "",
                "bridge_state_schema_version": 999_999,
            }
        )


def test_rejects_dict_cycle_in_context() -> None:
    cyclic: dict = {}
    cyclic["self"] = cyclic
    with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
        validate_inbound_bridge_state({"context": {"c": cyclic}, "replayt_next": ""})


def test_rejects_bytes_in_context() -> None:
    with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
        validate_inbound_bridge_state({"context": {"b": b"no"}, "replayt_next": ""})


def test_rejects_unknown_top_level_keys() -> None:
    with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
        validate_inbound_bridge_state(
            {"context": {}, "replayt_next": "", "extra_field": 1}
        )


def test_initial_bridge_state_validates_context() -> None:
    with pytest.raises(BridgeStateValidationError):
        initial_bridge_state(context={"x": object()})


def test_rejected_first_invoke_no_handler_no_checkpoint(tmp_path: Path) -> None:
    """Bad first input: no handler, no new checkpoint tuple (STATE_PAYLOAD_VALIDATION + CHECKPOINT_PERSISTENCE)."""
    ran = False

    wf = Workflow("val_first")

    @wf.step("a")
    def a(ctx):
        nonlocal ran
        ran = True
        return None

    wf.set_initial("a")

    store = JSONLStore(tmp_path / "e.jsonl")
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())
    saver = MemorySaver()
    graph = compile_replayt_workflow(wf, checkpointer=saver)
    cfg = {"configurable": {"thread_id": "reject-first"}}

    assert len(list(saver.list(cfg))) == 0
    with pytest.raises(BridgeStateValidationError):
        graph.invoke(
            {"context": {"x": object()}, "replayt_next": ""},
            config=cfg,
            context={"runner": runner},
        )
    assert ran is False
    assert len(list(saver.list(cfg))) == 0


def test_resume_with_bad_schema_does_not_advance_checkpoint(tmp_path: Path) -> None:
    """Second ``invoke`` with bad schema does not advance ``MemorySaver`` (CHECKPOINT_PERSISTENCE §5 / STATE_PAYLOAD)."""
    wf = Workflow("val_resume")

    @wf.step("a")
    def a(ctx):
        return None

    wf.set_initial("a")

    store = JSONLStore(tmp_path / "e2.jsonl")
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())
    saver = MemorySaver()
    graph = compile_replayt_workflow(wf, checkpointer=saver)
    cfg = {"configurable": {"thread_id": "resume-bad"}}

    graph.invoke(
        initial_bridge_state(context={"ok": True}),
        config=cfg,
        context={"runner": runner},
    )
    n_before = len(list(saver.list(cfg)))
    tup_before = saver.get_tuple(cfg)
    assert tup_before is not None
    before_id = tup_before.checkpoint["id"]
    assert "bridge_state_schema_version" not in tup_before.checkpoint["channel_values"]

    with pytest.raises(BridgeStateValidationError):
        graph.invoke(
            {
                "context": {},
                "replayt_next": "",
                "bridge_state_schema_version": 999_999,
            },
            config=cfg,
            context={"runner": runner},
        )

    assert len(list(saver.list(cfg))) == n_before
    tup_after = saver.get_tuple(cfg)
    assert tup_after is not None
    assert tup_after.checkpoint["id"] == before_id
    assert "bridge_state_schema_version" not in tup_after.checkpoint["channel_values"]


def test_input_checkpoint_validation_reads_schema_from___start__() -> None:
    log = logging.getLogger("test_bridge_val")
    cv = {
        "context": {},
        "replayt_next": "",
        "__start__": {"bridge_state_schema_version": 999_999},
    }
    with pytest.raises(
        BridgeStateValidationError, match="Unsupported bridge state schema version"
    ):
        validate_input_checkpoint_channel_values(cv, logger=log)


def test_debug_log_emits_without_payload_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="replayt_langgraph_bridge")
    with pytest.raises(BridgeStateValidationError):
        validate_inbound_bridge_state(
            {"context": {"x": object()}, "replayt_next": ""},
        )
    assert any(
        "bridge state validation failed" in r.getMessage() for r in caplog.records
    )
    joined = " ".join(r.getMessage() for r in caplog.records)
    assert "object at" not in joined
