use std::time::Instant;

use log::info;
use opencv::prelude::MatTraitConst;
use opencv::{core::Mat, videoio::VideoCapture};

use crate::puck_detector::{
    DetectionOutput, DetectionPipeline, DetectorSettings, PuckDetector, RuntimeDetectorSettings,
};

pub struct TimedPuckDetector<T> {
    inner: T,
    detection_frame_count: u64,
    total_detect_ms: f64,
    capture_frame_count: u64,
    total_capture_ms: f64,
}

impl<T> TimedPuckDetector<T> {
    fn new_with_inner(inner: T) -> Self {
        Self {
            inner,
            detection_frame_count: 0,
            total_detect_ms: 0.0,
            capture_frame_count: 0,
            total_capture_ms: 0.0,
        }
    }

    fn measure_execution_time<F, R>(func: F) -> (R, f64)
    where
        F: FnOnce() -> R,
    {
        let start = Instant::now();
        let result = func();
        let elapsed = start.elapsed();
        let elapsed_ms = elapsed.as_secs_f64() * 1000.0;
        (result, elapsed_ms)
    }
}

impl TimedPuckDetector<PuckDetector> {
    pub fn new() -> Self {
        Self::new_with_inner(PuckDetector::new())
    }

    pub fn with_settings(settings: DetectorSettings) -> Self {
        Self::new_with_inner(PuckDetector::with_settings(settings))
    }

    pub fn with_runtime_settings(runtime_settings: RuntimeDetectorSettings) -> Self {
        Self::new_with_inner(PuckDetector::with_runtime_settings(runtime_settings))
    }

    pub fn update_runtime_settings(&mut self, runtime_settings: RuntimeDetectorSettings) {
        self.inner.apply_runtime_settings(runtime_settings);
    }

    pub fn detect_current_frame(&mut self) -> opencv::Result<Option<TimedFrameProcessing>> {
        if self.inner.buffers.original.empty() {
            return Ok(None);
        }

        let detect_output = self.detect()?;
        let detect_ms = detect_output.detect_ms;

        Ok(Some(TimedFrameProcessing {
            original: self.inner.buffers.original.clone(),
            output: detect_output,
            green_mask: Some(self.inner.buffers.cleaned_mask.clone()),
            h_mask: Some(self.inner.buffers.h_mask.clone()),
            s_mask: Some(self.inner.buffers.s_mask.clone()),
            v_mask: Some(self.inner.buffers.v_mask.clone()),
            capture_ms: None,
            detect_ms: Some(detect_ms),
        }))
    }
}

impl Default for TimedPuckDetector<PuckDetector> {
    fn default() -> Self {
        Self::new()
    }
}

impl DetectionPipeline for TimedPuckDetector<PuckDetector> {
    type CaptureOutput = opencv::Result<TimedCaptureOutput>;
    type DetectOutput = opencv::Result<TimedDetectionOutput>;
    type CombinedOutput = opencv::Result<Option<TimedFrameProcessing>>;

    fn capture(&mut self, cam: &mut VideoCapture) -> opencv::Result<TimedCaptureOutput> {
        let (_, capture_ms) = Self::measure_execution_time(|| self.inner.capture(cam));

        self.total_capture_ms += capture_ms;
        self.capture_frame_count += 1;

        let avg_capture_ms = self.total_capture_ms / self.capture_frame_count as f64;
        info!(
            "Total: {:.2}ms (Capture: {:.2}ms | Detect: n/a) | Avg: {:.2}ms",
            self.total_capture_ms, capture_ms, avg_capture_ms
        );

        Ok(TimedCaptureOutput {
            inner: Some(()),
            capture_ms,
        })
    }

    fn detect(&mut self) -> opencv::Result<TimedDetectionOutput> {
        let (processed, detect_ms) = Self::measure_execution_time(|| self.inner.detect());

        self.detection_frame_count += 1;
        self.total_detect_ms += detect_ms;

        let avg_elapsed_ms = self.total_detect_ms / self.detection_frame_count as f64;

        info!(
            "Total: {:.2}ms (Capture: n/a | Detect: {:.2}ms) | Avg: {:.2}ms",
            self.total_detect_ms, detect_ms, avg_elapsed_ms
        );

        Ok(TimedDetectionOutput {
            inner: Some(processed?),
            detect_ms,
        })
    }

    fn capture_and_detect(
        &mut self,
        cam: &mut VideoCapture,
    ) -> opencv::Result<Option<TimedFrameProcessing>> {
        let capture_output = self.capture(cam)?;

        if self.inner.buffers.original.empty() {
            return Ok(None);
        }

        let detect_output = self.detect()?;

        let capture_ms = capture_output.capture_ms;
        let detect_ms = detect_output.detect_ms;

        Ok(Some(TimedFrameProcessing {
            original: self.inner.buffers.original.clone(),
            output: detect_output,
            green_mask: Some(self.inner.buffers.cleaned_mask.clone()),
            h_mask: Some(self.inner.buffers.h_mask.clone()),
            s_mask: Some(self.inner.buffers.s_mask.clone()),
            v_mask: Some(self.inner.buffers.v_mask.clone()),
            capture_ms: Some(capture_ms),
            detect_ms: Some(detect_ms),
        }))
    }
}

pub struct TimedDetectionOutput {
    pub inner: Option<DetectionOutput>,
    detect_ms: f64,
}

pub struct TimedCaptureOutput {
    pub inner: Option<()>,
    capture_ms: f64,
}

pub struct TimedFrameProcessing {
    pub original: Mat,
    pub output: TimedDetectionOutput,
    pub green_mask: Option<Mat>,
    pub h_mask: Option<Mat>,
    pub s_mask: Option<Mat>,
    pub v_mask: Option<Mat>,
    pub capture_ms: Option<f64>,
    pub detect_ms: Option<f64>,
}
