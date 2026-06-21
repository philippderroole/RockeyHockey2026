use anyhow::Result;
use nalgebra::Point2;

mod stepper;
mod stepper_handle;

pub use stepper::{DryRunStepper, GrblStepper};
pub use stepper_handle::StepperHandle;
pub use stepper_handle::spawn_stepper_worker;

pub trait Stepper: Send {
    fn calibrate(&mut self) -> Result<()>;
    fn move_to_position(&mut self, position: Point2<f64>, feedrate: u32) -> Result<()>;
}
