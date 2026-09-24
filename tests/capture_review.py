"""Capture the built guide and unconfigured reference UI; never call a model."""

import json
import os
import shutil
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

from app_loader import load_app

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "test-results/visual"


def main():
    os.environ["APIM_BASE_URL"] = ""
    os.environ["APIM_API_KEY"] = ""
    os.environ.pop("CODESPACES", None)
    module, _ = load_app(ROOT / "solution/app.py", "review_reference")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        shutil.copytree(ROOT / "site", Path(temporary) / "the-mai-workshop")
        guide = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=temporary)
        )
        app = make_server("127.0.0.1", 0, module.app, threaded=True)
        servers = [guide, app]
        threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
        for thread in threads:
            thread.start()
        evidence = []
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(args=["--mute-audio"])
                for surface, url in [
                    ("guide", f"http://127.0.0.1:{guide.server_port}/the-mai-workshop/"),
                    ("app", f"http://127.0.0.1:{app.server_port}/"),
                ]:
                    for size, width, height in [("desktop", 1440, 1000), ("mobile", 390, 844)]:
                        page = browser.new_page(
                            viewport={"width": width, "height": height}, reduced_motion="reduce"
                        )
                        page.goto(url, wait_until="load")
                        page.evaluate("document.fonts.ready")
                        if surface == "app":
                            page.locator("#target-locale").select_option("es-ES")
                            page.locator("#english-word").fill("apple")
                            page.locator("#target-word").fill("manzana")
                            page.locator("#word-form button").click()
                        page.evaluate("window.scrollTo(0, 0)")
                        name = f"{size}.png" if surface == "guide" else f"app-{size}.png"
                        page.screenshot(path=str(OUTPUT / name))
                        if surface == "guide":
                            page.goto(url + "lessons/02-bilingual-speech/", wait_until="load")
                            page.locator(".highlight").first.screenshot(
                                path=str(OUTPUT / f"guide-code-{size}.png")
                            )
                        else:
                            page.locator(".practice-panel").screenshot(
                                path=str(OUTPUT / f"app-practice-{size}.png")
                            )
                        overflow = page.evaluate("document.documentElement.scrollWidth > innerWidth")
                        if overflow:
                            raise RuntimeError(f"Horizontal overflow in {surface}/{size}")
                        evidence.append({
                            "surface": surface, "viewport": [width, height],
                            "file": name, "overflow": overflow,
                        })
                        page.close()
                browser.close()
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=5)
        (OUTPUT / "captures.json").write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    main()
