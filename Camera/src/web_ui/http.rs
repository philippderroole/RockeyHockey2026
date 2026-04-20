use std::io::{self, Read};
use std::thread;
use std::time::Duration;

use log::error;
use tiny_http::{Method, Request, Response, Server, StatusCode};

use crate::puck_detector::RuntimeDetectorSettings;

use super::render::{cache_control_no_store, content_type, html_page};
use super::state::{
    PlaybackControlUpdate, PreviewStreamKind, SharedPlaybackControl, SharedPreviewFrames,
    SharedRuntimeSettings, WebRuntimeLog,
};

type BoxedResponse = Response<Box<dyn Read + Send>>;

#[derive(Clone)]
pub(super) struct WebUiDependencies {
    pub shared: SharedRuntimeSettings,
    pub previews: SharedPreviewFrames,
    pub playback: SharedPlaybackControl,
}

#[derive(Clone)]
struct WebUiRequestHandler {
    deps: WebUiDependencies,
}

impl WebUiRequestHandler {
    fn new(deps: WebUiDependencies) -> Self {
        Self { deps }
    }

    fn handle(&self, mut request: Request) {
        let path = request.url().split('?').next().unwrap_or("/");
        let route = Route::from_method_path(request.method(), path);

        let response_result = match route {
            Route::Home => Ok(box_response(
                Response::from_string(html_page())
                    .with_header(content_type("text/html; charset=UTF-8")),
            )),
            Route::GetSettings => self.get_settings_response(),
            Route::GetDetectionPreview => Ok(box_response(preview_response(
                self.deps.previews.get_detection_jpeg(),
            ))),
            Route::GetMaskPreview => Ok(box_response(preview_response(
                self.deps.previews.get_mask_jpeg(),
            ))),
            Route::GetHMaskPreview => Ok(box_response(preview_response(
                self.deps.previews.get_h_mask_jpeg(),
            ))),
            Route::GetSMaskPreview => Ok(box_response(preview_response(
                self.deps.previews.get_s_mask_jpeg(),
            ))),
            Route::GetVMaskPreview => Ok(box_response(preview_response(
                self.deps.previews.get_v_mask_jpeg(),
            ))),
            Route::GetDetectionStream => Ok(box_response(mjpeg_response(
                self.deps.previews.clone(),
                PreviewStreamKind::Detection,
            ))),
            Route::GetMaskStream => Ok(box_response(mjpeg_response(
                self.deps.previews.clone(),
                PreviewStreamKind::Mask,
            ))),
            Route::GetHMaskStream => Ok(box_response(mjpeg_response(
                self.deps.previews.clone(),
                PreviewStreamKind::HMask,
            ))),
            Route::GetSMaskStream => Ok(box_response(mjpeg_response(
                self.deps.previews.clone(),
                PreviewStreamKind::SMask,
            ))),
            Route::GetVMaskStream => Ok(box_response(mjpeg_response(
                self.deps.previews.clone(),
                PreviewStreamKind::VMask,
            ))),
            Route::GetLatestLogs => Ok(box_response(log_response(
                self.deps.previews.get_latest_log(),
            ))),
            Route::GetPlayback => self.get_playback_response(),
            Route::PostSettings => {
                handle_update_request(&mut request, &self.deps.shared, &self.deps.previews)
                    .map(box_response)
            }
            Route::PostPlayback => {
                handle_playback_update_request(&mut request, &self.deps.playback).map(box_response)
            }
            Route::NotFound => Ok(box_response(
                Response::from_string("Not found").with_status_code(StatusCode(404)),
            )),
        };

        let response = match response_result {
            Ok(response) => response,
            Err(err) => {
                error!("web UI request handling error: {err}");
                box_response(Response::from_string(err).with_status_code(StatusCode(400)))
            }
        };

        if let Err(err) = request.respond(response) {
            error!("failed to respond to web UI request: {err}");
        }
    }

    fn get_settings_response(&self) -> Result<BoxedResponse, String> {
        match serde_json::to_string(&self.deps.shared.get()) {
            Ok(body) => Ok(box_response(
                Response::from_string(body).with_header(content_type("application/json")),
            )),
            Err(err) => Err(format!("failed to serialize settings: {err}")),
        }
    }

    fn get_playback_response(&self) -> Result<BoxedResponse, String> {
        match serde_json::to_string(&self.deps.playback.get_state()) {
            Ok(body) => Ok(box_response(
                Response::from_string(body).with_header(content_type("application/json")),
            )),
            Err(err) => Err(format!("failed to serialize playback state: {err}")),
        }
    }
}

enum Route {
    Home,
    GetSettings,
    GetDetectionPreview,
    GetMaskPreview,
    GetHMaskPreview,
    GetSMaskPreview,
    GetVMaskPreview,
    GetDetectionStream,
    GetMaskStream,
    GetHMaskStream,
    GetSMaskStream,
    GetVMaskStream,
    GetLatestLogs,
    GetPlayback,
    PostSettings,
    PostPlayback,
    NotFound,
}

impl Route {
    fn from_method_path(method: &Method, path: &str) -> Self {
        match (method, path) {
            (Method::Get, "/") => Self::Home,
            (Method::Get, "/api/settings") => Self::GetSettings,
            (Method::Get, "/api/preview/detection.jpg") => Self::GetDetectionPreview,
            (Method::Get, "/api/preview/mask.jpg") => Self::GetMaskPreview,
            (Method::Get, "/api/preview/mask-h.jpg") => Self::GetHMaskPreview,
            (Method::Get, "/api/preview/mask-s.jpg") => Self::GetSMaskPreview,
            (Method::Get, "/api/preview/mask-v.jpg") => Self::GetVMaskPreview,
            (Method::Get, "/api/stream/detection.mjpg") => Self::GetDetectionStream,
            (Method::Get, "/api/stream/mask.mjpg") => Self::GetMaskStream,
            (Method::Get, "/api/stream/mask-h.mjpg") => Self::GetHMaskStream,
            (Method::Get, "/api/stream/mask-s.mjpg") => Self::GetSMaskStream,
            (Method::Get, "/api/stream/mask-v.mjpg") => Self::GetVMaskStream,
            (Method::Get, "/api/logs/latest") => Self::GetLatestLogs,
            (Method::Get, "/api/playback") => Self::GetPlayback,
            (Method::Post, "/api/settings") => Self::PostSettings,
            (Method::Post, "/api/playback") => Self::PostPlayback,
            _ => Self::NotFound,
        }
    }
}

pub(super) fn serve_requests(server: Server, deps: WebUiDependencies) {
    serve_requests_with_spawner(server, deps, &ThreadRequestSpawner);
}

trait RequestSpawner {
    fn spawn(&self, job: Box<dyn FnOnce() + Send>) -> std::io::Result<()>;
}

struct ThreadRequestSpawner;

impl RequestSpawner for ThreadRequestSpawner {
    fn spawn(&self, job: Box<dyn FnOnce() + Send>) -> std::io::Result<()> {
        thread::Builder::new()
            .name("web-ui-request".to_string())
            .spawn(job)?;
        Ok(())
    }
}

fn serve_requests_with_spawner(
    server: Server,
    deps: WebUiDependencies,
    spawner: &dyn RequestSpawner,
) {
    for request in server.incoming_requests() {
        let handler = WebUiRequestHandler::new(deps.clone());
        if let Err(err) = spawner.spawn(Box::new(move || handler.handle(request))) {
            error!("failed to spawn web UI request thread: {err}");
        }
    }
}

struct MjpegStream {
    previews: SharedPreviewFrames,
    kind: PreviewStreamKind,
    last_frame: u64,
    chunk: Vec<u8>,
    chunk_offset: usize,
}

impl MjpegStream {
    fn new(previews: SharedPreviewFrames, kind: PreviewStreamKind) -> Self {
        Self {
            previews,
            kind,
            last_frame: 0,
            chunk: Vec::new(),
            chunk_offset: 0,
        }
    }

    fn refill_chunk(&mut self) {
        loop {
            let next =
                self.previews
                    .wait_for_jpeg(self.kind, self.last_frame, Duration::from_millis(500));
            if let Some((frame, jpeg)) = next {
                self.last_frame = frame;
                self.chunk = build_mjpeg_chunk(&jpeg);
                self.chunk_offset = 0;
                return;
            }
        }
    }
}

impl Read for MjpegStream {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        if buf.is_empty() {
            return Ok(0);
        }

        if self.chunk_offset >= self.chunk.len() {
            self.refill_chunk();
        }

        let remaining = &self.chunk[self.chunk_offset..];
        let to_copy = remaining.len().min(buf.len());
        buf[..to_copy].copy_from_slice(&remaining[..to_copy]);
        self.chunk_offset += to_copy;
        Ok(to_copy)
    }
}

fn build_mjpeg_chunk(jpeg: &[u8]) -> Vec<u8> {
    let mut chunk = Vec::with_capacity(jpeg.len() + 96);
    chunk.extend_from_slice(b"--frame\r\n");
    chunk.extend_from_slice(b"Content-Type: image/jpeg\r\n");
    chunk.extend_from_slice(format!("Content-Length: {}\r\n\r\n", jpeg.len()).as_bytes());
    chunk.extend_from_slice(jpeg);
    chunk.extend_from_slice(b"\r\n");
    chunk
}

fn box_response<R: Read + Send + 'static>(response: Response<R>) -> BoxedResponse {
    response.boxed()
}

fn mjpeg_response(previews: SharedPreviewFrames, kind: PreviewStreamKind) -> Response<MjpegStream> {
    Response::new(
        StatusCode(200),
        vec![
            content_type("multipart/x-mixed-replace; boundary=frame"),
            cache_control_no_store(),
        ],
        MjpegStream::new(previews, kind),
        None,
        None,
    )
}

fn preview_response(bytes: Option<Vec<u8>>) -> Response<std::io::Cursor<Vec<u8>>> {
    if let Some(bytes) = bytes {
        return Response::from_data(bytes)
            .with_header(content_type("image/jpeg"))
            .with_header(cache_control_no_store());
    }

    Response::from_string("No preview frame yet")
        .with_status_code(StatusCode(503))
        .with_header(content_type("text/plain; charset=UTF-8"))
}

fn log_response(log: Option<WebRuntimeLog>) -> Response<std::io::Cursor<Vec<u8>>> {
    if let Some(log) = log
        && let Ok(body) = serde_json::to_string(&log)
    {
        return Response::from_string(body)
            .with_header(content_type("application/json"))
            .with_header(cache_control_no_store());
    }

    Response::from_string("No runtime log yet")
        .with_status_code(StatusCode(503))
        .with_header(content_type("text/plain; charset=UTF-8"))
}

fn handle_update_request(
    request: &mut Request,
    shared: &SharedRuntimeSettings,
    previews: &SharedPreviewFrames,
) -> Result<Response<std::io::Cursor<Vec<u8>>>, String> {
    let mut body = String::new();
    request
        .as_reader()
        .read_to_string(&mut body)
        .map_err(|err| format!("failed to read request body: {err}"))?;

    let parsed: RuntimeDetectorSettings =
        serde_json::from_str(&body).map_err(|err| format!("invalid JSON: {err}"))?;

    shared.set(parsed);
    previews.reset_runtime_averages();

    Ok(Response::from_string("ok").with_header(content_type("text/plain; charset=UTF-8")))
}

fn handle_playback_update_request(
    request: &mut Request,
    playback: &SharedPlaybackControl,
) -> Result<Response<std::io::Cursor<Vec<u8>>>, String> {
    let mut body = String::new();
    request
        .as_reader()
        .read_to_string(&mut body)
        .map_err(|err| format!("failed to read request body: {err}"))?;

    let parsed: PlaybackControlUpdate =
        serde_json::from_str(&body).map_err(|err| format!("invalid JSON: {err}"))?;

    let updated = playback.apply_update(parsed);
    let payload = serde_json::to_string(&updated)
        .map_err(|err| format!("failed to serialize playback state: {err}"))?;

    Ok(Response::from_string(payload).with_header(content_type("application/json")))
}
