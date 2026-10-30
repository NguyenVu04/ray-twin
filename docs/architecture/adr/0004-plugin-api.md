# 4. Plugin API

- **Status:** Accepted
- **Date:** 2026-10-29
- **Updated:** 2026-10-30
- **Deciders:** Nguyễn Duy Vũ

## Context

The first draft of the design listed six extension traits for the physics: `Backend`, `MaterialField`, `InteractionModel`, `AntennaPattern`, `RadioMapSink` and `TaskQueue`. The design review of 2026-10-29 found these problems:

- WGSL shaders cannot call Rust trait objects. A plugin for `MaterialField`, `AntennaPattern` or `InteractionModel` cannot run on a GPU backend.
- The GPU accumulates with atomics in VRAM. It cannot call back to a `RadioMapSink` on the CPU.
- The correct shape of `InteractionModel` is not known before the design of diffuse scattering and diffraction. Diffraction acts on edges, not on hit points.
- `TaskQueue` has only one implementation ([ADR 0001](0001-one-core-two-runtime-modes.md)).

Release 0.2 adds a service-quality layer. Its association, link, sharing, mobility and scenario models are policies that each operator and each researcher wants to replace. Measurement data, configuration data, antenna patterns and city models come in formats that change from vendor to vendor. On 2026-10-30 the owner accepted the plugin features PL-01 to PL-11 and rejected PL-12.

## Decision

1. Release 0.1 has no public plugin API. `Backend` is the only trait, an internal seam with three implementations (`Cpu`, `GpuCompute`, `GpuRayQuery`). Materials, antenna patterns, interactions and map accumulation are concrete types.
2. From release 0.2, a code plugin is a Python distribution that declares an entry point ([PyPA entry points specification](https://packaging.python.org/specifications/entry-points)). The module `raytwin.plugins` finds plugins with `importlib.metadata.entry_points(group=…)`. The groups are:

   | # | Group | Plugin supplies | Release |
   |---|---|---|---|
   | PL-01 | `raytwin.mdt_readers` | Reader of MDT, PM or CM data to the canonical MDT schema | 0.2 |
   | PL-02 | `raytwin.qos.association` | Cell selection for each user | 0.2 |
   | PL-03 | `raytwin.qos.link` | Map from SINR to rate | 0.2 |
   | PL-04 | `raytwin.qos.sharing` | Sharing of cell resources between users | 0.2 |
   | PL-05 | `raytwin.qos.mobility` | Trajectories and handover decision | 0.2 |
   | PL-06 | `raytwin.qos.scenario` | User population and traffic | 0.2 |
   | PL-07 | `raytwin.kpi`, `raytwin.exporters` | KPI definitions; export of results to other formats | 0.2 |
   | PL-08 | `raytwin.pattern_readers` | Reader of vendor antenna files to a pattern table | 0.3 |
   | PL-10 | `raytwin.scene_importers` | Converter of city models to the scene format | 0.3 |
   | PL-11 | `raytwin.son.policies` | SON policy that proposes configurations | 0.3 |

3. A data plugin is a table, not code. Tabulated antenna patterns (PL-08) and material tables (PL-09) enter the snapshot as inputs with a hash ([ADR 0002](0002-snapshot-identity-and-path-based-storage.md)). The core interpolates them with the same rule on the CPU and the GPU. This keeps the CPU–GPU agreement within 10⁻⁴.
4. Every code plugin obeys this contract:
   - It declares `api_version`, `name` and `version`. The host refuses a plugin with an unsupported `api_version` and gives the reason.
   - Its parameters are JSON values. The tuple (name, version, parameters) goes into the job spec, so it changes the job id. An exporter does not change a result, so it is not part of the job id.
   - It uses only the `numpy.random.Generator` that the host gives it. It does not read the clock, the network or a global random state.
   - The conformance check `raytwin.plugins.check` runs the plugin two times, and once with the input rows in a different order. The outputs must be bit-identical.
5. Code plugins run only in the client Python process. The Rust crates load no plugin code. Workers never run plugin code.
6. RayTwin provides none of these:
   - physics plugins (PL-12); diffraction and diffuse scattering stay in the core;
   - shader plugins in WGSL;
   - Rust libraries loaded at run time;
   - a WebAssembly sandbox.

## Consequences

**Positive**

- A new vendor format or a new policy needs no change of the core and no new release of RayTwin.
- The GPU backends do not change. No plugin can break the CPU–GPU agreement, because the GPU sees only tables.
- Plugin discovery uses the standard library. RayTwin adds no dependency for it.
- Plugin identity in the job id keeps cached results correct when a plugin changes.

**Negative**

- From release 0.2, the plugin groups are a public API. A change needs a new `api_version`.
- A plugin has all the rights of the client process. The user decides which packages to install, as with any Python package.
- A new physics model needs a change of the core.
- Users cannot add vendor antenna patterns before release 0.3.

**Neutral**

- `Backend` stays an internal trait, because three implementations use it.
- The built-in models of `raytwin.qos` register through the same entry points as external plugins.

## Alternatives considered

**Public Rust traits in release 0.1, with plugins that run only on the CPU.** Users could extend the physics early. Rejected for release 0.1, because the public API would freeze before the diffraction design.

**Plugins that supply WGSL code.** Every plugin could run on the GPU. Rejected because the shader interface would become a public API, and determinism would be hard to test.

**Rust libraries loaded at run time.** Plugins would run in the workers. Rejected because Rust has no stable ABI, so each plugin must match the exact compiler and crate versions.

**A WebAssembly sandbox on the workers.** Untrusted plugins could run on the workers with resource limits. Rejected because no plugin runs on the workers. Reconsider it if third-party code must run there.

**Physics plugins as Rust crates behind a cargo feature (PL-12).** Researchers could add diffraction models in their own builds. Rejected by the owner on 2026-10-30.
