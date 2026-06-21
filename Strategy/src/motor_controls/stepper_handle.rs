use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::mpsc::{self, SyncSender, TryRecvError, TrySendError};
use std::thread;

use anyhow::{Context, Result};

use crate::commands::Command;
use crate::config::COMMAND_QUEUE_CAPACITY;
use crate::motor_controls::Stepper;

#[derive(Clone)]
pub struct StepperHandle {
    pub tx: SyncSender<Command>,
    queue_depth: Arc<AtomicUsize>,
}

impl StepperHandle {
    pub fn try_send_move(&self, command: Command) -> bool {
        self.queue_depth.fetch_add(1, Ordering::Relaxed);
        match self.tx.try_send(command) {
            Ok(()) => true,
            Err(TrySendError::Full(_)) => {
                decrement_queue_depth(&self.queue_depth);
                false
            }
            Err(TrySendError::Disconnected(_)) => {
                decrement_queue_depth(&self.queue_depth);
                false
            }
        }
    }

    pub fn execute(&self, command: Command) {
        if !self.try_send_move(command) {
            eprintln!("failed to send stepper command: queue is full or worker thread has stopped");
        }
    }

    pub fn calibrate(&mut self) -> Result<()> {
        let (response_tx, response_rx) = mpsc::channel();
        self.tx
            .send(Command::Calibrate(response_tx))
            .context("enqueue calibrate command")?;

        response_rx.recv().context("wait for calibrate command")?
    }
}

pub fn spawn_stepper_worker(mut stepper: Box<dyn Stepper>) -> Result<StepperHandle> {
    let (tx, rx) = mpsc::sync_channel::<Command>(COMMAND_QUEUE_CAPACITY);
    let queue_depth = Arc::new(AtomicUsize::new(0));
    let worker_depth = Arc::clone(&queue_depth);

    thread::Builder::new()
        .name("stepper-worker".into())
        .spawn(move || {
            while let Ok(mut command) = rx.recv() {
                decrement_queue_depth(&worker_depth);

                loop {
                    match rx.try_recv() {
                        Ok(next) => {
                            decrement_queue_depth(&worker_depth);
                            command = next;
                        }
                        Err(TryRecvError::Empty) => break,
                        Err(TryRecvError::Disconnected) => break,
                    }
                }

                match command {
                    Command::Calibrate(response_tx) => {
                        let result = stepper.calibrate();
                        if let Err(err) = response_tx.send(result) {
                            eprintln!("stepper worker failed to report calibration result: {err}");
                        }
                    }
                    Command::MoveTo(position) => {
                        if let Err(err) = stepper.move_to_position(position, 1000) {
                            eprintln!(
                                "stepper worker failed for -> x={:.1} y={:.1}: {err}",
                                position.x, position.y
                            );
                        }
                    }
                    Command::Shoot { staging, target } => {
                        if let Err(err) = stepper.move_to_position(staging, 1000) {
                            eprintln!(
                                "stepper worker failed for staging position -> x={:.1} y={:.1}: {err}",
                                staging.x, staging.y
                            );
                        }
                        if let Err(err) = stepper.move_to_position(target, 1500) {
                            eprintln!(
                                "stepper worker failed for target position -> x={:.1} y={:.1}: {err}",
                                target.x, target.y
                            );
                        }
                    }
                    Command::Defend(position) => {
                        if let Err(err) = stepper.move_to_position(position, 1000) {
                            eprintln!(
                                "stepper worker failed for -> x={:.1} y={:.1}: {err}",
                                position.x, position.y
                            );
                        }
                    }
                }
            }
        })
        .context("spawn stepper worker thread")?;

    Ok(StepperHandle { tx, queue_depth })
}

fn decrement_queue_depth(depth: &AtomicUsize) {
    let mut current = depth.load(Ordering::Relaxed);
    while current > 0 {
        match depth.compare_exchange_weak(
            current,
            current - 1,
            Ordering::Relaxed,
            Ordering::Relaxed,
        ) {
            Ok(_) => return,
            Err(next) => current = next,
        }
    }
}
