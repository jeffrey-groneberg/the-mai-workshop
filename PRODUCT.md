# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Zensical documentation and small Flask applications with directly served HTML,
CSS, and JavaScript. GitHub Codespaces is the primary environment; local Python
is the fallback. Each application has four main source files.

## Users and purpose

Developers familiar with basic Python and HTML build a vocabulary-learning app
to understand MAI speech, transcription, and image APIs. The instructor provides
individual, temporary APIM gateway access.

## Operating context

The participant edits `starter/`; `solution/` is an independently runnable,
complete reference. The starter has a styled sample vocabulary view, not
completed word-list or recording functionality. The fixed workshop slot is two
hours with environment readiness as pre-work. Its pacing requires a learner pilot.

Each concise lesson explains what, how, and which components participate, then
delivers a working end-to-end feature followed by a participant experiment.

## Capabilities and constraints

Learners build word-list persistence, bilingual playback, browser recording and
WAV conversion, MAI transcription, deterministic answer matching, and image
generation. MAI-Thinking mnemonics are an optional after-core extension.

Use only documented voice/locale combinations. Transcript matching is not
pronunciation assessment. Microphone participation is voluntary and requires
approved data guidance. Gateway endpoint URLs and API keys stay in private
server-side configuration; neither belongs in Git or published documentation.
No automatic inference,
database, frontend build system, provider framework, or fake model fallback.

## Brand commitments

The visual authority is https://microsoft.ai/models/: warm paper, brown ink,
serif typography, compact monospaced labels, generous spacing, and gentle pastel
accents. Use redistributable fonts rather than commercial Bradford LL.

The user supplied this existing visual reference and approved the
collection/practice layout during planning. This is a reference extension, not
a randomly selected new visual world: no selection roll, seed, or separate
bespoke comp was produced. Do not invent retrospective selection provenance.

The workshop includes three original MAI-Image-2.6 teaching illustrations:
a vocabulary journey and two explicitly prompted senses of "bank".
They are labeled AI-generated and have prompt provenance in
`docs/assets/images/provenance.json`. They are not evidence of a participant
gateway's live behavior.

The Zensical guide is published to GitHub Pages. Flask continues to run in
Codespaces or locally, never on the static Pages site.

## Accessibility

Keyboard-operable controls, clear permission/error states, reduced motion,
responsive layouts, and synthetic-audio alternatives are required.
