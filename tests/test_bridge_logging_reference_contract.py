"""Contract for stable bridge logger qualname (BACKLOG_BRIDGE_LOGGING_REFERENCE L3)."""

from __future__ import annotations

from replayt_langgraph_bridge import get_bridge_logger
from replayt_langgraph_bridge.bridge_log import BRIDGE_LOGGER_NAME


def test_bridge_logger_qualname_stable() -> None:
    assert BRIDGE_LOGGER_NAME == "replayt_langgraph_bridge"
    assert get_bridge_logger().name == "replayt_langgraph_bridge"
