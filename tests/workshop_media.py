"""Optional documentation capture alongside the existing offline lesson replay."""

import json
import os
import subprocess
from pathlib import Path

from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[1]
# Live MAI-Thinking-1 answer to the reference /mnemonic prompt for apple / pomme (French),
# recorded once and replayed offline for screenshots.
RECORDED_MNEMONIC = (
    "Imagine taking a big bite of a juicy pomme and going \u201cmmm\u201d\u2014that satisfied "
    "sound is all the reminder you need that it's an apple!"
)


def output_directory():
    value = os.getenv("WORKSHOP_MEDIA_DIR")
    if not value:
        return None
    directory = Path(value).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def ffmpeg(*arguments):
    try:
        return subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, arguments)],
            check=True, capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as error:
        raise RuntimeError(error.stderr.decode("utf-8", errors="replace")) from error


def example_image():
    if output_directory() is None:
        return None
    return ffmpeg(
        "-i", ROOT / "docs/assets/images/vocabulary-journey.webp",
        "-vf", "crop=320:320:30:220,scale=1024:1024",
        "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "pipe:1",
    )


def save_webp(png, destination):
    subprocess.run(
        ["cwebp", "-quiet", "-lossless", "-z", "6", str(png), "-o", str(destination)],
        check=True,
    )


def set_walkthrough_playback(path):
    """Slow the GIF 1.5x and loop it without re-encoding any image data."""
    data = bytearray(path.read_bytes())
    if data[:6] != b"GIF89a" or b"NETSCAPE2.0" in data:
        raise ValueError("Expected a newly captured, non-looping GIF89a.")
    header_end = 13 + (3 * 2 ** ((data[10] & 7) + 1) if data[10] & 128 else 0)
    cursor = header_end
    while data[cursor] != 0x3B:
        marker = data[cursor]
        cursor += 1
        if marker == 0x21:
            label = data[cursor]
            cursor += 1
            if label == 0xF9:
                if data[cursor] != 4:
                    raise ValueError("Unexpected GIF graphic-control size.")
                delay = int.from_bytes(data[cursor + 2:cursor + 4], "little")
                slower = max(1, (delay * 3 + 1) // 2)
                data[cursor + 2:cursor + 4] = slower.to_bytes(2, "little")
        elif marker == 0x2C:
            flags = data[cursor + 8]
            cursor += 9 + (3 * 2 ** ((flags & 7) + 1) if flags & 128 else 0)
            cursor += 1
        else:
            raise ValueError(f"Unexpected GIF block: {marker}")
        while data[cursor]:
            cursor += 1 + data[cursor]
        cursor += 1
    if cursor != len(data) - 1:
        raise ValueError("Unexpected data after the GIF trailer.")
    loop = b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00"
    path.write_bytes(data[:header_end] + loop + data[header_end:])


def checkpoint(page, name, selector):
    directory = output_directory()
    if directory is None:
        return
    viewport = page.viewport_size
    scroll = page.evaluate("({x: scrollX, y: scrollY})")
    page.set_viewport_size({"width": 1120, "height": 820})
    page.evaluate("document.fonts.ready")
    if page.locator("#app-error").count():
        expect(page.locator("#app-error")).to_be_hidden()
    png = directory / f"{name}.png"
    page.locator(selector).screenshot(path=str(png), animations="disabled")
    save_webp(png, directory / f"{name}.webp")
    png.unlink()
    page.set_viewport_size(viewport)
    page.evaluate("position => scrollTo(position.x, position.y)", scroll)


# The guide's own primary indigo, so the badges look like part of the docs.
# It is used only in the capture; the app's styles stay untouched.
BUILD_MAP_COLOR = "#4051b5"
BUILD_MAPS = []


def build_map(page, name, region, marks):
    """Capture `region` with numbered outlines around the elements a lesson creates.

    marks is a list; mark n (1-based) outlines the union of its selectors. A mark is either
    a list of selectors (badge left of the outline) or {"select": [...], "badge": "right"}.
    Badges sit outside the outline so they never cover the app's text. The overlay uses
    CSSOM styles, which the app's Content-Security-Policy allows.
    """
    marks = [mark if isinstance(mark, dict) else {"select": mark, "badge": "left"} for mark in marks]
    directory = output_directory()
    if directory is None:
        return
    viewport = page.viewport_size
    scroll = page.evaluate("({x: scrollX, y: scrollY})")
    page.set_viewport_size({"width": 1120, "height": 820})
    page.evaluate("document.fonts.ready")
    if page.locator("#app-error").count():
        expect(page.locator("#app-error")).to_be_hidden()
    page.locator(region).scroll_into_view_if_needed()
    clip = page.evaluate("""([region, marks, color]) => {
        const pageBox = (elements) => {
            const boxes = elements.map((element) => element.getBoundingClientRect())
                .filter((box) => box.width && box.height);
            if (!boxes.length) throw new Error("Build map target is not visible");
            const left = Math.min(...boxes.map((box) => box.left)) + scrollX;
            const top = Math.min(...boxes.map((box) => box.top)) + scrollY;
            return {left, top,
                    width: Math.max(...boxes.map((box) => box.right)) + scrollX - left,
                    height: Math.max(...boxes.map((box) => box.bottom)) + scrollY - top};
        };
        const layer = document.createElement("div");
        layer.id = "build-map-layer";
        Object.assign(layer.style, {position: "absolute", left: "0", top: "0", zIndex: "2147483647",
                                    pointerEvents: "none"});
        document.body.append(layer);
        marks.forEach((mark, index) => {
            const elements = mark.select.flatMap((selector) => [...document.querySelectorAll(selector)]);
            if (!elements.length) throw new Error(`No element for build map mark ${index + 1}`);
            const box = pageBox(elements);
            const frame = document.createElement("div");
            Object.assign(frame.style, {position: "absolute", left: `${box.left - 7}px`, top: `${box.top - 7}px`,
                                        width: `${box.width + 14}px`, height: `${box.height + 14}px`,
                                        border: `3px solid ${color}`, borderRadius: "14px", boxSizing: "border-box",
                                        boxShadow: "0 0 0 2px rgba(255, 255, 255, 0.85)"});
            const badge = document.createElement("div");
            badge.textContent = String(index + 1);
            Object.assign(badge.style, {position: "absolute", [mark.badge === "right" ? "right" : "left"]: "-44px",
                                        top: "-3px", width: "30px",
                                        height: "30px", borderRadius: "50%", background: color, color: "#fff",
                                        font: "700 16px/30px system-ui, -apple-system, sans-serif",
                                        textAlign: "center", boxShadow: "0 0 0 3px #fff"});
            frame.append(badge);
            layer.append(frame);
        });
        const area = pageBox([document.querySelector(region), ...layer.querySelectorAll("div > div")]);
        const padding = 20;
        const left = Math.max(0, area.left - padding);
        const top = Math.max(0, area.top - padding);
        return {x: left, y: top,
                width: Math.min(document.documentElement.scrollWidth - left, area.left - left + area.width + padding),
                height: area.top - top + area.height + padding};
    }""", [region, marks, BUILD_MAP_COLOR])
    png = directory / f"{name}.png"
    try:
        page.screenshot(path=str(png), clip=clip, full_page=True, animations="disabled")
    finally:
        page.evaluate("document.querySelector('#build-map-layer')?.remove()")
    save_webp(png, directory / f"{name}.webp")
    png.unlink()
    BUILD_MAPS.append({"file": f"{name}.webp", "marks": len(marks)})
    page.set_viewport_size(viewport)
    page.evaluate("position => scrollTo(position.x, position.y)", scroll)


def walkthrough(browser, origin, state):
    directory = output_directory()
    if directory is None:
        return
    state["demo"] = True
    state["text"] = "Pomme."
    context = browser.new_context(
        viewport={"width": 1120, "height": 820},
        permissions=["microphone"],
        record_video_dir=str(directory / "recording"),
        record_video_size={"width": 1120, "height": 820},
        reduced_motion="reduce",
    )
    page = context.new_page()
    video = page.video
    try:
        page.goto(origin)
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(600)
        page.locator("#target-locale").select_option("fr-FR")
        page.locator("#english-word").press_sequentially("apple", delay=70)
        page.locator("#target-word").press_sequentially("pomme", delay=70)
        page.locator("#word-form button").click()
        page.locator(".workspace").evaluate("element => element.scrollIntoView({block: 'start'})")
        page.locator("#reveal-answer").click()
        page.wait_for_timeout(1100)

        page.locator("#speak-english").click()
        expect(page.locator("#speak-english")).to_be_enabled()
        page.wait_for_timeout(900)
        page.locator("#speak-target").click()
        expect(page.locator("#speak-target")).to_be_enabled()
        page.wait_for_timeout(900)

        page.locator("#audio-consent").check()
        page.locator("#record-answer").click()
        expect(page.locator("#record-status")).to_contain_text("Recording locally")
        page.wait_for_timeout(1400)
        page.locator("#stop-recording").click()
        expect(page.locator("#record-status")).to_contain_text("Ready to preview locally")
        page.locator("#audio-preview").evaluate("audio => audio.play()")
        page.wait_for_timeout(900)
        page.locator("#send-answer").click()
        expect(page.locator("#answer-result")).to_contain_text("That matches")
        page.locator("#answer-result").scroll_into_view_if_needed()
        page.wait_for_timeout(2000)

        page.locator("#image-detail").fill("A red apple, soft watercolor")
        page.locator("#generate-image").click()
        expect(page.locator("#memory-figure")).to_be_visible()
        page.locator("#memory-figure").scroll_into_view_if_needed()
        page.wait_for_timeout(1800)
        page.screenshot(path=str(directory / "walkthrough-poster.png"))
        save_webp(directory / "walkthrough-poster.png", directory / "walkthrough-poster.webp")
        (directory / "walkthrough-poster.png").unlink()

        page.locator(".extension summary").click()
        page.locator("#generate-mnemonic").click()
        expect(page.locator("#mnemonic-result")).to_have_text(RECORDED_MNEMONIC)
        page.locator(".extension").scroll_into_view_if_needed()
        checkpoint(page, "06-mnemonic", ".extension")
        build_map(page, "06-build-map", ".extension", [["#generate-mnemonic"], ["#mnemonic-result"]])
        page.wait_for_timeout(1800)
    finally:
        context.close()
        state.pop("demo", None)
    raw_video = Path(video.path())
    ffmpeg(
        "-i", raw_video,
        "-filter_complex",
        "fps=5,scale=880:-2:flags=lanczos,split[a][b];"
        "[a]palettegen=max_colors=96:stats_mode=diff[p];"
        "[b][p]paletteuse=dither=bayer:bayer_scale=3",
        "-loop", "-1", directory / "app-walkthrough.gif",
    )
    raw_video.unlink()
    (directory / "recording").rmdir()
    animation = directory / "app-walkthrough.gif"
    set_walkthrough_playback(animation)
    if animation.stat().st_size > 3 * 1024 * 1024:
        raise RuntimeError("The walkthrough exceeds its 3 MiB download budget.")
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,nb_read_frames,duration",
        "-of", "json", str(animation),
    ], text=True))["streams"][0]
    (directory / "README.txt").write_text(
        "Capture command (from repository root; FFmpeg and cwebp required):\n"
        "WORKSHOP_MEDIA_DIR=test-results/workshop-media python -m pytest -q tests/test_lessons.py\n\n"
        "Screenshots show the actual app produced by the published lesson edits.\n"
        "The silent GIF records that completed learner app, including optional mnemonics.\n"
        "Playback loops and runs at two-thirds speed, without re-encoding its image frames.\n"
        "Model responses and microphone input are offline fixtures, not live model calls.\n"
        "The transcript (Pomme.) and the mnemonic are recorded live responses, replayed offline.\n"
        "Build maps (NN-build-map.webp) add numbered blue outlines around what each lesson\n"
        "creates; the overlay exists only in the capture, not in the app.\n"
        "The image fixture is an apple crop (320:320:30:220) of the existing MAI-generated\n"
        "docs/assets/images/vocabulary-journey.webp. No endpoint or key is captured.\n",
        encoding="utf-8",
    )
    (directory / "manifest.json").write_text(json.dumps({
        "capture": "Chromium browser of the exact sequential lesson app",
        "model_responses": "offline examples",
        "microphone": "synthetic browser device",
        "viewport": {"width": 1120, "height": 820},
        "image_source": "../images/vocabulary-journey.webp",
        "image_crop": {"width": 320, "height": 320, "x": 30, "y": 220},
        "screenshots": [
            "01-word-list.webp",
            "02-bilingual-speech.webp", "03-transcription.webp",
            "04-answer-match.webp", "05-memory-image.webp", "06-mnemonic.webp",
        ],
        "build_maps": BUILD_MAPS,
        "build_map_color": BUILD_MAP_COLOR,
        "animation": "app-walkthrough.gif",
        "animation_details": {
            "width": probe["width"], "height": probe["height"],
            "frames": int(probe["nb_read_frames"]),
            "duration_seconds": float(probe["duration"]),
            "bytes": animation.stat().st_size, "repeat": True,
            "playback_rate": 2 / 3,
        },
        "reduced_motion": "walkthrough-poster.webp",
    }, indent=2) + "\n", encoding="utf-8")
