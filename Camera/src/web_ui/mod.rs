use std::path::PathBuf;
use std::thread;

use anyhow::Context;
use log::{error, info};
use tokio::runtime::Builder;
use web_ui::{WebUI, WebUIConfig};

mod http;
mod render;
mod state;

pub use state::{
    PlaybackControlSnapshot, SharedPlaybackControl, SharedPreviewFrames, SharedRuntimeSettings,
};

use http::{WebUiDependencies, serve_requests};

pub fn spawn_web_ui_server(
    shared: SharedRuntimeSettings,
    previews: SharedPreviewFrames,
    playback: SharedPlaybackControl,
    port: u16,
) -> anyhow::Result<()> {
    let static_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("src/web_ui_static");
    let static_dir_str = static_dir.to_string_lossy().to_string();

    thread::Builder::new()
        .name("web-ui-server".to_string())
        .spawn(move || {
            let deps = WebUiDependencies {
                shared,
                previews,
                playback,
            };

            let runtime = match Builder::new_current_thread().enable_all().build() {
                Ok(runtime) => runtime,
                Err(err) => {
                    error!("failed to create web UI runtime: {err}");
                    return;
                }
            };

            runtime.block_on(async move {
                let config = WebUIConfig::default()
                    .with_host([0, 0, 0, 0])
                    .with_port(port)
                    .with_title("RockeyHockey Detector Controls".to_string())
                    .with_static_dir(static_dir_str);

                let web_ui = WebUI::new(config);
                serve_requests(&web_ui, deps).await;

                info!("Web UI available at http://127.0.0.1:{port}");
                if let Err(err) = web_ui.run().await {
                    error!("web UI server stopped with an error: {err}");
                }
            });
        })
        .context("failed to spawn web UI server thread")?;

    Ok(())
}
