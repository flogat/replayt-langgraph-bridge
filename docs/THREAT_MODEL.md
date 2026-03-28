# Threat Model: Checkpoint and State Data

This document outlines the threat model for the `replayt-langgraph-bridge` regarding checkpoint and state data handling. It focuses on assets, adversaries, mitigations, and explicit non-goals.

## 1. Assets

- **Workflow State (`ReplaytBridgeState["context"]`)**: Data passed between workflow steps. May contain user inputs, intermediate results, or configuration.
- **LangGraph Checkpoints**: Serialized snapshots of the graph state, including the workflow context, stored by the configured checkpointer.
- **LLM Prompts/Outputs**: If the workflow involves LLM calls, prompts and responses may be stored in state or checkpoints.
- **Credentials/Secrets**: Any API keys, tokens, or secrets inadvertently placed in the workflow context.

## 2. Adversaries

- **Malicious Integrator**: Controls the workflow definition and step handlers. Can intentionally place sensitive data in state.
- **Untrusted inbound state**: Any source that can supply or alter serialized / dict-shaped `ReplaytBridgeState` consumed by the bridge (e.g. restored checkpoints, RPC layers, or compromised middleware) may attempt **oversized**, **deeply nested**, **cyclic**, or **schema-incompatible** payloads to cause DoS or undefined behavior. Mitigations are specified in **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** once implemented.
- **Compromised Checkpoint Backend**: If the LangGraph checkpointer uses a compromised storage backend (e.g., misconfigured S3 bucket), an external attacker may access checkpoint data.
- **Insider Threat**: A user with access to the checkpoint storage who extracts data beyond their authorization.

## 3. Trust Boundaries

- **Integrator-Controlled Code**: The `Workflow` definition, step handlers, and `Runner` store are controlled by the integrator. The bridge does not sandbox this logic.
- **LangGraph/Replayt Runtimes**: The bridge forwards execution to these frameworks; it does not control their internal serialization or persistence mechanisms.
- **Checkpoint Storage**: The bridge accepts a user-supplied `Checkpointer`. The security of the storage backend is the integrator's responsibility.
- **Inbound channel state**: Dict-shaped graph state the bridge reads before copying into replayt `RunContext.data` is treated as **untrusted** at the validation boundary described in **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)** (spec; implementation tracked by backlog).

## 4. Mitigations

- **Explicit Documentation**: This threat model and the `DESIGN_PRINCIPLES.md` security section warn against storing secrets or PII in graph state.
- **Inbound validation (planned)**: Size limits, schema version checks, and safe failure modes for `ReplaytBridgeState` are normatively specified in **[STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md)**; rejected input must not run step handlers or leave partial checkpoint writes (see that doc).
- **Shallow Merging**: `ReplaytBridgeState["context"]` is shallow-merged across updates. This limits accidental data propagation but does not prevent intentional storage.
- **No Default Persistence**: The bridge does not enable checkpointing by default; the integrator must supply a `Checkpointer`.
- **Error Messages**: Transition validation errors include step names and allowed targets but avoid logging full state to reduce leakage.

## 5. Explicit Non-Goals

- **Sandboxing**: The bridge does not isolate or sandbox integrator code.
- **Secrets Management**: The bridge does not inject secrets for integrators; storage and rotation remain integrator-owned.
- **Log redaction scope**: Optional **bridge-originated** structured log redaction is specified in **[LOG_REDACTION.md](LOG_REDACTION.md)**. It does **not** cover LangGraph internals, arbitrary application logging, or full DLP.
- **Compliance Claims**: This model does not assert compliance with GDPR, HIPAA, or other regulations.
- **Encryption**: The bridge does not enforce encryption at rest or in transit for checkpoints; this depends on the checkpointer implementation.

## 6. Unsafe Fields

The following field types should **never** be persisted in LangGraph checkpoints or workflow state without proper redaction:

- **API Keys and Tokens**: Any authentication credentials (e.g., `api_key`, `token`, `secret_key`)
- **Password Fields**: User passwords or hashed passwords
- **Personal Identifiable Information (PII)**: Names, email addresses, phone numbers, social security numbers, etc.
- **Financial Data**: Credit card numbers, bank account details, transaction records
- **Health Information**: Medical records, health identifiers, insurance information
- **Encryption Keys**: Private keys, symmetric keys, or any cryptographic material
- **Session Tokens**: Active session identifiers or cookies
- **Database Connection Strings**: Contains credentials and should be treated as secrets
- **OAuth Tokens**: Access tokens, refresh tokens, or client secrets
- **Private Messages**: Direct messages, chat logs, or confidential communications

**Note**: This list is not exhaustive. Integrators should apply the principle of least privilege and consult their organization's security policies when determining what data is safe to persist.

## 7. Recommendations for Integrators

- **Avoid Storing Secrets**: Do not place API keys, passwords, or tokens in `ReplaytBridgeState["context"]`.
- **Use Secure Checkpoint Backends**: Configure LangGraph checkpointers with encrypted, access-controlled storage.
- **Redact Sensitive Data**: If PII or secrets must be in state, apply redaction before persistence.
- **Audit Checkpoint Storage**: Regularly review checkpoint storage permissions and access logs.

## Links

- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) - Security considerations section.
- [LOG_REDACTION.md](LOG_REDACTION.md) - Normative spec for bridge log redaction (implemented; see `replayt_langgraph_bridge.redaction` and `bridge_log`).
- [STATE_PAYLOAD_VALIDATION.md](STATE_PAYLOAD_VALIDATION.md) - Normative spec for validating untrusted inbound bridge state (implementation backlog).
- [MISSION.md](MISSION.md) - Project scope and success metrics.
