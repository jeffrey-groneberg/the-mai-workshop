import base64
import importlib.util
import io
import json
import struct
import sys
import wave
import zlib
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("workshop_solution", ROOT / "solution/app.py")
backend = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = backend
spec.loader.exec_module(backend)


def wav_bytes(seconds=0.1, rate=16000):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(struct.pack("<h", 1200) * int(rate * seconds))
    return buffer.getvalue()


def png_bytes():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    raw = (b"\x00" + b"\x6e\x8a\x65" * 1024) * 1024
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1024, 1024, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    )


@pytest.fixture(autouse=True)
def no_live_requests(monkeypatch):
    monkeypatch.setenv("APIM_BASE_URL", "https://workshop.example.test")
    monkeypatch.setenv("APIM_API_KEY", "test-key-not-a-real-credential")
    monkeypatch.delenv("MAI_IMAGE_DEPLOYMENT", raising=False)
    monkeypatch.delenv("MAI_THINKING_DEPLOYMENT", raising=False)
    monkeypatch.setitem(backend.app.config, "TESTING", True)

    def blocked(*args, **kwargs):
        raise AssertionError("A test attempted an unmocked upstream request.")
    monkeypatch.setattr(backend.httpx, "post", blocked)


@pytest.fixture
def client():
    return backend.app.test_client()


def post(client, path, **kwargs):
    return client.post(path, headers={"Origin": "http://localhost"}, **kwargs)


def upstream(monkeypatch, *, payload=None, content=None, status=200, headers=None):
    calls = []
    def fake(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(
            status, json=payload if content is None else None, content=content,
            headers=headers, request=httpx.Request("POST", url),
        )
    monkeypatch.setattr(backend.httpx, "post", fake)
    return calls


def test_page_does_not_expose_credentials(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"test-key-not-a-real-credential" not in response.data
    assert b"workshop.example.test" not in response.data
    assert b"Model access is checked when you use a feature" in response.data
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_starter_runs_without_completed_features():
    starter_spec = importlib.util.spec_from_file_location("workshop_starter", ROOT / "starter/app.py")
    starter = importlib.util.module_from_spec(starter_spec)
    sys.modules[starter_spec.name] = starter
    starter_spec.loader.exec_module(starter)
    starter_client = starter.app.test_client()
    response = starter_client.get("/")
    assert response.status_code == 200
    assert b"apple" in response.data
    assert b"Your starting app:" in response.data
    assert starter_client.get("/static/style.css").status_code == 200
    script = starter_client.get("/static/app.js").data
    assert b"MediaRecorder" not in script and b"localStorage" not in script
    assert starter_client.post("/speak").status_code == 404


def test_missing_configuration_is_not_fake_success(client, monkeypatch):
    monkeypatch.delenv("APIM_API_KEY")
    assert client.get("/").status_code == 200
    response = post(client, "/speak", json={"text": "apple", "locale": "en-US"})
    assert response.status_code == 503
    assert "Configure" in response.json["error"]


@pytest.mark.parametrize("base", [
    "http://workshop.example.test", "https://workshop.example.test/mai/v1",
    "https://user:password@workshop.example.test", "https://workshop.example.test?api-key=bad",
    "https://workshop.example.test:invalid", "https://[broken", "https://workshop.example.test:0",
])
def test_invalid_gateway_configuration(client, monkeypatch, base):
    monkeypatch.setenv("APIM_BASE_URL", base)
    assert post(client, "/speak", json={"text": "apple", "locale": "en-US"}).status_code == 503


def test_configuration_copy_whitespace_is_normalized(client, monkeypatch):
    monkeypatch.setenv("APIM_BASE_URL", "  https://workshop.example.test/ \n")
    monkeypatch.setenv("APIM_API_KEY", "  test-key-not-a-real-credential\n")
    calls = upstream(monkeypatch, content=wav_bytes())
    assert post(client, "/speak", json={"text": "apple", "locale": "en-US"}).status_code == 200
    assert calls[0][0] == "https://workshop.example.test/speech/tts"
    assert calls[0][1]["headers"]["api-key"] == "test-key-not-a-real-credential"


def test_invalid_key_format_is_not_logged_or_forwarded(client, monkeypatch):
    monkeypatch.setenv("APIM_API_KEY", "line1\nline2")
    response = post(client, "/speak", json={"text": "apple", "locale": "en-US"})
    assert response.status_code == 503
    assert b"line1" not in response.data

def test_cross_origin_and_missing_origin_are_denied(client):
    assert client.post("/speak", json={}).status_code == 403
    response = client.post("/speak", json={}, headers={"Origin": "https://untrusted.example"})
    assert response.status_code == 403
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.parametrize("port", [5050, 5051])
def test_exact_codespaces_origin(client, monkeypatch, port):
    host = f"learning-space-{port}.app.github.dev"
    monkeypatch.setattr(backend, "codespace_hosts", {host})
    monkeypatch.setitem(backend.app.config, "TRUSTED_HOSTS", [host])
    upstream(monkeypatch, content=wav_bytes())
    response = client.post(
        "/speak", json={"text": "apple", "locale": "en-US"},
        base_url=f"https://{host}", headers={"Origin": f"https://{host}"},
    )
    assert response.status_code == 200
    assert client.post(
        "/speak", json={"text": "apple", "locale": "en-US"},
        base_url=f"https://{host}", headers={"Origin": "https://another-space-5050.app.github.dev"},
    ).status_code == 403


def test_unknown_host_denied(client):
    assert client.get("/", base_url="https://untrusted.example").status_code == 400


@pytest.mark.parametrize("locale", list(backend.LANGUAGES))
def test_speech_contract_and_all_voice_mappings(client, monkeypatch, locale):
    calls = upstream(monkeypatch, content=wav_bytes())
    response = post(client, "/speak", json={"text": "apple & <pear>", "locale": locale})
    assert response.status_code == 200
    assert response.mimetype == "audio/wav"
    url, options = calls[0]
    assert url == "https://workshop.example.test/speech/tts"
    assert options["headers"]["api-key"] == "test-key-not-a-real-credential"
    assert "Ocp-Apim-Subscription-Key" not in options["headers"]
    assert options["headers"]["X-Microsoft-OutputFormat"] == "riff-16khz-16bit-mono-pcm"
    assert backend.LANGUAGES[locale]["voice"].encode() in options["content"]
    assert b"apple &amp; &lt;pear&gt;" in options["content"]


@pytest.mark.parametrize("body", [
    [], {"text": "", "locale": "de-DE"}, {"text": "word", "locale": "ja-JP"},
    {"text": "x" * 121, "locale": "de-DE"}, {"text": "\x00", "locale": "de-DE"},
    {"text": "\ud800", "locale": "de-DE"}, {"text": "word", "locale": []},
])
def test_invalid_speech_input(client, body):
    assert post(client, "/speak", json=body).status_code == 400


def test_wrong_speech_response_is_failure(client, monkeypatch):
    upstream(monkeypatch, content=b"<html>login required</html>")
    assert post(client, "/speak", json={"text": "apple", "locale": "en-US"}).status_code == 502


def test_native_transcription_contract(client, monkeypatch):
    calls = upstream(monkeypatch, payload={"combinedPhrases": [{"text": "Apfel."}]})
    audio = wav_bytes()
    response = post(client, "/transcribe", data={
        "locale": "de-DE", "audio": (io.BytesIO(audio), "answer.wav"),
    })
    assert response.json == {"text": "Apfel."}
    url, options = calls[0]
    assert url.endswith("/speech/transcribe")
    assert options["params"] == {"api-version": "2025-10-15"}
    definition = json.loads(options["data"]["definition"])
    assert definition == {
        "enhancedMode": {"enabled": True, "model": "MAI-Transcribe-2"}, "locales": ["de"],
    }
    assert "phraseList" not in definition
    assert options["files"]["audio"] == ("answer.wav", audio, "audio/wav")


@pytest.mark.parametrize("audio", [b"webm-not-wav", wav_bytes(13), wav_bytes(rate=8000), wav_bytes()[:-8]])
def test_bad_wav_is_rejected_before_model_call(client, audio):
    response = post(client, "/transcribe", data={"locale": "de-DE", "audio": (io.BytesIO(audio), "fake.wav")})
    assert response.status_code == 400


@pytest.mark.parametrize("payload,status", [
    ({}, 502), ({"combinedPhrases": []}, 422),
    ({"combinedPhrases": [{"text": ""}]}, 422),
    ({"combinedPhrases": [{"text": 42}]}, 502),
])
def test_unusable_transcript_is_not_wrong_answer(client, monkeypatch, payload, status):
    upstream(monkeypatch, payload=payload)
    response = post(client, "/transcribe", data={"locale": "de-DE", "audio": (io.BytesIO(wav_bytes()), "answer.wav")})
    assert response.status_code == status
    assert "text" not in response.json


def test_request_size_limit(client):
    assert post(client, "/transcribe", data=b"x" * (2 * 1024 * 1024 + 1)).status_code == 413


def test_image_contract_and_binary_response(client, monkeypatch):
    image = png_bytes()
    calls = upstream(monkeypatch, payload={"data": [{"b64_json": base64.b64encode(image).decode()}]})
    response = post(client, "/image", json={"word": "bank", "detail": "Beside a river"})
    assert response.status_code == 200 and response.mimetype == "image/png"
    assert response.data == image
    url, options = calls[0]
    assert url.endswith("/mai/v1/images/generations")
    assert options["json"]["model"] == "mai-image-flash"
    assert options["json"]["width"] == options["json"]["height"] == 1024
    assert "Beside a river" in options["json"]["prompt"]
    assert not {"size", "quality", "n", "response_format"} & options["json"].keys()


@pytest.mark.parametrize("payload", [
    {}, {"data": []}, {"data": [None]}, {"data": [{"b64_json": "not base64!"}]},
    {"data": [{"b64_json": base64.b64encode(b"not a PNG").decode()}]},
])
def test_invalid_images_are_errors(client, monkeypatch, payload):
    upstream(monkeypatch, payload=payload)
    assert post(client, "/image", json={"word": "apple"}).status_code == 502


def test_optional_mnemonic_is_plain_text(client, monkeypatch):
    calls = upstream(monkeypatch, payload={"choices": [{"message": {"content": "An apple a daydream."}}]})
    response = post(client, "/mnemonic", json={"word": "apple"})
    assert response.json == {"text": "An apple a daydream."}
    assert calls[0][0].endswith("/mai/v1/chat/completions")
    assert calls[0][1]["json"]["model"] == "mai-thinking"
    assert "response_format" not in calls[0][1]["json"]


@pytest.mark.parametrize("payload", [{}, {"choices": []}, {"choices": [{"message": {"content": ""}}]}])
def test_empty_mnemonic_is_not_success(client, monkeypatch, payload):
    upstream(monkeypatch, payload=payload)
    assert post(client, "/mnemonic", json={"word": "apple"}).status_code == 502


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500])
def test_gateway_errors_are_visible_and_redacted(client, monkeypatch, status):
    calls = upstream(monkeypatch, status=status, payload={"secret": "test-key-not-a-real-credential"}, headers={"Retry-After": "9"})
    response = post(client, "/speak", json={"text": "apple", "locale": "en-US"})
    assert response.status_code == (502 if status == 500 else status)
    assert "error" in response.json
    assert b"test-key-not-a-real-credential" not in response.data
    assert len(calls) == 1
    if status == 429:
        assert response.headers["Retry-After"] == "9"


def test_gateway_timeout(client, monkeypatch):
    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout("private upstream details")
    monkeypatch.setattr(backend.httpx, "post", timeout)
    response = post(client, "/speak", json={"text": "apple", "locale": "en-US"})
    assert response.status_code == 504
    assert b"private upstream" not in response.data
