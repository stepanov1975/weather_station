# Active Context

The app has been refactored toward an IMS-only weather station.

## Current Focus

- Keep runtime behavior simple and resilient.
- Prefer direct IMS requests plus cache fallback over separate generic network
  gating.
- Keep GUI-facing payloads as dictionaries for compatibility while using typed
  service models internally.
- Keep agent workflow aligned with `AGENTS.md`: run pytest, ruff, and mypy.

## Important Recent Changes

- Forecast service uses the IMS city portal for Hadera.
- Forecast payloads persist through `JsonCache`.
- Startup no longer exits when the network is unavailable.
- Signal shutdown now performs normal cleanup.
- Active weather API-key handling has been removed.
