"""Accès serveur à Albert ; aucune clé dans les résultats ou les erreurs."""
import re
from types import SimpleNamespace
import json
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

# Intégration Albert réactivée à la demande du pilote le 23 octobre 2026.
ALBERT_PAUSED = True

BASE_URL = 'https://albert.api.etalab.gouv.fr/v1'


class AlbertError(RuntimeError):
    pass


class AlbertServiceError(AlbertError):
    """Indisponibilité technique uniquement, distincte d'un contenu à vérifier."""
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _http_error(status):
    notices = {401: 'Clé Albert refusée ou expirée.', 403: 'Accès Albert non autorisé pour ce compte ou ce modèle.',
               404: 'Modèle ou service Albert introuvable.', 429: 'Quota Albert atteint ; réessayez plus tard.'}
    return AlbertServiceError(notices.get(status, 'Service Albert indisponible (HTTP ' + str(status) + ').'), 'http_' + str(status))


def _request(api_key, method, route, payload=None, timeout=90):
    if ALBERT_PAUSED:
        raise AlbertServiceError('Albert temporairement désactivé pour les essais.', 'temporarily_disabled')
    if not isinstance(api_key, str) or not api_key.strip() or any(c in api_key for c in '\r\n'):
        raise AlbertServiceError('Clé Albert absente ou non conforme dans les secrets Streamlit.', 'key_unavailable')
    request = Request(BASE_URL + route, method=method,
                      headers={'Authorization': 'Bearer ' + api_key.strip(), 'Content-Type': 'application/json'},
                      data=json.dumps(payload).encode() if payload is not None else None)
    try:
        with build_opener(_NoRedirect()).open(request, timeout=timeout) as response:
            if response.status != 200:
                raise _http_error(response.status)
            data = response.read()
    except HTTPError as exc:
        status = exc.code
        exc.close()
        raise _http_error(status) from None
    except (URLError, TimeoutError, OSError):
        raise AlbertServiceError('Connexion Albert indisponible ou délai dépassé.', 'connection_unavailable') from None
    try:
        return json.loads(data)
    except (ValueError, UnicodeError):
        raise AlbertServiceError('Réponse Albert illisible.', 'unreadable_response') from None


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
    def __init__(self, api_key, model, temperature=0.0, timeout=90):
        if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9_./:-]{1,200}', model):
            raise AlbertError('Indiquez un identifiant exact de modèle Albert.')
        self._api_key = api_key
        self.provider = 'albert'
        self.timeout = timeout
        self.model = model
        self.temperature = temperature
        self.resolved_model = None

    def complete(self, prompt, **kwargs):
        if kwargs:
            raise AlbertError('Paramètres supplémentaires non pris en charge par ce comparateur.')
        data = _request(self._api_key, 'POST', '/chat/completions',
                        {'model': self.model, 'messages': [{'role': 'user', 'content': str(prompt)}],
                         'temperature': self.temperature, 'stream': False, 'max_tokens': 4096}, timeout=self.timeout)
        try:
            choice = data['choices'][0]
            content = choice['message']['content']
            if choice.get('finish_reason') == 'length':
                raise AlbertError('Réponse Albert tronquée par la limite de sortie ; résultat non validé.')
            if not isinstance(content, str) or not content.strip():
                raise AlbertServiceError('Albert ne fournit pas de réponse textuelle exploitable.', 'empty_response')
        except (KeyError, IndexError, TypeError):
            raise AlbertServiceError('Réponse Albert non conforme au format de génération attendu.', 'invalid_envelope') from None
        self.resolved_model = data.get('model') if isinstance(data.get('model'), str) else None
        # Seuls le texte de réponse et les compteurs sont transmis aux contrôles existants.
        return SimpleNamespace(text=content, raw={'usage': data.get('usage')})


class AlbertWithFallback:
    """Un seul essai Albert, puis secours conservé pour la fin de cette question.

    Un contenu documentaire insatisfaisant reste soumis au contrôle habituel ;
    il ne déclenche jamais ce secours. Les deux tentatives sont traçables.
    """
    def __init__(self, primary, fallback):
        self.primary, self.fallback = primary, fallback
        self.model = primary.model
        self.temperature = primary.temperature
        self.resolved_model = None
        self.fallback_reason = None

    def complete_with_attempts(self, prompt, invoke, **kwargs):
        if self.fallback_reason is None:
            try:
                result = invoke(self.primary, prompt, **kwargs)
                self.resolved_model = self.primary.resolved_model or self.primary.model
                return result
            except AlbertServiceError as exc:
                self.fallback_reason = exc.code
        # Pas de boucle, pas de retour Albert durant une réparation documentaire.
        result = invoke(self.fallback, prompt, **kwargs)
        self.resolved_model = self.fallback.model
        return result

    def complete(self, prompt, **kwargs):
        return self.complete_with_attempts(prompt, lambda target, text, **opts: target.complete(text, **opts), **kwargs)


def generation_llm(*, openai_llm, api_key=None, albert_model='', provider='albert'):
    """Objet neuf par question : aucun état de panne partagé entre collègues."""
    if ALBERT_PAUSED or provider == 'openai' or not api_key:
        return openai_llm
    if provider != 'albert':
        raise ValueError('FOURNISSEUR_IA doit valoir albert ou openai.')
    primary = AlbertLLM(api_key, albert_model or 'gpt-oss-120b',
                        temperature=openai_llm.temperature, timeout=45)
    return AlbertWithFallback(primary, openai_llm)
