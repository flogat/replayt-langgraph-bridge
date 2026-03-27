"""Structured logging entry point for the bridge (redacted ``extra``)."""

from __future__ import annotations

import logging
import warnings
from typing import Any

from .redaction import RedactorHook, redact_log_attachment, redact_log_message

BRIDGE_LOGGER_NAME = "replayt_langgraph_bridge"


def get_bridge_logger() -> logging.Logger:
    return logging.getLogger(BRIDGE_LOGGER_NAME)


def emit_bridge_record(
    logger: logging.Logger,
    level: int,
    message: str,
    structured: dict[str, Any] | None,
    *,
    redact: bool,
    strict_redact: bool,
    redactor: RedactorHook | None,
) -> None:
    """Log one record with ``extra["replayt_bridge"]`` holding JSON-friendly metadata."""

    structured = dict(structured) if structured else {}
    if not redact:
        warnings.warn(
            "Bridge log redaction is disabled (redact=False); sensitive fields may appear in logs.",
            stacklevel=2,
        )
        logger.log(level, message, extra={"replayt_bridge": structured})
        return
    attachment = redact_log_attachment(
        structured, strict_redact=strict_redact, redactor=redactor
    )
    safe_message = redact_log_message(message, strict_redact=strict_redact)
    logger.log(level, safe_message, extra={"replayt_bridge": attachment})
