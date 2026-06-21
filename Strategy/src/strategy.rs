use nalgebra::Point2;

use crate::{
    config::{
        BOARD_HEIGHT, BOARD_WIDTH, GOAL_Y_MAX, GOAL_Y_MIN, LEFT_BORDER_REPOSITION_X,
        PLAYABLE_PUCK_THRESHOLD, PUCK_RADIUS, RESTING_PUCK_THRESHOLD, ROBOT_ATTACK_MAX_X,
        ROBOT_DEFENSE_MAX_Y, ROBOT_DEFENSE_MIN_Y, ROBOT_MAX_X, ROBOT_MAX_Y,
    },
    puck::Puck,
    simulation::predict_puck_path,
};

pub fn get_next_move(
    _robot_pos: Point2<f64>,
    puck: &Puck,
) -> (Option<Point2<f64>>, Vec<Point2<f64>>) {
    let predicted_puck_path = predict_puck_path(puck);

    let new_target = if puck_at_left_border(puck)
        && puck.velocity().magnitude() >= RESTING_PUCK_THRESHOLD
    {
        None
    } else if let Some(goal_block_target) = goal_block_target(&predicted_puck_path) {
        Some(goal_block_target)
    } else if puck_at_left_border(puck) {
        left_border_reposition_target(puck)
    } else if puck.velocity().magnitude() < PLAYABLE_PUCK_THRESHOLD && puck.x() < ROBOT_ATTACK_MAX_X
    {
        attack_target(puck)
    } else {
        None
    };

    (new_target, predicted_puck_path)
}

fn goal_block_target(predicted_puck_path: &[Point2<f64>]) -> Option<Point2<f64>> {
    predicted_puck_path
        .iter()
        .find(|point| point.x <= PUCK_RADIUS && point.y >= GOAL_Y_MIN && point.y <= GOAL_Y_MAX)
        .map(|point| {
            Point2::new(
                10.0,
                point.y.clamp(ROBOT_DEFENSE_MIN_Y, ROBOT_DEFENSE_MAX_Y),
            )
        })
}

fn attack_target(puck: &Puck) -> Option<Point2<f64>> {
    let puck_position = Point2::new(puck.x(), puck.y());
    let goal_center = Point2::new(BOARD_HEIGHT, (GOAL_Y_MIN + GOAL_Y_MAX) * 0.5);
    let aim_point = preferred_attack_aim_point(puck_position, goal_center);

    Some(overshoot_target(puck_position, aim_point))
}

fn preferred_attack_aim_point(puck_position: Point2<f64>, goal_center: Point2<f64>) -> Point2<f64> {
    let top_bank = Point2::new(goal_center.x, -goal_center.y);
    let bottom_bank = Point2::new(goal_center.x, BOARD_WIDTH * 2.0 - goal_center.y);

    let top_bounce_x = wall_bounce_x(puck_position, top_bank, 0.0);
    let bottom_bounce_x = wall_bounce_x(puck_position, bottom_bank, BOARD_WIDTH);

    let top_bounce_is_safe = top_bounce_x
        .map(|x| (PUCK_RADIUS..=BOARD_HEIGHT - PUCK_RADIUS).contains(&x))
        .unwrap_or(false);
    let bottom_bounce_is_safe = bottom_bounce_x
        .map(|x| (PUCK_RADIUS..=BOARD_HEIGHT - PUCK_RADIUS).contains(&x))
        .unwrap_or(false);

    match (top_bounce_is_safe, bottom_bounce_is_safe) {
        (true, false) => top_bank,
        (false, true) => bottom_bank,
        (true, true) => {
            if puck_position.y < BOARD_WIDTH * 0.5 {
                top_bank
            } else {
                bottom_bank
            }
        }
        (false, false) => goal_center,
    }
}

fn wall_bounce_x(puck_position: Point2<f64>, aim_point: Point2<f64>, wall_y: f64) -> Option<f64> {
    let delta_y = aim_point.y - puck_position.y;
    if delta_y.abs() <= f64::EPSILON {
        return None;
    }

    let t = (wall_y - puck_position.y) / delta_y;
    if !(0.0..=1.0).contains(&t) {
        return None;
    }

    Some(puck_position.x + (aim_point.x - puck_position.x) * t)
}

fn overshoot_target(puck_position: Point2<f64>, aim_point: Point2<f64>) -> Point2<f64> {
    let shot_vector = aim_point - puck_position;
    let shot_distance = shot_vector.magnitude();
    if shot_distance <= f64::EPSILON {
        return puck_position;
    }

    let overshoot_distance = (PUCK_RADIUS * 2.5).max(20.0);
    let overshoot_position = puck_position + shot_vector / shot_distance * overshoot_distance;

    Point2::new(
        overshoot_position.x.clamp(0.0, ROBOT_MAX_X),
        overshoot_position.y.clamp(0.0, ROBOT_MAX_Y),
    )
}

fn puck_at_left_border(puck: &Puck) -> bool {
    puck.x() < LEFT_BORDER_REPOSITION_X
}

fn left_border_reposition_target(puck: &Puck) -> Option<Point2<f64>> {
    let puck_position = Point2::new(puck.x(), puck.y());
    let horizontal_offset = (PUCK_RADIUS * 4.0).min(ROBOT_MAX_X);
    let vertical_offset = if puck.y() < BOARD_WIDTH * 0.5 {
        PUCK_RADIUS * 3.0
    } else {
        -PUCK_RADIUS * 3.0
    };

    Some(Point2::new(
        (puck_position.x + horizontal_offset).clamp(0.0, ROBOT_MAX_X),
        (puck_position.y + vertical_offset).clamp(0.0, ROBOT_MAX_Y),
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use nalgebra::{Point2, Vector2};

    fn puck_at_left_border_with_velocity(velocity: Vector2<f64>) -> Puck {
        let mut puck = Puck::new();
        puck.set_position(Point2::new(PUCK_RADIUS, GOAL_Y_MIN + 10.0));
        puck.set_velocity(velocity);
        puck
    }

    #[test]
    fn left_border_puck_waits_while_moving() {
        let puck =
            puck_at_left_border_with_velocity(Vector2::new(0.0, RESTING_PUCK_THRESHOLD + 1.0));

        let (target, _) = get_next_move(Point2::new(0.0, 0.0), &puck);

        assert!(target.is_none());
    }

    #[test]
    fn left_border_puck_repositions_when_resting() {
        let puck = puck_at_left_border_with_velocity(Vector2::new(0.0, 0.0));

        let (target, _) = get_next_move(Point2::new(0.0, 0.0), &puck);

        let target = target.expect("expected a reposition target");
        assert!(target.x > puck.x());
        assert_ne!(target.y, puck.y());
    }

    #[test]
    fn attack_target_overshoots_puck_toward_goal() {
        let mut puck = Puck::new();
        puck.set_position(Point2::new(180.0, 180.0));
        puck.set_velocity(Vector2::new(10.0, 0.0));

        let target = attack_target(&puck).expect("expected an attacking target");

        assert!(target.x > puck.x());
        assert!(target.x <= ROBOT_MAX_X);
        assert!(target.y >= 0.0);
        assert!(target.y <= ROBOT_MAX_Y);
    }
}
