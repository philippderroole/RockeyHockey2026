use nalgebra::{Point2, Vector2};

use crate::{
    config::{
        BOARD_HEIGHT, BOARD_WIDTH, GOAL_Y_MAX, GOAL_Y_MIN, PUCK_RADIUS, RESTING_PUCK_THRESHOLD,
    },
    puck::Puck,
};

const WINDOW_MARGIN: f64 = 0.0;

pub fn predict_puck_path(puck: &Puck) -> Vec<Point2<f64>> {
    if puck.velocity().magnitude() < RESTING_PUCK_THRESHOLD {
        return Vec::new();
    }

    let steps = ((0.01 * puck.velocity().magnitude()) as usize * 40).min(20);
    let time_step_seconds = 0.02;

    let mut path = Vec::with_capacity(steps + 1);

    for step in 0..=steps {
        let time_seconds = step as f64 * time_step_seconds;
        let pos = predict_puck_position(puck, time_seconds);
        path.push(pos);

        // Stop predicting once the puck would hit the goal area.
        if pos.x <= PUCK_RADIUS && pos.y >= GOAL_Y_MIN && pos.y <= GOAL_Y_MAX {
            break;
        }
    }

    path
}

fn simulate_puck_motion(
    mut position: Point2<f64>,
    mut velocity: Vector2<f64>,
    total_time_seconds: f64,
    step_seconds: f64,
) -> (Point2<f64>, Vector2<f64>) {
    let min_x = WINDOW_MARGIN;
    let max_x = WINDOW_MARGIN + BOARD_HEIGHT;
    let min_y = WINDOW_MARGIN;
    let max_y = WINDOW_MARGIN + BOARD_WIDTH;

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

fn predict_puck_position(puck: &Puck, time_seconds: f64) -> Point2<f64> {
    simulate_puck_motion(
        Point2::new(puck.x(), puck.y()),
        puck.velocity(),
        time_seconds,
        0.02,
    )
    .0
}
