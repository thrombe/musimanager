
use pyo3::{pyclass, pymethods};

use anyhow::Result;
// use pyo3::PyResult as Result;

// https://docs.rs/mpv/0.2.3/mpv/enum.Event.html
use mpv;

#[pyclass]
pub struct Player {
    // mpv never seems to not return stuff when it should. unlike gst_player
    pub mpv: mpv::MpvHandler,
    finished: bool,
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
        let mut p = Player {mpv, url: None, finished: false, pos: 0.0, dur: None};
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

    // pub fn loop_current_song(&mut self) {
    //     let next_loop = match self.mpv.get_property::<&str>("loop-file") {
    //         Ok(x) => {
    //             if x == "inf" || x == "yes" {
    //                 println!("Toggling loop off");
    //                 "no"
    //             } else if x == "no" || x == "1" {
    //                 println!("Toggling loop on");
    //                 "inf"
    //             } else {
    //                 panic!("Unexpected value for loop-file property")
    //             }
    //         }
    //         Err(e) => panic!("{}", e),
    //     };
    //     self.mpv.set_property("loop-file", next_loop).expect(
    //         "Toggling loop-file property",
    //     );
    // }

    // pub fn queue(&mut self, new: String) {
    //     self.mpv
    //         .command(&["loadfile", &new, "append-play"])
    //         .expect("Error loading file");
    // }

    // pub fn seek_percentage(&mut self, t: f32) -> Result<()> {
    //     self.clear_event_loop();
    //     self.mpv.command(&["seek", &t.to_string(), "absolute-percent"])?;
    //     Ok(())
    // }

    pub fn stop(&mut self) -> Result<()> {
        self.clear_event_loop();
        self.mpv.command(&["stop"])?;
        Ok(())
    }

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

    fn block_till_song_ready(&self) {
        if self.finished || self.dur.is_some() || self.url.is_none() {return}
        while self.duration_option().is_none() {}
    }

    pub fn play(&mut self, url: String) -> Result<()> {
        self.clear_event_loop();

        self.finished = false;
        self.dur = None;
        self.pos = 0.0;
        self.mpv.command(&["loadfile", &url, "replace"])?;
        self.url = Some(url);
        Ok(())
    }

    pub fn seek(&mut self, t: f64) -> Result<()> {
        self.clear_event_loop();

        if self.url.is_some() { // url is sent to mpv
            if self.duration_option().is_none() {
                if self.dur.is_none() { // song is not ready yet, its probably too soon
                    self.block_till_song_ready();
                } else { // its too late, song ended
                    self.play(self.url.as_ref().unwrap().clone())?;
                    self.block_till_song_ready();
                    self.seek(self.pos+t)?;
                }
            }
            self.mpv.command(&["seek", &t.to_string()])?;
        }
        Ok(())
    }

    pub fn position(&mut self) -> f64 {
        self.clear_event_loop();

        if self.finished {
            return self.duration();
        }
        let rem = match self.position_option() {
            None => {
                self.maybe_mark_finished();
                return 0.0
            },
            Some(p) => p,
        };
        let dur = self.duration(); // rem returned Some, so duration should return Some too
        dur - rem
    }

    fn maybe_mark_finished(&mut self) {
        if self.dur.is_some() && self.duration_option().is_none() {
            self.finished = true;
        }
    }

    pub fn duration(&mut self) -> f64 {
        self.clear_event_loop();

        let dur = self.duration_option();
        if dur.is_some() {
            self.dur = dur;
        } else {
            self.maybe_mark_finished();
        }
        *self.dur.as_ref().unwrap_or(&0.0)
    }

    pub fn progress(&mut self) -> f64 {
        self.clear_event_loop();

        // let progress = self.pos/self.dur.unwrap_or(f64::MAX);
        let new_prog = self.position()/self.duration();
        new_prog
    }

    pub fn is_finished(&mut self) -> bool {
        self.clear_event_loop();
        
        self.maybe_mark_finished();
        self.finished
    }
}