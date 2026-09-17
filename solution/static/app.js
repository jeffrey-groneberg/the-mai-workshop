"use strict";

const $ = (selector) => document.querySelector(selector);
const STORAGE_KEY = "mai-vocabulary-v1";
const MAX_SECONDS = 12;
const words = [];
let selectedId = null;
let version = 0;
let requestController = null;
let audioPlayer = null;
let recorder = null;
let recordingTimer = null;
let pendingAudio = null;
let previewUrl = null;
let storageReadable = true;
const speechCache = new Map();
const memoryImages = new Map();

function showError(message) {
  $("#app-error").textContent = message;
  $("#app-error").hidden = !message;
}

function selectedWord() {
  return words.find((word) => word.id === selectedId);
}

function saveWords() {
  if (!storageReadable) {
    showError("Saved data could not be read. Clear it explicitly before saving a new list.");
    return false;
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(words));
    return true;
  } catch {
    showError("This browser could not save your words. They remain available until you close this page.");
    return false;
  }
}

function loadWords() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    const locales = [...$("#target-locale").options].map((option) => option.value).filter(Boolean);
    if (!Array.isArray(saved) || saved.some((word) =>
      !word || typeof word.id !== "string" ||
      typeof word.english !== "string" || !word.english.trim() || word.english.length > 120 ||
      typeof word.target !== "string" || !word.target.trim() || word.target.length > 120 ||
      !locales.includes(word.locale)
    ) || new Set(saved.map((word) => word.id)).size !== saved.length) {
      throw new Error("Unreadable vocabulary");
    }
    words.push(...saved);
  } catch {
    storageReadable = false;
    $("#reset-storage").hidden = false;
    showError("Your saved list is unreadable or storage is blocked. Nothing has been overwritten.");
  }
}

function discardRecording() {
  pendingAudio = null;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;
  $("#audio-preview").pause();
  $("#audio-preview").removeAttribute("src");
  $("#audio-preview").hidden = true;
  $("#recording-review").hidden = true;
  $("#audio-file").value = "";
}

function cancelActivity() {
  version += 1;
  requestController?.abort();
  requestController = null;
  audioPlayer?.pause();
  if (recorder?.state === "recording") recorder.stop();
  clearTimeout(recordingTimer);
  $("#record-answer").disabled = false;
  document.querySelectorAll(".listen-actions button, #send-answer, #generate-image, #generate-mnemonic")
    .forEach((button) => { button.disabled = false; });
  $("#stop-recording").hidden = true;
  $("#record-status").textContent = "";
  $("#model-status").textContent = "";
  $("#image-status").textContent = "";
  $("#answer-result").hidden = true;
  discardRecording();
}

function selectWord(id) {
  cancelActivity();
  selectedId = id;
  const word = selectedWord();
  $("#practice-empty").hidden = Boolean(word);
  $("#practice-content").hidden = !word;
  $("#answer-result").hidden = true;
  $("#mnemonic-result").textContent = "";
  if (word) {
    $("#practice-word").textContent = word.english;
    $("#saved-translation").textContent = word.target;
    $("#saved-translation").lang = word.locale;
    $("#saved-translation").hidden = true;
    $("#reveal-answer").textContent = "Reveal translation";
    $("#practice-language").textContent = [...$("#target-locale").options]
      .find((option) => option.value === word.locale).textContent;
  }
  renderMemory();
  renderList();
}

function renderMemory() {
  const saved = memoryImages.get(selectedId);
  $("#image-mount").replaceChildren();
  $("#memory-figure").hidden = !saved;
  $("#image-detail").value = saved?.detail ?? "";
  $("#generate-image").textContent = saved ? "Generate a new image" : "Make a memory image";
  if (saved) {
    const picture = new Image();
    picture.id = "memory-image";
    picture.alt = `Generated visual cue for ${saved.english}`;
    picture.src = saved.url;
    $("#image-mount").append(picture);
  }
}

function renderList() {
  $("#word-list").replaceChildren();
  for (const word of words) {
    const row = document.createElement("li");
    const pick = document.createElement("button");
    pick.type = "button";
    pick.className = "word-choice";
    pick.textContent = `${word.english} / ${word.locale}`;
    pick.setAttribute("aria-pressed", String(word.id === selectedId));
    pick.addEventListener("click", () => selectWord(word.id));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "remove-word";
    remove.textContent = "\u00d7";
    remove.setAttribute("aria-label", `Remove ${word.english}`);
    remove.addEventListener("click", () => {
      const saved = memoryImages.get(word.id);
      if (saved) URL.revokeObjectURL(saved.url);
      memoryImages.delete(word.id);
      words.splice(words.indexOf(word), 1);
      saveWords();
      if (word.id === selectedId) selectWord(words[0]?.id ?? null);
      else renderList();
    });
    row.append(pick, remove);
    $("#word-list").append(row);
  }
  $("#word-count").textContent = String(words.length);
  $("#list-empty").hidden = words.length > 0;
}

async function callApp(path, options, signal) {
  let response;
  try {
    response = await fetch(path, {...options, signal});
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error("Cannot reach Flask. Check the server, or reopen the private Codespaces port and sign in.");
  }
  if (!response.ok) {
    let message = `Request failed (${response.status}). Reopen the app if your Codespaces sign-in expired.`;
    if (response.headers.get("Content-Type")?.includes("application/json")) {
      const body = await response.json();
      if (typeof body.error === "string") message = body.error;
    }
    const retry = response.headers.get("Retry-After");
    if (retry && /^\d+$/.test(retry)) message += ` Retry after ${retry} seconds.`;
    throw new Error(message);
  }
  return response;
}

function jsonOptions(body) {
  return {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)};
}

async function runAction(button, message, action) {
  if (requestController || !selectedWord()) return;
  showError("");
  const currentVersion = version;
  const controller = new AbortController();
  requestController = controller;
  document.querySelectorAll(".listen-actions button, #send-answer, #generate-image, #generate-mnemonic")
    .forEach((control) => { control.disabled = true; });
  $("#model-status").textContent = message;
  try {
    await action(controller.signal, currentVersion);
  } catch (error) {
    if (error.name !== "AbortError" && currentVersion === version) showError(error.message);
  } finally {
    if (requestController === controller) {
      document.querySelectorAll(".listen-actions button, #send-answer, #generate-image, #generate-mnemonic")
        .forEach((control) => { control.disabled = false; });
      requestController = null;
      $("#model-status").textContent = "";
    }
  }
}

async function speechBlob(text, locale, signal) {
  const key = JSON.stringify([text, locale]);
  if (!speechCache.has(key)) {
    const response = await callApp("/speak", jsonOptions({text, locale}), signal);
    if (!response.headers.get("Content-Type")?.includes("audio/wav")) {
      throw new Error("Expected WAV audio. Reopen the app if your Codespaces sign-in expired.");
    }
    speechCache.set(key, await response.blob());
  }
  return speechCache.get(key);
}

function playWord(target) {
  const button = $(target ? "#speak-target" : "#speak-english");
  runAction(button, "Asking MAI Voice to read your word...", async (signal, currentVersion) => {
    const word = selectedWord();
    const blob = await speechBlob(target ? word.target : word.english, target ? word.locale : "en-US", signal);
    if (version !== currentVersion) return;
    audioPlayer?.pause();
    const url = URL.createObjectURL(blob);
    const player = new Audio(url);
    audioPlayer = player;
    const release = () => URL.revokeObjectURL(url);
    player.addEventListener("ended", release, {once: true});
    player.addEventListener("error", () => {
      release();
      if (version === currentVersion) showError("The browser could not play the returned WAV.");
    }, {once: true});
    player.addEventListener("pause", release, {once: true});
    try { await player.play(); } catch { release(); throw new Error("Playback was blocked. Try the speaker button again."); }
  });
}

function encodeWav(samples, sampleRate = 16000) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeText = (offset, text) => [...text].forEach((char, index) => view.setUint8(offset + index, char.charCodeAt(0)));
  writeText(0, "RIFF"); view.setUint32(4, 36 + samples.length * 2, true);
  writeText(8, "WAVE"); writeText(12, "fmt "); view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  writeText(36, "data"); view.setUint32(40, samples.length * 2, true);
  samples.forEach((sample, index) => {
    const clamped = Math.max(-1, Math.min(1, sample));
    view.setInt16(44 + index * 2, clamped * (clamped < 0 ? 32768 : 32767), true);
  });
  return new Blob([buffer], {type: "audio/wav"});
}

async function recordingToWav(blob) {
  const context = new AudioContext();
  let decoded;
  try {
    decoded = await context.decodeAudioData(await blob.arrayBuffer());
  } finally {
    await context.close();
  }
  const frames = Math.min(Math.ceil(decoded.duration * 16000), MAX_SECONDS * 16000);
  if (!frames) throw new Error("The recording is empty. Try again.");
  const offline = new OfflineAudioContext(1, frames, 16000);
  const source = offline.createBufferSource();
  source.buffer = decoded;
  source.connect(offline.destination);
  source.start();
  const mono = await offline.startRendering();
  return encodeWav(mono.getChannelData(0));
}

function reviewRecording(blob) {
  cancelActivity();
  pendingAudio = blob;
  previewUrl = URL.createObjectURL(blob);
  $("#audio-preview").src = previewUrl;
  $("#audio-preview").hidden = false;
  $("#recording-review").hidden = false;
  $("#record-status").textContent = "Ready to preview. Nothing has been sent yet.";
}

async function recordAnswer() {
  if (!selectedWord()) return;
  if (!$("#audio-consent").checked) { showError("Read the audio guidance and choose whether to participate first."); return; }
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    showError("Recording is unavailable. Open the HTTPS app in a normal browser tab, or choose a synthetic WAV.");
    return;
  }
  showError("");
  cancelActivity();
  const currentVersion = version;
  $("#record-answer").disabled = true;
  $("#stop-recording").hidden = false;
  $("#record-status").textContent = "Waiting for microphone permission...";
  let stream = null;
  let activeRecorder = null;
  try {
    stream = await navigator.mediaDevices.getUserMedia({audio: true});
    if (version !== currentVersion) { stream.getTracks().forEach((track) => track.stop()); return; }
    activeRecorder = new MediaRecorder(stream);
    recorder = activeRecorder;
    const chunks = [];
    activeRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size) chunks.push(event.data);
    });
    const stopped = new Promise((resolve, reject) => {
      activeRecorder.addEventListener("stop", resolve, {once: true});
      activeRecorder.addEventListener("error", () => reject(new Error("Recording failed.")), {once: true});
    });
    activeRecorder.start();
    $("#record-status").textContent = `Recording locally. Stops after ${MAX_SECONDS} seconds.`;
    recordingTimer = setTimeout(() => {
      if (activeRecorder.state === "recording") activeRecorder.stop();
    }, MAX_SECONDS * 1000);
    await stopped;
    stream.getTracks().forEach((track) => track.stop());
    if (version !== currentVersion) return;
    $("#record-status").textContent = "Converting your recording to WAV...";
    const wav = await recordingToWav(new Blob(chunks, {type: activeRecorder.mimeType}));
    if (version === currentVersion) reviewRecording(wav);
  } catch (error) {
    if (version === currentVersion) {
      showError(error.name === "NotAllowedError"
        ? "Microphone access was declined. You can use a synthetic WAV instead."
        : "Recording or WAV conversion failed. Check your microphone or choose a synthetic WAV.");
      $("#record-status").textContent = "";
    }
  } finally {
    stream?.getTracks().forEach((track) => track.stop());
    if (recorder === activeRecorder) { recorder = null; clearTimeout(recordingTimer); }
    if (version === currentVersion) {
      $("#record-answer").disabled = false;
      $("#stop-recording").hidden = true;
    }
  }
}

function normalizeAnswer(text, locale) {
  return text.normalize("NFC").toLocaleLowerCase(locale).normalize("NFC")
    .trim().replace(/^[\p{P}\s]+|[\p{P}\s]+$/gu, "").replace(/\s+/gu, " ");
}

function showMatch(heard, word) {
  const recognized = normalizeAnswer(heard, word.locale);
  const expectedText = normalizeAnswer(word.target, word.locale);
  const matches = Boolean(recognized && expectedText && recognized === expectedText);
  const result = $("#answer-result");
  result.className = `answer-result ${matches ? "matched" : "try-again"}`;
  result.replaceChildren();
  const heading = document.createElement("strong");
  heading.textContent = matches ? "That matches your saved translation." : "Not a match this time.";
  const transcript = document.createElement("p");
  transcript.textContent = `I heard: ${heard}`;
  transcript.lang = word.locale;
  const expected = document.createElement("p");
  expected.textContent = `Saved answer: ${word.target}`;
  expected.lang = word.locale;
  const caveat = document.createElement("p");
  caveat.textContent = "Did it hear you correctly? Recognition and saved translations can both be wrong.";
  result.append(heading, transcript, expected, caveat);
  result.hidden = false;
}

$("#word-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const english = $("#english-word").value.trim();
  const target = $("#target-word").value.trim();
  const locale = $("#target-locale").value;
  if (!english || !target || !locale) { showError("Choose a target language and enter both words."); return; }
  if (!normalizeAnswer(english, "en-US") || !normalizeAnswer(target, locale)) {
    showError("Enter words, not only punctuation."); return;
  }
  showError("");
  const word = {id: crypto.randomUUID(), english, target, locale};
  words.push(word);
  saveWords();
  $("#english-word").value = "";
  $("#target-word").value = "";
  selectWord(word.id);
  $("#english-word").focus();
});
$("#reset-storage").addEventListener("click", () => {
  if (!confirm("Clear the unreadable vocabulary stored for this app?")) return;
  try {
    localStorage.removeItem(STORAGE_KEY);
    storageReadable = true;
    $("#reset-storage").hidden = true;
    showError("");
    saveWords();
  } catch { showError("Browser storage is still unavailable. Check its privacy settings."); }
});
$("#reveal-answer").addEventListener("click", () => {
  $("#saved-translation").hidden = !$("#saved-translation").hidden;
  $("#reveal-answer").textContent = $("#saved-translation").hidden ? "Reveal translation" : "Hide translation";
});
$("#speak-english").addEventListener("click", () => playWord(false));
$("#speak-target").addEventListener("click", () => playWord(true));
$("#download-sample").addEventListener("click", () => {
  runAction($("#download-sample"), "Preparing synthetic target-language audio...", async (signal, currentVersion) => {
    const word = selectedWord();
    const blob = await speechBlob(word.target, word.locale, signal);
    if (version !== currentVersion) return;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `sample-${word.locale}.wav`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
});
$("#record-answer").addEventListener("click", recordAnswer);
$("#stop-recording").addEventListener("click", () => {
  if (recorder?.state === "recording") recorder.stop();
  else cancelActivity();
});
$("#discard-recording").addEventListener("click", () => {
  cancelActivity();
  $("#record-status").textContent = "Recording discarded.";
});
$("#audio-consent").addEventListener("change", () => {
  if (!$("#audio-consent").checked) cancelActivity();
});
$("#audio-file").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (!file) return;
  if (file.size > 2 * 1024 * 1024) { showError("Choose a WAV smaller than 2 MiB."); event.target.value = ""; return; }
  reviewRecording(file);
});
$("#send-answer").addEventListener("click", () => {
  if (!pendingAudio) return;
  if (!$("#audio-consent").checked) { showError("Choose whether to send sample audio before continuing."); return; }
  $("#answer-result").hidden = true;
  runAction($("#send-answer"), "MAI is listening to your sample...", async (signal, currentVersion) => {
    const word = selectedWord();
    const form = new FormData();
    form.append("audio", pendingAudio, "answer.wav");
    form.append("locale", word.locale);
    const response = await callApp("/transcribe", {method: "POST", body: form}, signal);
    const result = await response.json();
    if (typeof result.text !== "string" || !result.text.trim()) throw new Error("No usable transcript was returned.");
    if (version === currentVersion) showMatch(result.text, word);
  });
});
$("#generate-image").addEventListener("click", () => {
  runAction($("#generate-image"), "MAI Image is creating a visual cue...", async (signal, currentVersion) => {
    const word = selectedWord();
    const detail = $("#image-detail").value.trim();
    const response = await callApp("/image", jsonOptions({word: word.english, detail}), signal);
    if (!response.headers.get("Content-Type")?.includes("image/png")) throw new Error("The response was not a PNG image.");
    const url = URL.createObjectURL(await response.blob());
    const picture = new Image();
    picture.id = "memory-image";
    picture.alt = `Generated visual cue for ${word.english}`;
    picture.src = url;
    try { await picture.decode(); } catch { URL.revokeObjectURL(url); throw new Error("The generated image could not be displayed."); }
    if (version !== currentVersion) { URL.revokeObjectURL(url); return; }
    const previous = memoryImages.get(word.id);
    if (previous) URL.revokeObjectURL(previous.url);
    memoryImages.set(word.id, {url, detail, english: word.english});
    $("#image-mount").replaceChildren(picture);
    $("#memory-figure").hidden = false;
    $("#generate-image").textContent = "Generate a new image";
    $("#image-status").textContent = "Every new image is another model request. Try changing the scene.";
  });
});
$("#generate-mnemonic").addEventListener("click", () => {
  runAction($("#generate-mnemonic"), "MAI Thinking is considering your word...", async (signal, currentVersion) => {
    const response = await callApp("/mnemonic", jsonOptions({word: selectedWord().english}), signal);
    const result = await response.json();
    if (typeof result.text !== "string") throw new Error("No mnemonic text was returned.");
    if (version === currentVersion) $("#mnemonic-result").textContent = result.text;
  });
});
window.addEventListener("pagehide", (event) => {
  cancelActivity();
  if (!event.persisted) {
    memoryImages.forEach((image) => URL.revokeObjectURL(image.url));
    memoryImages.clear();
    speechCache.clear();
  }
});
loadWords();
selectWord(words[0]?.id ?? null);
