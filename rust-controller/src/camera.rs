use std::io::ErrorKind;
use std::net::{SocketAddr, UdpSocket};
use std::sync::mpsc::{self, Receiver};
use std::thread;
use std::time::{Duration, Instant};

use anyhow::{Context, Result};
use serde::Deserialize;

use crate::config::{
    CAM_X_OFFSET, CAM_Y_OFFSET, CAMERA_MAP_FROM_X_MAX, CAMERA_MAP_FROM_X_MIN,
    CAMERA_MAP_FROM_Y_MAX, CAMERA_MAP_FROM_Y_MIN, ROBOT_MAX_X, ROBOT_MAX_Y,
};
use crate::types::{DetectionSnapshot, Point};

#[derive(Debug, Deserialize)]
struct DetectorMessage {
    #[serde(default)]
    detections: Vec<Detection>,
}

#[derive(Debug, Deserialize)]
struct Detection {
    target_name: String,
    x: f64,
    y: f64,
}

pub fn spawn_camera_listener(host: &str, port: u16) -> Result<Receiver<DetectionSnapshot>> {
    let remote: SocketAddr = format!("{host}:{port}")
        .parse()
        .with_context(|| format!("invalid camera endpoint: {host}:{port}"))?;

    let socket = UdpSocket::bind("0.0.0.0:0").context("bind UDP listener")?;
    socket.connect(remote).context("connect UDP listener")?;
    socket
        .set_read_timeout(Some(Duration::from_millis(1000)))
        .context("set UDP read timeout")?;
    socket.send(b"subscribe").context("send subscribe")?;

    let (tx, rx) = mpsc::channel();

    thread::Builder::new()
        .name("camera-listener".into())
        .spawn(move || {
            let mut buf = vec![0_u8; 65_535];
            loop {
                match socket.recv(&mut buf) {
                    Ok(size) => {
                        let payload = &buf[..size];
                        if let Some(snapshot) = parse_message(payload)
                            && tx.send(snapshot).is_err()
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

fn parse_message(bytes: &[u8]) -> Option<DetectionSnapshot> {
    let message: DetectorMessage = serde_json::from_slice(bytes).ok()?;
    let mut puck = None;
    let mut robot = None;

    for detection in message.detections {
        match detection.target_name.as_str() {
            "Puck" => {
                puck = Some(map_camera_coordinates(detection.x, detection.y));
            }
            "Robot" => {
                robot = Some(map_camera_coordinates(detection.x, detection.y));
            }
            _ => {}
        }
    }

    Some(DetectionSnapshot {
        puck,
        robot,
        timestamp: Instant::now(),
    })
}

fn map_camera_coordinates(cam_x: f64, cam_y: f64) -> Point {
    let x = map_range(
        cam_x + CAM_X_OFFSET,
        CAMERA_MAP_FROM_X_MIN,
        CAMERA_MAP_FROM_X_MAX,
        0.0,
        ROBOT_MAX_X,
    );
    let y = map_range(
        cam_y + CAM_Y_OFFSET,
        CAMERA_MAP_FROM_Y_MIN,
        CAMERA_MAP_FROM_Y_MAX,
        0.0,
        ROBOT_MAX_Y,
    );

    Point { x, y }
}

fn map_range(value: f64, from_min: f64, from_max: f64, to_min: f64, to_max: f64) -> f64 {
    (value - from_min) / (from_max - from_min) * (to_max - to_min) + to_min
}
