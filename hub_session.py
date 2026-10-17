"""État de navigation : les préférences ne sont pas une mémoire des réponses."""
def allowed_modules(public):
    if not public:
        return ()
    return ('textes',) if public == '1er degré' else ('ipack', 'examens', 'textes')


def select_public(state, public):
    state['public_valide'] = bool(public)
    state['messages_hub'] = []
    state.pop('current_prompt', None)
    if public == '1er degré':
        select_module(state, 'textes')


def select_module(state, module):
    if state.get('niveau_actif_form') == '1er degré':
        module = 'textes'
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
                and state.get('active_module') in allowed_modules(state.get('niveau_actif_form'))
                and (state.get('active_module') != 'examens' or state.get('academie_utilisateur')))


def public_label(public):
    """Libellé affiché ; les identifiants utilisés par la recherche restent stables."""
    return {
        'Lycée Général & Techno': 'Lycée voie générale',
        'Lycée Pro / CAP': 'Lycée voie professionnelle',
    }.get(public, public)
