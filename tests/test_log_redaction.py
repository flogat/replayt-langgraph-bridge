from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver
from replayt.persistence import JSONLStore
from replayt.runner import Runner
from replayt.workflow import Workflow

from replayt_langgraph_bridge import compile_replayt_workflow, initial_bridge_state
from replayt_langgraph_bridge.bridge_log import emit_bridge_record, get_bridge_logger
from replayt_langgraph_bridge.redaction import redact_log_attachment, redact_log_message


SECRET_SK = "sk-test-0123456789abcdef"


class _ListHandler(logging.Handler):
    def __init__(self, buf: list[logging.LogRecord]) -> None:
        super().__init__()
        self._buf = buf

    def emit(self, record: logging.LogRecord) -> None:
        self._buf.append(record)


def _record_fingerprint(rec: logging.LogRecord) -> str:
    extra = getattr(rec, "replayt_bridge", {})
    return json.dumps(
        {"message": rec.getMessage(), "replayt_bridge": extra}, sort_keys=True
    )


def test_default_redaction_strips_api_key_value() -> None:
    redacted = redact_log_attachment({"api_key": SECRET_SK, "run_id": "r1"})
    blob = json.dumps(redacted)
    assert SECRET_SK not in blob
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["run_id"] == "r1"


def test_patterns_mask_openai_key_in_allow_listed_message_field() -> None:
    redacted = redact_log_attachment({"message": f"key {SECRET_SK}"})
    blob = json.dumps(redacted)
    assert SECRET_SK not in blob
    assert "[REDACTED]" in blob


def test_patterns_mask_email_in_attachment_string() -> None:
    """PAT_EMAIL: representative PII must not appear in default redacted attachment JSON."""
    redacted = redact_log_attachment({"note": "contact user@example.com ok"})
    blob = json.dumps(redacted)
    assert "user@example.com" not in blob
    assert "[REDACTED]" in blob


def test_emit_bridge_record_no_secret_in_output() -> None:
    buf: list[logging.LogRecord] = []
    log = logging.getLogger("replayt_langgraph_bridge.test_emit")
    log.handlers.clear()
    log.addHandler(_ListHandler(buf))
    log.setLevel(logging.INFO)
    log.propagate = False
    try:
        emit_bridge_record(
            log,
            logging.INFO,
            "hello",
            {"api_key": SECRET_SK, "step": "a"},
            redact=True,
            strict_redact=False,
            redactor=None,
        )
    finally:
        log.removeHandler(log.handlers[0])
        log.propagate = True
    assert len(buf) == 1
    assert SECRET_SK not in _record_fingerprint(buf[0])


def test_custom_redactor_runs_last() -> None:
    def hook(d: dict) -> dict:
        d["integrator_marker"] = 1
        return d

    redacted = redact_log_attachment({"run_id": "x"}, redactor=hook)
    assert redacted["integrator_marker"] == 1
    assert redacted["run_id"] == "x"


def test_redactor_error_sets_flag_and_does_not_leak_secret() -> None:
    def bad(_: dict) -> dict:
        raise RuntimeError("hook failed")

    redacted = redact_log_attachment({"api_key": SECRET_SK}, redactor=bad)
    assert redacted.get("redactor_error") is True
    assert SECRET_SK not in json.dumps(redacted)


def test_strict_redacts_long_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REPLAYT_BRIDGE_STRICT_REDACT", "1")
    long_val = "n" * 300
    redacted = redact_log_attachment({"note": long_val})
    assert redacted["note"] == "[REDACTED]"
    assert long_val not in json.dumps(redacted)


def test_default_keeps_long_low_entropy_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REPLAYT_BRIDGE_STRICT_REDACT", raising=False)
    long_val = "n" * 300
    redacted = redact_log_attachment({"note": long_val})
    assert redacted["note"] == long_val


def test_strict_high_entropy_masks_without_env_param() -> None:
    opaque = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
    redacted = redact_log_attachment({"blob": opaque}, strict_redact=True)
    assert redacted["blob"] == "[REDACTED]"


def test_graph_invoke_log_excludes_secret_from_handler_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("REPLAYT_BRIDGE_STRICT_REDACT", raising=False)

    buf: list[logging.LogRecord] = []
    log = get_bridge_logger()
    h = _ListHandler(buf)
    log.addHandler(h)
    log.setLevel(logging.INFO)
    old_propagate = log.propagate
    log.propagate = False
    try:
        wf = Workflow("sec")

        @wf.step("first")
        def first(ctx):
            ctx.set("api_key", SECRET_SK)
            ctx.set("safe", True)
            return None

        wf.set_initial("first")

        store = JSONLStore(tmp_path / "e.jsonl")
        runner = Runner(wf, store)
        runner.run_id = str(uuid.uuid4())

        graph = compile_replayt_workflow(
            wf, checkpointer=MemorySaver(), bridge_logger=log
        )
        graph.invoke(
            initial_bridge_state(),
            config={"configurable": {"thread_id": "t-sec"}},
            context={"runner": runner},
        )
    finally:
        log.removeHandler(h)
        log.propagate = old_propagate

    joined = "\n".join(_record_fingerprint(r) for r in buf)
    assert SECRET_SK not in joined
    assert "[REDACTED]" in joined


def test_redact_false_emits_warning() -> None:
    buf: list[logging.LogRecord] = []
    log = logging.getLogger("replayt_langgraph_bridge.warn_test")
    log.handlers.clear()
    log.addHandler(_ListHandler(buf))
    log.setLevel(logging.INFO)
    log.propagate = False
    try:
        with pytest.warns(UserWarning, match="redact=False"):
            emit_bridge_record(
                log,
                logging.INFO,
                "x",
                {"api_key": SECRET_SK},
                redact=False,
                strict_redact=False,
                redactor=None,
            )
    finally:
        log.removeHandler(log.handlers[0])
        log.propagate = True
    assert SECRET_SK in json.dumps(getattr(buf[0], "replayt_bridge", {}))


def test_jwt_like_string_redacted_in_message() -> None:
    jwt_like = "aaaa.bbbb.cccccccc"
    out = redact_log_message(f"bearer {jwt_like}")
    assert "aaaa.bbbb" not in out
    assert "[REDACTED]" in out
