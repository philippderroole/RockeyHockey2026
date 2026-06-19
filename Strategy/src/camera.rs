use std::io::ErrorKind;
use std::net::{SocketAddr, UdpSocket};
use std::sync::mpsc::{self, Receiver};
use std::thread;
use std::time::{Duration, Instant};

use anyhow::{Context, Result};
use nalgebra::Point2;
use serde::Deserialize;

pub enum DetectionTarget {
    Puck,
    Robot,
    Unknown,
}

pub struct Detection {
    pub target: DetectionTarget,
    pub position: Point2<f64>,
    pub timestamp: Instant,
}

#[derive(Debug, Deserialize)]
struct DetectorMessage {
    #[serde(default)]
    detections: Vec<ReceivedDetection>,
}

#[derive(Debug, Deserialize)]
struct ReceivedDetection {
    target_name: String,
    x: f64,
    y: f64,
}

pub fn spawn_camera_listener(host: &str, port: u16) -> Result<Receiver<Vec<Detection>>> {
    let remote: SocketAddr = format!("{host}:{port}")
        .parse()
        .with_context(|| format!("invalid camera endpoint: {host}:{port}"))?;

    let socket = UdpSocket::bind("0.0.0.0:0").context("bind UDP listener")?;
    socket.connect(remote).context("connect UDP listener")?;
    socket
        .set_read_timeout(Some(Duration::from_millis(1000)))
        .context("set UDP read timeout")?;

    let (tx, rx) = mpsc::channel();

    thread::Builder::new()
        .name("camera-listener".into())
        .spawn(move || {
            let mut buf = vec![0_u8; 65_535];
            loop {
                match socket.recv(&mut buf) {
                    Ok(size) => {
                        let payload = &buf[..size];
                        if let Ok(detections) = parse_message(payload)
                            && tx.send(detections).is_err()
                        {
                            break;
                        }
                    }
                    Err(err) if err.kind() == ErrorKind::WouldBlock => {}
                    Err(err) if err.kind() == ErrorKind::TimedOut => {}
                    Err(err) => {
                        eprintln!("camera socket error: {err}");
                    }
                }
            }
        })
        .context("spawn camera listener thread")?;

    Ok(rx)
}

fn parse_message(bytes: &[u8]) -> anyhow::Result<Vec<Detection>> {
    let message: DetectorMessage = serde_json::from_slice(bytes).context("parse camera message")?;

    Ok(message
        .detections
        .into_iter()
        .map(|detection| {
            let target = match detection.target_name.as_str() {
                "Puck" => DetectionTarget::Puck,
                "Robot" => DetectionTarget::Robot,
                _ => DetectionTarget::Unknown,
            };
            let position = Point2::new(detection.x, detection.y);
            let timestamp = Instant::now();

            Detection {
                target,
                position,
                timestamp,
            }
        })
        .collect())
}
