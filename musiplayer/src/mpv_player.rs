

use derivative::Derivative;
use anyhow::Result;
// use pyo3::PyResult as Result;

// https://docs.rs/mpv/0.2.3/mpv/enum.Event.html
// https://mpv.io/manual/master/#properties
use mpv;

use crate::MusiPlayer;

#[derive(Derivative)]
#[derivative(Debug)]
pub struct Player {
    // mpv never seems to not return stuff when it should. unlike gst_player
    #[derivative(Debug="ignore")]
    mpv: mpv::MpvHandler,
    finished: bool,
    started: bool,
    url: Option<String>,
    dur: Option<f64>,
    pos: f64,
    waiting_for_response: bool,
}

unsafe impl Send for Player {}
unsafe impl Sync for Player {}

impl Player {

    pub fn new() -> Result<Player> {
        let mut mpv = mpv::MpvHandlerBuilder::new()?
            .build()?;
        // mpv.set_option("ytdl", "yes").expect(
        //     "Couldn't enable ytdl in libmpv",
        // );
        mpv.set_option("vo", "null")?;
        let mut p = Player {
            mpv,
            url: None,
            finished: false,
            pos: 0.0,
            dur: None,
            started: false,
            waiting_for_response: false,
        };
        p.clear_event_loop()?;
        Ok(p)
    }

    // from the comments, it seemed that clearing the events is important. so i added this in every method.
    fn clear_event_loop(&mut self) -> Result<()> {

        if self.waiting_for_response {
            // assuming that it never not returns stuff till its done playing
            // blocking till the player is ready
            while let Some(event) = self.mpv.wait_event(0.0) {
                match event {
                    mpv::Event::Shutdown | mpv::Event::Idle => {
                        anyhow::bail!("could not play song");
                    }
                    mpv::Event::PlaybackRestart => {
                        self.waiting_for_response = false;
                        self.started = true;
                        self.dur = Some(self.duration_option()?);
                
                        if self.is_paused().unwrap_or(false) {
                            self.unpause()?;
                        }
                    }
                    _ => (),
                }
            }
        } else {
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
        Ok(())
    }

    // pub fn seek_percentage(&mut self, t: f32) -> Result<()> {
    //     self.clear_event_loop()?;
    //     self.mpv.command(&["seek", &t.to_string(), "absolute-percent"])?;
    //     Ok(())
    // }

    pub fn pause(&mut self) -> Result<()> {
        self.clear_event_loop()?;
        Ok(self.mpv.set_property("pause", true)?)
    }
    
    pub fn unpause(&mut self) -> Result<()> {
        self.clear_event_loop()?;
        Ok(self.mpv.set_property("pause", false)?)
    }

    pub fn is_paused(&mut self) -> Result<bool> {
        self.clear_event_loop()?;
        Ok(self.mpv.get_property::<bool>("pause")?)
    }
    
    pub fn toggle_pause(&mut self) -> Result<()> {
        self.clear_event_loop()?;
        if self.is_paused()? {
            self.unpause()?;
        } else {
            self.pause()?;
        }
        Ok(())
    }

    fn duration_option(&self) -> Result<f64> {
        Ok(self.mpv.get_property::<f64>("duration")?)
    }

    fn position_option(&mut self) -> Result<f64> {
        Ok(self.mpv.get_property::<f64>("time-remaining")?)
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
        self.clear_event_loop()?;
        
        self.reset_vars();
        self.mpv.command(&["stop"])?;
        Ok(())
    }

    pub fn play(&mut self, url: String) -> Result<()> {
        self.reset_vars();
        self.mpv.command(&["loadfile", &url, "replace"])?;
        self.url = Some(url);
        self.waiting_for_response = true;
        self.clear_event_loop()?;
        Ok(())
    }

    pub fn seek(&mut self, mut t: f64) -> Result<()> {
        if !self.started {return Ok(())}
        if self.is_finished()? {
            if t > 0.0 {
                return Ok(());
            }
            self.play(self.url.as_ref().unwrap().clone())?;
            t += self.duration()?;
        }
        self.mpv.command(&["seek", &t.to_string()])?;
        Ok(())
    }

    pub fn position(&mut self) -> Result<f64> {
        if !self.started {
            return Ok(self.pos);
        }

        if self.is_finished()? {
            return self.duration();
        }
        let rem = self.position_option()?;
        let dur = self.duration()?;

        self.pos = dur - rem;
        Ok(self.pos)
    }

    pub fn duration(&mut self) -> Result<f64> {
        self.clear_event_loop()?;

        if !self.started {
            return Ok(f64::MAX);
        }
        Ok(*self.dur.as_ref().unwrap())
    }

    pub fn progress(&mut self) -> Result<f64> {
        let pos = if self.is_finished()? {
            1.0
        } else {
            self.percent_pos()
        };
        Ok(pos)
    }

    pub fn is_finished(&mut self) -> Result<bool> {
        self.clear_event_loop()?;
        
        if !self.started {return Ok(false);}
        if self.dur.is_some() && self.duration_option().is_err() {
            self.finished = true;
            Ok(true)
        } else {
            Ok(false)
        }
    }
}

impl MusiPlayer for Player {
    fn duration(&mut self) -> Result<f64> {
        Self::duration(self)
    }
    fn new() -> Result<Self> {
        Self::new()
    }
    fn play(&mut self, url: String) -> Result<()> {
        Self::play(self, url)
    }
    fn is_finished(&mut self) -> Result<bool> {
        Self::is_finished(self)
    }
    fn is_paused(&mut self) -> Result<bool> {
        Self::is_paused(self)
    }
    fn position(&mut self) -> Result<f64> {
        Self::position(self)
    }
    fn progress(&mut self) -> Result<f64> {
        Self::progress(self)
    }
    fn seek(&mut self, t: f64) -> Result<()> {
        Self::seek(self, t)
    }
    fn stop(&mut self) -> Result<()> {
        Self::stop(self)
    }
    fn toggle_pause(&mut self) -> Result<()> {
        Self::toggle_pause(self)
    }
}
