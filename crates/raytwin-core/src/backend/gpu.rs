//! GPU backends on `wgpu`. The only module that imports `wgpu`
//! (ARCHITECTURE §6.2 rule 2, P-01).

pub mod compute;
pub mod ray_query;
