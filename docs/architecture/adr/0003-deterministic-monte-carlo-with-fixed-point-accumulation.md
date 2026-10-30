# 3. Deterministic Monte Carlo with fixed-point accumulation

- **Status:** Accepted
- **Date:** 2026-10-29
- **Updated:** 2026-10-30
- **Deciders:** Nguyễn Duy Vũ

## Context

SBR is a Monte Carlo method. SON compares candidate configurations, for example two tilt values. The Monte Carlo noise can be larger than the difference that SON must measure.

The accepted criteria are:

- The same seed gives a bit-identical result for any number of CPU threads.
- Each GPU path is bit-identical between runs and within 10⁻⁴ (relative) of the CPU.
- Four workers agree with one worker within 10⁻⁶ (relative).

The first draft of the design takes random numbers from the key (job, Tx, ray id, bounce). Two jobs that compare two configurations have different job ids, so they get different random numbers. The draft also uses fixed-point accumulation only on the GPU. A floating-point sum depends on the order of its terms. Thread count, worker count and merge order can then change the last bits of a CPU result.

The design review of 2026-10-30 added two needs. The service-quality layer compares scenarios, so its random user populations need the same protection as the rays. Planning edits change one transmitter at a time, so the result of one transmitter must not depend on the others.

## Decision

1. A counter-based generator (Philox 4x32-10) supplies all random numbers of the trace.
   - The key is (manifest seed, 64-bit hash of the transmitter id).
   - The counter is (global ray index, bounce, draw index).
   - The job id, the batch index and the other transmitters are not part of the key or the counter.
2. Ray directions come from the Fibonacci lattice for the configured ray count. Ray *i* has the same direction in every job with the same ray count.
3. Russian roulette and the selection of an interaction use the path throughput without the transmitter antenna gain. Thus a change of tilt, azimuth or transmit power changes the weight of each ray, but not its path.
4. Every backend accumulates radio-map contributions as 64-bit integers, q = round(P·ℓ / s). The CPU backend, both GPU paths and every stored part use this representation. A merge of two parts of one transmitter is an integer addition.
5. The planner calculates one scale s for each transmitter, before any task starts. It uses only the trace inputs of that transmitter: ray count, voxel size and the peak gain of its antenna pattern. Every task of that transmitter carries the same s. Maps of two transmitters are never added as integers, so two scales do not conflict.
6. Each part also counts the ray segments in each voxel as a 32-bit integer (`segments`). The merge adds the counts. A reader uses the count to find the ray-sufficient cells (at least 100 segments).
7. The merge converts the integer sum to f32 path gain one time, after the last part arrives.
8. The result of one transmitter depends only on its own trace inputs and on the shared scene, field, bands, solver settings and grid. A cache can therefore reuse it when other transmitters change (release 0.3, [ADR 0002](0002-snapshot-identity-and-path-based-storage.md)).
9. The service-quality layer draws its random values (user positions, traffic, residual fading) from a generator with the key (scenario seed, model id). The key contains no network configuration. Two candidate configurations of one scenario thus see the same users.

## Consequences

**Positive**

- The result does not depend on thread count, worker count, batch size, task order or merge order. Gate 2 gets bit-identical results, which is stronger than 10⁻⁶.
- The coordinator can merge parts in any order.
- Two jobs with the same seed, geometry, materials and ray count trace the same rays. The difference between two tilt values has no path-sampling noise (common random numbers).
- A new site, a removed site or a new tilt changes only the result of that transmitter. The other results stay bit-identical.
- Service-quality comparisons have no user-sampling noise.
- CPU and GPU share one accumulation rule. The remaining CPU–GPU difference comes only from the floating-point value of each contribution and from grazing hits.
- CPU workers and GPU workers in one job write parts in the same format.

**Negative**

- A contribution smaller than s rounds to zero. The dynamic range is about 190 dB less the overflow headroom. This is sufficient for RSRP maps, but very weak voxels lose precision.
- A part uses 8 bytes per voxel and band instead of 4, plus 4 bytes per voxel for the segment count. Part memory and part storage increase.
- The formula for s must prevent overflow. Component 4 must test the formula ([ARCHITECTURE §12](../ARCHITECTURE.md#12-open-items)).
- Common random numbers apply only to changes that keep the geometry, the material field and the ray count. A change of the position of a transmitter changes the paths of that transmitter.

**Neutral**

- The CPU reference uses the same quantization as the GPU. The oracle comparison uses the converted f32 result.

## Alternatives considered

**Fixed-point on the GPU only, f64 sums on the CPU.** The CPU reference has no quantization. Rejected because two determinism mechanisms need separate tests. Also, the coordinator must merge in task order, and jobs with CPU and GPU workers need two part formats.

**Floating-point atomics on the GPU.** This is faster and simpler. Rejected because the sum depends on thread order, so two runs are not bit-identical.

**A key that contains the job id.** Different jobs get independent random numbers. Rejected because SON comparisons need common random numbers between jobs.

**One scale s for the whole job.** It is one number to store. Rejected because the scale would depend on all transmitters. A new site would then change the integer values of the other transmitters, and their results could not be reused.
