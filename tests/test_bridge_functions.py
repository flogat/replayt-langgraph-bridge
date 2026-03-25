import pytest
from replayt_langgraph_bridge.graph import _merge_context, _merged_llm_defaults, _normalize_next

def test_merge_context():
    """Test _merge_context function."""
    left = {"a": 1, "b": 2}
    right = {"b": 3, "c": 4}
    result = _merge_context(left, right)
    assert result == {"a": 1, "b": 3, "c": 4}
    
    # Test with None right
    result = _merge_context(left, None)
    assert result == {"a": 1, "b": 2}
    
    # Test with empty dicts
    result = _merge_context({}, {})
    assert result == {}

def test_merged_llm_defaults():
    """Test _merged_llm_defaults function."""
    from replayt.workflow import Workflow
    
    # Workflow requires a name argument
    wf = Workflow(name="test_workflow")
    
    @wf.step("step1")
    def step1(ctx):
        return "step2"
    
    @wf.step("step2") 
    def step2(ctx):
        return "__end__"
    
    # Test with workflow that has llm_defaults
    wf.llm_defaults = {"temperature": 0.7}
    result = _merged_llm_defaults(wf)
    assert result == {"temperature": 0.7}
    
    # Test with workflow that has no llm_defaults
    wf.llm_defaults = None
    result = _merged_llm_defaults(wf)
    assert result == {}

def test_normalize_next():
    """Test _normalize_next function."""
    # Test normal cases
    assert _normalize_next("step1") == "step1"
    assert _normalize_next("step2") == "step2"
    
    # Test None and empty string
    assert _normalize_next(None) == ""
    assert _normalize_next("") == ""
    
    # Test with whitespace (function does NOT strip whitespace)
    assert _normalize_next(" step1 ") == " step1 "

if __name__ == "__main__":
    pytest.main([__file__])
