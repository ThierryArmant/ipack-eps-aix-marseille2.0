"""Conditions décisives issues de fiches vérifiées, sans appel réseau."""
import re


def complete_gt_shn_conditions(question, answer, documentary_context):
    """Complète une omission, uniquement lorsque la fiche GT vérifiée est présente."""
    verified_notice = '### Bac général et technologique : SHN et sportifs non listés'
    if verified_notice not in documentary_context or 'MENE2531948N' not in documentary_context:
        return answer
    if re.search(r'option|eppcs', question, re.I):
        return answer
    if not answer.strip() or answer.startswith('Erreur de traitement IA'):
        return answer
    has_authority = re.search(r'recteur|rectorale?', answer, re.I)
    has_evidence = re.search(r'justificatif|justifier|attestation|statut.{0,30}(attest|justif)', answer, re.I)
    has_proposal = re.search(r'comit[eé] de pilotage', answer, re.I)
    if has_authority and has_evidence and has_proposal:
        return answer
    return answer + (
        '\n\n<strong>Conditions de l’aménagement :</strong> le statut doit être justifié lors de '
        'l’inscription. L’aménagement EPS du bac général ou technologique suppose une proposition '
        'du comité de pilotage des sportifs de haut niveau et une validation par le recteur. '
        'L’inscription en sport-études ne suffit pas à accorder cet aménagement ni la note de 20/20. '
        'Référence : note de service du 20 février 2026, MENE2531948N, chapitre 4.'
    )
