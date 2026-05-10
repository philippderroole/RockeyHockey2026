use std::net::{SocketAddr, UdpSocket};

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
    socket: UdpSocket,
    target_addr: SocketAddr,
}

impl TargetOutputSender {
    pub fn new(target_addr: SocketAddr) -> anyhow::Result<Self> {
        let socket =
            UdpSocket::bind("0.0.0.0:0").context("Failed to bind UDP socket for target output")?;

        Ok(Self {
            socket,
            target_addr,
        })
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
        let _ = self.socket.send_to(&payload, self.target_addr);

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
