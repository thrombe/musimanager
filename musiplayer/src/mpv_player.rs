
use pyo3::{pyclass, pymethods};

use anyhow::Result;
// use pyo3::PyResult as Result;

// https://docs.rs/mpv/0.2.3/mpv/enum.Event.html
// https://mpv.io/manual/master/#properties
use mpv;

#[pyclass]
pub struct Player {
    // mpv never seems to not return stuff when it should. unlike gst_player
    pub mpv: mpv::MpvHandler,
    finished: bool,
    started: bool,
    url: Option<String>,
    dur: Option<f64>,
    pos: f64,
}

unsafe impl Send for Player {}
unsafe impl Sync for Player {}

#[pymethods]
impl Player {

    #[new]
    pub fn new() -> Player {
        let mut mpv = mpv::MpvHandlerBuilder::new()
            .expect("Couldn't initialize MpvHandlerBuilder")
            .build()
            .expect("Couldn't build MpvHandler");
        // mpv.set_option("ytdl", "yes").expect(
        //     "Couldn't enable ytdl in libmpv",
        // );
        mpv.set_option("vo", "null").expect(
            "Couldn't set vo=null in libmpv",
        );
        let mut p = Player {mpv, url: None, finished: false, pos: 0.0, dur: None, started: false};
        p.clear_event_loop();
        p
    }

    // from the comments, it seemed that clearing the events is important. so i added this in every method.
    pub fn clear_event_loop(&mut self) {
        // even if you don't do anything with the events, it is still necessary to empty
        // the event loop
        while let Some(event) = self.mpv.wait_event(0.0) {
            match event {
                // Shutdown will be triggered when the window is explicitely closed,
                // while Idle will be triggered when the queue will end
                // mpv::Event::Shutdown | mpv::Event::Idle => {
                //     break 'main;
                // }
                // mpv::Event::PlaybackRestart => {
                //     if !lol {
                //         lol = !lol;
                //         pl.seek();
                //     }
                // }
                _ => (),
            }
        }
    }

    // pub fn seek_percentage(&mut self, t: f32) -> Result<()> {
    //     self.clear_event_loop();
    //     self.mpv.command(&["seek", &t.to_string(), "absolute-percent"])?;
    //     Ok(())
    // }

    pub fn pause(&mut self) -> Result<()> {
        self.clear_event_loop();
        Ok(self.mpv.set_property("pause", true)?)
    }
    
    pub fn unpause(&mut self) -> Result<()> {
        self.clear_event_loop();
        Ok(self.mpv.set_property("pause", false)?)
    }

    pub fn is_paused(&mut self) -> Result<bool> {
        self.clear_event_loop();
        Ok(self.mpv.get_property::<bool>("pause")?)
    }
    
    pub fn toggle_pause(&mut self) -> Result<()> {
        self.clear_event_loop();
        if self.is_paused()? {
            self.unpause()?;
        } else {
            self.pause()?;
        }
        Ok(())
    }

    fn duration_option(&self) -> Option<f64> {
        self.mpv.get_property::<f64>("duration").ok()
    }

    fn position_option(&mut self) -> Option<f64> {
        self.mpv.get_property::<f64>("time-remaining").ok()
    }

    fn percent_pos(&self) -> f64 {
        self.mpv.get_property::<f64>("percent-pos").unwrap_or(0.0)*0.01
    }

    fn reset_vars(&mut self) {
        self.started = false;
        self.finished = false;
        self.dur = None;
        self.pos = 0.0;
    }

    pub fn stop(&mut self) -> Result<()> {
        self.clear_event_loop();
        
        self.reset_vars();
        self.mpv.command(&["stop"])?;
        Ok(())
    }

    pub fn play(&mut self, url: String) -> Result<()> {
        self.reset_vars();
        self.mpv.command(&["loadfile", &url, "replace"])?;
        self.url = Some(url);
        
        // assuming that it never not returns stuff till its done playing
        // blocking till the player is ready
        'loup: loop {
            while let Some(event) = self.mpv.wait_event(0.0) {
                match event {
                    mpv::Event::Shutdown | mpv::Event::Idle => {
                        panic!("could not play song");
                    }
                    mpv::Event::PlaybackRestart => {
                        break 'loup;
                    }
                    _ => (),
                }
            }
        }
        self.started = true;
        self.dur = Some(self.duration_option().unwrap());

        self.clear_event_loop();
        Ok(())
    }

    pub fn seek(&mut self, mut t: f64) -> Result<()> {
        if !self.started {return Ok(())}
        if self.is_finished() {
            if t > 0.0 {
                return Ok(());
            }
            self.play(self.url.as_ref().unwrap().clone())?;
            t += self.duration();
        }
        self.mpv.command(&["seek", &t.to_string()])?;
        Ok(())
    }

    pub fn position(&mut self) -> f64 {
        if !self.started {
            return self.pos;
        }

        if self.is_finished() {
            return self.duration();
        }
        let rem = self.position_option().unwrap();
        let dur = self.duration();

        self.pos = dur - rem;
        self.pos
    }

    pub fn duration(&mut self) -> f64 {
        self.clear_event_loop();

        if !self.started {
            return f64::MAX;
        }
        *self.dur.as_ref().unwrap()
    }

    pub fn progress(&mut self) -> f64 {
        if self.is_finished() {
            1.0
        } else {
            self.percent_pos()
        }
    }

    pub fn is_finished(&mut self) -> bool {
        self.clear_event_loop();
        
        if !self.started {return false;}
        if self.dur.is_some() && self.duration_option().is_none() {
            self.finished = true;
            true
        } else {
            false
        }
    }
}