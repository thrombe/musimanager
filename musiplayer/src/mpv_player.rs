
use pyo3::{pyclass, pymethods};

use anyhow::Result;
// use pyo3::PyResult as Result;

use mpv;

#[pyclass]
pub struct Player {
    pub mpv: mpv::MpvHandler,
}
// https://docs.rs/mpv/0.2.3/mpv/enum.Event.html

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
        let mut p = Player {mpv};
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

    pub fn play(&mut self, new: &str) -> Result<()> {
        self.clear_event_loop();
        self.mpv.command(&["loadfile", &new, "replace"])?;
        Ok(())
    }

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

    pub fn seek(&mut self, t: f64) -> Result<()> {
        self.clear_event_loop();
        Ok(self.mpv.command(&["seek", &t.to_string()])?)
    }

    pub fn seek_percentage(&mut self, t: f32) -> Result<()> {
        self.clear_event_loop();
        self.mpv.command(&["seek", &t.to_string(), "absolute-percent"])?;
        Ok(())
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

    pub fn position(&mut self) -> f64 {
        self.clear_event_loop();
        let dur = self.duration();
        if dur > 99999999998.0 {return 0.0}
        dur - self.mpv.get_property::<f64>("time-remaining").unwrap_or(0.0)
    }

    pub fn duration(&mut self) -> f64 {
        self.clear_event_loop();
        self.mpv.get_property::<f64>("duration").unwrap_or(99999999999.0)
    }

    pub fn progress(&mut self) -> f64 {
        self.clear_event_loop();
        self.position()/self.duration()
    }

    pub fn is_finished(&mut self) -> bool {
        self.clear_event_loop();
        0.5 > self.duration() - self.position() // last 0.5 secs ignored
    }
}