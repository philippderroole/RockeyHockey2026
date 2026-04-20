use opencv::core::Rect;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Serialize, Deserialize)]
pub struct CropSettings {
    pub enabled: bool,
    pub left_pct: f64,
    pub top_pct: f64,
    pub width_pct: f64,
    pub height_pct: f64,
}

impl CropSettings {
    pub fn disabled() -> Self {
        Self {
            enabled: false,
            left_pct: 0.0,
            top_pct: 0.0,
            width_pct: 1.0,
            height_pct: 1.0,
        }
    }

    pub fn as_rect(self, frame_width: i32, frame_height: i32) -> Rect {
        if !self.enabled {
            return Rect::new(0, 0, frame_width.max(1), frame_height.max(1));
        }

        let frame_width = frame_width.max(1);
        let frame_height = frame_height.max(1);

        let left = self.left_pct.clamp(0.0, 1.0);
        let top = self.top_pct.clamp(0.0, 1.0);
        // Keep crop inside frame even when left/top are near the edge.
        let width_pct = self.width_pct.clamp(0.01, 1.0 - left);
        let height_pct = self.height_pct.clamp(0.01, 1.0 - top);

        let x = ((frame_width as f64) * left).round() as i32;
        let y = ((frame_height as f64) * top).round() as i32;
        let width = ((frame_width as f64) * width_pct).round() as i32;
        let height = ((frame_height as f64) * height_pct).round() as i32;

        let width = width.min((frame_width - x).max(1)).max(1);
        let height = height.min((frame_height - y).max(1)).max(1);

        Rect::new(x, y, width, height)
    }
}
