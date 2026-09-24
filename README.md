# MAI vocabulary workshop

Build a Flask app with bilingual speech, voice answers, and generated memory
images. In each step you paste the controls, write the one MAI call yourself
from a short contract, check it, and try an experiment.

**[Run the workshop](https://jeffrey-groneberg.github.io/the-mai-workshop/)**

## Get going

1. Fork this repository's `main` branch and open a Codespace.
2. Get your gateway values from the instructor's event page and set
   `APIM_BASE_URL` and `APIM_API_KEY` as Codespaces secrets.
   [Setup details](docs/getting-ready.md).
3. From the repository root:

```sh
python -m flask --app starter/app.py run --reload --host 0.0.0.0 --port 5050
```

Open port **5050** in your browser. Save a file and reload the browser; Flask
reloads on its own.

You edit three files in `starter/`: `app.py`, `templates/index.html`, and
`static/app.js`. The provided `workshop.py` and `static/workshop.js` handle the
plumbing. Behind? `python checkpoints/restore.py 03` copies a lesson's finished
files over yours. The completed app is in `solution/`:

```sh
python -m flask --app solution/app.py run --reload --host 0.0.0.0 --port 5051
```

## Build

| Step | Result | You write |
| --- | --- | --- |
| [00 — Open the app](docs/lessons/00-open-your-app.md) | Flask serves the page. | — |
| [01 — Word list](docs/lessons/01-word-list.md) | Add, select, and save word pairs. | — |
| [02 — Speech](docs/lessons/02-bilingual-speech.md) | Hear English and the translation. | `/speak` with MAI-Voice-2-Flash |
| [03 — Transcription](docs/lessons/03-record-and-transcribe.md) | Record an answer and see the transcript. | `/transcribe` with MAI-Transcribe-2 |
| [04 — Matching](docs/lessons/04-check-your-answer.md) | Compare the transcript with the saved answer. | `normalizeAnswer` in JavaScript |
| [05 — Images](docs/lessons/05-memory-images.md) | Generate a visual cue for a word. | `/image` with MAI-Image-2.6-Flash |

[Optional: mnemonics](docs/extensions/mnemonics.md) ·
[Compare models and cost](docs/compare-models.md) ·
[Local setup](docs/local-setup.md) · [API and troubleshooting](docs/reference.md)

## Maintainers

The lesson pages are the source of truth. `python tests/lesson_replay.py`
regenerates `checkpoints/` and `solution/` from them; the tests fail if either
drifts. Media: `WORKSHOP_MEDIA_DIR=test-results/workshop-media python -m pytest -q tests/test_lessons.py`.
