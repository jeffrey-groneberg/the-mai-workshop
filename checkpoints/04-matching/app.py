"""Your vocabulary app.

The imports cover every lesson, so later steps only replace the marker
comments at the bottom of this file.
"""

import base64
import binascii
import json
import os
from xml.sax.saxutils import escape

import httpx
from flask import Response, abort, jsonify, render_template, request

from workshop import (
    TIMEOUT, check_png, check_wav, create_app, gateway, json_body,
    optional_text, text_field, upstream_json,
)

app = create_app(__name__)

LANGUAGES = {
    "en-US": {"label": "English (US)", "stt": "en", "voice": "en-US-Harper:MAI-Voice-2-Flash"},
    "zh-CN": {"label": "Chinese (Simplified Mandarin)", "stt": "zh", "voice": "zh-CN-Mei:MAI-Voice-2-Flash"},
    "nl-NL": {"label": "Dutch", "stt": "nl", "voice": "nl-NL-Sander:MAI-Voice-2-Flash"},
    "fr-FR": {"label": "French", "stt": "fr", "voice": "fr-FR-Soleil:MAI-Voice-2-Flash"},
    "de-DE": {"label": "German", "stt": "de", "voice": "de-DE-Mia:MAI-Voice-2-Flash"},
    "hi-IN": {"label": "Hindi", "stt": "hi", "voice": "hi-IN-Kavya:MAI-Voice-2-Flash"},
    "hu-HU": {"label": "Hungarian", "stt": "hu", "voice": "hu-HU-Lilla:MAI-Voice-2-Flash"},
    "it-IT": {"label": "Italian", "stt": "it", "voice": "it-IT-Rosa:MAI-Voice-2-Flash"},
    "ko-KR": {"label": "Korean", "stt": "ko", "voice": "ko-KR-Haena:MAI-Voice-2-Flash"},
    "pt-BR": {"label": "Portuguese (Brazil)", "stt": "pt", "voice": "pt-BR-Luana:MAI-Voice-2-Flash"},
    "pt-PT": {"label": "Portuguese (Portugal)", "stt": "pt", "voice": "pt-PT-Rui:MAI-Voice-2-Flash"},
    "ro-RO": {"label": "Romanian", "stt": "ro", "voice": "ro-RO-Elena:MAI-Voice-2-Flash"},
    "ru-RU": {"label": "Russian", "stt": "ru", "voice": "ru-RU-Masha:MAI-Voice-2-Flash"},
    "es-ES": {"label": "Spanish (Spain)", "stt": "es", "voice": "es-ES-Marta:MAI-Voice-2-Flash"},
    "es-MX": {"label": "Spanish (Mexico)", "stt": "es", "voice": "es-MX-Valeria:MAI-Voice-2-Flash"},
    "th-TH": {"label": "Thai", "stt": "th", "voice": "th-TH-Krit:MAI-Voice-2-Flash"},
    "tr-TR": {"label": "Turkish", "stt": "tr", "voice": "tr-TR-Elif:MAI-Voice-2-Flash"},
}


def language_for(locale):
    if not isinstance(locale, str) or locale not in LANGUAGES:
        abort(400, "Choose a language from the supported list.")
    return LANGUAGES[locale]


@app.get("/")
def index():
    return render_template("index.html", languages=LANGUAGES)


@app.post("/speak")
def speak():
    data = json_body()
    text = text_field(data, "text")
    locale = data.get("locale")
    language = language_for(locale)
    base, headers = gateway()
    ssml = (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{locale}"><voice name="{language["voice"]}">'
        f"{escape(text)}</voice></speak>"
    )
    response = httpx.post(
        f"{base}/speech/tts",
        headers={**headers, "Content-Type": "application/ssml+xml",
                 "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
                 "User-Agent": "mai-vocabulary-workshop"},
        content=ssml.encode("utf-8"), timeout=TIMEOUT,
    )
    response.raise_for_status()
    check_wav(response.content, max_seconds=60, error_status=502)
    return Response(response.content, mimetype="audio/wav")


@app.post("/transcribe")
def transcribe():
    language = language_for(request.form.get("locale"))
    upload = request.files.get("audio")
    if upload is None:
        abort(400, "Record or choose a WAV before sending.")
    audio = upload.read()
    check_wav(audio)
    base, headers = gateway()
    definition = {
        "enhancedMode": {"enabled": True, "model": "MAI-Transcribe-2"},
        "locales": [language["stt"]],
    }
    response = httpx.post(
        f"{base}/speech/transcribe",
        params={"api-version": "2025-10-15"}, headers=headers,
        files={"audio": ("answer.wav", audio, "audio/wav")},
        data={"definition": json.dumps(definition)}, timeout=TIMEOUT,
    )
    payload = upstream_json(response)
    phrases = payload.get("combinedPhrases")
    if not isinstance(phrases, list) or not all(
        isinstance(item, dict) and isinstance(item.get("text"), str) for item in phrases
    ):
        abort(502, "The model returned no usable transcript.")
    text = " ".join(item["text"].strip() for item in phrases).strip()
    if not text:
        abort(422, "No words were recognized. Preview the sample or try again.")
    return jsonify(text=text)


# Lesson 5: add the /image route here.


# Extension: add the /mnemonic route here.
