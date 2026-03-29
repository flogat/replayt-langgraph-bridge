"""Minimal replayt workflow compiled through the bridge with one LLM-backed step (LangChain).

Install vendor clients explicitly; they are not part of the default or ``[dev]`` graphs::

    pip install -e ".[demo]"
    # or: uv sync --extra demo

Run from the repository root (after install)::

    python examples/llm_node_graph.py

Environment (credentials)
-------------------------
**OpenAI:** set ``OPENAI_API_KEY`` to use the OpenAI route (default when this variable is non-empty
and ``LLM_PROVIDER`` does not force Anthropic).

**Anthropic:** set ``ANTHROPIC_API_KEY`` to use the Anthropic route when OpenAI is not selected.

**``LLM_PROVIDER``:** optional ``openai`` or ``anthropic`` to force a backend; the matching API key
variable above must be set.

**LangChain / LangSmith:** this sample does not read ``LANGCHAIN_TRACING_V2``, ``LANGCHAIN_PROJECT``,
or ``LANGCHAIN_API_KEY``. Add tracing in your own code if needed; see upstream LangChain docs for
current environment variables.

Cost
----
Calls are vendor-metered and may incur charges. This package does not enforce quotas or billing
limits.

Logging and secrets
-------------------
Bridge-originated structured logs follow ``docs/LOG_REDACTION.md``. This script does not print or
log API keys, prompts, or model output—only a short completion line on success.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from uuid import uuid4

from replayt.persistence import JSONLStore
from replayt.runner import Runner
from replayt.workflow import Workflow

from replayt_langgraph_bridge import compile_replayt_workflow, initial_bridge_state


def _select_backend() -> str:
    """Return ``openai`` or ``anthropic`` based on ``LLM_PROVIDER`` and available keys."""
    pref = (os.environ.get("LLM_PROVIDER") or "").strip().lower()
    has_openai = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
    hint = (
        "Install replayt-langgraph-bridge[demo], then set OPENAI_API_KEY and/or "
        "ANTHROPIC_API_KEY (optional LLM_PROVIDER=openai|anthropic). See README LLM demos."
    )
    if pref == "openai":
        if not has_openai:
            raise ValueError(f"OPENAI_API_KEY is required when LLM_PROVIDER=openai. {hint}")
        return "openai"
    if pref == "anthropic":
        if not has_anthropic:
            raise ValueError(f"ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic. {hint}")
        return "anthropic"
    if pref:
        raise ValueError(f"LLM_PROVIDER must be openai, anthropic, or unset. {hint}")
    if has_openai:
        return "openai"
    if has_anthropic:
        return "anthropic"
    raise ValueError(
        "Set OPENAI_API_KEY or ANTHROPIC_API_KEY in the environment (or set LLM_PROVIDER with the "
        f"matching key). {hint}"
    )


def _make_chat_model(backend: str):
    """Construct a LangChain chat model (requires ``[demo]`` packages)."""
    if backend == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini")
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model="claude-3-5-haiku-20241022")


def build_demo_workflow() -> Workflow:
    """Build the sample :class:`~replayt.workflow.Workflow` (no network until a step runs)."""

    wf = Workflow("llm_node_graph_demo")

    @wf.step("call_llm")
    def call_llm(ctx):
        backend = _select_backend()
        model = _make_chat_model(backend)
        from langchain_core.messages import HumanMessage

        topic = str(ctx.get("topic", "replayt"))
        _ = model.invoke(
            [
                HumanMessage(
                    content=(
                        "Reply with the single word OK and nothing else. "
                        f"Topic hint (do not quote): {topic}."
                    )
                )
            ]
        )
        ctx.set("llm_ok", True)
        return None

    wf.set_initial("call_llm")
    return wf


def main() -> None:
    _select_backend()
    wf = build_demo_workflow()

    with tempfile.TemporaryDirectory() as tmp:
        store_path = Path(tmp) / "replayt_events.jsonl"
        store = JSONLStore(store_path)
        runner = Runner(wf, store)
        runner.run_id = str(uuid4())

        graph = compile_replayt_workflow(wf)
        result = graph.invoke(
            initial_bridge_state(context={"topic": "replayt"}),
            context={"runner": runner},
        )

    if not result["context"].get("llm_ok"):
        raise SystemExit("Expected llm_ok in context after LLM step.")
    print("Finished (one LLM-backed replayt step via LangGraph).")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        raise SystemExit(str(e)) from e
