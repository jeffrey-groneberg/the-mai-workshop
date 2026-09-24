import json
import os
import threading

import httpx
import pytest
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

from test_app import backend, helpers, png_bytes, wav_bytes


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setenv("APIM_BASE_URL", "https://fake-gateway.example.test")
    monkeypatch.setenv("APIM_API_KEY", "browser-test-secret")
    calls = []
    state = {"transcript": "Apfel.", "failure": None}

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        req = httpx.Request("POST", url)
        if state["failure"]:
            headers = {"retry-after-ms": "16427"} if state["failure"] == 429 else None
            return httpx.Response(state["failure"], json={"error": "private detail"}, headers=headers, request=req)
        if url.endswith("/speech/tts"):
            return httpx.Response(200, content=wav_bytes(), request=req)
        if url.endswith("/speech/transcribe"):
            if state.get("response_gate"):
                state["response_gate"].wait(timeout=5)
            return httpx.Response(200, json={"combinedPhrases": [{"text": state["transcript"]}]}, request=req)
        if url.endswith("/images/generations"):
            import base64
            return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(png_bytes()).decode()}]}, request=req)
        if url.endswith("/chat/completions"):
            return httpx.Response(200, json={"choices": [{"message": {"content": "<script>not executed</script> Remember the apple."}}]}, request=req)
        raise AssertionError(f"Unexpected upstream path: {url}")

    monkeypatch.setattr(backend.httpx, "post", fake_post)
    app_server = make_server("127.0.0.1", 0, backend.app, threaded=True)
    thread = threading.Thread(target=app_server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{app_server.server_port}", calls, state
    finally:
        app_server.shutdown()
        thread.join(timeout=5)
        app_server.server_close()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel=os.getenv("PLAYWRIGHT_BROWSER_CHANNEL") or None,
            args=["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream", "--mute-audio"],
        )
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
    page = context.new_page()
    yield page
    context.close()


def add_word(page, english="apple", target="Apfel", locale="de-DE"):
    page.locator("#target-locale").select_option(locale)
    page.locator("#english-word").fill(english)
    page.locator("#target-word").fill(target)
    page.get_by_role("button", name="Add to my words").click()
    expect(page.locator("#practice-word")).to_have_text(english)


def test_vocabulary_persistence_and_literal_text(page, server):
    url, calls, _ = server
    page.goto(url)
    add_word(page, "<script>apple</script>", "Apfel")
    expect(page.locator("#practice-word")).to_have_text("<script>apple</script>")
    page.reload()
    expect(page.locator("#practice-word")).to_have_text("<script>apple</script>")
    page.get_by_role("button", name="Reveal translation").click()
    expect(page.locator("#saved-translation")).to_have_text("Apfel")
    assert not calls
    assert "browser-test-secret" not in page.content()
    page.get_by_role("button", name="Remove <script>apple</script>").click()
    expect(page.locator("#practice-empty")).to_be_visible()


def test_bilingual_playback_and_download(page, server):
    url, calls, _ = server
    page.goto(url)
    add_word(page)
    page.get_by_role("button", name="Hear English", exact=True).click()
    expect(page.locator("#model-status")).to_be_empty()
    page.get_by_role("button", name="Hear translation", exact=True).click()
    expect(page.locator("#model-status")).to_be_empty()
    bodies = [options["content"].decode() for _, options in calls]
    assert "en-US-Harper:MAI-Voice-2-Flash" in bodies[0]
    assert "de-DE-Mia:MAI-Voice-2-Flash" in bodies[1]
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Download synthetic WAV").click()
    download = download_info.value
    assert download.suggested_filename == "sample-de-DE.wav"
    assert len(calls) == 2  # A successful identical utterance is cached in this page.


def test_synthetic_upload_match_mismatch_and_no_words(page, server):
    url, calls, state = server
    page.goto(url)
    add_word(page)
    page.locator("#audio-file").set_input_files({
        "name": "answer.wav", "mimeType": "audio/wav", "buffer": wav_bytes(),
    })
    expect(page.locator("#audio-preview")).to_be_visible()
    assert not calls
    page.get_by_role("button", name="Send for transcription").click()
    expect(page.locator("#app-error")).to_contain_text("Choose whether")
    assert not calls
    page.locator("#audio-consent").check()
    page.get_by_role("button", name="Send for transcription").click()
    expect(page.locator("#answer-result")).to_contain_text("That matches")
    state["transcript"] = "Birne."
    page.get_by_role("button", name="Send for transcription").click()
    expect(page.locator("#answer-result")).to_contain_text("Not a match")
    state["transcript"] = ""
    page.get_by_role("button", name="Send for transcription").click()
    expect(page.locator("#app-error")).to_contain_text("No words were recognized")
    expect(page.locator("#answer-result")).to_be_hidden()


def test_real_browser_recording_emits_pcm_wav(page, server):
    url, calls, _ = server
    page.goto(url)
    add_word(page)
    page.locator("#audio-consent").check()
    page.get_by_role("button", name="Record answer", exact=True).click()
    expect(page.locator("#record-status")).to_contain_text("Recording locally")
    page.wait_for_timeout(350)  # Collect nonempty synthetic microphone frames.
    page.get_by_role("button", name="Stop recording").click()
    expect(page.locator("#recording-review")).to_be_visible(timeout=15000)
    assert not calls
    page.get_by_role("button", name="Send for transcription").click()
    expect(page.locator("#answer-result")).to_contain_text("That matches")
    audio = calls[0][1]["files"]["audio"][1]
    helpers.check_wav(audio)
    assert audio[:4] == b"RIFF"


def test_withdrawing_consent_discards_an_in_flight_transcript(page, server):
    url, calls, state = server
    page.goto(url)
    add_word(page)
    page.locator("#audio-consent").check()
    page.locator("#audio-file").set_input_files({
        "name": "answer.wav", "mimeType": "audio/wav", "buffer": wav_bytes(),
    })
    gate = threading.Event()
    state["response_gate"] = gate
    page.get_by_role("button", name="Send for transcription").click()
    expect(page.locator("#discard-recording")).to_be_disabled()
    expect(page.locator("#audio-consent")).to_be_enabled()
    page.locator("#audio-consent").uncheck()
    gate.set()
    expect(page.locator("#record-status")).to_have_text("Local recording discarded.")
    expect(page.locator("#model-status")).to_be_empty()
    expect(page.locator("#answer-result")).to_be_hidden()
    expect(page.locator("#recording-review")).to_be_hidden()
    assert len(calls) == 1


def test_word_switching_waits_for_the_current_action(page, server):
    url, calls, state = server
    page.goto(url)
    add_word(page)
    add_word(page, "pear", "Birne")
    page.locator("#audio-consent").check()
    page.locator("#audio-file").set_input_files({
        "name": "answer.wav", "mimeType": "audio/wav", "buffer": wav_bytes(),
    })
    gate = threading.Event()
    state["response_gate"] = gate
    state["transcript"] = "Birne."
    page.get_by_role("button", name="Send for transcription").click()
    expect(page.get_by_role("button", name="apple / de-DE", exact=True)).to_be_disabled()
    assert page.evaluate("selectWord(words[0].id) ?? document.querySelector('#app-error').textContent") \
        == "Wait for the current action to finish."
    gate.set()
    expect(page.locator("#answer-result")).to_contain_text("That matches")
    expect(page.locator("#practice-word")).to_have_text("pear")


def test_permission_denied_and_late_permission_cleanup(page, server):
    url, calls, _ = server
    page.add_init_script("""
      navigator.mediaDevices.getUserMedia = () =>
        Promise.reject(new DOMException("declined", "NotAllowedError"));
    """)
    page.goto(url)
    add_word(page)
    page.locator("#audio-consent").check()
    page.get_by_role("button", name="Record answer", exact=True).click()
    expect(page.locator("#app-error")).to_contain_text("Microphone access was declined")
    expect(page.locator("#record-answer")).to_be_enabled()
    assert not calls


def test_cancel_while_permission_is_pending_releases_tracks(page, server):
    url, calls, _ = server
    page.add_init_script("""
      const original = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
      navigator.mediaDevices.getUserMedia = async (constraints) => {
        const stream = await original(constraints);
        window.fakeStream = stream;
        for (const track of stream.getTracks()) {
          const stop = track.stop.bind(track);
          track.stop = () => {
            stop();
            document.documentElement.dataset.tracksStopped =
              String(stream.getTracks().every(item => item.readyState === "ended"));
          };
        }
        return new Promise(resolve => {
          window.releasePermission = () => resolve(stream);
          document.documentElement.dataset.permissionPending = "true";
        });
      };
    """)
    page.goto(url)
    add_word(page)
    page.locator("#audio-consent").check()
    page.get_by_role("button", name="Record answer", exact=True).click()
    expect(page.locator("html")).to_have_attribute("data-permission-pending", "true")
    page.get_by_role("button", name="Stop recording").click()
    page.evaluate("window.releasePermission()")
    expect(page.locator("html")).to_have_attribute("data-tracks-stopped", "true")
    expect(page.locator("#recording-review")).to_be_hidden()
    assert not calls


def test_image_and_mnemonic_are_visible_not_html(page, server):
    url, calls, _ = server
    page.goto(url)
    add_word(page)
    page.locator("#image-detail").fill("An apple wearing a crown")
    page.get_by_role("button", name="Make a memory image").click()
    expect(page.locator("#memory-figure")).to_be_visible()
    assert page.locator("#memory-image").evaluate("(image) => image.naturalWidth") == 1024
    add_word(page, "pear", "Birne")
    expect(page.locator("#memory-figure")).to_be_hidden()
    page.get_by_role("button", name="apple / de-DE", exact=True).click()
    expect(page.locator("#memory-figure")).to_be_visible()
    expect(page.locator("#image-detail")).to_have_value("An apple wearing a crown")
    assert len(calls) == 1
    page.locator("summary").click()
    page.get_by_role("button", name="Suggest a mnemonic").click()
    expect(page.locator("#mnemonic-result")).to_contain_text("<script>not executed</script>")
    assert page.locator("#mnemonic-result script").count() == 0
    assert len(calls) == 2


def test_rate_limit_and_changed_selection(page, server):
    url, calls, state = server
    page.goto(url)
    add_word(page)
    state["failure"] = 429
    page.get_by_role("button", name="Hear English", exact=True).click()
    expect(page.locator("#app-error")).to_contain_text("rate limited")
    expect(page.locator("#app-error")).to_contain_text("Retry after 17 seconds.")
    expect(page.locator("#speak-english")).to_be_enabled()
    assert len(calls) == 1
    state["failure"] = None
    add_word(page, "pear", "Birne")
    expect(page.locator("#answer-result")).to_be_hidden()
    expect(page.locator("#memory-figure")).to_be_hidden()


@pytest.mark.parametrize("left,right,locale,equal", [
    (" APFEL! ", "Apfel", "de-DE", True),
    ("cafe\u0301.", "caf\u00e9", "fr-FR", True),
    ("cafe", "caf\u00e9", "fr-FR", False),
    ("Stra\u00dfe", "Strasse", "de-DE", False),
    ("I", "\u0131", "tr-TR", True),
    ("\u0130", "i", "tr-TR", True),
    ("l'avion", "lavion", "fr-FR", False),
    ("ice-cream", "icecream", "en-US", False),
    ("a   word", "a word", "en-US", True),
])
def test_conservative_matching(page, server, left, right, locale, equal):
    page.goto(server[0])
    actual = page.evaluate(
        "([a,b,locale]) => normalizeAnswer(a,locale) === normalizeAnswer(b,locale)",
        [left, right, locale],
    )
    assert actual is equal


def test_wav_encoder_shape_and_mobile_layout(page, server):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(server[0])
    add_word(page)
    data = page.evaluate("""async () => Array.from(new Uint8Array(
      await encodeWav(new Float32Array([-1, 0, 1])).arrayBuffer()
    ))""")
    assert bytes(data[:4]) == b"RIFF"
    assert bytes(data[24:28]) == b"\x80\x3e\x00\x00"
    assert bytes(data[44:]) == b"\x00\x80\x00\x00\xff\x7f"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_corrupt_storage_is_explicit(page, server):
    page.goto(server[0])
    page.evaluate("localStorage.setItem('mai-learner-words-v1', '{broken')")
    page.reload()
    expect(page.locator("#app-error")).to_contain_text("Nothing was overwritten")
    assert page.evaluate("localStorage.getItem('mai-learner-words-v1')") == "{broken"
    expect(page.locator("#reset-storage")).to_be_visible()
