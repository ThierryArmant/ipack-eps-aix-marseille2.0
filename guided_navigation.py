"""Parcours facultatifs iPackEPS, sans modèle et sans mémoire des réponses."""
from pathlib import Path
import re
from navigation_help import SOURCE
ROOT = Path(__file__).resolve().parent
MENU = ROOT / 'data/ipack/plan_des_menus_professeur_2026.txt'


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


def render_guide(st, key, public):
    available = routes()
    if not available:
        st.info('Guide indisponible pour le moment.')
        return
    st.link_button('▶ Découvrir l’interface iPackEPS', 'https://ipackeps.ac-creteil.fr/spip.php?article34')
    goal = st.radio('Que souhaitez-vous faire ?', list(available) + ['Je ne sais pas encore'], index=None, key=key + '_goal')
    if goal is None:
        return
    if goal == 'Je ne sais pas encore':
        goal = 'Me repérer depuis le début'
    route = available[goal]
    state_key = key + '_position_' + str(list(available).index(goal))
    position = st.session_state.get(state_key, 0)
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
        st.session_state[key + '_position_0'] = 0
        st.session_state[key + '_goal'] = 'Me repérer depuis le début'
    st.button('Je suis encore perdu · Repartir du début', key=prefix + '_restart', on_click=restart)
