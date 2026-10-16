"""Contrat d'application des preuves, indépendant des thèmes EPS.

Les ancrages sont contrôlés littéralement ; leur interprétation reste celle du
modèle. Ce contrôle n'est pas une preuve d'implication sémantique.
"""
import re
import unicodedata


def literal(value):
    value = unicodedata.normalize('NFKC', str(value)).replace('’', "'")
    return re.sub(r'\s+', ' ', value).strip().casefold()


def grounding_errors(claims, question):
    """Vérifie les ancrages et interdit l'effacement d'une condition inconnue."""
    errors = []
    for index, claim in enumerate(claims):
        problems = []
        ground = claim.get('application')
        if not isinstance(ground, dict):
            errors.append({'index': index, 'errors': ['application à la question absente']})
            continue
        question_quote = ground.get('question_quote')
        if (not isinstance(question_quote, str) or len(question_quote.strip()) < 4
                or literal(question_quote) not in literal(question)):
            problems.append('ancrage absent de la question réelle')
        if ground.get('role') not in ('answer', 'necessary_step', 'clarification'):
            problems.append('développement sans rôle utile pour la demande')
        source_quote = ground.get('source_quote')
        proofs = [e.get('quote', '') for e in claim.get('evidence', [])]
        if (not isinstance(source_quote, str) or not 20 <= len(source_quote) <= 1000
                or not any(literal(source_quote) in literal(p) for p in proofs)):
            problems.append('preuve ciblée absente des passages sélectionnés')
        conditions = ground.get('conditions')
        if not isinstance(conditions, list) or len(conditions) > 6:
            problems.append('conditions non structurées')
            conditions = []
        for condition in conditions:
            if not isinstance(condition, dict):
                problems.append('condition non structurée')
                continue
            quote = condition.get('source_quote')
            if (not isinstance(quote, str) or len(quote.strip()) < 4
                    or not any(literal(quote) in literal(p) for p in proofs)):
                problems.append('condition absente de la preuve')
                continue
            state = condition.get('state')
            if state == 'established':
                anchor = condition.get('question_quote')
                if (not isinstance(anchor, str) or len(anchor.strip()) < 4
                        or literal(anchor) not in literal(question)):
                    problems.append('condition déclarée acquise sans fait cité de la question')
            elif state == 'unknown':
                # Le rédacteur conserve les mots de la condition dans la même
                # affirmation : une réserve ailleurs ne corrige pas une étape.
                if literal(quote) not in literal(claim['text']):
                    problems.append('condition inconnue supprimée de l’affirmation')
            else:
                problems.append('condition exclue ou état invalide : retirer cette branche')
        # Un antécédent explicite dans la preuve ciblée ne peut disparaître
        # simplement parce que le modèle a retourné conditions=[].
        if isinstance(source_quote, str):
            antecedents = re.findall(
                r"\b(?:si|lorsque|en cas de|à condition que|sous réserve que)\s+[^,;:.!?\n]{4,160}(?=[,;:.!?\n]|$)",
                source_quote, re.I)
            for antecedent in antecedents:
                if not any(isinstance(c, dict) and isinstance(c.get('source_quote'), str)
                           and (literal(antecedent) in literal(c['source_quote'])
                                or literal(c['source_quote']) in literal(antecedent))
                           for c in conditions):
                    problems.append('antécédent explicite de la preuve non examiné')
        if problems:
            errors.append({'index': index, 'claim': claim, 'errors': problems})
    return errors


GROUNDING_SCHEMA = '''{"claims":[{"section":"decision|condition|etape|limite",
"text":"Affirmation avec ses conditions utiles",
"evidence":[{"document_id":"D1","passage_ids":["D1P1"]}],
"application":{"role":"answer|necessary_step|clarification",
"question_quote":"fragment exact de la demande auquel cette phrase répond",
"source_quote":"phrase exacte ciblée dans les passages sélectionnés",
"conditions":[{"source_quote":"condition exacte de la source",
"state":"established|unknown","question_quote":"fait exact si établi, sinon chaîne vide"}]}}]}'''

GROUNDING_INSTRUCTIONS = '''
Avant chaque affirmation, établir son application (champ application, non affiché).
question_quote : fragment EXACT de la demande auquel cette affirmation répond.
source_quote : phrase EXACTE ciblée qui justifie cette action sur cet objet,
et non un paragraphe entier couvrant plusieurs cas. Le même sujet ne suffit pas.
role : answer pour la réponse directe, necessary_step pour une étape indispensable,
clarification pour une information réellement manquante. Supprimer le reste.
Ne pas développer une branche voisine à titre de précaution si elle ne résout pas
la demande et qu'aucun fait fourni ne l'établit.
Préserver l'objet ET l'effet de l'action source : une manipulation sur un fichier
ne prouve pas une modification de statut ; aucun effet supplémentaire n'est acquis.
conditions : relever les antécédents nécessaires de la source pour cette affirmation.
Si un fait de la question les établit, state=established et citer ce fait exactement.
Sinon state=unknown : CONSERVER MOT POUR MOT la courte condition source dans la
phrase publiée et présenter l'action comme conditionnelle, y compris dans Démarches.
Si les faits excluent la branche, ne pas produire d'affirmation pour cette branche.
Une cause possible n'est pas une cause confirmée. Si le symptôme manque, demander
la précision utile avant de prescrire sa résolution comme certaine.
Pour une alternative, exposer dès la décision les issues pertinentes ; ne pas cacher
la seconde dans les conditions. Ne pas répéter une même règle dans plusieurs rubriques.
Une demande de précision invite à compléter la question ; ne pas annoncer un bouton,
un champ, une pièce jointe ou un écran qui n'est pas décrit dans l'interface fournie.
'''
