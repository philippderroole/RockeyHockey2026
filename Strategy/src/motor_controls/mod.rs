mod stepper;
mod worker_thread;

use anyhow::Result;
use nalgebra::Point2;
use std::sync::mpsc;

pub use stepper::{DryRunStepper, GrblStepper};
pub use worker_thread::spawn_stepper_worker;

#[derive(Debug)]
pub(crate) enum StepperCommand {
    Calibrate(mpsc::Sender<Result<()>>),
    Move(StepperMoveCommand),
    Stop,
}

pub trait Stepper: Send {
    fn calibrate(&mut self) -> Result<()>;
    fn move_to_position(&mut self, position: Point2<f64>, feedrate: u32) -> Result<()>;
    fn stop(&mut self) -> Result<()>;
}

#[derive(Debug, Clone, Copy)]
pub struct StepperMoveCommand {
    pub position: Point2<f64>,
    pub feedrate: u32,
}
