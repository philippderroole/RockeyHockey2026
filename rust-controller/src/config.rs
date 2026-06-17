use std::time::Duration;

pub const BOARD_WIDTH: f64 = 400.0;
pub const BOARD_HEIGHT: f64 = 800.0;

pub const ROBOT_MAX_X: f64 = 350.0;
pub const ROBOT_MAX_Y: f64 = 360.0;

pub const DEFENSIVE_LINE: f64 = 20.0;

pub const ROBOT_MOVE_FEEDRATE: u32 = 20_000;
pub const ROBOT_SLOW_MOVE_FEEDRATE: u32 = 10_000;
pub const ROBOT_SLOW_MOVE_DISTANCE_MM: f64 = 100.0;
pub const ROBOT_MOVE_DEADBAND_MM: f64 = 20.0;
pub const ROBOT_TARGET_SMOOTHING_ALPHA: f64 = 0.35;
pub const AGGRESSIVE_COMMAND_MIN_INTERVAL: Duration = Duration::from_millis(8);
pub const BACKPRESSURE_COMMAND_INTERVAL: Duration = Duration::from_millis(80);
pub const RECENT_CLOSE_COMMAND_INTERVAL: Duration = Duration::from_millis(250);
pub const RECENT_CLOSE_COMMAND_DEADBAND_MM: f64 = 35.0;
pub const COMMAND_QUEUE_BACKPRESSURE_DEPTH: usize = 2;
pub const COMMAND_QUEUE_CAPACITY: usize = 0;
pub const AGGRESSIVE_MOVE_DEADBAND_MM: f64 = 6.0;

pub const COMMAND_TTL: Duration = Duration::from_millis(60);
pub const CAMERA_STALE_TIMEOUT: Duration = Duration::from_millis(120);
pub const METRICS_PRINT_INTERVAL: Duration = Duration::from_millis(1000);

pub const CAM_X_OFFSET: f64 = -42.0;
pub const CAM_Y_OFFSET: f64 = 0.0;

pub const CAMERA_MAP_FROM_X_MIN: f64 = 0.0;
pub const CAMERA_MAP_FROM_X_MAX: f64 = 269.0;
pub const CAMERA_MAP_FROM_Y_MIN: f64 = 0.0;
pub const CAMERA_MAP_FROM_Y_MAX: f64 = 326.0;

pub const DEFAULT_CAMERA_HOST: &str = "192.168.2.2";
pub const DEFAULT_CAMERA_PORT: u16 = 5005;
pub const DEFAULT_STEPPER_PORT: &str = "/dev/cu.usbmodem11301";
pub const DEFAULT_STEPPER_BAUDRATE: u32 = 115200;
