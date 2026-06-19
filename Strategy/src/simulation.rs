use nalgebra::{Point2, Vector2};

use crate::{
    config::{BOARD_HEIGHT, BOARD_WIDTH},
    puck::Puck,
};

const WINDOW_MARGIN: f64 = 0.0;
const PUCK_RADIUS: f64 = 10.0;

pub fn predict_puck_path(
    puck: &Puck,
    launch_velocity: Vector2<f64>,
    time_step_seconds: f64,
    steps: usize,
) -> Vec<Point2<f64>> {
    let mut path = Vec::with_capacity(steps + 1);

    for step in 0..=steps {
        let time_seconds = step as f64 * time_step_seconds;
        path.push(predict_puck_position(puck, time_seconds, launch_velocity));
    }

    path
}

fn simulate_puck_motion(
    mut position: Point2<f64>,
    mut velocity: Vector2<f64>,
    total_time_seconds: f64,
    step_seconds: f64,
) -> (Point2<f64>, Vector2<f64>) {
    let min_x = WINDOW_MARGIN + PUCK_RADIUS;
    let max_x = WINDOW_MARGIN + BOARD_HEIGHT - PUCK_RADIUS;
    let min_y = WINDOW_MARGIN + PUCK_RADIUS;
    let max_y = WINDOW_MARGIN + BOARD_WIDTH - PUCK_RADIUS;

    let mut remaining_time = total_time_seconds.max(0.0);
    let step_seconds = step_seconds.max(0.001);

    while remaining_time > 0.0 {
        let dt = remaining_time.min(step_seconds);

        position += velocity * dt;

        if position.x < min_x {
            position.x = min_x;
            velocity.x = -velocity.x;
        } else if position.x > max_x {
            position.x = max_x;
            velocity.x = -velocity.x;
        }

        if position.y < min_y {
            position.y = min_y;
            velocity.y = -velocity.y;
        } else if position.y > max_y {
            position.y = max_y;
            velocity.y = -velocity.y;
        }

        remaining_time -= dt;
    }

    (position, velocity)
}

fn predict_puck_position(
    puck: &Puck,
    time_seconds: f64,
    launch_velocity: Vector2<f64>,
) -> Point2<f64> {
    simulate_puck_motion(
        puck.position(),
        puck.velocity() + launch_velocity,
        time_seconds,
        0.02,
    )
    .0
}
