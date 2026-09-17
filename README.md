# Word by word: a MAI workshop

Build a small vocabulary app with Flask, plain JavaScript, and Microsoft's MAI
models. Save English words and your translations, hear both languages, record
and transcribe an answer, compare the recognized text, and generate a visual
memory cue.

**The target is a two-hour participant session, selected by the workshop
owner. It is not a validated pacing claim.** Environment readiness is pre-work.
The guided core includes implementing both the word list and browser recording /
WAV conversion, plus one experiment after every working checkpoint. A
representative learner-paced pilot is still needed; agent execution speed does
not establish a classroom fit.

## Start here

Complete [readiness pre-work](docs/getting-ready.md), then follow
[Open your app](docs/lessons/00-open-your-app.md). You need basic Python and HTML;
you do not need Node, an Azure SDK, or infrastructure tooling.

**Use the workshop source branch:**
[`jeffrey-groneberg-mai-vocabulary-workshop`](https://github.com/jeffrey-groneberg/the-mai-workshop/tree/jeffrey-groneberg-mai-vocabulary-workshop).
Initial publication preserves this branch rather than merging it into `main`;
the default `main` currently contains only a README.
The recommended participant path is a **fork in your own GitHub account**:
retain the workshop branch, then select it under **New with options** and choose
2 cores if offered, otherwise the smallest allowed machine. Follow readiness for
the exact fork and private-secret steps. The
[source-branch Codespaces creation link](https://codespaces.new/jeffrey-groneberg/the-mai-workshop/tree/jeffrey-groneberg-mai-vocabulary-workshop)
is for instructors with write access to the original repository, not your fork.

**Published workshop guide:**
[jeffrey-groneberg.github.io/the-mai-workshop/](https://jeffrey-groneberg.github.io/the-mai-workshop/).
Publication of the **static workshop guide** is authorized; verify the deployed
site before sharing it as live. Pages cannot run Flask or hold participant
secrets. Your app and the finished solution still run in Codespaces or locally.

| Location | Purpose |
| --- | --- |
| `starter/` | **Your app.** The only application folder you edit. Initially a styled, working sample page, not a completed word list or recorder. |
| `solution/` | **Finished solution.** An independently runnable reference to inspect, not an implementation imported by your app. |
| `docs/` | **Workshop guide.** The lessons, instructor notes, and reference. |

Both apps have four main source files: `app.py`, `templates/index.html`,
`static/app.js`, and `static/style.css`. Licensed font assets are additional
assets, not application layers. There is no frontend build, database, factory,
blueprint, provider framework, or per-lesson project.

In a ready Codespace, run each command from the repository root in a **separate
terminal**:

```sh
python -m flask --app starter/app.py run --host 0.0.0.0 --port 5050
```

```sh
python -m flask --app solution/app.py run --host 0.0.0.0 --port 5051
```

```sh
zensical serve --dev-addr 0.0.0.0:8000
```

Keep all forwarded ports **Private**. Open **Your app** (5050), **Finished
solution** (5051), and **Workshop guide** (8000) from the Ports panel. Use the
HTTPS forwarded app in a **normal browser tab**, not an iframe or editor preview,
for microphone access. [Local setup](docs/local-setup.md) uses a Python virtual
environment and loopback binding instead.

The third command previews the documentation. If you are reading the deployed
Pages guide, you do not need that preview server. A Pages lesson is not the app:
recording, playback, uploads, and model requests happen in the Flask app tab.

## The guided build

1. [Open your app](docs/lessons/00-open-your-app.md): trace the four files.
2. [Make it your vocabulary](docs/lessons/01-word-list.md): implement inputs,
   selection, and browser persistence.
3. [Hear both languages](docs/lessons/02-bilingual-speech.md): send SSML through
   Flask and play real WAV audio.
4. [Speak and see what was heard](docs/lessons/03-record-and-transcribe.md):
   implement local capture, WAV conversion, preview, and explicit upload.
5. [Check your answer](docs/lessons/04-check-your-answer.md): match recognized
   text conservatively, without another model call.
6. [Make a visual memory cue](docs/lessons/05-memory-images.md): request and
   display a generated PNG.

Each lesson gives exact edits, a browser-visible checkpoint, then two or three
choices. **Try one:** predict, change one thing, run the feature again, compare,
and choose what to keep. [MAI-Thinking mnemonics](docs/extensions/mnemonics.md)
and larger feature additions are after-core, optional work.

## Access, privacy, and verification

The instructor privately supplies a gateway **origin** and an individual
temporary key. **Both `APIM_BASE_URL` and `APIM_API_KEY` are sensitive
configuration.** Keep both server-side as Codespaces secrets, or in an ignored
root `.env` fallback. `APIM_BASE_URL` must be an HTTPS origin with no path;
environment variables take precedence over `.env`. No real endpoint or working
credential is included. Never put either value in Git, documentation,
screenshots, logs, image provenance, browser code, or the published site. Keep
`.env.example` values empty and never copy private `.env` files into `site/`.

The portal currently permits synthetic/sample data only. Microphone
participation needs instructor-approved guidance **and** explicit consent;
consent alone does not change that policy. Preview locally before choosing to
send. The apps do not persist recordings. Instead of using a microphone, generate
and download a short synthetic target-language WAV with the speech feature.

Matching a transcript is **not pronunciation assessment**. Models, transcripts,
and saved translations can be wrong. Both
[image](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-image)
and [thinking](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-thinking)
offerings are preview; deployed availability and shared capacity must be checked
by the instructor. See [the API contract and limitations](docs/reference.md) and
[instructor readiness and verification](docs/instructor.md).

Local fixture checks can verify code and requests, not live model behavior,
Codespaces permissions, microphone hardware, or the two-hour fit. Startup and
tests must not make model calls. Publishing the static guide does not deploy
either Flask app, provision a model, or verify participant gateway access.
