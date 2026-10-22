"""Charge un ensemble cohérent du prototype admin, sans recharger les modules publics."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import threading
import types

_LOCK = threading.RLock()
_FILES = ('albert_adapter', 'confirmed_scope', 'clarification_pilot', 'architecture_comparison')


def load_comparison(base_dir=None):
    root = Path(base_dir) if base_dir is not None else Path(__file__).parent
    sources = [(name, root / (name + '.py'), (root / (name + '.py')).read_bytes()) for name in _FILES]
    fingerprint = hashlib.sha256(b'\0'.join(name.encode() + b'\0' + data for name, _, data in sources)).hexdigest()
    package_name = '_eps_admin_comparison_' + fingerprint
    target = package_name + '.architecture_comparison'
    with _LOCK:
        if target in sys.modules:
            return sys.modules[target]
        package = types.ModuleType(package_name)
        package.__path__ = [str(root)]
        package.__package__ = package_name
        sys.modules[package_name] = package
        try:
            for name, path, data in sources:
                full_name = package_name + '.' + name
                module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(full_name, path))
                sys.modules[full_name] = module
                # Compiler les octets dont l'empreinte a été calculée, sans cache de bytecode périmé.
                exec(compile(data, str(path), 'exec'), module.__dict__)
            return sys.modules[target]
        except BaseException:
            for name in _FILES:
                sys.modules.pop(package_name + '.' + name, None)
            sys.modules.pop(package_name, None)
            raise
