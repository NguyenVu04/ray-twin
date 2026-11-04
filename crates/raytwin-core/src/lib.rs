//! Physics, backends, task planning and merge. No I/O (ADR 0001).
//!
//! The modules form layers, from high to low: `task`, then `backend`, then
//! `trace`, `map`, `paths` and `tape`, then `em`, `geom`, `field` and `rng`.
//! A module imports only modules of its own layer or of a lower layer
//! (ARCHITECTURE §6.2 rule 6).

pub mod task;

pub mod backend;

pub mod map;
pub mod paths;
pub mod tape;
pub mod trace;

pub mod em;
pub mod field;
pub mod geom;
pub mod rng;
