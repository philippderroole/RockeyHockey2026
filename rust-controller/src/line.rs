use nalgebra::Vector2;

use crate::types::Point;

#[derive(Debug, Clone, Copy)]
pub struct Line {
    p1: Point,
    direction: Vector2<f64>,
}

impl Line {
    pub fn from_points(p1: Point, p2: Point) -> Self {
        Self {
            p1,
            direction: Vector2::new(p2.x - p1.x, p2.y - p1.y),
        }
    }

    pub fn from_point_and_slope(p1: Point, m: f64) -> Self {
        Self {
            p1,
            direction: Vector2::new(1.0, m),
        }
    }

    pub fn slope(self) -> Option<f64> {
        if self.direction.x.abs() < f64::EPSILON {
            None
        } else {
            Some(self.direction.y / self.direction.x)
        }
    }
}
