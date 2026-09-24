"""Provided workshop plumbing. You do not need to edit this file.

Your routes in app.py call these helpers. They keep the gateway key on the
server, accept POST requests only from this app's own page, validate input and
model output, and turn failures into short messages for the browser.
"""

import io
import os
import struct
import wave
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv
from flask import Flask, abort, current_app, jsonify, request
from werkzeug.exceptions import HTTPException

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

TIMEOUT = httpx.Timeout(120, connect=10)
PLACEHOLDER_KEYS = {"replace-me", "your-participant-key"}
GATEWAY_MESSAGES = {
    400: "The model rejected the request. Check its settings and sample input.",
    401: "Your key may be expired, rotated, or invalid. Check the workshop portal.",
    403: "Access or content was blocked. Check portal access and approved sample data.",
    404: "The gateway route or deployment was not found. Check the instructor's settings.",
    429: "The model or gateway is rate limited. Wait before trying again.",
}


def create_app(import_name):
    """Create the Flask app with the workshop's request checks and error handling."""
    app = Flask(import_name)
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["CODESPACE_HOSTS"] = codespace_hosts()
    app.config["TRUSTED_HOSTS"] = ["localhost", "127.0.0.1", *app.config["CODESPACE_HOSTS"]]
    app.before_request(require_same_origin)
    app.after_request(browser_headers)
    app.context_processor(lambda: {"gateway_configured": gateway_settings() is not None})
    app.register_error_handler(HTTPException, request_error)
    app.register_error_handler(httpx.HTTPStatusError, gateway_error)
    app.register_error_handler(httpx.RequestError, connection_error)
    return app


def codespace_hosts():
    if os.getenv("CODESPACES") != "true":
        return set()
    name = os.getenv("CODESPACE_NAME", "")
    domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "")
    if not name or not domain:
        return set()
    return {f"{name}-{port}.{domain}" for port in (5050, 5051)}


def require_same_origin():
    if request.method == "POST":
        scheme = "https" if request.host in current_app.config["CODESPACE_HOSTS"] else "http"
        if request.headers.get("Origin") != f"{scheme}://{request.host}":
            abort(403, "Open the app in its own browser tab and send from there.")


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
    """Return (origin, headers) from APIM_BASE_URL and APIM_API_KEY, or None if unusable."""
    base = os.getenv("APIM_BASE_URL", "").strip().rstrip("/")
    key = os.getenv("APIM_API_KEY", "").strip()
    try:
        parsed = urlsplit(base)
        port = parsed.port
        httpx.URL(base)
    except (ValueError, httpx.InvalidURL):
        return None
    if (
        parsed.scheme != "https" or not parsed.hostname or parsed.path
        or parsed.query or parsed.fragment or parsed.username or parsed.password
        or port == 0 or "\\" in base or any(char.isspace() for char in base)
        or not key or key in PLACEHOLDER_KEYS or not key.isascii()
        or any(char.isspace() for char in key)
    ):
        return None
    return base, {"api-key": key}


def gateway():
    """Return the gateway origin and the api-key header for a model request."""
    settings = gateway_settings()
    if settings is None:
        abort(503, "Configure APIM_BASE_URL and APIM_API_KEY, then restart Flask.")
    return settings


def json_body():
    """Return the request's JSON object."""
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400, "Send a JSON object.")
    return data


def _unsupported(value):
    return any(
        (ord(char) < 32 and char not in "\t\n\r")
        or 0xD800 <= ord(char) <= 0xDFFF or ord(char) in {0xFFFE, 0xFFFF}
        for char in value
    )


def text_field(data, name, limit=120):
    """Return a required text field, trimmed."""
    value = data.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        abort(400, f"{name} must contain 1 to {limit} characters.")
    if _unsupported(value):
        abort(400, f"{name} contains unsupported characters.")
    return value.strip()


def optional_text(data, name, limit):
    """Return an optional text field, trimmed; missing means empty."""
    value = data.get(name, "")
    if not isinstance(value, str) or len(value) > limit or _unsupported(value):
        abort(400, f"{name} must be text of up to {limit} characters.")
    return value.strip()


def check_wav(audio, max_seconds=12, error_status=400):
    """Stop unless audio is a complete mono, 16-bit, 16 kHz PCM WAV."""
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


def check_png(image, width=1024, height=1024):
    """Stop unless image is a PNG with the requested dimensions."""
    if (
        len(image) < 33 or image[:8] != b"\x89PNG\r\n\x1a\n" or image[12:16] != b"IHDR"
        or struct.unpack(">II", image[16:24]) != (width, height)
    ):
        abort(502, "The image model did not return the requested PNG.")


def upstream_json(response):
    """Raise for gateway errors, then return the response's JSON object."""
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError:
        abort(502, "The gateway returned unreadable JSON.")
    if not isinstance(payload, dict):
        abort(502, "The gateway returned an unexpected response shape.")
    return payload


def retry_after_seconds(headers):
    """Read Retry-After in seconds, or the gateway's retry-after-ms header."""
    seconds = headers.get("Retry-After", "").strip()
    if seconds.isdigit():
        return min(int(seconds), 300)
    milliseconds = headers.get("retry-after-ms", "").strip()
    if milliseconds.isdigit():
        return min(-(-int(milliseconds) // 1000), 300)
    return None


def request_error(error):
    current_app.logger.warning("App request failed: HTTP %s", error.code)
    return jsonify(error=error.description), error.code


def gateway_error(error):
    status = error.response.status_code
    current_app.logger.warning("Gateway request failed: HTTP %s", status)
    message = GATEWAY_MESSAGES.get(status, "The model service is unavailable. Try again later.")
    response = jsonify(error=message)
    response.status_code = status if status in GATEWAY_MESSAGES else 502
    retry = retry_after_seconds(error.response.headers) if status == 429 else None
    if retry is not None:
        response.headers["Retry-After"] = str(retry)
    return response


def connection_error(error):
    current_app.logger.warning("Gateway connection failed: %s", type(error).__name__)
    if not isinstance(error, httpx.TimeoutException):
        message = "The gateway could not be reached. Check your connection and APIM_BASE_URL."
    elif _read_timeout(error) < TIMEOUT.read:
        message = "The model needed longer than this request allows. Pass timeout=TIMEOUT to httpx.post."
    else:
        message = "The model did not answer in time. Try again in a moment."
    return jsonify(error=message), 504


def _read_timeout(error):
    try:
        return error.request.extensions.get("timeout", {}).get("read") or TIMEOUT.read
    except RuntimeError:
        return TIMEOUT.read
