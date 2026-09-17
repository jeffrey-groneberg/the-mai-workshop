# Reference and troubleshooting

The lessons show the runnable main path. This page keeps detailed contracts,
limitations, and recovery out of that path. No live endpoint/key is supplied, and
no deployed model or Codespaces verification is implied by these references.

## Guide address versus app address

The authorized static-guide deployment target is
[https://jeffrey-groneberg.github.io/the-mai-workshop/](https://jeffrey-groneberg.github.io/the-mai-workshop/).
The publishing maintainer verifies the live deployment and its project-prefix
links. GitHub Pages cannot run Flask or hold private gateway configuration.

The published guide and the private port-8000 documentation preview are for
**reading instructions**. The browser tab on private port 5050 is **Your app**;
5051 is the independent **Finished solution**. Those Flask servers render the
interactive UI and keep both the private gateway endpoint and key server-side. Local loopback servers
are the fallback.

Keep `fetch("/speak")`, `/transcribe`, `/image`, and `/mnemonic` relative to the
**Flask app's origin**, not the Pages guide URL or port 8000. Do not add Pages
to Flask's allowed origins or enable CORS to bridge the two: they have separate
jobs, and the guide must never receive private endpoint values, participant keys,
or recordings.

## Gateway contract

Wrapper-specific facts are pinned to provider revision
`9d2fa8d6d2214764ea02c281498ef243e3420d29`:
[model catalog](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/config/models.yaml),
[participant requests](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/app/catalog.py),
[APIM routes](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/infra/gateway.tf),
and [live acceptance script](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/scripts/test_apim_live.py).
Recheck the deployed event against that contract rather than assuming repository
code proves current capacity.

`APIM_BASE_URL` is **sensitive configuration**, just like `APIM_API_KEY`. Its
private value must be an HTTPS **origin only**, with no path, query, embedded
credentials, or fragment. Show only the variable names and relative API paths
in shared material, never actual gateway/inference hosts. All REST requests use the participant **`api-key`**
header, including Speech. Do not send a direct Speech resource key, Azure backend
credential, GitHub token, or key in a query string. Python adds the route; browser
requests use only relative, same-origin Flask URLs.

| Capability | Gateway request and response | First-party API source |
| --- | --- | --- |
| Speech | `POST /speech/tts`; native SSML; `Content-Type: application/ssml+xml`; `X-Microsoft-OutputFormat: riff-16khz-16bit-mono-pcm`; real WAV bytes. | [MAI voices](https://learn.microsoft.com/azure/ai-services/speech-service/mai-voices) |
| Transcription | `POST /speech/transcribe?api-version=2025-10-15`; multipart `audio` and JSON-encoded `definition`; `enhancedMode: {"enabled": true, "model": "MAI-Transcribe-2"}`; optional `locales: ["fr"]`; read `combinedPhrases[].text`. | [MAI transcription](https://learn.microsoft.com/azure/ai-services/speech-service/mai-transcribe) |
| Image | `POST /mai/v1/images/generations`; JSON `model: "mai-image-flash"`, English `prompt`, `width: 1024`, `height: 1024`; decode `data[0].b64_json` as PNG. | [MAI image](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-image) |
| Optional thinking | `POST /mai/v1/chat/completions`; JSON `model: "mai-thinking"` and `messages`; read `choices[0].message.content` as untrusted text, not guaranteed JSON. | [MAI Thinking](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-thinking) |

`mai-image-flash` and `mai-thinking` are deployment names in this gateway, not
generic model names or Speech selectors. The reference's `MAI_IMAGE_DEPLOYMENT`
and `MAI_THINKING_DEPLOYMENT` environment overrides are for instructor-confirmed
deployed variants; the learner's corresponding strings are explicit in its
routes. There is no automatic deployment discovery or silent fallback.

Both the image and thinking offerings are **preview**. Availability, quotas,
content filtering, accuracy, and latency must not be promised from sample code.
Image dimensions have a documented minimum of 768 and a maximum pixel budget of
1,048,576; 1024 x 1024 fits. CSS displays a smaller thumbnail without reducing the
model request. Generated images are memory cues, not verified definitions.

## Language, locale, voice, model

The following explicit map is used by the lessons and reference. The
[official MAI voice table](https://learn.microsoft.com/azure/ai-services/speech-service/mai-voices)
is the synthesis authority; the
[transcription documentation](https://learn.microsoft.com/azure/ai-services/speech-service/mai-transcribe)
is the STT authority. Recheck both before the event.

| Locale | Label | STT code | MAI-Voice-2-Flash voice |
| --- | --- | --- | --- |
| `en-US` | English (source) | `en` | `en-US-Harper:MAI-Voice-2-Flash` |
| `zh-CN` | Chinese (Simplified Mandarin) | `zh` | `zh-CN-Mei:MAI-Voice-2-Flash` |
| `nl-NL` | Dutch | `nl` | `nl-NL-Sander:MAI-Voice-2-Flash` |
| `fr-FR` | French | `fr` | `fr-FR-Soleil:MAI-Voice-2-Flash` |
| `de-DE` | German | `de` | `de-DE-Mia:MAI-Voice-2-Flash` |
| `hi-IN` | Hindi | `hi` | `hi-IN-Kavya:MAI-Voice-2-Flash` |
| `hu-HU` | Hungarian | `hu` | `hu-HU-Lilla:MAI-Voice-2-Flash` |
| `it-IT` | Italian | `it` | `it-IT-Rosa:MAI-Voice-2-Flash` |
| `ko-KR` | Korean | `ko` | `ko-KR-Haena:MAI-Voice-2-Flash` |
| `pt-BR` | Portuguese (Brazil) | `pt` | `pt-BR-Luana:MAI-Voice-2-Flash` |
| `pt-PT` | Portuguese (Portugal) | `pt` | `pt-PT-Rui:MAI-Voice-2-Flash` |
| `ro-RO` | Romanian | `ro` | `ro-RO-Elena:MAI-Voice-2-Flash` |
| `ru-RU` | Russian | `ru` | `ru-RU-Masha:MAI-Voice-2-Flash` |
| `es-ES` | Spanish (Spain) | `es` | `es-ES-Marta:MAI-Voice-2-Flash` |
| `es-MX` | Spanish (Mexico) | `es` | `es-MX-Valeria:MAI-Voice-2-Flash` |
| `th-TH` | Thai | `th` | `th-TH-Krit:MAI-Voice-2-Flash` |
| `tr-TR` | Turkish | `tr` | `tr-TR-Elif:MAI-Voice-2-Flash` |

There are **14 non-English languages / 16 target locales**, with no forced
German default. Korean **Flash** uses Haena; regular-model Hana is not the same
voice identifier. Japanese is not offered in this verified prebuilt-voice
intersection. STT supporting a language does not make a TTS voice exist.

Changing a language menu affects the next saved entry; it does not translate the
list. The English default is Harper. TTS reads your stored text; transcription
receives the language hint, **never the expected translation as a phrase hint**.
Speech output and transcription are separate requests with separate failure
modes.

## Audio and browser mechanics

The browser owns capture. In Codespaces, Flask runs remotely and the browser
opens GitHub's private forwarded **HTTPS** URL; the internal Flask server stays
HTTP. Use a normal tab, not an embedded editor preview.
[`getUserMedia`](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
requires an appropriate secure context and permission.

[`MediaRecorder`](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
records a browser-supported format, which may not be WAV.
[`decodeAudioData`](https://developer.mozilla.org/en-US/docs/Web/API/BaseAudioContext/decodeAudioData)
decodes the complete blob;
[`OfflineAudioContext`](https://developer.mozilla.org/en-US/docs/Web/API/OfflineAudioContext)
resamples to mono PCM; the learner writes the WAV header and samples. Renaming
WebM/Opus bytes `.wav` or setting `type: "audio/wav"` alone is not conversion.

Our answer-audio guardrails are a complete mono, 16-bit, 16 kHz PCM WAV of up to
12 seconds and a Flask request limit of 2 MiB, including multipart overhead.
Generated speech can be longer, so use a **short** synthetic word/phrase for
upload. These are app limits, not a claim about the service's global limits.
WAV headers and complete frames are checked server-side; image signatures and
dimensions are checked before the browser decodes them.

Track stop, local preview, and explicit Send are distinct. The app does not save
recordings to disk or localStorage. A user-requested synthetic WAV download is a
local file, not a hidden stored recording. Discard, selection changes, or page
exit release page-owned audio resources. Revoking consent stops local capture
but cannot recall an already-submitted request.

## Matching is not pronunciation assessment

The browser compares whole recognized text against the saved target using NFC,
locale-aware lowercasing, normalized whitespace, and removal of surrounding
punctuation. It preserves accents, internal apostrophes/hyphens, and German
sharp-s. `été` is not `ete`; `Straße` is not `Strasse`; a longer phrase containing
the answer is not the whole answer.

Homophones, recognition errors, valid alternative translations, and mistakes in
the saved answer all limit the result. Show both heard and saved text; no-speech,
invalid data, and failed requests are not wrong-answer verdicts. Azure's
[pronunciation assessment](https://learn.microsoft.com/azure/ai-services/speech-service/pronunciation-assessment-tool)
is a different capability not used by this workshop.

## Data and secrets

The provider's current portal guidance permits **synthetic/sample data only**.
Microphone participation needs approved instructor guidance as well as explicit
consent. Do not infer permission from a checkbox or promise a model retention
period not established by the instructor's actual service/policy arrangement.

Vocabulary stays in localStorage until a participant uses a model feature; that
action sends the relevant text/audio to Flask, the APIM gateway, and hosted
models. In Codespaces, Flask is already cloud-hosted. Only vocabulary is
persistent in browser storage; generated media caches last for the page.
Different app origins have separate lists.

Keep **both `APIM_BASE_URL` and `APIM_API_KEY`** as server-side Codespaces secrets,
or in an ignored root `.env`; environment variables win over `.env`. Tracked
`.env.example` values stay empty. Never expose either value in browser code,
documentation, HTML/JS, logs, screenshots, Git, provenance, or published assets.
Never copy private environment files into `site/`. Errors log status or
exception type rather than upstream bodies or endpoint URLs. Isolated test
fixtures use explicitly synthetic `.test` hosts, not live gateway addresses.
Public GitHub/Pages and documentation links are not private gateway settings. The
[provider access documentation](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/README.md)
sets a 24-hour key lifetime from issuance; rotation/revocation can end it sooner.

## Troubleshooting

| Symptom | Check and safe recovery |
| --- | --- |
| App shows an old version | Save all edits. Restart **Your app's** Flask terminal after Python changes; reload/hard-refresh after HTML/JS changes. Confirm port 5050, not solution 5051. |
| Flask won't start | Read the terminal error; check import/indentation and the lesson's exact insertion point. Keep JS initialization last. Do not copy solution files over work. |
| Can't reach Flask / sign-in HTML instead of JSON, WAV, or PNG | Reopen the private forwarded port and sign in. Confirm the process is running. This is not necessarily APIM authentication failure. |
| App `503` configuration error | The private origin must be HTTPS with no path; the key must be present server-side. Check both injected secrets versus `.env` precedence, then restart. Never print either value. |
| Gateway `401` | Check expired/rotated/revoked or mistyped participant access with the portal/instructor. Changing code or a Speech resource key is not a fix. |
| `403` | Distinguish the app's same-origin message from gateway access/content blocking. Use the normal app tab and approved sample data; check the instructor's access settings. Do not disable guards or bypass content policy. |
| `404` | Check the gateway origin and instructor-confirmed routes/deployments against the pinned catalog. Do not probe unrelated endpoints. |
| `429` | Respect displayed `Retry-After` guidance, wait, and coordinate shared quota/capacity with the instructor. No automatic retry loop or silent model fallback. |
| Gateway timeout / other server failure | Keep the error visible; retry deliberately only after checking connectivity/service status. A timeout may still have consumed capacity; no guaranteed latency is implied. |
| No microphone / permission declined | Check HTTPS normal tab, browser permission, hardware, and policy. If unavailable or not approved, choose a synthetic WAV. Do not bypass browser/OS warnings. |
| WAV rejected / `413` | Use the short MAI-generated sample or the learner's real PCM converter. Check rate/channels/duration and request size; a filename or MIME label does not establish format. |
| No words / `422` | Preview the sample, check locale and silence, then try approved audio again. This is not a mismatch verdict. |
| Image or text format error | The app checks response shape and refuses malformed output. Check the provider contract; do not display base64/HTML as if it were a valid model result. |
| List missing after changing URL | localStorage belongs to the exact app origin. Solution, starter, another Codespace, and localhost do not share a list. |
| Unreadable/blocked storage | Nothing should be silently overwritten. Preserve wanted data if possible; use the app's explicit reset only if you choose to clear it. Check browser storage policy. |

GitHub references:
[forwarding ports](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace),
[default environment variables](https://docs.github.com/en/codespaces/developing-in-a-codespace/default-environment-variables-for-your-codespace),
[recommended secrets](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/configuring-dev-containers/specifying-recommended-secrets-for-a-repository),
and [Codespaces security](https://docs.github.com/en/codespaces/reference/security-in-github-codespaces).
Local fallback commands and PowerShell guidance are on
[Local setup](local-setup.md).
