"""Vérification manuelle et bornée de l'accès au modèle demandé, sans secours."""
import re


def probe_gpt54(api_key, client_factory=None):
    if not api_key:
        return {'ok': False, 'message': 'Clé OpenAI absente des secrets du Hub.'}
    try:
        if client_factory is None:
            from openai import OpenAI
            client_factory = OpenAI
        with client_factory(api_key=api_key, max_retries=0, timeout=20) as client:
            response = client.chat.completions.create(
                model='gpt-5.4',
                messages=[{'role': 'user', 'content': 'Réponds uniquement OK.'}],
                reasoning_effort='none', max_completion_tokens=32, store=False)
        model = response.model
        text = response.choices[0].message.content
        if not model or not (model == 'gpt-5.4' or model.startswith('gpt-5.4-')) or not text:
            return {'ok': False, 'message': 'Réponse reçue, mais accès GPT-5.4 non confirmé.'}
        usage = response.usage
        return {'ok': True, 'message': 'Accès GPT-5.4 confirmé avec la clé du Hub.',
                'model': model, 'input_tokens': getattr(usage, 'prompt_tokens', None),
                'output_tokens': getattr(usage, 'completion_tokens', None)}
    except Exception as exc:
        status = getattr(exc, 'status_code', None)
        code = getattr(exc, 'code', None)
        # Ne jamais afficher le message brut du SDK, ses en-têtes ou la clé.
        safe_code = code if isinstance(code, str) and re.fullmatch(r'[a-z_]{1,60}', code) else None
        messages = {401: 'Authentification refusée pour la clé du Hub.',
                    403: 'Accès refusé : vérifier les permissions du projet ou du modèle.',
                    404: 'Modèle introuvable ou non accessible avec cette clé.',
                    429: 'Quota, crédit ou limite de débit atteint ; accès non confirmé.',
                    400: 'Paramètres refusés par le service ; accès non confirmé.'}
        return {'ok': False, 'message': messages.get(status, 'Vérification indisponible ; accès non confirmé.'),
                'http_status': status, 'error_code': safe_code}
