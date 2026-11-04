//! The internal `Backend` seam and its implementations. Not a public plugin API
//! (ADR 0004).

pub mod cpu;
#[cfg(feature = "gpu")]
pub mod gpu;
pub mod select;
