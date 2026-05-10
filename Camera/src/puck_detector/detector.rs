use opencv::{
    core::{self, Mat, Point, Scalar, Size},
    imgproc::{self, COLOR_BGR2HSV, MORPH_ELLIPSE, MORPH_OPEN},
    prelude::MatTraitConst,
    videoio::{VideoCapture, VideoCaptureTrait},
};

use crate::puck_detector::{
    DetectionPipeline,
    settings::{DetectorSettings, HsvThresholds, RuntimeDetectorSettings},
};

pub struct PuckDetector {
    pub original: Mat,
    cropped: Mat,
    resized: Mat,
    frame_buffers: ProcessingBuffers,
    settings: DetectorSettings,
    morph_kernel: Mat,
    pub detector_states: Vec<DetectorState>,
}

pub struct DetectorState {
    pub hsv_thresholds: HsvThresholds,
    pub buffers: ProcessingBuffers,
}

#[derive(Default)]
pub struct ProcessingBuffers {
    hsv: Mat,
    h_channel: Mat,
    s_channel: Mat,
    v_channel: Mat,
    mask: Mat,
    pub cleaned_mask: Mat,
    pub h_mask: Mat,
    pub s_mask: Mat,
    pub v_mask: Mat,
}

impl PuckDetector {
    pub fn new() -> Self {
        Self::with_settings(DetectorSettings::default())
    }

    pub fn with_settings(settings: DetectorSettings) -> Self {
        Self::with_runtime_settings(RuntimeDetectorSettings {
            detector: settings,
            hsv: HsvThresholds::default(),
            additional_hsv_targets: Vec::new(),
            target_names: Vec::new(),
        })
    }

    pub fn with_runtime_settings(runtime_settings: RuntimeDetectorSettings) -> Self {
        Self {
            original: Mat::default(),
            cropped: Mat::default(),
            resized: Mat::default(),
            frame_buffers: ProcessingBuffers::default(),
            settings: runtime_settings.detector,
            morph_kernel: Mat::default(),
            detector_states: Self::build_detector_states(&runtime_settings),
        }
    }

    pub fn apply_runtime_settings(&mut self, runtime_settings: RuntimeDetectorSettings) {
        let old_quality = self.settings.quality;
        self.settings = runtime_settings.detector;
        self.detector_states = Self::build_detector_states(&runtime_settings);

        if self.settings.quality != old_quality {
            self.morph_kernel = Mat::default();
            self.frame_buffers = ProcessingBuffers::default();
        }
    }

    pub fn target_previews(&self) -> Vec<TargetPreviewOutput> {
        self.detector_states
            .iter()
            .enumerate()
            .map(|(target_index, state)| TargetPreviewOutput {
                target_index,
                hsv_thresholds: state.hsv_thresholds,
                mask: state.buffers.cleaned_mask.clone(),
                h_mask: state.buffers.h_mask.clone(),
                s_mask: state.buffers.s_mask.clone(),
                v_mask: state.buffers.v_mask.clone(),
            })
            .collect()
    }

    fn build_detector_states(runtime_settings: &RuntimeDetectorSettings) -> Vec<DetectorState> {
        let targets = runtime_settings.all_hsv_targets();

        if targets.is_empty() {
            return vec![DetectorState {
                hsv_thresholds: HsvThresholds::default().normalized(),
                buffers: ProcessingBuffers::default(),
            }];
        }

        targets
            .into_iter()
            .map(|hsv_thresholds| DetectorState {
                hsv_thresholds: hsv_thresholds.normalized(),
                buffers: ProcessingBuffers::default(),
            })
            .collect()
    }
}

impl DetectionPipeline for PuckDetector {
    type CaptureOutput = opencv::Result<()>;
    type DetectOutput = opencv::Result<Vec<DetectionOutput>>;
    type CombinedOutput = opencv::Result<Vec<Option<DetectionOutput>>>;

    fn capture(&mut self, cam: &mut VideoCapture) -> opencv::Result<()> {
        cam.read(&mut self.original)?;

        Ok(())
    }

    fn detect(&mut self) -> opencv::Result<Vec<DetectionOutput>> {
        if self.original.empty() {
            return Ok(Vec::new());
        }

        self.crop()?;

        let quality = self.settings.quality;
        let scale_factor = quality.scale_factor();
        self.resize(quality.resize_interpolation(), scale_factor)?;
        self.ensure_morph_kernel()?;

        let morph_kernel = &self.morph_kernel;
        let crop_rect = self
            .settings
            .crop
            .as_rect(self.original.cols(), self.original.rows());

        // Convert resized frame to HSV once and extract channels into frame-level buffers
        #[cfg(any(target_arch = "arm", all(target_arch = "aarch64", target_os = "linux")))]
        imgproc::cvt_color(&self.resized, &mut self.frame_buffers.hsv, COLOR_BGR2HSV, 0)?;

        #[cfg(not(any(target_arch = "arm", all(target_arch = "aarch64", target_os = "linux"))))]
        imgproc::cvt_color(
            &self.resized,
            &mut self.frame_buffers.hsv,
            COLOR_BGR2HSV,
            0,
            core::AlgorithmHint::ALGO_HINT_DEFAULT,
        )?;

        core::extract_channel(
            &self.frame_buffers.hsv,
            &mut self.frame_buffers.h_channel,
            0,
        )?;
        core::extract_channel(
            &self.frame_buffers.hsv,
            &mut self.frame_buffers.s_channel,
            1,
        )?;
        core::extract_channel(
            &self.frame_buffers.hsv,
            &mut self.frame_buffers.v_channel,
            2,
        )?;

        let mut detections = Vec::with_capacity(self.detector_states.len());
        for (target_index, state) in self.detector_states.iter_mut().enumerate() {
            Self::create_mask(&morph_kernel, &self.frame_buffers, state)?;

            let detection = Self::detect_center_in_resized_mask(state)?
                .map(|center| Self::map_center_to_original(center, scale_factor, crop_rect));

            detections.push(DetectionOutput {
                target_index,
                hsv_thresholds: state.hsv_thresholds,
                detection,
            });
        }

        Ok(detections)
    }

    fn capture_and_detect(
        &mut self,
        cam: &mut VideoCapture,
    ) -> opencv::Result<Vec<Option<DetectionOutput>>> {
        self.capture(cam)?;
        let output = self.detect()?;

        Ok(output.into_iter().map(Some).collect())
    }
}

impl Default for PuckDetector {
    fn default() -> Self {
        Self::new()
    }
}

impl PuckDetector {
    fn crop(&mut self) -> opencv::Result<()> {
        let crop_rect = self
            .settings
            .crop
            .as_rect(self.original.cols(), self.original.rows());
        let roi = self.original.roi(crop_rect)?;

        self.cropped = roi.clone_pointee();
        Ok(())
    }

    fn resize(&mut self, quality: i32, scale_factor: f64) -> opencv::Result<f64> {
        imgproc::resize(
            &self.cropped,
            &mut self.resized,
            Size::new(0, 0),
            scale_factor,
            scale_factor,
            quality,
        )?;

        Ok(scale_factor)
    }

    fn ensure_morph_kernel(&mut self) -> opencv::Result<()> {
        if !self.morph_kernel.empty() {
            return Ok(());
        }

        self.morph_kernel = imgproc::get_structuring_element(
            MORPH_ELLIPSE,
            Size::new(
                self.settings.quality.morphology_kernel_size(),
                self.settings.quality.morphology_kernel_size(),
            ),
            Point::new(-1, -1),
        )?;

        Ok(())
    }

    fn detect_center_in_resized_mask(state: &DetectorState) -> opencv::Result<Option<Point>> {
        let moments = imgproc::moments(&state.buffers.cleaned_mask, true)?;
        if moments.m00.abs() < f64::EPSILON {
            return Ok(None);
        }

        let center_x = (moments.m10 / moments.m00) as i32;
        let center_y = (moments.m01 / moments.m00) as i32;
        Ok(Some(Point::new(center_x, center_y)))
    }

    fn map_center_to_original(center: Point, scale_factor: f64, crop_rect: core::Rect) -> Point {
        let inv_scale = if scale_factor <= 0.0 {
            1.0
        } else {
            1.0 / scale_factor
        };

        let mapped_x = ((center.x as f64) * inv_scale).round() as i32 + crop_rect.x;
        let mapped_y = ((center.y as f64) * inv_scale).round() as i32 + crop_rect.y;
        Point::new(mapped_x, mapped_y)
    }

    fn create_mask(
        morph_kernel: &Mat,
        frame_buffers: &ProcessingBuffers,
        state: &mut DetectorState,
    ) -> opencv::Result<()> {
        let (lower_hsv, upper_hsv) = state.hsv_thresholds.as_scalars();

        core::in_range(
            &frame_buffers.h_channel,
            &Scalar::all(state.hsv_thresholds.h_min as f64),
            &Scalar::all(state.hsv_thresholds.h_max as f64),
            &mut state.buffers.h_mask,
        )?;
        core::in_range(
            &frame_buffers.s_channel,
            &Scalar::all(state.hsv_thresholds.s_min as f64),
            &Scalar::all(state.hsv_thresholds.s_max as f64),
            &mut state.buffers.s_mask,
        )?;
        core::in_range(
            &frame_buffers.v_channel,
            &Scalar::all(state.hsv_thresholds.v_min as f64),
            &Scalar::all(state.hsv_thresholds.v_max as f64),
            &mut state.buffers.v_mask,
        )?;

        core::in_range(
            &frame_buffers.hsv,
            &lower_hsv,
            &upper_hsv,
            &mut state.buffers.mask,
        )?;

        if morph_kernel.rows() <= 1 && morph_kernel.cols() <= 1 {
            std::mem::swap(&mut state.buffers.mask, &mut state.buffers.cleaned_mask);
        } else {
            imgproc::morphology_ex(
                &state.buffers.mask,
                &mut state.buffers.cleaned_mask,
                MORPH_OPEN,
                morph_kernel,
                Point::new(-1, -1),
                1,
                core::BORDER_CONSTANT,
                imgproc::morphology_default_border_value()?,
            )?;
        }

        Ok(())
    }
}

#[derive(Clone, Copy)]
pub struct DetectionOutput {
    pub target_index: usize,
    pub hsv_thresholds: HsvThresholds,
    pub detection: Option<Point>,
}

#[derive(Clone)]
pub struct TargetPreviewOutput {
    pub target_index: usize,
    pub hsv_thresholds: HsvThresholds,
    pub mask: Mat,
    pub h_mask: Mat,
    pub s_mask: Mat,
    pub v_mask: Mat,
}
