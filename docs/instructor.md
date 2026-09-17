# Instructor guide

**The two-hour target is a user-selected constraint, not measured pacing.**
Environment readiness is pre-work. The guided core still includes the entire
word-list implementation, browser recording / WAV implementation, and one
experiment per checkpoint. MAI-Thinking and larger features are after-core.

## Publish the guide, not the Flask app

Publication to this repository's **GitHub Pages** is authorized. The deployment
target is
[https://jeffrey-groneberg.github.io/the-mai-workshop/](https://jeffrey-groneberg.github.io/the-mai-workshop/).
Confirm the actual deployed result before announcing that address as live.
Check the home page, a nested lesson, navigation, and image/provenance links
under the `/the-mai-workshop/` prefix, not only at a root-level local preview.

Keep the complete workshop source on
[`main`](https://github.com/jeffrey-groneberg/the-mai-workshop/tree/main).
Participants start from that default branch; `starter/` and `solution/` provide
the exercise/reference separation. The `gh-pages` branch contains only the
generated static site and is a publishing detail, not a participant workspace.

Pages serves the built **static workshop guide**. It cannot run Flask, accept
the app's recording uploads, make its server-side gateway requests, or hold
private gateway configuration. **Treat `APIM_BASE_URL` as sensitive, just like
`APIM_API_KEY`.** Do not put either value into Git, documentation, screenshots,
logs, provenance, generated HTML/JavaScript, assets, or deployment output.
Never copy private `.env` files into `site/`. Participants still run **Your app** on private port 5050
and **Finished solution** on private port 5051 in Codespaces, or use the local
fallback. Port 8000 is a documentation preview, not another app backend.

Successful Pages publication is not evidence of participant Codespaces access,
microphone operation, model capacity, or a learner-paced two-hour fit.

## Before inviting participants

| Readiness area | Confirm before the guided session |
| --- | --- |
| GitHub access | Use participant-owned forks of `jeffrey-groneberg/the-mai-workshop` with **Copy the main branch only** selected. Confirm fork ownership, an up-to-date `main`, Codespaces availability, and access to both private secrets. Help resolve sync conflicts without deleting participant work. |
| Billing | An approved Codespaces compute/storage arrangement and separate model-call/capacity arrangements. Do not promise a free environment or infer capacity from one successful request. |
| Container | In the participant's fork, use **New with options**, leave the branch on `main`, and choose 2 cores if offered, otherwise the smallest allowed machine. The source-repository creation link is for instructors with write access. Recommend both `APIM_BASE_URL` and `APIM_API_KEY` as Codespaces secrets by name/description only; test the prompt and fallback. |
| Ports and browser | Labels **Your app** 5050, **Finished solution** 5051, **Workshop guide** 8000; all remain **Private**. Verify forwarded HTTPS in a normal browser tab, sign-in, same-origin POSTs, playback, and the intended desktop browsers. |
| Gateway | Privately supply an HTTPS origin without a path and individual participant access. Store both `APIM_BASE_URL` and `APIM_API_KEY` as secrets; keep tracked `.env.example` values empty. Confirm the pinned routes, enabled deployments, event limits, outbound access, and content policy without publishing private hosts. |
| Access lifetime | Provider keys expire 24 hours after initial issuance; revocation/rotation can also invalidate access. Arrange issuance around the event and have the portal recovery path ready. |
| Model capability | Recheck each offered Flash voice against the official table. Korean uses Haena. Keep the explicit 14-language / 16-target-locale intersection; larger STT coverage is not TTS support. |
| Data guidance | The portal is synthetic/sample-data-only. Decide whether and under what approved guidance voluntary real-voice recordings are permitted. Consent alone is insufficient. No confidential vocabulary, personal data, or unapproved recordings. |
| Audio alternative | Generate/download a short target-language WAV using **Finished solution > Download synthetic WAV**. Verify preview and upload. There is no assumed prepackaged sample file. |
| Capacity | Budget for bilingual speech, sample generation, transcription, image requests, and each participant's chosen experiments. Optional thinking needs separate allowance. Repeated Send / Generate actions can be billable. |

Follow the existing provider's
[provisioning and event guidance](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/README.md)
and [live contract checks](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/scripts/test_apim_live.py).
This workshop does not provision cloud resources, create/revoke subscriptions,
change shared quotas, or need a participant's GitHub token at the gateway.
See [readiness pre-work](getting-ready.md) and
[API reference](reference.md) for first-party sources and troubleshooting.

## Facilitate the core in order

| Checkpoint | Participant evidence, not an instructor demonstration |
| --- | --- |
| Open | Their styled starter is reachable; they can identify the Python, HTML, JS, and CSS contributions. |
| Word list | They implemented adding/selecting/removing and browser persistence, and refreshed their own app successfully. |
| Bilingual speech | Both buttons make the appropriate text/locale request; a synthetic target WAV can be downloaded. |
| Record and transcribe | They added capture and real WAV conversion; local preview precedes explicit Send; a real gateway transcript is visible when authorized access is available. The synthetic alternative uses the same upload route. |
| Answer matching | Heard text, saved answer, and deterministic match/retry are visible; recognition failure is not labeled a wrong answer. |
| Memory image | A generated PNG appears on the correct word, and the complete practice loop works in their app. |

After **every** checkpoint, participants choose one of the page's two or three
experiments: predict, change one thing, run end to end, compare, choose. The
remaining choices are for later exploration. Ask what the documented capability
is, what the participant actually observed, and what remains their hypothesis.
Do not promise that a chosen prompt/voice/hint must improve a result.

Keep the small implementation visible. Learners edit only `starter/`; there is
no copied project per step, stage generator, custom checkpoint runner, or hidden
solution import. The complete `solution/` is a diagnostic reference. If a learner
is blocked, compare the relevant route/handler or demonstrate the solution while
explicitly marking their own checkpoint unfinished. Never count copying the
reference over their work as implementing a feature.

The documented learner app intentionally uses a single busy lock instead of the
reference's richer cancellation/stale-response handling. It caches speech and
the latest image per word for the current page, and uses explicit deployment
names in the two generation routes. The independent reference offers additional
UX polish and environment deployment overrides. Neither uses fake model outputs.

## Validate the target with learners

Run a **representative learner-paced pilot** that includes code entry, debugging,
browser permissions or the synthetic path, live service behavior, all core
features, and one experiment after each. Record actual completion/blockers and
the time spent on setup separately. A maintainer's paste-through or agent fixture
replay measures neither learning nor classroom pace.

If the pilot does not fit the fixed two-hour slot, surface the scope/slot
trade-off to the workshop owner. Do not quietly prebuild the word list or WAV
code, remove experiments, or move required core work to optional reading.
The target is unvalidated until that pilot supplies evidence.

## Maintainer checks and honest acceptance

With the development dependencies installed, the focused lesson check is:

```sh
python -m pytest -q tests/test_lessons.py
```

The test extracts the published fenced code, applies the stated replacements /
insertions to a **`tmp_path` copy of `starter/`**, and starts each evolving Flask
app on the same loopback origin. Headless Chromium follows the word-list,
English-first / bilingual speech, recording, upload, matching, image, and
optional mnemonic checkpoints. Its microphone is a synthetic browser test
device; native `MediaRecorder`, decoding, resampling, and WAV encoding still run.
All upstream `httpx.post` calls are intercepted by fixtures. Request/response
checks include errors, formats, the locale map, and exact host/origin guards.
This is an ordinary pytest test, not a shipped stage/checkpoint runner.

No checked-in app file is edited by the replay. Browser fixtures belong only in
tests; no fake-inference switch belongs in a shipped app.

The source snapshot
[`e009350`](https://github.com/jeffrey-groneberg/the-mai-workshop/commit/e0093507af7f122a706d7de2d771aa005302657d)
passed the [GitHub Check job on Python 3.12](https://github.com/jeffrey-groneberg/the-mai-workshop/actions/runs/35247785317).
Local checks also ran on Python 3.14. These are code/fixture observations, not
evidence of a live participant gateway or a learner-paced pilot.

Site maintainers also run:

```sh
zensical build --clean --strict
```

**Local fixture proof is limited.** It can establish runnable Python/JavaScript,
request shapes, validation, and browser behavior with synthetic fixtures. It
cannot establish actual gateway access, model quality/latency, content filtering
policy, retention, Codespaces permission/forwarding behavior, physical
microphone compatibility, or a learner-paced fit. No real endpoint/key is
provided in this repository; do not describe those as verified.

Run an **explicitly authorized, potentially billable live walkthrough** before
the event: create/restart a participant-equivalent Codespace, inject both secrets,
open the private forwarded guide and apps, build through the lessons, exercise
both speech languages, local capture/preview/stop/send or synthetic upload,
transcript matching, and image display. Use only approved sample data. Test
errors and shared-limit recovery deliberately, without automatically retrying
or changing cloud settings. Keep live checks out of startup and CI.

Review keyboard navigation, focus/status visibility, readable code, narrow
layouts, and reduced motion. Responsive layout alone does not prove mobile
microphone support. Real microphone/forwarded-tab and live-model acceptance
remain open until observed in the authorized environment.

## Close the session safely

Have participants preserve wanted edits and vocabulary according to event
guidance, then **stop** their Codespace to stop compute use. Explain that storage
cost/lifecycle is separate. Do not delete work without an explicit, informed
choice. Do not collect private endpoint URLs, participant keys, or recordings
in debugging logs/screenshots; use status codes, safe error messages, and sample
data.
