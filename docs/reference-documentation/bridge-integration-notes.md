# Bridge integration notes (first-party)

This file is **maintainer-written** summary text. It does not quote upstream manuals. For authoritative definitions and API details, use **`links.manifest.json`** and the upstream pages linked there.

## replayt (workflow plane)

The bridge treats **replayt** as the source of **workflow shape** and **step semantics**: a **`Workflow`** registers steps and transitions; a **`Runner`** executes handlers and persists **replayt-oriented** state through the store you attach. Concepts such as **`RunContext`**, approvals, and transition guards are owned by **replayt** and its published API. The adapter compiles that workflow into a LangGraph graph; it does not redefine replayt execution rules.

## LangGraph (graph plane)

**LangGraph** supplies the **graph runtime**: **compilation** of a **StateGraph**-style graph, **invocation** with configuration (for example **`thread_id`**), and optional **checkpoint** persistence via a **`Checkpointer`**. The bridge’s **`compile_replayt_workflow`** builds such a graph from a replayt **`Workflow`** and forwards step execution back into **replayt** handlers. Integrators choose checkpointers and hosting; see **`docs/CHECKPOINT_PERSISTENCE.md`** for how the two persistence planes interact.

## Where to read more

Open **`links.manifest.json`** in this directory for **replayt**- and **LangGraph**-oriented URLs aligned with **`pyproject.toml`** ranges and the current **`uv.lock`** resolution at last review.
