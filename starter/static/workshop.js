"use strict";
// Provided workshop helpers. You do not need to edit this file.
// Your app.js loads after this file and calls these functions.

const $ = (selector) => document.querySelector(selector);

function showError(message) {
  $("#app-error").textContent = message;
  $("#app-error").hidden = !message;
}

// ---- One action at a time ----------------------------------------------------
// runAction shows a status message, disables the page's controls, runs your
// async function, and shows any thrown error. Each run gets an attempt number,
// so a cancelled action cannot change the UI of a newer one. While an action
// runs, isBusy() is true and your selectWord refuses to switch words.

let busy = false;
let actionVersion = 0;

function isBusy() {
  return busy;
}

function setBusy(value) {
  busy = value;
  document.querySelectorAll("button, input, select").forEach((control) => {
    control.disabled = value;
  });
  if ($("#stop-recording")) $("#stop-recording").disabled = false;
  if ($("#audio-consent")) $("#audio-consent").disabled = false;
}

async function runAction(message, action) {
  if (busy) {
    showError("Wait for the current action to finish.");
    return;
  }
  showError("");
  const attempt = ++actionVersion;
  setBusy(true);
  $("#model-status").textContent = message;
  try {
    await action(attempt);
  } catch (error) {
    if (attempt === actionVersion) {
      showError(error.message || "The action failed. Check the server and try again.");
    }
  } finally {
    if (attempt === actionVersion) {
      setBusy(false);
      $("#model-status").textContent = "";
    }
  }
}

// ---- Calling your Flask routes ---------------------------------------------

function jsonOptions(body) {
  return {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)};
}

async function appJSON(response) {
  if (!response.headers.get("Content-Type")?.includes("application/json")) {
    throw new Error("Expected JSON from Flask. Reopen the private app port if sign-in expired.");
  }
  let body;
  try { body = await response.json(); }
  catch { throw new Error("Flask returned unreadable JSON."); }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new Error("Flask returned an unexpected response shape.");
  }
  return body;
}

async function callApp(path, options) {
  let response;
  try {
    response = await fetch(path, {...options, mode: "same-origin", credentials: "same-origin"});
  } catch {
    throw new Error("Cannot reach Flask. Check its terminal or reopen the private Codespaces port.");
  }
  if (!response.ok) {
    let message = `Request failed (${response.status}). Check the Flask terminal; reopen the app if Codespaces sign-in expired.`;
    if (response.headers.get("Content-Type")?.includes("application/json")) {
      const body = await appJSON(response);
      if (typeof body.error === "string") message = body.error;
    }
    const retry = response.headers.get("Retry-After");
    if (retry && /^\d+$/.test(retry)) message += ` Retry after ${retry} seconds.`;
    throw new Error(message);
  }
  return response;
}

// ---- Playing and saving audio ------------------------------------------------

const playbackUrls = new WeakMap();

function stopAudio(player) {
  player.pause();
  player.removeAttribute("src");
  player.hidden = true;
  if (playbackUrls.has(player)) URL.revokeObjectURL(playbackUrls.get(player));
  playbackUrls.delete(player);
}

async function playAudio(player, blob) {
  stopAudio(player);
  const url = URL.createObjectURL(blob);
  playbackUrls.set(player, url);
  player.onerror = () => showError("The browser could not play the WAV.");
  player.src = url;
  player.hidden = false;
  try { await player.play(); }
  catch { throw new Error("Automatic playback was blocked. Use the visible audio player's Play button."); }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ---- Lesson 3: recording answers ---------------------------------------------
// MediaRecorder may not produce WAV. recordingToWav decodes its output and
// resamples it to mono 16 kHz with OfflineAudioContext; encodeWav then writes a
// 44-byte header and 16-bit PCM samples. Renaming a file would not convert it.

const MAX_SECONDS = 12;

function encodeWav(samples) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeText = (offset, text) => [...text].forEach((char, index) => {
    view.setUint8(offset + index, char.charCodeAt(0));
  });
  writeText(0, "RIFF"); view.setUint32(4, 36 + samples.length * 2, true);
  writeText(8, "WAVE"); writeText(12, "fmt "); view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, 16000, true); view.setUint32(28, 32000, true);
  view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  writeText(36, "data"); view.setUint32(40, samples.length * 2, true);
  samples.forEach((sample, index) => {
    const value = Math.max(-1, Math.min(1, sample));
    view.setInt16(44 + index * 2, value * (value < 0 ? 32768 : 32767), true);
  });
  return new Blob([buffer], {type: "audio/wav"});
}

async function recordingToWav(blob) {
  const context = new AudioContext();
  let decoded;
  try { decoded = await context.decodeAudioData(await blob.arrayBuffer()); }
  finally { await context.close(); }
  const frames = Math.min(Math.ceil(decoded.duration * 16000), MAX_SECONDS * 16000);
  if (!frames) throw new Error("The recording was empty. Try again.");
  const offline = new OfflineAudioContext(1, frames, 16000);
  const source = offline.createBufferSource();
  source.buffer = decoded;
  source.connect(offline.destination);
  source.start();
  const mono = await offline.startRendering();
  return encodeWav(mono.getChannelData(0));
}

// setupAnswerRecorder wires the lesson 3 controls: consent, Record/Stop,
// the synthetic-WAV picker, the local preview, and Discard.
// It returns {audio, discard}:
//   audio()   -> the WAV Blob waiting to be sent, or null
//   discard() -> cancel any capture (including a pending permission prompt),
//                stop microphone tracks, and clear the preview
// onNewAudio runs whenever a new recording or file replaces the old one.
function setupAnswerRecorder({onNewAudio = () => {}} = {}) {
  let activeRecorder = null;
  let captureStream = null;
  let recordingTimer = null;
  let captureAttempt = null;
  let pendingAudio = null;
  let previewUrl = null;

  function clearPreview() {
    pendingAudio = null;
    $("#audio-preview").pause();
    $("#audio-preview").removeAttribute("src");
    $("#audio-preview").hidden = true;
    $("#recording-review").hidden = true;
    $("#audio-file").value = "";
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = null;
  }

  function finishCapture() {
    $("#stop-recording").hidden = true;
    if (activeRecorder?.state === "recording") activeRecorder.stop();
  }

  function review(blob) {
    clearPreview();
    pendingAudio = blob;
    previewUrl = URL.createObjectURL(blob);
    $("#audio-preview").src = previewUrl;
    $("#audio-preview").hidden = false;
    $("#recording-review").hidden = false;
    $("#record-status").textContent = "Ready to preview locally. Nothing has been sent yet.";
  }

  function cancel(status) {
    if (captureAttempt !== null && captureAttempt === actionVersion) {
      actionVersion += 1;
      setBusy(false);
      $("#model-status").textContent = "";
    }
    captureAttempt = null;
    if (activeRecorder?.state === "recording") activeRecorder.stop();
    captureStream?.getTracks().forEach((track) => track.stop());
    activeRecorder = null;
    captureStream = null;
    clearTimeout(recordingTimer);
    recordingTimer = null;
    $("#stop-recording").hidden = true;
    clearPreview();
    $("#record-status").textContent = status;
  }

  async function record() {
    if (!$("#audio-consent").checked) {
      showError("Read the approved audio guidance and choose whether to participate first.");
      return;
    }
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia ||
        !window.MediaRecorder || !window.AudioContext || !window.OfflineAudioContext) {
      showError("Recording is unavailable. Use the HTTPS app in a normal tab, or choose a synthetic WAV.");
      return;
    }
    await runAction("Preparing your microphone...", async (attempt) => {
      captureAttempt = attempt;
      const current = () => captureAttempt === attempt && actionVersion === attempt;
      let stream = null;
      let recorder = null;
      let timer = null;
      clearPreview();
      onNewAudio();
      $("#stop-recording").hidden = false;
      $("#record-status").textContent = "Waiting for microphone permission...";
      try {
        stream = await navigator.mediaDevices.getUserMedia({audio: true});
        if (!current() || !$("#audio-consent").checked) return;
        captureStream = stream;
        recorder = new MediaRecorder(stream);
        activeRecorder = recorder;
        const chunks = [];
        recorder.addEventListener("dataavailable", (event) => {
          if (event.data.size) chunks.push(event.data);
        });
        const stopped = new Promise((resolve, reject) => {
          recorder.addEventListener("stop", resolve, {once: true});
          recorder.addEventListener("error", () => reject(new Error("Capture failed.")), {once: true});
        });
        recorder.start();
        $("#record-status").textContent = `Recording locally; stops after ${MAX_SECONDS} seconds.`;
        timer = setTimeout(finishCapture, MAX_SECONDS * 1000);
        recordingTimer = timer;
        await stopped;
        stream.getTracks().forEach((track) => track.stop());
        if (!current()) return;
        $("#record-status").textContent = "Converting to WAV...";
        const wav = await recordingToWav(new Blob(chunks, {type: recorder.mimeType}));
        if (current()) review(wav);
      } catch (error) {
        if (!current()) return;
        $("#record-status").textContent = "Recording did not finish. Try again or choose a synthetic WAV.";
        throw new Error(error.name === "NotAllowedError"
          ? "Microphone access was declined. Choose a synthetic WAV instead."
          : "Recording or WAV conversion failed. Check your microphone or choose a synthetic WAV.");
      } finally {
        stream?.getTracks().forEach((track) => track.stop());
        if (recorder?.state === "recording") recorder.stop();
        clearTimeout(timer);
        if (captureAttempt === attempt) {
          captureAttempt = null;
          activeRecorder = null;
          captureStream = null;
          recordingTimer = null;
          $("#stop-recording").hidden = true;
        }
      }
    });
  }

  $("#record-answer").addEventListener("click", record);
  $("#stop-recording").addEventListener("click", () => {
    // Before recording starts (permission pending) Stop cancels; afterwards it only stops,
    // so a second press during WAV conversion cannot discard the new recording.
    if (activeRecorder) finishCapture();
    else cancel("Local recording discarded.");
  });
  $("#discard-recording").addEventListener("click", () => cancel("Local recording discarded."));
  $("#audio-consent").addEventListener("change", () => {
    if (!$("#audio-consent").checked) cancel("Local recording discarded.");
  });
  $("#audio-preview").addEventListener("error", () => showError("The browser could not preview this audio."));
  $("#audio-file").addEventListener("change", (event) => {
    const file = event.target.files[0];
    if (!file) return;
    runAction("Checking your WAV...", async () => {
      clearPreview();
      onNewAudio();
      if (file.size > 2 * 1024 * 1024) throw new Error("Choose a WAV smaller than 2 MiB.");
      const header = new Uint8Array(await file.slice(0, 12).arrayBuffer());
      const text = (start, end) => String.fromCharCode(...header.slice(start, end));
      if (header.length !== 12 || text(0, 4) !== "RIFF" || text(8, 12) !== "WAVE") {
        throw new Error("This is not a WAV file. Download a short synthetic sample from the speech buttons.");
      }
      review(file);
    });
  });
  window.addEventListener("pagehide", () => cancel(""));

  return {audio: () => pendingAudio, discard: () => cancel("")};
}
