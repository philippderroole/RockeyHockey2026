extern crate piston_window;

use std::sync::mpsc::{Receiver, TryRecvError};

use crate::{
    camera::{Detection, DetectionTarget, spawn_camera_listener},
    config::{
        BOARD_HEIGHT, BOARD_WIDTH, DEFAULT_CAMERA_HOST, DEFAULT_CAMERA_PORT,
        DEFAULT_STEPPER_BAUDRATE, DEFAULT_STEPPER_PORT, GOAL_Y_MAX, GOAL_Y_MIN, PUCK_RADIUS,
        SIMULATOR_BORDER, WINDOW_HEIGHT, WINDOW_WIDTH,
    },
    motor_controls::{DryRunStepper, GrblStepper, Stepper, spawn_stepper_worker},
    puck::Puck,
};
use clap::Parser;
use nalgebra::Point2;
use piston_window::{texture::TextureSettings, *};

mod camera;
mod config;
mod motor_controls;
mod puck;
mod simulation;
mod strategy;

const VELOCITY_DRAW_SCALE: f64 = 6.0;

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

    let rx = spawn_camera_listener(&cli.camera_host, cli.camera_port)?;
    let mut board = Board::new(rx, stepper)?;
    board.run()?;

    Ok(())
}

struct Board {
    robot_current_position: Point2<f64>,
    robot_target_position: Point2<f64>,
    puck: Puck,
    predicted_puck_path: Vec<Point2<f64>>,
    rx: Receiver<Vec<Detection>>,
    cursor_position: Point2<f64>,
    velocity_drag_start: Option<Point2<f64>>,
    stepper: Box<dyn Stepper>,
}

impl Board {
    pub fn new(
        rx: Receiver<Vec<Detection>>,
        stepper: Box<dyn Stepper + 'static>,
    ) -> anyhow::Result<Self> {
        Ok(Board {
            robot_current_position: Point2::new(100.0, 200.0),
            robot_target_position: Point2::new(100.0, 200.0),
            puck: Puck::new(),
            predicted_puck_path: Vec::new(),
            rx,
            cursor_position: Point2::new(0.0, 0.0),
            velocity_drag_start: None,
            stepper,
        })
    }

    pub fn run(&mut self) -> anyhow::Result<()> {
        let mut window: PistonWindow =
            WindowSettings::new("Rockey Hockey 2026", [WINDOW_HEIGHT, WINDOW_WIDTH])
                .exit_on_esc(true)
                .build()
                .map_err(|e| anyhow::anyhow!("failed to create window: {e}"))?;

        let mut glyphs = Glyphs::new(
            "./assets/FiraSans-Regular.ttf",
            window.create_texture_context(),
            TextureSettings::new(),
        )?;

        let mut events = Events::new(EventSettings::new().lazy(true).ups(60).max_fps(60));
        while let Some(e) = events.next(&mut window) {
            self.update(&e)?;
            self.draw(&e, &mut window, &mut glyphs)?;
        }

        Ok(())
    }

    pub fn update(&mut self, e: &Event) -> anyhow::Result<()> {
        match self.rx.try_recv() {
            Ok(detections) => {
                for detection in detections {
                    match detection.target {
                        DetectionTarget::Puck => {
                            self.puck.update(detection.position, detection.timestamp);
                        }
                        DetectionTarget::Robot => {
                            self.robot_current_position = detection.position;
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
            Err(TryRecvError::Empty) => {}
            Err(TryRecvError::Disconnected) => {
                anyhow::bail!("camera channel disconnected");
            }
        }

        e.mouse_cursor(|pos| {
            self.cursor_position = Point2::new(pos[0], pos[1]);
        });

        if let Some(Button::Mouse(MouseButton::Left)) = e.press_args() {
            self.puck.set_position(Point2::new(
                self.cursor_position[0] - SIMULATOR_BORDER,
                self.cursor_position[1] - SIMULATOR_BORDER,
            ));
        }

        if let Some(Button::Mouse(MouseButton::Right)) = e.press_args() {
            self.velocity_drag_start = Some(self.cursor_position);
        }

        if let Some(Button::Mouse(MouseButton::Right)) = e.release_args()
            && let Some(start_position) = self.velocity_drag_start.take()
        {
            let velocity = (self.cursor_position - start_position) * VELOCITY_DRAW_SCALE;
            if velocity.magnitude() > f64::EPSILON {
                self.puck.set_velocity(velocity);
            }
        }

        let (next_move, predicted_puck_path) =
            strategy::get_next_move(self.robot_current_position, &self.puck);
        self.predicted_puck_path = predicted_puck_path;

        if let Some(next_move) = next_move {
            Self::execute_move(
                &mut self.stepper,
                &mut self.robot_target_position,
                next_move,
            )?;
        }

        Ok(())
    }

    pub fn draw(
        &mut self,
        e: &Event,
        window: &mut PistonWindow,
        glyphs: &mut Glyphs,
    ) -> anyhow::Result<()> {
        window.draw_2d(e, |c, g, _| {
            use graphics::*;

            clear([0.5, 0.5, 0.5, 1.0], g);

            // Border
            Rectangle::new([0.0, 0.0, 0.0, 1.0]).draw(
                [
                    0.0,
                    0.0,
                    BOARD_HEIGHT + SIMULATOR_BORDER * 2.0,
                    BOARD_WIDTH + SIMULATOR_BORDER * 2.0,
                ],
                &c.draw_state,
                c.transform,
                g,
            );

            // Playable board
            Rectangle::new([0.8, 0.8, 0.8, 1.0]).draw(
                [0.0, 0.0, BOARD_HEIGHT, BOARD_WIDTH],
                &c.draw_state,
                c.transform.trans(SIMULATOR_BORDER, SIMULATOR_BORDER),
                g,
            );

            // Goal
            Rectangle::new([1.0, 0.0, 0.0, 1.0]).draw(
                [0.0, GOAL_Y_MIN, SIMULATOR_BORDER, GOAL_Y_MAX - GOAL_Y_MIN],
                &c.draw_state,
                c.transform,
                g,
            );

            Ellipse::new([1.0, 0.0, 0.0, 1.0]).draw(
                [
                    self.robot_target_position.x - 20.0,
                    self.robot_target_position.y - 20.0,
                    40.0,
                    40.0,
                ],
                &c.draw_state,
                c.transform.trans(SIMULATOR_BORDER, SIMULATOR_BORDER),
                g,
            );

            Ellipse::new([0.0, 1.0, 0.0, 1.0]).draw(
                [
                    self.robot_current_position.x - 20.0,
                    self.robot_current_position.y - 20.0,
                    40.0,
                    40.0,
                ],
                &c.draw_state,
                c.transform.trans(SIMULATOR_BORDER, SIMULATOR_BORDER),
                g,
            );

            Ellipse::new([0.0, 0.0, 1.0, 1.0]).draw(
                [
                    self.puck.x() - PUCK_RADIUS,
                    self.puck.y() - PUCK_RADIUS,
                    PUCK_RADIUS * 2.0,
                    PUCK_RADIUS * 2.0,
                ],
                &c.draw_state,
                c.transform.trans(SIMULATOR_BORDER, SIMULATOR_BORDER),
                g,
            );

            // Attack line
            Line::new([0.0, 0.0, 0.0, 1.0], 2.0).draw(
                [300.0, 0.0, 300.0, BOARD_WIDTH],
                &c.draw_state,
                c.transform.trans(SIMULATOR_BORDER, SIMULATOR_BORDER),
                g,
            );

            if let Some(start_position) = self.velocity_drag_start {
                Line::new([0.2, 0.2, 0.9, 1.0], 2.0).draw(
                    [
                        start_position.x,
                        start_position.y,
                        self.cursor_position.x,
                        self.cursor_position.y,
                    ],
                    &c.draw_state,
                    c.transform,
                    g,
                );
            }

            for segment in self.predicted_puck_path.windows(2) {
                let start = segment[0];
                let end = segment[1];
                Line::new([0.8, 0.0, 0.8, 1.0], 2.0).draw(
                    [start.x, start.y, end.x, end.y],
                    &c.draw_state,
                    c.transform.trans(SIMULATOR_BORDER, SIMULATOR_BORDER),
                    g,
                );
            }

            Text::new_color([1.0, 1.0, 0.0, 1.0], 32)
                .draw(
                    format!(
                        "Robot target: ({:.1}, {:.1})",
                        self.robot_target_position.x, self.robot_target_position.y
                    )
                    .as_str(),
                    glyphs,
                    &c.draw_state,
                    c.transform
                        .trans(20.0, BOARD_WIDTH + SIMULATOR_BORDER + 40.0),
                    g,
                )
                .unwrap();
        });

        Ok(())
    }

    fn execute_move(
        stepper: &mut Box<dyn Stepper + 'static>,
        robot_target_position: &mut Point2<f64>,
        target: Point2<f64>,
    ) -> Result<(), anyhow::Error> {
        *robot_target_position = target;

        let motor_target = Point2::new(
            (target.x - 2.0) * 138.0 / 106.0,
            (target.y - 2.0) * 330.0 / 306.0,
        );

        stepper.move_to_position(motor_target, 30000)
    }
}
