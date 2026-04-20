(function () {
    const POLL_MS = 1000;

    function createDefaultTarget() {
        return {
            h_min: 36,
            s_min: 91,
            v_min: 100,
            h_max: 47,
            s_max: 255,
            v_max: 209,
        };
    }

    function createDefaultSettings() {
        return {
            detector: {
                quality: "ultra_low",
                crop: {
                    enabled: true,
                    left_pct: 0,
                    top_pct: 0,
                    width_pct: 1,
                    height_pct: 1,
                },
            },
            hsv: createDefaultTarget(),
            additional_hsv_targets: [],
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
    }

    function normalizeSettings(settings) {
        const next = settings ? cloneSettings(settings) : createDefaultSettings();

        if (!next.detector) {
            next.detector = createDefaultSettings().detector;
        }
        if (!next.detector.crop) {
            next.detector.crop = createDefaultSettings().detector.crop;
        }
        if (!next.hsv) {
            next.hsv = createDefaultTarget();
        }
        if (!Array.isArray(next.additional_hsv_targets)) {
            next.additional_hsv_targets = [];
        }
        if (!next.virtual_coordinates) {
            next.virtual_coordinates = createDefaultSettings().virtual_coordinates;
        }
        if (!next.virtual_coordinates.corners) {
            next.virtual_coordinates.corners = createDefaultSettings().virtual_coordinates.corners;
        }

        return next;
    }

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
            virtualEnabled: document.getElementById("virtual-enabled"),
            virtualXSize: document.getElementById("virtual-x-size"),
            virtualYSize: document.getElementById("virtual-y-size"),
        },
        targets: {
            drawer: document.getElementById("detector-targets"),
            count: document.getElementById("target-count"),
            editor: document.getElementById("target-editor"),
            add: document.getElementById("add-target"),
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
        previewTargets: [],
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

    function getDetectorTargets(settings) {
        const next = normalizeSettings(settings);
        return [next.hsv].concat(next.additional_hsv_targets || []);
    }

    function formatTargetSummary(target) {
        return `H ${target.h_min}-${target.h_max} · S ${target.s_min}-${target.s_max} · V ${target.v_min}-${target.v_max}`;
    }

    function targetRowMarkup(label, field, min, max, value) {
        return `
            <div class="hsv-row">
                <span>${label}</span>
                <input type="range" min="${min}" max="${max}" step="1" value="${value}" data-target-field="${field}" data-role="range" />
                <input type="number" min="${min}" max="${max}" step="1" value="${value}" data-target-field="${field}" data-role="number" />
            </div>
        `;
    }

    function targetPreviewMarkup(kind, title) {
        return `
            <article class="preview-card preview-mini">
                <h3>${title}</h3>
                <img class="preview" alt="${title} preview" data-preview-kind="${kind}" />
            </article>
        `;
    }

    function createTargetCard(target, targetIndex) {
        const card = document.createElement("article");
        card.className = "target-card";
        card.dataset.targetCard = "true";
        card.dataset.targetIndex = String(targetIndex);

        const title = targetIndex === 0 ? "Primary target" : `Target ${targetIndex + 1}`;
        const subtitle = targetIndex === 0 ? "Base HSV profile" : "Additional HSV profile";

        card.innerHTML = `
            <div class="target-head">
                <div>
                    <h3>${title}</h3>
                    <p>${subtitle}</p>
                    <p class="target-summary">${formatTargetSummary(target)}</p>
                </div>
                <div class="target-actions">
                    <button type="button" data-action="remove-target" ${targetIndex === 0 ? "hidden" : ""}>Remove</button>
                </div>
            </div>
            <div class="target-controls">
                ${targetRowMarkup("H min", "h_min", 0, 179, target.h_min)}
                ${targetRowMarkup("H max", "h_max", 0, 179, target.h_max)}
                ${targetRowMarkup("S min", "s_min", 0, 255, target.s_min)}
                ${targetRowMarkup("S max", "s_max", 0, 255, target.s_max)}
                ${targetRowMarkup("V min", "v_min", 0, 255, target.v_min)}
                ${targetRowMarkup("V max", "v_max", 0, 255, target.v_max)}
            </div>
            <div class="target-previews">
                ${targetPreviewMarkup("mask", "Mask")}
                ${targetPreviewMarkup("h-mask", "Hue")}
                ${targetPreviewMarkup("s-mask", "Saturation")}
                ${targetPreviewMarkup("v-mask", "Value")}
            </div>
        `;

        return card;
    }

    function readTargetValue(card, field, fallback) {
        const selector = `[data-target-field="${field}"][data-role="number"]`;
        const input = card.querySelector(selector);
        return input ? asNumber(input.value, fallback) : fallback;
    }

    function readTargetFromCard(card) {
        return {
            h_min: readTargetValue(card, "h_min", 0),
            s_min: readTargetValue(card, "s_min", 0),
            v_min: readTargetValue(card, "v_min", 0),
            h_max: readTargetValue(card, "h_max", 179),
            s_max: readTargetValue(card, "s_max", 255),
            v_max: readTargetValue(card, "v_max", 255),
        };
    }

    function updateTargetSummary(card) {
        const summary = card.querySelector(".target-summary");
        if (!summary) {
            return;
        }

        summary.textContent = formatTargetSummary(readTargetFromCard(card));
    }

    function bindTargetPair(card, field) {
        const rangeEl = card.querySelector(`[data-target-field="${field}"][data-role="range"]`);
        const numberEl = card.querySelector(`[data-target-field="${field}"][data-role="number"]`);
        if (!rangeEl || !numberEl) {
            return;
        }

        const fromRange = () => {
            numberEl.value = rangeEl.value;
            updateTargetSummary(card);
            scheduleSettingsUpdate();
        };

        const fromNumber = () => {
            rangeEl.value = numberEl.value;
            updateTargetSummary(card);
            scheduleSettingsUpdate();
        };

        rangeEl.addEventListener("input", fromRange);
        numberEl.addEventListener("input", fromNumber);
    }

    function applyTargetPreviews() {
        if (!elements.targets.editor) {
            return;
        }

        const previewByIndex = new Map(
            (state.previewTargets || []).map((preview) => [preview.target_index, preview]),
        );

        elements.targets.editor.querySelectorAll("[data-target-card]").forEach((card) => {
            const targetIndex = Number(card.dataset.targetIndex);
            const preview = previewByIndex.get(targetIndex);

            const previewKinds = {
                "mask": preview ? preview.mask : null,
                "h-mask": preview ? preview.h_mask : null,
                "s-mask": preview ? preview.s_mask : null,
                "v-mask": preview ? preview.v_mask : null,
            };

            Object.entries(previewKinds).forEach(([kind, uri]) => {
                const image = card.querySelector(`[data-preview-kind="${kind}"]`);
                setImage(image, uri);
            });
        });
    }

    function applyPrimaryTargetPreview() {
        const primary = state.previewTargets.length > 0 ? state.previewTargets[0] : null;

        setImage(elements.previews.mask, primary ? primary.mask : null);
        setImage(elements.previews.hMask, primary ? primary.h_mask : null);
        setImage(elements.previews.sMask, primary ? primary.s_mask : null);
        setImage(elements.previews.vMask, primary ? primary.v_mask : null);
    }

    function renderTargetDrawer(settings) {
        const normalized = normalizeSettings(settings || state.settings || createDefaultSettings());
        if (!elements.targets.editor) {
            return;
        }

        const targets = getDetectorTargets(normalized);
        if (elements.targets.count) {
            elements.targets.count.textContent = `${targets.length} target${targets.length === 1 ? "" : "s"}`;
        }

        elements.targets.editor.innerHTML = "";

        targets.forEach((target, targetIndex) => {
            const card = createTargetCard(target, targetIndex);
            elements.targets.editor.appendChild(card);

            ["h_min", "h_max", "s_min", "s_max", "v_min", "v_max"].forEach((field) => {
                bindTargetPair(card, field);
            });

            const removeButton = card.querySelector('[data-action="remove-target"]');
            if (removeButton) {
                removeButton.addEventListener("click", () => removeTarget(targetIndex));
            }
        });

        applyTargetPreviews();
    }

    function removeTarget(targetIndex) {
        const next = collectSettingsFromControls();
        const additionalIndex = targetIndex - 1;
        if (additionalIndex < 0 || additionalIndex >= next.additional_hsv_targets.length) {
            return;
        }

        next.additional_hsv_targets.splice(additionalIndex, 1);
        state.settings = next;
        state.dirtyFromUser = true;
        renderTargetDrawer(next);

        sendCameraEvent("update_settings", { settings: next }).then(() => {
            state.dirtyFromUser = false;
        }).catch((error) => {
            setStatus(`Failed to update settings: ${error.message}`, true);
        });
    }

    function addTarget() {
        const next = collectSettingsFromControls();
        const existingTargets = getDetectorTargets(next);
        const source = existingTargets[existingTargets.length - 1] || createDefaultTarget();

        next.additional_hsv_targets.push(cloneSettings(source));
        state.settings = next;
        state.dirtyFromUser = true;
        renderTargetDrawer(next);

        sendCameraEvent("update_settings", { settings: next }).then(() => {
            state.dirtyFromUser = false;
        }).catch((error) => {
            setStatus(`Failed to update settings: ${error.message}`, true);
        });
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

        c.virtualEnabled.checked = Boolean(settings.virtual_coordinates.enabled);
        c.virtualXSize.value = settings.virtual_coordinates.x_size;
        c.virtualYSize.value = settings.virtual_coordinates.y_size;

        renderTargetDrawer(settings);
    }

    function collectSettingsFromControls() {
        const c = elements.controls;
        const next = normalizeSettings(state.settings ? cloneSettings(state.settings) : createDefaultSettings());

        next.detector.quality = c.quality.value;
        next.detector.crop.enabled = Boolean(c.cropEnabled.checked);
        next.detector.crop.left_pct = asNumber(c.cropLeft.value, 0);
        next.detector.crop.top_pct = asNumber(c.cropTop.value, 0);
        next.detector.crop.width_pct = asNumber(c.cropWidth.value, 1);
        next.detector.crop.height_pct = asNumber(c.cropHeight.value, 1);

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

        const targets = elements.targets.editor
            ? Array.from(elements.targets.editor.querySelectorAll("[data-target-card]"))
            : [];

        if (targets.length > 0) {
            next.hsv = readTargetFromCard(targets[0]);
            next.additional_hsv_targets = targets.slice(1).map((card) => readTargetFromCard(card));
        }

        return next;
    }

    function applyPayload(payload) {
        if (!payload) {
            return;
        }

        if (payload.settings) {
            state.settings = normalizeSettings(payload.settings);
            if (!state.dirtyFromUser) {
                applySettingsToControls(state.settings);
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
            state.previewTargets = Array.isArray(payload.previews.targets) ? payload.previews.targets : [];
            applyPrimaryTargetPreview();
            applyTargetPreviews();
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

        if (Array.isArray(payload.targets)) {
            state.previewTargets = payload.targets;
            applyPrimaryTargetPreview();
            applyTargetPreviews();
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

        if (elements.targets.add) {
            elements.targets.add.addEventListener("click", addTarget);
        }

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
