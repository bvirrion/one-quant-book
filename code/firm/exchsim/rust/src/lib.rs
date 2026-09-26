//! firm.exchsim (One Quant Book 10, chapter 26), Rust: the codec of every protocol and the matching engine,
//! byte-identical to the Python reference (`firm_exchsim_engine.py`) and the C++20 engine on the shared fixture.
//! PROTOCOL.md states the byte layouts and the rules.

pub mod codec;
pub mod engine;
pub mod json;

pub use codec::{Ctl, Feed, In, Out};
pub use engine::Engine;
