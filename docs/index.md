# Build a vocabulary app with MAI

Use Flask and browser JavaScript to add speech, voice answers, and memory images
to a vocabulary list.

**[Set up your Codespace](getting-ready.md)**, then follow the steps below.
Work in `starter/`; compare with `solution/`. After each working feature,
try one of its experiments.

<details open>
<summary>See the app in action</summary>
<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="assets/workshop/walkthrough-poster.webp">
  <img src="assets/workshop/app-walkthrough.gif" width="880" height="644" alt="App walkthrough: add a French word pair, hear both languages, record and match an answer, generate an image, and request a mnemonic." loading="lazy">
</picture>
<p>Silent walkthrough with example model responses. Plays once; close this panel to hide it.</p>
</details>

| Step | What you build |
| --- | --- |
| [00 — Open the app](lessons/00-open-your-app.md) | A page served by Flask. |
| [01 — Word list](lessons/01-word-list.md) | Word pairs saved in the browser. |
| [02 — Speech](lessons/02-bilingual-speech.md) | English and target-language playback. |
| [03 — Transcription](lessons/03-record-and-transcribe.md) | Recording, WAV conversion, and recognized text. |
| [04 — Matching](lessons/04-check-your-answer.md) | Feedback on the spoken answer. |
| [05 — Images](lessons/05-memory-images.md) | A generated visual cue for each word. |

Next: [add MAI-Thinking mnemonics](extensions/mnemonics.md).

## Which models you use

![Speech playback uses MAI-Voice-2-Flash; transcription uses MAI-Transcribe-2; images use MAI-Image-2.6-Flash; optional mnemonics use MAI-Thinking-1. Saving words and matching answers use JavaScript, not a model.](assets/diagrams/feature-model-map.webp){ width="960" height="549" loading="lazy" }

*MAI-generated diagram. [Full size](assets/diagrams/feature-model-map.webp) · [Prompts and revisions](assets/diagrams/provenance.json).*

Speech reads your saved text; it does not translate it.

[Explore the MAI family and compare costs](compare-models.md).

[Local setup](local-setup.md) · [API and troubleshooting](reference.md)
