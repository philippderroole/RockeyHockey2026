use opencv::core::Scalar;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Serialize, Deserialize)]
pub struct HsvThresholds {
    pub h_min: i32,
    pub s_min: i32,
    pub v_min: i32,
    pub h_max: i32,
    pub s_max: i32,
    pub v_max: i32,
}

impl Default for HsvThresholds {
    fn default() -> Self {
        Self {
            h_min: 36,
            s_min: 91,
            v_min: 100,
            h_max: 47,
            s_max: 255,
            v_max: 209,
        }
    }
}

impl HsvThresholds {
    pub fn normalized(self) -> Self {
        let h_min = self.h_min.clamp(0, 179);
        let s_min = self.s_min.clamp(0, 255);
        let v_min = self.v_min.clamp(0, 255);
        let h_max = self.h_max.clamp(h_min, 179);
        let s_max = self.s_max.clamp(s_min, 255);
        let v_max = self.v_max.clamp(v_min, 255);

        Self {
            h_min,
            s_min,
            v_min,
            h_max,
            s_max,
            v_max,
        }
    }

    pub fn as_scalars(self) -> (Scalar, Scalar) {
        let normalized = self.normalized();
        (
            Scalar::new(
                normalized.h_min as f64,
                normalized.s_min as f64,
                normalized.v_min as f64,
                0.0,
            ),
            Scalar::new(
                normalized.h_max as f64,
                normalized.s_max as f64,
                normalized.v_max as f64,
                0.0,
            ),
        )
    }
}
