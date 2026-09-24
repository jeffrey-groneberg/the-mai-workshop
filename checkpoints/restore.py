"""Copy a lesson checkpoint over your starter files, or undo the last copy.

    python checkpoints/restore.py 03     # catch up to the end of lesson 3
    python checkpoints/restore.py undo   # bring back the files it replaced

Checkpoints hold the three files you edit (app.py, templates/index.html, and
static/app.js) as they are after each lesson. Your current versions are first
copied to .checkpoint-backups/<time>/, so nothing is lost. Copied files get a
fresh modification time, so a running `flask run --reload` picks them up.
"""

import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUPS = ROOT / ".checkpoint-backups"
FILES = ("app.py", "templates/index.html", "static/app.js")


def copy_into_starter(source):
    for file in FILES:
        if (source / file).exists():
            target = ROOT / "starter" / file
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / file, target)


def main(arguments):
    if arguments == ["undo"]:
        backups = sorted(BACKUPS.iterdir()) if BACKUPS.is_dir() else []
        if not backups:
            print("Nothing to undo: no backups in .checkpoint-backups/ yet.")
            return 2
        copy_into_starter(backups[-1])
        print(f"starter/ has your files from {backups[-1].name} again. Flask reloads; reload the browser.")
        return 0
    names = sorted(path.name for path in (ROOT / "checkpoints").iterdir() if path.is_dir())
    matches = [name for name in names if arguments and name.startswith(arguments[0])]
    if len(arguments) != 1 or len(matches) != 1:
        print("Usage: python checkpoints/restore.py <checkpoint> | undo")
        print("Checkpoints: " + ", ".join(names))
        return 2
    backup = BACKUPS / time.strftime("%Y%m%d-%H%M%S")
    for file in FILES:
        current = ROOT / "starter" / file
        if current.exists():
            (backup / file).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(current, backup / file)
    copy_into_starter(ROOT / "checkpoints" / matches[0])
    print(f"starter/ now matches checkpoint {matches[0]}. Flask reloads; reload the browser.")
    print(f"Your previous files are in {backup.relative_to(ROOT)}/; `python checkpoints/restore.py undo` brings them back.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
