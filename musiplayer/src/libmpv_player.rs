
use pyo3::{pyclass, pymethods};

use anyhow::{Result, Context};

use libmpv;

#[pyclass]
pub struct Player {
    mpv: libmpv::Mpv,
}

//https://docs.rs/libmpv/2.0.1/libmpv/struct.Mpv.html

#[pymethods]
impl Player {  // new, position, duration, seek, play, stop, is_finished, is_paused, pause, unpause, toggle_pause, progress

    #[new]
    pub fn new() -> Result<Self> {
        Ok(Player { mpv: libmpv::Mpv::new().ok().context("player could not be created")? })
    }

}