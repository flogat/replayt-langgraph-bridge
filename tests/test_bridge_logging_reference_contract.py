"""Contract for stable bridge logger qualname (BACKLOG_BRIDGE_LOGGING_REFERENCE L3)."""

from __future__ import annotations

from replayt_langgraph_bridge import get_bridge_logger
from replayt_langgraph_bridge.bridge_log import BRIDGE_LOGGER_NAME


def test_bridge_logger_qualname_stable() -> None:
    """L3: logger qualname is part of the integrator-facing logging contract (see docs/API.md)."""
    assert BRIDGE_LOGGER_NAME == "replayt_langgraph_bridge", (
        "BACKLOG_BRIDGE_LOGGING_REFERENCE L3: BRIDGE_LOGGER_NAME must remain "
        "'replayt_langgraph_bridge' (docs/API.md bridge logging)"
    )
    assert get_bridge_logger().name == "replayt_langgraph_bridge", (
        "BACKLOG_BRIDGE_LOGGING_REFERENCE L3: get_bridge_logger().name must remain "
        "'replayt_langgraph_bridge' (docs/API.md bridge logging)"
    )
