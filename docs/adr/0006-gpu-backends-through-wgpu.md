# 6. GPU backends through wgpu

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Nguyễn Duy Vũ
- **Supersedes:** —
- **Superseded by:** —

## Context

The MVP must run on CPU and on GPU ([TR §10.7](../technical-report.html#kt-gpu)). The development GPU is an RTX 3050 Ti with 4 GB of VRAM.

Facts about the GPU options for Rust ([TR §9](../technical-report.html#rust)):

- The Rust CUDA and OptiX bindings are in an early stage.
- In wgpu 30.0.1, ray query is experimental and only available on Vulkan.
- `SHADER_F64` is only available on Vulkan.
- 64-bit integer atomics are available on Vulkan and DX12.

The CIR criterion |Δτ| ≤ 1 ps needs f64 in the image method. Each GPU path must be bit-identical between runs and within 10⁻⁴ of the CPU.

[TR §10.7](../technical-report.html#kt-gpu) also proposes two 32-bit atomics with carry to emulate a 64-bit add. The backend selection in the same section already requires 64-bit atomics for the compute path.

## Decision

1. Three backends implement the internal trait `Backend`:
   - `Cpu` uses `rayon` and `obvhs`. It is the reference.
   - `GpuCompute` uses WGSL compute shaders with its own BVH traversal.
   - `GpuRayQuery` uses WGSL with `EXPERIMENTAL_RAY_QUERY`, which uses RT cores.
2. The two GPU paths share one wavefront pipeline and its shaders. They differ only in the intersection step.
3. The full pipeline runs on the GPU. This includes the image method per element pair in f64 and the occlusion tests.
4. The `auto` setting tries the backends in this order and logs why it skips each one:
   1. `GpuRayQuery`, if a Vulkan adapter has ray query, f64 and 64-bit atomics.
   2. `GpuCompute`, if a Vulkan adapter has f64 and 64-bit atomics.
   3. `Cpu`.
5. RayTwin has no 32-bit emulation of 64-bit atomics. An adapter without 64-bit atomics uses the CPU backend.
6. The CPU backend and the compute shader use the same watertight ray–triangle test.
7. The GPU code is in `raytwin-core` behind the cargo feature `gpu`. The Linux and Windows wheels enable the feature. The macOS wheel does not.
8. The workspace pins one wgpu version.

## Consequences

**Positive**

- One GPU API serves Vulkan now, and it can serve Metal and DX12 later.
- The ray query path uses RT cores. The compute path still works where ray query fails.
- The CPU backend stays the reference for every comparison.

**Negative**

- Ray query is experimental. A wgpu upgrade can contain breaking changes or serious defects.
- In the MVP, the GPU backends run only on Linux and Windows.
- FP64 on GeForce GPUs is slow, so the image method on the GPU is slow.
- Three backends are a scope risk for one person ([TR §15](../technical-report.html#rui-ro)).
- RT-core hits can differ from CPU hits on grazing rays. Reports must give the rate of different hit or miss results.

**Neutral**

- The MVP measures and reports GPU performance. It sets no performance target.

## Alternatives considered

**CUDA and OptiX through Rust CUDA.** These give the most mature NVIDIA ray tracing. Rejected because the Rust project is in an early stage, and it supports only NVIDIA hardware.

**CPU only in the MVP.** This removes most of the scope risk. Rejected by the owner, who requires the GPU in the MVP.

**Ray query only.** This gives one GPU path. Rejected because the feature is experimental and has no alternative path if it fails.

**Emulation of 64-bit atomics with two 32-bit atomics ([TR §10.7](../technical-report.html#kt-gpu)).** More adapters could use the GPU. Rejected because the backend selection already sends those adapters to the CPU. The emulation would be code that no supported path runs.
