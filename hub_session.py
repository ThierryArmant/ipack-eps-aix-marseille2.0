"""État de navigation : les préférences ne sont pas une mémoire des réponses."""
def select_module(state, module):
    state['active_module'] = module
    state['contexte_valide'] = True
    state['messages_hub'] = []
    state.pop('current_prompt', None)


def new_question(state):
    state['messages_hub'] = []
    state.pop('current_prompt', None)
    state['reset_steps'] = False


def ready_for_question(state):
    return bool(state.get('contexte_valide') and state.get('niveau_actif_form')
                and (state.get('active_module') != 'examens' or state.get('academie_utilisateur')))
