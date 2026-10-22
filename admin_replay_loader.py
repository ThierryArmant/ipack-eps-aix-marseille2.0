"""Actualiser le rejeu administrateur sans recharger un module en cours ailleurs."""
import hashlib
from pathlib import Path
import threading
import types

_LOCK=threading.RLock()
_MODULES={}

def load_replay(base_dir=None):
    path=(Path(base_dir) if base_dir is not None else Path(__file__).parent)/'admin_retest_113_live.py'
    source=path.read_bytes()
    key=hashlib.sha256(source).hexdigest()
    with _LOCK:
        if key not in _MODULES:
            module=types.ModuleType('_eps_replay_'+key)
            exec(compile(source,str(path),'exec'),module.__dict__)
            _MODULES[key]=module
        return _MODULES[key]
