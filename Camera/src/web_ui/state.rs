use std::sync::{Arc, Condvar, Mutex};
use std::time::Duration;

use opencv::prelude::MatTraitConst;
use serde::{Deserialize, Serialize};

use crate::puck_detector::{RuntimeDetectorSettings, TimedFrameProcessing};

use super::render::{draw_debug_detection, encode_jpeg};

#[derive(Clone)]
pub struct SharedRuntimeSettings {
    settings: Arc<Mutex<RuntimeDetectorSettings>>,
}

#[derive(Clone, Copy, Serialize)]
pub struct WebPlaybackState {
    pub paused: bool,
}

#[derive(Clone, Copy, Deserialize)]
pub struct PlaybackControlUpdate {
    pub paused: Option<bool>,
    pub reprocess_current_frame: Option<bool>,
    pub step_next_frame: Option<bool>,
}

#[derive(Clone, Copy)]
pub struct PlaybackControlSnapshot {
    pub paused: bool,
    pub reprocess_generation: u64,
    pub step_generation: u64,
}

#[derive(Default)]
struct PlaybackControlState {
    paused: bool,
    reprocess_generation: u64,
    step_generation: u64,
}

#[derive(Clone, Default)]
pub struct SharedPlaybackControl {
    inner: Arc<Mutex<PlaybackControlState>>,
}

impl SharedPlaybackControl {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(PlaybackControlState::default())),
        }
    }

    pub fn apply_update(&self, update: PlaybackControlUpdate) -> WebPlaybackState {
        let mut paused = false;
        if let Ok(mut guard) = self.inner.lock() {
            if let Some(next_paused) = update.paused {
                guard.paused = next_paused;
            }

            if update.reprocess_current_frame.unwrap_or(false) {
                guard.reprocess_generation = guard.reprocess_generation.wrapping_add(1);
            }

            if update.step_next_frame.unwrap_or(false) {
                guard.step_generation = guard.step_generation.wrapping_add(1);
            }

            paused = guard.paused;
        }

        WebPlaybackState { paused }
    }

    pub fn get_state(&self) -> WebPlaybackState {
        if let Ok(guard) = self.inner.lock() {
            return WebPlaybackState {
                paused: guard.paused,
            };
        }

        WebPlaybackState { paused: false }
    }

    pub fn snapshot(&self) -> PlaybackControlSnapshot {
        if let Ok(guard) = self.inner.lock() {
            return PlaybackControlSnapshot {
                paused: guard.paused,
                reprocess_generation: guard.reprocess_generation,
                step_generation: guard.step_generation,
            };
        }

        PlaybackControlSnapshot {
            paused: false,
            reprocess_generation: 0,
            step_generation: 0,
        }
    }
}

impl SharedRuntimeSettings {
    pub fn new(initial: RuntimeDetectorSettings) -> Self {
        Self {
            settings: Arc::new(Mutex::new(initial)),
        }
    }

    pub fn get(&self) -> RuntimeDetectorSettings {
        self.settings.lock().map(|guard| *guard).unwrap_or_default()
    }

    pub fn set(&self, next: RuntimeDetectorSettings) {
        if let Ok(mut guard) = self.settings.lock() {
            *guard = next;
        }
    }
}

#[derive(Default)]
struct PreviewFrames {
    detection_jpeg: Option<Vec<u8>>,
    mask_jpeg: Option<Vec<u8>>,
    h_mask_jpeg: Option<Vec<u8>>,
    s_mask_jpeg: Option<Vec<u8>>,
    v_mask_jpeg: Option<Vec<u8>>,
    latest_log: Option<WebRuntimeLog>,
    frame_count: u64,
    capture_sum_ms: f64,
    capture_samples: u64,
    detect_sum_ms: f64,
    detect_samples: u64,
    total_sum_ms: f64,
    total_samples: u64,
}

#[derive(Clone, Serialize)]
pub(super) struct WebRuntimeLog {
    frame: u64,
    detection_found: bool,
    capture_ms: Option<f64>,
    avg_capture_ms: Option<f64>,
    detect_ms: Option<f64>,
    avg_detect_ms: Option<f64>,
    total_ms: Option<f64>,
    avg_total_ms: Option<f64>,
    detection_point: Option<WebNormalizedPoint>,
}

#[derive(Clone)]
pub(super) struct PreviewSnapshot {
    pub frame: u64,
    pub detection_jpeg: Option<Vec<u8>>,
    pub mask_jpeg: Option<Vec<u8>>,
    pub h_mask_jpeg: Option<Vec<u8>>,
    pub s_mask_jpeg: Option<Vec<u8>>,
    pub v_mask_jpeg: Option<Vec<u8>>,
    pub latest_log: Option<WebRuntimeLog>,
}
#[derive(Clone, Serialize)]
struct WebNormalizedPoint {
    x: f64,
    y: f64,
}

#[derive(Clone, Default)]
pub struct SharedPreviewFrames {
    frames: Arc<(Mutex<PreviewFrames>, Condvar)>,
}

impl SharedPreviewFrames {
    pub fn new() -> Self {
        Self {
            frames: Arc::new((Mutex::new(PreviewFrames::default()), Condvar::new())),
        }
    }

    pub fn update_from_processed(&self, processed: &TimedFrameProcessing) -> anyhow::Result<()> {
        if processed.original.empty() {
            return Ok(());
        }

        let detection_overlay = draw_debug_detection(&processed.original, &processed.output)?;
        let detection_jpeg = encode_jpeg(&detection_overlay)?;

        let mask_jpeg = if let Some(mask) = &processed.green_mask {
            if mask.empty() {
                None
            } else {
                Some(encode_jpeg(mask)?)
            }
        } else {
            None
        };

        let h_mask_jpeg = if let Some(mask) = &processed.h_mask {
            if mask.empty() {
                None
            } else {
                Some(encode_jpeg(mask)?)
            }
        } else {
            None
        };

        let s_mask_jpeg = if let Some(mask) = &processed.s_mask {
            if mask.empty() {
                None
            } else {
                Some(encode_jpeg(mask)?)
            }
        } else {
            None
        };

        let v_mask_jpeg = if let Some(mask) = &processed.v_mask {
            if mask.empty() {
                None
            } else {
                Some(encode_jpeg(mask)?)
            }
        } else {
            None
        };

        let total_ms =
            Some(processed.capture_ms.unwrap_or(0.0) + processed.detect_ms.unwrap_or(0.0));

        let width = processed.original.cols().max(1) as f64;
        let height = processed.original.rows().max(1) as f64;
        let detection_point = processed
            .output
            .inner
            .as_ref()
            .and_then(|detection| detection.detection)
            .map(|point| WebNormalizedPoint {
                x: (point.x as f64 / width).clamp(0.0, 1.0),
                y: (point.y as f64 / height).clamp(0.0, 1.0),
            });
        let detection_found = detection_point.is_some();

        let (lock, condvar) = &*self.frames;
        if let Ok(mut guard) = lock.lock() {
            guard.frame_count += 1;
            if let Some(capture_ms) = processed.capture_ms {
                guard.capture_sum_ms += capture_ms;
                guard.capture_samples += 1;
            }
            if let Some(detect_ms) = processed.detect_ms {
                guard.detect_sum_ms += detect_ms;
                guard.detect_samples += 1;
            }
            if let Some(total_ms) = total_ms {
                guard.total_sum_ms += total_ms;
                guard.total_samples += 1;
            }
            guard.detection_jpeg = Some(detection_jpeg);
            guard.mask_jpeg = mask_jpeg;
            guard.h_mask_jpeg = h_mask_jpeg;
            guard.s_mask_jpeg = s_mask_jpeg;
            guard.v_mask_jpeg = v_mask_jpeg;
            guard.latest_log = Some(WebRuntimeLog {
                frame: guard.frame_count,
                detection_found,
                capture_ms: processed.capture_ms,
                avg_capture_ms: (guard.capture_samples > 0)
                    .then_some(guard.capture_sum_ms / guard.capture_samples as f64),
                detect_ms: processed.detect_ms,
                avg_detect_ms: (guard.detect_samples > 0)
                    .then_some(guard.detect_sum_ms / guard.detect_samples as f64),
                total_ms,
                avg_total_ms: (guard.total_samples > 0)
                    .then_some(guard.total_sum_ms / guard.total_samples as f64),
                detection_point,
            });
            condvar.notify_all();
        }

        Ok(())
    }

    pub fn reset_runtime_averages(&self) {
        let (lock, _) = &*self.frames;
        if let Ok(mut guard) = lock.lock() {
            guard.capture_sum_ms = 0.0;
            guard.capture_samples = 0;
            guard.detect_sum_ms = 0.0;
            guard.detect_samples = 0;
            guard.total_sum_ms = 0.0;
            guard.total_samples = 0;

            if let Some(log) = &mut guard.latest_log {
                log.avg_capture_ms = None;
                log.avg_detect_ms = None;
                log.avg_total_ms = None;
            }
        }
    }

    pub(super) fn snapshot(&self) -> PreviewSnapshot {
        let (lock, _) = &*self.frames;
        if let Ok(guard) = lock.lock() {
            return PreviewSnapshot {
                frame: guard.frame_count,
                detection_jpeg: guard.detection_jpeg.clone(),
                mask_jpeg: guard.mask_jpeg.clone(),
                h_mask_jpeg: guard.h_mask_jpeg.clone(),
                s_mask_jpeg: guard.s_mask_jpeg.clone(),
                v_mask_jpeg: guard.v_mask_jpeg.clone(),
                latest_log: guard.latest_log.clone(),
            };
        }

        PreviewSnapshot {
            frame: 0,
            detection_jpeg: None,
            mask_jpeg: None,
            h_mask_jpeg: None,
            s_mask_jpeg: None,
            v_mask_jpeg: None,
            latest_log: None,
        }
    }

    pub(super) fn wait_for_snapshot_after(
        &self,
        last_seen_frame: u64,
        timeout: Duration,
    ) -> PreviewSnapshot {
        let (lock, condvar) = &*self.frames;

        let mut guard = match lock.lock() {
            Ok(guard) => guard,
            Err(_) => return self.snapshot(),
        };

        if guard.frame_count <= last_seen_frame {
            match condvar.wait_timeout_while(guard, timeout, |frames| {
                frames.frame_count <= last_seen_frame
            }) {
                Ok((next_guard, _)) => {
                    guard = next_guard;
                }
                Err(_) => return self.snapshot(),
            }
        }

        PreviewSnapshot {
            frame: guard.frame_count,
            detection_jpeg: guard.detection_jpeg.clone(),
            mask_jpeg: guard.mask_jpeg.clone(),
            h_mask_jpeg: guard.h_mask_jpeg.clone(),
            s_mask_jpeg: guard.s_mask_jpeg.clone(),
            v_mask_jpeg: guard.v_mask_jpeg.clone(),
            latest_log: guard.latest_log.clone(),
        }
    }
}
