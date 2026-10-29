# Architecture decision records

An ADR captures one architecturally significant decision: what we chose, what
else we considered, and what it costs us. It is written when the decision is
made, while the alternatives are still fresh, and it is never rewritten
afterwards — a decision that turns out wrong gets a *new* record that supersedes
the old one.

The point is not process. It is that in two years someone will ask why this
system works the way it does, and the answer will otherwise have left the project.

The architecture document [`../architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md)
links each decision below to the view that it shapes.

## When to write one

Write an ADR when a decision is **costly to reverse** and **not obvious from the
code**:

- choosing or replacing a datastore, framework, protocol, or third-party service;
- a change to a public API contract or an integration boundary;
- a security, privacy, or data-residency posture;
- a deliberate departure from a team or organisation standard;
- accepting a known trade-off — performance for simplicity, consistency for
  availability — that a future reader would otherwise read as an accident.

Do not write one for a decision the code states plainly, a reversible choice, or
a matter of style the linter already settles.

## How

1. Copy [`0000-record-architecture-decisions.md`](0000-record-architecture-decisions.md)
   to `NNNN-short-title-in-kebab-case.md`, where `NNNN` is the next unused number.
   Numbers are never reused, even if a record is withdrawn.
2. Fill it in. Aim for one page. If it needs more, the decision probably contains
   two decisions.
3. Open it as a pull request with status **Proposed**, and let the discussion
   happen in review rather than in the record.
4. On approval, set the status to **Accepted** and add a row to the index below.

## Lifecycle

| Status | Meaning |
|---|---|
| **Proposed** | Under discussion; not yet binding |
| **Accepted** | In force. This is how the system works |
| **Superseded by NNNN** | Replaced. Kept as history — never delete or edit the reasoning |
| **Deprecated** | No longer applies, with nothing replacing it |

Superseding a record means editing exactly two lines: the old record's status, and
the new record's `Supersedes` line. The old record's Context and Decision stay as
they were written, because they are the historical account.

## Index

| # | Title | Status | Date |
|---|---|---|---|
| [0000](0000-record-architecture-decisions.md) | Record architecture decisions | Accepted | 2026-10-29 |
| [0001](0001-one-core-two-runtime-modes.md) | One Rust core for two runtime modes | Accepted | 2026-10-29 |
| [0002](0002-snapshot-identity-and-path-based-storage.md) | Snapshot identity and path-based storage | Accepted | 2026-10-29 |
| [0003](0003-deterministic-monte-carlo-with-fixed-point-accumulation.md) | Deterministic Monte Carlo with fixed-point accumulation | Accepted | 2026-10-29 |
| [0004](0004-work-distribution-with-nats-jetstream.md) | Work distribution with NATS JetStream | Accepted | 2026-10-29 |
| [0005](0005-nats-as-the-client-protocol.md) | NATS as the client protocol | Accepted | 2026-10-29 |
| [0006](0006-gpu-backends-through-wgpu.md) | GPU backends through wgpu | Accepted | 2026-10-29 |
| [0007](0007-no-public-plugin-api-in-release-0-1.md) | No public plugin API in release 0.1 | Accepted | 2026-10-29 |
| [0008](0008-calibration-on-frozen-paths-in-pytorch.md) | Calibration on frozen paths in PyTorch | Accepted | 2026-10-29 |
| [0009](0009-zarr-as-the-only-result-format.md) | Zarr as the only result format | Accepted | 2026-10-29 |
| [0010](0010-trusted-pull-requests-on-the-gpu-runner.md) | Trusted pull requests on the GPU runner | Accepted | 2026-10-29 |
