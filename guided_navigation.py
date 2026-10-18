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


def render_guide(st, key, public):
    available = routes()
    if not available or any(not p.is_file() for route in available.values() for _, p in route):
        st.info('Le parcours documenté est indisponible. Précisez le titre de votre écran dans votre question.')
        return
    st.caption('Version de test · iPackEPS uniquement · aucun appel à l’IA pour les choix et les étapes')
    goal = st.radio('Que souhaitez-vous faire ?', list(available) + ['Je ne sais pas encore'],
                    index=None, key=key + '_goal')
    if goal is None:
        return
    if goal == 'Je ne sais pas encore':
        st.info('Vous pouvez choisir « Me repérer depuis le début ». Sinon, décrivez le résultat souhaité et les mots visibles à l’écran ; il n’est pas nécessaire de connaître le nom du module.')
        return
    route = available[goal]
    state_key = key + '_position_' + str(list(available).index(goal))
    position = st.session_state.get(state_key, 0)
    text, path = route[position]
    st.write(f'**Étape {position + 1} sur {len(route)}**')
    st.info(text)
    st.caption('Si cette étape est déjà réalisée, passez à la suivante sans recommencer les saisies.')
    prefix = state_key + '_' + str(position)
    status = st.radio('Où en êtes-vous maintenant ?', ['C’est fait', 'Je ne trouve pas cet écran', 'Je bloque dans cet écran'],
                      index=None, key=prefix + '_status')
    if status in ('Je ne trouve pas cet écran', 'Je bloque dans cet écran'):
        st.write('Précisez votre blocage en quelques mots :')
        detail = st.text_input('Titre, bouton introuvable ou message affiché (sans données personnelles)', key=prefix + '_detail')
        question = f'Dans iPackEPS ({public}), je souhaite : {goal.lower()}. Étape concernée : {text} Mon problème : {status.lower()}. {detail}'.strip()
        st.code(question, language=None)
        st.caption('Copiez cette demande puis cliquez sur « Poser une autre question ». Le guide ne lance aucune réponse automatiquement.')
    if status == 'C’est fait' and position < len(route) - 1:
        if st.button('Étape suivante →', key=prefix + '_next'):
            st.session_state[state_key] = position + 1
            st.rerun()
    if position > 0:
        if st.button('← Étape précédente', key=prefix + '_back'):
            st.session_state[state_key] = position - 1
            st.rerun()
    if status == 'C’est fait' and position == len(route) - 1:
        result = st.radio('Avez-vous trouvé ce que vous cherchiez ?', ['Oui', 'Non, j’ai encore besoin d’aide'], index=None, key=prefix + '_result')
        if result == 'Oui':
            st.success('Parcours terminé. Vous pouvez fermer cette aide.')
        elif result:
            st.info('Cette version du guide s’arrête au dernier écran documenté. Pour continuer, précisez le champ ou le bouton qui vous bloque ; aucune étape supplémentaire ne sera inventée.')
            detail = st.text_input('Que voyez-vous, et que souhaitez-vous obtenir ? (sans données personnelles)', key=prefix + '_end_detail')
            st.code(f'Dans iPackEPS ({public}), je souhaite : {goal.lower()}. J’ai suivi le parcours jusqu’à : {text} Je bloque ensuite : {detail}', language=None)
            st.caption('Copiez cette demande et cliquez sur « Poser une autre question ».')
    with st.expander('Source de cette étape'):
        st.write(path.read_text(encoding='utf-8').splitlines()[0].lstrip('# '))
        st.caption('Documentation du logiciel. Les dates et les circuits académiques restent à vérifier lorsqu’ils interviennent dans votre démarche.')
