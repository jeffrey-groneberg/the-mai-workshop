---
title: MAI Vocabulary Workshop
description: Build a small vocabulary app with Flask and MAI, one working feature and one experiment at a time.
template: home.html
hide:
  - navigation
  - toc
---

<!-- THESIS: A readable invitation to build a real vocabulary practice loop, not a model dashboard.
OWN-WORLD: Microsoft AI companion: warm paper, brown Source Serif 4, Red Hat Mono, sand pills, quiet peach.
STORY: Get ready in Codespaces, build in starter, reach a working checkpoint, then try one deliberate change.
FIRST VIEWPORT: Spacious serif introduction, clear readiness action, honest session target, and the build/checkpoint/experiment rhythm.
FORM: The user-approved Microsoft AI reference; content-led workshop guide with an unboxed lesson sequence.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md -->

<section class="workshop-hero" markdown="1">

# Make a word<br>your starting point.

Build a small vocabulary app with Python, HTML, and MAI. Keep a word, hear both
languages, speak an answer, then make a picture to help it stick.
{ .workshop-intro }

<div class="workshop-actions" markdown="1">

[Get ready in Codespaces](getting-ready.md){ .md-button .md-button--primary }
[Open your first app](lessons/00-open-your-app.md){ .md-button }

</div>

For developers who know a little Python and HTML. **A 2-hour session target, not
validated pacing:** environment readiness is pre-work, and the full learning
path still needs a representative learner pilot.
{ .workshop-session }

</section>

<section class="workshop-rhythm" markdown="1">

## Build. See it work. Then experiment.

<ol>
<li>
<h3>Build one feature.</h3>
<p>Make a small, explained change in your app. Trace what happens in the browser,
in Flask, and, when needed, at the model.</p>
</li>
<li>
<h3>Reach a working checkpoint.</h3>
<p>Run the feature in your browser. Your current <code>starter/</code> app must work
before you move on; inspecting the solution is not the checkpoint.</p>
</li>
<li>
<h3>Try one change.</h3>
<p>Predict a result, change one option, and run it again. Compare what happened and
choose what to keep. Every core lesson includes an experiment.</p>
</li>
</ol>

</section>

<figure class="workshop-illustration" markdown="1">

![Watercolor of an apple beside an open notebook, with sound waves flowing toward a small mountain landscape.](assets/images/vocabulary-journey.webp){ width="1344" height="768" loading="lazy" decoding="async" }

<figcaption>AI-generated learning illustration: a word, a voice, and a visual memory cue. Not a live app result.</figcaption>

</figure>

<section class="workshop-studio" markdown="1">
<div markdown="1">

## Small enough to understand.

Four main files. One application you can follow from a click to a response.
No frontend build system, database, or hidden provider framework.

You will build a saved word list, bilingual playback, recording and transcription,
answer matching, and on-demand memory images. Matching checks recognized text
against your saved translation; it is **not a pronunciation score**.

</div>
<dl class="workshop-files">
  <div><dt><code>app.py</code></dt><dd>Flask routes and model requests</dd></div>
  <div><dt><code>templates/index.html</code></dt><dd>The page and its controls</dd></div>
  <div><dt><code>static/style.css</code></dt><dd>Typography, layout, and states</dd></div>
  <div><dt><code>static/app.js</code></dt><dd>Browser interactions and local storage</dd></div>
</dl>
<div class="workshop-copies" markdown="1">

**`starter/` is yours to build.** It opens as a styled sample page, not a finished
word list or recorder. Make your guided changes and experiments here.

**`solution/` is your reference.** Run it separately to understand the goal or
compare a feature. Model actions require valid instructor-provided gateway access.

</div>
</section>

<section class="workshop-path" markdown="1">
<div markdown="1">

## One app.<br>Six working checkpoints.

Start with [readiness pre-work](getting-ready.md), then follow these lessons in
order. Keep your editor, app, and guide side by side.

Codespaces is the default for your Flask app. Follow the
[fork-and-branch setup](getting-ready.md#create-the-codespace) to create your
own workspace on the workshop branch, not `main`.

GitHub Pages hosts only this static guide; it cannot run Flask or securely store
private configuration. Keep both
`APIM_BASE_URL` and `APIM_API_KEY` in Codespaces secrets. Do not put either value
in Git, the published guide, screenshots, or logs. To run the same app on your
computer instead, use [local setup](local-setup.md).

</div>
<div class="workshop-lessons" markdown="1">

0. [Open your app](lessons/00-open-your-app.md)

    Launch the starter, inspect the finished solution, and meet the four files.

1. [Make it your vocabulary](lessons/01-word-list.md)

    Choose a target language, add word pairs, and keep them in this browser.

2. [Hear both languages](lessons/02-bilingual-speech.md)

    Connect English and target-language playback through the same Flask route.

3. [Speak and see what was heard](lessons/03-record-and-transcribe.md)

    Build recording and WAV conversion, preview locally, then choose to send.
    A synthetic-audio alternative keeps microphone use voluntary.

4. [Check your answer](lessons/04-check-your-answer.md)

    Compare the transcript with your saved translation, without another model call.

5. [Make a visual memory cue](lessons/05-memory-images.md)

    Generate a picture on demand and use the complete practice loop.

</div>
</section>

<section class="workshop-after" markdown="1">

## A little further, when you are ready.

Once the core works, try the optional [MAI-Thinking mnemonic lab](extensions/mnemonics.md).
Use the [reference](reference.md) for request details and troubleshooting, or the
[instructor guide](instructor.md) to prepare access, sample-data guidance, and
classroom capacity.

</section>
