# Architecture decision records

An ADR records one decision that is costly to reverse and not obvious from the code: what we chose, what else we considered, and what it costs.

RayTwin keeps an ADR only for its most important decisions. The architecture document [`../ARCHITECTURE.md`](../ARCHITECTURE.md) records every other decision as a row in [section 10](../ARCHITECTURE.md#10-decisions-and-rationale). Rows D-01 to D-04 of that table are the four ADRs below.

## Rules during the design phase

RayTwin has no code yet. During this phase:

1. When a decision changes, edit its ADR or its row in section 10 directly. Do not write a superseding record.
2. Set the `Updated` line of the ADR to the date of the change.
3. Update the links in the README and the architecture document in the same change.
4. Add a new ADR only for a decision as significant as the four below. Number it with the next number.

## Index

| # | Title | Status | Updated |
|---|---|---|---|
| [0001](0001-one-core-two-runtime-modes.md) | One Rust core for two runtime modes | Accepted | 2026-10-30 |
| [0002](0002-snapshot-identity-and-path-based-storage.md) | Snapshot identity and path-based storage | Accepted | 2026-10-30 |
| [0003](0003-deterministic-monte-carlo-with-fixed-point-accumulation.md) | Deterministic Monte Carlo with fixed-point accumulation | Accepted | 2026-10-30 |
| [0004](0004-plugin-api.md) | Plugin API | Accepted | 2026-10-30 |
