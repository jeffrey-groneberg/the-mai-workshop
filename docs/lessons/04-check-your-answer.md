# Check your answer

Compare the transcript with the saved translation and show match/retry feedback.
JavaScript handles this in `showTranscript`; no extra model call is needed.

## Build

In **`starter/static/app.js`, replace the entire `showTranscript(heard, word)`
function**, including its closing `}`, with this block. Keep the Send handler
unchanged.

```javascript title="starter/static/app.js"
function normalizeAnswer(text, locale) {
  return text.normalize("NFC").toLocaleLowerCase(locale).trim()
    .replace(/^[\p{P}\s]+|[\p{P}\s]+$/gu, "").replace(/\s+/gu, " ");
}

function showTranscript(heard, word) {
  const actual = normalizeAnswer(heard, word.locale);
  const expected = normalizeAnswer(word.target, word.locale);
  if (!actual) throw new Error("The transcript contains no usable words. Try another sample.");
  if (!expected) throw new Error("Your saved translation needs words, not only punctuation.");
  const matches = actual === expected;
  const result = $("#answer-result");
  result.className = `answer-result ${matches ? "matched" : "try-again"}`;
  result.removeAttribute("lang");
  const heading = document.createElement("strong");
  heading.textContent = matches ? "That matches your saved translation." : "Not a match this time.";
  const transcript = document.createElement("p");
  transcript.textContent = `I heard: ${heard}`;
  transcript.lang = word.locale;
  const saved = document.createElement("p");
  saved.textContent = `Saved answer: ${word.target}`;
  saved.lang = word.locale;
  const caveat = document.createElement("p");
  caveat.textContent = "Did it hear you correctly? Recognition and saved translations can both be wrong.";
  result.replaceChildren(heading, transcript, saved, caveat);
  result.hidden = false;
}
```

Normalization tolerates case, surrounding punctuation, and extra spaces while
preserving accents and internal punctuation. It compares whole strings, not
substrings. This checks the recognized word, not pronunciation quality.

**Run:** reload and send an answer. Then send a different word's WAV against the
same entry. Confirm the heard/saved text and the match versus retry result.

## Try one

- Replace `const matches = actual === expected;` with
  `const matches = heard === word.target;`. Reload and resend audio whose
  transcript differs only in case/punctuation. Compare, then restore normalization.
- Compare saved `été` and `ete` against the same French audio. If the transcript
  is `été`, only the accented entry should match.

[Next: generate a memory image](05-memory-images.md).
