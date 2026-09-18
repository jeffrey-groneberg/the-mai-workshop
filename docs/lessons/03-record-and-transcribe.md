# Speak and see what was heard

Record an answer, convert it to WAV, and display what MAI heard.

![Record with MediaRecorder, decode and resample to mono 16 kHz 16-bit PCM WAV, and preview locally. Send then calls MAI-Transcribe-2 through Flask and APIM to return text.](../assets/diagrams/audio-path.webp){ width="960" height="549" loading="lazy" }

*MAI-generated diagram. [Full size](../assets/diagrams/audio-path.webp).*

## Build

### 1. Receive and validate audio in Flask

In **`starter/app.py`, add `import json` to the imports**, then **append**:

```python title="starter/app.py"
def upstream_json(response):
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError:
        abort(502, "The gateway returned unreadable JSON.")
    if not isinstance(payload, dict):
        abort(502, "The gateway returned an unexpected response shape.")
    return payload


@app.post("/transcribe")
def transcribe():
    language = language_for(request.form.get("locale"))
    upload = request.files.get("audio")
    if upload is None:
        abort(400, "Record or choose a WAV before sending.")
    audio = upload.read()
    check_wav(audio)
    base, headers = gateway_settings()
    definition = {
        "enhancedMode": {"enabled": True, "model": "MAI-Transcribe-2"},
        "locales": [language["stt"]],
    }
    response = httpx.post(
        f"{base}/speech/transcribe",
        params={"api-version": "2025-10-15"}, headers=headers,
        files={"audio": ("answer.wav", audio, "audio/wav")},
        data={"definition": json.dumps(definition)}, timeout=TIMEOUT,
    )
    payload = upstream_json(response)
    phrases = payload.get("combinedPhrases")
    if not isinstance(phrases, list) or not all(
        isinstance(item, dict) and isinstance(item.get("text"), str) for item in phrases
    ):
        abort(502, "The model returned no usable transcript.")
    text = " ".join(item["text"].strip() for item in phrases).strip()
    if not text:
        abort(422, "No words were recognized. Preview the sample or try again.")
    return jsonify(text=text)
```

The [API](https://learn.microsoft.com/azure/ai-services/speech-service/mai-transcribe)
expects multipart `audio` plus JSON-encoded `definition`.
`enhancedMode` selects MAI-Transcribe-2; `locales` takes a language code such
as `fr`, not `fr-FR`. The transcript is in `combinedPhrases[].text`.

### 2. Add recording controls

In **`starter/templates/index.html`, replace**
`<!-- Add answer controls here. -->` with:

```html title="starter/templates/index.html"
<section class="practice-step" aria-labelledby="voice-title">
  <div class="step-title"><span class="step-number">01</span><h3 id="voice-title">Say it in your language.</h3></div>
  <p class="muted">Preview locally before sending through Flask and the workshop gateway to MAI. This app does not save recordings. Use synthetic audio unless the instructor has approved microphone guidance.</p>
  <label class="consent-label"><input id="audio-consent" type="checkbox"> I choose to send sample audio under the instructor's approved guidance.</label>
  <div class="record-actions">
    <button id="record-answer" class="button primary" type="button">Record answer</button>
    <button id="stop-recording" class="button secondary" type="button" hidden>Stop recording</button>
    <label class="file-label" for="audio-file">Or choose a synthetic WAV<input id="audio-file" type="file" accept=".wav,audio/wav"></label>
  </div>
  <p id="record-status" class="status" role="status"></p>
  <audio id="audio-preview" controls hidden aria-label="Local audio, not yet sent"></audio>
  <div id="recording-review" class="record-actions" hidden>
    <button id="send-answer" class="button primary" type="button">Send for transcription</button>
    <button id="discard-recording" class="text-button" type="button">Discard recording</button>
  </div>
  <div id="answer-result" class="answer-result" role="status" hidden></div>
  <p class="fine-print">Recognized text is not a pronunciation score.</p>
</section>
```

### 3. Implement capture, conversion, preview, and upload

In **`starter/static/app.js`, insert before `// Start the page.`**

[`MediaRecorder`](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
may not produce WAV. `decodeAudioData` decodes its output;
[`OfflineAudioContext`](https://developer.mozilla.org/en-US/docs/Web/API/OfflineAudioContext)
resamples it to mono at 16 kHz. `encodeWav` writes a 44-byte header and 16-bit
PCM samples. Renaming the original blob would not convert it.

```javascript title="starter/static/app.js"
const MAX_SECONDS = 12;
let activeRecorder = null;
let captureStream = null;
let recordingTimer = null;
let captureAttempt = null;
let pendingAudio = null;
let previewUrl = null;

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

function discardRecording() {
  pendingAudio = null;
  $("#audio-preview").pause();
  $("#audio-preview").removeAttribute("src");
  $("#audio-preview").hidden = true;
  $("#recording-review").hidden = true;
  $("#audio-file").value = "";
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
}

function reviewRecording(blob) {
  discardRecording();
  pendingAudio = blob;
  previewUrl = URL.createObjectURL(blob);
  $("#audio-preview").src = previewUrl;
  $("#audio-preview").hidden = false;
  $("#recording-review").hidden = false;
  $("#record-status").textContent = "Ready to preview locally. Nothing has been sent yet.";
}

function cancelRecording() {
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
  discardRecording();
  $("#record-status").textContent = "Local recording discarded.";
}

async function recordAnswer() {
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
    discardRecording();
    stopPlayback();
    $("#answer-result").hidden = true;
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
      timer = setTimeout(() => {
        if (recorder.state === "recording") recorder.stop();
      }, MAX_SECONDS * 1000);
      recordingTimer = timer;
      await stopped;
      stream.getTracks().forEach((track) => track.stop());
      if (!current()) return;
      $("#record-status").textContent = "Converting to WAV...";
      const wav = await recordingToWav(new Blob(chunks, {type: recorder.mimeType}));
      if (current()) reviewRecording(wav);
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

function showTranscript(heard, word) {
  const result = $("#answer-result");
  result.className = "answer-result";
  result.textContent = `I heard: ${heard}`;
  result.lang = word.locale;
  result.hidden = false;
}

$("#record-answer").addEventListener("click", recordAnswer);
$("#stop-recording").addEventListener("click", () => {
  if (activeRecorder?.state === "recording") activeRecorder.stop();
  else cancelRecording();
});
$("#discard-recording").addEventListener("click", cancelRecording);
$("#audio-consent").addEventListener("change", () => {
  if (!$("#audio-consent").checked) cancelRecording();
});
$("#audio-preview").addEventListener("error", () => showError("The browser could not preview this audio."));
$("#audio-file").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (!file) return;
  runAction("Checking your WAV...", async () => {
    discardRecording();
    $("#answer-result").hidden = true;
    if (file.size > 2 * 1024 * 1024) throw new Error("Choose a WAV smaller than 2 MiB.");
    const header = new Uint8Array(await file.slice(0, 12).arrayBuffer());
    const text = (start, end) => String.fromCharCode(...header.slice(start, end));
    if (header.length !== 12 || text(0, 4) !== "RIFF" || text(8, 12) !== "WAVE") {
      throw new Error("This is not a WAV file. Download a short synthetic sample from the speech buttons.");
    }
    reviewRecording(file);
  });
});
$("#send-answer").addEventListener("click", () => {
  if (!pendingAudio) { showError("Record or choose a WAV first."); return; }
  if (!$("#audio-consent").checked) { showError("Choose whether to send sample audio first."); return; }
  $("#answer-result").hidden = true;
  runAction("MAI is transcribing your sample...", async () => {
    const word = selectedWord();
    const form = new FormData();
    form.append("audio", pendingAudio, "answer.wav");
    form.append("locale", word.locale);
    const response = await callApp("/transcribe", {method: "POST", body: form});
    const result = await appJSON(response);
    if (typeof result.text !== "string" || !result.text.trim()) {
      throw new Error("No usable transcript was returned.");
    }
    showTranscript(result.text, word);
  });
});
window.addEventListener("pagehide", cancelRecording);
```

In the same file, **inside `selectWord`, immediately after `stopPlayback();`,
insert**:

```javascript title="starter/static/app.js"
  discardRecording();
  $("#answer-result").hidden = true;
  $("#record-status").textContent = "";
```

Changing words clears the old recording. Cancelling advances the attempt number
so a late microphone response cannot replace newer work.

**Run:** restart Flask and reload the HTTPS app tab. Select a pair, tick the
audio checkbox, record its translation, stop, and preview. Then press
**Send for transcription**. Network shows multipart `audio`/`locale`; the card
shows **I heard: ...**.

![Recording controls, a local audio preview, and the transcript I heard: pomme.](../assets/workshop/03-transcription.webp){ width="484" loading="lazy" }

*Captured with an example transcript.*

**No microphone?** Choose the synthetic WAV downloaded in lesson 2 and use the
same Send button. If a permission prompt hangs, **Stop recording** unlocks
the file picker. Keep samples within the app's 12-second limit.

## Try one

- Remove `"locales": [language["stt"]],` from `definition` in `starter/app.py`.
  Restart and send the same audio. Compare automatic detection with the hint,
  then restore the line. Keep the expected answer out of recognition hints.
- Compare an isolated word with a short phrase. Does the added context change
  the transcript?

[Next: check the answer](04-check-your-answer.md).
