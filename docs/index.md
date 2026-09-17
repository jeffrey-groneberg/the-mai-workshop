# MAI Vocabulary Workshop

Build a small Flask vocabulary app, one working feature at a time. Save English
words and their translations, hear both languages, record an answer, check the
recognized text, and generate a visual memory cue.

**[Start with readiness pre-work](getting-ready.md)**, then
[open your app](lessons/00-open-your-app.md).

You need basic Python and HTML. The guided session has a **two-hour target**;
environment setup is pre-work, and the pacing still needs a representative
learner pilot.

## How each lesson works

1. **Understand:** what you are adding, how it works, and which components take part.
2. **Build and run:** make small edits and see the complete feature work in your browser.
3. **Experiment:** choose one option, predict the result, change it, run again, and compare.

Your working app is the checkpoint. Looking at the finished solution does not
replace implementing the feature yourself.

## Follow the workshop

| Lesson | What works at the end |
| --- | --- |
| [00 — Open your app](lessons/00-open-your-app.md) | A running starter and a separately accessible finished reference. |
| [01 — Your word list](lessons/01-word-list.md) | Your own word pairs, target-language choice, and browser persistence. |
| [02 — Hear both languages](lessons/02-bilingual-speech.md) | English and target-language playback through MAI Voice. |
| [03 — Record and transcribe](lessons/03-record-and-transcribe.md) | Recording, genuine WAV conversion, local preview, and explicit transcription. |
| [04 — Check your answer](lessons/04-check-your-answer.md) | The recognized text compared with your saved translation. |
| [05 — Make memory images](lessons/05-memory-images.md) | An on-demand picture and the complete practice loop. |

After the core, try the optional
[MAI-Thinking mnemonic lab](extensions/mnemonics.md).

## Know where you are working

| Location | Purpose |
| --- | --- |
| `starter/` — port 5050 | Your app. Edit these files during the lessons. |
| `solution/` — port 5051 | The finished reference. Run it separately to compare behavior. |
| GitHub Pages | This static workshop guide, not a Flask server. |
| Port 8000 | An optional local preview of the guide. |

Each app has four main files: `app.py`, `templates/index.html`,
`static/app.js`, and `static/style.css`. There is no frontend build system,
database, or hidden provider framework.

Codespaces is the recommended environment. Follow the
[Codespaces setup](getting-ready.md#create-the-codespace) using the default
`main` branch. If Codespaces is unavailable, use the same app through
[local setup](local-setup.md).

## Important boundaries

- Keep **both** `APIM_BASE_URL` and `APIM_API_KEY` in private server-side
  configuration. Never commit or publish their values.
- Use approved sample data. Microphone participation is voluntary; a synthetic
  WAV alternative is provided.
- Matching recognized text is **not** pronunciation assessment or verification
  that your saved translation is correct.

Use the [reference](reference.md) for API details and troubleshooting, and the
[instructor guide](instructor.md) for access, data guidance, and classroom readiness.

## From a word to a visual cue

![Watercolor of an apple, an open notebook, and sound waves leading toward a landscape.](assets/images/vocabulary-journey.webp){ width="640" height="366" loading="lazy" }

*AI-generated teaching illustration, not a live app result.
[Image provenance](assets/images/provenance.json).*
