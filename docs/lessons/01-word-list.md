# Make it your vocabulary

Add word pairs, select one to practise, and keep the list after reload.
Flask supplies the language menu; JavaScript renders the list and saves it in
`localStorage`. No model call is needed.

## Build

### 1. Supply the language menu

**Replace all of `starter/app.py`.** Each entry maps a label to a
[documented voice and transcription code](../reference.md#languages-and-voices).
The next lessons use those fields.

```python title="starter/app.py"
from flask import Flask, render_template

app = Flask(__name__)

LANGUAGES = {
    "en-US": {"label": "English (US)", "stt": "en", "voice": "en-US-Harper:MAI-Voice-2-Flash"},
    "zh-CN": {"label": "Chinese (Simplified Mandarin)", "stt": "zh", "voice": "zh-CN-Mei:MAI-Voice-2-Flash"},
    "nl-NL": {"label": "Dutch", "stt": "nl", "voice": "nl-NL-Sander:MAI-Voice-2-Flash"},
    "fr-FR": {"label": "French", "stt": "fr", "voice": "fr-FR-Soleil:MAI-Voice-2-Flash"},
    "de-DE": {"label": "German", "stt": "de", "voice": "de-DE-Mia:MAI-Voice-2-Flash"},
    "hi-IN": {"label": "Hindi", "stt": "hi", "voice": "hi-IN-Kavya:MAI-Voice-2-Flash"},
    "hu-HU": {"label": "Hungarian", "stt": "hu", "voice": "hu-HU-Lilla:MAI-Voice-2-Flash"},
    "it-IT": {"label": "Italian", "stt": "it", "voice": "it-IT-Rosa:MAI-Voice-2-Flash"},
    "ko-KR": {"label": "Korean", "stt": "ko", "voice": "ko-KR-Haena:MAI-Voice-2-Flash"},
    "pt-BR": {"label": "Portuguese (Brazil)", "stt": "pt", "voice": "pt-BR-Luana:MAI-Voice-2-Flash"},
    "pt-PT": {"label": "Portuguese (Portugal)", "stt": "pt", "voice": "pt-PT-Rui:MAI-Voice-2-Flash"},
    "ro-RO": {"label": "Romanian", "stt": "ro", "voice": "ro-RO-Elena:MAI-Voice-2-Flash"},
    "ru-RU": {"label": "Russian", "stt": "ru", "voice": "ru-RU-Masha:MAI-Voice-2-Flash"},
    "es-ES": {"label": "Spanish (Spain)", "stt": "es", "voice": "es-ES-Marta:MAI-Voice-2-Flash"},
    "es-MX": {"label": "Spanish (Mexico)", "stt": "es", "voice": "es-MX-Valeria:MAI-Voice-2-Flash"},
    "th-TH": {"label": "Thai", "stt": "th", "voice": "th-TH-Krit:MAI-Voice-2-Flash"},
    "tr-TR": {"label": "Turkish", "stt": "tr", "voice": "tr-TR-Elif:MAI-Voice-2-Flash"},
}


@app.get("/")
def index():
    return render_template("index.html", languages=LANGUAGES)
```

### 2. Give the list and practice card a home

**Replace all of `starter/templates/index.html`.** Keep the existing CSS.
The comments mark where later controls will go.

```html title="starter/templates/index.html"
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>My words | MAI Workshop</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  <script src="{{ url_for('static', filename='app.js') }}" defer></script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to your words</a>
  <header class="site-header">
    <a class="brand" href="/">MAI <span>WORKSHOP</span></a>
    <span class="eyebrow">YOUR APP</span>
  </header>
  <main id="main" class="app-shell">
    <section class="intro">
      <h1>A little vocabulary.<br>A world to explore.</h1>
      <p class="intro-copy">Choose a language. Keep a word. Make it yours.</p>
    </section>
    <p id="app-error" class="notice error-notice" role="alert" hidden></p>
    <div class="workspace">
      <section class="panel vocabulary-panel" aria-labelledby="list-title">
        <h2 id="list-title">Words worth keeping.</h2>
        <form id="word-form">
          <label for="target-locale">I want to practise</label>
          <select id="target-locale" required>
            <option value="">Choose a target language</option>
            {% for locale, language in languages.items() %}
            {% if locale != 'en-US' %}<option value="{{ locale }}">{{ language.label }}</option>{% endif %}
            {% endfor %}
          </select>
          <div class="input-pair">
            <div><label for="english-word">English word</label><input id="english-word" maxlength="120" placeholder="apple" required></div>
            <div><label for="target-word">Your translation</label><input id="target-word" maxlength="120" placeholder="Your word" required></div>
          </div>
          <button class="button primary" type="submit">Add to my words</button>
        </form>
        <div class="list-heading"><span class="eyebrow">YOUR WORDS</span><span id="word-count" class="count">0</span></div>
        <ul id="word-list" class="word-list" aria-label="Saved vocabulary"></ul>
        <p id="list-empty" class="muted">Your list stays in this browser, at this app address.</p>
        <button id="reset-storage" class="text-button" type="button" hidden>Clear unreadable saved data</button>
      </section>
      <section class="panel practice-panel" aria-label="Practise your selected word">
        <div id="practice-empty" class="empty-state"><h2>Start with a word.</h2><p>Add a pair, then choose it in your list.</p></div>
        <div id="practice-content" hidden>
          <div class="word-heading">
            <p id="practice-language" class="eyebrow"></p>
            <h2 id="practice-word" lang="en"></h2>
            <button id="reveal-answer" class="text-button" type="button">Show / hide translation</button>
            <p id="saved-translation" class="translation" hidden></p>
          </div>
          <!-- Add speech controls here. -->
          <!-- Add answer controls here. -->
          <!-- Add memory controls here. -->
          <!-- Add mnemonic controls here. -->
        </div>
        <p id="model-status" class="status" role="status"></p>
      </section>
    </div>
  </main>
  <footer class="site-footer"><span>MAI Workshop</span><p>Use sample data only.</p></footer>
</body>
</html>
```

### 3. Implement saving, selection, and rendering

**Replace all of `starter/static/app.js`.** The form handler creates a pair;
`renderList` draws it; `saveWords` persists it. `textContent` displays entered
words as text.

```javascript title="starter/static/app.js"
"use strict";

const $ = (selector) => document.querySelector(selector);
const STORAGE_KEY = "mai-learner-words-v1";
let words = [];
let selectedId = null;
let storageReadable = true;

function showError(message) {
  $("#app-error").textContent = message;
  $("#app-error").hidden = !message;
}

function selectedWord() {
  return words.find((word) => word.id === selectedId);
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
      selectWord(word.id === selectedId ? words[0]?.id ?? null : selectedId);
    });
    row.append(pick, remove);
    $("#word-list").append(row);
  }
  $("#word-count").textContent = String(words.length);
  $("#list-empty").hidden = words.length > 0;
}

function selectWord(id) {
  selectedId = id;
  const word = selectedWord();
  $("#practice-empty").hidden = Boolean(word);
  $("#practice-content").hidden = !word;
  if (word) {
    $("#practice-word").textContent = word.english;
    $("#saved-translation").textContent = word.target;
    $("#saved-translation").lang = word.locale;
    $("#saved-translation").hidden = true;
    $("#practice-language").textContent = [...$("#target-locale").options]
      .find((option) => option.value === word.locale).textContent;
  }
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
  $("#saved-translation").hidden = !$("#saved-translation").hidden;
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

// Start the page.
loadWords();
selectWord(words[0]?.id ?? null);
```

Keep `// Start the page.` and its calls **last** so initialization runs after
all state and handlers are defined.

**Run:** restart Flask and reload. Add two pairs, select each, reveal the
translation, then reload again. Both pairs should remain. Remove one.
To correct a pair, remove it and add it again.

![A saved apple and pomme word pair selected in the learner's vocabulary list.](../assets/workshop/01-word-list.webp){ width="960" loading="lazy" }

## Try one

- Add a pair in another language. Switch between entries: each keeps its own
  locale; changing the menu does not translate existing words.
- Add `summer` / `été` in French, or a non-Latin word you know. Reload and check
  that the spelling survives storage.

[Next: hear both languages](02-bilingual-speech.md).
