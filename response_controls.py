"""Conditions décisives issues de fiches vérifiées, sans appel réseau."""
import re


def complete_gt_shn_conditions(question, answer, documentary_context):
    """Complète une omission, uniquement lorsque la fiche GT vérifiée est présente."""
    verified_notice = '### Bac général et technologique : SHN et sportifs non listés'
    if verified_notice not in documentary_context or 'MENE2531948N' not in documentary_context:
        return answer
    if not re.search(r'\bbac|baccalaur|\bccf\b|examen|certification|20\s*/?\s*20', question, re.I):
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


def documented_dnb_dispense(question, public):
    """Une dispense déjà attestée ne constitue pas une décision médicale à prendre."""
    q = question.lower()
    return bool(re.search(r'dnb|brevet', q)
                and re.search(r'dispense r[eé]glementaire', q)
                and re.search(r'attest[eé]|accord[eé]|valid[eé]', q))


def reference_url(metadata, question):
    years = set(re.findall(r'\b20\d{2}\b', question))
    if len(years) == 1:
        return metadata.get('urls_par_session', {}).get(next(iter(years)), metadata.get('url', ''))
    return metadata.get('url', '')


def constrain_santorin_unlock(question, answer, documentary_context):
    q = question.lower().replace('é', 'e')
    if 'santorin' not in q or not re.search(r'deverrouill|lot.{0,30}(ferme|verrouille)', q):
        return answer
    if 'statut: guide_technique_actuel_verifie' in documentary_context:
        return answer
    return ('Les documents consultés ne permettent pas de confirmer un droit de déverrouillage '
            'pour votre rôle, votre académie et la version de Santorin utilisée. '
            'Un lot fermé ou un bouton absent ne démontre pas un droit universel réservé aux chefs d’établissement. '
            'Précisez votre rôle, la session et le message affiché ; vérifiez le guide technique actuel '
            'ou faites confirmer l’habilitation par l’assistance académique. '
            'Ne pas confondre les conditions pour verrouiller un lot avec les droits pour le déverrouiller.')


def prevent_invented_gt_medical_sequence(question, answer, documentary_context):
    q = question.lower().replace('é', 'e').replace('è', 'e')
    a = answer.lower().replace('é', 'e').replace('è', 'e')
    third = r'(?:troisieme|3e).{0,35}(?:epreuve|sequence)'
    if not (re.search(r'bac\s*(?:gt|general|technologique)', q) and 'inapt' in q
            and 'MENE2531948N' in documentary_context and re.search(third, a)
            and not re.search(third, q)):
        return answer
    return ('La question ne précise pas qu’une troisième épreuve est empêchée ni que deux notes sont déjà acquises. '
            'Je ne peux donc pas imposer ce scénario ni un code DI. '
            'Pour préserver les évaluations possibles, il faut partir des indications médicales, '
            'de la période de validité, des APSA concernées et des évaluations déjà réalisées. '
            'Pour une inaptitude partielle, l’épreuve peut être adaptée sur les indications médicales ; '
            'une évaluation différée peut être envisagée selon la situation. '
            'Les menus et codes de saisie nécessitent un guide technique actuel applicable à votre académie. '
            'Référence : note MENE2531948N du 20 février 2026, dispositions relatives à l’inaptitude temporaire.')
