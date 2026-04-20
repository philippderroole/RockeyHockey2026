use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Serialize, Deserialize)]
pub struct VirtualCoordinateSystem {
    pub enabled: bool,
    pub x_size: f64,
    pub y_size: f64,
    #[serde(default)]
    pub corners: CornerTrackers,
}

impl Default for VirtualCoordinateSystem {
    fn default() -> Self {
        Self {
            enabled: false,
            x_size: 100.0,
            y_size: 100.0,
            corners: CornerTrackers::default(),
        }
    }
}

impl VirtualCoordinateSystem {
    pub fn normalized(self) -> Self {
        Self {
            enabled: self.enabled,
            x_size: self.x_size.max(1.0),
            y_size: self.y_size.max(1.0),
            corners: self.corners.normalized(),
        }
    }
}

#[derive(Clone, Copy, Serialize, Deserialize, Default)]
pub struct CornerTrackers {
    #[serde(default)]
    pub top_left: Option<NormalizedPoint>,
    #[serde(default)]
    pub top_right: Option<NormalizedPoint>,
    #[serde(default)]
    pub bottom_right: Option<NormalizedPoint>,
    #[serde(default)]
    pub bottom_left: Option<NormalizedPoint>,
}

impl CornerTrackers {
    fn normalized(self) -> Self {
        Self {
            top_left: self.top_left.map(NormalizedPoint::normalized),
            top_right: self.top_right.map(NormalizedPoint::normalized),
            bottom_right: self.bottom_right.map(NormalizedPoint::normalized),
            bottom_left: self.bottom_left.map(NormalizedPoint::normalized),
        }
    }
}

#[derive(Clone, Copy, Serialize, Deserialize, Default)]
pub struct NormalizedPoint {
    pub x: f64,
    pub y: f64,
}

impl NormalizedPoint {
    pub fn normalized(self) -> Self {
        Self {
            x: self.x.clamp(0.0, 1.0),
            y: self.y.clamp(0.0, 1.0),
        }
    }
}
