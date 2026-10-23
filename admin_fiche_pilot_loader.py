"""Charge la version immuable du panneau pilote, sans reload partagé."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import threading
_LOCK = threading.RLock()

def load_panel(root=None):
    root = Path(root) if root is not None else Path(__file__).parent
    path = root/'admin_fiche_pilot.py'
    source = path.read_bytes()
    name = '_eps_admin_fiche_' + hashlib.sha256(source).hexdigest()
    with _LOCK:
        if name not in sys.modules:
            module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, path))
            exec(compile(source, str(path), 'exec'), module.__dict__)
            sys.modules[name] = module
        return sys.modules[name]
