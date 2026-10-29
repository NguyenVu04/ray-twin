# 4. Work distribution with NATS JetStream

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Nguyễn Duy Vũ
- **Supersedes:** —
- **Superseded by:** —

## Context

Distributed mode splits one job into tasks and runs the tasks on many workers ([TR §10.4](../technical-report.html#kt-jetstream)). A task is heavy. One ray batch can run longer than 30 seconds. A worker can stop at any time. A task that always fails must not run without limit.

These JetStream defaults shape the design:

- WorkQueue retention deletes a message at its first acknowledgement.
- `AckWait` is 30 seconds.
- `MaxDeliver` is −1, which means no limit.
- `max_payload` is 1 MB.

The owner accepted NATS JetStream with pull consumers ([TR Appendix A](../technical-report.html#quyet-dinh)). On 2026-10-29 the owner also decided two things. Calibration tapes run in distributed mode too ([ADR 0008](0008-calibration-on-frozen-paths-in-pytorch.md)). A client can cancel a job ([ADR 0005](0005-nats-as-the-client-protocol.md)), so the coordinator needs a way to remove the queued tasks of one job.

## Decision

1. The stream `RAYTWIN_TASKS` has WorkQueue retention and the subjects `raytwin.tasks.<job>.<task>`.
2. One durable pull consumer, `workers`, with the filter `raytwin.tasks.>`, serves all workers. Each fetch takes one message.
3. `AckWait` is 30 seconds. A worker sends an in-progress acknowledgement every 10 seconds. `MaxDeliver` is 5. The coordinator listens to the max-deliveries advisory and marks the job as failed.
4. A task message contains only references. These are the job id, the task index, the kind, the snapshot id, the manifest URI and the transmitter. They also include the ray range or the receiver range, the scale s and the part key.
5. Three task kinds exist:

   | Kind | Split | Merge |
   |---|---|---|
   | `radio_map` | Transmitter × ray batch | Integer addition ([ADR 0003](0003-deterministic-monte-carlo-with-fixed-point-accumulation.md)) |
   | `paths` | Transmitter × receiver group | Concatenation in task order |
   | `tape` | Transmitter × group of measurement samples | Concatenation in task order |

6. A worker does the last three steps of a task in this order:
   1. It writes the part with a create-only write ([ADR 0002](0002-snapshot-identity-and-path-based-storage.md)).
   2. It publishes a completion event to the stream `RAYTWIN_EVENTS`, with the message id `<job>.<task>`.
   3. It acknowledges the task.
7. A worker handles errors by kind:
   - A transient I/O error gets a `nak` with a delay.
   - A hash mismatch or an invalid task gets a `term` and a failure event with the reason.
   - A panic gets no acknowledgement, so JetStream delivers the task again until `MaxDeliver`.

## Consequences

**Positive**

- A fast worker takes more tasks. A new worker needs no change to the coordinator.
- JetStream gives the task of a stopped worker to another worker after `AckWait`. The new worker calculates the same part ([ADR 0003](0003-deterministic-monte-carlo-with-fixed-point-accumulation.md)).
- Per-job subjects let the coordinator purge all queued tasks of a cancelled job in one call.
- `paths` and `tape` tasks need no global deduplication, because each receiver belongs to exactly one task.

**Negative**

- NATS is one more service to operate. Library mode does not need it.
- A `paths` or `tape` task traces the full SBR of its transmitter. A split into k receiver groups traces k times.
- A permanently failing task costs 5 attempts before the job fails.
- A worker must send acknowledgements while it calculates. The calculation runs on a blocking thread, and the acknowledgement timer runs on the async runtime.

**Neutral**

- The MVP runs one JetStream node in Docker Compose. The broker has no redundancy.

## Alternatives considered

**The coordinator pushes tasks to workers.** The coordinator controls placement exactly. Rejected because the coordinator must then track worker load and worker failures itself.

**Split `paths` tasks by ray batch.** All task kinds would split the same way. Rejected because two workers can find the same path, and a global deduplication becomes necessary ([TR §10.4](../technical-report.html#kt-jetstream)).

**Large data inside messages.** A worker would need no object-store read. Rejected because `max_payload` is 1 MB, and NATS does not recommend more than 8 MB.
