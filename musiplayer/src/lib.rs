
// https://pyo3.rs/latest/
// https://docs.rs/pyo3/latest/pyo3/

// use anyhow::Context;

use pyo3::prelude::{Python, PyModule, PyResult};
use pyo3::{pymodule, pyclass, pymethods};

use gstreamer_player::prelude::Cast;
use gstreamer_player as gst_player;

#[pymodule]
fn musiplayer(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Player>()?;
    Ok(())
}

#[pyclass]
struct Player {
    gst_player: gst_player::Player,
    paused: bool,
    position: u64,
    duration: u64,
}

impl Player {
    fn new_player() -> gstreamer_player::Player {
        let dispatcher = gst_player::PlayerGMainContextSignalDispatcher::new(None);
        let player = gst_player::Player::new(
            None,
            Some(&dispatcher.upcast::<gst_player::PlayerSignalDispatcher>()),
        );
        player.set_video_track_enabled(false);

        player
    }
}

#[pymethods]
impl Player {

    #[new]
    fn new() -> Self {
        Self {gst_player: Self::new_player(), paused: true, duration: 0, position: 0}
    }

    fn position(&mut self) -> PyResult<u64>{
        // return Ok(self.gst_player.position().context("position none")?.seconds());

        // gst_plsyer.position can return none even if its not supposed to be. so it needs to be catched
        let pos = self.gst_player.position();
        if pos.is_some() {
            self.position = pos.unwrap().seconds();
        }
        Ok(self.position)
    }

    fn duration(&mut self) -> PyResult<u64>{
        // return Ok(self.gst_player.duration().context("duration none")?.seconds());

        // duration 
        if self.duration == 0 {
            let duration = self.gst_player.duration();
            if duration.is_some() {
                self.duration = duration.unwrap().seconds();
            }
        }
        Ok(self.duration)
    }

    fn seek(&mut self, t: i64) -> PyResult<()> {
        let pos = {
            let pos = self.gst_player.position();
            if pos.is_some() {
                pos.unwrap()
            } else {
                gstreamer::ClockTime::from_seconds(self.position)
            }
        };
        let seekpos = {if t.is_positive() {
            pos.checked_add(gstreamer::ClockTime::from_seconds(t as u64))
        } else {
            pos.checked_sub(gstreamer::ClockTime::from_seconds(t.abs() as u64))
        }};
        let mut seekpos = {if let Some(t) = seekpos {
            t
        } else {
            gstreamer::ClockTime::from_seconds(0)
        }};
        if seekpos.seconds() > self.duration && self.duration != 0 {
            self.position = self.duration;
            seekpos = gstreamer::ClockTime::from_seconds(self.duration);
        }
        self.gst_player.seek(seekpos);
        Ok(())
    }

    fn play(&mut self, url: String) -> PyResult<()> {
        self.gst_player.stop();
        self.gst_player = Self::new_player();
        self.gst_player.set_uri(&url);
        self.gst_player.play();
        self.paused = false;
        self.duration = 0;
        self.duration()?;
        Ok(())
    }

    fn is_finished(&mut self) -> PyResult<bool> {
        if self.paused || self.duration == 0 {return Ok(false)}
        Ok(self.position()? == self.duration()?)
    }

    fn is_paused(&self) -> bool {
        self.paused
    }

    fn pause(&mut self) {
        self.gst_player.pause();
        self.paused = true;
    }

    fn unpause(&mut self) -> PyResult<()> {
        if self.is_finished()? {return Ok(())}
        self.gst_player.play();
        self.paused = false;
        Ok(())
    }

    fn toggle_pause(&mut self) -> PyResult<bool> {
        if self.paused {
            self.unpause()?;
        } else {
            self.pause();
        }
        Ok(self.paused)
    }

    fn progress(&mut self) -> PyResult<f64> {
        if self.duration()? == 0 {return Ok(1.0)}
        Ok((self.position()? as f64)/(self.duration()? as f64))
    }
}