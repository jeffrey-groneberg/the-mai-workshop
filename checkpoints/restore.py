"""Copy a lesson checkpoint over your starter files.

    python checkpoints/restore.py 03

Checkpoints hold the three files you edit (app.py, templates/index.html, and
static/app.js) as they are after each lesson. Your current versions are first
copied to .checkpoint-backups/<time>/, so nothing is lost. The restored files
get a fresh modification time, so a running `flask run --reload` picks them up.
"""

import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("app.py", "templates/index.html", "static/app.js")


def main(arguments):
    names = sorted(path.name for path in (ROOT / "checkpoints").iterdir() if path.is_dir())
    matches = [name for name in names if arguments and name.startswith(arguments[0])]
    if len(arguments) != 1 or len(matches) != 1:
        print("Usage: python checkpoints/restore.py <checkpoint>")
        print("Checkpoints: " + ", ".join(names))
        return 2
    source = ROOT / "checkpoints" / matches[0]
    backup = ROOT / ".checkpoint-backups" / time.strftime("%Y%m%d-%H%M%S")
    for file in FILES:
        current = ROOT / "starter" / file
        if current.exists():
            (backup / file).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(current, backup / file)
        current.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / file, current)
    print(f"starter/ now matches checkpoint {matches[0]}. Flask reloads; reload the browser.")
    print(f"Your previous files are in {backup.relative_to(ROOT)}/.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
