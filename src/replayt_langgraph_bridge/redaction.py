"""Default redaction for bridge-originated structured log attachments.

Behavior matches ``docs/LOG_REDACTION.md``: key deny lists (recursive dict
branches; single-level dicts inside lists), value patterns, optional strict mode
(``REPLAYT_BRIDGE_STRICT_REDACT``), and integrator hook.
"""

from __future__ import annotations

import copy
import os
import re
from typing import Any, Callable

RedactorHook = Callable[[dict[str, Any]], dict[str, Any]]

_SENTINEL = "[REDACTED]"

# Normalized for case-insensitive match (hyphens folded to underscores).
_DEFAULT_DENY_KEYS: frozenset[str] = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "auth",
        "bearer",
        "client_secret",
        "connection_string",
        "cookie",
        "credential",
        "credentials",
        "database_url",
        "dsn",
        "id_token",
        "password",
        "passwd",
        "private_key",
        "refresh_token",
        "secret",
        "secret_key",
        "session",
        "session_id",
        "token",
        "access_token",
    }
)

# Redact entire value only when value is str or list.
_CONDITIONAL_DENY_KEYS: frozenset[str] = frozenset(
    {"completion", "content", "input", "messages", "prompt"}
)

# Keys whose string values may stay long in strict mode if they do not match secret patterns.
_ALLOW_VALUE_KEYS: frozenset[str] = frozenset(
    {
        "checkpoint_id",
        "checkpoint_ns",
        "error_type",
        "event",
        "event_type",
        "from_step",
        "message",
        "run_id",
        "step",
        "thread_id",
        "to_step",
        "workflow",
    }
)

_STRICT_EXTRA_DENY_KEYS: frozenset[str] = frozenset({"headers", "metadata"})

_STRICT_LONG_STRING = 256
_HIGH_ENTROPY_MIN_LEN = 48

# JWT: three Base64url-ish segments; each segment at least 4 chars (conservative lower bound).
_RE_JWT = re.compile(
    r"(?P<jwt>[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,})"
)
_RE_EMAIL = re.compile(r"(?P<email>[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")
_RE_OPENAI_SK = re.compile(r"(?P<sk>sk-[A-Za-z0-9-]{8,})")


def normalize_log_key(key: str) -> str:
    """Lowercase and fold hyphens to underscores for deny/allow matching."""

    return key.lower().replace("-", "_")


def strict_redaction_enabled() -> bool:
    """True when ``REPLAYT_BRIDGE_STRICT_REDACT`` requests strict mode."""

    v = os.environ.get("REPLAYT_BRIDGE_STRICT_REDACT", "")
    return v.strip().lower() in ("1", "true", "yes", "on")


def _deny_for_key(norm_key: str, value: Any, *, strict: bool) -> bool:
    if norm_key in _DEFAULT_DENY_KEYS:
        return True
    if strict and norm_key in _STRICT_EXTRA_DENY_KEYS and isinstance(value, dict):
        return True
    if norm_key in _CONDITIONAL_DENY_KEYS and isinstance(value, (str, list)):
        return True
    return False


def _redact_nested_dict(d: dict[str, Any], *, strict: bool) -> dict[str, Any]:
    """Second level: keys inside a dict that is a direct child of the attachment."""

    out: dict[str, Any] = {}
    for k, v in d.items():
        nk = normalize_log_key(k)
        if _deny_for_key(nk, v, strict=strict):
            out[k] = _SENTINEL
        elif nk == normalize_log_key("content") and isinstance(v, str):
            out[k] = _SENTINEL
        elif isinstance(v, dict):
            out[k] = _redact_nested_dict(v, strict=strict)
        elif isinstance(v, list):
            out[k] = _redact_list(v, strict=strict)
        else:
            out[k] = v
    return out


def _redact_list(items: list[Any], *, strict: bool) -> list[Any]:
    out: list[Any] = []
    for elem in items:
        if isinstance(elem, dict):
            inner: dict[str, Any] = {}
            for k, v in elem.items():
                nk = normalize_log_key(k)
                if _deny_for_key(nk, v, strict=strict):
                    inner[k] = _SENTINEL
                elif nk == normalize_log_key("content") and isinstance(v, str):
                    inner[k] = _SENTINEL
                else:
                    inner[k] = v
            out.append(inner)
        else:
            out.append(elem)
    return out


def apply_field_redaction(
    attachment: dict[str, Any], *, strict: bool
) -> dict[str, Any]:
    """Apply key-based deny/conditional rules at the root and under nested dict values.

    Dict values are traversed recursively for field rules. List elements that are
    dicts get one level of key-based rules; nested dicts inside those elements
    are not traversed for deny matching.
    """

    out: dict[str, Any] = {}
    for k, v in attachment.items():
        nk = normalize_log_key(k)
        if _deny_for_key(nk, v, strict=strict):
            out[k] = _SENTINEL
            continue
        if isinstance(v, dict):
            out[k] = _redact_nested_dict(v, strict=strict)
        elif isinstance(v, list):
            out[k] = _redact_list(v, strict=strict)
        else:
            out[k] = v
    return out


def _high_entropy(s: str) -> bool:
    if len(s) < _HIGH_ENTROPY_MIN_LEN:
        return False
    alnum = sum(1 for c in s if c.isalnum())
    return alnum / len(s) >= 0.85


def _apply_string_patterns(
    value: str,
    *,
    strict: bool,
    parent_key: str | None,
) -> str:
    s = value
    s = _RE_JWT.sub(_SENTINEL, s)
    s = _RE_EMAIL.sub(_SENTINEL, s)
    s = _RE_OPENAI_SK.sub(_SENTINEL, s)
    if strict:
        if (
            parent_key is not None
            and normalize_log_key(parent_key) in _ALLOW_VALUE_KEYS
        ):
            pass
        elif len(s) > _STRICT_LONG_STRING:
            s = _SENTINEL
        elif _high_entropy(s):
            s = _SENTINEL
    return s


def _pattern_pass_on_structure(
    obj: Any, *, strict: bool, parent_key: str | None
) -> Any:
    if isinstance(obj, str):
        return _apply_string_patterns(obj, strict=strict, parent_key=parent_key)
    if isinstance(obj, dict):
        return {
            k: _pattern_pass_on_structure(v, strict=strict, parent_key=k)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [
            _pattern_pass_on_structure(x, strict=strict, parent_key=parent_key)
            for x in obj
        ]
    return obj


def effective_strict(*, strict_redact: bool = False) -> bool:
    """Strict redaction is on if the env requests it or ``strict_redact`` is true."""

    return strict_redaction_enabled() or strict_redact


def redact_log_attachment(
    attachment: dict[str, Any],
    *,
    strict_redact: bool = False,
    redactor: RedactorHook | None = None,
) -> dict[str, Any]:
    """Run field redaction, pattern passes, then optional integrator hook.

    ``attachment`` is not mutated; a deep copy is used before the hook runs.
    """

    use_strict = effective_strict(strict_redact=strict_redact)
    after_fields = apply_field_redaction(attachment, strict=use_strict)
    after_patterns = _pattern_pass_on_structure(
        after_fields, strict=use_strict, parent_key=None
    )
    assert isinstance(after_patterns, dict)
    payload = copy.deepcopy(after_patterns)
    if redactor is None:
        return payload
    try:
        return redactor(payload)
    except Exception:
        fallback = apply_field_redaction(attachment, strict=True)
        fb = _pattern_pass_on_structure(fallback, strict=True, parent_key=None)
        assert isinstance(fb, dict)
        fb = copy.deepcopy(fb)
        fb["redactor_error"] = True
        return fb


def redact_log_message(message: str, *, strict_redact: bool = False) -> str:
    """Apply value patterns to a free-form log message."""

    use_strict = effective_strict(strict_redact=strict_redact)
    return _apply_string_patterns(message, strict=use_strict, parent_key="message")
