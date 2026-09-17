import base64
import binascii
import io
import json
import os
import struct
import wave
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

import httpx
from dotenv import load_dotenv
from flask import Flask, Response, abort, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
TIMEOUT = httpx.Timeout(120, connect=10)

# Published MAI-Voice-2-Flash voices; STT takes a language code, not a voice locale.
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

codespace_hosts = set()
if os.getenv("CODESPACES") == "true":
    name = os.getenv("CODESPACE_NAME", "")
    domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "")
    if name and domain:
        codespace_hosts = {f"{name}-{port}.{domain}" for port in (5050, 5051)}
app.config["TRUSTED_HOSTS"] = ["localhost", "127.0.0.1", *codespace_hosts]


@app.before_request
def require_same_origin():
    if request.method == "POST":
        scheme = "https" if request.host in codespace_hosts else "http"
        if request.headers.get("Origin") != f"{scheme}://{request.host}":
            abort(403, "Open the app in its own browser tab and send requests from there.")


@app.after_request
def browser_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Permissions-Policy"] = "microphone=(self), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' blob:; media-src 'self' blob:; font-src 'self'; "
        "connect-src 'self'; object-src 'none'; base-uri 'self'; "
        "frame-ancestors 'none'; form-action 'self'"
    )
    return response


def gateway_settings():
    base = os.getenv("APIM_BASE_URL", "").strip().rstrip("/")
    key = os.getenv("APIM_API_KEY", "").strip()
    try:
        parsed = urlsplit(base)
        port = parsed.port
        httpx.URL(base)
    except (ValueError, httpx.InvalidURL):
        abort(503, "The private gateway URL must be a valid HTTPS origin.")
    if (
        parsed.scheme != "https" or not parsed.hostname or parsed.path
        or parsed.query or parsed.fragment or parsed.username or parsed.password
        or not key or key in {"replace-me", "your-participant-key"}
        or not key.isascii() or any(char.isspace() for char in key)
        or port == 0
    ):
        abort(503, "Configure APIM_BASE_URL and APIM_API_KEY, then restart Flask.")
    return base, {"api-key": key}


def text_field(data, name, limit=120):
    value = data.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        abort(400, f"{name} must contain 1 to {limit} characters.")
    if any(ord(char) < 32 and char not in "\t\n\r" for char in value):
        abort(400, f"{name} contains unsupported control characters.")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        abort(400, f"{name} must contain valid Unicode characters.")
    return value.strip()


def json_body():
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400, "Send a JSON object.")
    return data


def language_for(locale):
    if not isinstance(locale, str) or locale not in LANGUAGES:
        abort(400, "Choose a language from the supported list.")
    return LANGUAGES[locale]


def check_wav(audio, max_seconds=12, error_status=400):
    try:
        with wave.open(io.BytesIO(audio), "rb") as wav:
            frames = wav.getnframes()
            if (
                wav.getnchannels() != 1 or wav.getsampwidth() != 2
                or wav.getframerate() != 16000 or wav.getcomptype() != "NONE"
                or not 0 < frames <= 16000 * max_seconds
                or len(wav.readframes(frames)) != frames * 2
            ):
                raise ValueError("Invalid PCM parameters")
    except (wave.Error, EOFError, ValueError):
        abort(error_status, f"Use a complete mono, 16-bit, 16 kHz WAV of up to {max_seconds} seconds.")


def upstream_json(response):
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError:
        abort(502, "The gateway returned an unreadable model response.")
    if not isinstance(data, dict):
        abort(502, "The gateway returned an unexpected model response.")
    return data


@app.errorhandler(HTTPException)
def request_error(error):
    app.logger.warning("Application request failed: HTTP %s", error.code)
    return jsonify(error=error.description), error.code


@app.errorhandler(httpx.HTTPStatusError)
def gateway_error(error):
    status = error.response.status_code
    app.logger.warning("Gateway request failed: HTTP %s", status)
    messages = {
        400: "The model rejected this request. Check its settings and sample input.",
        401: "Your participant key may be expired, rotated, or invalid. Check the workshop portal.",
        403: "Access or content was blocked. Check your portal access and use approved sample content.",
        404: "The gateway route or deployment was not found. Check the instructor's settings.",
        429: "The gateway or model is rate limited. Wait before trying again.",
    }
    response = jsonify(error=messages.get(status, "The model service is unavailable. Try again later."))
    response.status_code = status if status in messages else 502
    retry_after = error.response.headers.get("Retry-After", "")
    if status == 429 and retry_after.isdigit():
        response.headers["Retry-After"] = str(min(int(retry_after), 300))
    return response


@app.errorhandler(httpx.RequestError)
def connection_error(error):
    app.logger.warning("Gateway connection failed: %s", type(error).__name__)
    return jsonify(error="The gateway could not be reached in time. Check your connection and try again."), 504


@app.get("/")
def index():
    configured = bool(os.getenv("APIM_BASE_URL") and os.getenv("APIM_API_KEY"))
    return render_template("index.html", languages=LANGUAGES, configured=configured)


@app.post("/speak")
def speak():
    data = json_body()
    text = text_field(data, "text")
    locale = data.get("locale")
    language = language_for(locale)
    base, headers = gateway_settings()
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
        abort(400, "Choose or record a WAV before sending.")
    audio = upload.read()
    check_wav(audio)
    base, headers = gateway_settings()
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
        abort(502, "The model did not return a usable transcript.")
    text = " ".join(item["text"].strip() for item in phrases).strip()
    if not text:
        abort(422, "No words were recognized. Listen to your sample or try recording again.")
    return jsonify(text=text)


@app.post("/image")
def image():
    data = json_body()
    word = text_field(data, "word")
    detail = data.get("detail", "")
    if (
        not isinstance(detail, str) or len(detail) > 360
        or any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF for char in detail)
    ):
        abort(400, "The optional scene must be text of up to 360 characters.")
    base, headers = gateway_settings()
    response = httpx.post(
        f"{base}/mai/v1/images/generations", headers=headers,
        json={
            "model": os.getenv("MAI_IMAGE_DEPLOYMENT", "mai-image-flash"),
            "prompt": (
                f'Illustrate the English vocabulary word "{word}" as a memorable, '
                f"clear visual cue. No letters or captions. {detail}"
            ),
            "width": 1024, "height": 1024,
        }, timeout=TIMEOUT,
    )
    payload = upstream_json(response)
    entries = payload.get("data")
    if not isinstance(entries, list) or not entries or not isinstance(entries[0], dict):
        abort(502, "The image model returned no image.")
    encoded = entries[0].get("b64_json")
    if not isinstance(encoded, str) or len(encoded) > 24 * 1024 * 1024:
        abort(502, "The image model returned an invalid image payload.")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        abort(502, "The image model returned invalid base64.")
    if (
        len(image_bytes) < 33 or image_bytes[:8] != b"\x89PNG\r\n\x1a\n"
        or image_bytes[12:16] != b"IHDR"
        or struct.unpack(">II", image_bytes[16:24]) != (1024, 1024)
    ):
        abort(502, "The image model did not return the requested PNG.")
    return Response(image_bytes, mimetype="image/png")


@app.post("/mnemonic")
def mnemonic():
    data = json_body()
    word = text_field(data, "word")
    base, headers = gateway_settings()
    response = httpx.post(
        f"{base}/mai/v1/chat/completions", headers=headers,
        json={
            "model": os.getenv("MAI_THINKING_DEPLOYMENT", "mai-thinking"),
            "messages": [{"role": "user", "content": (
                f"Write one short, imaginative English mnemonic for the English word "
                f"{word!r}. Use at most two sentences. Do not claim that it is a verified fact."
            )}],
            "max_completion_tokens": 2048,
        }, timeout=TIMEOUT,
    )
    payload = upstream_json(response)
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        abort(502, "The reasoning model returned no suggestion.")
    message = choices[0].get("message")
    text = message.get("content") if isinstance(message, dict) else None
    if not isinstance(text, str) or not text.strip():
        abort(502, "No text suggestion was returned. The model may have exhausted its output budget.")
    return jsonify(text=text.strip())
