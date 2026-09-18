import hashlib
import json
import re
import subprocess
import tomllib
from decimal import Decimal, ROUND_HALF_UP
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


def test_checkpoint_screenshots_match_the_workshop_steps():
    directory = ROOT / "docs/assets/workshop"
    pages = {
        "lessons/00-open-your-app.md": ["00-open-app.webp"],
        "lessons/01-word-list.md": ["01-word-list.webp"],
        "lessons/02-bilingual-speech.md": ["02-english-speech.webp", "02-bilingual-speech.webp"],
        "lessons/03-record-and-transcribe.md": ["03-transcription.webp"],
        "lessons/04-check-your-answer.md": ["04-answer-match.webp"],
        "lessons/05-memory-images.md": ["05-memory-image.webp"],
        "extensions/mnemonics.md": ["06-mnemonic.webp"],
    }
    manifest = json.loads((directory / "manifest.json").read_text())
    expected = [name for names in pages.values() for name in names]
    assert manifest["screenshots"] == expected
    assert manifest["model_responses"] == "offline examples"
    for page, images in pages.items():
        text = (ROOT / "docs" / page).read_text()
        for name in images:
            assert f"../assets/workshop/{name}" in text
            data = (directory / name).read_bytes()
            assert data[:4] == b"RIFF" and data[8:12] == b"WEBP"
            assert 1024 < len(data) < 512 * 1024


def test_walkthrough_is_small_finite_and_has_a_reduced_motion_alternative():
    directory = ROOT / "docs/assets/workshop"
    data = (directory / "app-walkthrough.gif").read_bytes()
    manifest = json.loads((directory / "manifest.json").read_text())
    details = manifest["animation_details"]
    assert data[:6] == b"GIF89a"
    assert len(data) == details["bytes"] < 3 * 1024 * 1024
    assert int.from_bytes(data[6:8], "little") == details["width"] == 880
    assert int.from_bytes(data[8:10], "little") == details["height"] == 644
    assert b"NETSCAPE2.0" not in data  # No animation loop extension: play once.

    cursor = 13 + (3 * (2 ** ((data[10] & 7) + 1)) if data[10] & 128 else 0)
    frames = hundredths = 0
    while data[cursor] != 0x3B:
        marker = data[cursor]
        cursor += 1
        if marker == 0x21:
            label = data[cursor]
            cursor += 1
            if label == 0xF9:
                hundredths += int.from_bytes(data[cursor + 2:cursor + 4], "little")
        elif marker == 0x2C:
            flags = data[cursor + 8]
            cursor += 9 + (3 * (2 ** ((flags & 7) + 1)) if flags & 128 else 0)
            cursor += 1  # LZW minimum code size.
            frames += 1
        else:
            pytest.fail(f"Unexpected GIF block marker: {marker}")
        while data[cursor]:
            cursor += 1 + data[cursor]
        cursor += 1
    assert frames == details["frames"] > 20
    assert hundredths / 100 == pytest.approx(details["duration_seconds"])
    assert 10 <= hundredths / 100 <= 30
    assert (directory / "walkthrough-poster.webp").is_file()
    home = (ROOT / "docs/index.md").read_text()
    assert 'media="(prefers-reduced-motion: reduce)"' in home
    assert 'srcset="assets/workshop/walkthrough-poster.webp"' in home
    assert "<details open>" in home and "<summary>See the app in action</summary>" in home
    assert "example model responses" in home


def test_explanatory_diagrams_have_reviewed_revision_provenance():
    directory = ROOT / "docs/assets/diagrams"
    provenance = json.loads((directory / "provenance.json").read_text())
    assert provenance["model"] == "MAI-Image-2.6"
    assert len(provenance["images"]) == 6
    for image in provenance["images"]:
        data = (directory / image["file"]).read_bytes()
        assert data[:4] == b"RIFF" and data[8:12] == b"WEBP"
        assert hashlib.sha256(data).hexdigest() == image["sha256"]
        assert 1024 < len(data) < 300 * 1024
        assert image["width"] * image["height"] <= 1_048_576
        assert image["revisions"][-1]["verdict"].startswith("Accepted:")
        for index, revision in enumerate(image["revisions"]):
            assert (directory / revision["prompt"]).is_file()
            assert len(revision["png_sha256"]) == 64
            if revision["operation"] == "edit":
                assert index > 0
                assert revision["input_sha256"] == image["revisions"][index - 1]["png_sha256"]
    mapping = next(image for image in provenance["images"] if image["file"] == "feature-model-map.webp")
    assert mapping["models"] == [
        "MAI-Voice-2-Flash", "MAI-Transcribe-2", "MAI-Image-2.6-Flash", "MAI-Thinking-1",
    ]
    assert mapping["no_model"] == ["Save words", "Match answers"]
    family = next(image for image in provenance["images"] if image["file"] == "mai-family.webp")
    assert len(family["families"]) == 6
    assert family["not_a_separate_model"] == "Microsoft Frontier Tuning"
    by_name = {item["name"]: item for item in family["families"]}
    assert by_name["MAI-Code-1.1-Flash"]["access"] == "GitHub Copilot"
    assert by_name["MAI-Cyber-1-Flash"]["access"] == "Restricted MDASH"
    embeddings = {
        "index.md": "feature-model-map.webp",
        "lessons/02-bilingual-speech.md": "request-loop.webp",
        "lessons/03-record-and-transcribe.md": "audio-path.webp",
        "lessons/04-check-your-answer.md": "answer-matching.webp",
        "lessons/05-memory-images.md": "image-flow.webp",
        "compare-models.md": "mai-family.webp",
    }
    for page, image in embeddings.items():
        text = (ROOT / "docs" / page).read_text()
        assert f"assets/diagrams/{image}" in text
        assert "MAI-generated diagram" in text
        assert "Full size" in text


def test_comparison_price_math_and_unverified_totals():
    text = (ROOT / "docs/compare-models.md").read_text()
    money = lambda value: value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    mai_transcribe = Decimal(1000) / 60 * Decimal("0.10")
    whisper = Decimal(1000) / 60 * Decimal("0.396")
    savings = ((whisper - mai_transcribe) / whisper * 100).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    assert f"**${money(mai_transcribe)}**" in text
    assert f"**${money(whisper)}**" in text
    assert f"**{savings}% lower if the MAI promotion applies.**" in text
    assert "31 December 2026" in text
    assert "18 September 2026" in text
    gpt_image = Decimal(100) * (100 * 5 + 1056 * 40) / 1_000_000
    assert f"**${gpt_image}**" in text
    mai_prompt_cost = Decimal(10_000) * Decimal("1.75") / 1_000_000
    assert f"costing ${mai_prompt_cost}" in text
    assert "**10,000 text-input tokens (100 per image)**" in text
    assert "Identical prompts need not tokenize identically" in text
    assert "**Q is its actual total image-output\ntokens**" in text
    assert "tokens**. No verified MAI pixel-to-token formula" in text
    for value in (Decimal(2) + Decimal("0.1") * 8, Decimal("0.25") + Decimal("0.1") * 2):
        assert f"**${money(value)}**" in text
    assert "model-specific tariff not verified" in text
    assert "record cost as **unverified** rather than ranking it." in text
    assert "not measured app runs" in text


def test_observed_diagram_text_is_bound_to_final_image_bytes():
    root = ROOT / "docs/assets/diagrams"
    provenance = json.loads((root / "provenance.json").read_text())
    audit = json.loads((root / provenance["text_audit"]).read_text())
    assert audit["language_correction"] is False
    records = {row["file"]: row for row in audit["images"]}
    assert set(records) == {row["file"] for row in provenance["images"]}
    for image in provenance["images"]:
        observed = records[image["file"]]
        assert observed["sha256"] == image["sha256"]
        assert observed["sha256"] == hashlib.sha256((root / image["file"]).read_bytes()).hexdigest()
        assert (observed["width"], observed["height"]) == (image["width"], image["height"])
        assert "frondier" not in " ".join(observed["observed_lines"]).lower()

    family = "\n".join(records["mai-family.webp"]["observed_lines"])
    assert "Microsoft Frontier Tuning: model customization, not a separate model." in family
    family_url = f"assets/diagrams/mai-family.webp?v={records['mai-family.webp']['sha256'][:8]}"
    assert (ROOT / "docs/compare-models.md").read_text().count(family_url) == 2
    for name in ("MAI-Voice-2", "MAI-Transcribe-2", "MAI-Image-2.6",
                 "MAI-Thinking-1", "MAI-Code-1.1-Flash", "MAI-Cyber-1-Flash"):
        assert name in family
    assert family.count("Foundry preview") == 2
    assert family.count("Speech preview") == 2
    assert "GitHub Copilot" in family and "Restricted MDASH" in family
    loop = records["request-loop.webp"]["observed_lines"]
    assert loop.count("Request") == loop.count("Response") == 3
    audio = records["audio-path.webp"]["observed_lines"]
    assert all(text in audio for text in ("MediaRecorder", "16 kHz / mono", "16-bit PCM", "MAI-Transcribe-2"))
    matching = records["answer-matching.webp"]["observed_lines"]
    assert matching.count("Normalize") == 2
    assert "JavaScript in the browser / no model call" in matching
    image_flow = records["image-flow.webp"]["observed_lines"]
    assert all(text in image_flow for text in ("base64 PNG", "Decode in Flask", "1024 x 1024 source"))
    mapping = "\n".join(records["feature-model-map.webp"]["observed_lines"])
    for name in ("MAI-Voice-2-Flash", "MAI-Transcribe-2", "MAI-Image-2.6-Flash", "MAI-Thinking-1"):
        assert name in mapping
    assert "JavaScript / no model" in mapping
