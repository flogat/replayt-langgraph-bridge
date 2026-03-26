"""Security tests for threat model validation."""

from __future__ import annotations

import pytest
import uuid
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from monkeypatch_action.monkeypatch_action import MonkeyPatch  # Wait, no: use pytest.monkeypatch
from replayt.persistence import JSONLStore
from replayt.runner import Runner

from replayt_langgraph_bridge import compile_replayt_workflow, initial