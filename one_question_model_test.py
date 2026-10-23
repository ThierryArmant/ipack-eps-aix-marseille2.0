"""Essais administrateur bornés, consommés par les questions directes."""


def consume_gpt41_test(state):
    remaining = state.get('gpt41_once_pending', 0)
    if not state.get('is_admin', False):
        state.pop('gpt41_once_pending', None)
        return False
    if not isinstance(remaining, int) or not 1 <= remaining <= 10:
        state.pop('gpt41_once_pending', None)
        return False
    if remaining == 1:
        state.pop('gpt41_once_pending', None)
    else:
        state['gpt41_once_pending'] = remaining - 1
    return True


def consume_model_test(state):
    from openai_test_adapter import TEST_MODELS
    model = state.get('openai_test_model', 'gpt-4.1')
    if model not in TEST_MODELS:
        state.pop('gpt41_once_pending', None)
        return None
    return model if consume_gpt41_test(state) else None
