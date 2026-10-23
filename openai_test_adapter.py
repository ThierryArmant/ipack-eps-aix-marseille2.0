"""Appels de test explicites, un seul appel réseau par étape, sans secours."""
import re
from types import SimpleNamespace

TEST_MODELS = ('gpt-4o-mini', 'gpt-4.1-mini', 'gpt-4.1', 'gpt-5.4')


class TestCallLimitError(RuntimeError):
    code = 'test_call_limit'


class OpenAITestLLM:
    provider = 'openai'
    temperature = 0.0

    def __init__(self, *, model, api_key, max_tokens, max_prompt_chars, client_factory=None):
        if model not in TEST_MODELS:
            raise ValueError('Modèle de test non autorisé.')
        self.model, self._api_key = model, api_key
        self.max_tokens, self.max_prompt_chars = max_tokens, max_prompt_chars
        self._factory, self._used = client_factory, False
        self.resolved_model = None

    def complete(self, prompt, **kwargs):
        if kwargs or not isinstance(prompt, str) or len(prompt) > self.max_prompt_chars:
            raise ValueError('Paramètres ou volume du test hors plafond.')
        if self._used:
            raise TestCallLimitError('Plafond atteint : aucune nouvelle génération de test.')
        self._used = True
        factory = self._factory
        if factory is None:
            from openai import OpenAI
            factory = OpenAI
        params = dict(model=self.model, messages=[{'role':'user','content':prompt}],
                      temperature=0.0, store=False)
        if self.model == 'gpt-5.4':
            params.update(reasoning_effort='none', max_completion_tokens=self.max_tokens)
        else:
            params['max_tokens'] = self.max_tokens
        with factory(api_key=self._api_key, max_retries=0, timeout=45) as client:
            result = client.chat.completions.create(**params)
        self.resolved_model = result.model
        if not (result.model == self.model or re.fullmatch(re.escape(self.model) + r'-\d{4}-\d{2}-\d{2}', result.model)):
            raise ValueError('Le service a répondu avec un autre modèle que celui demandé.')
        if not result.choices or not result.choices[0].message.content:
            raise ValueError('Le modèle ne renvoie aucun texte utilisable.')
        return SimpleNamespace(text=result.choices[0].message.content, raw=result)


def test_clients(model, api_key, client_factory=None):
    return (OpenAITestLLM(model=model, api_key=api_key, max_tokens=600,
                         max_prompt_chars=14000, client_factory=client_factory),
            OpenAITestLLM(model=model, api_key=api_key, max_tokens=1600,
                         max_prompt_chars=50000, client_factory=client_factory))
