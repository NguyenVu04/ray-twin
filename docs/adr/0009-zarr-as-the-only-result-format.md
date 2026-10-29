# 9. Zarr as the only result format

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Nguyễn Duy Vũ
- **Supersedes:** —
- **Superseded by:** —

## Context

The TR stores radio maps in Zarr and CIRs in Parquet ([TR §13.2](../technical-report.html#cir-thiet-ke), criterion 3 in [TR §14.3](../technical-report.html#mvp-tieu-chi)).

Radio maps, material fields and parts are dense N-dimensional arrays. The CIR is also dense: `a[rx, rx_ant, tx, tx_ant, path, band]` and `τ[rx, rx_ant, tx, tx_ant, path]`. The path count differs between links, so a dense array needs padding and a validity mask.

MDT input is a table. The calibration loop reads it in Python. Parquet support in Rust adds the `arrow` and `parquet` crates to every wheel on three operating systems.

## Decision

1. RayTwin writes all results in Zarr v3 through `zarrs`:
   - radio maps `[band, tx, z, y, x]` and measurement planes
   - CIR and CFR arrays
   - path metadata (interaction kinds, vertices, primitive ids) as padded arrays
   - tapes, material fields and parts
2. The path axis has the length of the largest path count in the array. A boolean array `valid[..., path]` marks the real paths. RayTwin does not write chunks that contain only fill values.
3. `raytwin-core` and `raytwin-store` do not depend on `arrow` or `parquet`.
4. MDT input stays in Parquet. `raytwin.calib` reads it with `pyarrow`.

## Consequences

**Positive**

- RayTwin has one result format, one crate, one chunk model and one reader.
- The dependency tree is smaller, so the wheels build faster on three operating systems.
- The CIR arrays on disk have the same shape as the arrays that Python receives.

**Negative**

- A table query (DuckDB, pandas) on path lists needs a conversion step first.
- Padding uses space when path counts differ much between links. Compression and the omission of empty chunks reduce that cost.
- TR criterion 3 changes from "read back from Parquet" to "read back from Zarr".

**Neutral**

- A user can export CIR arrays to Parquet in Python.

## Alternatives considered

**Zarr for maps, Parquet for CIR ([TR §13.2](../technical-report.html#cir-thiet-ke)).** Path lists are easy to query as tables. Rejected because it adds a second format with two read and write paths, and it adds `arrow` and `parquet` to the Rust build.
