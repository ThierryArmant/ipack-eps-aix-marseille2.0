"""Catalogue documentaire local : aucune dépendance réseau ni appel d'API."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path


def normalise(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                   if unicodedata.category(c) != 'Mn')


_EQUIVALENCES = None


def enrich(text):
    """Question normalisée + termes officiels équivalents au langage courant (config/langage_collegues.json).

    Rien n'est remplacé : les termes sont ajoutés, pour que les motifs existants restent valables."""
    global _EQUIVALENCES
    if _EQUIVALENCES is None:
        try:
            data = json.loads((Path(__file__).resolve().parent / 'config' / 'langage_collegues.json').read_text(encoding='utf-8'))
            _EQUIVALENCES = [(re.compile(e['motif']), e['ajout']) for e in data.get('equivalences', [])]
        except (OSError, ValueError, re.error):
            _EQUIVALENCES = []
    q = normalise(text)
    ajouts = [ajout for motif, ajout in _EQUIVALENCES if motif.search(q)]
    return q + (' || ' + ' ; '.join(ajouts) if ajouts else '')


def active_paths(folder):
    """Parcours stable, récursif, sans les archives conservées pour traçabilité."""
    root = Path(folder)
    return sorted(p for p in root.rglob('*.txt')
                  if not {'archives', 'archive', 'a_verifier'} & set(p.parts))


def fingerprint():
    digest = hashlib.sha256()
    for folder in ('data', 'config'):
        for p in sorted(Path(folder).rglob('*')):
            if p.is_file() and p.suffix in ('.txt', '.json', '.csv'):
                digest.update(str(p).encode())
                digest.update(p.read_bytes())
    return digest.hexdigest()


def catalog():
    path = Path('config/catalogue_documents.json')
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def document_records(folder):
    entries, seen = catalog(), set()
    paths = active_paths(folder)
    if folder in ('data/ipack', 'data/examens', 'data/textes'):
        paths += active_paths('data/commun')
    for p in paths:
        if entries.get(p.as_posix(), {}).get('retrieval_enabled') is False:
            continue
        content = p.read_text(encoding='utf-8')
        signature = hashlib.sha256(content.encode()).hexdigest()
        if signature in seen:
            continue
        seen.add(signature)
        metadata = dict(entries.get(p.as_posix(), {}))
        metadata.update(source=p.name, path=p.as_posix())
        metadata.setdefault('statut', 'synthese_non_revalidee')
        yield content, metadata


def incompatible(text, targets, metadata=None):
    """Filtre uniquement les portées explicitement déclarées ; pas d'inférence sur un mot isolé."""
    match = re.search(r'\[PORTEE:\s*([a-z,\s]+)\]', text)
    declared = (metadata or {}).get('examens') or []
    scopes = set(declared) if declared else ({s.strip() for s in match.group(1).split(',')} if match else set())
    return bool(targets and scopes and not scopes & set(targets))


def passage_key(text):
    """Deux passages différents ne deviennent pas doublons par leur introduction."""
    return hashlib.sha256(re.sub(r'\s+', ' ', text).strip().encode()).hexdigest()


def obsolete_reference(text):
    """Ces références ne justifient plus une réponse pour la session courante."""
    q = normalise(text)
    if 'mene2517122c' in q or 'mene2505383c' in q:
        return False  # une fiche actuelle peut expliquer quel texte elle remplace
    return bool(re.search(r'mene2037057c|mene2018678c|circulaire (du )?29 decembre 2020|'
                          r'circulaire (du )?17 juillet 2020', q))


def section_scopes(title):
    q = normalise(title)
    scopes = set()
    if re.search(r'bac(calaureat)? ?(general|gt|technologique)|lycee gt', q):
        scopes.add('gt')
    if re.search(r'bac(calaureat)? ?(pro|professionnel)|lycee pro|\bbma\b', q):
        scopes.add('pro')
    if re.search(r'\bcap\b', q):
        scopes.add('cap')
    if re.search(r'\bdnb\b|\bbrevet\b', q):
        scopes.add('dnb')
    return sorted(scopes)


def activity_goal_clarification(question, public):
    """Ancienne clarification de champ, déplacée avant recherche et génération.

    Aucun verdict de certification : demander l'objectif manquant seulement.
    """
    if public not in ('Lycée Général & Techno', 'Lycée Pro / CAP'):
        return ''
    q = normalise(question).replace('course de duree', 'course en duree')
    if not re.search(r'\bcourse en duree\b', q):
        return ''
    if re.search(r'performance|\bca ?[15]\b|champ [15]|chrono|entretien', q):
        return ''
    if not re.search(r'protocole|ensemble certificatif|meme |possible|valable|ca passe|compatible|champ|depos|referentiel|\bfca\b', q):
        return ''
    return ("Pouvez-vous préciser ce que vous mettez derrière « course en durée » : "
            "performance mesurée (demi-fond, CA1) ou entretien de soi (course en durée, CA5) ? "
            "C'est ce que l'élève apprend et ce qui est évalué qui fixe le champ d'apprentissage, pas le nom de l'activité. "
            "Posez une nouvelle question complète dans la zone habituelle, en conservant votre demande initiale "
            "et en précisant cet objectif.")


def teaching_registration_clarification(question):
    """L'activité et la classe ne déterminent pas la rubrique à renseigner."""
    q = normalise(question)
    teaching = re.search(r"enseign|je (?:fais|pratique)|(?:ma|mes|avec les|avec ma|avec mes).{0,20}(?:eleves|classes?|[3-6](?:e|eme))", q)
    registration = re.search(r'renseign|rempl|saisir|saisie|declar|enregistr|rentrer|indiquer', q)
    target = re.search(r'programmation|sequences?|groupes?|emploi du temps|dossier|fiche|specialit|competence|'
                       r'liste.{0,15}apsa|(?:dans|menu|rubrique).{0,20}apsa|protocole|certific|notes?|evaluation|inapt', q)
    if teaching and registration and not target:
        return "Pouvez-vous préciser ce que vous souhaitez renseigner dans iPackEPS ?"
    return ''


def clarification(question, public, *, mode=None):
    q = normalise(question)
    # Le contexte iPackEPS ne désigne pas le logiciel dans lequel le collègue
    # saisit ses notes. Identifier l'outil avant toute procédure de déblocage.
    if (mode == 'ipack' and re.search(r'\bnotes?\b', q)
            and re.search(r'sais|enregistr|rentr|mettre|modifi|cases?', q)
            and re.search(r'ne peux (?:plus|pas)|n.arrive (?:plus|pas)|impossible|bloqu|grise|inacti', q)
            and not re.search(r'ipack|santorin|cyclades|pronote|ecole.?directe|\blsu\b|\bccf\b|\baflp?\b|\blots?\b|protocole', q)):
        return ("Dans quel logiciel la saisie est-elle bloquée : Santorin, Pronote/ÉcoleDirecte ou iPackEPS ?")
    if mode in (None, "ipack"):
        teaching = teaching_registration_clarification(question)
        if teaching:
            return teaching
    goal = activity_goal_clarification(question, public)
    if goal:
        return goal
    q = normalise(question)
    # Les procédures de licences UNSS ne sont pas documentées par des sources
    # dont l'utilisation a été autorisée pour le HUB. Ne jamais substituer
    # une fiche iPackEPS sur les élèves ou les groupes à cette demande.
    if re.search(r'\bunss\b', q) and re.search(r'licenc|affili|adhes', q):
        return ("Je ne dispose pas de documentation autorisée permettant de confirmer "
                "la procédure de licence ou d'affiliation UNSS. Je ne peux donc pas "
                "vous indiquer de manipulation fiable dans iPackEPS.")
    # Une alerte de comptage sans écran ni message exact ne permet pas de
    # choisir entre déclaration des activités et contrôle d'un protocole.
    if (re.search(r'ipack|verificateur', q) and re.search(r'apsa', q)
            and re.search(r'pas assez|insuffisant|plus (?:que |de )?3|nombre', q)
            and not re.search(r'protocole|ensemble certificatif|dossier.{0,15}apsa|\bcourses\b|relais|demi.fond', q)):
        return ("Sur quel écran le vérificateur signale-t-il le problème : déclaration des APSA du dossier EPS "
                "ou protocole d’un groupe dans le dossier certificatif ? Recopiez le message exact et indiquez "
                "les APSA concernées, sans nom d’élève, pour identifier la vérification adaptée.")
    # « Vœux SSS » ne dit pas quelle demande de campagne est envisagée.
    if (re.search(r'voeux|vœux', q) and re.search(r'\bsss\b|section sportive', q)
            and not re.search(r'ouvr|ouverture|reconduc|renouv|fermet|chang.{0,20}(?:apsa|activite)', q)):
        return ("Ces vœux concernent-ils l’ouverture d’une section sportive, sa reconduction ou sa fermeture "
                "pour l’année prochaine ? La démarche iPackEPS dépend du type de demande. "
                "Pour une question de dates ou de pièces de campagne, indiquez aussi votre académie.")
    # Identifier le dossier avant d'en inventer le chemin. Cette clarification
    # ne décide ni du contenu du projet ni d'une règle institutionnelle.
    project_search = re.search(r'projet', q) and re.search(r'retrouv|consult|bilan|archive|precedent', q)
    project_type = re.search(r'\beps\b|\bas\b|etablissement|\bsss\b|section sportive|sports.etudes', q)
    # Relevé à l'écran (18/10/2026) : établissement, EPS, AS et SSS sont tous dans [Dossier EPS] > [Projets] ;
    # la fiche ciblée répond directement, sans demander le type de projet.
    # Les conditions médicales restent nécessaires pour choisir une valeur
    # individuelle, pas pour expliquer un circuit logiciel ou les possibilités.
    if re.search(r'dispens.{0,20}epreuve.{0,15}eps|\baflp\d?\b|'
                 r'ccf.{0,40}(?:mercredi|emploi du temps)|'
                 r'(?:transform|modifi|corrig).{0,25}(?:note|dispense)|'
                 r'note.{0,30}transform|dispens.{0,25}deux activites', q):
        return ''
    # Une question de participation à une autre épreuve ne demande pas de
    # déterminer une note ou un statut médical individuel.
    participation = re.search(r'epreuve facultative|\boption\b|peut.{0,30}(?:passer|presenter|participer)', q)
    chooses_value = re.search(r'quelle? (?:note|code|statut)|je (?:mets|dois mettre)|je saisis|\b(?:di|disp|zero|0)\b', q)
    if participation and not chooses_value:
        return ''
    # La période couvrant l'épreuve est déjà donnée : laisser les passages exposer
    # les possibilités, sans transformer la question en choix médical automatique.
    if re.search(r'certificat(?: medical)?.{0,70}(?:couvr|valable|valide).{0,55}(?:jour|date|ccf|epreuve)|'
                 r'(?:jour|date) du ccf.{0,55}(?:couvert|certificat)', q):
        if public != 'Lycée Pro / CAP' or re.search(r'\bcap\b|bac(?:calaureat)?\s+(?:pro|professionnel)', q):
            return ''
    individual_value = bool(re.search(
        r'\b(?:di|disp|ab|abs|zero|0)\b(?! (?:candidat|eleve|lot))|je (?:mets|dois mettre)|'
        r'(?:quelle|quel|comment).{0,25}(?:note|code|statut).{0,25}(?:mettre|saisir|choisir)', q))
    # Une question sur le certificat lui-même (arrivé en retard, rétroactif, valable, modèle) ne porte pas
    # sur le choix d'une note : la demande de précisions médicales la détournait (audit en ligne, D8).
    certificate_question = bool(re.search(
        r'certificat.{0,80}(?:arriv|retard|tardi|apres|retroacti|antidat|valable|valide|accept|recevable|'
        r'conforme|modele|date|delai)|(?:retroacti|antidat|en retard).{0,60}certificat', q))
    if certificate_question and not individual_value:
        return ''
    # Règle générale (AFL2/AFL3 seuls) ou situation déjà décrite (nombre de notes disponibles) : le texte
    # national permet d'exposer les possibilités ; la demande de précisions bloquait la réponse (EX091, EX106).
    general_rule = bool(re.search(r'afl ?2.{0,40}afl ?3', q))
    facts_given = bool(re.search(
        r"qu.une (?:seule )?note|une seule note|une note sur (?:deux|trois)|deux notes|"
        r"(?:deux|2) inaptitudes?(?: totales?| partielles?)? et (?:une|1) note|"
        r"not[eé]\w*.{0,25}(?:sur|que sur) (?:une|1) (?:seule )?[eé]preuve|"
        r"\bdi ?\+ ?di\b|di partout|(?:inapte|dispense)\w* sur (?:une|deux|1|2|les deux) (?:epreuves?|activites?)", q))
    exam_named = bool(re.search(r'\b(cap|dnb|brevet|college|lgt|gt)\b|bac(calaureat)?\s+(pro|professionnel|general|technologique)', q))
    if (general_rule or facts_given) and (public != 'Lycée Pro / CAP' or exam_named):
        return ''
    procedure = bool(re.search(
        r'santorin|cyclades|protocole|lot|reinitialis|reaffect|'
        r'qui.{0,35}(?:choisi|decid|valid|coch)|cfa|apprenti|'
        r'(?:epreuve|evaluation).{0,20}adapt|'
        r'adapt.{0,25}(?:epreuve|evaluation)|dispens.{0,25}epreuve', q))
    if procedure and not individual_value:
        return ''
    # General procedures do not choose a medical status or an individual grade.
    asks_code = bool(re.search(r'\b(di|disp|ab|zero|0)\b|je (mets|dois mettre)|je saisis', q))
    general_procedure = bool(re.search(
        r'quel.*certificat|qui.*(?:valide|decide|declare)|comment.*(?:declarer|enregistrer)|'
        r'inscri.*(?:inapt|apte)|inapt.*inscri|formation continue|'
        r'difference.*(?:ccf|ponctuel)|amenag.*(?:delai|recours)|'
        r'(?:delai|recours).*amenag', q))
    if general_procedure and not asks_code:
        return ''
    medical = bool(re.search(r'inapt|dispens|certificat medical', q))
    decision = bool(re.search(r'\b(di|disp|zero|0)\b|sais|notes?|ccf|epreuv', q))
    exam = bool(re.search(r'\b(cap|dnb|brevet|college|lgt|gt)\b|bac(calaureat)?\s+(pro|professionnel|general|technologique)', q))
    # Le choix CAP / bac pro ne change que les décisions individuelles ou médicales ;
    # une question d'outil (export, import, absences, tablette) reçoit les deux réponses.
    if public == 'Lycée Pro / CAP' and decision and not exam and (medical or individual_value):
        return ('Précisez le diplôme concerné : CAP ou baccalauréat professionnel, ainsi que la session. '
                'Ces deux examens n\'ont pas les mêmes modalités. Aucun code de saisie ne peut être choisi à ce stade.')
    general_information = bool(re.search(
        r'comment est calcul|quel certificat|quels? certificats|comment declarer|comment enregistrer|'
        r'qui (le )?valide|quelle (est la )?note finale|(?:on|doit.on|peut.on) fai(?:t|re) la moyenne|'
        r'comment calculer|quel calcul|coefficient|comment fonctionne.*(?:inapt|dispens)', q))
    if general_information and not re.search(r'\b(di|disp|ab|zero|0)\b|\bsais|je (mets|dois mettre)', q):
        return ''
    medical_type = bool(re.search(r'partiel|total', q))
    medical_period = bool(re.search(r'temporaire|permanent|toute l.annee|'
                                    r'\bdu\s+\d|\bjusqu|\bpendant\s+\d|\bpour\s+\d', q))
    if medical and decision and not (medical_type and medical_period):
        return ('Pour décider d\'une note ou d\'un statut, précisez si l\'inaptitude est totale ou partielle, '
                'sa période de validité, les évaluations déjà réalisées et la possibilité d\'une épreuve adaptée ou différée. '
                'Le mot « dispensé » seul ne permet pas de choisir entre zéro, DI et une dispense d\'épreuve.')
    return ''


# Le niveau choisi compte comme un mot de la question pour les exclusions de fiche :
# une fiche collège qui exclut « lycee » ne doit pas répondre à un professeur de lycée.
_LEVEL_WORD = {'Collège (DNB)': 'college', 'Lycée Général & Techno': 'lycee',
               'Lycée Pro / CAP': 'lycee', '1er degré': 'ecole primaire'}


def canonical_public(public):
    return {'Collège': 'Collège (DNB)', 'Lycée voie générale': 'Lycée Général & Techno',
            'Lycée voie professionnelle': 'Lycée Pro / CAP'}.get(public, public)


def reference_notice(targets, question=None, public=None):
    entries = catalog()
    result = []
    public = canonical_public(public)
    level = _LEVEL_WORD.get(public, '')
    for path, md in entries.items():
        if md.get('retrieval_enabled') is False:
            continue
        if not md.get('prioritaire') or (md.get('examens') and not set(md['examens']) & set(targets)):
            continue
        if question is not None:
            q = normalise(question)
            enriched = enrich(question)
            years = set(re.findall(r'\b20\d{2}\b', q))
            if years and md.get('sessions') and not years & set(md['sessions']):
                continue
            # Motifs positifs : sur la question enrichie du langage courant ; exclusions : sur la question d'origine.
            scoped_patterns = md.get('motifs_contextuels', {}).get(public, [])
            if not any(re.search(m, enriched) for m in md.get('motifs', []) + scoped_patterns):
                continue
            if any(re.search(m, q) or (level and re.search(m, level)) for m in md.get('exclure_motifs', [])):
                continue
        result.append((path, md))
    # Une fiche de situation doit précéder une synthèse générale : dix passages
    # sont transmis au maximum et une fiche exclusive peut interrompre la recherche.
    return sorted(result, key=lambda item: -item[1].get('priorite', 0))



def has_text_reference(question, public):
    """Un sujet professionnel reconnu par une fiche prioritaire n'est pas hors périmètre.

    Ce repère autorise seulement la recherche : il ne produit ni réponse, ni décision.
    Les fiches propres aux examens et aux logiciels ne sont pas utilisées pour élargir
    l'onglet Textes. Les motifs et exclusions restent ceux du catalogue.
    """
    public, _ = effective_context(question, public, 'textes')
    targets = {'Collège (DNB)': {'dnb'}, 'Lycée Général & Techno': {'gt'},
               'Lycée Pro / CAP': {'pro', 'cap'}, '1er degré': {'primaire'}}.get(public, set())
    return any(md.get('priorite', 0) >= 300
               and md.get('modes') == ['textes']
               and Path(path).is_file()
               for path, md in reference_notice(targets, question, public))


def documented_response(question, public, mode):
    """Réponse relue et ciblée du catalogue, sans réécriture par le modèle."""
    q = normalise(question)
    targets = set()
    if re.search(r'bac(?:calaureat)?\s+(?:pro|professionnel)', q):
        targets.add('pro')
    if re.search(r'\bcap\b', q):
        targets.add('cap')
    if re.search(r'bac(?:calaureat)?\s+(?:general|gt|technologique)', q):
        targets.add('gt')
    if re.search(r'\bdnb\b|\bbrevet\b', q):
        targets.add('dnb')
    if not targets:
        targets = {'Collège (DNB)': {'dnb'}, 'Lycée Général & Techno': {'gt'},
                   'Lycée Pro / CAP': {'pro', 'cap'}}.get(public, set())
    for path, md in reference_notice(targets, question, public):
        if md.get('modes') and mode not in md['modes']:
            continue
        if not Path(path).is_file():
            continue
        # Le mot « installation » seul ne désigne pas une installation logicielle.
        # Une réponse d'accès à un logiciel exige un objet technique explicite.
        if path == 'data/ipack/acces_ipackeps_problemes.txt' and not re.search(
                r'\bipack|logiciel|application|ordinateur|navigateur|windows|\bmac\b|esterel|arena', q):
            continue
        if path == 'data/ipack/acces_ipackeps_problemes.txt' and re.search(
                r'installations?.{0,35}(?:sportiv|ferme|travaux|indisponib)|'
                r'(?:ferme|travaux|indisponib).{0,35}installations?', q):
            continue
        responses = md.get('reponses_directes', []) + [{
            'motifs': md.get('reponse_directe_motifs', []),
            'reponse': md.get('reponse_directe', '')}]
        for response in responses:
            if response.get('reponse') and any(re.search(m, q) for m in response.get('motifs', [])):
                return response['reponse'], md
    return '', {}


def effective_context(question, public, mode):
    """Les diplômes explicites priment ; un protocole seul reste ambigu."""
    public = canonical_public(public)
    q = normalise(question)
    pro = bool(re.search(r"\bbac(?:calaureat)?\s+(?:pro|professionnel)|\b(?:bcp|cap)\b", q))
    gt = bool(re.search(r"\bbac(?:calaureat)?\s+(?:gt|general|technologique)|\b(?:seconde|premiere|terminale)\b", q))
    college = bool(re.search(r"\bdnb\b|\bbrevet\b|\bcollege\b|"
                             r"(?:eleves?|classes?|mes|nos|les|de|en) (?:sixiemes?|cinquiemes?|quatriemes?|troisiemes?|6e|5e|4e|3e)\b", q))
    primaire = bool(re.search(r"\b(?:cp|ce[12]|cm[12])\b|premier degre|elementaire|maternelle|ecole primaire", q))
    # Le lieu de travail d'un adulte ne définit pas le public des élèves.
    secondaire_explicit = bool(re.search(r"\bdnb\b|\bbrevet\b|(?:eleves?|classes?|mes|nos|les|de|en) (?:sixiemes?|cinquiemes?|quatriemes?|troisiemes?|6e|5e|4e|3e)\b", q))
    if primaire and not secondaire_explicit:
        college = False
    if primaire and not any((pro, gt, college)):
        public = '1er degré'
    elif sum((pro, gt, college)) == 1 and not primaire:
        public = 'Lycée Pro / CAP' if pro else 'Lycée Général & Techno' if gt else 'Collège (DNB)'
    # Une question sur iPackEPS lui-même (version, interfaçage) reste dans iPackEPS même si elle cite Cyclades.
    if mode == 'ipack' and re.search(r"\bcyclades\b|\bsantorin\b", q) and not re.search(r"\bipack", q):
        mode = 'examens'
    # La décision réglementaire SHN est contrôlée par le circuit Examens.
    # Une manipulation explicite dans le logiciel conserve le circuit technique.
    if (mode == 'ipack' and re.search(r'\bshn\b|sportif de haut niveau', q)
            and re.search(r'noter|notation|droit|\b20\s*/\s*20|un seul cycle|une seule epreuve', q)
            and not re.search(r'saisir|saisie|menu|bouton|cliquer|enregistrer|declarer|\bipack', q)):
        mode = 'examens'
    return public, mode


def priority_context(question, public, mode):
    """Texte des fiches prioritaires que le hub transmet à l'IA pour cette question (même sélection que app.py :
    diplômes visés, reference_notice, filtre de mode, arrêt sur une fiche exclusive). Sert aux tests : vérifier
    ce que l'IA reçoit, maintenant que la plupart des réponses en dur sont redevenues des fiches."""
    niveau, mode = effective_context(question, public, mode)
    q = normalise(question)
    targets = set()
    if re.search(r"\bbac(calaureat)?s? ?pro\b|baccalaureat professionnel|\bbacs? professionnels?\b|\bbcp\b", q):
        targets.add('pro')
    if re.search(r'\bcap\b', q):
        targets.add('cap')
    if niveau == '1er degré':
        targets.add('primaire')
    elif re.search(r"\b(dnb|brevet|college|collegiens?)\b", q):
        targets.add('dnb')
    if re.search(r"bac(calaureat)? ?(general|techno|gt)\b|\blgt\b|voie (generale|techno)", q):
        targets.add('gt')
    if not targets:
        targets = {'Collège (DNB)': {'dnb'}, 'Lycée Général & Techno': {'gt'},
                   'Lycée Pro / CAP': {'pro', 'cap'}, '1er degré': {'primaire'}}.get(niveau, set())
    texts = []
    for path, md in reference_notice(targets, question, niveau):
        if md.get('modes') and mode not in md['modes']:
            continue
        if len(texts) >= 10:
            break
        texts.append(Path(path).read_text(encoding='utf-8'))
        if any(re.search(m, q) for m in md.get('exclusif_motifs', [])):
            break
    return '\n'.join(texts)


def delivered_text(question, public, mode):
    """Ce que le hub fournit pour cette question hors recherche par le sens : la réponse en dur si un garde-fou
    se déclenche, sinon le texte des fiches prioritaires transmis à l'IA."""
    niveau, m = effective_context(question, public, mode)
    direct = documented_response(question, niveau, m)[0]
    return direct or priority_context(question, public, mode)


def priority_titles(question, public, mode):
    """Titres des fiches prioritaires transmises à l'IA (même sélection que priority_context)."""
    niveau, m = effective_context(question, public, mode)
    direct, md = documented_response(question, niveau, m)
    if direct:
        return [md.get('title', '')]
    texte = priority_context(question, public, mode)
    titres = []
    for path, entry in catalog().items():
        if Path(path).is_file() and entry.get('title') and Path(path).read_text(encoding='utf-8') in texte:
            titres.append(entry['title'])
    return titres
