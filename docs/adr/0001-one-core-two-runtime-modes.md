# 1. One Rust core for two runtime modes

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Nguyễn Duy Vũ
- **Supersedes:** —
- **Superseded by:** —

## Context

RayTwin must run in two ways. Library mode runs in one process for research, notebooks and CI. Distributed mode runs on many machines for large areas and many transmitters ([TR §10.3](../technical-report.html#kt-che-do)).

Both modes must give the same result for the same snapshot and seed. Gate 2 measures this directly ([TR §14.4](../technical-report.html#mvp-nghiem-thu)).

One person builds and maintains the system ([TR Appendix A](../technical-report.html#quyet-dinh)). Each physics implementation must pass the comparison with the reference oracle in CI. Two physics implementations would double that work.

TR §10.3 also gives library mode an in-memory task queue (`LocalQueue`) behind a `TaskQueue` trait. Library mode needs no lease, no acknowledgement and no redelivery.

## Decision

We put all physics in one Rust crate, `raytwin-core`. The crate has no network, filesystem, async-runtime or Python dependency.

Library mode and distributed mode are thin runtimes around the core. Both modes call the same two functions:

1. `run_task(snapshot, task, backend)` traces one task and returns one part.
2. `merge(parts)` combines the parts of one job into one result.

Library mode runs the tasks of a job with `rayon` in the calling process. Distributed mode sends the same tasks to workers through NATS JetStream ([ADR 0004](0004-work-distribution-with-nats-jetstream.md)). The core contains no task-queue abstraction.

## Consequences

**Positive**

- One physics implementation needs verification. The oracle comparison in CI covers both modes.
- A test of library mode against distributed mode compares two runtimes, not two physics codes.
- The core compiles and runs its tests without a broker, an object store or Python.

**Negative**

- The core cannot read files. `raytwin-store` reads the scene files and gives core types to the core.
- Each runtime converts its I/O into core types. This adds glue code in `raytwin-store`, `raytwin-dist` and `raytwin-py`.
- The rule "the core has no I/O" needs a check. cargo-deny bans the I/O crates in the core ([ARCHITECTURE §6.2](../architecture/ARCHITECTURE.md#62-allowed-to-use-rules)).

**Neutral**

- Library mode has no queue. A crash in library mode loses the job. The user runs the job again with the same seed and gets the same result.

## Alternatives considered

**Separate engines for each mode.** Each engine could fit its runtime better. Rejected because two physics codes double the oracle work for one person, and Gate 2 compares results that must agree.

**A `TaskQueue` trait with an in-memory `LocalQueue` ([TR §10.3](../technical-report.html#kt-che-do)).** The two modes would share one code path for task dispatch. Rejected because library mode uses no queue feature. A parallel iteration over the task list does the same work with no extra type.

**The core only as a service.** Library mode would call a local service, so only one runtime would exist. Rejected because notebooks and CI would then need a broker and an object store, and library mode must not need them.
