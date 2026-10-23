"""Essai manuel unique : isoler une fiche sans changer son contenu."""
TARGET = 'data/examens/complement_saisie_bloquee_diagnostic.txt'

def consume_single_document_test(state, mode):
    if not state.get('is_admin', False):
        state.pop('single_document_pending', None)
        return False
    if mode != 'examens':
        return False
    return bool(state.pop('single_document_pending', False))

def isolate_document(packets, path):
    selected = [p for p in packets if p.get('path') == path]
    if len(selected) != 1:
        raise ValueError("Essai annulé : la fiche unique attendue n'est pas disponible.")
    return selected
