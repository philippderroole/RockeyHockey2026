use serde::{Deserialize, Serialize};

pub use crop_settings::CropSettings;
pub use hsv_settings::HsvThresholds;
pub use quality_settings::ProcessingQuality;

mod crop_settings;
mod hsv_settings;
mod quality_settings;

#[derive(Clone, Serialize, Deserialize)]
pub struct RuntimeDetectorSettings {
    pub detector: DetectorSettings,
    pub hsv: HsvThresholds,

    #[serde(default)]
    pub additional_hsv_targets: Vec<HsvThresholds>,
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
            additional_hsv_targets: Vec::new(),
        }
    }
}

impl RuntimeDetectorSettings {
    pub fn all_hsv_targets(&self) -> Vec<HsvThresholds> {
        let mut targets = Vec::with_capacity(1 + self.additional_hsv_targets.len());
        targets.push(self.hsv);
        targets.extend(self.additional_hsv_targets.iter().copied());
        targets
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
