"""Validate untrusted inbound :class:`ReplaytBridgeState`-shaped mappings.

Limits and schema rules are normative in ``docs/STATE_PAYLOAD_VALIDATION.md``.
Allowed value types inside ``context`` (recursive): ``None``, ``bool``, ``int`` (excluding
``bool``), ``float``, ``str``, ``dict`` (``str`` keys only), ``list``, ``tuple``, ``set``,
``frozenset``. Rejected: ``bytes``, ``bytearray``, ``memoryview``, callables, and any other
types.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Collection, Iterator, Mapping, Sequence
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)

from replayt_langgraph_bridge.bridge_log import get_bridge_logger

ChannelVersions = dict[str, str | int | float]

MAX_CONTEXT_NESTING_DEPTH = 32
MAX_CONTEXT_WALK_NODES = 50_000
MAX_CONTEXT_STRING_BYTES = 4_194_304
MAX_CONTEXT_TOP_LEVEL_KEYS = 10_000
MAX_REPLAYT_NEXT_LEN = 1024

SUPPORTED_BRIDGE_STATE_SCHEMA_VERSIONS: frozenset[int] = frozenset({1})

_ALLOWED_TOP_KEYS = frozenset(
    {"context", "replayt_next", "bridge_state_schema_version"}
)


class BridgeStateValidationError(ValueError):
    """Inbound bridge state failed validation (generic :meth:`str` for callers)."""


def _is_int_not_bool(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _reject(
    logger: logging.Logger,
    *,
    public_message: str,
    reason_code: str,
    limit_name: str | None = None,
    observed_depth: int | None = None,
    observed_nodes: int | None = None,
    observed_string_bytes: int | None = None,
) -> None:
    extra: dict[str, Any] = {
        "reason_code": reason_code,
    }
    if limit_name is not None:
        extra["limit_name"] = limit_name
    if observed_depth is not None:
        extra["observed_depth"] = observed_depth
    if observed_nodes is not None:
        extra["observed_nodes"] = observed_nodes
    if observed_string_bytes is not None:
        extra["observed_string_bytes"] = observed_string_bytes
    logger.debug("bridge state validation failed", extra=extra)
    raise BridgeStateValidationError(public_message)


class _ContextWalk:
    __slots__ = ("logger", "nodes", "path", "done", "str_bytes")

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.nodes = 0
        self.str_bytes = 0
        self.path: set[int] = set()
        self.done: set[int] = set()

    def _bump_node(self) -> None:
        self.nodes += 1
        if self.nodes > MAX_CONTEXT_WALK_NODES:
            _reject(
                self.logger,
                public_message="Invalid bridge state",
                reason_code="context_node_limit",
                limit_name="MAX_CONTEXT_WALK_NODES",
                observed_nodes=self.nodes,
            )

    def _add_string_bytes(self, n: int) -> None:
        self.str_bytes += n
        if self.str_bytes > MAX_CONTEXT_STRING_BYTES:
            _reject(
                self.logger,
                public_message="Invalid bridge state",
                reason_code="context_string_bytes_limit",
                limit_name="MAX_CONTEXT_STRING_BYTES",
                observed_string_bytes=self.str_bytes,
            )

    def walk(self, value: Any, depth: int) -> None:
        if depth > MAX_CONTEXT_NESTING_DEPTH:
            _reject(
                self.logger,
                public_message="Invalid bridge state",
                reason_code="context_nesting_depth",
                limit_name="MAX_CONTEXT_NESTING_DEPTH",
                observed_depth=depth,
            )

        if value is None or isinstance(value, bool):
            return
        if _is_int_not_bool(value):
            return
        if isinstance(value, float):
            return
        if isinstance(value, str):
            self._add_string_bytes(len(value.encode("utf-8")))
            return
        if isinstance(value, (bytes, bytearray, memoryview)):
            _reject(
                self.logger,
                public_message="Invalid bridge state",
                reason_code="context_disallowed_type",
                limit_name="bytes_like",
            )
        if callable(value):
            _reject(
                self.logger,
                public_message="Invalid bridge state",
                reason_code="context_disallowed_type",
                limit_name="callable",
            )

        oid = id(value)
        if oid in self.done:
            return
        if oid in self.path:
            _reject(
                self.logger,
                public_message="Invalid bridge state",
                reason_code="context_cycle",
            )

        if isinstance(value, dict):
            self.path.add(oid)
            try:
                for key, child in value.items():
                    if not isinstance(key, str):
                        _reject(
                            self.logger,
                            public_message="Invalid bridge state",
                            reason_code="context_key_type",
                        )
                    self._add_string_bytes(len(key.encode("utf-8")))
                    self._bump_node()
                    self.walk(child, depth + 1)
            finally:
                self.path.discard(oid)
            self.done.add(oid)
            return

        if isinstance(value, (list, tuple)):
            self.path.add(oid)
            try:
                for item in value:
                    self._bump_node()
                    self.walk(item, depth + 1)
            finally:
                self.path.discard(oid)
            self.done.add(oid)
            return

        if isinstance(value, (set, frozenset)):
            self.path.add(oid)
            try:
                for item in value:
                    self._bump_node()
                    self.walk(item, depth + 1)
            finally:
                self.path.discard(oid)
            self.done.add(oid)
            return

        _reject(
            self.logger,
            public_message="Invalid bridge state",
            reason_code="context_disallowed_type",
            limit_name=type(value).__name__,
        )


def _validate_resolved_bridge_payload(
    *,
    context: Any,
    replayt_next_raw: Any,
    schema_version: int,
    logger: logging.Logger,
) -> None:
    if schema_version not in SUPPORTED_BRIDGE_STATE_SCHEMA_VERSIONS:
        _reject(
            logger,
            public_message="Unsupported bridge state schema version",
            reason_code="unsupported_schema_version",
        )

    if not isinstance(context, dict):
        _reject(
            logger,
            public_message="Invalid bridge state",
            reason_code="context_not_dict",
        )

    if len(context) > MAX_CONTEXT_TOP_LEVEL_KEYS:
        _reject(
            logger,
            public_message="Invalid bridge state",
            reason_code="context_top_level_keys",
            limit_name="MAX_CONTEXT_TOP_LEVEL_KEYS",
        )

    nxt = str(replayt_next_raw)
    if len(nxt) > MAX_REPLAYT_NEXT_LEN:
        _reject(
            logger,
            public_message="Invalid bridge state",
            reason_code="replayt_next_length",
            limit_name="MAX_REPLAYT_NEXT_LEN",
        )

    walker = _ContextWalk(logger)
    for _key, val in context.items():
        walker.walk(val, 0)


def validate_input_checkpoint_channel_values(
    channel_values: Mapping[str, Any],
    *,
    logger: logging.Logger | None = None,
) -> None:
    """Validate merged bridge channels for LangGraph INPUT checkpoints before ``put`` persists.

    LangGraph can persist invoke/resume merges before step nodes run; this enforces the same
    limits as :func:`validate_inbound_bridge_state` for that path. Reads
    ``bridge_state_schema_version`` from channel values or from the ``__start__`` payload when
    present.
    """
    log = logger if logger is not None else get_bridge_logger()
    if "context" not in channel_values or "replayt_next" not in channel_values:
        return

    context = channel_values["context"]
    replayt_next_raw = channel_values["replayt_next"]

    if "bridge_state_schema_version" in channel_values:
        v = channel_values["bridge_state_schema_version"]
        if not _is_int_not_bool(v):
            _reject(
                log,
                public_message="Invalid bridge state",
                reason_code="schema_version_type",
            )
        schema_version = v
    else:
        start = channel_values.get("__start__")
        if isinstance(start, Mapping) and "bridge_state_schema_version" in start:
            raw = start["bridge_state_schema_version"]
            if not _is_int_not_bool(raw):
                _reject(
                    log,
                    public_message="Invalid bridge state",
                    reason_code="schema_version_type",
                )
            schema_version = raw
        else:
            schema_version = 1

    _validate_resolved_bridge_payload(
        context=context,
        replayt_next_raw=replayt_next_raw,
        schema_version=schema_version,
        logger=log,
    )


def validate_inbound_bridge_state(
    state: Mapping[str, Any],
    *,
    logger: logging.Logger | None = None,
) -> None:
    """Raise :exc:`BridgeStateValidationError` if ``state`` violates bridge limits or shape.

    Call before copying ``state[\"context\"]`` into replayt :class:`~replayt.runner.RunContext`
    data or when validating full inbound dict state at the bridge boundary.
    """
    log = logger if logger is not None else get_bridge_logger()

    if not isinstance(state, Mapping):
        _reject(
            log,
            public_message="Invalid bridge state",
            reason_code="state_not_mapping",
        )

    extra_keys = set(state.keys()) - _ALLOWED_TOP_KEYS
    if extra_keys:
        _reject(
            log,
            public_message="Invalid bridge state",
            reason_code="unknown_top_level_keys",
        )

    if "context" not in state or "replayt_next" not in state:
        _reject(
            log,
            public_message="Invalid bridge state",
            reason_code="missing_required_key",
        )

    context = state["context"]
    replayt_next_raw = state["replayt_next"]

    if "bridge_state_schema_version" in state:
        v = state["bridge_state_schema_version"]
        if not _is_int_not_bool(v):
            _reject(
                log,
                public_message="Invalid bridge state",
                reason_code="schema_version_type",
            )
        schema_version = v
    else:
        schema_version = 1

    _validate_resolved_bridge_payload(
        context=context,
        replayt_next_raw=replayt_next_raw,
        schema_version=schema_version,
        logger=log,
    )


def _checkpoint_put_needs_bridge_validation(
    metadata: CheckpointMetadata,
    new_versions: ChannelVersions,
) -> bool:
    """True when LangGraph is persisting a checkpoint that includes a new ``invoke`` merge.

    Resumed threads often skip ``source=\"input\"`` puts; those merges appear on the next
    ``loop`` put with ``__start__`` in ``new_versions``.
    """
    src = metadata.get("source")
    if src == "input":
        return True
    if src == "loop" and "__start__" in new_versions:
        return True
    return False


class BridgeValidatingCheckpointSaver(BaseCheckpointSaver):
    """Wraps a saver to validate bridge channel values on INPUT checkpoints before persistence."""

    def __init__(
        self,
        inner: BaseCheckpointSaver,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(serde=inner.serde)
        self._inner = inner
        self._validation_logger = logger if logger is not None else get_bridge_logger()

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        return self._inner.get_tuple(config)

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        return self._inner.list(config, filter=filter, before=before, limit=limit)

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return self._inner.put_writes(config, writes, task_id, task_path=task_path)

    def delete_thread(self, thread_id: str) -> None:
        return self._inner.delete_thread(thread_id)

    def delete_for_runs(self, run_ids: Sequence[str]) -> None:
        return self._inner.delete_for_runs(run_ids)

    def copy_thread(self, source_thread_id: str, target_thread_id: str) -> None:
        return self._inner.copy_thread(source_thread_id, target_thread_id)

    def prune(
        self,
        thread_ids: Sequence[str],
        *,
        strategy: str = "keep_latest",
    ) -> None:
        return self._inner.prune(thread_ids, strategy=strategy)

    def get_next_version(self, current: Any, channel: None = None) -> Any:
        return self._inner.get_next_version(current, channel)

    def with_allowlist(
        self, extra_allowlist: Collection[tuple[str, ...]]
    ) -> BaseCheckpointSaver:
        wrapped = self._inner.with_allowlist(extra_allowlist)
        return BridgeValidatingCheckpointSaver(wrapped, logger=self._validation_logger)

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        return await self._inner.aget_tuple(config)

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        async for item in self._inner.alist(
            config, filter=filter, before=before, limit=limit
        ):
            yield item

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return await self._inner.aput_writes(
            config, writes, task_id, task_path=task_path
        )

    async def adelete_thread(self, thread_id: str) -> None:
        return await self._inner.adelete_thread(thread_id)

    async def adelete_for_runs(self, run_ids: Sequence[str]) -> None:
        return await self._inner.adelete_for_runs(run_ids)

    async def acopy_thread(self, source_thread_id: str, target_thread_id: str) -> None:
        return await self._inner.acopy_thread(source_thread_id, target_thread_id)

    async def aprune(
        self,
        thread_ids: Sequence[str],
        *,
        strategy: str = "keep_latest",
    ) -> None:
        return await self._inner.aprune(thread_ids, strategy=strategy)

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        if _checkpoint_put_needs_bridge_validation(metadata, new_versions):
            validate_input_checkpoint_channel_values(
                checkpoint.get("channel_values") or {},
                logger=self._validation_logger,
            )
        return self._inner.put(config, checkpoint, metadata, new_versions)

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        if _checkpoint_put_needs_bridge_validation(metadata, new_versions):
            validate_input_checkpoint_channel_values(
                checkpoint.get("channel_values") or {},
                logger=self._validation_logger,
            )
        return await self._inner.aput(config, checkpoint, metadata, new_versions)
