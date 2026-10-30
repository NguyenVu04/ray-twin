# 2. Snapshot identity and path-based storage

- **Status:** Accepted
- **Date:** 2026-10-29
- **Updated:** 2026-10-30
- **Deciders:** Nguyễn Duy Vũ

## Context

A manifest describes every input of one simulation. The hash of the manifest identifies the snapshot, and workers cache inputs by content hash.

The completion criteria of component 1 require that the same scene gives the same hash from local disk, from MinIO and from S3. The example manifest of the first draft contains URIs. A hash over that manifest changes when only the location changes. The example also identifies the material field by a version number. A number does not prove the content.

Two storage layouts were possible:

1. Content-addressed storage. RayTwin copies each input to a key that is its hash, and readable names are references to hashes.
2. Path-based storage. Each input stays at the path that the user selects, and the manifest records its hash.

The design review of 2026-10-30 added three needs:

- RSRP, SINR and service quality need radio parameters, for example the reference-signal power and the cell individual offset. These parameters do not change the ray paths. A change of them must not cause a new ray trace.
- A planning engineer edits a configuration in small steps and must be able to go back to an earlier step.
- Real measurement data has geographic coordinates. The scene needs a coordinate reference.

## Decision

1. The snapshot id is the BLAKE3 hash of the canonical manifest (RFC 8785 JSON canonicalization), with every `uri` field removed.
2. Each input appears in the manifest as a pair `{uri, hash}`. The URI tells RayTwin where to read. The hash tells RayTwin what it must read.
3. Inputs stay at the paths that the user selects. RayTwin does not copy them.
4. RayTwin calculates the BLAKE3 hash of an input when it reads the input. If the hash does not agree with the manifest, RayTwin stops with an error. A worker does this check one time, when it puts the input into its local cache.
5. RayTwin writes every object with create-only semantics (`PutMode::Create` in `object_store`). RayTwin never overwrites an object. If the object exists and its hash agrees, the write counts as a success.
6. Hash rules:
   - A scene hash covers the XML file and each referenced PLY file, in reference order.
   - A Zarr hash covers the array metadata and all chunks, in sorted key order. `raytwin-store` calculates it when it writes the array.
7. The snapshot holds only the inputs of the ray trace:
   - the scene, with an optional coordinate reference `crs` (EPSG code and the origin of the scene coordinates);
   - the material field, and from release 0.3 the material tables;
   - the bands;
   - the transmitters: position, azimuth, tilt, antenna array and pattern, and from release 0.3 tabulated patterns;
   - the solver settings and the seed.
8. Radio parameters that act only when a result is read are in a separate **RAN config** document, `raytwin.ran/v1`, with its own hash:
   - Release 0.1: reference-signal EPRE per cell and band, the on/off state of each cell, noise figure, UE antenna gain and body loss.
   - Release 0.2: also the cell individual offset, the handover parameters and the resource grid.

   A change of the RAN config makes no new snapshot and no new trace. A value that depends on it (RSRP, SINR, service quality) is identified by the pair (job id, RAN config hash).
9. An edit never changes a snapshot or a RAN config in place. A `ConfigDelta` (`raytwin.delta/v1`) applied to one of them gives a new document with a new hash. The delta can add, remove or change a transmitter, or change RAN parameters.
10. A named reference records the history of a plan. Each entry is an object `refs/<name>/<seq>.json` with the snapshot id, the RAN config hash, the parent entry, the delta, a message, the author and the time.
    - The writer selects the next free `seq`, with the same rule as field versions.
    - The head is the entry with the highest `seq`.
    - A rollback writes a new entry that points to an earlier pair. RayTwin deletes no entry.
11. From release 0.3, the result of one transmitter has its own key. The key is the canonical hash of the trace inputs of that transmitter: scene, field, that transmitter, bands, solver settings and grid. It contains no RAN parameter ([ADR 0003](0003-deterministic-monte-carlo-with-fixed-point-accumulation.md)).
12. RayTwin writes its own objects under fixed keys: `snapshots/`, `ran/`, `refs/`, `fields/<name>/v<N>.zarr`, `calib/` and `jobs/<job-id>/`. [ARCHITECTURE §6.5](../ARCHITECTURE.md#65-raytwin-store) lists the layout.

## Consequences

**Positive**

- The same content gives the same snapshot id on local disk, on MinIO and on S3.
- Import needs no copy, and users keep their own bucket layout.
- RayTwin itself cannot damage an earlier snapshot, because it never overwrites an object.
- A redelivered task writes the same part again. Create-only writes with the hash check make that second write a safe no-op.
- A change of power, offset or handover parameters needs no trace.
- History and rollback need no database. They work in library mode and in distributed mode. A rollback finds the earlier results by job id, so it calculates nothing again.

**Negative**

- Immutability of user inputs is only a convention. If a person or another tool overwrites an input, every snapshot that uses it fails the hash check. RayTwin detects the damage but cannot repair it.
- Each new input costs one full hash pass when a worker caches it.
- Create-only writes need conditional PUT in the object store. A store without conditional PUT cannot be a RayTwin target.
- Version numbers and reference entries need a counter. If two writers select the same next number, the second writer gets `AlreadyExists` with a different hash. It must try again with the next number.
- A result of RSRP or service quality has two identities, the job and the RAN config. The API must carry both.
- To find the head of a reference, the reader lists its prefix. The list grows with each edit.

**Neutral**

- RayTwin deletes nothing in the MVP. Objects that no snapshot uses stay in the bucket ([ARCHITECTURE §12](../ARCHITECTURE.md#12-open-items)).

## Alternatives considered

**Content-addressed blobs with named references.** The structure itself guarantees immutability and removes duplicates. Rejected by the owner because import must copy every input, the bucket is hard to read by eye, and unused blobs need garbage collection. Hash checks with create-only writes protect every object that RayTwin writes.

**A manifest hash that includes the URIs.** This is the simplest rule. Rejected because one content at two locations gets two ids. That breaks the criteria of component 1 and the worker cache by content.

**Field versions identified only by number.** Numbers are easy to read. Rejected because a number does not prove which content a snapshot used.

**Radio parameters in the manifest.** One document would hold every input. Rejected because a change of power or offset would change the snapshot id and start a new trace, although the ray paths stay the same.

**A mutable "current configuration" object.** It is simple to read. Rejected because an overwrite loses the history, and RayTwin writes no object two times.
