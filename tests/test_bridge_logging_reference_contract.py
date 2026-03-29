"""Stable bridge logger qualname (docs/API.md — Bridge logging)."""

from __future__ import annotations

from replayt_langgraph_bridge import get_bridge_logger
from replayt_langgraph_bridge.bridge_log import BRIDGE_LOGGER_NAME


def test_bridge_logger_qualname_stable() -> None:
    """Logger name is part of the integrator-facing contract in docs/API.md."""
    assert BRIDGE_LOGGER_NAME == "replayt_langgraph_bridge", (
        "BRIDGE_LOGGER_NAME must remain 'replayt_langgraph_bridge' (docs/API.md, Bridge logging)"
    )
    assert get_bridge_logger().name == "replayt_langgraph_bridge", (
        "get_bridge_logger().name must remain 'replayt_langgraph_bridge' (docs/API.md, Bridge logging)"
    )
