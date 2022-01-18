
// https://pyo3.rs/latest/
// https://docs.rs/pyo3/latest/pyo3/

// use anyhow::Context;

use pyo3::prelude::{Python, PyModule, PyResult};
use pyo3::{pymodule, pyclass, pymethods};

use gstreamer_player::prelude::Cast;
use gstreamer_player as gst_player;
use gstreamer;

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

fn map_time(t: gstreamer::ClockTime) -> u64 {
    (t.mseconds() as f64/1000.0).round() as u64
}

#[pymethods]
impl Player {

    #[new]
    fn new() -> Self {
        Self {gst_player: Self::new_player(), paused: true, duration: 0, position: 0}
    }

    fn position(&mut self) -> PyResult<u64>{
        // return Ok(map_time(self.gst_player.position().context("position none")?));

        // gst_plsyer.position can return none even if its not supposed to be. so it needs to be catched
        // gst_player often does not reach the value of sgt_player.duration, so it needs rounding off (hence the map_time function)
        let pos = self.gst_player.position();
        if pos.is_some() {
            self.position = map_time(pos.unwrap());
        }
        Ok(self.position)
    }

    fn duration(&mut self) -> PyResult<u64>{
        // return Ok(map_time(self.gst_player.duration().context("duration none")?));

        let duration = self.gst_player.duration();
        if duration.is_some() {
            self.duration = map_time(duration.unwrap());
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
        if map_time(seekpos) > self.duration && self.duration != 0 {
            self.position = self.duration;
            seekpos = gstreamer::ClockTime::from_seconds(self.duration);
        }
        self.gst_player.seek(seekpos);
        Ok(())
    }

    fn play(&mut self, url: String) -> PyResult<()> {
        self.gst_player.set_uri(&url);
        self.gst_player.play();
        self.paused = false;
        self.duration = 0;
        self.position = 0;
        self.duration()?;
        Ok(())
    }

    fn stop(&mut self) {
        self.duration = 0;
        self.position = 0;
        self.gst_player.stop();
        self.paused = true;
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
