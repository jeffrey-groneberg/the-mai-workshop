"use strict";
// Your browser code. workshop.js loads first and provides $, showError,
// runAction, callApp, and the other helpers listed in the reference.

const STORAGE_KEY = "mai-learner-words-v1";
const wordChangeHooks = [];
let words = [];
let selectedId = null;
let storageReadable = true;

function selectedWord() {
  return words.find((word) => word.id === selectedId);
}

function onWordChange(hook) {
  wordChangeHooks.push(hook);
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
      throw new Error("Invalid saved vocabulary");
    }
    words = saved;
  } catch {
    storageReadable = false;
    $("#reset-storage").hidden = false;
    showError("Saved vocabulary is unreadable or storage is blocked. Nothing was overwritten.");
  }
}

function saveWords(nextWords) {
  if (!storageReadable) {
    showError("Clear the unreadable data explicitly before saving a new list.");
    return false;
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextWords));
    words = nextWords;
    return true;
  } catch {
    showError("This browser could not save the change. Check its storage/privacy settings.");
    return false;
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
    remove.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" ' +
      'fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">' +
      '<path d="M6 6l12 12M18 6L6 18"/></svg>';
    remove.setAttribute("aria-label", `Remove ${word.english}`);
    remove.addEventListener("click", () => {
      if (!saveWords(words.filter((item) => item.id !== word.id))) return;
      if (word.id === selectedId) selectWord(words[0]?.id ?? null);
      else renderList();
    });
    row.append(pick, remove);
    $("#word-list").append(row);
  }
  $("#word-count").textContent = String(words.length);
  $("#list-empty").hidden = words.length > 0;
}

function selectWord(id) {
  if (isBusy()) {
    showError("Wait for the current action to finish.");
    return;
  }
  selectedId = id;
  const word = selectedWord();
  $("#practice-empty").hidden = Boolean(word);
  $("#practice-content").hidden = !word;
  if (word) {
    $("#practice-word").textContent = word.english;
    $("#saved-translation").textContent = word.target;
    $("#saved-translation").lang = word.locale;
    $("#saved-translation").hidden = true;
    $("#reveal-answer").textContent = "Reveal translation";
    $("#practice-language").textContent = [...$("#target-locale").options]
      .find((option) => option.value === word.locale).textContent;
  }
  wordChangeHooks.forEach((hook) => hook(word));
  renderList();
}

$("#word-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const english = $("#english-word").value.trim();
  const target = $("#target-word").value.trim();
  const locale = $("#target-locale").value;
  if (!english || !target || !locale) {
    showError("Choose a language and enter both words.");
    return;
  }
  const word = {id: crypto.randomUUID(), english, target, locale};
  if (!saveWords([...words, word])) return;
  showError("");
  $("#english-word").value = "";
  $("#target-word").value = "";
  selectWord(word.id);
  $("#english-word").focus();
});

$("#reveal-answer").addEventListener("click", () => {
  const hidden = !$("#saved-translation").hidden;
  $("#saved-translation").hidden = hidden;
  $("#reveal-answer").textContent = hidden ? "Reveal translation" : "Hide translation";
});

$("#reset-storage").addEventListener("click", () => {
  if (!confirm("Clear this app's unreadable saved vocabulary?")) return;
  try {
    localStorage.removeItem(STORAGE_KEY);
    words = [];
    storageReadable = true;
    $("#reset-storage").hidden = true;
    showError("");
    selectWord(null);
  } catch {
    showError("Storage is still blocked. Check the browser's privacy settings.");
  }
});

const speechCache = new Map();

async function speechBlob(text, locale) {
  const key = JSON.stringify([text, locale]);
  if (!speechCache.has(key)) {
    const response = await callApp("/speak", jsonOptions({text, locale}));
    if (!response.headers.get("Content-Type")?.includes("audio/wav")) {
      throw new Error("Expected WAV audio. Reopen the app if Codespaces sign-in expired.");
    }
    speechCache.set(key, await response.blob());
  }
  return speechCache.get(key);
}

$("#speak-english").addEventListener("click", () => {
  const word = selectedWord();
  runAction("Asking MAI Voice for English audio...", async () => {
    await playAudio($("#speech-audio"), await speechBlob(word.english, "en-US"));
  });
});
$("#speak-target").addEventListener("click", () => {
  const word = selectedWord();
  runAction("Asking MAI Voice for your translation...", async () => {
    await playAudio($("#speech-audio"), await speechBlob(word.target, word.locale));
  });
});
$("#download-sample").addEventListener("click", () => {
  const word = selectedWord();
  runAction("Preparing synthetic target-language audio...", async () => {
    downloadBlob(await speechBlob(word.target, word.locale), `sample-${word.locale}.wav`);
  });
});
onWordChange(() => stopAudio($("#speech-audio")));
window.addEventListener("pagehide", () => stopAudio($("#speech-audio")));

const recorder = setupAnswerRecorder({
  onNewAudio: () => {
    stopAudio($("#speech-audio"));
    $("#answer-result").hidden = true;
  },
});

// Lesson 4: replace from this line to the matching end line.
function showTranscript(heard, word) {
  const result = $("#answer-result");
  result.className = "answer-result";
  result.textContent = `I heard: ${heard}`;
  result.lang = word.locale;
  result.hidden = false;
}
// Lesson 4: replace to this line.

$("#send-answer").addEventListener("click", () => {
  const audio = recorder.audio();
  if (!audio) { showError("Record or choose a WAV first."); return; }
  if (!$("#audio-consent").checked) { showError("Choose whether to send sample audio first."); return; }
  const word = selectedWord();
  $("#answer-result").hidden = true;
  runAction("MAI is transcribing your sample...", async () => {
    const form = new FormData();
    form.append("audio", audio, "answer.wav");
    form.append("locale", word.locale);
    const result = await appJSON(await callApp("/transcribe", {method: "POST", body: form}));
    if (typeof result.text !== "string" || !result.text.trim()) {
      throw new Error("No usable transcript was returned.");
    }
    if (recorder.audio() === audio) showTranscript(result.text, word);
  });
});
onWordChange(() => {
  recorder.discard();
  $("#answer-result").hidden = true;
});

// Lesson 5: add memory images here.

// Extension: add mnemonics here.

// Start the page.
loadWords();
selectWord(words[0]?.id ?? null);
