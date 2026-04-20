use std::any;

use image::RgbImage;
use raspicam_rs::{
    RaspiCam,
    bindings::{RASPICAM_EXPOSURE, RASPICAM_FORMAT},
};

pub struct PiCamera {
    cfg: config::CameraConfig,
    frame_chan: (mpsc::UnboundedSender<Mat>, mpsc::UnboundedReceiver<Mat>),
}

impl PiCamera {
    pub async fn new(cfg: config::CameraConfig) -> Result<Self> {
        Ok(PiCamera {
            cfg,
            frame_chan: mpsc::unbounded_channel(),
        })
    }
}

async fn start(&mut self) -> Result<()> {
    let cfg = self.cfg.clone();

    // spin up a new thread for the camera processing
    // because if you do it in the main tick task it will block everything
    // and won't be good for the health of the overall system.
    let sender = self.frame_chan.0.clone();
    std::thread::spawn(move || {
        let mut raspicam = RaspiCam::new();
        raspicam
            .set_capture_size(640, 480)
            .set_frame_rate(120)
            .set_format(RASPICAM_FORMAT::RASPICAM_FORMAT_RGB)
            .set_sensor_mode(7)
            .set_shutter_speed(15000)
            .open(true)?;

        loop {
            raspicam.grab();

            Mat::new_nd(&[cfg.width as i32, cfg.height as i32], CV_8UC3, None, None).unwrap();
        }
        {
            let _ = sender.send(mat);
        }
    });

    Ok(())
}
