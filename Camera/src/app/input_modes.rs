use opencv::Error;
use opencv::core::StsError;
use opencv::videoio::{CAP_ANY, VideoCapture, VideoCaptureTraitConst};

use super::runner::DetectorRunner;

pub enum InputSource {
    VideoFile(String),
    Camera(i32),
    PiCamera,
}

impl InputSource {
    fn open_capture(&self) -> opencv::Result<VideoCapture> {
        match self {
            Self::VideoFile(path) => self.open_video_capture(path),
            Self::Camera(index) => self.open_camera_capture(*index),
            Self::PiCamera => Err(Error::new(
                StsError,
                "PiCamera input mode not implemented yet",
            )),
        }
    }

    fn open_video_capture(&self, path: &str) -> opencv::Result<VideoCapture> {
        let cam = VideoCapture::from_file(path, CAP_ANY)?;
        if !VideoCapture::is_opened(&cam)? {
            return Err(Error::new(StsError, "Could not open video file"));
        }
        Ok(cam)
    }

    fn open_camera_capture(&self, index: i32) -> opencv::Result<VideoCapture> {
        let cam = VideoCapture::new(index, CAP_ANY)?; // Open default camera
        if !VideoCapture::is_opened(&cam)? {
            return Err(Error::new(StsError, "Could not open camera"));
        }
        Ok(cam)
    }
}

pub fn run_capture_loop(
    runner: &mut dyn DetectorRunner,
    source: InputSource,
) -> opencv::Result<()> {
    let mut cam = source.open_capture()?;

    loop {
        let frame_available = runner.run_step(&mut cam)?;
        if !frame_available {
            break;
        }
    }

    Ok(())
}
