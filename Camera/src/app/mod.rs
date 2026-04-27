pub mod input_modes;
pub mod runner;

use rockey_hockey::puck_detector::RuntimeDetectorSettings;

use crate::app::input_modes::InputSource;

use self::runner::{DetectorRunner, PlainDetectorRunner, WebUiDetectorRunner};

pub struct RunConfig {
    pub input_source: InputSource,
    pub web_ui_enabled: bool,
    pub web_ui_port: u16,
}

pub fn run(config: RunConfig) -> anyhow::Result<()> {
    let runtime_settings = RuntimeDetectorSettings::default();

    let mut runner = create_runner(config.web_ui_enabled, config.web_ui_port, runtime_settings)?;
    input_modes::run_capture_loop(&mut *runner, config.input_source)
}

fn create_runner(
    web_ui_enabled: bool,
    web_ui_port: u16,
    runtime_settings: RuntimeDetectorSettings,
) -> anyhow::Result<Box<dyn DetectorRunner>> {
    match web_ui_enabled {
        true => Ok(Box::new(WebUiDetectorRunner::with_web_ui(
            web_ui_port,
            runtime_settings,
        )?)),
        false => Ok(Box::new(PlainDetectorRunner::new(runtime_settings))),
    }
}
