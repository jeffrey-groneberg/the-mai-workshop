import json
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_participant_docs_do_not_require_a_development_branch():
    paths = [ROOT / "README.md", ROOT / "zensical.toml", *(ROOT / "docs").rglob("*.md")]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "jeffrey-groneberg-mai-vocabulary-workshop" not in text, str(path)
        assert "currently contains only a README" not in text, str(path)
    readiness = (ROOT / "docs/getting-ready.md").read_text()
    assert "Use the default **`main`** branch." in readiness
    assert "Keep **Copy the main branch only**" in readiness


def test_guide_uses_native_zensical_styling():
    config = tomllib.loads((ROOT / "zensical.toml").read_text())
    project = config["project"]
    theme = project["theme"]
    assert "extra_css" not in project
    assert "custom_dir" not in theme
    assert "font" not in theme
    assert "palette" not in theme
    home = (ROOT / "docs/index.md").read_text()
    assert "template: home.html" not in home
    assert 'class="workshop-' not in home
    assert not (ROOT / "docs/stylesheets/workshop.css").exists()


def test_private_endpoint_hosts_are_not_in_publishable_source():
    paths = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, text=True,
    ).splitlines()
    endpoint = re.compile(
        r"https?://[a-zA-Z0-9.-]+(?:\.azure-api\.net|"
        r"\.services\.ai\.azure\.com|\.cognitiveservices\.azure\.com)"
    )
    for relative in set(paths):
        path = ROOT / relative
        if path.suffix not in {".md", ".py", ".js", ".html", ".json", ".toml", ".yml", ".yaml", ".example"}:
            continue
        if path.is_file() and endpoint.search(path.read_text(encoding="utf-8")):
            pytest.fail(f"Endpoint-shaped URL found in {relative}; remove it before publishing.", pytrace=False)


def test_example_configuration_has_no_endpoint_or_key():
    values = {}
    for line in (ROOT / ".env.example").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    for key in ("APIM_BASE_URL", "APIM_API_KEY"):
        if key not in values or values[key]:
            pytest.fail(f"{key} must be present but empty in .env.example.", pytrace=False)


def test_generated_teaching_images_have_provenance():
    folder = ROOT / "docs/assets/images"
    provenance = json.loads((folder / "provenance.json").read_text())
    assert provenance["model"] == "MAI-Image-2.6"
    assert len(provenance["images"]) == 3
    for image in provenance["images"]:
        data = (folder / image["file"]).read_bytes()
        assert data[:4] == b"RIFF" and data[8:12] == b"WEBP"
        assert image["prompt"]
        assert len(image["original_png_sha256"]) == 64
