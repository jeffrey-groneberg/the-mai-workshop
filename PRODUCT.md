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

Participants start from the repository's default `main` branch. No development
branch is part of the workshop instructions. `gh-pages` contains generated
documentation only, not a participant workspace.

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

## Visual commitments

The workshop guide uses **native Zensical styling**. The user replaced the
custom companion skin to prioritize readable prose, code, and navigation.
Use ordinary Markdown and built-in documentation components; do not reintroduce
custom guide fonts, colors, or landing-page overrides.

The Flask apps retain the https://microsoft.ai/models/ companion direction:
warm paper, brown ink, serif typography, compact monospaced labels, generous
spacing, and gentle pastel accents. The user approved a redistributable serif
instead of commercial Bradford LL. The collection/practice layout is unchanged.
No selection roll or separate bespoke comp was produced; do not invent one.

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
