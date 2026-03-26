"""Tests for dependency strategy and version constraints."""

import sys
from importlib.metadata import version

import pytest


def test_python_version_requirement():
    """Test that Python version meets minimum requirement."""
    python_version = sys.version_info
    assert python_version >= (3, 11), "Python 3.11+ is required"


def test_replayt_version_constraint():
    """Test that replayt version meets specified constraints."""
    try:
        replayt_version = version("replayt")
        # Parse version string (e.g., "0.4.2" -> (0, 4, 2))
        version_parts = tuple(map(int, replayt_version.split(".")[:3]))
        
        # Check minimum version (>= 0.4.0)
        assert version_parts >= (0, 4, 0), f"replayt {replayt_version} is below minimum 0.4.0"
        
        # Check upper bound (< 0.5.0)
        assert version_parts < (0, 5, 0), f"replayt {replayt_version} exceeds upper bound < 0.5.0"
    except ImportError:
        pytest.skip("replayt not installed")


def test_langgraph_version_constraint():
    """Test that langgraph version meets specified constraints."""
    try:
        langgraph_version = version("langgraph")
        # Parse version string (e.g., "1.1.3" -> (1, 1, 3))
        version_parts = tuple(map(int, langgraph_version.split(".")[:3]))
        
        # Check minimum version (>= 1.1.0)
        assert version_parts >= (1, 1, 0), f"langgraph {langgraph_version} is below minimum 1.1.0"
        
        # Check upper bound (< 1.2.0)
        assert version_parts < (1, 2, 0), f"langgraph {langgraph_version} exceeds upper bound < 1.2.0"
    except ImportError:
        pytest.skip("langgraph not installed")


def test_dev_dependencies_available():
    """Test that development dependencies are available for testing."""
    # This test ensures pytest is available (listed in dev dependencies)
    import pytest as pytest_module
    assert pytest_module is not None
