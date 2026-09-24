"""Load a workshop Flask app together with its own provided workshop.py.

Each app folder (starter/, solution/, or a temporary learner copy) has its own
workshop.py, and app.py imports it as ``workshop``. load_app imports the right
one, then restores sys.path and any previously loaded ``workshop`` module so
several apps can coexist in one test process.
"""

import sys
from pathlib import Path
from types import ModuleType


def load_app(app_file, name, monkeypatch=None):
    """Return (app_module, workshop_module) for app_file, compiled fresh from disk."""
    app_file = Path(app_file).resolve()
    saved_path = list(sys.path)
    saved_workshop = sys.modules.pop("workshop", None)
    module = ModuleType(name)
    module.__file__ = str(app_file)
    if monkeypatch is not None:
        monkeypatch.setitem(sys.modules, name, module)
    else:
        sys.modules[name] = module
    sys.path.insert(0, str(app_file.parent))
    try:
        # Compile the current file, not a same-second bytecode cache from an earlier edit.
        exec(compile(app_file.read_text(encoding="utf-8"), str(app_file), "exec"), module.__dict__)
        workshop = sys.modules["workshop"]
    finally:
        sys.path[:] = saved_path
        sys.modules.pop("workshop", None)
        if saved_workshop is not None:
            sys.modules["workshop"] = saved_workshop
    return module, workshop
