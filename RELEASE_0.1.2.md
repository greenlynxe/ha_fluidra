# 0.1.2

Small reliability update for the Fluidra Z250iQ integration.

## Included in this version

- enforced a full fallback refresh every 2 minutes for all entities
- kept WebSocket push enabled for near-real-time updates
- aligned the options flow text with the enforced 2-minute refresh policy

## Why this matters

This release makes the integration more predictable when a cloud push event is missed.

Even without a WebSocket event, entity state is refreshed from the API at least every 2 minutes.
