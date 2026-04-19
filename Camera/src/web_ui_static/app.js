(function () {
    const POLL_MS = 1000;

    const elements = {
        status: document.getElementById("status"),
        playbackState: document.getElementById("playback-state"),
        previews: {
            detection: document.getElementById("preview-detection"),
            mask: document.getElementById("preview-mask"),
            hMask: document.getElementById("preview-h-mask"),
            sMask: document.getElementById("preview-s-mask"),
            vMask: document.getElementById("preview-v-mask"),
        },
        runtime: {
            detection: document.getElementById("log-detection"),
            virtual: document.getElementById("log-virtual"),
            capture: document.getElementById("log-capture"),
            detect: document.getElementById("log-detect"),
            total: document.getElementById("log-total"),
            captureAvg: document.getElementById("log-capture-avg"),
            detectAvg: document.getElementById("log-detect-avg"),
            totalAvg: document.getElementById("log-total-avg"),
        },
        controls: {
            quality: document.getElementById("quality"),
            cropEnabled: document.getElementById("crop-enabled"),
            cropLeft: document.getElementById("crop-left"),
            cropTop: document.getElementById("crop-top"),
            cropWidth: document.getElementById("crop-width"),
            cropHeight: document.getElementById("crop-height"),
            hMin: document.getElementById("h-min"),
            hMinNumber: document.getElementById("h-min-number"),
            hMax: document.getElementById("h-max"),
            hMaxNumber: document.getElementById("h-max-number"),
            sMin: document.getElementById("s-min"),
            sMinNumber: document.getElementById("s-min-number"),
            sMax: document.getElementById("s-max"),
            sMaxNumber: document.getElementById("s-max-number"),
            vMin: document.getElementById("v-min"),
            vMinNumber: document.getElementById("v-min-number"),
            vMax: document.getElementById("v-max"),
            vMaxNumber: document.getElementById("v-max-number"),
            virtualEnabled: document.getElementById("virtual-enabled"),
            virtualXSize: document.getElementById("virtual-x-size"),
            virtualYSize: document.getElementById("virtual-y-size"),
        },
        buttons: {
            play: document.getElementById("playback-play"),
            pause: document.getElementById("playback-pause"),
            reprocess: document.getElementById("playback-reprocess"),
            next: document.getElementById("playback-next"),
            saveTopLeft: document.getElementById("save-top-left"),
            saveTopRight: document.getElementById("save-top-right"),
            saveBottomLeft: document.getElementById("save-bottom-left"),
            saveBottomRight: document.getElementById("save-bottom-right"),
            clearCorners: document.getElementById("clear-corners"),
            exportSettings: document.getElementById("export-settings"),
            importSettings: document.getElementById("import-settings"),
        },
        importFile: document.getElementById("import-settings-file"),
    };

    const state = {
        settings: null,
        playbackPaused: false,
        latestPoint: null,
        lastSyncFailed: false,
        dirtyFromUser: false,
        updateTimer: null,
        streamLoopRunning: false,
        streamLastFrame: 0,
    };

    function setStatus(message, isError) {
        elements.status.textContent = message;
        elements.status.classList.toggle("error", Boolean(isError));
    }

    function asNumber(value, fallback) {
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : fallback;
    }

    function formatMs(value) {
        if (value == null || !Number.isFinite(value)) {
            return "-";
        }
        return value.toFixed(2);
    }

    function setImage(element, uri) {
        if (!element) {
            return;
        }
        if (typeof uri === "string" && uri.length > 0) {
            element.src = uri;
        }
    }

    function syncPair(rangeEl, numberEl) {
        if (!rangeEl || !numberEl) {
            return;
        }

        const fromRange = () => {
            numberEl.value = rangeEl.value;
            scheduleSettingsUpdate();
        };
        const fromNumber = () => {
            rangeEl.value = numberEl.value;
            scheduleSettingsUpdate();
        };

        rangeEl.addEventListener("input", fromRange);
        numberEl.addEventListener("input", fromNumber);
    }

    function cloneSettings(settings) {
        return JSON.parse(JSON.stringify(settings));
    }

    function applySettingsToControls(settings) {
        if (!settings) {
            return;
        }

        const c = elements.controls;
        c.quality.value = settings.detector.quality;

        c.cropEnabled.checked = Boolean(settings.detector.crop.enabled);
        c.cropLeft.value = settings.detector.crop.left_pct;
        c.cropTop.value = settings.detector.crop.top_pct;
        c.cropWidth.value = settings.detector.crop.width_pct;
        c.cropHeight.value = settings.detector.crop.height_pct;

        c.hMin.value = settings.hsv.h_min;
        c.hMinNumber.value = settings.hsv.h_min;
        c.hMax.value = settings.hsv.h_max;
        c.hMaxNumber.value = settings.hsv.h_max;
        c.sMin.value = settings.hsv.s_min;
        c.sMinNumber.value = settings.hsv.s_min;
        c.sMax.value = settings.hsv.s_max;
        c.sMaxNumber.value = settings.hsv.s_max;
        c.vMin.value = settings.hsv.v_min;
        c.vMinNumber.value = settings.hsv.v_min;
        c.vMax.value = settings.hsv.v_max;
        c.vMaxNumber.value = settings.hsv.v_max;

        c.virtualEnabled.checked = Boolean(settings.virtual_coordinates.enabled);
        c.virtualXSize.value = settings.virtual_coordinates.x_size;
        c.virtualYSize.value = settings.virtual_coordinates.y_size;
    }

    function collectSettingsFromControls() {
        const c = elements.controls;

        const next = state.settings ? cloneSettings(state.settings) : {
            detector: {
                quality: "ultra_low",
                crop: {
                    enabled: true,
                    left_pct: 0,
                    top_pct: 0,
                    width_pct: 0,
                    height_pct: 0,
                },
            },
            hsv: {
                h_min: 36,
                s_min: 91,
                v_min: 100,
                h_max: 47,
                s_max: 255,
                v_max: 209,
            },
            virtual_coordinates: {
                enabled: false,
                x_size: 100,
                y_size: 100,
                corners: {
                    top_left: null,
                    top_right: null,
                    bottom_right: null,
                    bottom_left: null,
                },
            },
        };

        next.detector.quality = c.quality.value;
        next.detector.crop.enabled = Boolean(c.cropEnabled.checked);
        next.detector.crop.left_pct = asNumber(c.cropLeft.value, 0);
        next.detector.crop.top_pct = asNumber(c.cropTop.value, 0);
        next.detector.crop.width_pct = asNumber(c.cropWidth.value, 1);
        next.detector.crop.height_pct = asNumber(c.cropHeight.value, 1);

        next.hsv.h_min = asNumber(c.hMin.value, 0);
        next.hsv.h_max = asNumber(c.hMax.value, 179);
        next.hsv.s_min = asNumber(c.sMin.value, 0);
        next.hsv.s_max = asNumber(c.sMax.value, 255);
        next.hsv.v_min = asNumber(c.vMin.value, 0);
        next.hsv.v_max = asNumber(c.vMax.value, 255);

        next.virtual_coordinates.enabled = Boolean(c.virtualEnabled.checked);
        next.virtual_coordinates.x_size = asNumber(c.virtualXSize.value, 100);
        next.virtual_coordinates.y_size = asNumber(c.virtualYSize.value, 100);
        if (!next.virtual_coordinates.corners) {
            next.virtual_coordinates.corners = {
                top_left: null,
                top_right: null,
                bottom_right: null,
                bottom_left: null,
            };
        }

        return next;
    }

    function applyPayload(payload) {
        if (!payload) {
            return;
        }

        if (payload.settings) {
            state.settings = payload.settings;
            if (!state.dirtyFromUser) {
                applySettingsToControls(payload.settings);
            }
        }

        if (payload.playback) {
            state.playbackPaused = Boolean(payload.playback.paused);
            elements.playbackState.textContent = state.playbackPaused ? "Paused" : "Running";
        }

        if (payload.runtime_log) {
            applyRuntimeLog(payload.runtime_log);
        }

        if (payload.previews) {
            setImage(elements.previews.detection, payload.previews.detection);
            setImage(elements.previews.mask, payload.previews.mask);
            setImage(elements.previews.hMask, payload.previews.h_mask);
            setImage(elements.previews.sMask, payload.previews.s_mask);
            setImage(elements.previews.vMask, payload.previews.v_mask);
        }
    }

    function applyRuntimeLog(log) {
        state.latestPoint = log.detection_point || null;
        elements.runtime.detection.textContent = log.detection_found ? "Detected" : "Not found";
        elements.runtime.virtual.textContent = log.detection_point
            ? `x=${log.detection_point.x.toFixed(3)} y=${log.detection_point.y.toFixed(3)}`
            : "-";
        elements.runtime.capture.textContent = formatMs(log.capture_ms);
        elements.runtime.detect.textContent = formatMs(log.detect_ms);
        elements.runtime.total.textContent = formatMs(log.total_ms);
        elements.runtime.captureAvg.textContent = formatMs(log.avg_capture_ms);
        elements.runtime.detectAvg.textContent = formatMs(log.avg_detect_ms);
        elements.runtime.totalAvg.textContent = formatMs(log.avg_total_ms);
    }

    function applyStreamPayload(payload) {
        if (!payload) {
            return;
        }

        if (Number.isFinite(payload.frame)) {
            state.streamLastFrame = payload.frame;
        }

        if (typeof payload.detection === "string" && payload.detection.length > 0) {
            setImage(elements.previews.detection, payload.detection);
        }

        if (payload.runtime_log) {
            applyRuntimeLog(payload.runtime_log);
        }
    }

    async function sendCameraEvent(eventType, data) {
        if (!window.webui || typeof window.webui.sendEvent !== "function") {
            throw new Error("webui.js not loaded");
        }

        const response = await window.webui.sendEvent("camera", eventType, data || {});
        if (!response || !response.success) {
            const message = response && response.message ? response.message : "request failed";
            throw new Error(message);
        }

        if (response.data) {
            applyPayload(response.data);
        }

        if (response.message) {
            setStatus(response.message, false);
        }

        return response;
    }

    async function sync() {
        try {
            await sendCameraEvent("sync", {});
            if (state.lastSyncFailed) {
                setStatus("Connection restored", false);
                state.lastSyncFailed = false;
            }
        } catch (error) {
            state.lastSyncFailed = true;
            setStatus(`Sync failed: ${error.message}`, true);
        }
    }

    async function runStreamLoop() {
        if (state.streamLoopRunning) {
            return;
        }

        state.streamLoopRunning = true;

        while (state.streamLoopRunning) {
            try {
                const response = await sendCameraEvent("stream_frame", {
                    last_frame: state.streamLastFrame,
                });

                if (response && response.data) {
                    applyStreamPayload(response.data);
                }

                if (state.lastSyncFailed) {
                    setStatus("Connection restored", false);
                    state.lastSyncFailed = false;
                }
            } catch (error) {
                state.lastSyncFailed = true;
                setStatus(`Stream failed: ${error.message}`, true);
                await new Promise((resolve) => window.setTimeout(resolve, 300));
            }
        }
    }

    function scheduleSettingsUpdate() {
        state.dirtyFromUser = true;
        if (state.updateTimer) {
            window.clearTimeout(state.updateTimer);
        }

        state.updateTimer = window.setTimeout(async () => {
            state.updateTimer = null;
            const settings = collectSettingsFromControls();
            try {
                await sendCameraEvent("update_settings", { settings: settings });
                state.dirtyFromUser = false;
            } catch (error) {
                setStatus(`Failed to update settings: ${error.message}`, true);
            }
        }, 120);
    }

    function withDetectedCorner(label, cornerKey) {
        return async function () {
            if (!state.latestPoint) {
                setStatus("No detection point available to store as a corner", true);
                return;
            }

            const next = collectSettingsFromControls();
            next.virtual_coordinates.corners[cornerKey] = {
                x: state.latestPoint.x,
                y: state.latestPoint.y,
            };

            try {
                await sendCameraEvent("update_settings", { settings: next });
                state.dirtyFromUser = false;
                setStatus(`${label} corner stored`, false);
            } catch (error) {
                setStatus(`Failed to save corner: ${error.message}`, true);
            }
        };
    }

    function clearCorners() {
        const next = collectSettingsFromControls();
        next.virtual_coordinates.corners = {
            top_left: null,
            top_right: null,
            bottom_right: null,
            bottom_left: null,
        };

        sendCameraEvent("update_settings", { settings: next }).catch((error) => {
            setStatus(`Failed to clear corners: ${error.message}`, true);
        });
    }

    function exportSettings() {
        if (!state.settings) {
            setStatus("No settings available to export yet", true);
            return;
        }

        const blob = new Blob([JSON.stringify(state.settings, null, 2)], {
            type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "camera-settings.json";
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
        URL.revokeObjectURL(url);
        setStatus("Settings exported", false);
    }

    function importSettingsFromFile(file) {
        const reader = new FileReader();
        reader.onload = async function () {
            try {
                const parsed = JSON.parse(String(reader.result || ""));
                await sendCameraEvent("update_settings", { settings: parsed });
                state.dirtyFromUser = false;
                setStatus("Settings imported", false);
            } catch (error) {
                setStatus(`Import failed: ${error.message}`, true);
            }
        };
        reader.onerror = function () {
            setStatus("Failed to read settings file", true);
        };
        reader.readAsText(file);
    }

    function bindControls() {
        const c = elements.controls;
        const b = elements.buttons;

        syncPair(c.hMin, c.hMinNumber);
        syncPair(c.hMax, c.hMaxNumber);
        syncPair(c.sMin, c.sMinNumber);
        syncPair(c.sMax, c.sMaxNumber);
        syncPair(c.vMin, c.vMinNumber);
        syncPair(c.vMax, c.vMaxNumber);

        [
            c.quality,
            c.cropEnabled,
            c.cropLeft,
            c.cropTop,
            c.cropWidth,
            c.cropHeight,
            c.virtualEnabled,
            c.virtualXSize,
            c.virtualYSize,
        ].forEach((el) => {
            if (!el) {
                return;
            }
            el.addEventListener("change", scheduleSettingsUpdate);
            el.addEventListener("input", scheduleSettingsUpdate);
        });

        b.play.addEventListener("click", () => {
            sendCameraEvent("playback", { paused: false }).catch((error) => {
                setStatus(`Playback update failed: ${error.message}`, true);
            });
        });

        b.pause.addEventListener("click", () => {
            sendCameraEvent("playback", { paused: true }).catch((error) => {
                setStatus(`Playback update failed: ${error.message}`, true);
            });
        });

        b.reprocess.addEventListener("click", () => {
            sendCameraEvent("playback", { reprocess_current_frame: true }).catch((error) => {
                setStatus(`Playback update failed: ${error.message}`, true);
            });
        });

        b.next.addEventListener("click", () => {
            sendCameraEvent("playback", { step_next_frame: true }).catch((error) => {
                setStatus(`Playback update failed: ${error.message}`, true);
            });
        });

        b.saveTopLeft.addEventListener("click", withDetectedCorner("Top-left", "top_left"));
        b.saveTopRight.addEventListener("click", withDetectedCorner("Top-right", "top_right"));
        b.saveBottomLeft.addEventListener("click", withDetectedCorner("Bottom-left", "bottom_left"));
        b.saveBottomRight.addEventListener("click", withDetectedCorner("Bottom-right", "bottom_right"));
        b.clearCorners.addEventListener("click", clearCorners);

        b.exportSettings.addEventListener("click", exportSettings);
        b.importSettings.addEventListener("click", () => elements.importFile.click());

        elements.importFile.addEventListener("change", () => {
            const file = elements.importFile.files && elements.importFile.files[0];
            if (file) {
                importSettingsFromFile(file);
            }
            elements.importFile.value = "";
        });
    }

    function bootstrap() {
        bindControls();
        setStatus("Connecting...", false);
        sync();
        runStreamLoop();
        window.setInterval(sync, POLL_MS);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bootstrap);
    } else {
        bootstrap();
    }
})();
