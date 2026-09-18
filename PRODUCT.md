# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Zensical documentation and small Flask applications with directly served HTML,
CSS, and JavaScript. GitHub Codespaces is the primary environment; local Python
is the fallback. Each application has four main source files.

## Users and purpose

Experienced developers build a vocabulary-learning app to try MAI speech,
transcription, and image APIs. The instructor provides gateway access.

## Operating context

The participant edits `starter/`; `solution/` is an independently runnable,
complete reference. The starter has a styled sample vocabulary view, not
completed word-list or recording functionality. The fixed workshop slot is two
hours with environment readiness as pre-work. Its pacing requires a learner pilot.

Participants start from the repository's default `main` branch. No development
branch is part of the workshop instructions. `gh-pages` contains generated
documentation only, not a participant workspace.

Each lesson states the result, explains the relevant mechanism, gives exact
edits, and ends with a run check and an experiment. Remove repeated workshop
process, facilitator commentary, and privacy guidance from the written guide;
the instructor handles that briefing. App controls and credential handling
remain unchanged.

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

Checkpoint screenshots show the actual learner app produced by the lesson
edits. A short GIF introduces the completed flow. Media uses labeled example
model responses and includes a static alternative for reduced motion.

MAI-generated explanatory diagrams cover request flow, audio conversion,
local matching, image creation, feature/model mapping, and the currently
featured model family. Their labels are checked against code and official
sources; prompts and revision history accompany the assets. A single optional
comparison chapter grounds model-cost claims in cited, dated rates and explicit
workload assumptions rather than assumed quality parity.

## Accessibility

Keyboard-operable controls, clear permission/error states, reduced motion,
responsive layouts, and synthetic-audio alternatives are required.
