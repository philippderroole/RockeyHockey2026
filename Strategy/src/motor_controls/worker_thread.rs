use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::mpsc::{self, SyncSender, TryRecvError, TrySendError};
use std::thread;

use anyhow::{Context, Result};
use nalgebra::Point2;

use crate::config::COMMAND_QUEUE_CAPACITY;
use crate::motor_controls::{Stepper, StepperCommand, StepperMoveCommand};

#[derive(Clone)]
pub struct StepperHandle {
    pub(crate) tx: SyncSender<StepperCommand>,
    queue_depth: Arc<AtomicUsize>,
}

impl StepperHandle {
    pub fn try_send_move(&self, command: StepperMoveCommand) -> bool {
        self.queue_depth.fetch_add(1, Ordering::Relaxed);
        match self.tx.try_send(StepperCommand::Move(command)) {
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

    pub fn try_send_stop(&self) -> bool {
        self.queue_depth.fetch_add(1, Ordering::Relaxed);
        match self.tx.try_send(StepperCommand::Stop) {
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
}

impl Stepper for StepperHandle {
    fn calibrate(&mut self) -> Result<()> {
        let (response_tx, response_rx) = mpsc::channel();
        self.tx
            .send(StepperCommand::Calibrate(response_tx))
            .context("enqueue calibrate command")?;

        response_rx.recv().context("wait for calibrate command")?
    }

    fn move_to_position(&mut self, position: Point2<f64>, feedrate: u32) -> Result<()> {
        if self.try_send_move(StepperMoveCommand { position, feedrate }) {
            Ok(())
        } else {
            anyhow::bail!("stepper command queue full or disconnected")
        }
    }

    fn stop(&mut self) -> Result<()> {
        if self.try_send_stop() {
            Ok(())
        } else {
            anyhow::bail!("stepper command queue full or disconnected")
        }
    }
}

pub fn spawn_stepper_worker(mut stepper: Box<dyn Stepper>) -> Result<StepperHandle> {
    let (tx, rx) = mpsc::sync_channel::<StepperCommand>(COMMAND_QUEUE_CAPACITY);
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
                    StepperCommand::Calibrate(response_tx) => {
                        let result = stepper.calibrate();
                        if let Err(err) = response_tx.send(result) {
                            eprintln!("stepper worker failed to report calibration result: {err}");
                        }
                    }
                    StepperCommand::Move(command) => {
                        if let Err(err) =
                            stepper.move_to_position(command.position, command.feedrate)
                        {
                            eprintln!(
                                "stepper worker failed for -> x={:.1} y={:.1}: {err}",
                                command.position.x, command.position.y
                            );
                        }
                    }
                    StepperCommand::Stop => {
                        if let Err(err) = stepper.stop() {
                            eprintln!("stepper worker failed to stop motion: {err}");
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
