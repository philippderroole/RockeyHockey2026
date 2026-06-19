pub const BOARD_WIDTH: f64 = 400.0;
pub const BOARD_HEIGHT: f64 = 650.0;

pub const ROBOT_MAX_X: f64 = 350.0;
pub const ROBOT_MAX_Y: f64 = 360.0;

// If the puck is moving slower than this speed, we consider it "playable" and will try to hit it
pub const PLAYABLE_PUCK_THRESHOLD: f64 = 200.0;

pub const RESTING_PUCK_THRESHOLD: f64 = 100.0;

pub const GOAL_Y_MIN: f64 = 130.0;
pub const GOAL_Y_MAX: f64 = 245.0;

pub const DEFAULT_CAMERA_HOST: &str = "192.168.2.2";
pub const DEFAULT_CAMERA_PORT: u16 = 5005;
pub const DEFAULT_STEPPER_PORT: &str = "/dev/cu.usbmodem11301";
pub const DEFAULT_STEPPER_BAUDRATE: u32 = 115200;
pub const COMMAND_QUEUE_CAPACITY: usize = 10;

pub const PUCK_RADIUS: f64 = 25.0 / 2.0;
