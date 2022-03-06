
// https://pyo3.rs/latest/
// https://docs.rs/pyo3/latest/pyo3/

// https://gstreamer.pages.freedesktop.org/gstreamer-rs/stable/latest/docs/gstreamer_player/struct.Player.html

// use anyhow::Context;

use pyo3::prelude::{Python, PyModule, PyResult};
use pyo3::{pymodule};


#[cfg(any(all(feature = "player-gst", feature = "force"), all(target_os = "linux", target_arch = "x86_64")))]
mod gst_player;
#[cfg(any(all(feature = "player-gst", feature = "force"), all(target_os = "linux", target_arch = "x86_64")))]
use gst_player::{Player};

#[cfg(any(all(feature = "player-mpv", feature = "force"), all(target_os = "android", target_arch = "aarch64")))]
mod mpv_player;
#[cfg(any(all(feature = "player-mpv", feature = "force"), all(target_os = "android", target_arch = "aarch64")))]
use mpv_player::{Player};

#[cfg(feature = "player-libmpv")]
mod libmpv_player;
#[cfg(feature = "player-libmpv")]
use libmpv_player::{Player};


#[pymodule]
fn musiplayer(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Player>()?;
    Ok(())
}
