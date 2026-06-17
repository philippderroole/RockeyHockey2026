# Rust Controller (Headless)

This is a fast, UI-free reimplementation of the Python robot controller.

## What is included

- UDP camera subscriber (compatible with detector payload containing `detections` with `target_name`, `x`, `y`)
- Coordinate mapping from camera space to table space
- Strategy state machine (`DEFENDING` / `PLAYING_BACK`) with line-based bounce prediction
- GRBL jog output over serial
- Automatic GRBL homing calibration on startup
- Smoothing, deadband, command TTL, and stale-camera guardrails

## What is intentionally removed

- PyQt UI
- Simulator UI code
- Web UI / browser UI dependencies
- Python threading + QThread move queue implementation

## Build

```bash
cd rust-controller
cargo build --release
```

## Run (hardware)

```bash
cargo run --release -- \
  --camera-host 192.168.2.2 \
  --camera-port 5005 \
  --stepper-port /dev/cu.usbmodem11301 \
  --stepper-baudrate 115200
```

## Run (dry run, no motor output)

```bash
cargo run --release -- --dry-run
```

## CLI

```bash
cargo run -- --help
```
