# Log redaction specification (bridge-originated logs)

This document is the **normative spec** for how `replayt-langgraph-bridge` should redact sensitive data in **structured log records** the package emits. It exists so observability stays useful (correlation IDs, step names, transitions) without turning logs into a disclosure channel.

**Status:** Implemented in `replayt_langgraph_bridge.redaction` and `replayt_langgraph_bridge.bridge_log` (wired from `compile_replayt_workflow`). Defaults below match module-level constants unless noted.

## Backlog traceability

Maps the product backlog item **“Specify redaction hooks for logged graph and replayt events”** to this spec so phase **3** (Builder) and phase **4** (Tester) share a single checklist.

| Backlog acceptance criterion | Where it is specified | How it is verified (today) |
| ----------------------------- | ---------------------- | --------------------------- |
| Documented default **allow** and **deny** lists for log **fields** | [Default field policy](#default-field-policy-deny-list) and [Keys that must not be redacted](#keys-that-must-not-be-redacted-by-default-allow-list) | Tables match `_DEFAULT_DENY_KEYS`, `_CONDITIONAL_DENY_KEYS`, `_STRICT_EXTRA_DENY_KEYS`, and `_ALLOW_VALUE_KEYS` in `replayt_langgraph_bridge.redaction` |
| Documented default **string patterns** | [Default string pattern policy](#default-string-pattern-policy-value-masking) | Pattern behavior matches `_RE_JWT`, `_RE_EMAIL`, `_RE_OPENAI_SK`, and strict-only high-entropy / long-string rules in the same module |
| At least one **unit test** proves a representative secret-like value does **not** appear in **emitted** log output under **default** config | [Verification obligations](#verification-obligations) | `tests/test_log_redaction.py`: minimum `redact_log_attachment` + `json.dumps` assert; **recommended** `emit_bridge_record` and/or compiled graph invoke (see obligations) |
| **Extension point** or callback documented for stricter integrators | [Extension point](#extension-point-integrator-hook) and README / API on `RedactorHook`, `compile_replayt_workflow(..., redactor=...)` | Doc + tests `test_custom_redactor_runs_last`, `test_redactor_error_sets_flag_and_does_not_leak_secret` |

## Scope

### In scope

- **Bridge-originated structured logs** — Records produced by this package when it logs workflow/graph lifecycle events (e.g. step transitions, replayt `run_id` correlation, errors that attach a bounded state snapshot).
- **Replayt-facing event payloads** when the bridge forwards or mirrors replayt events into those same structured records (same redaction pipeline as graph state snippets attached to logs).

**Graph vs replayt events:** Any structured dict the bridge passes to `emit_bridge_record` (including metadata derived from workflow steps, transitions, or replayt `run_id` correlation) is treated as one attachment shape: there is no separate “replayt-only” or “graph-only” redactor. Integrators who log outside this path are out of scope ([Out of scope](#out-of-scope-non-goals)).

### Out of scope (non-goals)

- **Full DLP** — No content discovery, ML classification, or enterprise policy engines.
- **LangGraph framework logs** — The bridge does not control LangGraph’s internal logging; integrators configure LangGraph and hosting separately.
- **Arbitrary integrator `print` / application logging** — Only records emitted through the bridge’s documented logging path.
- **Checkpoint encryption or at-rest protection** — See **[THREAT_MODEL.md](THREAT_MODEL.md)**; persistence security remains integrator-owned unless a future, explicitly documented API says otherwise.

## Design goals

1. **Default-safe logs** — Under default configuration, common secret-like **field names** and **string patterns** are stripped or masked before a record is handed to the logging backend.
2. **Correlation without secrets** — Identifiers such as `run_id`, `thread_id`, step names, and workflow identifiers (non-secret) remain available by default.
3. **Strict mode** — Opt-in tightening for environments that want fewer leaks at the cost of more `[REDACTED]` fields.
4. **Extension** — Integrators with stricter needs can supply a hook that runs after built-in rules.

## Structured log record (contract)

**Emission shape (implemented):** Bridge code calls `logging.Logger.log(level, msg, extra={"replayt_bridge": <dict>})`. The redaction pipeline runs on:

1. **Structured attachment** — the dict intended for `extra["replayt_bridge"]` (JSON-serializable metadata: `run_id`, `step`, `event`, selected `ReplaytBridgeState["context"]` keys, etc.).
2. **Log message string** — the human-readable `msg` after template expansion; **value patterns** run on this string (not the full key-based deny list).

**“Emitted log record” for tests:** The observable output is the `logging.LogRecord` after `emit_bridge_record` (or an equivalent path used in production). Assertions MUST cover at least `record.getMessage()` and `getattr(record, "replayt_bridge", {})` serialized together (e.g. `json.dumps`) so both the message body and structured extra are checked. Testing only `redact_log_attachment` in isolation satisfies the backlog’s **minimum** bar if the test name and docstring state that it stands in for the attachment half of the pipeline; an end-to-end test through `emit_bridge_record` or `compile_replayt_workflow` is **strongly recommended** and already present in the suite.

Correlation IDs that are numeric or opaque non-secret strings (e.g. `run_id`) remain unless a pattern or strict rule masks them.

## Traversal semantics (field vs pattern passes)

These rules describe **current** behavior in `replayt_langgraph_bridge.redaction`; update this section if traversal changes.

- **Key-based deny / conditional / strict field rules (`apply_field_redaction`):**
  - Applied to the **root** attachment dict and, when a value is a **nested dict**, **recursively** to all dict values at any depth under that branch.
  - When a value is a **list**, each element that is a **dict** is processed with **one level** of key-based rules on that dict’s keys; values inside those dicts that are themselves dicts are **not** further traversed for key-based redaction (they are left as-is). Non-dict list elements are unchanged by key rules.
- **String pattern passes (`PAT_*`):** After field redaction, patterns run over **all** string values anywhere in the attachment structure (full recursive walk over dicts and lists), and over the log message string via `redact_log_message`.

**Key normalization:** Matching uses `normalize_log_key`: lowercased keys with `-` folded to `_`, so `api-key` and `api_key` are equivalent for deny/allow decisions.

## Default field policy (deny list)

Matching uses [key normalization](#traversal-semantics-field-vs-pattern-passes) on dict keys as described in the traversal section above.

### Deny list (keys whose values are replaced)

When a key matches (case-insensitive), replace the value with a sentinel (recommended literal: `[REDACTED]`) or remove the key (document which behavior the implementation chooses; **replacement is preferred** so keys remain visible for debugging).

| Key (match) | Rationale |
| ------------- | --------- |
| `api_key`, `apikey`, `api-key` | Provider keys |
| `password`, `passwd`, `secret`, `secret_key`, `client_secret` | Credentials |
| `token`, `access_token`, `refresh_token`, `id_token` | OAuth / bearer tokens |
| `authorization`, `auth` | Header blobs |
| `bearer` | Common token carrier |
| `private_key`, `credential`, `credentials` | Crypto / generic secrets |
| `cookie`, `session`, `session_id` | Session material |
| `connection_string`, `dsn`, `database_url` | Connection strings |

### Keys that must not be redacted by default (allow list)

These are **always emitted** when present unless strict mode or a custom hook removes them (default config must keep them):

| Key / concept | Rationale |
| --------------- | --------- |
| `run_id` | Replayt correlation |
| `thread_id`, `checkpoint_ns`, `checkpoint_id` | LangGraph correlation (if surfaced by bridge logs) |
| `step`, `from_step`, `to_step`, `workflow` (name/id only) | Operator debugging |
| `event`, `event_type` | Structured classification |
| `error_type`, `message` (after pattern pass) | Failure triage — subject to pattern redaction below |

If an allow-listed key’s **value** matches a secret pattern (e.g. user mistakenly puts a JWT in `message`), **pattern redaction still applies** to string values.

## Default string pattern policy (value masking)

Apply to **all string values** in the structured attachment and to the log message body **after** field redaction. Order: **field deny list → pattern passes → custom hook**.

Recommended sentinels: replace matched substring with `[REDACTED]` or a fixed token; document exact behavior in API docs.

| ID | Description | Spec (normative intent) |
| -- | ------------- | ------------------------- |
| `PAT_EMAIL` | Email addresses | Match common `local@domain` forms (implementation may use a conservative regex; false positives acceptable). |
| `PAT_JWT` | JWT-like three-segment tokens | Three Base64url-ish segments separated by `.`, length bounds to reduce false positives (document bounds in code docstring). |
| `PAT_OPENAI_SK` | OpenAI-style keys | Prefix `sk-` followed by alphanumeric / `-` segment. |
| `PAT_HIGH_ENTROPY` | Long opaque strings | Optional in default mode: strings over **N** characters with high ratio of alphanumeric (e.g. **N = 48**); **enable only in strict mode** to avoid hiding legitimate prose. |

### Raw prompts and LLM payloads

- **Default mode:** Do not attempt to detect “prompts” generically. If the structured attachment includes known keys such as `prompt`, `messages`, `input`, `completion`, **treat them as deny-list keys** (add to default deny list): `prompt`, `messages`, `input`, `completion`, `content` **only when** the value is a string or list (redact entire value). For nested message lists, redact each string `content` field **one level deep** in default mode.
- **Strict mode:** Redact any string value longer than **L** characters (**L = 256** suggested) unless the key is in the allow list and the value matches no secret pattern — document final `L` in implementation.

## Strict mode

- **Env var (implemented):** `REPLAYT_BRIDGE_STRICT_REDACT` — truthy values (`1`, `true`, `yes`, `on`, case-insensitive) enable strict behavior. **Precedence:** strict is **on** if the environment requests it **or** the caller passes `strict_redact=True` to `redact_log_attachment` / `compile_replayt_workflow` / `emit_bridge_record` (**most restrictive wins**).
- **Effects (minimum):**
  - Add `PAT_HIGH_ENTROPY` (or equivalent) for long opaque strings.
  - Apply long-string truncation/redaction per **Raw prompts** rules.
  - Optionally extend deny list with: `headers`, `metadata` (entire subtree redacted if value is dict).

## Extension point (integrator hook)

**Contract:** After built-in field and pattern passes, the implementation invokes an optional **callable** supplied by the integrator.

**Public surfaces (implemented):**

- `compile_replayt_workflow(..., redactor: RedactorHook | None = None, redact: bool = True, strict_redact: bool = False)` — propagates to every `emit_bridge_record` call for that compiled graph.
- `redact_log_attachment(..., redactor=...)` — for integrator tests, custom loggers, or middleware that reuse the same pipeline without compiling a graph.

README and package docstrings remain the integrator-facing summary; this document is normative for behavior.

Suggested signature (normative for typing/docs):

```python
from typing import Any, Callable

RedactorHook = Callable[[dict[str, Any]], dict[str, Any]]
```

- **Input:** Deep copy of the structured attachment after built-in field and pattern passes (`copy.deepcopy`); the hook may mutate the dict it receives.
- **Output:** Dict attached to `LogRecord.replayt_bridge`; the hook may add keys but should not strip built-in redaction unless intentionally documented as an escape hatch (`redact=False`).
- **Ordering:** Built-ins run first; hook runs last.
- **Errors:** If the hook raises, the implementation returns a **safe** fallback dict: built-in redaction re-run with `strict=True`, plus `redactor_error: True`, without leaking prior secret substrings.

## API sketch (historical)

The shipped API matches the [Extension point](#extension-point-integrator-hook) section. **`redact=False`** disables built-in redaction and emits a `UserWarning`; use only in controlled tests.

## Verification obligations

**Maintainers MUST keep the following true in CI** (backlog + regression safety):

1. **Documented defaults** — Default deny-list keys, conditional keys, strict extras, allow-value keys, and pattern semantics in this file stay consistent with `replayt_langgraph_bridge.redaction` (or the doc explicitly records an intentional divergence and a follow-up issue).
2. **Minimum secret-leak test (required)** — Under **default** redaction (`redact=True`, `strict_redact=False`, `REPLAYT_BRIDGE_STRICT_REDACT` unset), at least one test uses a representative secret-like literal (e.g. `api_key` → `sk-test-0123456789abcdef` or a JWT-shaped three-segment string) and asserts that literal’s **substring does not appear** in `json.dumps` of the redacted attachment and/or in a fingerprint of the full `LogRecord` as defined in [Structured log record](#structured-log-record-contract).
3. **Extension hook (required for backlog)** — At least one test proves a custom `RedactorHook` runs **after** built-in passes and can add or rewrite keys; at least one test proves a raising hook yields a safe fallback (`redactor_error` set, secret substrings absent).
4. **Strict mode (recommended)** — With `REPLAYT_BRIDGE_STRICT_REDACT=1` or `strict_redact=True`, assert stricter masking (e.g. long opaque string or long non-allow-listed prose) compared to default.

Reference suite: `tests/test_log_redaction.py`.

## Builder-facing acceptance criteria (from backlog)

The following are **done** when the feature ships (aligned with [Backlog traceability](#backlog-traceability)):

1. **Documented defaults** — This file stays aligned with code: default deny-list keys and pattern IDs match implementation constants or generated docs.
2. **Unit test** — Satisfies [Verification obligations](#verification-obligations) item 2.
3. **Extension test** — Satisfies item 3.
4. **Strict mode test** — Satisfies item 4 (recommended but already covered in the reference suite).

## Implementation map

| Spec area | Code |
| --------- | ---- |
| Key deny lists (default + conditional + strict extras) + allow keys for strict long-string carve-out | `replayt_langgraph_bridge.redaction`: `_DEFAULT_DENY_KEYS`, `_CONDITIONAL_DENY_KEYS`, `_STRICT_EXTRA_DENY_KEYS`, `_ALLOW_VALUE_KEYS` |
| Key normalization | `normalize_log_key()` |
| Value patterns (`PAT_*`) | Same module: `_RE_JWT`, `_RE_EMAIL`, `_RE_OPENAI_SK`, `_high_entropy` (strict) |
| Strict env + compiler flag | `strict_redaction_enabled()`, `compile_replayt_workflow(..., strict_redact=...)` — strict is on if the environment requests it **or** `strict_redact=True` (most restrictive) |
| Integrator hook | `RedactorHook`, `redact_log_attachment(..., redactor=...)`, `compile_replayt_workflow(..., redactor=...)` |
| Emission | `emit_bridge_record` / `compile_replayt_workflow` — `logging.Logger.log(..., extra={"replayt_bridge": ...})` |
| Disable built-in redaction | `compile_replayt_workflow(..., redact=False)` emits `UserWarning` |

## References

- **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** — Security and secrets policy.
- **[THREAT_MODEL.md](THREAT_MODEL.md)** — Checkpoint and state trust boundaries.
