use base64::Engine;
use base64::engine::general_purpose::STANDARD;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::time::Duration;
use web_ui::{UIResponse, WebUI};

use crate::puck_detector::RuntimeDetectorSettings;

use super::state::{
    PlaybackControlUpdate, SharedPlaybackControl, SharedPreviewFrames, SharedRuntimeSettings,
    WebPlaybackState, WebRuntimeLog,
};

#[derive(Clone)]
pub(super) struct WebUiDependencies {
    pub shared: SharedRuntimeSettings,
    pub previews: SharedPreviewFrames,
    pub playback: SharedPlaybackControl,
}

#[derive(Serialize)]
struct SyncPayload {
    settings: RuntimeDetectorSettings,
    playback: WebPlaybackState,
    runtime_log: Option<WebRuntimeLog>,
    previews: PreviewPayload,
}

#[derive(Serialize)]
struct PreviewPayload {
    detection: Option<String>,
    mask: Option<String>,
    h_mask: Option<String>,
    s_mask: Option<String>,
    v_mask: Option<String>,
}

#[derive(Deserialize)]
struct SettingsUpdateRequest {
    settings: RuntimeDetectorSettings,
}

#[derive(Deserialize)]
struct PlaybackUpdateRequest {
    #[serde(default)]
    paused: Option<bool>,
    #[serde(default)]
    reprocess_current_frame: Option<bool>,
    #[serde(default)]
    step_next_frame: Option<bool>,
}

pub(super) async fn serve_requests(web_ui: &WebUI, deps: WebUiDependencies) {
    register_sync_handler(web_ui, deps.clone()).await;
    register_stream_frame_handler(web_ui, deps.clone()).await;
    register_settings_handler(web_ui, deps.clone()).await;
    register_playback_handler(web_ui, deps).await;
}

#[derive(Deserialize)]
struct StreamFrameRequest {
    #[serde(default)]
    last_frame: Option<u64>,
}

#[derive(Serialize)]
struct StreamFramePayload {
    frame: u64,
    detection: Option<String>,
    runtime_log: Option<WebRuntimeLog>,
}

async fn register_sync_handler(web_ui: &WebUI, deps: WebUiDependencies) {
    web_ui
        .bind_event("camera", "sync", move |event| {
            let payload = build_sync_payload(&deps);
            Ok(success_response(json!(payload), None, event.request_id))
        })
        .await;
}

async fn register_stream_frame_handler(web_ui: &WebUI, deps: WebUiDependencies) {
    web_ui
        .bind_event("camera", "stream_frame", move |event| {
            let parsed = deserialize_data::<StreamFrameRequest>(event.data)?;
            let last_frame = parsed.last_frame.unwrap_or(0);

            // Long-poll for a short window so the browser can chain requests
            // and receive new detector frames with lower latency.
            let snapshot = deps
                .previews
                .wait_for_snapshot_after(last_frame, Duration::from_millis(250));

            let payload = StreamFramePayload {
                frame: snapshot.frame,
                detection: to_data_uri(snapshot.detection_jpeg),
                runtime_log: snapshot.latest_log,
            };

            Ok(success_response(json!(payload), None, event.request_id))
        })
        .await;
}

async fn register_settings_handler(web_ui: &WebUI, deps: WebUiDependencies) {
    web_ui
        .bind_event("camera", "update_settings", move |event| {
            let parsed = deserialize_data::<SettingsUpdateRequest>(event.data)?;
            deps.shared.set(parsed.settings);
            deps.previews.reset_runtime_averages();

            let payload = build_sync_payload(&deps);
            Ok(success_response(
                json!(payload),
                Some("Settings updated".to_string()),
                event.request_id,
            ))
        })
        .await;
}

async fn register_playback_handler(web_ui: &WebUI, deps: WebUiDependencies) {
    web_ui
        .bind_event("camera", "playback", move |event| {
            let parsed = deserialize_data::<PlaybackUpdateRequest>(event.data)?;
            deps.playback.apply_update(PlaybackControlUpdate {
                paused: parsed.paused,
                reprocess_current_frame: parsed.reprocess_current_frame,
                step_next_frame: parsed.step_next_frame,
            });

            let payload = build_sync_payload(&deps);
            Ok(success_response(
                json!(payload),
                Some("Playback updated".to_string()),
                event.request_id,
            ))
        })
        .await;
}

fn build_sync_payload(deps: &WebUiDependencies) -> SyncPayload {
    let previews = deps.previews.snapshot();

    SyncPayload {
        settings: deps.shared.get(),
        playback: deps.playback.get_state(),
        runtime_log: previews.latest_log,
        previews: PreviewPayload {
            detection: to_data_uri(previews.detection_jpeg),
            mask: to_data_uri(previews.mask_jpeg),
            h_mask: to_data_uri(previews.h_mask_jpeg),
            s_mask: to_data_uri(previews.s_mask_jpeg),
            v_mask: to_data_uri(previews.v_mask_jpeg),
        },
    }
}

fn deserialize_data<T>(data: Value) -> Result<T, String>
where
    T: for<'de> Deserialize<'de>,
{
    serde_json::from_value(data).map_err(|err| format!("invalid event data: {err}"))
}

fn success_response(data: Value, message: Option<String>, request_id: Option<u32>) -> UIResponse {
    UIResponse {
        success: true,
        message,
        data: Some(data),
        request_id,
    }
}

fn to_data_uri(bytes: Option<Vec<u8>>) -> Option<String> {
    bytes.map(|bytes| {
        let encoded = STANDARD.encode(bytes);
        format!("data:image/jpeg;base64,{encoded}")
    })
}
