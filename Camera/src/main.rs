use clap::Parser;
use rockey_hockey::pi_camera;

mod app;

#[derive(Parser, Debug)]
#[command(name = "RockeyHockey")]
#[command(about = "Puck detection system for hockey", long_about = None)]
struct Args {
    /// Optional path to a recorded video file instead of webcam input
    #[arg(long)]
    video: Option<String>,
    /// Optional flag to use the Raspberry Pi camera instead of a webcam
    #[arg(long)]
    pi_camera: bool,
    /// Enable browser-based live settings editor at http://127.0.0.1:<web_ui_port>
    #[arg(long)]
    web_ui: bool,
    /// Port for browser-based live settings editor
    #[arg(long, default_value_t = 8080)]
    web_ui_port: u16,
}

fn main() -> opencv::Result<()> {
    env_logger::init();

    let args = Args::parse();
    app::run(app::RunConfig {
        video_path: args.video,
        web_ui_enabled: args.web_ui,
        web_ui_port: args.web_ui_port,
    })
}
