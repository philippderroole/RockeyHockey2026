pub mod input_modes;
pub mod runner;
pub mod target_output;

use rockey_hockey::puck_detector::RuntimeDetectorSettings;

use crate::app::input_modes::InputSource;
use crate::app::target_output::TargetOutputSender;

use self::runner::{DetectorRunner, PlainDetectorRunner, WebUiDetectorRunner};

pub struct RunConfig {
    pub input_source: InputSource,
    pub web_ui_enabled: bool,
    pub web_ui_port: u16,
    pub target_output: Option<std::net::SocketAddr>,
}

pub fn run(config: RunConfig) -> anyhow::Result<()> {
    let runtime_settings = RuntimeDetectorSettings::default();
    let target_output = match config.target_output {
        Some(target_output) => Some(TargetOutputSender::new(target_output)?),
        None => None,
    };

    let mut runner = create_runner(
        config.web_ui_enabled,
        config.web_ui_port,
        runtime_settings,
        target_output,
    )?;
    input_modes::run_capture_loop(&mut *runner, config.input_source)
}

fn create_runner(
    web_ui_enabled: bool,
    web_ui_port: u16,
    runtime_settings: RuntimeDetectorSettings,
    target_output: Option<TargetOutputSender>,
) -> anyhow::Result<Box<dyn DetectorRunner>> {
    match web_ui_enabled {
        true => Ok(Box::new(WebUiDetectorRunner::with_web_ui(
            web_ui_port,
            runtime_settings,
            target_output,
        )?)),
        false => Ok(Box::new(PlainDetectorRunner::new(
            runtime_settings,
            target_output,
        ))),
    }
}
