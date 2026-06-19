extern crate piston_window;

use std::sync::mpsc::TryRecvError;

use crate::{
    camera::{DetectionTarget, spawn_camera_listener},
    config::{
        BOARD_HEIGHT, BOARD_WIDTH, DEFAULT_CAMERA_HOST, DEFAULT_CAMERA_PORT,
        DEFAULT_STEPPER_BAUDRATE, DEFAULT_STEPPER_PORT, GOAL_Y_MAX, GOAL_Y_MIN,
        PLAYABLE_PUCK_THRESHOLD, PUCK_RADIUS,
    },
    motor_controls::{DryRunStepper, GrblStepper, Stepper, spawn_stepper_worker},
    puck::Puck,
    simulation::predict_puck_path,
};
use clap::Parser;
use nalgebra::Point2;
use piston_window::{
    Button, EventLoop, EventSettings, Events, MouseButton, MouseCursorEvent, PistonWindow,
    PressEvent, WindowSettings, graphics,
};

mod camera;
mod config;
mod motor_controls;
mod puck;
mod simulation;

const SIMULATOR_BORDER: f64 = 10.0;
const ROBOT_TARGET_OFFSET: f64 = 7.5;

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

    let enable_detection = true;
    let rx = spawn_camera_listener(&cli.camera_host, cli.camera_port)?;

    let mut window: PistonWindow = WindowSettings::new("shapes", [BOARD_HEIGHT, BOARD_WIDTH])
        .exit_on_esc(true)
        .build()
        .map_err(|e| anyhow::anyhow!("failed to create window: {e}"))?;

    let mut robot_target_position: Point2<f64> = Point2::new(100.0, 200.0);
    let mut robot_current_position = Point2::new(100.0, 200.0);

    let mut puck = Puck::new();
    let mut events = Events::new(EventSettings::new().lazy(true).ups(60).max_fps(60));

    let mut cursor_position = [0.0, 0.0];

    while let Some(e) = events.next(&mut window) {
        if enable_detection {
            loop {
                match rx.try_recv() {
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
                    Err(TryRecvError::Empty) => break,
                    Err(TryRecvError::Disconnected) => {
                        anyhow::bail!("camera channel disconnected");
                    }
                }
            }
        }

        if let Some(Button::Mouse(MouseButton::Left)) = e.press_args() {
            puck.set_position(Point2::new(
                cursor_position[0] - SIMULATOR_BORDER - PUCK_RADIUS,
                cursor_position[1] - SIMULATOR_BORDER - PUCK_RADIUS,
            ));
        }

        e.mouse_cursor(|pos| {
            cursor_position = pos;
        });

        let predicted_puck_path = predict_puck_path(&puck);

        /*
        println!("Board coordinates:");
        println!("  Puck: ({:.1}, {:.1})", puck.x(), puck.y());
        println!(
            "  Robot: ({:.1}, {:.1})",
            robot_current_position.x, robot_current_position.y
        );

        println!("Motor coordinates:");
        let motor_robot_position =
            map_board_coordinates_to_motor_coordinates(&robot_current_position);
        println!(
            "  Robot: ({:.1}, {:.1})",
            motor_robot_position.x, motor_robot_position.y
        );
         */

        let new_target = if let Some(goal_block_target) = goal_block_target(&predicted_puck_path) {
            Some(goal_block_target)
        } else if puck.x() < 300.0 && puck.velocity().magnitude() < PLAYABLE_PUCK_THRESHOLD {
            // playable puck on our side, move aggressively
            Some(Point2::new(
                puck.x() - ROBOT_TARGET_OFFSET,
                puck.y() - ROBOT_TARGET_OFFSET,
            ))
        } else {
            None
        };

        if let Some(new_target) = new_target {
            robot_target_position = new_target;
            stepper.move_to_position(
                map_board_coordinates_to_motor_coordinates(&robot_target_position),
                30000,
            )?;
        }

        window.draw_2d(&e, |c, g, _| {
            use graphics::*;

            clear([0.5, 0.5, 0.5, 1.0], g);

            Ellipse::new([1.0, 0.0, 0.0, 1.0]).draw(
                [
                    robot_target_position.x + SIMULATOR_BORDER,
                    robot_target_position.y + SIMULATOR_BORDER,
                    40.0,
                    40.0,
                ],
                &c.draw_state,
                c.transform,
                g,
            );

            Ellipse::new([0.0, 1.0, 0.0, 1.0]).draw(
                [
                    robot_current_position.x + SIMULATOR_BORDER,
                    robot_current_position.y + SIMULATOR_BORDER,
                    40.0,
                    40.0,
                ],
                &c.draw_state,
                c.transform,
                g,
            );

            Ellipse::new([0.0, 0.0, 1.0, 1.0]).draw(
                [
                    puck.x() + SIMULATOR_BORDER - PUCK_RADIUS,
                    puck.y() + SIMULATOR_BORDER - PUCK_RADIUS,
                    PUCK_RADIUS * 2.0,
                    PUCK_RADIUS * 2.0,
                ],
                &c.draw_state,
                c.transform,
                g,
            );

            Rectangle::new([0.0, 0.0, 0.0, 1.0]).draw(
                [
                    0.0 + SIMULATOR_BORDER,
                    GOAL_Y_MIN + SIMULATOR_BORDER,
                    1.0 - 2.0 * SIMULATOR_BORDER,
                    GOAL_Y_MAX - GOAL_Y_MIN,
                ],
                &c.draw_state,
                c.transform,
                g,
            );

            Line::new([0.0, 0.0, 0.0, 1.0], 2.0).draw(
                [
                    300.0 + SIMULATOR_BORDER,
                    0.0,
                    300.0 + SIMULATOR_BORDER,
                    BOARD_HEIGHT,
                ],
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

fn map_board_coordinates_to_motor_coordinates(board_position: &Point2<f64>) -> Point2<f64> {
    Point2::new(
        (board_position.x - 2.0) * 138.0 / 106.0,
        (board_position.y - 2.0) * 330.0 / 306.0,
    )
}

fn goal_block_target(predicted_puck_path: &[Point2<f64>]) -> Option<Point2<f64>> {
    predicted_puck_path
        .iter()
        .find(|point| point.x <= PUCK_RADIUS && point.y >= GOAL_Y_MIN && point.y <= GOAL_Y_MAX)
        .map(|point| Point2::new(10.0, point.y - ROBOT_TARGET_OFFSET))
}
