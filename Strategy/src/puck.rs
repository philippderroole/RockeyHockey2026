use std::{collections::VecDeque, time::Instant};

use nalgebra::{Point2, Vector2};

const VELOCITY_HISTORY_SIZE: usize = 5;

pub struct Puck {
    position: Point2<f64>,
    velocity: Vector2<f64>,
    last_seen: Instant,
    detection_history: VecDeque<(Point2<f64>, Instant)>,
}

impl Puck {
    pub fn new() -> Self {
        Self {
            position: Point2::new(0.0, 0.0),
            velocity: Vector2::new(0.0, 0.0),
            last_seen: Instant::now(),
            detection_history: VecDeque::with_capacity(VELOCITY_HISTORY_SIZE),
        }
    }

    pub fn update(&mut self, new_position: Point2<f64>, timestamp: Instant) {
        self.position = new_position;
        self.last_seen = timestamp;
        self.detection_history
            .push_back((self.position, self.last_seen));

        while self.detection_history.len() > VELOCITY_HISTORY_SIZE {
            self.detection_history.pop_front();
        }

        self.velocity = self.estimate_velocity_from_history();
    }

    pub fn set_position(&mut self, new_position: Point2<f64>) {
        self.position = new_position;
        self.velocity = Vector2::new(0.0, 0.0);
        self.last_seen = Instant::now();
        self.detection_history.clear();
        self.detection_history
            .push_back((self.position, self.last_seen));
    }

    pub fn x(&self) -> f64 {
        self.position.x
    }

    pub fn y(&self) -> f64 {
        self.position.y
    }

    pub fn velocity(&self) -> Vector2<f64> {
        self.velocity
    }

    fn estimate_velocity_from_history(&self) -> Vector2<f64> {
        if self.detection_history.len() < 2 {
            return Vector2::new(0.0, 0.0);
        }

        let reference_time = self.detection_history.front().unwrap().1;
        let mut time_values = Vec::with_capacity(self.detection_history.len());
        let mut x_values = Vec::with_capacity(self.detection_history.len());
        let mut y_values = Vec::with_capacity(self.detection_history.len());

        for (position, timestamp) in &self.detection_history {
            let t = timestamp.duration_since(reference_time).as_secs_f64();
            time_values.push(t);
            x_values.push(position.x);
            y_values.push(position.y);
        }

        let slope_x = linear_regression_slope(&time_values, &x_values);
        let slope_y = linear_regression_slope(&time_values, &y_values);

        Vector2::new(slope_x, slope_y)
    }
}

fn linear_regression_slope(times: &[f64], values: &[f64]) -> f64 {
    let sample_count = times.len();
    if sample_count < 2 {
        return 0.0;
    }

    let mean_time = times.iter().sum::<f64>() / sample_count as f64;
    let mean_value = values.iter().sum::<f64>() / sample_count as f64;

    let mut numerator = 0.0;
    let mut denominator = 0.0;

    for (time, value) in times.iter().zip(values.iter()) {
        let centered_time = time - mean_time;
        numerator += centered_time * (value - mean_value);
        denominator += centered_time * centered_time;
    }

    if denominator <= f64::EPSILON {
        0.0
    } else {
        numerator / denominator
    }
}
