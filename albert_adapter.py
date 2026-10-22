"""Accès serveur à Albert ; aucune clé dans les résultats ou les erreurs."""
import re
from types import SimpleNamespace
import json
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

BASE_URL = 'https://albert.api.etalab.gouv.fr/v1'


class AlbertError(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _http_error(status):
    notices = {401: 'Clé Albert refusée ou expirée.', 403: 'Accès Albert non autorisé pour ce compte ou ce modèle.',
               404: 'Modèle ou service Albert introuvable.', 429: 'Quota Albert atteint ; réessayez plus tard.'}
    return AlbertError(notices.get(status, 'Service Albert indisponible (HTTP ' + str(status) + ').'))


def _request(api_key, method, route, payload=None):
    if not isinstance(api_key, str) or not api_key.strip() or any(c in api_key for c in '\r\n'):
        raise AlbertError('Clé Albert absente ou non conforme dans les secrets Streamlit.')
    request = Request(BASE_URL + route, method=method,
                      headers={'Authorization': 'Bearer ' + api_key.strip(), 'Content-Type': 'application/json'},
                      data=json.dumps(payload).encode() if payload is not None else None)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=90) as response:
            if response.status != 200:
                raise _http_error(response.status)
            data = response.read()
    except HTTPError as exc:
        status = exc.code
        exc.close()
        raise _http_error(status) from None
    except (URLError, TimeoutError, OSError):
        raise AlbertError('Connexion Albert indisponible ou délai dépassé. Aucun nouvel essai automatique.') from None
    try:
        return json.loads(data)
    except (ValueError, UnicodeError):
        raise AlbertError('Réponse Albert illisible.') from None


def available_models(api_key):
    data = _request(api_key, 'GET', '/models')
    entries = data.get('data') if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise AlbertError('Liste des modèles Albert non conforme.')
    ids = sorted({entry['id'] for entry in entries if isinstance(entry, dict)
                  and isinstance(entry.get('id'), str) and entry['id'].strip()
                  and entry.get('type') in (None, 'text-generation')})
    if not ids:
        raise AlbertError('Aucun modèle de génération de texte accessible dans la liste retournée.')
    return ids


class AlbertLLM:
    def __init__(self, api_key, model, temperature=0.0):
        if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9_./:-]{1,200}', model):
            raise AlbertError('Indiquez un identifiant exact de modèle Albert.')
        self._api_key = api_key
        self.model = model
        self.temperature = temperature
        self.resolved_model = None

    def complete(self, prompt, **kwargs):
        if kwargs:
            raise AlbertError('Paramètres supplémentaires non pris en charge par ce comparateur.')
        data = _request(self._api_key, 'POST', '/chat/completions',
                        {'model': self.model, 'messages': [{'role': 'user', 'content': str(prompt)}],
                         'temperature': self.temperature, 'stream': False, 'max_tokens': 4096})
        try:
            choice = data['choices'][0]
            content = choice['message']['content']
            if choice.get('finish_reason') == 'length':
                raise AlbertError('Réponse Albert tronquée par la limite de sortie ; résultat non validé.')
            if not isinstance(content, str) or not content.strip():
                raise AlbertError('Albert ne fournit pas de réponse textuelle exploitable.')
        except (KeyError, IndexError, TypeError):
            raise AlbertError('Réponse Albert non conforme au format de génération attendu.') from None
        self.resolved_model = data.get('model') if isinstance(data.get('model'), str) else None
        # Seuls le texte de réponse et les compteurs sont transmis aux contrôles existants.
        return SimpleNamespace(text=content, raw={'usage': data.get('usage')})
