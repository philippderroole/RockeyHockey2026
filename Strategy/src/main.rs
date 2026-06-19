extern crate piston_window;

use std::{sync::mpsc::RecvTimeoutError, time::Duration};

use crate::{
    camera::{DetectionTarget, spawn_camera_listener},
    config::{
        BOARD_HEIGHT, BOARD_WIDTH, DEFAULT_CAMERA_HOST, DEFAULT_CAMERA_PORT,
        DEFAULT_STEPPER_BAUDRATE, DEFAULT_STEPPER_PORT, GOAL_Y_MAX, GOAL_Y_MIN,
        PLAYABLE_PUCK_THRESHOLD, SIMULATION_VELOCITY_PER_PIXEL,
    },
    motor_controls::{DryRunStepper, GrblStepper, Stepper, spawn_stepper_worker},
    puck::Puck,
    simulation::predict_puck_path,
};
use clap::Parser;
use nalgebra::Point2;
use piston_window::*;

mod camera;
mod config;
mod motor_controls;
mod puck;
mod simulation;

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
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    let mut stepper: Box<dyn Stepper> = if cli.dry_run {
        Box::new(spawn_stepper_worker(Box::new(DryRunStepper::new()))?)
    } else {
        Box::new(spawn_stepper_worker(Box::new(GrblStepper::connect(
            &cli.stepper_port,
            cli.stepper_baudrate,
        )?))?)
    };

    stepper.calibrate()?;

    let enable_detection = false;
    let rx = spawn_camera_listener("127.0.0.1", 8000)?;

    let mut window: PistonWindow = WindowSettings::new("shapes", [BOARD_HEIGHT, BOARD_WIDTH])
        .exit_on_esc(true)
        .build()
        .map_err(|e| anyhow::anyhow!("failed to create window: {e}"))?;

    let mut robot_target_position = Point2::new(200.0, 300.0);
    let mut robot_current_position = Point2::new(100.0, 200.0);

    let mut puck = Puck::new();
    let mut events = Events::new(EventSettings::new().lazy(true).ups(60).max_fps(60));

    let mut cursor_position = [0.0, 0.0];

    while let Some(e) = events.next(&mut window) {
        if enable_detection {
            match rx.recv_timeout(Duration::from_millis(10)) {
                Ok(detections) => {
                    for detection in detections {
                        match detection.target {
                            DetectionTarget::Puck => {
                                puck.update(detection.position, detection.timestamp);
                            }
                            DetectionTarget::Robot => {
                                robot_current_position = detection.position;
                            }
                            DetectionTarget::Unknown => {
                                println!(
                                    "Unknown target detected at ({}, {})",
                                    detection.position.x, detection.position.y
                                );
                            }
                        }
                    }
                }
                Err(RecvTimeoutError::Timeout) => {}
                Err(RecvTimeoutError::Disconnected) => {
                    anyhow::bail!("camera channel disconnected");
                }
            }
        }

        if let Some(Button::Mouse(MouseButton::Left)) = e.press_args() {
            puck.set_position(Point2::new(cursor_position[0], cursor_position[1]));
        }

        e.mouse_cursor(|pos| {
            cursor_position = pos;
        });

        if !enable_detection {
            puck.set_velocity(
                (Point2::new(cursor_position[0], cursor_position[1]) - puck.position())
                    * SIMULATION_VELOCITY_PER_PIXEL,
            );
        }
        let cursor_point = Point2::new(cursor_position[0], cursor_position[1]);
        let launch_velocity = (cursor_point - puck.position()) * SIMULATION_VELOCITY_PER_PIXEL;
        let predicted_puck_path = predict_puck_path(&puck, launch_velocity, 0.08, 40);

        if puck.x() < 400.0 && puck.velocity().magnitude() < PLAYABLE_PUCK_THRESHOLD {
            // playable puck on our side, move aggressively

            robot_target_position.x = 350.0;
        } else {
            // otherwise, move to block a goal on the defensive line
            robot_target_position.x = 20.0;
            stepper.move_to_position(robot_target_position, 1000)?;
        }

        window.draw_2d(&e, |c, g, _| {
            use graphics::*;

            clear([0.5, 0.5, 0.5, 1.0], g);

            Ellipse::new([1.0, 0.0, 0.0, 1.0]).draw(
                [
                    robot_target_position.x - 10.0,
                    robot_target_position.y - 10.0,
                    20.0,
                    20.0,
                ],
                &c.draw_state,
                c.transform,
                g,
            );

            Ellipse::new([0.0, 1.0, 0.0, 1.0]).draw(
                [
                    robot_current_position.x - 10.0,
                    robot_current_position.y - 10.0,
                    20.0,
                    20.0,
                ],
                &c.draw_state,
                c.transform,
                g,
            );

            Ellipse::new([0.0, 0.0, 1.0, 1.0]).draw(
                [puck.x() - 10.0, puck.y() - 10.0, 20.0, 20.0],
                &c.draw_state,
                c.transform,
                g,
            );

            Rectangle::new([0.0, 0.0, 0.0, 1.0]).draw(
                [0.0, GOAL_Y_MIN, 1.0, GOAL_Y_MAX - GOAL_Y_MIN],
                &c.draw_state,
                c.transform,
                g,
            );

            for segment in predicted_puck_path.windows(2) {
                let start = segment[0];
                let end = segment[1];
                Line::new([0.8, 0.0, 0.8, 1.0], 2.0).draw(
                    [start.x, start.y, end.x, end.y],
                    &c.draw_state,
                    c.transform,
                    g,
                );
            }
        });
    }

    Ok(())
}
