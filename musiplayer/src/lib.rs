
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
pub struct Player {
    internal_player: InternalPlayer, // refcell for internal mutability?
}

#[pymethods]
impl Player {
    #[new]
    pub fn new() -> Self {
        Self {
            internal_player: InternalPlayer::new(),
        }
    }
    pub fn play(&mut self, url: String) -> Result<()> {
        self.internal_player.play(url)
    }
    pub fn stop(&mut self) -> Result<()> {
        self.internal_player.stop()
    }
    pub fn toggle_pause(&mut self) -> Result<()> {
        self.internal_player.toggle_pause()
    }
    pub fn seek(&mut self, t: f64) -> Result<()> {
        self.internal_player.seek(t)
    }
    pub fn is_finished(&mut self) -> bool {
        self.internal_player.is_finished()
    }
    pub fn progress(&mut self) -> f64 {
        self.internal_player.progress()
    }
    pub fn position(&mut self) -> f64 {
        self.internal_player.position()
    }
    pub fn duration(&mut self) -> f64 {
        self.internal_player.duration()
    }
    /// this function should be executed every frame in event loop, this does not mlock much
    /// it is needed cuz im lazy
    pub fn clear_event_loop(&mut self) {
        self.internal_player.clear_event_loop();
    }

}

pub trait MusiPlayer
where Self:  Sized + 'static + Send + Sync
{
    // why trait for this?
    //   . i dont need to change the internal_player in runtime, so i dont need trait objects
    //   . im not exposing this as a crate, so i dont need a trait as a mode of expansion by users
    //   . will be harder to add new stuff to the trait
    //   . 
    
    // good points:
    //   \. will be easier to add new internal_players
    //   \. all players will have same behaviour for return types and inputs
    //   . no need to have pyo3 up in all the internal_player code
    //   \. all players will have only the exposed_player api as features to the python code
    //   . 



    fn new() -> Self;
    fn play(&mut self, url: String) -> Result<()>;
    fn stop(&mut self) -> Result<()>;
    fn toggle_pause(&mut self) -> Result<()>;
    fn seek(&mut self, t: f64) -> Result<()>;
    fn is_finished(&mut self) -> bool;
    fn progress(&mut self) -> f64;
    fn position(&mut self) -> f64;
    fn duration(&mut self) -> f64;
}

