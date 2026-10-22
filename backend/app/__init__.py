"""
Intent-Aware Deception System Backend Application Package.
"""

import sys
import types
from pathlib import Path

# Self-resolving package anchor:
# Ensures 'backend' and 'backend.app' exist in sys.modules and sys.path
# regardless of whether the execution root is the repo root, backend/, or /var/task.
_CURRENT_FILE = Path(__file__).resolve()
_APP_DIR = _CURRENT_FILE.parent
_BACKEND_DIR = _APP_DIR.parent
_ROOT_DIR = _BACKEND_DIR.parent

for _p in [str(_ROOT_DIR), str(_BACKEND_DIR), str(_APP_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

if "backend" not in sys.modules:
    _backend_pkg = types.ModuleType("backend")
    _backend_pkg.__path__ = [str(_BACKEND_DIR)]
    _backend_pkg.__file__ = str(_BACKEND_DIR / "__init__.py")
    sys.modules["backend"] = _backend_pkg

if "backend.app" not in sys.modules:
    _app_mod = sys.modules.get("app")
    if _app_mod is not None:
        sys.modules["backend.app"] = _app_mod
