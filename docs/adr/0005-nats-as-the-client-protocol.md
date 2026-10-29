# 5. NATS as the client protocol

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Nguyễn Duy Vũ
- **Supersedes:** —
- **Superseded by:** —

## Context

A client submits a job to the coordinator and waits for the result. [TR §10.5](../technical-report.html#kt-api) and [TR §14.1](../technical-report.html#mvp-pham-vi) put a gRPC client API (`tonic`) in the MVP.

The coordinator already connects to NATS for tasks and events ([ADR 0004](0004-work-distribution-with-nats-jetstream.md)). A gRPC API adds `tonic`, `prost`, protobuf code generation, a listening port, and authentication and TLS work.

A SON application can send the same request again after a timeout. On 2026-10-29 the owner asked for job cancellation.

## Decision

1. Clients talk to the coordinator only through NATS. The MVP has no gRPC API.
2. A client submits a job with a request on `raytwin.jobs.submit`.
   - The request is a job spec in JSON, schema `raytwin.job/v1`.
   - The reply is the job id and its state, or a validation error.
3. The job id is the BLAKE3 hash of the canonical job spec without `uri` fields. This is the same rule as for snapshots ([ADR 0002](0002-snapshot-identity-and-path-based-storage.md)).
4. A second submission of the same job spec gets the same job id. The coordinator then acts by state:
   - `queued` or `running`: it replies with the current state.
   - `done`: it replies with the result.
   - `failed` or `cancelled`: it starts the job again. Parts that exist count as written.
5. The KV bucket `RAYTWIN_JOBS` holds the job state under the key `job.<id>`.
   - The value contains the state, the task counts, the result URI and the error.
   - The states are `queued`, `running`, `done`, `failed` and `cancelled`.
   - Only the coordinator writes the value. Clients watch the key.
6. A client cancels a job with a request on `raytwin.jobs.cancel`. The coordinator does these steps in this order:
   1. It sets the state to `cancelled`.
   2. It purges the subjects `raytwin.tasks.<job>.>`.
   3. It replies to the client.
7. A worker reads the job state when it starts a task and at each in-progress acknowledgement. If the state is `cancelled`, the worker stops between two sub-batches of rays and sends `term`. The coordinator ignores events of a cancelled job.
8. The coordinator and the workers open no listening port. They make only outbound connections to NATS and to the object store.

## Consequences

**Positive**

- RayTwin uses one messaging protocol, with no code generation.
- NATS authentication (user and password, nkeys, JWT accounts) also covers clients.
- Clients get progress from a KV watch, with no extra server code.
- A second submission of the same job is safe.
- RayTwin processes expose no inbound port.

**Negative**

- Clients need network access and credentials for the NATS server.
- The contract is a JSON Schema, not protobuf types. The coordinator must check every request at the trust boundary.
- An integrator needs a NATS client library. A later gRPC or REST gateway is one more component.
- Cancellation is cooperative. A running task stops within one in-progress interval (10 seconds) plus one sub-batch, not at once.
- Parts of a cancelled job stay in the object store.

**Neutral**

- The Python client wraps `async-nats` inside `raytwin-py`. The Python package needs no extra dependency for it.

## Alternatives considered

**gRPC with `tonic` ([TR §10.5](../technical-report.html#kt-api)).** The contract is typed, and external systems know gRPC well. Rejected for the MVP because it adds a second protocol stack for one Python client, and RayTwin would have to build authentication itself.

**An HTTP REST API.** Every language can call it. Rejected because it has the same costs as gRPC, and it gives no state stream.

**No cancellation.** This is less code. Rejected by the owner.
