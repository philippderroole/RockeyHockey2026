use std::fs::{self, File};
use std::io::Write;
use std::path::PathBuf;
use std::process;
use std::time::{SystemTime, UNIX_EPOCH};

use anyhow::Context;

const INDEX_HTML: &str = include_str!("../web_ui_static/index.html");
const APP_JS: &str = include_str!("../web_ui_static/app.js");
const WEBUI_JS: &str = include_str!("../web_ui_static/webui.js");

pub fn prepare_embedded_static_dir() -> anyhow::Result<PathBuf> {
    let mut dir = std::env::temp_dir();
    dir.push(format!(
        "rockey_hockey_webui_{}_{}",
        process::id(),
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .context("system clock is before UNIX_EPOCH")?
            .as_millis()
    ));

    fs::create_dir_all(&dir).with_context(|| {
        format!(
            "failed to create embedded web UI directory at {}",
            dir.display()
        )
    })?;

    write_file(&dir.join("index.html"), INDEX_HTML)?;
    write_file(&dir.join("app.js"), APP_JS)?;
    write_file(&dir.join("webui.js"), WEBUI_JS)?;

    Ok(dir)
}

fn write_file(path: &PathBuf, content: &str) -> anyhow::Result<()> {
    let mut file = File::create(path)
        .with_context(|| format!("failed to create embedded asset {}", path.display()))?;
    file.write_all(content.as_bytes())
        .with_context(|| format!("failed to write embedded asset {}", path.display()))?;
    file.flush()
        .with_context(|| format!("failed to flush embedded asset {}", path.display()))?;
    Ok(())
}
