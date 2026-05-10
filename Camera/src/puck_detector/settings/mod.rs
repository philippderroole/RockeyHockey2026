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

    #[serde(default)]
    pub target_names: Vec<String>,
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
            target_names: Vec::new(),
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

    pub fn target_name(&self, target_index: usize) -> String {
        let fallback = if target_index == 0 {
            "Primary target".to_string()
        } else {
            format!("Target {}", target_index + 1)
        };

        self.target_names
            .get(target_index)
            .map(|name| name.trim())
            .filter(|name| !name.is_empty())
            .map(|name| name.to_string())
            .unwrap_or(fallback)
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
