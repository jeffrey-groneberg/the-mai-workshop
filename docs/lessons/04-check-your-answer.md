# Check your answer

**What:** show the recognized text, your saved translation, and a clear
match/retry result.

**How and which components:** the existing `/transcribe` response reaches
`showTranscript` in `starter/static/app.js`. JavaScript normalizes and compares
the **whole** transcript with the saved target. HTML displays the result using
the existing CSS. **There is no extra model call, grading prompt, or hidden
pronunciation service.**

## Build it and see it work

In **`starter/static/app.js`, replace the entire `showTranscript(heard, word)`
function** from lesson 3, including its closing `}`, with this block. Leave the
Send handler's `showTranscript(result.text, word)` call unchanged.

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

NFC makes canonically equivalent Unicode spellings comparable. Locale-aware
lowercasing tolerates case differences; the regular expressions remove
**surrounding** punctuation and normalize whitespace. They preserve accents,
internal apostrophes/hyphens, and German `ß` versus `ss`. We do not strip all
non-ASCII characters, search for a matching substring, or accept a whole phrase
just because it contains the expected word.

**Run it end to end:** save JavaScript and reload. Select a pair and use the
record/preview/send flow or the synthetic WAV. Read the heard text **and** saved
answer. For a controlled mismatch, download another word's synthetic target WAV,
select the original pair again, and send the other WAV. A usable different
transcript should show **Not a match this time**. A rejected upload or no-speech
response remains an error, not a mismatch.

A match means only that recognized text matches what you saved. Homophones can
sound alike but have different spellings; the recognizer can choose the wrong
word; your saved translation can be mistaken; several translations may be valid.
Inspect the evidence before correcting the audio or entry. This is **not
pronunciation, accent, or fluency assessment**. Azure's
[pronunciation assessment](https://learn.microsoft.com/azure/ai-services/speech-service/pronunciation-assessment-tool)
is a separate capability not called here. Compare with the
[reference normalization function](https://github.com/jeffrey-groneberg/the-mai-workshop/blob/jeffrey-groneberg-mai-vocabulary-workshop/solution/static/app.js)
if useful.

## Experiment with your working feature

**Try one. Predict -> change -> run -> compare -> choose.**

| Choice | Exact change and interpreting component | Observe and restore |
| --- | --- | --- |
| Strict versus tolerant | In `starter/static/app.js`, change `const matches = actual === expected;` to `const matches = heard === word.target;`. Add a sample entry whose saved target differs from its observed transcript only in case or surrounding punctuation. JavaScript now compares raw strings. | Reload and send the same approved WAV for that entry. Compare strict feedback with the normalized baseline, then restore `actual === expected` unless you intentionally want stricter matching. The displayed transcript reveals whether your test really isolated case/punctuation. |
| Preserve meaning | With the normalizer restored, use an accented example you know. For illustrative French, compare saved `été` with a synthetic recording of `été`, then an entry saved as `ete` using that same WAV. | Send for both entries and inspect the actual transcript. If it says `été`, the accented entry should match and `ete` should not. Keep the meaningful spelling. If recognition changed the spelling, that is a recognition observation, not evidence that accents were removed by this function. |

Each repeated Send is a new transcription request; the comparison itself is
local and deterministic. Restore the normalization baseline before continuing
to [Make a visual memory cue](05-memory-images.md).
