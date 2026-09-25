"""Replay the published lesson edits onto a copy of starter/.

The lesson pages are the single source of truth for how the app changes.
Each lesson's replayable code blocks (titled exactly ``starter/<file>``) are
applied, in page order, by the edits listed in LESSONS below. Blocks titled
``Your turn: starter/<file>`` are skeletons for participants and are not replayed.

    python tests/lesson_replay.py           # regenerate checkpoints/ and solution/
    python tests/lesson_replay.py --check   # fail if either is out of date
"""

import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EDITED = ("app.py", "templates/index.html", "static/app.js")
IGNORED = {"__pycache__", ".DS_Store"}
FENCE = re.compile(
    r"^(?P<indent>[ ]*)```(?P<lang>[\w-]+)(?P<attrs>[^\n]*)\n(?P<body>.*?)\n(?P=indent)```[ ]*$",
    re.M | re.S,
)
TITLE = re.compile(r'title="([^"]*)"')
# A comment line such as `# ❶` or `<!-- ❷ -->` labels the line below it with the matching
# numbered outline in the lesson's build map. It is for reading; replay drops the line.
BUILD_MARKS = "❶❷❸❹❺❻❼❽❾"
BUILD_MARK = re.compile(rf"^[ \t]*(?:<!--|#|//)(?:[ \t]*[{BUILD_MARKS}])+[ \t]*(?:-->)?[ \t]*\n", re.M)


def strip_build_marks(code):
    return BUILD_MARK.sub("", code)


@dataclass(frozen=True)
class Edit:
    file: str
    kind: str  # "file", "marker", or "region"
    anchor: str = ""
    end: str = ""


LESSONS = {
    "01-word-list": ("lessons/01-word-list.md", [
        Edit("app.py", "file"),
        Edit("templates/index.html", "file"),
        Edit("static/app.js", "file"),
    ]),
    "02-speech": ("lessons/02-bilingual-speech.md", [
        Edit("templates/index.html", "marker", "<!-- Lesson 2: add speech controls here. -->"),
        Edit("app.py", "marker", "# Lesson 2: add the /speak route here."),
        Edit("static/app.js", "marker", "// Lesson 2: add speech here."),
    ]),
    "03-transcription": ("lessons/03-record-and-transcribe.md", [
        Edit("templates/index.html", "marker", "<!-- Lesson 3: add answer controls here. -->"),
        Edit("app.py", "marker", "# Lesson 3: add the /transcribe route here."),
        Edit("static/app.js", "marker", "// Lesson 3: add recording here."),
    ]),
    "04-matching": ("lessons/04-check-your-answer.md", [
        Edit("static/app.js", "region", "// Lesson 4: replace from this line", "// Lesson 4: replace to this line."),
    ]),
    "05-images": ("lessons/05-memory-images.md", [
        Edit("templates/index.html", "marker", "<!-- Lesson 5: add memory controls here. -->"),
        Edit("app.py", "marker", "# Lesson 5: add the /image route here."),
        Edit("static/app.js", "marker", "// Lesson 5: add memory images here."),
    ]),
    "06-mnemonics": ("extensions/mnemonics.md", [
        Edit("templates/index.html", "marker", "<!-- Extension: add mnemonic controls here. -->"),
        Edit("app.py", "marker", "# Extension: add the /mnemonic route here."),
        Edit("static/app.js", "marker", "// Extension: add mnemonics here."),
    ]),
}
CHECKPOINTS = ("01-word-list", "02-speech", "03-transcription", "04-matching", "05-images")
SOLUTION_DELTA = (
    ("templates/index.html", '<span class="eyebrow">YOUR APP</span>', '<span class="eyebrow">FINISHED SOLUTION</span>'),
)


def fenced_blocks(page):
    """Yield (language, title, code) for every fenced block, dedented from admonitions."""
    text = (DOCS / page).read_text(encoding="utf-8")
    for match in FENCE.finditer(text):
        indent = match.group("indent")
        lines = match.group("body").split("\n")
        code = "\n".join(line[len(indent):] if line.startswith(indent) else line.lstrip(" ") for line in lines)
        title = TITLE.search(match.group("attrs"))
        yield match.group("lang"), title.group(1) if title else "", code + "\n"


def replayable_blocks(page):
    """Return [(file, code)] for blocks titled exactly starter/<file>, in page order."""
    return [
        (title.removeprefix("starter/"), strip_build_marks(code))
        for _, title, code in fenced_blocks(page)
        if re.fullmatch(r"starter/[\w./-]+", title)
    ]


def skeleton_blocks(page):
    """Return [(file, code)] for participant skeletons titled 'Your turn: starter/<file>'."""
    return [
        (title.removeprefix("Your turn: starter/"), code)
        for _, title, code in fenced_blocks(page)
        if title.startswith("Your turn: starter/")
    ]


def _line_bounds(text, anchor, path):
    count = text.count(anchor)
    if count != 1:
        raise ValueError(f"{path}: expected one {anchor!r}, found {count}")
    position = text.index(anchor)
    start = text.rfind("\n", 0, position) + 1
    end = text.find("\n", position)
    end = len(text) if end == -1 else end + 1
    return start, end, text[start:position]


def _indent(code, indent):
    if not indent:
        return code
    return "".join(indent + line if line.strip() else line for line in code.splitlines(keepends=True))


def apply_edit(app_dir, edit, code):
    path = Path(app_dir) / edit.file
    if edit.kind == "file":
        path.write_text(code, encoding="utf-8")
        return
    text = path.read_text(encoding="utf-8")
    start, end, indent = _line_bounds(text, edit.anchor, path)
    if edit.kind == "region":
        _, end, _ = _line_bounds(text, edit.end, path)
    if text[start:start + len(indent)].strip():
        raise ValueError(f"{path}: {edit.anchor!r} must start its line")
    path.write_text(text[:start] + _indent(code, indent) + text[end:], encoding="utf-8")


def apply_lesson(app_dir, key):
    """Apply one lesson's replayable blocks to app_dir (a copy of starter/)."""
    page, edits = LESSONS[key]
    blocks = replayable_blocks(page)
    if [file for file, _ in blocks] != [edit.file for edit in edits]:
        raise ValueError(
            f"{page}: replayable blocks {[file for file, _ in blocks]} "
            f"do not match the recipe {[edit.file for edit in edits]}"
        )
    for edit, (_, code) in zip(edits, blocks):
        apply_edit(app_dir, edit, code)


def _files(root):
    root = Path(root)
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not IGNORED & set(path.relative_to(root).parts)
    }


def expected_outputs():
    """Return {repository path: bytes} for every generated checkpoint and solution file."""
    outputs = {}
    with tempfile.TemporaryDirectory() as temporary:
        app_dir = Path(temporary) / "app"
        shutil.copytree(ROOT / "starter", app_dir, ignore=shutil.ignore_patterns(*IGNORED))
        for key in LESSONS:
            apply_lesson(app_dir, key)
            if key in CHECKPOINTS:
                for file in EDITED:
                    outputs[f"checkpoints/{key}/{file}"] = (app_dir / file).read_bytes()
        for file, old, new in SOLUTION_DELTA:
            path = app_dir / file
            text = path.read_text(encoding="utf-8")
            if text.count(old) != 1:
                raise ValueError(f"Solution delta anchor {old!r} must occur once in {file}")
            path.write_text(text.replace(old, new), encoding="utf-8")
        for file, data in _files(app_dir).items():
            outputs[f"solution/{file}"] = data
    return outputs


def generated_files_on_disk():
    found = {f"solution/{file}": data for file, data in _files(ROOT / "solution").items()}
    for key in CHECKPOINTS:
        folder = ROOT / "checkpoints" / key
        found.update({f"checkpoints/{key}/{file}": data for file, data in _files(folder).items()})
    return found


def differences():
    """Describe how the committed checkpoints/solution differ from a fresh replay."""
    expected = expected_outputs()
    actual = generated_files_on_disk()
    problems = [f"missing {path}" for path in sorted(expected.keys() - actual.keys())]
    problems += [f"unexpected {path}" for path in sorted(actual.keys() - expected.keys())]
    problems += [f"outdated {path}" for path in sorted(expected.keys() & actual.keys())
                 if expected[path] != actual[path]]
    return problems


def write():
    expected = expected_outputs()
    shutil.rmtree(ROOT / "solution", ignore_errors=True)
    checkpoints = ROOT / "checkpoints"
    for folder in checkpoints.glob("[0-9][0-9]-*"):
        if folder.is_dir():
            shutil.rmtree(folder)
    for path, data in expected.items():
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(f"Wrote {len(expected)} files to checkpoints/ and solution/.")


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        issues = differences()
        print("\n".join(issues) or "checkpoints/ and solution/ match the lessons.")
        sys.exit(1 if issues else 0)
    write()
