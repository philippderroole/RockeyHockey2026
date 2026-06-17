mod app;
mod camera;
mod config;
mod puck_predictor;
mod stepper;
mod strategy;
mod types;

use anyhow::Result;
use clap::Parser;

use crate::app::Runtime;
use crate::camera::spawn_camera_listener;
use crate::config::{
    DEFAULT_CAMERA_HOST, DEFAULT_CAMERA_PORT, DEFAULT_STEPPER_BAUDRATE, DEFAULT_STEPPER_PORT,
};
use crate::stepper::{DryRunStepper, GrblStepper, Stepper};

#[derive(Debug, Parser)]
#[command(author, version, about = "Fast headless Rocky Hockey controller")]
struct Cli {
    #[arg(long, default_value = DEFAULT_CAMERA_HOST)]
    camera_host: String,
    #[arg(long, default_value_t = DEFAULT_CAMERA_PORT)]
    camera_port: u16,
    #[arg(long, default_value = DEFAULT_STEPPER_PORT)]
    stepper_port: String,
    #[arg(long, default_value_t = DEFAULT_STEPPER_BAUDRATE)]
    stepper_baudrate: u32,
    #[arg(long, default_value_t = false)]
    dry_run: bool,
    #[arg(long, default_value_t = true)]
    bot_active: bool,
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    let rx = spawn_camera_listener(&cli.camera_host, cli.camera_port)?;

    let mut stepper: Box<dyn Stepper> = if cli.dry_run {
        Box::new(DryRunStepper)
    } else {
        Box::new(GrblStepper::connect(
            &cli.stepper_port,
            cli.stepper_baudrate,
        )?)
    };

    stepper.calibrate()?;

    Runtime::new(rx, stepper)?.run()
}
