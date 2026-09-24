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


# Lesson 2: add the /speak route here.


# Lesson 3: add the /transcribe route here.


# Lesson 5: add the /image route here.


# Extension: add the /mnemonic route here.
