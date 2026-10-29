# 2. Snapshot identity and path-based storage

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Nguyễn Duy Vũ
- **Supersedes:** —
- **Superseded by:** —

## Context

A manifest describes every input of one simulation. The hash of the manifest identifies the snapshot, and workers cache inputs by content hash ([TR §10.2](../technical-report.html#kt-du-lieu)).

TR criterion 1 requires that the same scene gives the same hash from local disk, from MinIO and from S3 ([TR §14.3](../technical-report.html#mvp-tieu-chi)). The example manifest in TR §10.2 contains URIs. A hash over that manifest changes when only the location changes. The example also identifies the material field by a version number. A number does not prove the content.

Two storage layouts were possible:

1. Content-addressed storage. RayTwin copies each input to a key that is its hash, and readable names are references to hashes.
2. Path-based storage. Each input stays at the path that the user selects, and the manifest records its hash.

## Decision

1. The snapshot id is the BLAKE3 hash of the canonical manifest (RFC 8785 JSON canonicalization), with every `uri` field removed.
2. Each input appears in the manifest as a pair `{uri, hash}`. The URI tells RayTwin where to read. The hash tells RayTwin what it must read.
3. Inputs stay at the paths that the user selects. RayTwin does not copy them.
4. RayTwin calculates the BLAKE3 hash of an input when it reads the input. If the hash does not agree with the manifest, RayTwin stops with an error. A worker does this check one time, when it puts the input into its local cache.
5. RayTwin writes every object with create-only semantics (`PutMode::Create` in `object_store`). RayTwin never overwrites an object. If the object exists and its hash agrees, the write counts as a success.
6. Hash rules:
   - A scene hash covers the XML file and each referenced PLY file, in reference order.
   - A Zarr hash covers the array metadata and all chunks, in sorted key order. `raytwin-store` calculates it when it writes the array.
7. RayTwin writes its own objects under fixed keys: `snapshots/`, `fields/<name>/v<N>.zarr`, `calib/`, and `jobs/<job-id>/`. [ARCHITECTURE §6.5](../architecture/ARCHITECTURE.md#65-raytwin-store) lists the layout.

## Consequences

**Positive**

- The same content gives the same snapshot id on local disk, on MinIO and on S3.
- Import needs no copy, and users keep their own bucket layout.
- RayTwin itself cannot damage an earlier snapshot, because it never overwrites an object.
- A redelivered task writes the same part again. Create-only writes with the hash check make that second write a safe no-op.

**Negative**

- Immutability of user inputs is only a convention. If a person or another tool overwrites an input, every snapshot that uses it fails the hash check. RayTwin detects the damage but cannot repair it.
- Each new input costs one full hash pass when a worker caches it.
- Create-only writes need conditional PUT in the object store. A store without conditional PUT cannot be a RayTwin target.
- Version numbers in field paths need a counter. If two writers select the same next number, the second writer gets `AlreadyExists` with a different hash. It must try again with the next number.

**Neutral**

- RayTwin deletes nothing in the MVP. Objects that no snapshot uses stay in the bucket ([ARCHITECTURE §12](../architecture/ARCHITECTURE.md#12-open-items)).

## Alternatives considered

**Content-addressed blobs with named references.** The structure itself guarantees immutability and removes duplicates. Rejected by the owner because import must copy every input, the bucket is hard to read by eye, and unused blobs need garbage collection. Hash checks with create-only writes protect every object that RayTwin writes.

**A manifest hash that includes the URIs.** This is the simplest rule. Rejected because one content at two locations gets two ids. That breaks TR criterion 1 and the worker cache by content.

**Field versions identified only by number.** Numbers are easy to read. Rejected because a number does not prove which content a snapshot used.
