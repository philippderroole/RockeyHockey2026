use std::time::Instant;

use nalgebra::{Point2, Vector2};

pub struct Puck {
    position: Point2<f64>,
    velocity: Vector2<f64>,
    last_seen: Instant,
}

impl Puck {
    pub fn new() -> Self {
        Self {
            position: Point2::new(0.0, 0.0),
            velocity: Vector2::new(0.0, 0.0),
            last_seen: Instant::now(),
        }
    }

    pub fn update(&mut self, new_position: Point2<f64>, timestamp: Instant) {
        let old_position = self.position;
        let dt = (timestamp - self.last_seen).as_secs_f64();
        if dt > 0.0 {
            // Point2 - Point2 yields a Vector2; divide by dt to get velocity vector
            self.velocity = (new_position - old_position) / dt;
        }
        self.position = new_position;
        self.last_seen = timestamp;
    }

    pub fn set_velocity(&mut self, new_velocity: Vector2<f64>) {
        self.velocity = new_velocity;
    }

    pub fn set_position(&mut self, new_position: Point2<f64>) {
        self.position = new_position;
    }

    pub fn x(&self) -> f64 {
        self.position.x
    }

    pub fn y(&self) -> f64 {
        self.position.y
    }

    pub fn position(&self) -> Point2<f64> {
        self.position
    }

    pub fn velocity(&self) -> Vector2<f64> {
        self.velocity
    }
}
