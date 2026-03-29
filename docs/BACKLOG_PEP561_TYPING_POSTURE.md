# Backlog spec: PEP 561 typing posture (`py.typed`, stubs, contributor guidance)

Normative **spec and acceptance criteria** for Mission Control backlog **PEP 561 typing posture: py.typed, stub coverage, and contributor note** (item `c6dc5460-a605-4f40-a707-b10bda712a36`). Phase **2** (spec lead) owns this document; phase **3** (builder) implements against it; phase **2b** (spec gate) checks completeness.

**Related normative docs:** public surface **[API.md](API.md)**; contributor setup **[CONTRIBUTING.md](../CONTRIBUTING.md)**; packaging contract **`pyproject.toml`**; CI **`.github/workflows/ci.yml`**; lock strategy **[DEPENDENCY_LOCK_STRATEGY.md](DEPENDENCY_LOCK_STRATEGY.md)**.

---

## 1. Reconciliation with repository state

Treat the following as **facts** for builders unless a later change explicitly updates this section:

| Topic | Current state |
| ----- | --------------- |
| **`py.typed` marker** | **Present** at **`src/replayt_langgraph_bridge/py.typed`**. **`[tool.setuptools.package-data]`** lists it so wheels/sdists include the marker (contract: **`tests/test_pep561_packaging.py`**). |
| **Setuptools layout** | **`[tool.setuptools.package-dir]`** maps **`""` → `src`**; packages discovered under **`src`**. **`package-data`** is required so a **`py.typed`** file is not dropped from artifacts. |
| **Inline annotations** | Public re-exports use **`TypedDict`**, **`Literal`**, and type aliases in several places; internal modules use **`typing`** / **`typing_extensions`** as needed. |
| **CI** | Job **`test`** runs **`uv run pytest`**, **`uv run ruff check src tests`**, and **`uv run mypy -p replayt_langgraph_bridge`** after **`uv sync --frozen --extra dev`**. |
| **`[dev]` extra** | **pytest**, **ruff**, **pip-audit**, **mypy**; **mypy** is pinned in **`uv.lock`**. Smoke settings live under **`[tool.mypy]`** in **`pyproject.toml`** (**`follow_imports = "skip"`**, **`ignore_missing_imports = true`**). |

---

## 2. Product acceptance criteria (verbatim backlog → testable IDs)

| ID | Original acceptance criterion | Normative interpretation |
| -- | ----------------------------- | ------------------------- |
| **A1** | Audit **`pyproject.toml`** / wheel contents for **`py.typed`** (or document explicit omission with rationale). | **Preferred:** Add **`src/replayt_langgraph_bridge/py.typed`** (empty marker file) **and** configure setuptools so **wheel** and **sdist** both include it; verify with a wheel inspection (e.g. **`python -m build`** then list **`replayt_langgraph_bridge/py.typed`** inside **`dist/*.whl`**). **Alternative:** Document **explicit omission** with integrator-visible rationale in **README.md** **and** a maintainer-facing **§7** note in **this doc**, and ensure **CONTRIBUTING.md** points to that rationale. |
| **A2** | If **`py.typed`** is added or adjusted, verify **mypy** or **pyright** smoke on the public import path in CI or documented local command (minimal—no full strictification unless already planned). | **Minimal smoke:** exactly **one** of: (i) a **CI** step on the primary **`test`** job (after **`uv sync --frozen --extra dev`**) running **mypy** *or* **pyright** against the **installed** **`replayt_langgraph_bridge`** package / its **`src`** tree with a **documented, narrow** scope (public import path and bridge-owned modules—not a repo-wide strict pass over **`tests/`** unless already project policy); **or** (ii) **CONTRIBUTING.md** commands that reproduce the same check locally with **no** extra unpublished flags. If the tool is added to **`[project.optional-dependencies] dev`**, pin it via **`uv.lock`** and prefer CI so contributor and integrator docs stay aligned. It is acceptable to use pragmatic flags for **upstream** packages (e.g. **`replayt`**, **`langgraph`**) such as **`--ignore-missing-imports`** (mypy) or **`reportMissingImports: false`** for those roots **only** if documented—provided **bridge-owned** public API types are still meaningfully checked. |
| **A3** | Update **CONTRIBUTING.md** with how contributors should treat annotations on public APIs. | **CONTRIBUTING.md** section **Public API typing (annotations)** (added in phase **2** spec) is the normative contributor contract; keep it aligned with **`__all__`** and **API.md** when the public set changes. |

---

## 3. Recommended builder default (unless §7 omission is chosen)

1. Ship **`py.typed`** beside **`__init__.py`** and wire **`[tool.setuptools.package-data]`** (or equivalent) so the file is not dropped from artifacts.
2. Add **either** **mypy** **or** **pyright** to **`dev`**, regenerate **`uv.lock`**, and add the **smoke** invocation to **CI** **or** document the same command in **CONTRIBUTING.md** per **A2**.
3. Update **README.md** with a short **Typing** or **Integrators** note when **`py.typed`** is present (PEP 561 marker for type checkers).

---

## 4. Stub coverage policy

| Situation | Policy |
| --------- | ------ |
| **Public API** | **Inline** annotations in **`src/replayt_langgraph_bridge/`** are the **primary** typing story; **`py.typed`** marks the package as typed for PEP 561–aware tools. |
| **Separate stub package (`types-replayt-langgraph-bridge`)** | **Out of scope** for this backlog unless a follow-on item explicitly adds it. |
| **Internal / boundary looseness** | **`Any`**, **`TYPE_CHECKING`**, or ignores in **non–`__all__`** implementation modules are acceptable when needed for LangGraph or replayt interoperability; they **do not** justify leaving **`__all__`** symbols untyped or misleading. |

---

## 5. Changelog and release notes (builder)

User-visible delivery (**`py.typed`**, new **dev** type-checker dependency, **CI** step) requires **CHANGELOG.md** **Unreleased** bullets per **CONTRIBUTING.md**. Pure spec-only edits under **docs/** for phase **2** are documented in **CHANGELOG** only when the project treats normative spec additions as integrator-notable (this phase added **Documentation** entries).

---

## 6. Spec gate / builder checklist (phases 2b / 3)

- [x] **A1** satisfied: **`py.typed`** in artifacts **or** documented omission with README + **§7** rationale.
- [x] **A2** satisfied: **mypy** *or* **pyright** smoke **in CI** **or** verbatim **CONTRIBUTING** commands; scope stays **minimal** (public / bridge-owned path, not wholesale strictification).
- [x] **A3** satisfied: **CONTRIBUTING** **Public API typing** matches **`__all__`** / **API.md** after any API edits.
- [x] **README** mentions typing expectations when **`py.typed`** ships.
- [x] **CHANGELOG** updated for user-visible packaging or CI changes.

---

## 7. Rationale template (only if deliberately omitting `py.typed`)

If maintainers choose **not** to ship **`py.typed`** despite inline annotations, **must** document:

1. **Why** the marker is omitted (e.g. known incorrect public annotations, blocking upstream typing gaps).
2. **Integrator workaround** (e.g. rely on source installs, vendor stubs, or named ignores).
3. **Follow-up** (issue or backlog id) toward enabling **`py.typed`**.

This section is **inactive** once **`py.typed`** ships.
