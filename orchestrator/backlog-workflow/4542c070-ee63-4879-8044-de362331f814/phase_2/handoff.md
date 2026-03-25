# Handoff: Phase 2 - Carve internal vs public modules before graph logic lands

## Decisions
- Defined public API in `src/replayt_langgraph_bridge/__init__.py` with `__all__`.
- Marked `graph` module as internal (not part of public API).
- Updated `README.md` to reflect stable import paths and usage examples.

## Files Touched
- `src/replayt_langgraph_bridge/__init__.py`
- `README.md`

## Risks
- None identified. This change only clarifies the API surface and does not modify behavior.

## Open Questions
- None.

## Next Actions
- Proceed to phase 3 (verify CI workflow runs successfully with updated code).
