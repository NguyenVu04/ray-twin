# 3. Deterministic Monte Carlo with fixed-point accumulation

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Nguyễn Duy Vũ
- **Supersedes:** —
- **Superseded by:** —

## Context

SBR is a Monte Carlo method. SON compares candidate configurations, for example two tilt values. The Monte Carlo noise can be larger than the difference that SON must measure ([TR §3](../technical-report.html#boi-canh)).

The accepted criteria ([TR §14.3](../technical-report.html#mvp-tieu-chi)) are:

- The same seed gives a bit-identical result for any number of CPU threads.
- Each GPU path is bit-identical between runs and within 10⁻⁴ (relative) of the CPU.
- Four workers agree with one worker within 10⁻⁶ (relative).

[TR §10.7](../technical-report.html#kt-gpu) takes random numbers from the key (job, Tx, ray id, bounce). Two jobs that compare two configurations have different job ids, so they get different random numbers. TR §10.7 also uses fixed-point accumulation only on the GPU. A floating-point sum depends on the order of its terms. Thread count, worker count and merge order can then change the last bits of a CPU result.

## Decision

1. A counter-based generator (Philox 4x32-10) supplies all random numbers.
   - The key is (manifest seed, 64-bit hash of the transmitter id).
   - The counter is (global ray index, bounce, draw index).
   - The job id and the batch index are not part of the key or the counter.
2. Ray directions come from the Fibonacci lattice for the configured ray count. Ray *i* has the same direction in every job with the same ray count.
3. Russian roulette and the selection of an interaction use the path throughput without the transmitter antenna gain. Thus a change of tilt, azimuth or transmit power changes the weight of each ray, but not its path.
4. Every backend accumulates radio-map contributions as 64-bit integers, q = round(P·ℓ / s). The CPU backend, both GPU paths and every stored part use this representation. A merge of two parts is an integer addition.
5. The job planner calculates the scale s one time per job, from the manifest (transmit power, ray count, voxel size), before any task starts. Every task of the job carries the same s.
6. The merge converts the integer sum to f32 path gain one time, after the last part arrives.

## Consequences

**Positive**

- The result does not depend on thread count, worker count, batch size, task order or merge order. Gate 2 gets bit-identical results, which is stronger than 10⁻⁶.
- The coordinator can merge parts in any order.
- Two jobs with the same seed, geometry, materials and ray count trace the same rays. The difference between two tilt values has no path-sampling noise (common random numbers).
- CPU and GPU share one accumulation rule. The remaining CPU–GPU difference comes only from the floating-point value of each contribution and from grazing hits.
- CPU workers and GPU workers in one job write parts in the same format.

**Negative**

- A contribution smaller than s rounds to zero. The dynamic range is about 190 dB less the overflow headroom. This is sufficient for RSRP maps, but very weak voxels lose precision.
- A part uses 8 bytes per voxel instead of 4. Part memory and part storage double.
- The formula for s must prevent overflow. Component 4 must test the formula ([ARCHITECTURE §12](../architecture/ARCHITECTURE.md#12-open-items)).
- Common random numbers apply only to changes that keep the geometry, the material field, the transmitter positions and the ray count. Other changes change the paths.

**Neutral**

- The CPU reference uses the same quantization as the GPU. The oracle comparison uses the converted f32 result.

## Alternatives considered

**Fixed-point on the GPU only, f64 sums on the CPU.** The CPU reference has no quantization. Rejected because two determinism mechanisms need separate tests. Also, the coordinator must merge in task order, and jobs with CPU and GPU workers need two part formats.

**Floating-point atomics on the GPU.** This is faster and simpler. Rejected because the sum depends on thread order, so two runs are not bit-identical.

**A key that contains the job id ([TR §10.7](../technical-report.html#kt-gpu)).** Different jobs get independent random numbers. Rejected because SON comparisons need common random numbers between jobs.
