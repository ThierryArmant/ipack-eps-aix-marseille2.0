"""Parcours facultatifs iPackEPS, sans modèle et sans mémoire des réponses."""
from pathlib import Path
import re
from navigation_help import SOURCE
ROOT = Path(__file__).resolve().parent
MENU = ROOT / 'data/ipack/plan_des_menus_professeur_2026.txt'
COLLEGE = ROOT / 'config/guide_ipack_college.json'


def is_college(public):
    return str(public or '').startswith('Collège')


def college_routes():
    """Parcours collège relevés à l'écran ; une étape sans preuve dans sa fiche retire tout le parcours."""
    import json
    try:
        data = json.loads(COLLEGE.read_text(encoding='utf-8'))['parcours']
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


def college_menu(available):
    """Menu à deux niveaux qui suit les intitulés de l'écran iPackEPS ; entrées sans parcours valide retirées."""
    import json
    try:
        menu = json.loads(COLLEGE.read_text(encoding='utf-8')).get('menu', [])
    except (OSError, ValueError):
        return []
    out = []
    for block in menu:
        entries = [e for e in block.get('entrees', []) if e.get('parcours') in available]
        if entries:
            out.append({'rubrique': block['rubrique'], 'entrees': entries})
    return out


def render_guide(st, key, public):
    college = is_college(public) and college_routes()
    available = college or routes()
    if not available:
        st.info('Guide indisponible pour le moment.')
        return
    st.link_button('▶ Découvrir l’interface iPackEPS', 'https://ipackeps.ac-creteil.fr/spip.php?article34')
    rule = order_rule()
    if rule:
        st.info(rule)
    menu = college_menu(available) if college else []
    if menu:
        left, right = st.columns(2)
        names = [b['rubrique'] for b in menu]
        with left:
            rubrique = st.selectbox('Rubrique iPackEPS', names, index=None,
                                    placeholder='Choisissez un dossier…', key=key + '_rub')
        if rubrique not in names:
            return
        entries = menu[names.index(rubrique)]['entrees']
        if len(entries) == 1:
            goal = entries[0]['parcours']
        else:
            with right:
                choice = st.radio('Sous-menu', [e['libelle'] for e in entries], index=None,
                                  key=key + '_sub_' + str(names.index(rubrique)))
            if choice is None:
                return
            goal = next(e['parcours'] for e in entries if e['libelle'] == choice)
        first_rubrique = names[0]
    else:
        goal = st.radio('Que souhaitez-vous faire ?', list(available) + ['Je ne sais pas encore'], index=None, key=key + '_goal')
        if goal is None:
            return
        first_rubrique = None
    first = list(available)[0]
    if goal == 'Je ne sais pas encore' or goal not in available:
        goal = first
    route = available[goal]
    state_key = key + '_position_' + str(list(available).index(goal))
    position = min(st.session_state.get(state_key, 0), len(route) - 1)
    if college:
        label, url = route[position]['clic'], video_url(route[position].get('video'))
    else:
        text, path = route[position]
        label, url = step_presentation(goal, position, text)
    st.write(f'**Étape {position + 1}/{len(route)} · {label}**')
    if url:
        with st.expander('📺 Voir comment faire'):
            st.video(url)
    else:
        st.caption('Choisissez ensuite la rubrique qui vous intéresse dans la liste ci-dessus.')
    prefix = state_key + '_' + str(position)
    if position < len(route) - 1:
        if st.button('C’est fait · Suivant →', key=prefix + '_next'):
            st.session_state[state_key] = position + 1
            st.rerun()
    else:
        if st.button('✓ J’ai trouvé', key=prefix + '_done'):
            st.success('Vous pouvez fermer le guide ou choisir une autre rubrique.')
    if position > 0:
        if st.button('← Retour', key=prefix + '_back'):
            st.session_state[state_key] = position - 1
            st.rerun()
    def restart():
        st.session_state[key + '_position_' + str(list(available).index(first))] = 0
        if first_rubrique:
            st.session_state[key + '_rub'] = first_rubrique
        else:
            st.session_state[key + '_goal'] = first
    st.button('Je suis encore perdu(e) · Repartir du début', key=prefix + '_restart', on_click=restart)
