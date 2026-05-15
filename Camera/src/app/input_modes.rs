use anyhow::anyhow;
use opencv::videoio::{CAP_ANY, CAP_GSTREAMER, VideoCapture, VideoCaptureTraitConst};

use super::runner::DetectorRunner;

pub enum InputSource {
    VideoFile(String),
    Camera(i32),
    PiCamera,
}

impl InputSource {
    fn open_capture(&self) -> anyhow::Result<VideoCapture> {
        match self {
            Self::VideoFile(path) => self.open_video_capture(path),
            Self::Camera(index) => self.open_camera_capture(*index),
            Self::PiCamera => self.open_pi_camera_capture(),
        }
    }

    fn open_video_capture(&self, path: &str) -> anyhow::Result<VideoCapture> {
        let cam = VideoCapture::from_file(path, CAP_ANY)?;
        if !VideoCapture::is_opened(&cam)? {
            return Err(anyhow!("Could not open video file"));
        }
        Ok(cam)
    }

    fn open_camera_capture(&self, index: i32) -> anyhow::Result<VideoCapture> {
        let cam = VideoCapture::new(index, CAP_ANY)?; // Open default camera
        if !VideoCapture::is_opened(&cam)? {
            return Err(anyhow!("Could not open camera"));
        }
        Ok(cam)
    }

    fn open_pi_camera_capture(&self) -> anyhow::Result<VideoCapture> {
        let pipeline = "libcamerasrc ! video/x-raw,format=NV12,width=640,height=480,framerate=60/1 ! videoconvert ! appsink drop=true max-buffers=1 sync=false";

        let cam = VideoCapture::from_file(pipeline, CAP_GSTREAMER)?;
        if !VideoCapture::is_opened(&cam)? {
            return Err(anyhow!("Could not open PiCamera with GStreamer pipeline"));
        }
        Ok(cam)
    }
}

pub fn run_capture_loop(
    runner: &mut dyn DetectorRunner,
    source: InputSource,
) -> anyhow::Result<()> {
    let mut cam = source.open_capture()?;

    loop {
        let frame_available = runner.run_step(&mut cam)?;
        if !frame_available {
            break;
        }
    }

    Ok(())
}
