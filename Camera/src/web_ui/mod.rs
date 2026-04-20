use std::thread;

use anyhow::Context;
use log::info;
use tiny_http::Server;

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
    let bind_addr = format!("0.0.0.0:{port}");
    let server = Server::http(&bind_addr)
        .map_err(|err| anyhow::anyhow!("failed to bind web UI server on {bind_addr}: {err}"))?;

    thread::Builder::new()
        .name("web-ui-server".to_string())
        .spawn(move || {
            info!("Web UI available at http://127.0.0.1:{port}");
            let deps = WebUiDependencies {
                shared,
                previews,
                playback,
            };
            serve_requests(server, deps);
        })
        .context("failed to spawn web UI server thread")?;

    Ok(())
}
