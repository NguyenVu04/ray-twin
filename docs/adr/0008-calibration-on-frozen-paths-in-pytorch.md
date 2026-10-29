# 8. Calibration on frozen paths in PyTorch

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Nguyễn Duy Vũ
- **Supersedes:** —
- **Superseded by:** —

## Context

Calibration estimates the material correction δ from RSRP samples ([TR §11](../technical-report.html#vat-lieu)). Automatic differentiation through a Rust ray tracer is experimental (`std::autodiff` needs nightly Rust).

The owner accepted a PyTorch loop over frozen paths ([TR §11.3](../technical-report.html#vl-pytorch)). With fixed paths, the predicted RSRP is an analytic function of δ. The design review of 2026-10-29 asked two more questions:

1. Where does the intensity physics of the loop live?
2. Do tapes run only in library mode? The owner decided that tapes also run in distributed mode.

## Decision

1. Rust traces with the current field and writes one tape for each measurement sample. A tape holds the paths, the hit points, the angles and the interaction kinds. It also holds 8 grid indices and 8 trilinear weights per hit, the path lengths, the antenna gains and the band.
2. `raytwin.calib` implements the intensity model in PyTorch: ITU prior plus δ, Fresnel coefficients, the thin-slab model and the incoherent sum. Autograd gives the gradients. Adam or L-BFGS updates δ.
3. A parity test runs in CI. For the same tape and δ = 0, the RSRP from PyTorch agrees with the RSRP from Rust within 10⁻⁶ (relative). A physics change on either side must keep this test green.
4. Tapes run in both modes:
   - In library mode, Rust gives NumPy views on its own memory, and `torch.from_numpy` uses them without a copy.
   - In distributed mode, the job kind `tape` ([ADR 0004](0004-work-distribution-with-nats-jetstream.md)) writes tape parts in Zarr ([ADR 0009](0009-zarr-as-the-only-result-format.md)). Python reads them into NumPy and then calls `torch.from_numpy`.
5. Every K iterations the loop traces again with the current δ. In distributed mode, Python first writes δ to `calib/<run>/iter-<k>.zarr` with a create-only write. Then it makes a new snapshot and submits a new `tape` job.
6. The final field goes to `fields/<name>/v<N>.zarr` ([ADR 0002](0002-snapshot-identity-and-path-based-storage.md)).

## Consequences

**Positive**

- A change of the loss, the regularization or the optimizer needs no Rust build.
- The design needs no automatic differentiation in Rust.
- The tape trace uses the same backends as every other job, CPU or GPU.

**Negative**

- The Fresnel and thin-slab formulas exist two times, in Rust and in PyTorch. The parity test is the only guard against drift.
- A tape does not see that the path set changes when the materials change. The loop must trace again at intervals.
- In distributed mode, tapes go through the object store, which adds a copy and some latency.
- Tape size grows with samples × paths × hits. Component 9 must measure it ([ARCHITECTURE §12](../architecture/ARCHITECTURE.md#12-open-items)).
- Intermediate fields stay in the object store, because the MVP deletes nothing.

**Neutral**

- PyTorch and pyarrow are an optional extra, `raytwin[calib]`.

## Alternatives considered

**Rust forward model with an analytic gradient, wrapped as a `torch.autograd.Function`.** The physics has one source, and it runs faster. Rejected because the complex derivatives of the slab model need manual derivation and `gradcheck` tests, and each model change needs a Rust build.

**Automatic differentiation in Rust (Enzyme on nightly, burn or candle).** The full tracer could be differentiable. Rejected because `std::autodiff` is experimental and needs nightly Rust.

**Tapes only in library mode.** This needs no `tape` task kind. Rejected by the owner, because calibration on large areas needs workers.
