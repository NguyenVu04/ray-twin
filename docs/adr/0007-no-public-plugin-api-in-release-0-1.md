# 7. No public plugin API in release 0.1

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Nguyễn Duy Vũ
- **Supersedes:** —
- **Superseded by:** —

## Context

[TR §10.6](../technical-report.html#kt-plugin) lists six extension traits: `Backend`, `MaterialField`, `InteractionModel`, `AntennaPattern`, `RadioMapSink` and `TaskQueue`. Component 10 requires stable traits and a sample plugin in a separate crate ([TR §14.3](../technical-report.html#mvp-tieu-chi)).

The design review of 2026-10-29 found these problems:

- WGSL shaders cannot call Rust trait objects. A plugin for `MaterialField`, `AntennaPattern` or `InteractionModel` cannot run on a GPU backend.
- `RadioMapSink::accumulate` is a callback for each contribution. The GPU accumulates with atomics in VRAM and cannot call back to the CPU.
- `RadioMapSink::merge(&mut self, other: &Self)` makes the trait not dyn-compatible. `Backend::trace_map` takes `&mut dyn RadioMapSink`, so the signatures do not compile together.
- The correct shape of `InteractionModel` is not known before the design of diffuse scattering and diffraction. Diffraction acts on edges, not on hit points.
- After [ADR 0001](0001-one-core-two-runtime-modes.md), `TaskQueue` has only one implementation.

## Decision

1. Release 0.1 has no public plugin API. No trait carries a stability promise.
2. A trait exists only as an internal seam with two or more implementations. In the MVP that is only `Backend` (`Cpu`, `GpuCompute`, `GpuRayQuery`).
3. The other extension points become concrete types:
   - `MaterialField` is a struct: ITU prior per class plus the δ grid.
   - `AntennaPattern` is an enum: isotropic, dipole, TR 38.901.
   - Interactions are functions: specular reflection and thin-slab transmission.
   - Map accumulation is an enum: voxel grid and measurement plane.
4. Component 10 drops the sample-plugin criterion. It keeps the documentation and the release.
5. This direction applies after the MVP. It does not bind the plugin API:
   1. Plugin traits keep the signatures of the internal types, for example `MaterialField::eval(x, class, f)`.
   2. First, a job that uses a plugin runs on the CPU backend. The `auto` setting selects the CPU and logs why.
   3. Next, the core samples the plugin into a grid or a table when it loads the snapshot. The GPU interpolates that data. The CPU uses the same data, so the CPU–GPU agreement stays inside 10⁻⁴.
   4. A new ADR records the plugin API when it starts.

## Consequences

**Positive**

- The public API is smaller, so 0.x releases can change internal code freely.
- The interaction model does not freeze before the diffraction design exists.
- No feature in 0.1 works on the CPU but not on the GPU.

**Negative**

- Users cannot add vendor antenna patterns or new material models without a change to the core.
- The scope of TR component 10 changes.
- A later release must design the plugin API from the start.

**Neutral**

- `Backend` stays a trait, because three implementations use it.

## Alternatives considered

**Public traits, with plugins that run only on the CPU.** Users could extend RayTwin in 0.1. Rejected by the owner for release 0.1.

**Plugins as sampled data in 0.1.** Plugin patterns and fields would run on the GPU. Rejected for 0.1 because vendor patterns are outside the MVP, and the table kernel is extra work now.

**Plugins that supply WGSL code.** Every plugin could run on the GPU. Rejected because the shader interface would become a public API, and determinism would be hard to test.
