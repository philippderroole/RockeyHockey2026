use std::thread;
use std::time::Duration;

use log::info;
use opencv::Error;
use opencv::core::StsError;
use opencv::videoio::VideoCapture;

use rockey_hockey::puck_detector::{
    DetectionPipeline, PuckDetector, RuntimeDetectorSettings, TimedFrameProcessing,
    TimedPuckDetector,
};
use rockey_hockey::web_ui::{
    PlaybackControlSnapshot, SharedPlaybackControl, SharedPreviewFrames, SharedRuntimeSettings,
    spawn_web_ui_server,
};

#[derive(Clone)]
struct WebUiShared {
    settings: SharedRuntimeSettings,
    previews: SharedPreviewFrames,
    playback: SharedPlaybackControl,
}

impl WebUiShared {
    fn from_runtime_settings(
        port: u16,
        runtime_settings: RuntimeDetectorSettings,
    ) -> opencv::Result<Self> {
        let settings = SharedRuntimeSettings::new(runtime_settings);
        let previews = SharedPreviewFrames::new();
        let playback = SharedPlaybackControl::new();

        if let Err(err) =
            spawn_web_ui_server(settings.clone(), previews.clone(), playback.clone(), port)
        {
            return Err(Error::new(
                StsError,
                format!("Failed to start web UI: {err}"),
            ));
        }

        info!("Live settings editor enabled at http://127.0.0.1:{}", port);
        Ok(Self {
            settings,
            previews,
            playback,
        })
    }

    fn apply_settings_to(&self, detector: &mut TimedPuckDetector<PuckDetector>) {
        detector.update_runtime_settings(self.settings.get());
    }

    fn publish_processed(&self, processed: &TimedFrameProcessing) -> anyhow::Result<()> {
        self.previews.update_from_processed(processed)
    }

    fn playback_snapshot(&self) -> PlaybackControlSnapshot {
        self.playback.snapshot()
    }
}

pub trait DetectorRunner {
    fn run_step(&mut self, cam: &mut VideoCapture) -> anyhow::Result<bool>;
}

pub struct PlainDetectorRunner {
    detector: PuckDetector,
}

impl PlainDetectorRunner {
    pub fn new(runtime_settings: RuntimeDetectorSettings) -> Self {
        Self {
            detector: PuckDetector::with_runtime_settings(runtime_settings),
        }
    }
}

impl DetectorRunner for PlainDetectorRunner {
    fn run_step(&mut self, cam: &mut VideoCapture) -> anyhow::Result<bool> {
        Ok(self.detector.capture_and_detect(cam)?.is_some())
    }
}

pub struct WebUiDetectorRunner {
    detector: TimedPuckDetector<PuckDetector>,
    web_ui: WebUiShared,
    last_reprocess_generation: u64,
    last_step_generation: u64,
}

impl WebUiDetectorRunner {
    pub(super) fn with_web_ui(
        port: u16,
        runtime_settings: RuntimeDetectorSettings,
    ) -> anyhow::Result<Self> {
        Ok(Self {
            detector: TimedPuckDetector::with_runtime_settings(runtime_settings),
            web_ui: WebUiShared::from_runtime_settings(port, runtime_settings)?,
            last_reprocess_generation: 0,
            last_step_generation: 0,
        })
    }
}

impl DetectorRunner for WebUiDetectorRunner {
    fn run_step(&mut self, cam: &mut VideoCapture) -> anyhow::Result<bool> {
        self.web_ui.apply_settings_to(&mut self.detector);

        let playback = self.web_ui.playback_snapshot();
        if playback.paused {
            if playback.step_generation != self.last_step_generation {
                self.last_step_generation = playback.step_generation;
                let processed = self.detector.capture_and_detect(cam)?;

                if let Some(processed) = processed.as_ref() {
                    self.web_ui.publish_processed(processed)?;
                }

                return Ok(true);
            }

            if playback.reprocess_generation == self.last_reprocess_generation {
                thread::sleep(Duration::from_millis(20));
                return Ok(true);
            }

            self.last_reprocess_generation = playback.reprocess_generation;
            let processed = self.detector.detect_current_frame()?;

            if let Some(processed) = processed.as_ref() {
                self.web_ui.publish_processed(processed)?;
            }

            return Ok(true);
        }

        self.last_step_generation = playback.step_generation;

        let processed = self.detector.capture_and_detect(cam)?;

        if let Some(processed) = processed.as_ref() {
            self.web_ui.publish_processed(processed)?;
        }

        Ok(processed.is_some())
    }
}
