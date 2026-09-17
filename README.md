# MAI vocabulary workshop

Build a Flask app with bilingual speech, voice answers, and generated memory
images. Each step adds a working feature, then an experiment.

**[Run the workshop](https://jeffrey-groneberg.github.io/the-mai-workshop/)**

## Get going

1. Fork this repository's `main` branch and open a Codespace.
2. Set `APIM_BASE_URL` and `APIM_API_KEY` in Codespaces secrets using the
   instructor's values. [Setup details](docs/getting-ready.md).
3. From the repository root:

```sh
python -m flask --app starter/app.py run --host 0.0.0.0 --port 5050
```

Open port **5050** in your browser. Edit `starter/`; the completed app is in
`solution/`. To run the solution in another terminal:

```sh
python -m flask --app solution/app.py run --host 0.0.0.0 --port 5051
```

## Build

| Step | Result |
| --- | --- |
| [00 — Open the app](docs/lessons/00-open-your-app.md) | Flask serves the page. |
| [01 — Word list](docs/lessons/01-word-list.md) | Add, select, and save word pairs. |
| [02 — Speech](docs/lessons/02-bilingual-speech.md) | Hear English and the translation. |
| [03 — Transcription](docs/lessons/03-record-and-transcribe.md) | Record an answer and see the transcript. |
| [04 — Matching](docs/lessons/04-check-your-answer.md) | Compare the transcript with the saved answer. |
| [05 — Images](docs/lessons/05-memory-images.md) | Generate a visual cue for a word. |

[Optional: mnemonics](docs/extensions/mnemonics.md) ·
[Local setup](docs/local-setup.md) · [API and troubleshooting](docs/reference.md)
