# API and troubleshooting

## Connection

Flask reads `APIM_BASE_URL` and `APIM_API_KEY` from the environment, with root
`.env` as a fallback. The base URL is an HTTPS origin without an API path.
All gateway REST requests use the `api-key` header, including Speech.

Browser calls such as `fetch("/speak")` target Flask on port **5050**, not this
guide. Port **5051** runs the solution; **8000** optionally previews documentation.

## Requests

| Feature | Gateway request | Response |
| --- | --- | --- |
| Speech | `POST /speech/tts`; SSML body; `X-Microsoft-OutputFormat: riff-16khz-16bit-mono-pcm` | WAV bytes |
| Transcription | `POST /speech/transcribe?api-version=2025-10-15`; multipart `audio` and JSON-encoded `definition`; `enhancedMode` selects `MAI-Transcribe-2` | `combinedPhrases[].text` |
| Images | `POST /mai/v1/images/generations`; JSON with `model: "mai-image-flash"`, English `prompt`, `width: 1024`, `height: 1024` | `data[0].b64_json` — base64 PNG |
| Mnemonics | `POST /mai/v1/chat/completions`; JSON with `model: "mai-thinking"` and `messages` | `choices[0].message.content` — text |

`mai-image-flash` and `mai-thinking` are deployment names. The solution supports
`MAI_IMAGE_DEPLOYMENT` and `MAI_THINKING_DEPLOYMENT` overrides; lesson code uses
explicit names. Both image and thinking offerings are preview.

Provider contract:
[catalog](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/config/models.yaml),
[requests](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/app/catalog.py),
[routes](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/infra/gateway.tf).
Microsoft APIs:
[Voice](https://learn.microsoft.com/azure/ai-services/speech-service/mai-voices),
[Transcribe](https://learn.microsoft.com/azure/ai-services/speech-service/mai-transcribe),
[Image](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-image),
[Thinking](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-thinking).

## Languages and voices

The language menu uses the intersection of documented transcription languages
and prebuilt MAI-Voice-2-Flash voices. TTS selects a voice; STT takes a language
code. Changing the menu does not translate existing entries.

| Locale | Language | STT code | MAI-Voice-2-Flash voice |
| --- | --- | --- | --- |
| `en-US` | English | `en` | `en-US-Harper:MAI-Voice-2-Flash` |
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

## Formats and matching

- **Answer audio:** mono, 16-bit, 16 kHz PCM WAV, up to 12 seconds; maximum
  request size 2 MiB. These are app limits. `MediaRecorder` output is decoded
  and resampled before the app writes WAV bytes; renaming a file is not conversion.
- **Image:** 1024 × 1024 PNG, displayed as a smaller thumbnail. The API requires
  each dimension to be at least 768 and at most 1,048,576 pixels in total.
- **Match:** whole transcript versus saved translation, ignoring case,
  surrounding punctuation, and extra whitespace. Accents and internal
  apostrophes/hyphens remain significant. This checks words, not pronunciation.
- **Caching:** words survive reload in `localStorage`; speech and images last
  only for the page. Different app URLs have separate word lists.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Old code appears | Save, restart Flask after Python/HTML edits, then reload. JS/CSS need reload only. Check port 5050, not 5051. |
| Flask will not start | Check the terminal error, indentation, and insertion point. Keep `// Start the page.` last in JavaScript. |
| Connection failure or HTML instead of JSON/audio | Restart Flask or reopen the Codespaces port and sign in again. |
| `503` | Check both settings and environment-over-`.env` precedence; restart Flask. |
| `401` | Obtain a current participant key; keys expire 24 hours after issuance or earlier if revoked. |
| `403` | Use the Flask app tab; check the displayed message and gateway access with the instructor. |
| `404` | Check the gateway origin and deployment name. |
| `429` or timeout | Follow `Retry-After`, then retry deliberately; check shared capacity with the instructor. |
| Microphone unavailable or prompt unanswered | Open the HTTPS app in a normal tab. Press **Stop recording** to cancel; choose a downloaded synthetic WAV instead. |
| WAV rejected or `413` | Use a short 16 kHz mono PCM WAV. Check duration, channels, and file size. |
| No words / `422` | Preview the audio and check the selected language. |
| Image/text cannot be decoded | Compare the response format with the table above. |
| Word list missing | Return to the same app URL. For unreadable storage, use the app's reset if you want to clear it. |
