use anyhow::Result;
use nalgebra::Point2;
use std::sync::mpsc;

#[derive(Debug, Clone)]
pub enum Command {
    Calibrate(mpsc::Sender<Result<()>>),
    MoveTo(Point2<f64>),
    Shoot {
        staging: Point2<f64>,
        target: Point2<f64>,
    },
    Defend(Point2<f64>),
}

impl Command {
    pub fn get_target_position(&self) -> Point2<f64> {
        match self {
            Command::MoveTo(position) => *position,
            Command::Shoot { staging, .. } => *staging,
            Command::Defend(position) => *position,
            Command::Calibrate(_) => Point2::new(0.0, 0.0),
        }
    }
}
