"""Orientation commune avant recherche : guide, précision et réponse documentaire existante."""
from guide_request import (requests_guide, vague_request_opens_guide, MESSAGE,
                           MESSAGE_PARCOURS, MESSAGE_EXAMENS)
from guided_navigation import suggested_entries
from hub_session import public_label
from knowledge_catalog import clarification, documented_response
from response_controls import documented_dnb_dispense


def prepare_question(prompt, niveau_actuel_form, mode):
    _guide_demande = (requests_guide(prompt, mode, niveau_actuel_form)
                      or vague_request_opens_guide(prompt, mode, niveau_actuel_form))
    GUIDE_MESSAGE = MESSAGE
    if _guide_demande and mode == 'examens':
        GUIDE_MESSAGE = MESSAGE_EXAMENS
    elif _guide_demande and suggested_entries(prompt, public_label(niveau_actuel_form)):
        GUIDE_MESSAGE = MESSAGE_PARCOURS
    demande_precision = GUIDE_MESSAGE if _guide_demande else ('' if documented_dnb_dispense(prompt, niveau_actuel_form)
                                                            else clarification(prompt, niveau_actuel_form, mode=mode))
    if mode == 'textes' and demande_precision.startswith("Pour décider d'une note"):
        demande_precision = ''
    reponse_documentee, source_documentee = documented_response(prompt, niveau_actuel_form, mode)
    kind = 'documentee' if reponse_documentee else ('guide' if _guide_demande else
                                                 ('clarification' if demande_precision else 'ia'))
    return dict(kind=kind, guide=_guide_demande, precision=demande_precision,
                documented_answer=reponse_documentee, documented_source=source_documentee)
