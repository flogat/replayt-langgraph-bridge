"""Tests for inbound bridge state validation (STATE_PAYLOAD_VALIDATION.md §7, §9).

Graph + ``MemorySaver`` cases trace checkpoint behavior to ``docs/CHECKPOINT_PERSISTENCE.md`` §7.
Parametrized boundaries and schema cases follow **STATE_PAYLOAD_VALIDATION §9.2–§9.5**.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

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
    MAX_CONTEXT_NESTING_DEPTH,
    MAX_CONTEXT_STRING_BYTES,
    MAX_CONTEXT_TOP_LEVEL_KEYS,
    MAX_CONTEXT_WALK_NODES,
    MAX_REPLAYT_NEXT_LEN,
    SUPPORTED_BRIDGE_STATE_SCHEMA_VERSIONS,
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


def _context_at_depth_limit() -> dict[str, Any]:
    """STATE_PAYLOAD_VALIDATION §9.2 — deepest leaf at ``MAX_CONTEXT_NESTING_DEPTH``."""
    return {"a": _deep_nest_dict(MAX_CONTEXT_NESTING_DEPTH)}


def _context_over_depth_limit() -> dict[str, Any]:
    return {"a": _deep_nest_dict(MAX_CONTEXT_NESTING_DEPTH + 1)}


def _context_string_bytes_total(n_bytes: int) -> dict[str, Any]:
    """Single value string; only ``context`` values contribute to the string byte tally."""
    return {"s": "x" * n_bytes}


def _context_walk_node_count(n_nodes: int) -> dict[str, Any]:
    """STATE_PAYLOAD_VALIDATION §9.2 — walk nodes via list elements (no large string total)."""
    return {"L": [0] * n_nodes}


def _context_top_level_key_count(n_keys: int) -> dict[str, Any]:
    return {str(i): 0 for i in range(n_keys)}


def _minimal_state(context: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {"context": context, "replayt_next": "", **extra}


@pytest.mark.parametrize(
    ("state", "expect_ok"),
    [
        pytest.param(
            _minimal_state(_context_at_depth_limit()), True, id="nesting_at_limit"
        ),
        pytest.param(
            _minimal_state(_context_over_depth_limit()),
            False,
            id="nesting_over_limit",
        ),
        pytest.param(
            _minimal_state(_context_string_bytes_total(MAX_CONTEXT_STRING_BYTES)),
            True,
            id="string_bytes_at_limit",
        ),
        pytest.param(
            _minimal_state(_context_string_bytes_total(MAX_CONTEXT_STRING_BYTES + 1)),
            False,
            id="string_bytes_over_limit",
        ),
        pytest.param(
            _minimal_state(_context_walk_node_count(MAX_CONTEXT_WALK_NODES)),
            True,
            id="walk_nodes_at_limit",
        ),
        pytest.param(
            _minimal_state(_context_walk_node_count(MAX_CONTEXT_WALK_NODES + 1)),
            False,
            id="walk_nodes_over_limit",
        ),
        pytest.param(
            _minimal_state(_context_top_level_key_count(MAX_CONTEXT_TOP_LEVEL_KEYS)),
            True,
            id="top_level_keys_at_limit",
        ),
        pytest.param(
            _minimal_state(
                _context_top_level_key_count(MAX_CONTEXT_TOP_LEVEL_KEYS + 1)
            ),
            False,
            id="top_level_keys_over_limit",
        ),
        pytest.param(
            {"context": {}, "replayt_next": "x" * MAX_REPLAYT_NEXT_LEN},
            True,
            id="replayt_next_at_limit",
        ),
        pytest.param(
            {"context": {}, "replayt_next": "x" * (MAX_REPLAYT_NEXT_LEN + 1)},
            False,
            id="replayt_next_over_limit",
        ),
    ],
)
def test_boundary_size_parametrized(state: dict[str, Any], expect_ok: bool) -> None:
    """STATE_PAYLOAD_VALIDATION §9.2 — all five §4 size rows (limits from ``state_validation`` exports)."""
    if expect_ok:
        validate_inbound_bridge_state(state)
    else:
        with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
            validate_inbound_bridge_state(state)


@pytest.mark.parametrize(
    "unsupported_version",
    [
        0,
        max(SUPPORTED_BRIDGE_STATE_SCHEMA_VERSIONS) + 1,
        999_999,
    ],
)
def test_unsupported_schema_version_rejected(unsupported_version: int) -> None:
    """STATE_PAYLOAD_VALIDATION §9.3 — explicit integer not in ``SUPPORTED_BRIDGE_STATE_SCHEMA_VERSIONS``."""
    with pytest.raises(
        BridgeStateValidationError,
        match="Unsupported bridge state schema version",
    ):
        validate_inbound_bridge_state(
            _minimal_state(
                {},
                bridge_state_schema_version=unsupported_version,
            )
        )


@pytest.mark.parametrize(
    "bad_schema_value",
    [
        pytest.param(True, id="bool"),
        pytest.param("1", id="str"),
        pytest.param(1.0, id="float"),
        pytest.param(None, id="none"),
        pytest.param([1], id="list"),
        pytest.param({}, id="dict"),
    ],
)
def test_schema_version_wrong_type_top_level_rejected(bad_schema_value: Any) -> None:
    """STATE_PAYLOAD_VALIDATION §9.3 — ``bridge_state_schema_version`` wrong type (top-level state)."""
    with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
        validate_inbound_bridge_state(
            _minimal_state({}, bridge_state_schema_version=bad_schema_value)
        )


@pytest.mark.parametrize(
    "bad_schema_value",
    [
        pytest.param(True, id="bool"),
        pytest.param("1", id="str"),
        pytest.param(1.0, id="float"),
        pytest.param(None, id="none"),
        pytest.param([1], id="list"),
        pytest.param({}, id="dict"),
    ],
)
def test_schema_version_wrong_type___start___channel_rejected(
    bad_schema_value: Any,
) -> None:
    """STATE_PAYLOAD_VALIDATION §9.3 — schema from ``__start__`` merge path (checkpoint channel values)."""
    log = logging.getLogger("test_bridge_val_schema_type")
    cv = {
        "context": {},
        "replayt_next": "",
        "__start__": {"bridge_state_schema_version": bad_schema_value},
    }
    with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
        validate_input_checkpoint_channel_values(cv, logger=log)


@pytest.mark.parametrize(
    "explicit_version",
    [pytest.param(None, id="omitted"), pytest.param(1, id="explicit_1")],
)
def test_supported_schema_version_passes(explicit_version: int | None) -> None:
    """STATE_PAYLOAD_VALIDATION §9.3 — omitted defaults to 1; explicit ``1`` passes."""
    extra: dict[str, Any] = {}
    if explicit_version is not None:
        extra["bridge_state_schema_version"] = explicit_version
    validate_inbound_bridge_state(_minimal_state({}, **extra))


@pytest.mark.parametrize(
    "channel_patch",
    [
        pytest.param(
            {"bridge_state_schema_version": 999_999},
            id="top_level_channel_key",
        ),
        pytest.param(
            {"__start__": {"bridge_state_schema_version": 999_999}},
            id="start_channel_nested",
        ),
    ],
)
def test_input_checkpoint_unsupported_schema_from_channels(
    channel_patch: dict[str, Any],
) -> None:
    """STATE_PAYLOAD_VALIDATION §9.3 — unsupported version via checkpoint channel layout."""
    log = logging.getLogger("test_bridge_val_ckpt_schema")
    cv = {"context": {}, "replayt_next": "", **channel_patch}
    with pytest.raises(
        BridgeStateValidationError,
        match="Unsupported bridge state schema version",
    ):
        validate_input_checkpoint_channel_values(cv, logger=log)


@pytest.mark.parametrize(
    "case",
    [
        pytest.param("first_invoke", id="first_invoke_rejection"),
        pytest.param("resume_invalid_schema", id="resume_rejection"),
    ],
)
def test_checkpoint_non_mutation_memory_saver(tmp_path: Path, case: str) -> None:
    """STATE_PAYLOAD_VALIDATION §9.4 / §6 — MemorySaver unchanged after rejected inbound state."""
    ran = 0

    wf = Workflow(f"val_ckpt_{case}")

    @wf.step("a")
    def a(ctx):
        nonlocal ran
        ran += 1
        return None

    wf.set_initial("a")

    store = JSONLStore(tmp_path / f"{case}.jsonl")
    runner = Runner(wf, store)
    runner.run_id = str(uuid.uuid4())
    saver = MemorySaver()
    graph = compile_replayt_workflow(wf, checkpointer=saver)
    cfg = {"configurable": {"thread_id": f"nm-{case}"}}

    if case == "first_invoke":
        assert len(list(saver.list(cfg))) == 0, (
            "STATE_PAYLOAD_VALIDATION §6: no checkpoint before first invoke"
        )
        with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
            graph.invoke(
                {"context": {"x": object()}, "replayt_next": ""},
                config=cfg,
                context={"runner": runner},
            )
        assert ran == 0, (
            "STATE_PAYLOAD_VALIDATION §9.4: no handler on first invoke rejection"
        )
        assert len(list(saver.list(cfg))) == 0, (
            "STATE_PAYLOAD_VALIDATION §6: no durable checkpoint after rejected first invoke"
        )
        return

    graph.invoke(
        initial_bridge_state(context={"ok": True}),
        config=cfg,
        context={"runner": runner},
    )
    assert ran == 1
    n_before = len(list(saver.list(cfg)))
    tup_before = saver.get_tuple(cfg)
    assert tup_before is not None
    before_id = tup_before.checkpoint["id"]
    assert "bridge_state_schema_version" not in tup_before.checkpoint["channel_values"]

    with pytest.raises(
        BridgeStateValidationError,
        match="Unsupported bridge state schema version",
    ):
        graph.invoke(
            {
                "context": {},
                "replayt_next": "",
                "bridge_state_schema_version": 999_999,
            },
            config=cfg,
            context={"runner": runner},
        )

    assert ran == 1, (
        "STATE_PAYLOAD_VALIDATION §9.4: handler does not run again on rejected resume"
    )
    assert len(list(saver.list(cfg))) == n_before, (
        "STATE_PAYLOAD_VALIDATION §9.4: checkpoint count unchanged after rejected resume"
    )
    tup_after = saver.get_tuple(cfg)
    assert tup_after is not None
    assert tup_after.checkpoint["id"] == before_id, (
        "STATE_PAYLOAD_VALIDATION §6: checkpoint id unchanged after rejected resume"
    )
    assert (
        "bridge_state_schema_version" not in tup_after.checkpoint["channel_values"]
    ), (
        "STATE_PAYLOAD_VALIDATION §9.4: channel_values not corrupted by bad schema payload"
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
    with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
        initial_bridge_state(context={"x": object()})


def test_debug_log_emits_without_payload_values(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """STATE_PAYLOAD_VALIDATION §9.5 — DEBUG must not embed raw disallowed object repr."""
    caplog.set_level(logging.DEBUG, logger="replayt_langgraph_bridge")
    with pytest.raises(BridgeStateValidationError, match="Invalid bridge state"):
        validate_inbound_bridge_state(
            {"context": {"x": object()}, "replayt_next": ""},
        )
    assert any(
        "bridge state validation failed" in r.getMessage() for r in caplog.records
    ), "STATE_PAYLOAD_VALIDATION §9.5: debug reason is logged"
    joined = " ".join(r.getMessage() for r in caplog.records)
    assert "object at" not in joined, (
        "STATE_PAYLOAD_VALIDATION §9.5: no raw payload value fingerprints in debug text"
    )
