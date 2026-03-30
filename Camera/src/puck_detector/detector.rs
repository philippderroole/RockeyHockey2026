use opencv::{
    core::{self, Mat, Point, Scalar, Size},
    imgproc::{self, COLOR_BGR2HSV, MORPH_ELLIPSE, MORPH_OPEN},
    prelude::MatTraitConst,
    videoio::{VideoCapture, VideoCaptureTrait},
};

use crate::puck_detector::{
    DetectionPipeline, VirtualCoordinateSystem,
    settings::{DetectorSettings, HsvThresholds, RuntimeDetectorSettings},
};

pub struct PuckDetector {
    lower_green: Scalar,
    upper_green: Scalar,
    settings: DetectorSettings,
    hsv_thresholds: HsvThresholds,
    virtual_coordinates: VirtualCoordinateSystem,
    morph_kernel: Mat,
    pub buffers: ProcessingBuffers,
}

#[derive(Default)]
pub struct ProcessingBuffers {
    pub original: Mat,
    cropped: Mat,
    resized: Mat,
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
            virtual_coordinates: VirtualCoordinateSystem::default(),
        })
    }

    pub fn with_runtime_settings(runtime_settings: RuntimeDetectorSettings) -> Self {
        let normalized_hsv = runtime_settings.hsv.normalized();
        let (lower_green, upper_green) = normalized_hsv.as_scalars();

        Self {
            lower_green,
            upper_green,
            settings: runtime_settings.detector,
            hsv_thresholds: normalized_hsv,
            virtual_coordinates: runtime_settings.virtual_coordinates.normalized(),
            morph_kernel: Mat::default(),
            buffers: ProcessingBuffers::default(),
        }
    }

    pub fn apply_runtime_settings(&mut self, runtime_settings: RuntimeDetectorSettings) {
        let old_quality = self.settings.quality;
        self.settings = runtime_settings.detector;

        self.hsv_thresholds = runtime_settings.hsv.normalized();
        (self.lower_green, self.upper_green) = self.hsv_thresholds.as_scalars();
        self.virtual_coordinates = runtime_settings.virtual_coordinates.normalized();

        if self.settings.quality != old_quality {
            self.morph_kernel = Mat::default();
        }
    }
}

impl DetectionPipeline for PuckDetector {
    type CaptureOutput = opencv::Result<()>;
    type DetectOutput = opencv::Result<DetectionOutput>;
    type CombinedOutput = opencv::Result<Option<DetectionOutput>>;

    fn capture(&mut self, cam: &mut VideoCapture) -> opencv::Result<()> {
        cam.read(&mut self.buffers.original)?;

        Ok(())
    }

    fn detect(&mut self) -> opencv::Result<DetectionOutput> {
        if self.buffers.original.empty() {
            return Ok(DetectionOutput { detection: None });
        }

        self.crop()?;
        self.resize()?;
        self.create_mask()?;

        let scale_factor = self.settings.quality.scale_factor();
        let detection = self
            .detect_center_in_resized_mask()?
            .map(|center| self.map_center_to_original(center, scale_factor));

        Ok(DetectionOutput { detection })
    }

    fn capture_and_detect(
        &mut self,
        cam: &mut VideoCapture,
    ) -> opencv::Result<Option<DetectionOutput>> {
        self.capture(cam)?;
        let output = self.detect()?;

        Ok(Some(output))
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
            .as_rect(self.buffers.original.cols(), self.buffers.original.rows());
        let roi = self.buffers.original.roi(crop_rect)?;

        self.buffers.cropped = roi.clone_pointee();
        Ok(())
    }

    fn resize(&mut self) -> opencv::Result<f64> {
        let quality = self.settings.quality;
        let scale_factor = quality.scale_factor();

        imgproc::resize(
            &self.buffers.cropped,
            &mut self.buffers.resized,
            Size::new(0, 0),
            scale_factor,
            scale_factor,
            quality.resize_interpolation(),
        )?;

        Ok(scale_factor)
    }

    fn detect_center_in_resized_mask(&self) -> opencv::Result<Option<Point>> {
        let moments = imgproc::moments(&self.buffers.cleaned_mask, true)?;
        if moments.m00.abs() < f64::EPSILON {
            return Ok(None);
        }

        let center_x = (moments.m10 / moments.m00) as i32;
        let center_y = (moments.m01 / moments.m00) as i32;
        Ok(Some(Point::new(center_x, center_y)))
    }

    fn map_center_to_original(&self, center: Point, scale_factor: f64) -> Point {
        let crop_rect = self
            .settings
            .crop
            .as_rect(self.buffers.original.cols(), self.buffers.original.rows());

        let inv_scale = if scale_factor <= 0.0 {
            1.0
        } else {
            1.0 / scale_factor
        };

        let mapped_x = ((center.x as f64) * inv_scale).round() as i32 + crop_rect.x;
        let mapped_y = ((center.y as f64) * inv_scale).round() as i32 + crop_rect.y;
        Point::new(mapped_x, mapped_y)
    }

    fn create_mask(&mut self) -> opencv::Result<()> {
        if self.morph_kernel.empty() {
            self.morph_kernel = imgproc::get_structuring_element(
                MORPH_ELLIPSE,
                Size::new(
                    self.settings.quality.morphology_kernel_size(),
                    self.settings.quality.morphology_kernel_size(),
                ),
                Point::new(-1, -1),
            )?;
        }

        #[cfg(any(target_arch = "arm", all(target_arch = "aarch64", target_os = "linux")))]
        imgproc::cvt_color(
            &self.buffers.resized,
            &mut self.buffers.hsv,
            COLOR_BGR2HSV,
            0,
        )?;

        #[cfg(not(any(target_arch = "arm", all(target_arch = "aarch64", target_os = "linux"))))]
        imgproc::cvt_color(
            &self.buffers.resized,
            &mut self.buffers.hsv,
            COLOR_BGR2HSV,
            0,
            core::AlgorithmHint::ALGO_HINT_DEFAULT,
        )?;

        core::extract_channel(&self.buffers.hsv, &mut self.buffers.h_channel, 0)?;
        core::extract_channel(&self.buffers.hsv, &mut self.buffers.s_channel, 1)?;
        core::extract_channel(&self.buffers.hsv, &mut self.buffers.v_channel, 2)?;

        core::in_range(
            &self.buffers.h_channel,
            &Scalar::all(self.hsv_thresholds.h_min as f64),
            &Scalar::all(self.hsv_thresholds.h_max as f64),
            &mut self.buffers.h_mask,
        )?;
        core::in_range(
            &self.buffers.s_channel,
            &Scalar::all(self.hsv_thresholds.s_min as f64),
            &Scalar::all(self.hsv_thresholds.s_max as f64),
            &mut self.buffers.s_mask,
        )?;
        core::in_range(
            &self.buffers.v_channel,
            &Scalar::all(self.hsv_thresholds.v_min as f64),
            &Scalar::all(self.hsv_thresholds.v_max as f64),
            &mut self.buffers.v_mask,
        )?;

        core::in_range(
            &self.buffers.hsv,
            &self.lower_green,
            &self.upper_green,
            &mut self.buffers.mask,
        )?;

        if self.morph_kernel.rows() <= 1 && self.morph_kernel.cols() <= 1 {
            std::mem::swap(&mut self.buffers.mask, &mut self.buffers.cleaned_mask);
        } else {
            imgproc::morphology_ex(
                &self.buffers.mask,
                &mut self.buffers.cleaned_mask,
                MORPH_OPEN,
                &self.morph_kernel,
                Point::new(-1, -1),
                1,
                core::BORDER_CONSTANT,
                imgproc::morphology_default_border_value()?,
            )?;
        }

        Ok(())
    }
}

pub struct DetectionOutput {
    pub detection: Option<Point>,
}
