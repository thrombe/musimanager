
// https://pyo3.rs/latest/
// https://docs.rs/pyo3/latest/pyo3/

// use anyhow::{Result};

use pyo3::prelude::{Python, PyModule, PyResult};
use pyo3::{pymodule};
use pyo3::{pyclass, pymethods};

use anyhow::Result;


#[cfg(any(all(feature = "player-gst", feature = "force"), all(any(target_os = "windows", target_os = "linux"), target_arch = "x86_64", not(feature = "force"))))]
mod gst_player;
#[cfg(any(all(feature = "player-gst", feature = "force"), all(any(target_os = "windows", target_os = "linux"), target_arch = "x86_64", not(feature = "force"))))]
use gst_player::{Player as InternalPlayer};

#[cfg(any(all(feature = "player-mpv", feature = "force"), all(target_os = "android", target_arch = "aarch64", not(feature = "force"))))]
mod mpv_player;
#[cfg(any(all(feature = "player-mpv", feature = "force"), all(target_os = "android", target_arch = "aarch64", not(feature = "force"))))]
use mpv_player::{Player as InternalPlayer};

#[cfg(feature = "player-libmpv")]
mod libmpv_player;
#[cfg(feature = "player-libmpv")]
use libmpv_player::{Player as InternalPlayer};


#[pymodule]
fn musiplayer(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Player>()?;
    Ok(())
}

#[pyclass]
#[derive(Debug)]
pub struct Player {
    internal_player: InternalPlayer,
}


#[pymethods]
impl Player {
    #[new]
    pub fn new() -> Result<Self> {
        Ok(Self {internal_player: MusiPlayer::new()?})
    }
    pub fn duration(&mut self) -> Result<f64> {
        MusiPlayer::duration(&mut self.internal_player)
    }
    pub fn is_finished(&mut self) -> Result<bool> {
        MusiPlayer::is_finished(&mut self.internal_player)
    }
    pub fn is_paused(&mut self) -> Result<bool> {
        MusiPlayer::is_paused(&mut self.internal_player)
    }
    pub fn play(&mut self, url: String) -> Result<()> {
        MusiPlayer::play(&mut self.internal_player, url)
    }
    pub fn position(&mut self) -> Result<f64> {
        MusiPlayer::position(&mut self.internal_player)
    }
    pub fn progress(&mut self) -> Result<f64> {
        MusiPlayer::progress(&mut self.internal_player)
    }
    pub fn seek(&mut self, t: f64) -> Result<()> {
        MusiPlayer::seek(&mut self.internal_player, t)
    }
    pub fn stop(&mut self) -> Result<()> {
        MusiPlayer::stop(&mut self.internal_player)
    }
    pub fn toggle_pause(&mut self) -> Result<()> {
        MusiPlayer::toggle_pause(&mut self.internal_player)
    }
}

pub trait MusiPlayer
where Self:  Sized + 'static + Send + Sync
{
    fn new() -> Result<Self>;
    fn play(&mut self, url: String) -> Result<()>;
    fn stop(&mut self) -> Result<()>;
    fn toggle_pause(&mut self) -> Result<()>;
    fn seek(&mut self, t: f64) -> Result<()>;
    fn is_finished(&mut self) -> Result<bool>;
    fn is_paused(&mut self) -> Result<bool>;
    fn progress(&mut self) -> Result<f64>;
    fn position(&mut self) -> Result<f64>;
    fn duration(&mut self) -> Result<f64>;
}

