# Rocky-Hockey

## Rust Headless Rewrite

The UI-free Rust controller is available in [rust-controller](rust-controller).

- Entry point: [rust-controller/src/main.rs](rust-controller/src/main.rs)
- Runtime loop: [rust-controller/src/app.rs](rust-controller/src/app.rs)
- Strategy: [rust-controller/src/strategy.rs](rust-controller/src/strategy.rs)
- Camera UDP input: [rust-controller/src/camera.rs](rust-controller/src/camera.rs)
- GRBL stepper output: [rust-controller/src/stepper.rs](rust-controller/src/stepper.rs)

Use [rust-controller/README.md](rust-controller/README.md) for build and run instructions.

## Setup Python venv for VSCode

The file `.vscode/tasks.json` defines a task to set up a python virtual environment (`venv`) in Visual Studio Code. The task can be run by clicking *"Terminal"* -> *"Run Task"* -> *"Build Python Env"*.

- Source for Hockey Image: https://www.svgrepo.com/svg/92168/air-hockey