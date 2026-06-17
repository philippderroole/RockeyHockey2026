use std::io::{ErrorKind, Write};
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::mpsc::{self, SyncSender, TryRecvError, TrySendError};
use std::thread;
use std::time::{Duration, Instant};

use anyhow::{Context, Result};
use serialport::SerialPort;

use crate::config::{COMMAND_QUEUE_CAPACITY, ROBOT_MAX_X, ROBOT_MAX_Y};
use crate::types::MoveType;

pub trait Stepper: Send {
    fn calibrate(&mut self) -> Result<()>;
    fn move_to_position(&mut self, x: f64, y: f64, feedrate: u32) -> Result<()>;
    fn stop(&mut self) -> Result<()>;
}

#[derive(Debug, Clone, Copy)]
pub struct StepperMoveCommand {
    pub x: f64,
    pub y: f64,
    pub feedrate: u32,
    pub move_type: MoveType,
}

#[derive(Debug, Clone, Copy)]
enum StepperCommand {
    Move(StepperMoveCommand),
    Stop,
}

#[derive(Clone)]
pub struct StepperHandle {
    tx: SyncSender<StepperCommand>,
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

    pub fn queue_depth(&self) -> usize {
        self.queue_depth.load(Ordering::Relaxed)
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
                    StepperCommand::Move(command) => {
                        if let Err(err) =
                            stepper.move_to_position(command.x, command.y, command.feedrate)
                        {
                            eprintln!(
                                "stepper worker failed for {:?} -> x={:.1} y={:.1}: {err}",
                                command.move_type, command.x, command.y
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

pub struct DryRunStepper;

impl Stepper for DryRunStepper {
    fn calibrate(&mut self) -> Result<()> {
        println!("[dry-run] calibrate");
        Ok(())
    }

    fn move_to_position(&mut self, x: f64, y: f64, _feedrate: u32) -> Result<()> {
        println!("[dry-run] move to ({x:.1}, {y:.1})");
        Ok(())
    }

    fn stop(&mut self) -> Result<()> {
        println!("[dry-run] stop");
        Ok(())
    }
}

pub struct GrblStepper {
    connection: Box<dyn SerialPort>,
}

impl GrblStepper {
    pub fn connect(port: &str, baudrate: u32) -> Result<Self> {
        let mut connection = serialport::new(port, baudrate)
            .timeout(Duration::from_millis(1000))
            .open()
            .with_context(|| format!("open serial port {port} @ {baudrate}"))?;

        connection.write_all(b"\r\n\r\n").context("wake up GRBL")?;
        thread::sleep(Duration::from_millis(2000));

        let mut stepper = Self { connection };
        let _ = stepper.send_command("$X")?;
        Ok(stepper)
    }

    fn send_command(&mut self, command: &str) -> Result<String> {
        let payload = format!("{command}\n");
        self.connection
            .write_all(payload.as_bytes())
            .with_context(|| format!("write command: {command}"))?;

        let start = Instant::now();
        let timeout = Duration::from_millis(2000);
        let mut line_buf = Vec::<u8>::with_capacity(128);

        while start.elapsed() < timeout {
            line_buf.clear();
            if read_line(&mut *self.connection, &mut line_buf)? {
                let response = trim_ascii_whitespace(&line_buf);
                if response == b"ok" || response.starts_with(b"error") {
                    return Ok(String::from_utf8_lossy(response).to_string());
                }
            } else {
                thread::sleep(Duration::from_millis(2));
            }
        }

        Ok("TIMEOUT".to_string())
    }

    fn wait_for_idle(&mut self, timeout: Duration, recover_alarm: bool) -> Result<()> {
        let start = Instant::now();
        let mut line_buf = Vec::<u8>::with_capacity(128);

        while start.elapsed() < timeout {
            self.connection
                .write_all(b"?")
                .context("query GRBL status")?;

            line_buf.clear();
            if read_line(&mut *self.connection, &mut line_buf)? {
                let response = trim_ascii_whitespace(&line_buf);
                if response.starts_with(b"<Idle") {
                    return Ok(());
                }
                if response.starts_with(b"<Alarm") {
                    let alarm = String::from_utf8_lossy(response).to_string();
                    if recover_alarm {
                        eprintln!("GRBL alarm during homing, trying unlock: {alarm}");
                        let unlock = self.send_command("$X")?;
                        if unlock.starts_with("error") {
                            anyhow::bail!(
                                "GRBL alarm recovery failed while unlocking after homing: {unlock}"
                            );
                        }
                        thread::sleep(Duration::from_millis(50));
                        continue;
                    }

                    anyhow::bail!("GRBL entered alarm state: {alarm}");
                }
            }

            thread::sleep(Duration::from_millis(10));
        }

        anyhow::bail!("timeout waiting for GRBL idle state");
    }
}

impl Stepper for GrblStepper {
    fn calibrate(&mut self) -> Result<()> {
        let response = self.send_command("$H")?;
        if response.starts_with("error") {
            anyhow::bail!("GRBL homing error: {response}");
        }
        self.wait_for_idle(Duration::from_secs(20), true)?;

        let unlock = self.send_command("$X")?;
        if unlock.starts_with("error") {
            anyhow::bail!("GRBL unlock error after homing: {unlock}");
        }
        Ok(())
    }

    fn move_to_position(&mut self, x: f64, y: f64, feedrate: u32) -> Result<()> {
        let x = x.clamp(0.0, ROBOT_MAX_X);
        let y = y.clamp(0.0, ROBOT_MAX_Y);
        let cmd = format!("$J=G21G90X{:.2}Y{:.2}F{}", x, y, feedrate.max(1));
        let response = self.send_command(&cmd)?;
        if response.starts_with("error") {
            anyhow::bail!("GRBL error on move command: {response}");
        }
        Ok(())
    }

    fn stop(&mut self) -> Result<()> {
        self.connection
            .write_all(&[0x85])
            .context("send GRBL jog cancel")?;
        Ok(())
    }
}

fn trim_ascii_whitespace(bytes: &[u8]) -> &[u8] {
    let mut start = 0;
    let mut end = bytes.len();

    while start < end && bytes[start].is_ascii_whitespace() {
        start += 1;
    }

    while end > start && bytes[end - 1].is_ascii_whitespace() {
        end -= 1;
    }

    &bytes[start..end]
}

fn read_line(port: &mut dyn SerialPort, out: &mut Vec<u8>) -> Result<bool> {
    let mut byte = [0_u8; 1];
    loop {
        match port.read(&mut byte) {
            Ok(0) => return Ok(false),
            Ok(1) => {
                out.push(byte[0]);
                if byte[0] == b'\n' {
                    return Ok(true);
                }
            }
            Ok(_) => {}
            Err(err) if err.kind() == ErrorKind::TimedOut => return Ok(false),
            Err(err) => return Err(err).context("read serial response"),
        }
    }
}
