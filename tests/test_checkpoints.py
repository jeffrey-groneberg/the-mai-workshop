"""Keep lessons, checkpoints, and the generated solution consistent."""

import io
import os
import re
import shutil
import subprocess
import sys
import wave

import httpx
import pytest

import lesson_replay
from app_loader import load_app
from lesson_replay import CHECKPOINTS, LESSONS, ROOT, apply_lesson, replayable_blocks, skeleton_blocks

MARKER = re.compile(r"(?:#|//|<!--) (?:Lesson \d|Extension): [^\n]*?(?: -->)?$", re.M)


def test_checkpoints_and_solution_match_a_fresh_replay():
    problems = lesson_replay.differences()
    assert not problems, "Run `python tests/lesson_replay.py`:\n" + "\n".join(problems)


def test_every_lesson_one_marker_is_consumed_once_and_named_in_its_lesson():
    lesson_one = "".join(code for _, code in replayable_blocks(LESSONS["01-word-list"][0]))
    markers = MARKER.findall(lesson_one)
    anchors = [edit.anchor for _, edits in LESSONS.values() for edit in edits if edit.kind == "marker"]
    assert sorted(markers) == sorted(anchors)
    for page, edits in LESSONS.values():
        text = (ROOT / "docs" / page).read_text(encoding="utf-8")
        for edit in edits:
            for anchor in filter(None, (edit.anchor, edit.end)):
                assert f"`{anchor}" in text, f"{page} must name the marker {anchor!r}"


def test_replayed_code_never_contains_build_marks():
    for page, _ in LESSONS.values():
        for file, code in replayable_blocks(page):
            assert not re.search(f"[{lesson_replay.BUILD_MARKS}]", code), f"{page}: {file} kept a build mark"


def test_lessons_avoid_partial_line_edits():
    for page, _ in LESSONS.values():
        text = (ROOT / "docs" / page).read_text(encoding="utf-8").lower()
        for phrase in ("replace only", "immediately after", "immediately before", "add `import"):
            assert phrase not in text, f"{page} asks for a partial edit: {phrase!r}"


def test_skeletons_are_valid_code():
    node = shutil.which("node")
    for key, (page, _) in LESSONS.items():
        for file, code in skeleton_blocks(page):
            if file.endswith(".py"):
                compile(code, f"{page}:{file}", "exec")
            elif node:
                subprocess.run([node, "--check", "-"], input=code, text=True, check=True)


@pytest.mark.parametrize("key,path,body", [
    ("02-speech", "/speak", {"json": {"text": "pomme", "locale": "fr-FR"}}),
    ("03-transcription", "/transcribe", {"data": "wav"}),
    ("05-images", "/image", {"json": {"word": "apple", "detail": ""}}),
    ("06-mnemonics", "/mnemonic", {"json": {"word": "apple", "target": "pomme", "locale": "fr-FR"}}),
])
def test_pasted_skeleton_runs_and_asks_to_be_finished(tmp_path, monkeypatch, key, path, body):
    monkeypatch.setenv("APIM_BASE_URL", "https://gateway.example.test")
    monkeypatch.setenv("APIM_API_KEY", "fixture-only-not-a-real-key")

    def blocked(*args, **kwargs):
        raise AssertionError("A skeleton must not call the gateway.")
    monkeypatch.setattr(httpx, "post", blocked)
    app_dir = tmp_path / "starter"
    shutil.copytree(ROOT / "starter", app_dir)
    for earlier in LESSONS:
        if earlier == key:
            break
        apply_lesson(app_dir, earlier)
    page, edits = LESSONS[key]
    python_edit = next(edit for edit in edits if edit.file == "app.py")
    ((_, skeleton),) = [block for block in skeleton_blocks(page) if block[0] == "app.py"]
    lesson_replay.apply_edit(app_dir, python_edit, skeleton)
    module, _ = load_app(app_dir / "app.py", f"skeleton_{key.replace('-', '_')}", monkeypatch)
    client = module.app.test_client()
    if body.get("data") == "wav":
        audio = io.BytesIO()
        with wave.open(audio, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\0\0" * 1600)
        kwargs = {"data": {"locale": "fr-FR", "audio": (io.BytesIO(audio.getvalue()), "answer.wav")}}
    else:
        kwargs = body
    response = client.post(path, headers={"Origin": "http://localhost"}, **kwargs)
    assert response.status_code == 501
    assert "finish the" in response.json["error"]


def test_restore_copies_a_checkpoint_and_backs_up_the_learner_files(tmp_path):
    shutil.copytree(ROOT / "starter", tmp_path / "starter")
    shutil.copytree(ROOT / "checkpoints", tmp_path / "checkpoints")
    (tmp_path / "starter/app.py").write_text("# my own work\n", encoding="utf-8")
    learner_mtime = (tmp_path / "starter/app.py").stat().st_mtime_ns
    old = learner_mtime - 3_600_000_000_000
    for file in (tmp_path / "checkpoints/03-transcription").rglob("*"):
        if file.is_file():
            os.utime(file, ns=(old, old))  # A git checkout often leaves checkpoints older than your edits.
    result = subprocess.run(
        [sys.executable, str(tmp_path / "checkpoints/restore.py"), "03"],
        capture_output=True, text=True, check=True,
    )
    assert "03-transcription" in result.stdout
    for file in ("app.py", "templates/index.html", "static/app.js"):
        assert (tmp_path / "starter" / file).read_bytes() == (
            tmp_path / "checkpoints/03-transcription" / file
        ).read_bytes()
    # Werkzeug's stat reloader restarts only when a watched file's mtime increases.
    assert (tmp_path / "starter/app.py").stat().st_mtime_ns > learner_mtime
    (backup,) = (tmp_path / ".checkpoint-backups").iterdir()
    assert (backup / "app.py").read_text(encoding="utf-8") == "# my own work\n"
    (tmp_path / "starter/app.py").write_text("# checkpoint edited\n", encoding="utf-8")
    before_undo = (tmp_path / "starter/app.py").stat().st_mtime_ns
    undo = subprocess.run(
        [sys.executable, str(tmp_path / "checkpoints/restore.py"), "undo"], capture_output=True, text=True, check=True,
    )
    assert "your files" in undo.stdout
    assert (tmp_path / "starter/app.py").read_text(encoding="utf-8") == "# my own work\n"
    assert (tmp_path / "starter/app.py").stat().st_mtime_ns > before_undo
    ambiguous = subprocess.run(
        [sys.executable, str(tmp_path / "checkpoints/restore.py"), "0"], capture_output=True, text=True,
    )
    assert ambiguous.returncode == 2 and "Checkpoints:" in ambiguous.stdout


def test_checkpoint_folders_hold_only_the_learner_files():
    folders = sorted(path.name for path in (ROOT / "checkpoints").iterdir() if path.is_dir())
    assert folders == list(CHECKPOINTS)
    for folder in folders:
        files = sorted(
            path.relative_to(ROOT / "checkpoints" / folder).as_posix()
            for path in (ROOT / "checkpoints" / folder).rglob("*") if path.is_file()
        )
        assert files == ["app.py", "static/app.js", "templates/index.html"]
