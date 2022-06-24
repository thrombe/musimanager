
// https://gstreamer.pages.freedesktop.org/gstreamer-rs/stable/latest/docs/gstreamer_player/struct.Player.html


use gstreamer_player::{self, prelude::Cast};
use gstreamer;


use crate::MusiPlayer;
use anyhow::Result;

#[derive(Debug)]
pub struct Player {
    player: gstreamer_player::Player,
    paused: bool,
    position: u64,
    duration: u64,
    
    // currently this is only used to so that progress() reports 0 when no song is being played (when it is called just after initialising Player)
    started: bool,
}

impl Player {
    fn new_player() -> gstreamer_player::Player {
        let dispatcher = gstreamer_player::PlayerGMainContextSignalDispatcher::new(None);
        let player = gstreamer_player::Player::new(
            None,
            Some(&dispatcher.upcast::<gstreamer_player::PlayerSignalDispatcher>()),
        );
        player.set_video_track_enabled(false);

        player
    }
}

impl Player {

    pub fn new() -> Self {
        Self {player: Self::new_player(), paused: true, duration: 0, position: 0, started: false}
    }

    pub fn position(&mut self) -> u64 {
        // gst_plsyer.position can return none even if its not supposed to be. so it needs to be catched
        let pos = self.player.position();
        let cached_position = self.position;
        if pos.is_some() {
            self.position = pos.unwrap().mseconds();
        }

        // max needed to make seeking more reliable (self.seek() sets the value of self.position, and
        // self.position() might still return the old value as the audio may not be loaded yet)
        u64::max(self.position, cached_position)
    }

    pub fn duration(&mut self) -> u64 {
        let duration = self.player.duration();
        if duration.is_some() {
            self.duration = duration.unwrap().mseconds();
        }
        self.duration
    }

    // t in seconds
    pub fn seek(&mut self, t: f64) {
        let t = (t*1000.0) as i64;

        let pos = gstreamer::ClockTime::from_mseconds({
            let cached_pos = self.position;
            let pos = self.position();

            // this is needed to make seeking more reliable, allows seek to work even when spamming this method
            if t.is_negative() {
                u64::min(cached_pos, pos)
            } else {
                u64::max(cached_pos, pos)
            }
        });
        let mut seekpos = {if t.is_positive() {
            pos + gstreamer::ClockTime::from_mseconds(t as u64)
        } else {
            pos.checked_sub(
                gstreamer::ClockTime::from_mseconds(t.abs() as u64))
                .unwrap_or(gstreamer::ClockTime::from_seconds(0)
            ) // if -ve, set to 0
        }};

        if seekpos.mseconds() > self.duration && self.duration != 0 {
            seekpos = gstreamer::ClockTime::from_mseconds(self.duration - 60);
        }

        // overwriting position with new value, so that correct value is returned by self.position() even if audio hasnt completed loading
        self.position = seekpos.mseconds();
        self.player.seek(seekpos);
    }

    pub fn play(&mut self, url: String) {
        self.player.set_uri(&url);
        self.player.play();
        self.paused = false;
        self.duration = 0;
        self.position = 0;
        self.duration();
    }

    pub fn stop(&mut self) {
        self.duration = 0;
        self.position = 0;
        self.player.stop();
        self.paused = true;
    }

    pub fn is_finished(&mut self) -> bool {
        // gstreamer_player.position() never reaches the values of .duration() (reaches around minimun .duration()-15 (mseconds))
        // it does not have a .is_finished() method (or atleast i could'nt find it)

        let duration = self.duration();
        if self.paused || duration == 0 {return false}

        // i64 was needed as in release mode there are no overflow checks and u64-lil_bigger_u64 cant be smaller than 50
        (duration as i64) - (self.position() as i64) < 50
    }

    pub fn is_paused(&self) -> bool {
        self.paused
    }

    pub fn pause(&mut self) {
        self.player.pause();
        self.paused = true;
    }

    pub fn unpause(&mut self) {
        if self.is_finished() {return}
        self.player.play();
        self.paused = false;
    }

    pub fn toggle_pause(&mut self) {
        if self.paused {
            self.unpause();
        } else {
            self.pause();
        }
    }

    pub fn progress(&mut self) -> f64 {
        if self.duration() == 0 {
            if !self.started {
                return 0.0;
            } else {
                return 1.0;
            }
        } else {
            self.started = true;
        }
        (self.position() as f64)/(self.duration() as f64)
    }
}


impl MusiPlayer for Player {
    fn new() -> Result<Self> {
        Ok(Self::new())
    }
    fn duration(&mut self) -> Result<f64> {
        Ok(Self::duration(self) as f64/1000.0)
    }
    fn is_finished(&mut self) -> Result<bool> {
        Ok(Self::is_finished(self))
    }
    fn play(&mut self, url: String) -> Result<()> {
        Ok(Self::play(self, url))
    }
    fn position(&mut self) -> Result<f64> {
        Ok(Self::position(self) as f64/1000.0)
    }
    fn progress(&mut self) -> Result<f64> {
        Ok(Self::progress(self))
    }
    fn seek(&mut self, t: f64) -> Result<()> {
        Ok(Self::seek(self, t))
    }
    fn stop(&mut self) -> Result<()> {
        Ok(Self::stop(self))
    }
    fn toggle_pause(&mut self) -> Result<()> {
        Ok(Self::toggle_pause(self))
    }
    fn is_paused(&mut self) -> Result<bool> {
        Ok(Self::is_paused(&self))
    }
}