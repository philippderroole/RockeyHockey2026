use std::io::{ErrorKind, Write};
use std::thread;
use std::time::{Duration, Instant};

use anyhow::{Context, Result};
use nalgebra::Point2;
use serialport::SerialPort;

use crate::config::{ROBOT_MAX_X, ROBOT_MAX_Y};
use crate::motor_controls::Stepper;

pub struct DryRunStepper {
    target_position: Point2<f64>,
}

impl DryRunStepper {
    pub fn new() -> Self {
        Self {
            target_position: Point2::new(0.0, 0.0),
        }
    }
}

impl Stepper for DryRunStepper {
    fn calibrate(&mut self) -> Result<()> {
        println!("[dry-run] calibrate");
        Ok(())
    }

    fn move_to_position(&mut self, position: Point2<f64>, _feedrate: u32) -> Result<()> {
        let x = position.x;
        let y = position.y;

        if (self.target_position.x - x).abs() < 1e-6 && (self.target_position.y - y).abs() < 1e-6 {
            return Ok(());
        }

        println!("[dry-run] move to ({x:.1}, {y:.1})");
        self.target_position = position;
        Ok(())
    }

    fn stop(&mut self) -> Result<()> {
        println!("[dry-run] stop");
        Ok(())
    }
}

pub struct GrblStepper {
    connection: Box<dyn SerialPort>,
    target_position: Point2<f64>,
}

impl GrblStepper {
    pub fn connect(port: &str, baudrate: u32) -> Result<Self> {
        let mut connection = serialport::new(port, baudrate)
            .timeout(Duration::from_millis(1000))
            .open()
            .with_context(|| format!("open serial port {port} @ {baudrate}"))?;

        connection.write_all(b"\r\n\r\n").context("wake up GRBL")?;
        thread::sleep(Duration::from_millis(2000));

        let mut stepper = Self {
            connection,
            target_position: Point2::new(0.0, 0.0),
        };
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

    fn move_to_position(&mut self, position: Point2<f64>, feedrate: u32) -> Result<()> {
        let x = position.x.clamp(0.0, ROBOT_MAX_X);
        let y = position.y.clamp(0.0, ROBOT_MAX_Y);

        if (self.target_position.x - x).abs() < 1e-6 && (self.target_position.y - y).abs() < 1e-6 {
            return Ok(());
        }

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
