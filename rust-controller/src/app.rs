use std::sync::mpsc::{Receiver, RecvTimeoutError};
use std::time::{Duration, Instant};

use anyhow::Result;

use crate::config::{
    AGGRESSIVE_COMMAND_MIN_INTERVAL, AGGRESSIVE_MOVE_DEADBAND_MM, BACKPRESSURE_COMMAND_INTERVAL,
    CAMERA_STALE_TIMEOUT, COMMAND_QUEUE_BACKPRESSURE_DEPTH, COMMAND_TTL, METRICS_PRINT_INTERVAL,
    ROBOT_MOVE_DEADBAND_MM, ROBOT_MOVE_FEEDRATE, ROBOT_TARGET_SMOOTHING_ALPHA,
};
use crate::stepper::{Stepper, StepperHandle, StepperMoveCommand, spawn_stepper_worker};
use crate::strategy::RobotController;
use crate::types::{DetectionSnapshot, MoveTarget, MoveType, Point};

pub struct Runtime {
    rx: Receiver<DetectionSnapshot>,
    controller: RobotController,
    stepper: StepperHandle,
    bot_active: bool,
    smoothed_target: Option<Point>,
    last_enqueued_target: Option<Point>,
    last_command_ts: Option<Instant>,
    last_camera_ts: Option<Instant>,
    metrics: RuntimeMetrics,
}

struct RuntimeMetrics {
    frames_processed: u64,
    commands_sent: u64,
    dropped_frames: u64,
    max_frame_age: Duration,
    max_process_time: Duration,
    last_print: Instant,
}

impl RuntimeMetrics {
    fn new(now: Instant) -> Self {
        Self {
            frames_processed: 0,
            commands_sent: 0,
            dropped_frames: 0,
            max_frame_age: Duration::ZERO,
            max_process_time: Duration::ZERO,
            last_print: now,
        }
    }

    fn record_frame(&mut self, frame_age: Duration, process_time: Duration, dropped_frames: u64) {
        self.frames_processed += 1;
        self.dropped_frames += dropped_frames;
        self.max_frame_age = self.max_frame_age.max(frame_age);
        self.max_process_time = self.max_process_time.max(process_time);
    }

    fn record_command(&mut self) {
        self.commands_sent += 1;
    }

    fn maybe_print(&mut self, now: Instant) {
        if now.duration_since(self.last_print) < METRICS_PRINT_INTERVAL {
            return;
        }

        println!(
            "metrics frames={} commands={} dropped={} max_frame_age_ms={} max_process_ms={}",
            self.frames_processed,
            self.commands_sent,
            self.dropped_frames,
            self.max_frame_age.as_millis(),
            self.max_process_time.as_millis()
        );

        self.frames_processed = 0;
        self.commands_sent = 0;
        self.dropped_frames = 0;
        self.max_frame_age = Duration::ZERO;
        self.max_process_time = Duration::ZERO;
        self.last_print = now;
    }
}

impl Runtime {
    pub fn new(
        rx: Receiver<DetectionSnapshot>,
        stepper: Box<dyn Stepper>,
        bot_active: bool,
    ) -> Result<Self> {
        let stepper = spawn_stepper_worker(stepper)?;

        Ok(Self {
            rx,
            controller: RobotController::new(Instant::now()),
            stepper,
            bot_active,
            smoothed_target: None,
            last_enqueued_target: None,
            last_command_ts: None,
            last_camera_ts: None,
            metrics: RuntimeMetrics::new(Instant::now()),
        })
    }

    pub fn run(mut self) -> Result<()> {
        loop {
            match self.rx.recv_timeout(Duration::from_millis(10)) {
                Ok(first_snapshot) => {
                    let mut latest = first_snapshot;
                    let mut dropped_frames = 0_u64;
                    self.last_camera_ts = Some(first_snapshot.timestamp);

                    while let Ok(snapshot) = self.rx.try_recv() {
                        latest = snapshot;
                        self.last_camera_ts = Some(snapshot.timestamp);
                        dropped_frames += 1;
                    }

                    if self.camera_is_stale(Instant::now()) {
                        continue;
                    }

                    let frame_age = Instant::now().saturating_duration_since(latest.timestamp);
                    let started = Instant::now();
                    if let Some(target) = self.controller.update(latest, self.bot_active) {
                        if self.maybe_send_move(target)? {
                            self.metrics.record_command();
                        }
                    }
                    let process_time = started.elapsed();
                    self.metrics
                        .record_frame(frame_age, process_time, dropped_frames);
                    self.metrics.maybe_print(Instant::now());
                }
                Err(RecvTimeoutError::Timeout) => {
                    self.metrics.maybe_print(Instant::now());
                }
                Err(RecvTimeoutError::Disconnected) => {
                    anyhow::bail!("camera channel disconnected");
                }
            }
        }
    }

    fn camera_is_stale(&self, now: Instant) -> bool {
        match self.last_camera_ts {
            Some(last) => now.duration_since(last) > CAMERA_STALE_TIMEOUT,
            None => true,
        }
    }

    fn maybe_send_move(&mut self, mut target: MoveTarget) -> Result<bool> {
        let aggressive_move = matches!(
            target.move_type,
            MoveType::FastIntercept | MoveType::SlowIntercept
        );
        let requested = Point {
            x: target.x,
            y: target.y,
        };
        let smoothed = if aggressive_move {
            requested
        } else {
            self.smooth_target(requested)
        };
        target.x = smoothed.x;
        target.y = smoothed.y;

        let queue_depth = self.stepper.queue_depth();
        let min_command_interval = if queue_depth >= COMMAND_QUEUE_BACKPRESSURE_DEPTH {
            BACKPRESSURE_COMMAND_INTERVAL
        } else if aggressive_move {
            AGGRESSIVE_COMMAND_MIN_INTERVAL
        } else {
            COMMAND_TTL
        };

        if let Some(last) = self.last_command_ts {
            if last.elapsed() < min_command_interval {
                return Ok(false);
            }
        }

        if !aggressive_move {
            if let Some(previous) = self.smoothed_target {
                if previous.distance_to(smoothed) < ROBOT_MOVE_DEADBAND_MM {
                    return Ok(false);
                }
            }
        }

        if let Some(previous) = self.last_enqueued_target {
            let enqueue_deadband = if aggressive_move {
                AGGRESSIVE_MOVE_DEADBAND_MM
            } else {
                ROBOT_MOVE_DEADBAND_MM
            };
            if previous.distance_to(smoothed) < enqueue_deadband {
                return Ok(false);
            }
        }

        let enqueued = self.stepper.try_send_move(StepperMoveCommand {
            x: target.x,
            y: target.y,
            feedrate: ROBOT_MOVE_FEEDRATE,
            move_type: target.move_type,
        });
        if !enqueued {
            return Ok(false);
        }

        println!(
            "{:?} -> x={:.1} y={:.1} queue_depth={}",
            target.move_type,
            target.x,
            target.y,
            self.stepper.queue_depth()
        );
        self.last_command_ts = Some(Instant::now());
        self.smoothed_target = Some(smoothed);
        self.last_enqueued_target = Some(smoothed);
        Ok(true)
    }

    fn smooth_target(&self, target: Point) -> Point {
        let Some(prev) = self.smoothed_target else {
            return target;
        };

        Point {
            x: prev.x + ROBOT_TARGET_SMOOTHING_ALPHA * (target.x - prev.x),
            y: prev.y + ROBOT_TARGET_SMOOTHING_ALPHA * (target.y - prev.y),
        }
    }
}
