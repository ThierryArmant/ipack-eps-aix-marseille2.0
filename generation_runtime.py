"""Charge les appels fournisseur et leurs contrôles comme un ensemble immuable.

L'empreinte des sources évite une ancienne classe de trace retenue par Streamlit,
sans recharger un module partagé pendant la réponse d'une autre session.
"""
import hashlib
import importlib.util
from pathlib import Path
import sys
import threading
import types

_LOCK = threading.RLock()
_FILES = ('question_normalization', 'source_scope', 'evidence_logic', 'single_document_test', 'navigation_restore', 'albert_adapter', 'document_selector', 'claim_guards', 'exact_source_answer', 'documentary_review')


def load_runtime(base_dir=None):
    root = Path(base_dir) if base_dir is not None else Path(__file__).parent
    sources = [(name, root / (name + '.py'), (root / (name + '.py')).read_bytes()) for name in _FILES]
    fingerprint = hashlib.sha256(b'\0'.join(name.encode() + b'\0' + data for name, _, data in sources)).hexdigest()
    package_name = '_eps_generation_' + fingerprint
    with _LOCK:
        if package_name in sys.modules:
            return sys.modules[package_name]
        package = types.ModuleType(package_name)
        package.__path__ = [str(root)]
        package.__package__ = package_name
        try:
            sys.modules[package_name] = package
            for name, path, data in sources:
                full_name = package_name + '.' + name
                module = importlib.util.module_from_spec(importlib.util.spec_from_file_location(full_name, path))
                sys.modules[full_name] = module
                exec(compile(data, str(path), 'exec'), module.__dict__)
                setattr(package, name, module)
            # La fonction ne retourne le paquet qu’après compilation de tous les modules.
            package.generation_llm = package.albert_adapter.generation_llm
            for name in ('TracedLLM', 'usage_summary', 'review_exam_answer'):
                setattr(package, name, getattr(package.documentary_review, name))
            sys.modules[package_name] = package
            return package
        except BaseException:
            sys.modules.pop(package_name, None)
            for name, _, _ in sources:
                sys.modules.pop(package_name + '.' + name, None)
            raise
