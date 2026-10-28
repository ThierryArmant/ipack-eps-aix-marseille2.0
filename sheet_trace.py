"""Export du diagnostic existant, sans appel IA ni données de connexion."""
import hashlib
import json
import math
import uuid
from datetime import datetime, timezone

_SECRET_KEYS = {'api_key', 'apikey', 'authorization', 'password', 'mot_de_passe',
                'access_token', 'refresh_token', 'client_secret'}


def _json_value(value):
    if isinstance(value, dict):
        return {str(k): ('[retiré]' if str(k).lower() in _SECRET_KEYS else _json_value(v))
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def make_trace_payload(*, question, answer, mode, public, academy, version,
                       origin, diagnostic=None, usage=None):
    trial_id = str(uuid.uuid4())
    trace = _json_value({
        'schema_version': 1, 'id_essai': trial_id,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'question': question, 'mode': mode, 'public': public, 'academie': academy,
        'version': version, 'origine_reponse': origin,
        'diagnostic_disponible': diagnostic is not None,
        'diagnostic': diagnostic, 'usage': usage or {},
        'reponse_finale': answer,
    })
    raw = json.dumps(trace, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return {'id_essai': trial_id, 'trace_schema': 1, 'trace_json': raw,
            'trace_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest()}
