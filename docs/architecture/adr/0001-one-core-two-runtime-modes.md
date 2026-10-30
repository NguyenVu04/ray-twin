# 1. One Rust core for two runtime modes

- **Status:** Accepted
- **Date:** 2026-10-29
- **Updated:** 2026-10-30
- **Deciders:** Nguyễn Duy Vũ

## Context

RayTwin must run in two ways. Library mode runs in one process for research, notebooks and CI. Distributed mode runs on many machines for large areas and many transmitters ([TR §10.3](../../technical-report.html#kt-che-do)).

Both modes must give the same result for the same snapshot and seed. Gate 2 measures this directly ([TR §14.4](../../technical-report.html#mvp-nghiem-thu)).

One person builds and maintains the system ([TR Appendix A](../../technical-report.html#quyet-dinh)). Each physics implementation must pass the comparison with the reference oracle in CI. Two physics implementations would double that work.

TR §10.3 also gives library mode an in-memory task queue (`LocalQueue`) behind a `TaskQueue` trait. Library mode needs no lease, no acknowledgement and no redelivery.

Release 0.2 adds a service-quality layer ([TR §17](../../technical-report.html#qos)), and release 0.3 adds a SON loop ([TR §18.4](../../technical-report.html#pl-son)). Both read radio-map results. They do not trace rays.

## Decision

We put all physics in one Rust crate, `raytwin-core`. The crate has no network, filesystem, async-runtime or Python dependency.

Library mode and distributed mode are thin runtimes around the core. Both modes call the same two functions:

1. `run_task(snapshot, task, backend)` traces one task and returns one part.
2. `merge(parts)` combines the parts of one job into one result.

Library mode runs the tasks of a job with `rayon` in the calling process. Distributed mode sends the same tasks to workers through NATS JetStream ([D-05](../ARCHITECTURE.md#10-decisions-and-rationale)). The core contains no task-queue abstraction.

The service-quality layer (`raytwin.qos`), the SON loop (`raytwin.son`) and the viewer (`raytwin.viz`) are Python modules in the client process. They read results through the same API in both modes. They add no task kind.

## Consequences

**Positive**

- One physics implementation needs verification. The oracle comparison in CI covers both modes.
- A test of library mode against distributed mode compares two runtimes, not two physics codes.
- The core compiles and runs its tests without a broker, an object store or Python.
- The service-quality layer gets the same input in both modes, because it reads only the merged result.

**Negative**

- The core cannot read files. `raytwin-store` reads the scene files and gives core types to the core.
- Each runtime converts its I/O into core types. This adds glue code in `raytwin-store`, `raytwin-dist` and `raytwin-py`.
- The rule "the core has no I/O" needs a check. cargo-deny bans the I/O crates in the core ([ARCHITECTURE §6.2](../ARCHITECTURE.md#62-allowed-to-use-rules)).
- The service-quality layer runs in one client process. A very large scenario sweep runs in parallel processes on the client, not on the workers.

**Neutral**

- Library mode has no queue. A crash in library mode loses the job. The user runs the job again with the same seed and gets the same result.

## Alternatives considered

**Separate engines for each mode.** Each engine could fit its runtime better. Rejected because two physics codes double the oracle work for one person, and Gate 2 compares results that must agree.

**A `TaskQueue` trait with an in-memory `LocalQueue` ([TR §10.3](../../technical-report.html#kt-che-do)).** The two modes would share one code path for task dispatch. Rejected because library mode uses no queue feature. A parallel iteration over the task list does the same work with no extra type.

**The core only as a service.** Library mode would call a local service, so only one runtime would exist. Rejected because notebooks and CI would then need a broker and an object store, and library mode must not need them.

**A `qos` task kind in the core.** Workers would run service-quality jobs. Rejected for release 0.2, because one evaluation costs much less than one ray trace ([TR §17.6](../../technical-report.html#qos-danh-gia)). A measurement can change this decision.
