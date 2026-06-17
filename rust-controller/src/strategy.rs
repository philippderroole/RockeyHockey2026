use std::time::Instant;

use crate::config::{
    ATTACK_LANE_SPEED_MAX, BOARD_HEIGHT, BOARD_WIDTH, DEFENSIVE_LINE, PREDICTION_MAX_BOUNCES,
    PREDICTION_MIN_SPEED, PUCK_RADIUS, ROBOT_DEFEND_Y, ROBOT_MAX_X, ROBOT_MAX_Y, SPEED_THRESHOLD,
    STATE_ATTACK_X_THRESHOLD, STATE_TRANSITION_SPEED_THRESHOLD,
};
use crate::puck_predictor::{BoardDimensions, PuckPredictor};
use crate::types::{DetectionSnapshot, MoveTarget, MoveType, Point, Puck};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum State {
    Defending,
    AttackingMode,
}

#[derive(Debug)]
pub struct RobotController {
    active: bool,
    state: State,
    puck: Puck,
    last_puck_position: Point,
    last_frame_timestamp: Instant,
    predictor: PuckPredictor,
}

impl RobotController {
    pub fn new(now: Instant) -> Self {
        Self::with_board_dimensions(now, BoardDimensions::new(BOARD_WIDTH, BOARD_HEIGHT))
    }

    pub fn with_board_dimensions(now: Instant, board_dimensions: BoardDimensions) -> Self {
        Self {
            active: false,
            state: State::Defending,
            last_puck_position: Point::default(),
            last_frame_timestamp: now,
            puck: Puck::default(),
            predictor: PuckPredictor::new(board_dimensions, PUCK_RADIUS, PREDICTION_MAX_BOUNCES),
        }
    }

    pub fn update(&mut self, snapshot: DetectionSnapshot, bot_active: bool) -> Option<MoveTarget> {
        self.active = bot_active;

        match snapshot.puck {
            Some(p) => {
                self.puck.velocity = calculate_velocity(
                    p,
                    self.last_puck_position,
                    snapshot.timestamp,
                    self.last_frame_timestamp,
                );
                self.puck.position = p;
            }
            None => {
                self.state = State::Defending;
                self.last_puck_position = Point::default();
                self.last_frame_timestamp = snapshot.timestamp;
                self.puck = Puck::default();
            }
        };

        let speed = self.speed();
        let predicted = self.make_prediction(self.puck);

        self.update_state(speed, predicted);

        let movement = match self.state {
            State::Defending => {
                if speed > SPEED_THRESHOLD {
                    let fast_target_y = self.puck.position.y.clamp(0.0, ROBOT_MAX_Y);
                    Some(MoveTarget {
                        x: DEFENSIVE_LINE,
                        y: fast_target_y,
                        move_type: MoveType::FastIntercept,
                    })
                } else {
                    let target = predicted.unwrap_or(self.puck.position);
                    Some(MoveTarget {
                        x: DEFENSIVE_LINE,
                        y: target.y,
                        move_type: MoveType::SlowIntercept,
                    })
                }
            }
            State::AttackingMode => Some(MoveTarget {
                x: self.puck.position.x,
                y: self.puck.position.y,
                move_type: MoveType::Defend,
            }),
        };

        self.last_puck_position = self.puck.position;
        self.last_frame_timestamp = snapshot.timestamp;

        if self.is_puck_behind_robot(snapshot.robot, self.puck.position) {
            return None;
        }

        movement
    }

    fn update_state(&mut self, speed: f64, predicted: Option<Point>) {
        if !self.active {
            self.state = State::Defending;
            return;
        }

        if let Some(predicted) = predicted {
            if predicted.y > ROBOT_DEFEND_Y && speed > ATTACK_LANE_SPEED_MAX {
                self.state = State::Defending;
            }
        }

        if self.puck.position.x > STATE_ATTACK_X_THRESHOLD
            && speed < STATE_TRANSITION_SPEED_THRESHOLD
        {
            self.state = State::AttackingMode;
        }
    }

    #[cfg(test)]
    pub fn state(&self) -> State {
        self.state
    }

    fn speed(&self) -> f64 {
        (self.puck.velocity.x * self.puck.velocity.x + self.puck.velocity.y * self.puck.velocity.y)
            .sqrt()
    }

    fn make_prediction(&self, puck: Puck) -> Option<Point> {
        if self.speed() < PREDICTION_MIN_SPEED {
            return None;
        }

        self.predictor.predict(puck.position, puck.velocity, 0.25)
    }

    fn is_puck_behind_robot(&self, robot: Option<Point>, puck: Point) -> bool {
        let Some(robot) = robot else {
            return false;
        };

        if robot.y < 0.0 || puck.x < 0.0 || puck.y < 0.0 {
            return false;
        }

        robot.y > puck.y && robot.x > puck.x
    }
}

fn calculate_velocity(
    current: Point,
    previous: Point,
    now: Instant,
    last_frame_timestamp: Instant,
) -> Point {
    let dt = now.duration_since(last_frame_timestamp).as_secs_f64();
    if dt <= 0.0 {
        return Point::default();
    }

    Point {
        x: (current.x - previous.x) / dt,
        y: (current.y - previous.y) / dt,
    }
}

#[cfg(test)]
mod tests {
    use std::time::Duration;

    use super::*;

    #[test]
    fn transitions_to_playback_on_slow_close_puck() {
        let start = Instant::now();
        let mut controller = RobotController::new(start);

        let _ = controller.update(
            DetectionSnapshot {
                puck: Some(Point { x: 200.0, y: 100.0 }),
                robot: Some(Point { x: 20.0, y: 110.0 }),
                timestamp: start + Duration::from_millis(20),
            },
            true,
        );

        let _ = controller.update(
            DetectionSnapshot {
                puck: Some(Point { x: 196.0, y: 100.0 }),
                robot: Some(Point { x: 20.0, y: 110.0 }),
                timestamp: start + Duration::from_millis(120),
            },
            true,
        );

        assert_eq!(controller.state(), State::AttackingMode);
    }

    #[test]
    fn attacking_mode_targets_puck() {
        let start = Instant::now();
        let mut controller = RobotController::new(start);

        let _ = controller.update(
            DetectionSnapshot {
                puck: Some(Point { x: 200.0, y: 100.0 }),
                robot: Some(Point { x: 20.0, y: 110.0 }),
                timestamp: start + Duration::from_millis(20),
            },
            true,
        );

        let _ = controller.update(
            DetectionSnapshot {
                puck: Some(Point { x: 196.0, y: 100.0 }),
                robot: Some(Point { x: 20.0, y: 110.0 }),
                timestamp: start + Duration::from_millis(120),
            },
            true,
        );

        assert_eq!(controller.state(), State::AttackingMode);
        let target = controller.update(
            DetectionSnapshot {
                puck: Some(Point { x: 195.0, y: 100.0 }),
                robot: Some(Point { x: 20.0, y: 110.0 }),
                timestamp: start + Duration::from_millis(220),
            },
            true,
        );
        let target = target.expect("attack mode should produce a target");
        assert_eq!(target.x, 195.0);
        assert_eq!(target.y, 100.0);
        assert_eq!(target.move_type, MoveType::Defend);
    }

    #[test]
    fn attacks_when_puck_is_nearly_stationary() {
        let start = Instant::now();
        let mut controller = RobotController::new(start);

        let _ = controller.update(
            DetectionSnapshot {
                puck: Some(Point { x: 200.0, y: 100.0 }),
                robot: Some(Point { x: 20.0, y: 110.0 }),
                timestamp: start + Duration::from_millis(20),
            },
            true,
        );

        let _ = controller.update(
            DetectionSnapshot {
                puck: Some(Point { x: 199.3, y: 100.2 }),
                robot: Some(Point { x: 20.0, y: 110.0 }),
                timestamp: start + Duration::from_millis(120),
            },
            true,
        );

        assert_eq!(controller.state(), State::AttackingMode);
    }
}
