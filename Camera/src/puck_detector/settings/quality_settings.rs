use opencv::imgproc::{INTER_LINEAR, INTER_NEAREST};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProcessingQuality {
    High,
    Medium,
    Low,
    UltraLow,
}

impl ProcessingQuality {
    pub fn scale_factor(self) -> f64 {
        match self {
            ProcessingQuality::High => 1.0,
            ProcessingQuality::Medium => 0.75,
            ProcessingQuality::Low => 0.5,
            ProcessingQuality::UltraLow => 0.2,
        }
    }

    pub fn morphology_kernel_size(self) -> i32 {
        match self {
            ProcessingQuality::High => 5,
            ProcessingQuality::Medium => 5,
            ProcessingQuality::Low => 3,
            ProcessingQuality::UltraLow => 1,
        }
    }

    pub fn resize_interpolation(self) -> i32 {
        match self {
            ProcessingQuality::High | ProcessingQuality::Medium => INTER_LINEAR,
            ProcessingQuality::Low | ProcessingQuality::UltraLow => INTER_NEAREST,
        }
    }
}
