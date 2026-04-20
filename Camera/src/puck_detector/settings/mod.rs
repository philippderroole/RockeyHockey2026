use serde::{Deserialize, Serialize};

pub use crop_settings::CropSettings;
pub use hsv_settings::HsvThresholds;
pub use quality_settings::ProcessingQuality;

use crate::puck_detector::VirtualCoordinateSystem;

mod crop_settings;
mod hsv_settings;
mod quality_settings;

#[derive(Clone, Copy, Serialize, Deserialize)]
pub struct RuntimeDetectorSettings {
    pub detector: DetectorSettings,
    pub hsv: HsvThresholds,
    #[serde(default)]
    pub virtual_coordinates: VirtualCoordinateSystem,
}

impl Default for RuntimeDetectorSettings {
    fn default() -> Self {
        Self {
            detector: DetectorSettings {
                quality: ProcessingQuality::UltraLow,
                crop: CropSettings {
                    enabled: true,
                    left_pct: 0.0,
                    top_pct: 0.0,
                    width_pct: 1.0,
                    height_pct: 1.0,
                },
            },
            hsv: HsvThresholds::default(),
            virtual_coordinates: VirtualCoordinateSystem::default(),
        }
    }
}

#[derive(Clone, Copy, Serialize, Deserialize)]
pub struct DetectorSettings {
    pub quality: ProcessingQuality,
    pub crop: CropSettings,
}

impl Default for DetectorSettings {
    fn default() -> Self {
        Self {
            quality: ProcessingQuality::Medium,
            crop: CropSettings::disabled(),
        }
    }
}
