
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

#[pymethods]
impl Player {

    #[new]
    fn new() -> Self {
        Self {gst_player: Self::new_player(), paused: true, duration: 0, position: 0}
    }

    fn position(&mut self) -> PyResult<u64>{
        // gst_plsyer.position can return none even if its not supposed to be. so it needs to be catched
        let pos = self.gst_player.position();
        let cached_position = self.position;
        if pos.is_some() {
            self.position = pos.unwrap().mseconds();
        }

        // max needed to make seeking more reliable (self.seek() sets the value of self.position, and
        // self.position() might still return the old value as the audio may not be loaded yet)
        Ok(u64::max(self.position, cached_position))
    }

    fn duration(&mut self) -> PyResult<u64>{
        let duration = self.gst_player.duration();
        if duration.is_some() {
            self.duration = duration.unwrap().mseconds();
        }
        Ok(self.duration)
    }

    // t in seconds
    fn seek(&mut self, t: i64) -> PyResult<()> {

        let pos = gstreamer::ClockTime::from_mseconds({
            let cached_pos = self.position;
            let pos = self.position()?;

            // this is needed to make seeking more reliable, allows seek to work even when spamming this method
            if t.is_negative() {
                u64::min(cached_pos, pos)
            } else {
                u64::max(cached_pos, pos)
            }
        });
        let mut seekpos = {if t.is_positive() {
            pos + gstreamer::ClockTime::from_seconds(t as u64)
        } else {
            pos.checked_sub(gstreamer::ClockTime::from_seconds(t.abs() as u64)).unwrap_or(gstreamer::ClockTime::from_seconds(0)) // if -ve, set to 0
        }};

        if seekpos.mseconds() > self.duration && self.duration != 0 {
            seekpos = gstreamer::ClockTime::from_mseconds(self.duration - 60);
        }

        // overwriting position with new value, so that correct value is returned by self.position() even if audio hasnt completed loading
        self.position = seekpos.mseconds();
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
        // gstreamer_player.position() never reaches the values of .duration() (reaches around minimun .duration()-15 (mseconds))
        // it does not have a .is_finished() method (or atleast i could'nt find it)

        if self.paused || self.duration == 0 {return Ok(false)}

        // i64 was needed as in release mode there are no overflow checks and u64-lil_bigger_u64 cant be smaller than 50
        Ok((self.duration()? as i64) - (self.position()? as i64) < 50)
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
