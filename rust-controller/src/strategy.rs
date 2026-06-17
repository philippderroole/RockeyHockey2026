use std::time::Instant;

use crate::config::{DEFENSIVE_LINE, ROBOT_MAX_Y, ROBOT_MOVE_DEADBAND_MM, ROBOT_SLOW_MOVE_DISTANCE_MM};
use crate::types::{DetectionSnapshot, MoveTarget, MoveType, Point, Puck};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum State {
    Defending,
    Attacking,
}

#[derive(Debug)]
pub struct RobotController {
    state: State,
    puck: Option<Puck>,
    last_puck_position: Point,
    last_iteration_timestamp: Instant,
}

impl RobotController {
    pub fn new() -> Self {
        Self {
            state: State::Defending,
            last_puck_position: Point::default(),
            last_iteration_timestamp: Instant::now(),
            puck: None,
        }
    }

    pub fn update(&mut self, snapshot: DetectionSnapshot) -> Option<MoveTarget> {
        self.update_puck(snapshot);
        self.update_state();

        let movement = match self.state {
            State::Defending => {
                let puck_position = self.puck.unwrap().position;
                let delta = self.last_puck_position - puck_position;
                let distance = (delta.x * delta.x + delta.y * delta.y).sqrt();

                if distance < ROBOT_MOVE_DEADBAND_MM {
                    None
                } else {
                    let move_type = if distance < ROBOT_SLOW_MOVE_DISTANCE_MM {
                        MoveType::SlowIntercept
                    } else {
                        MoveType::FastIntercept
                    };
                    let target_y = self.puck.unwrap().position.y.clamp(0.0, ROBOT_MAX_Y);
                    Some(MoveTarget {
                        x: DEFENSIVE_LINE,
                        y: target_y,
                        move_type,
                    })
                }
            }
            State::Attacking => Some(MoveTarget {
                x: self.puck.unwrap().position.x,
                y: self.puck.unwrap().position.y,
                move_type: MoveType::Defend,
            }),
        };

        self.last_puck_position = self.puck.unwrap().position;
        self.last_iteration_timestamp = Instant::now();

        if self.is_puck_behind_robot(snapshot.robot, self.puck.unwrap().position) {
            return None;
        }

        movement
    }

    fn update_puck(&mut self, snapshot: DetectionSnapshot) {
        if let Some(p) = snapshot.puck {
            self.puck = Some(Puck {
                position: p,
                velocity: calculate_velocity(
                    p,
                    self.last_puck_position,
                    snapshot.timestamp,
                    self.last_iteration_timestamp,
                ),
            });
        } else {
            self.puck = None;
        }
    }

    fn update_state(&mut self) {
        let Some(puck) = self.puck else {
            return;
        };

        let x_speed = puck.velocity.x.abs();

        match self.state {
            State::Defending => {
                if x_speed > 100.0 {
                    self.state = State::Attacking;
                }
            }
            State::Attacking => {
                if x_speed < 100.0 {
                    self.state = State::Defending;
                }
            }
        }
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
    use std::time::{Duration, Instant};

    use super::{RobotController, State};
    use crate::types::{DetectionSnapshot, MoveType, Point};

    #[test]
    fn short_travel_distance_uses_slow_intercept() {
        let mut controller = RobotController::new();
        let start = Instant::now();

        assert!(controller
            .update(DetectionSnapshot {
                puck: Some(Point { x: 0.0, y: 0.0 }),
                robot: None,
                timestamp: start,
            })
            .is_none());

        let target = controller
            .update(DetectionSnapshot {
                puck: Some(Point { x: 40.0, y: 80.0 }),
                robot: None,
                timestamp: start + Duration::from_millis(1000),
            })
            .expect("expected a move target");

        assert_eq!(target.move_type, MoveType::SlowIntercept);
        assert_eq!(controller.state, State::Defending);
    }
}
