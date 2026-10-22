"""Point d'entrée stable vers un chargeur immuable, sans importlib.reload."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import threading

_LOCK = threading.RLock()


def load_runtime(base_dir=None):
    root = Path(base_dir) if base_dir is not None else Path(__file__).parent
    path = root / 'generation_runtime.py'
    source = path.read_bytes()
    name = '_eps_runtime_loader_' + hashlib.sha256(source).hexdigest()
    with _LOCK:
        loader = sys.modules.get(name)
        if loader is None:
            loader = importlib.util.module_from_spec(importlib.util.spec_from_file_location(name, path))
            exec(compile(source, str(path), 'exec'), loader.__dict__)
            sys.modules[name] = loader
        return loader.load_runtime(root)
