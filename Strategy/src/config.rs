pub const BOARD_WIDTH: f64 = 400.0;
pub const BOARD_HEIGHT: f64 = 650.0;

pub const SIMULATOR_BORDER: f64 = 10.0;

pub const WINDOW_WIDTH: f64 = BOARD_WIDTH + SIMULATOR_BORDER * 2.0;
pub const WINDOW_HEIGHT: f64 = BOARD_HEIGHT + 70.0;

pub const ROBOT_MAX_X: f64 = 350.0;
pub const ROBOT_MAX_Y: f64 = 360.0;

// The tracker is not perfectly centered on the robot, so we need to offset the target position to compensate for that
pub const ROBOT_TARGET_OFFSET: f64 = 7.5;

pub const ROBOT_DEFENSE_MIN_Y: f64 = 150.0;
pub const ROBOT_DEFENSE_MAX_Y: f64 = 215.0;

pub const ROBOT_ATTACK_MAX_X: f64 = 300.0;

// If the puck is moving slower than this speed, we consider it "playable" and will try to hit it
pub const PLAYABLE_PUCK_THRESHOLD: f64 = 100.0;

pub const RESTING_PUCK_THRESHOLD: f64 = 100.0;
pub const LEFT_BORDER_REPOSITION_X: f64 = 80.0;

pub const GOAL_Y_MIN: f64 = 130.0;
pub const GOAL_Y_MAX: f64 = 245.0;

pub const DEFAULT_CAMERA_HOST: &str = "192.168.2.2";
pub const DEFAULT_CAMERA_PORT: u16 = 5005;
pub const DEFAULT_STEPPER_PORT: &str = "/dev/cu.usbmodem11301";
pub const DEFAULT_STEPPER_BAUDRATE: u32 = 115200;
pub const COMMAND_QUEUE_CAPACITY: usize = 100;

pub const PUCK_RADIUS: f64 = 25.0 / 2.0;
