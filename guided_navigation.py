"""Parcours facultatifs iPackEPS, sans modèle et sans mémoire des réponses."""
from pathlib import Path
import re
from navigation_help import SOURCE
ROOT = Path(__file__).resolve().parent
MENU = ROOT / 'data/ipack/plan_des_menus_professeur_2026.txt'
COLLEGE = ROOT / 'config/guide_ipack_college.json'
LYCEE_GT = ROOT / 'config/guide_ipack_lycee_gt.json'
LYCEE_PRO = ROOT / 'config/guide_ipack_lycee_pro.json'
EXAMENS_LYCEE = ROOT / 'config/guide_examens_lycee.json'
DECLENCHEURS = ROOT / 'config/guide_declencheurs.json'


def guide_file(public, mode=None):
    """Guide à menu relevé à l'écran : collège, lycée général et technologique ; sinon parcours simples.
    Onglet Examens (lycée) : les 3 phases et 11 étapes de l'examen, iPackEPS, Cyclades et Santorin."""
    public = str(public or '')
    if mode == 'examens':
        lycee = ('Lycée voie générale', 'Lycée Général & Techno', 'Lycée voie professionnelle', 'Lycée Pro / CAP')
        return EXAMENS_LYCEE if public in lycee else None
    if public.startswith('Collège'):
        return COLLEGE
    if public in ('Lycée voie générale', 'Lycée Général & Techno'):
        return LYCEE_GT
    if public in ('Lycée voie professionnelle', 'Lycée Pro / CAP'):
        return LYCEE_PRO
    return None


def is_college(public):
    return str(public or '').startswith('Collège')


def college_routes(path=None):
    """Parcours relevés à l'écran ; une étape sans preuve dans sa fiche retire tout le parcours."""
    import json
    try:
        data = json.loads((path or COLLEGE).read_text(encoding='utf-8'))['parcours']
    except (OSError, ValueError, KeyError):
        return {}
    valid = {}
    for goal, steps in data.items():
        ok = bool(steps)
        for step in steps:
            path = ROOT / step.get('source', '')
            try:
                ok = ok and bool(step.get('clic')) and step.get('preuve', '') != '' and step['preuve'] in path.read_text(encoding='utf-8')
            except OSError:
                ok = False
        if ok:
            valid[goal] = steps
    return valid


def documented_steps():
    try:
        lines = SOURCE.read_text(encoding='utf-8').splitlines()
    except OSError:
        return [], ''
    line = next((x for x in lines if x.startswith('Ordre à suivre depuis le tableau de bord : ')), '')
    steps = re.findall(r'(?:^|; )\d\) (.*?)(?=; \d\)|$)', line.partition(': ')[2])
    source = next((x for x in lines if x.startswith('Source : ')), '')
    return (steps, source) if len(steps) == 3 and source else ([], '')


def routes():
    """Chaque instruction est attachée à son document ; pas de FAQ mixte injectée."""
    steps, source = documented_steps()
    if not steps or not MENU.is_file():
        return {}
    menus = MENU.read_text(encoding='utf-8')
    if not all(x in menus for x in ('[Créer un groupe]', '[Gérer les S.A.]', 'Configuration des Classes')):
        return {}
    base = '[Tableau de bord] > [Les Dossiers et Projets] > [Dossier EPS]'
    return {
        'Me repérer depuis le début': [(s, SOURCE) for s in steps],
        'Renseigner une activité avec une classe ou un groupe': [
            (base + ' > [Groupes] : repérez votre classe ou le groupe concerné. Les classes sont déjà configurées ; ne créez pas un doublon.', MENU),
            ('Dans [Groupes], utilisez [Gérer les S.A.] pour accéder aux séquences d’apprentissage du groupe concerné. Repérez la séquence et l’activité que vous souhaitez renseigner.', MENU),
        ],
        'Configurer les classes ou importer les élèves': [
            (base + ' > [Classes] > [Configuration des Classes]. Si cette configuration existe déjà, passez à la suite.', MENU),
            ('Dans [Classes], poursuivez par [Organisation des Classes]. Si cette étape est déjà réalisée, passez à la suite.', MENU),
            ('Dans [Classes], ouvrez [Importation des Élèves]. Pour une liste déjà importée à mettre à jour, le bouton documenté est [Actualiser].', ROOT / 'data/ipack/fiches/ipack_065_article_18_dossiers_dossiereps_eleves_placement_des_eleves_dans_les_groupes.txt'),
        ],
        'Trouver les activités de l’établissement': [(base + ' > [APSA]. Choisissez la liste correspondant à votre public. Cette rubrique est distincte de vos spécialités sportives personnelles.', MENU)],
        'Configurer les périodes': [(base + ' > [Périodes] : le bouton du menu est [Créer une nouvelle Période]. Si vos périodes sont déjà définies, ne les recréez pas.', MENU)],
        'Placer des élèves dans un groupe': [(base + ' > [Élèves] : ouvrez le placement des élèves dans les groupes. Repérez la classe et le groupe de destination.', MENU)],
        'Retrouver un projet ou son bilan': [(base + ' > [Projets]. Choisissez le projet concerné : Projet Établissement, Projet EPS, Projet AS ou Projet SSS.', MENU)],
    }


def step_presentation(goal, position, text):
    """Libellés courts et vidéos explicitement associées, sans recherche IA."""
    import json
    labels = {
        'Me repérer depuis le début': [('Établissement', '1. Saisie établissement'), ('Ma fiche Professeur', '2. Ma fiche Professeur'), ('Dossier EPS', None)],
        'Renseigner une activité avec une classe ou un groupe': [('Dossier EPS → Groupes', '3.1 Dossier EPS — Groupes'), ('Groupes → Gérer les S.A.', '3.1 Dossier EPS — Groupes')],
        'Configurer les classes ou importer les élèves': [('Classes → Configuration', '3.1 Dossier EPS — Classes'), ('Classes → Organisation', '3.1 Dossier EPS — Classes'), ('Classes → Importation des élèves', '3.1 Dossier EPS — Classes')],
        'Trouver les activités de l’établissement': [('Dossier EPS → APSA', '3.1 Dossier EPS — APSA')],
        'Configurer les périodes': [('Dossier EPS → Périodes', '3.1 Dossier EPS — Périodes')],
        'Placer des élèves dans un groupe': [('Dossier EPS → Élèves', '3.1 Dossier EPS — Élèves')],
        'Retrouver un projet ou son bilan': [('Dossier EPS → Projets', '3.1 Dossier EPS — Les axes du projet')],
    }
    label, video_key = labels[goal][position]
    try:
        videos = json.loads((ROOT / 'config/tutoriels_parcours_college.json').read_text(encoding='utf-8'))['tutoriels']
    except (OSError, ValueError, KeyError):
        videos = []
    url = next((v['url'] for v in videos if v.get('etape') == video_key), '')
    return label, url


def video_url(video_key):
    import json
    if not video_key:
        return ''
    if str(video_key).startswith('https://'):
        return video_key
    try:
        videos = json.loads((ROOT / 'config/tutoriels_parcours_college.json').read_text(encoding='utf-8'))['tutoriels']
    except (OSError, ValueError, KeyError):
        return ''
    return next((v['url'] for v in videos if v.get('etape') == video_key), '')


ORDER_RULE = ('**Bon à savoir : iPackEPS se remplit dans l’ordre.** '
              'D’abord [Établissement], puis [Ma Fiche Professeur], puis [Dossier EPS] ; '
              'dans chaque écran, de gauche à droite et de haut en bas. '
              'Une étape sautée bloque les suivantes : complétez-la avant d’avancer, '
              'vous éviterez des allers-retours.')


def order_rule():
    """Affichée seulement si la fiche validée par le correspondant porte toujours cette règle."""
    try:
        text = SOURCE.read_text(encoding='utf-8')
    except OSError:
        return ''
    return ORDER_RULE if 'dans l\'ordre, de gauche à droite et de haut en bas' in text else ''


def college_menu(available, path=None):
    """Menu à deux niveaux qui suit les intitulés de l'écran iPackEPS ; entrées sans parcours valide retirées."""
    import json
    try:
        menu = json.loads((path or COLLEGE).read_text(encoding='utf-8')).get('menu', [])
    except (OSError, ValueError):
        return []
    out = []
    for block in menu:
        entries = [e for e in block.get('entrees', []) if e.get('parcours') in available]
        if entries:
            out.append({'rubrique': block['rubrique'], 'entrees': entries})
    return out


def prerequisite_text(rubrique, entry):
    """« Avant [Projets], vous devez avoir complété… » : remplace le rappel général d'ordre."""
    items = entry.get('prerequis') or []
    if not items:
        return ''
    if entry.get('cible'):
        target = entry['cible']
    elif rubrique == 'Dossier EPS':
        target = '[' + entry['libelle'].split(' : ')[0].split(' · ')[0] + ']'
    else:
        target = '[' + rubrique + ']'
    return 'Avant ' + target + ', vous devez avoir complété : ' + ' → '.join(items) + '.'


def _normalise(text):
    import unicodedata
    text = str(text or '').lower().replace('\u2019', "'").replace('`', "'")
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def suggested_entries(question, public, mode=None, limit=2, path=None):
    """Parcours du guide qui correspondent aux mots de la question (config/guide_declencheurs.json).
    Renvoie [(rubrique, entrée)] les mieux notés, au plus `limit` ; liste vide si rien ne correspond.
    Le collègue n'a pas à connaître le module : la question mène au parcours, le menu reste en recours."""
    import json
    guide = guide_file(public, mode)
    if not guide or not question:
        return []
    try:
        config = json.loads((path or DECLENCHEURS).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    q = _normalise(question)
    apsa = config.get('apsa', '')
    menu = college_menu(college_routes(guide), guide)
    scored = []
    for block in menu:
        for entry in block['entrees']:
            score = 0
            for pattern in config.get('parcours', {}).get(entry['parcours'], []):
                pattern = apsa if pattern == '@apsa' else pattern
                try:
                    score += bool(pattern and re.search(pattern, q))
                except re.error:
                    pass
            if score:
                scored.append((score, block['rubrique'], entry))
    if not scored:
        return []
    best = max(s for s, _, _ in scored)
    seen, out = set(), []
    for score, rubrique, entry in sorted(scored, key=lambda x: -x[0]):
        if score == best and entry['parcours'] not in seen:
            seen.add(entry['parcours'])
            out.append((rubrique, entry))
    return out[:limit]


def render_guide(st, key, public, on_done=None, mode=None, question=None):
    path = guide_file(public, mode)
    college = bool(path) and college_routes(path)
    available = college or ([] if mode == 'examens' else routes())
    if not available:
        st.info('Guide indisponible pour le moment.')
        return
    menu = college_menu(available, path) if college else []
    suggestions = suggested_entries(question, public, mode) if menu else []
    picked = None
    if suggestions:
        autre = 'Autre chose : voir tout le menu'
        st.markdown('**Le parcours qui correspond à votre question :**')
        choice = st.radio('Parcours proposé', [e['libelle'] for _, e in suggestions] + [autre],
                          index=0, key=key + '_suggestion', label_visibility='collapsed')
        picked = next(((r, e) for r, e in suggestions if e['libelle'] == choice), None)
    if picked:
        rubrique, entry = picked
        goal = entry['parcours']
        before = prerequisite_text(rubrique, entry)
        explication = entry.get('explication', '')
    elif menu:
        left, right = st.columns(2)
        names = [b['rubrique'] for b in menu]
        with left:
            rubrique = st.selectbox('Rubrique iPackEPS', names, index=None, label_visibility='collapsed',
                                    placeholder='Choisissez une phase…' if mode == 'examens' else 'Choisissez un dossier…', key=key + '_rub')
        if rubrique not in names:
            return
        entries = menu[names.index(rubrique)]['entrees']
        if len(entries) == 1:
            entry = entries[0]
        else:
            with right:
                choice = st.radio('Sous-menu', [e['libelle'] for e in entries], index=None,
                                  key=key + '_sub_' + str(names.index(rubrique)), label_visibility='collapsed')
            if choice is None:
                return
            entry = next(e for e in entries if e['libelle'] == choice)
        goal = entry['parcours']
        before = prerequisite_text(rubrique, entry)
        explication = entry.get('explication', '')
    else:
        before = ''
        explication = ''
        goal = st.radio('Que souhaitez-vous faire ?', list(available) + ['Je ne sais pas encore'], index=None, key=key + '_goal')
        if goal is None:
            return
    first = list(available)[0]
    if goal == 'Je ne sais pas encore' or goal not in available:
        goal = first
    route = available[goal]
    state_key = key + '_parcours_' + str(list(available).index(goal))
    if before:
        st.info(before)
    # Toutes les étapes d'un coup (pas de bouton « Suivant ») ; chaque vidéo n'est proposée qu'une fois.
    deja = set()
    for position, step in enumerate(route):
        if college:
            label, url = step['clic'], video_url(step.get('video'))
        else:
            text, path = step
            label, url = step_presentation(goal, position, text)
        prefix = state_key + '_' + str(position)
        if url and url not in deja:
            deja.add(url)
            show = prefix + '_show_video'
            def toggle(show=show):
                st.session_state[show] = not st.session_state.get(show, False)
            st.button(f'▶ {position + 1}. {label} · Lancer le tutoriel vidéo', key=prefix + '_video',
                      on_click=toggle, use_container_width=True)
            if st.session_state.get(show, False):
                st.video(url)
        else:
            st.write(f'**{position + 1}. {label}**')
    if explication:
        # Les mêmes étapes en phrases complètes, pour qui ne connaît pas encore les écrans.
        st.markdown('**En phrases :** ' + explication)
    if not college:
        rule = order_rule()
        if rule:
            st.info(rule)
    def done():
        # Le guide se referme et repart de zéro ; retour au champ « Posez votre question ».
        for k in [k for k in st.session_state if str(k).startswith(key + '_')]:
            del st.session_state[k]
        if on_done:
            on_done()
    st.button('✓ J’ai trouvé', key=state_key + '_done', on_click=done)
