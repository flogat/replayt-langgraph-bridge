# Log redaction specification (bridge-originated logs)

This document is the **normative spec** for how `replayt-langgraph-bridge` should redact sensitive data in **structured log records** the package emits. It exists so observability stays useful (correlation IDs, step names, transitions) without turning logs into a disclosure channel.

**Status:** Specification for implementation. Until code lands, integrators must not assume redaction is active.

## Scope

### In scope

- **Bridge-originated structured logs** — Records produced by this package when it logs workflow/graph lifecycle events (e.g. step transitions, replayt `run_id` correlation, errors that attach a bounded state snapshot).
- **Replayt-facing event payloads** when the bridge forwards or mirrors replayt events into those same structured records (same redaction pipeline as graph state snippets attached to logs).

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

The implementation should define a single internal type or dict shape for “records” before they reach `logging` (exact field names are implementation details, but the **redaction pipeline** applies to this object):

- **Required conceptual fields:** severity, logger name, message, timestamp (or defer to logging config).
- **Optional structured attachment:** `context` or `extra` — a JSON-serializable dict holding bridge metadata (e.g. `run_id`, `step`, `event`, and a shallow copy of relevant `ReplaytBridgeState["context"]` keys for debugging).

**Redaction applies to the structured attachment and to any string values in the message template expansion**, not to numeric correlation IDs that are known safe.

## Default field policy (deny list)

Matching is **case-insensitive** on dict keys at the **top level** of the structured attachment and **one level deep** into nested dicts/lists (shallow walk: if the implementation recurses, document max depth; default spec is **depth 2** including list elements that are dicts).

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

- **Env var (proposed):** `REPLAYT_BRIDGE_STRICT_REDACT=1` — when set, enable strict behavior before any optional constructor flags (if both exist, document precedence: **env wins** or **most restrictive wins**).
- **Effects (minimum):**
  - Add `PAT_HIGH_ENTROPY` (or equivalent) for long opaque strings.
  - Apply long-string truncation/redaction per **Raw prompts** rules.
  - Optionally extend deny list with: `headers`, `metadata` (entire subtree redacted if value is dict).

## Extension point (integrator hook)

**Contract:** After built-in field and pattern passes, the implementation invokes an optional **callable** supplied by the integrator (e.g. `redactor` parameter on `compile_replayt_workflow` or a module-level setter — **exact surface is left to implementation** but must be documented in README and API reference).

Suggested signature (normative for typing/docs):

```python
from typing import Any, Callable

RedactorHook = Callable[[dict[str, Any]], dict[str, Any]]
```

- **Input:** Deep copy or read-only view of the structured attachment dict (implementation must document mutability).
- **Output:** Dict to log; hook may add keys but should not bypass earlier redaction unless documented as “escape hatch.”
- **Ordering:** Built-ins run first; hook runs last.
- **Errors:** If the hook raises, implementation should log a **safe** fallback (e.g. original record with an additional `redactor_error` flag and sensitive keys stripped by emergency deny list) — document exact behavior.

## API sketch (for Builder; not binding names)

The Builder phase should expose something equivalent to:

- `compile_replayt_workflow(..., redactor: RedactorHook | None = None)` — optional hook.
- Default redactor behavior active when `redactor is None` (built-in lists/patterns).
- Document how to **disable** built-in redaction (discouraged): only if required for tests; if supported, must emit a warning or require an explicit `redact=False` with security note.

Exact parameter names may vary; **behavior must match this document**.

## Builder-facing acceptance criteria (from backlog)

The following are **done** when the feature ships:

1. **Documented defaults** — This file stays aligned with code: default deny-list keys and pattern IDs match implementation constants or generated docs.
2. **Unit test** — At least one test constructs a structured log payload containing a representative secret (e.g. `api_key` with value `sk-test-0123456789abcdef` or a synthetic JWT-shaped string). Capture the serialized log record (or the dict passed to `logging.Logger.log` via a handler). **Assert** the secret substring does not appear in the output under **default** config.
3. **Extension test (recommended)** — One test proves a custom hook can rewrite or drop an additional key after built-in passes.
4. **Strict mode test (recommended)** — With `REPLAYT_BRIDGE_STRICT_REDACT=1`, assert an additional class of value (e.g. long opaque string) is masked compared to default.

## References

- **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** — Security and secrets policy.
- **[THREAT_MODEL.md](THREAT_MODEL.md)** — Checkpoint and state trust boundaries.
