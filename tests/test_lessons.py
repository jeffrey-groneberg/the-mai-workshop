"""Replay the published learner edits only in tmp_path, with no model traffic."""

import base64
import io
import json
import os
import shutil
import struct
import sys
import threading
import time
import wave
import zlib
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree

import httpx
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server
from app_loader import load_app as load_learner_app
from lesson_replay import apply_lesson
from workshop_media import RECORDED_MNEMONIC, checkpoint, example_image, walkthrough


ROOT = Path(__file__).resolve().parents[1]


def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, f"Edit must have one exact location in {path}: {old!r}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def load_app(path, name, monkeypatch):
    module, helpers = load_learner_app(path, name, monkeypatch)
    module.helpers = helpers
    module.app.config["TESTING"] = True
    return module


def wav_bytes(frames=4000, rate=16000, channels=1, width=2):
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(width)
        audio.setframerate(rate)
        audio.writeframes(b"\0" * frames * channels * width)
    return output.getvalue()


def png_bytes():
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data))
        )

    header = struct.pack(">IIBBBBB", 1024, 1024, 8, 2, 0, 0, 0)
    rows = (b"\0" + b"\xf5\xe3\xd6" * 1024) * 1024
    return (
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")
    )


def test_documented_sequence(tmp_path, monkeypatch, caplog):
    work = tmp_path / "learner"
    shutil.copytree(ROOT / "starter", work / "starter")
    app_dir = work / "starter"
    python = app_dir / "app.py"
    javascript = app_dir / "static/app.js"
    monkeypatch.setenv("APIM_BASE_URL", "https://gateway.example.test")
    monkeypatch.setenv("APIM_API_KEY", "fixture-only-not-a-real-key")
    for variable in ("CODESPACES", "CODESPACE_NAME", "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN"):
        monkeypatch.delenv(variable, raising=False)
    (work / ".env").write_text(
        "APIM_BASE_URL=https://ignored.example.test\nAPIM_API_KEY=ignored-fixture\n",
        encoding="utf-8",
    )
    media_image = example_image()
    wav = wav_bytes(frames=32000 if media_image else 4000)
    png = media_image or png_bytes()
    calls = []
    state = {"status": 200, "text": "Pomme.", "override": None, "timeout": False}

    def upstream(url, *, headers, timeout, **kwargs):
        assert url.startswith("https://gateway.example.test/")
        assert headers["api-key"] == "fixture-only-not-a-real-key"
        assert not any(key.lower() in {"authorization", "ocp-apim-subscription-key"} for key in headers)
        assert timeout.connect == 10 and timeout.read == 120
        calls.append((url, headers, kwargs))
        request = httpx.Request("POST", url)
        if state.get("demo"):
            time.sleep(0.7)
        if state["timeout"]:
            raise httpx.ReadTimeout("fixture timeout", request=request)
        if state["status"] != 200:
            return httpx.Response(
                state["status"], json={"error": "upstream-body-must-not-leak"},
                headers={"retry-after-ms": "6500"}, request=request,
            )
        if state["override"] is not None:
            value = state["override"]
            if isinstance(value, bytes):
                return httpx.Response(200, content=value, request=request)
            return httpx.Response(200, json=value, request=request)
        if url.endswith("/speech/tts"):
            assert headers["Content-Type"] == "application/ssml+xml"
            assert headers["X-Microsoft-OutputFormat"] == "riff-16khz-16bit-mono-pcm"
            assert isinstance(kwargs["content"], bytes)
            ElementTree.fromstring(kwargs["content"])
            return httpx.Response(200, content=wav, request=request)
        if url.endswith("/speech/transcribe"):
            gate = state.get("transcribe_gate")
            if gate:
                state["transcribe_started"].set()
                assert gate.wait(timeout=10), "Fixture response was not released"
            assert kwargs["params"] == {"api-version": "2025-10-15"}
            assert set(kwargs["data"]) == {"definition"}
            definition = json.loads(kwargs["data"]["definition"])
            assert definition["enhancedMode"] == {"enabled": True, "model": "MAI-Transcribe-2"}
            assert set(definition) <= {"enhancedMode", "locales"}
            name, audio, mime = kwargs["files"]["audio"]
            assert name == "answer.wav" and mime == "audio/wav"
            with wave.open(io.BytesIO(audio), "rb") as recorded:
                assert (recorded.getnchannels(), recorded.getsampwidth(), recorded.getframerate()) == (1, 2, 16000)
                assert 0 < recorded.getnframes() <= 12 * 16000
                assert len(recorded.readframes(recorded.getnframes())) == recorded.getnframes() * 2
            return httpx.Response(
                200, json={"combinedPhrases": [{"text": state["text"]}]}, request=request,
            )
        if url.endswith("/mai/v1/images/generations"):
            body = kwargs["json"]
            assert body["model"] == "mai-image-flash"
            assert (body["width"], body["height"]) == (1024, 1024)
            assert "English vocabulary word" in body["prompt"]
            return httpx.Response(
                200, json={"data": [{"b64_json": base64.b64encode(png).decode()}]}, request=request,
            )
        if url.endswith("/mai/v1/chat/completions"):
            body = kwargs["json"]
            assert body["model"] == "mai-thinking"
            assert body["max_completion_tokens"] == 2048
            assert body["messages"][0]["role"] == "user"
            assert "French word 'pomme' means 'apple'" in body["messages"][0]["content"]
            text = RECORDED_MNEMONIC if state.get("demo") else "<b>A sample mnemonic.</b>"
            return httpx.Response(
                200, json={"choices": [{"message": {"content": text}}]},
                request=request,
            )
        raise AssertionError(f"Unexpected gateway call: {url}")

    monkeypatch.setattr(httpx, "post", upstream)
    module = load_app(python, "lesson_open", monkeypatch)
    assert calls == []
    server = make_server("127.0.0.1", 0, module.app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    with urlopen(origin) as response:
        assert response.status == 200

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                channel=os.getenv("PLAYWRIGHT_BROWSER_CHANNEL") or None,
                args=[
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
                "--mute-audio",
                ],
            )
            context = browser.new_context(permissions=["microphone"], accept_downloads=True)
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(origin)
            expect(page.locator("#starter-status")).to_contain_text("JavaScript is connected")
            assert page.locator("#word-form").count() == 0
            assert calls == []
            checkpoint(page, "00-open-app", ".app-shell")

            apply_lesson(app_dir, "01-word-list")
            module = load_app(python, "lesson_words", monkeypatch)
            server.app = module.app
            page.reload()
            assert page.locator("#target-locale option").count() == 17
            page.locator("#target-locale").select_option("fr-FR")
            page.locator("#english-word").fill("apple")
            page.locator("#target-word").fill("pomme")
            page.locator("#word-form button").click()
            page.locator("#english-word").fill("summer")
            page.locator("#target-word").fill("été")
            page.locator("#word-form button").click()
            expect(page.locator("#word-count")).to_have_text("2")
            page.reload()
            expect(page.locator("#word-count")).to_have_text("2")
            page.get_by_role("button", name="summer / fr-FR", exact=True).click()
            page.locator("#reveal-answer").click()
            expect(page.locator("#saved-translation")).to_have_text("été")
            expect(page.locator("#reveal-answer")).to_have_text("Hide translation")
            page.get_by_role("button", name="Remove summer", exact=True).click()
            expect(page.locator("#practice-word")).to_have_text("apple")
            assert calls == [] and errors == []
            checkpoint(page, "01-word-list", ".workspace")

            apply_lesson(app_dir, "02-speech")
            module = load_app(python, "lesson_speech", monkeypatch)
            server.app = module.app
            page.reload()
            page.locator("#speak-english").click()
            expect(page.locator("#speech-audio")).to_be_visible()
            expect(page.locator("#speak-english")).to_be_enabled()
            assert len(calls) == 1
            assert b"en-US-Harper:MAI-Voice-2-Flash" in calls[-1][2]["content"]
            assert json.loads(page.evaluate("JSON.stringify([...speechCache.keys()])")) == ['["apple","en-US"]']
            page.locator("#speak-target").click()
            expect(page.locator("#speak-target")).to_be_enabled()
            assert b"fr-FR-Soleil:MAI-Voice-2-Flash" in calls[-1][2]["content"]
            assert b"pomme" in calls[-1][2]["content"]
            before_download = len(calls)
            with page.expect_download() as download:
                page.locator("#download-sample").click()
            sample = tmp_path / "synthetic-fr.wav"
            download.value.save_as(sample)
            assert sample.read_bytes() == wav
            assert len(calls) == before_download
            assert errors == []
            checkpoint(page, "02-bilingual-speech", ".workspace")

            apply_lesson(app_dir, "03-transcription")
            module = load_app(python, "lesson_transcribe", monkeypatch)
            server.app = module.app
            page.reload()
            before_record = len(calls)
            page.locator("#record-answer").click()
            expect(page.locator("#app-error")).to_contain_text("approved audio guidance")
            assert len(calls) == before_record
            page.locator("#audio-consent").check()
            page.evaluate("""() => {
                navigator.mediaDevices.getUserMedia = async () => {
                    throw new DOMException("Fixture denial", "NotAllowedError");
                };
            }""")
            page.locator("#record-answer").click()
            expect(page.locator("#app-error")).to_contain_text("Microphone access was declined")
            expect(page.locator("#stop-recording")).to_be_hidden()
            expect(page.locator("#record-status")).to_contain_text("Recording did not finish")
            assert len(calls) == before_record
            page.reload()
            page.locator("#audio-consent").check()
            page.evaluate("Object.defineProperty(navigator, 'mediaDevices', {value: undefined})")
            page.locator("#record-answer").click()
            expect(page.locator("#app-error")).to_contain_text("Recording is unavailable")
            assert len(calls) == before_record
            page.reload()
            page.locator("#audio-consent").check()
            page.evaluate("""() => {
                const original = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
                navigator.mediaDevices.getUserMedia = async (constraints) => {
                    const stream = await original(constraints);
                    window.testTracks = stream.getTracks();
                    return stream;
                };
            }""")
            page.locator("#record-answer").click()
            expect(page.locator("#record-status")).to_contain_text("Recording locally")
            page.wait_for_timeout(350)
            page.locator("#stop-recording").click()
            expect(page.locator("#record-status")).to_contain_text("Ready to preview locally")
            assert page.evaluate("window.testTracks.every(track => track.readyState === 'ended')")
            assert len(calls) == before_record
            page.locator("#audio-preview").evaluate("audio => audio.play()")
            page.locator("#send-answer").click()
            expect(page.locator("#answer-result")).to_have_text("I heard: Pomme.")
            assert len(calls) == before_record + 1
            checkpoint(page, "03-transcription", ".practice-step")
            assert json.loads(calls[-1][2]["data"]["definition"])["locales"] == ["fr"]
            storage = page.evaluate("JSON.parse(localStorage.getItem('mai-learner-words-v1'))")
            assert set(storage[0]) == {"id", "english", "target", "locale"}
            encoded = bytes(page.evaluate("""async () => Array.from(new Uint8Array(
                await encodeWav(new Float32Array([-2, -1, 0, 1, 2])).arrayBuffer()
            ))"""))
            with wave.open(io.BytesIO(encoded), "rb") as audio:
                assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, 16000)
                assert struct.unpack("<5h", audio.readframes(5)) == (-32768, -32768, 0, 32767, 32767)
            assert errors == []

            page.locator("#record-answer").click()
            expect(page.locator("#record-status")).to_contain_text("Recording locally")
            page.locator("#audio-consent").uncheck()
            expect(page.locator("#stop-recording")).to_be_hidden()
            expect(page.locator("#recording-review")).to_be_hidden()
            assert page.evaluate("window.testTracks.every(track => track.readyState === 'ended')")
            assert len(calls) == before_record + 1
            page.locator("#audio-file").set_input_files({
                "name": "not-really.wav", "mimeType": "audio/wav", "buffer": b"not a WAV",
            })
            expect(page.locator("#app-error")).to_contain_text("This is not a WAV file")
            expect(page.locator("#recording-review")).to_be_hidden()
            page.locator("#audio-file").set_input_files(str(sample))
            expect(page.locator("#record-status")).to_contain_text("Ready to preview locally")
            assert len(calls) == before_record + 1
            page.locator("#send-answer").click()
            expect(page.locator("#app-error")).to_contain_text("Choose whether to send sample audio")
            assert len(calls) == before_record + 1
            page.locator("#audio-consent").check()
            page.locator("#send-answer").click()
            expect(page.locator("#answer-result")).to_have_text("I heard: Pomme.")
            assert calls[-1][2]["files"]["audio"][1] == wav
            page.locator("#audio-consent").uncheck()
            expect(page.locator("#recording-review")).to_be_hidden()
            assert_pending_permission_fallback(page, sample, calls, state)

            apply_lesson(app_dir, "04-matching")
            page.reload()
            page.locator("#audio-consent").check()
            page.locator("#audio-file").set_input_files(str(sample))
            expect(page.locator("#record-status")).to_contain_text("Ready to preview locally")
            page.locator("#send-answer").click()
            expect(page.locator("#answer-result")).to_contain_text("That matches your saved translation.")
            checkpoint(page, "04-answer-match", "#answer-result")
            state["text"] = "rivière"
            page.locator("#send-answer").click()
            expect(page.locator("#answer-result")).to_contain_text("Not a match this time.")
            expect(page.locator("#answer-result")).to_contain_text("I heard: rivière")
            expect(page.locator("#answer-result")).to_contain_text("Saved answer: pomme")
            state["text"] = ""
            page.locator("#send-answer").click()
            expect(page.locator("#app-error")).to_contain_text("No words were recognized")
            expect(page.locator("#answer-result")).to_be_hidden()
            state["text"] = "Pomme."
            cases = [
                (" POMME! ", "pomme", "fr-FR", True),
                ("e\u0301te\u0301", "été", "fr-FR", True),
                ("été", "ete", "fr-FR", False),
                ("Straße", "Strasse", "de-DE", False),
                ("STRASSE", "strasse", "de-DE", True),
                ("l'été", "lété", "fr-FR", False),
                ("arc-en-ciel", "arc en ciel", "fr-FR", False),
                ("une pomme", "pomme", "fr-FR", False),
                ("iki   elma", "iki elma", "tr-TR", True),
                ("İ", "i", "tr-TR", True),
            ]
            for heard, saved, locale, matches in cases:
                assert page.evaluate(
                    "([a,b,locale]) => normalizeAnswer(a,locale) === normalizeAnswer(b,locale)",
                    [heard, saved, locale],
                ) is matches
            assert errors == []

            apply_lesson(app_dir, "05-images")
            module = load_app(python, "lesson_image", monkeypatch)
            server.app = module.app
            page.reload()
            page.locator("#image-detail").fill("A single apple on a picnic blanket, soft watercolor")
            page.locator("#generate-image").click()
            expect(page.locator("#memory-figure")).to_be_visible()
            assert page.locator("#memory-image").evaluate("image => image.naturalWidth") == 1024
            assert calls[-1][2]["json"]["prompt"].endswith("soft watercolor")
            checkpoint(page, "05-memory-image", ".practice-step:has(#generate-image)")
            page.locator("#english-word").fill("river")
            page.locator("#target-word").fill("rivière")
            page.locator("#target-locale").select_option("fr-FR")
            page.locator("#word-form button").click()
            expect(page.locator("#memory-figure")).to_be_hidden()
            before_select = len(calls)
            page.get_by_role("button", name="apple / fr-FR", exact=True).click()
            expect(page.locator("#memory-figure")).to_be_visible()
            assert len(calls) == before_select
            page.locator("#image-detail").fill("A single apple, pencil drawing")
            page.locator("#generate-image").click()
            expect(page.locator("#generate-image")).to_be_enabled()
            assert len(calls) == before_select + 1
            assert calls[-1][2]["json"]["prompt"].endswith("pencil drawing")
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.reload()
            expect(page.locator("#word-count")).to_have_text("2")
            expect(page.locator("#memory-figure")).to_be_hidden()
            assert errors == []

            apply_lesson(app_dir, "06-mnemonics")
            module = load_app(python, "lesson_mnemonic", monkeypatch)
            server.app = module.app
            page.reload()
            page.locator(".extension summary").click()
            page.locator("#generate-mnemonic").click()
            expect(page.locator("#mnemonic-result")).to_have_text("<b>A sample mnemonic.</b>")
            assert page.locator("#mnemonic-result b").count() == 0
            page.get_by_role("button", name="river / fr-FR", exact=True).click()
            expect(page.locator("#mnemonic-result")).to_have_text("")
            assert errors == []

            assert_gateway_failures(module, wav, png, state, calls, monkeypatch)
            assert_origin_boundary(python, monkeypatch, wav)
            baseline = python.read_text(encoding="utf-8")
            replace_once(python, '        "locales": [language["stt"]],\n', "")
            detection = load_app(python, "lesson_detection_experiment", monkeypatch)
            result = detection.app.test_client().post(
                "/transcribe", headers={"Origin": "http://localhost"},
                data={"locale": "fr-FR", "audio": (io.BytesIO(wav), "sample.wav")},
            )
            assert result.status_code == 200
            assert "locales" not in json.loads(calls[-1][2]["data"]["definition"])
            python.write_text(baseline, encoding="utf-8")
            for private_value in ("https://gateway.example.test", "fixture-only-not-a-real-key"):
                assert private_value not in page.content()
                assert private_value not in javascript.read_text(encoding="utf-8")
                assert private_value not in caplog.text
            assert "solution" not in python.read_text(encoding="utf-8")
            assert "solution" not in javascript.read_text(encoding="utf-8")
            walkthrough(browser, origin, state)
            context.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def assert_pending_permission_fallback(page, sample, calls, state):
    for cancel_with in ("stop", "consent"):
        page.reload()
        page.locator("#audio-consent").check()
        page.evaluate("""() => {
            window.originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
            navigator.mediaDevices.getUserMedia = () => new Promise((resolve) => {
                window.resolvePermission = resolve;
            });
        }""")
        before = len(calls)
        page.locator("#record-answer").click()
        expect(page.locator("#record-status")).to_contain_text("Waiting for microphone permission")
        expect(page.locator("#audio-file")).to_be_disabled()
        if cancel_with == "stop":
            page.locator("#stop-recording").click()
        else:
            page.locator("#audio-consent").uncheck()
        expect(page.locator("#audio-file")).to_be_enabled(timeout=1000)
        expect(page.locator("#stop-recording")).to_be_hidden()
        page.locator("#audio-file").set_input_files(str(sample))
        expect(page.locator("#record-status")).to_contain_text("Ready to preview locally")
        preview = page.locator("#audio-preview").get_attribute("src")
        assert len(calls) == before
        page.locator("#audio-consent").check()

        gate = threading.Event()
        started = threading.Event()
        state["transcribe_gate"] = gate
        state["transcribe_started"] = started
        try:
            page.locator("#send-answer").click()
            assert started.wait(timeout=5), "Synthetic upload did not reach Flask"
            expect(page.locator("#model-status")).to_contain_text("MAI is transcribing")
            expect(page.locator("#audio-file")).to_be_disabled()
            page.evaluate("""async () => {
                const stream = await window.originalGetUserMedia({audio: true});
                window.lateTracks = stream.getTracks();
                for (const track of window.lateTracks) {
                    const stop = track.stop.bind(track);
                    track.stop = () => {
                        stop();
                        document.documentElement.dataset.lateTracksEnded =
                            String(window.lateTracks.every(item => item.readyState === "ended"));
                    };
                }
                window.resolvePermission(stream);
            }""")
            expect(page.locator("html")).to_have_attribute("data-late-tracks-ended", "true")
            expect(page.locator("#audio-preview")).to_have_attribute("src", preview)
            expect(page.locator("#record-status")).to_contain_text("Ready to preview locally")
            expect(page.locator("#model-status")).to_contain_text("MAI is transcribing")
            expect(page.locator("#audio-file")).to_be_disabled()
            expect(page.locator("#send-answer")).to_be_disabled()
            expect(page.locator("#app-error")).to_be_hidden()
        finally:
            gate.set()
            state.pop("transcribe_gate")
            state.pop("transcribe_started")
        expect(page.locator("#answer-result")).to_have_text("I heard: Pomme.")
        expect(page.locator("#audio-file")).to_be_enabled()
        assert len(calls) == before + 1
        assert calls[-1][2]["files"]["audio"][1] == sample.read_bytes()


def assert_gateway_failures(module, wav, png, state, calls, monkeypatch):
    client = module.app.test_client()
    headers = {"Origin": "http://localhost"}

    def speak(body=None):
        return client.post("/speak", json=body or {"text": "apple", "locale": "en-US"}, headers=headers)

    def transcribe(audio=wav):
        return client.post(
            "/transcribe", data={"locale": "fr-FR", "audio": (io.BytesIO(audio), "answer.wav")},
            headers=headers,
        )

    assert module.helpers.gateway_settings()[0] == "https://gateway.example.test"
    assert len(module.LANGUAGES) == 17
    assert module.LANGUAGES["ko-KR"]["voice"] == "ko-KR-Haena:MAI-Voice-2-Flash"
    assert "ja-JP" not in module.LANGUAGES
    for locale, language in module.LANGUAGES.items():
        response = speak({"text": 'word & <sample> "text"', "locale": locale})
        assert response.status_code == 200 and response.data == wav
        ssml = calls[-1][2]["content"].decode()
        assert language["voice"] in ssml
        assert "&amp;" in ssml and "&lt;sample&gt;" in ssml

    before_invalid = len(calls)
    for body in (
        [], {"text": "word", "locale": "ja-JP"}, {"text": "word", "locale": []},
        {"text": "", "locale": "fr-FR"}, {"text": 7, "locale": "fr-FR"},
        {"text": "a" * 121, "locale": "fr-FR"}, {"text": "\x01", "locale": "fr-FR"},
    ):
        response = client.post("/speak", json=body, headers=headers)
        assert response.status_code == 400 and "error" in response.json
    assert client.post("/speak", data="not-json", headers=headers).status_code == 415
    assert transcribe(b"not a WAV").status_code == 400
    assert transcribe(wav_bytes(frames=0)).status_code == 400
    assert transcribe(wav_bytes(rate=8000)).status_code == 400
    assert transcribe(wav_bytes(channels=2)).status_code == 400
    assert transcribe(wav_bytes(width=1)).status_code == 400
    assert transcribe(wav_bytes(frames=12 * 16000 + 1)).status_code == 400
    assert transcribe(wav[:-2]).status_code == 400
    assert transcribe(b"x" * (2 * 1024 * 1024)).status_code == 413
    assert client.post("/transcribe", data={"locale": "fr-FR"}, headers=headers).status_code == 400
    assert len(calls) == before_invalid

    for base in (
        "http://gateway.example.test", "https://gateway.example.test/speech",
        "https://user:password@gateway.example.test", "https://gateway.example.test?key=x",
        "https://[", "https://gateway.example.test:wrong", "https://gateway.example.test:65536",
        "https://gateway.example.test:0", "https://gateway example.test",
    ):
        with monkeypatch.context() as change:
            change.setenv("APIM_BASE_URL", base)
            assert speak().status_code == 503
    with monkeypatch.context() as change:
        change.delenv("APIM_API_KEY")
        assert speak().status_code == 503

    for status in (400, 401, 403, 404, 429, 500):
        state["status"] = status
        response = speak()
        assert response.status_code == (status if status != 500 else 502)
        assert "error" in response.json and "upstream-body-must-not-leak" not in response.text
        if status == 429:
            assert response.headers["Retry-After"] == "7"  # from retry-after-ms: 6500
    state["status"] = 200
    state["timeout"] = True
    assert speak().status_code == 504
    state["timeout"] = False
    state["override"] = b"not a WAV"
    assert speak().status_code == 502
    for payload in (b"not JSON", [], {"combinedPhrases": "bad"}, {"combinedPhrases": [{}]},
                    {"combinedPhrases": [{"text": 3}]}):
        state["override"] = payload
        assert transcribe().status_code == 502
    state["override"] = {"combinedPhrases": [{"text": "  "}]}
    assert transcribe().status_code == 422
    state["override"] = {"combinedPhrases": [{"text": " une "}, {"text": " pomme "}]}
    assert transcribe().json == {"text": "une pomme"}
    state["override"] = None

    image_body = {"word": "apple", "detail": ""}
    for payload in ({}, {"data": []}, {"data": [{"b64_json": "%%%"}]},
                    {"data": [{"b64_json": base64.b64encode(b"not PNG").decode()}]}):
        state["override"] = payload
        assert client.post("/image", json=image_body, headers=headers).status_code == 502
    small_png = png[:16] + struct.pack(">II", 512, 512) + png[24:]
    state["override"] = {"data": [{"b64_json": base64.b64encode(small_png).decode()}]}
    assert client.post("/image", json=image_body, headers=headers).status_code == 502
    state["override"] = None
    for detail in (7, "x" * 361):
        assert client.post("/image", json={"word": "apple", "detail": detail}, headers=headers).status_code == 400
    for payload in ({}, {"choices": []}, {"choices": [{"message": {"content": None}}]}):
        state["override"] = payload
        assert client.post(
            "/mnemonic", json={"word": "apple", "target": "pomme", "locale": "fr-FR"}, headers=headers,
        ).status_code == 502
    state["override"] = None


def assert_origin_boundary(python, monkeypatch, wav):
    with monkeypatch.context() as change:
        change.setenv("CODESPACES", "true")
        change.setenv("CODESPACE_NAME", "fixture-space")
        change.setenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
        module = load_app(python, "lesson_forwarded", change)
        client = module.app.test_client()
        body = {"text": "apple", "locale": "en-US"}
        for port in (5050, 5051):
            base = f"https://fixture-space-{port}.app.github.dev"
            result = client.post("/speak", base_url=base, json=body, headers={"Origin": base})
            assert result.status_code == 200 and result.data == wav
            assert "Access-Control-Allow-Origin" not in result.headers
            assert result.headers["Cache-Control"] == "no-store"
            assert "frame-ancestors 'none'" in result.headers["Content-Security-Policy"]
            assert client.post("/speak", base_url=base, json=body).status_code == 403
            assert client.post(
                "/speak", base_url=base, json=body, headers={"Origin": "https://other.app.github.dev"},
            ).status_code == 403
        bad = "https://unapproved.app.github.dev"
        assert client.post("/speak", base_url=bad, json=body, headers={"Origin": bad}).status_code == 400
