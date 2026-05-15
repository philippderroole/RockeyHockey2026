use std::net::{SocketAddr, UdpSocket};
use std::sync::{Arc, Mutex};
use std::thread;

use anyhow::Context;
use opencv::core::Point;
use serde::Serialize;

use rockey_hockey::puck_detector::{
    DetectionOutput, RuntimeDetectorSettings, TimedFrameProcessing,
};

#[derive(Serialize)]
struct TargetCoordinatePacket {
    detections: Vec<TargetCoordinate>,
}

#[derive(Serialize)]
struct TargetCoordinate {
    target_index: usize,
    target_name: String,
    x: i32,
    y: i32,
}

pub struct TargetOutputSender {
    socket: Arc<UdpSocket>,
    client_addr: Arc<Mutex<Option<SocketAddr>>>,
}

impl TargetOutputSender {
    pub fn new(listen_addr: SocketAddr) -> anyhow::Result<Self> {
        let socket = Arc::new(
            UdpSocket::bind(listen_addr).context("Failed to bind UDP socket for target output")?,
        );
        let client_addr = Arc::new(Mutex::new(None));

        Self::spawn_subscription_listener(Arc::clone(&socket), Arc::clone(&client_addr));

        Ok(Self {
            socket,
            client_addr,
        })
    }

    fn spawn_subscription_listener(
        socket: Arc<UdpSocket>,
        client_addr: Arc<Mutex<Option<SocketAddr>>>,
    ) {
        thread::spawn(move || {
            let mut buffer = [0_u8; 1024];

            loop {
                match socket.recv_from(&mut buffer) {
                    Ok((_, sender_addr)) => {
                        if let Ok(mut client) = client_addr.lock() {
                            *client = Some(sender_addr);
                        }
                    }
                    Err(err) => {
                        if err.kind() == std::io::ErrorKind::Interrupted {
                            continue;
                        }

                        log::warn!("Target output subscription listener stopped: {err}");
                        break;
                    }
                }
            }
        });
    }

    pub fn publish_plain_detections(
        &self,
        runtime_settings: &RuntimeDetectorSettings,
        detections: &[Option<DetectionOutput>],
    ) -> anyhow::Result<()> {
        self.publish_coordinates(
            runtime_settings,
            detections.iter().filter_map(|detection| detection.as_ref()),
        )
    }

    pub fn publish_timed_detections(
        &self,
        runtime_settings: &RuntimeDetectorSettings,
        processed: &TimedFrameProcessing,
    ) -> anyhow::Result<()> {
        let Some(detections) = processed.output.inner.as_ref() else {
            return Ok(());
        };

        self.publish_coordinates(runtime_settings, detections.iter())
    }

    fn publish_coordinates<'a, I>(
        &self,
        runtime_settings: &RuntimeDetectorSettings,
        detections: I,
    ) -> anyhow::Result<()>
    where
        I: IntoIterator<Item = &'a DetectionOutput>,
    {
        let packet = TargetCoordinatePacket {
            detections: detections
                .into_iter()
                .filter_map(|detection| Self::detection_to_coordinate(runtime_settings, detection))
                .collect(),
        };

        if packet.detections.is_empty() {
            return Ok(());
        }

        let payload = serde_json::to_vec(&packet).context("Failed to serialize target packet")?;

        let Some(target_addr) = *self
            .client_addr
            .lock()
            .map_err(|_| anyhow::anyhow!("Target output client lock was poisoned"))?
        else {
            return Ok(());
        };

        self.socket
            .send_to(&payload, target_addr)
            .context("Failed to send target packet")?;

        Ok(())
    }

    fn detection_to_coordinate(
        runtime_settings: &RuntimeDetectorSettings,
        detection: &DetectionOutput,
    ) -> Option<TargetCoordinate> {
        let Point { x, y } = detection.detection?;

        Some(TargetCoordinate {
            target_index: detection.target_index,
            target_name: runtime_settings.target_name(detection.target_index),
            x,
            y,
        })
    }
}
