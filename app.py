import streamlit as st
import os
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# --- SECTION 0 : CHARGEMENT INVINCIBLE DES CONSIGNES DE PIERRE ---
@st.cache_resource
def charger_consignes_pierre():
    chemin = "gere_par_pierre.txt"
    if os.path.exists(chemin):
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                contenu = f.read()
            return [Document(text=contenu, metadata={"source": "Notes de Pierre"})]
        except Exception:
            return []
    return []

# ======================================================================
# 1. CONFIGURATION DE L'APPLICATION
# ======================================================================
st.set_page_config(page_title="Hub IA - EPS", layout="wide", initial_sidebar_state="collapsed")

# ======================================================================
# 2. GESTION MÉMOIRE ET COMPTEUR DE VISITES
# ======================================================================
if "messages_hub" not in st.session_state: st.session_state.messages_hub = []
if "active_module" not in st.session_state: st.session_state.active_module = "general"

def incrementer_et_obtenir_visites():
    fichier_compteur = "compteur_visites.txt"
    if not os.path.exists(fichier_compteur):
        try:
            with open(fichier_compteur, "w") as f: f.write("1")
            return 1
        except: return 1
    try:
        with open(fichier_compteur, "r") as f: valeur = int(f.read().strip())
        if "visite_comptabilisee" not in st.session_state:
            valeur += 1
            with open(fichier_compteur, "w") as f: f.write(str(valeur))
            st.session_state.visite_comptabilisee = True
        return valeur
    except: return 1

nb_visites_reel = incrementer_et_obtenir_visites()

# ======================================================================
# 3. INTERFACE GRAPHIQUE (CSS)
# ======================================================================
img_gauche, img_eps, img_droite, img_fond = "image_7.png", "image_6.png", "image_5.png", "image_8.png"
github_url = f"https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USERNAME')}/{st.secrets.get('GITHUB_REPO')}/main/"

st.markdown(f"""
    <style>
    /* Couleur de fond globale */
    .stApp {{ background-image: url('{github_url}{img_fond}') !important; background-size: cover !important; }}
    
    /* Couleur du texte principal et des cartes */
    .santorin-card, .general-card, .securite-card {{ 
        background-color: rgba(15, 23, 42, 0.45) !important; 
        color: #FFFFFF !important; 
        padding: 18px; 
        border-radius: 8px; 
    }}
    
    /* Couleur spécifique pour le texte dans les cartes */
    .santorin-card p, .general-card p, .securite-card p, 
    .santorin-card div, .general-card div, .securite-card div {{ 
        color: #FFFFFF !important; 
    }}
    
    /* Liens en orange */
    .santorin-card a, .general-card a, .securite-card a {{ 
        color: #FFB020 !important; 
        text-decoration: underline !important; 
    }}
    </style>
""", unsafe_allow_html=True)
# ======================================================================
# 4. CONFIGURATION IA ET BASES DE DOCUMENTS
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

@st.cache_resource
def initialiser_base_santorin():
    # Remplace ici tes documents réels dans la liste
    docs = [Document(text="Fiche Mémo - Correction Partagée Santorin...")]
    docs.extend(charger_consignes_pierre()) 
    return VectorStoreIndex.from_documents(docs).as_retriever(similarity_top_k=2)

@st.cache_resource
def initialiser_base_ipack():
    # Remplace ici tes documents réels dans la liste
    docs = [Document(text="Portail Pilote iPackEPS...")]
    docs.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs).as_retriever(similarity_top_k=2)

retriever_santorin = initialiser_base_santorin()
retriever_ipack = initialiser_base_ipack()
# ======================================================================
# 5. BANDEAU SUPERIEUR REHAUSSÉ AVEC VRAI COMPTEUR COMPLET
# ======================================================================
st.markdown(f"""
    <div class="hub-header">
        <div style="display: flex; align-items: center; width: 20%;">
            <img src="{github_url}{img_gauche}" height="60">
        </div>
        <div class="hub-title">
            <div class="title-row">
                <h1>HUB IA - EPS</h1>
                <span class="badge-visiteur">👁️ {nb_visites_reel}</span>
            </div>
            <p>ESPACE RESSOURCES &amp; ASSISTANCE NUMÉRIQUE</p>
        </div>
        <div style="display: flex; justify-content: flex-end; align-items: center; width: 25%; gap: 15px;">
            <img src="{github_url}{img_eps}" height="55">
            <img src="{github_url}{img_droite}" height="55">
        </div>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 6. EN-TÊTE DU TABLEAU DE BORD (AU-DESSUS DES BOUTONS)
# ======================================================================
label_titres = {
    "ipack": "🛠️ Mode Actif : Assistance Technique iPackEPS (Gestion du CCF & Inaptitudes)",
    "examens": "📊 Mode Actif : Réglementation Examens & Santorin (Copies Numérisées & Jurys)",
    "general": "🔍 Mode Actif : Questions Pédagogiques, Didactiques & Pratiques de Terrain",
    "securite": "🔒 Mode Actif : Sécurité & Responsabilité Juridique (Textes Officiels & Risques APPN)"
}

st.markdown(f"""
    <div class="column-title-top">
        <span class="instruction">⚙️ Choisissez le contexte de votre question ci-dessous</span>
        <span class="mode-actuel">{label_titres[st.session_state.active_module]}</span>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 7. BOUTONS DE CONTEXTE ALIGNÉS SUR 4 COLONNES
# ======================================================================
col_b1, col_b2, col_b3, col_b4 = st.columns(4, gap="small")

with col_b1:
    if st.button("🛠️ iPackEPS", use_container_width=True, key="btn_ip", type="primary" if st.session_state.active_module == "ipack" else "secondary"):
        st.session_state.active_module = "ipack"
        st.session_state.messages_hub = []
        st.rerun()

with col_b2:
    if st.button("📊 Examens & Santorin", use_container_width=True, key="btn_ex", type="primary" if st.session_state.active_module == "examens" else "secondary"):
        st.session_state.active_module = "examens"
        st.session_state.messages_hub = []
        st.rerun()

with col_b3:
    if st.button("🔍 Recherches Générales", use_container_width=True, key="btn_ge", type="primary" if st.session_state.active_module == "general" else "secondary"):
        st.session_state.active_module = "general"
        st.session_state.messages_hub = []
        st.rerun()

with col_b4:
    if st.button("🔒 Sécurité & Textes", use_container_width=True, key="btn_se", type="primary" if st.session_state.active_module == "securite" else "secondary"):
        st.session_state.active_module = "securite"
        st.session_state.messages_hub = []
        st.rerun()

# ======================================================================
# 7B. MESSAGES D'AVERTISSEMENT DYNAMIQUES (SOUS LES BOUTONS)
# ======================================================================
if st.session_state.active_module == "securite":
    message_alerte = """⚠️ <strong>Avis Institutionnel :</strong> Ce Hub est un outil d'aide réglementaire automatisé. En cas d'accident corporel grave avec mise en cause pénale directe, contactez immédiatement vos représentants syndicaux ou votre Autonomie de Solidarité Laïque (ASL) pour un accompagnement juridique humain dédié."""
elif st.session_state.active_module == "general":
    message_alerte = """💡 <strong>Exemples de recherches dans cet onglet :</strong> Projets pédagogiques innovants, fonctionnement de l'AS / UNSS, gestion de classe, aménagements d'épreuves, ressources par APSA, projets transversaux (SRE, Savoir Rouler, etc.).</em>"""
else:
    message_alerte = """⚠️ <strong>Conseil Flux Mixtes :</strong> Certaines questions touchent à la fois à la technique (iPackEPS) et à la réglementation (Santorin). N'hésitez pas à tester votre recherche dans ces deux onglets pour croiser les sources."""

st.markdown(f"""
    <div class="column-title-bottom">
        {message_alerte}
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 8. ZONE D'ACTION (NETTOYER + SAISIE)
# ======================================================================
col_action_clear, col_action_input = st.columns([1, 4.5], gap="small")

with col_action_clear:
    st.markdown('<div class="nettoyer-wrapper"></div>', unsafe_allow_html=True)
    if st.button("🧹 Nettoyer", key="clear_all"):
        st.session_state.messages_hub = []
        st.rerun()

with col_action_input:
    prompt = st.chat_input("Posez votre question institutionnelle, technique ou juridique ici...", key="chat_main")

# ======================================================================
# 9. FLUX DE MESSAGES ET TRAITEMENT IA (AVEC LES 4 FILTRES MÉTIERS STRICTS)
# ======================================================================
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        st.markdown(m["content"], unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": f"<span style='color: white; font-weight: normal;'>{prompt}</span>"})
    
    glossaire_loi = ["bo", "boen", "jo", "jorf", "journal officiel", "texte", "textes", "officiel", "officiels", "circulaire", "circulaires", "decret", "décret", "decrets", "décrets", "loi", "lois", "arrete", "arrêté", "arretes", "arrêtés", "reglementation", "réglementation", "jurisprudence", "responsabilite", "penal"]
    
    prompt_mots = prompt.lower().split()
    contient_terme_loi = any(mot in glossaire_loi for mot in prompt_mots) or "journal officiel" in prompt.lower()

    # Routage des bases de données et styles de cartes
    if st.session_state.active_module == "ipack":
        query_recherche = f"{prompt} iPackEPS"
        domaines_recherche = ["ipackeps.ac-creteil.fr", "eps.ac-creteil.fr", "eps.ac-normandie.fr", "eps.ac-versailles.fr"]
        texte_spinner = "Fouille de la base technique..."
        color_card = "general-card"
        badge_title = "🛠️ PROTOCOLE TECHNIQUE"
        instruction_date = "Pas de restriction de date pour le support technique."
    elif st.session_state.active_module == "examens":
        query_recherche = f"{prompt} examen EPS santorin"
        domaines_recherche = ["eduscol.education.gouv.fr", "pedagogie.ac-aix-marseille.fr", "eps.ac-creteil.fr", "siec.education.fr", "assistance.ac-noumea.nc"]
        texte_spinner = "Analyse réglementaire..."
        color_card = "santorin-card"
        badge_title = "📊 REGLEMENTATION & EXAMENS"
        instruction_date = "Exclus l'UNSS. Garde les textes de référence nationaux."
    elif st.session_state.active_module == "securite":
        query_recherche = f"{prompt} securite EPS responsabilite encadrement"
        domaines_recherche = ["eduscol.education.gouv.fr", "education.gouv.fr", "legifrance.gouv.fr", "eps.ac-creteil.fr"]
        texte_spinner = "Analyse juridique et sécuritaire..."
        color_card = "securite-card"
        badge_title = "🔒 SÉCURITÉ & PROTECTION JURIDIQUE"
        instruction_date = "Priorité absolue aux décrets et notes de service en vigueur. Filtre de date strict post-2020 sauf textes fondateurs du Code de l'éducation."
    else:
        query_recherche = prompt 
        domaines_recherche = ["eps.ac-aix-marseille.fr", "pedagogie.ac-aix-marseille.fr", "eduscol.education.gouv.fr", "eps.enseigne.ac-lyon.fr", "eps.ac-creteil.fr", "unss.org"]
        texte_spinner = "Recherche multi-académies & UNSS..."
        color_card = "general-card"
        badge_title = "🔍 RÉSULTATS DE RECHERCHE"
        
        if contient_terme_loi:
            instruction_date = "L'utilisateur recherche un texte officiel ou historique. LAISSE LES DATES LIBRES."
        else:
            instruction_date = "L'utilisateur pose une question de pratique courante, pédagogique ou liée à l'UNSS / AS. APPLIQUE UNE LIMITE STRICTE A 2020. Ignore l'ancien Lycée."

    with st.spinner(texte_spinner):
        extraits_doc = ""
        
        # Récupération Cache local
        if openai_api_key:
            try:
                if st.session_state.active_module == "examens":
                    noeuds_locaux = retriever_santorin.retrieve(prompt)
                    if noeuds_locaux:
                        extraits_doc += "--- DOCUMENTS DE RÉFÉRENCE INTERNES (SANTORIN) ---\n"
                        for n in noeuds_locaux:
                            extraits_doc += f"Source locale: {n.node.metadata.get('title')} ({n.node.metadata.get('url')})\nContenu: {n.node.text}\n\n"
                elif st.session_state.active_module == "ipack":
                    noeuds_locaux = retriever_ipack.retrieve(prompt)
                    if noeuds_locaux:
                        extraits_doc += "--- DOCUMENTS DE RÉFÉRENCE INTERNES (IPACKEPS) ---\n"
                        for n in noeuds_locaux:
                            extraits_doc += f"Source locale: {n.node.metadata.get('title')} ({n.node.metadata.get('url')})\nContenu: {n.node.text}\n\n"
            except:
                pass

        # Récupération Web Externe
        if tavily_api_key:
            try:
                payload = {
                    "api_key": tavily_api_key,
                    "query": query_recherche,
                    "search_depth": "advanced",
                    "include_domains": domaines_recherche
                }
                res = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
                if res.status_code == 200:
                    data_web = res.json()
                    if data_web.get("results"):
                        extraits_doc += "--- RÉSULTATS COMPLÉMENTAIRES DU WEB ---\n"
                        for item in data_web.get("results", []):
                            extraits_doc += f"Source: {item['title']} ({item['url']})\nContenu: {item['content']}\n\n"
            except: 
                pass

        # Injection des structures de prompts
        consigne_commune = f"""Analyse rigoureusement les documents et extraits du web mis à ta disposition ci-dessous :
        {extraits_doc}
        
        Réponds précisément à cette question : '{prompt}'.
        
        CRITÈRES DE FILTRAGE ET DE FORME IMPÉRATIFS : 
        1. Rédige une réponse claire, fluide, professionnelle et structurée.
        2. Tu devez OBLIGATOIREMENT lister l'intégralité des sources et documents officiels consultés à la toute fin de ta réponse sous forme de liens hypertextes cliquables au format Markdown exact : [Nom du document](URL). Si aucune source réelle n'est trouvée dans le contexte fourni pour étayer la réponse, NE CRÉE PAS de fausses sources ni de faux liens.
        3. Interdiction absolue d'inventer des URL, des circulaires, ou des numéros de décrets fictifs pour meubler. Si aucun texte précis n'est fourni, cite uniquement les grands Codes (Code de l'éducation, Code pénal) sans inventer de numéros de fiches ou de dates.
        4. GESTION DES DATES : {instruction_date}
        5. VERROU DISCIPLINAIRE STRICT (AVEC RELANCE DE SÉCURITÉ) : Tu es un outil EXCLUSIVEMENT dédié à l'Éducation Physique et Sportive (EPS). Si l'utilisateur nomme explicitement une autre matière scolaire ou discipline concurrente (ex: cours de Maths, exercice d'Électronique, devoir d'Histoire, Physique, SVT, Anglais), ou si sa formulation est ambiguë et te fait douter de son lien avec l'EPS, ne coupe pas brutalement la conversation. Réponds textuellement et poliment la phrase suivante, SANS RIEN RAJOUTER D'AUTRE : "Désolé, je suis un assistant exclusivement dédié à l'EPS et à ses outils spécifiques (iPackEPS, Santorin EPS). Votre demande semble sortir de ce cadre ou est un peu ambiguë. Pouvez-vous préciser votre pensée ou reformuler votre question en lien avec l'EPS ?"
        INTERDICTION ABSOLUE de déclencher ce verrou pour des termes de structure ou de gestion administrative du second degré comme "classe", "1ère", "Terminale", "Professionnelle", "Série", "Filière", "Générale", "Technologique" ou "Voie" : ces termes sont indispensables pour configurer les coefficients, les scolarités et les menus d'APSA pour l'épreuve d'EPS au Baccalauréat. Dans ce cas, traite la demande normalement comme une question EPS."""

        if st.session_state.active_module == "ipack":
            consigne_ia = f"""Tu es l'assistant technique absolu et l'expert référent de l'application institutionnelle iPackEPS (outil officiel de l'Éducation Nationale dédié à la gestion des évaluations, du CCF et des inaptitudes pour les enseignants d'Éducation Physique et Sportive - EPS). {consigne_commune}
            
            Tu devez STRICTEMENT appliquer et faire respecter les règles métiers, les verrous informatiques et les consignes de gradation de certitude adaptatives suivants :
            
            1. NATURE DE L'APPLICATION & FIN DES CONFUSIONS : iPackEPS est une application académique sécurisée pour les professeurs d'EPS. Ce n'est pas un service de livraison ni un système de certification informatique (SSL, Pix, etc.). Si l'utilisateur parle de "certificat" ou "certificat médical", il s'agit UNIQUEMENT de la justification médicale d'inaptitude (dispense de sport) d'un élève.
            
            2. INTERFACE & TÉLÉVERSEMENT DES CERTIFICATS MÉDICAUX : L'application possède un onglet dédié "Inaptitudes" permettant de piloter les dispenses (totales, partielles). Dans le tableau "Certificat Médical Inaptitude Permanente", il existe un bouton vert "Envoyer" permettant de téléverser et déposer directement le scan ou le fichier PDF du certificat médical de l'élève dans le système. La configuration générale s'effectue dans le menu 'Gestion/Suivi des élèves' > 'Fiche élève' > 'Saisir une inaptitude'. Ne prétends jamais que le dépôt de fichier PDF est impossible sur cette interface.
            
            3. RÈGLES DU CCF AU BACCALAURÉAT, PROTOCOLES & SOUVERAINETÉ : 
               - Pour valider le CCF en EPS, l'élève doit avoir au moins DEUX notes valides dans deux épreuves de familles d'activités différentes. S'il n'a qu'une seule note suite à une blessure, iPackEPS bloque le calcul automatique et le dossier va au Jury Académique via Cyclades. Une absence injustifiée donne 0/20 (comptabilisé), une inaptitude validée neutralise l'épreuve. Rappelle qu'on ne tape jamais "IN" ou "DI" à la main dans les notes brutes, c'est généré dynamiquement.
               - VERROU DE SOUVERAINETÉ JURIDIQUE : Le jury d'examen est seul souverain (Article L. 331-1 du Code de l'éducation). Toute demande de double correction, d'attribution d'un deuxième correcteur ou d'un deuxième évaluateur suite à la contestation d'un parent d'élève en CCF est juridiquement IRRECEVABLE. Il n'existe aucune procédure ou bouton informatique pour cela dans iPackEPS.
               - MODIFICATION DU PROTOCOLE D'ACTIVITÉS : Une fois le protocole d'établissement validé, il est informatiquement figé. Remplacer une activité par une autre (ex: Acrosport par de la Gymnastique) en cours d'année est une procédure administrative lourde iPackEPS qui nécessite obligatoirement l'intervention du coordonnateur EPS ou de l'inspection (IA-IPR) pour faire sauter le verrou académique. Il n'existe aucun bouton d'action autonome pour l'enseignant dans l'interface courante, et cela n'a strictement aucun rapport avec Santorin.
               - VERROU DE COMPÉTENCE SUR LES SECTIONS SPORTIVES SCOLAIRES (SSS) : L'ouverture, la fermeture ou la transformation d'une Section Sportive Scolaire (ex: transformer le Handball en Football) est une décision purement administrative et structurelle (Rectorat / Conseil d'Administration). Cela n'a STRICTEMENT aucun rapport avec l'application iPackEPS. Si l'utilisateur pose une question là-dessus, tu as l'interdiction absolue de décrire une manipulation ou une mise à jour dans iPackEPS (il n'y a aucune "fiche section" ou "bouton de création de section" dans l'interface prof). Tu dois uniquement renvoyer vers les démarches de l'établissement (CA) et du Rectorat, en appliquant la posture du Niveau 3.
               - VERROU GESTION DES ENSEIGNANTS / COMPTES PROF : L'ajout d'un nouveau professeur, la modification des profils ou des droits des enseignants ne se fait JAMAIS depuis l'interface iPackEPS Enseignant. Il n'existe aucun onglet "Gestion des utilisateurs" ou "Ajouter un professeur" pour l'enseignant. Ces données RH et de structure de service sont synchronisées automatiquement en amont par le secrétariat de direction via STSWeb. Renvoyer impérativement vers la direction de l'établissement.
            
            4. BOUTON 'CHANGEMENT D'ACTIVITÉ' GRISÉ : Si l'interface refuse de modifier l'activité ou l'option d'un élève pour le trimestre, c'est qu'une note existe déjà. Pour débloquer le bouton, l'enseignant doit aller dans 'Saisie des notes' de l'activité actuelle, effacer complètement la note (laisser la case vide, pas de zéro), puis enregistrer. Le bouton de modification dans la fiche élève redeviendra instantanément actif.
            
            5. LOGIQUE DE FORMULATION ET GRADATION DU TON (POSTURE SÉMANTIQUE NATURELLE) :
               Adapte la certitude de ton ton selon la nature de l'information, de manière fluide et naturelle, sans rabâcher de phrase pré-formatée automatique :
               
               - POSTURE TEXTES ET RÈGLES (Absolue) : Quand tu cites une règle administrative, nationale ou un texte officiel strict contenu dans tes fiches (ex: l'obligation des 2 notes de familles différentes au CCF, l'irrecevabilité d'une double correction parent, le blocage d'un protocole d'activités), sois direct, affirmatif et institutionnel. Affirme la règle immédiatement sans hésitation ni préambule.
               
               - POSTURE INTERFACE ET ÉCRAN (Prudente) : Quand tu décris une manipulation visuelle sur l'interface qui est bien documentée dans tes fiches (ex: bouton de changement d'activité grisé, onglet d'envoi de fichier), intègre des nuances de précaution naturelles dans le fil du texte (ex: "Dans une configuration standard...", "Généralement...", "Sous réserve des droits de votre session..."). Rappelle si nécessaire que la saisie brute collective des notes se fait via le menu global "Saisie des notes" par activité (et non pas individuellement élève par élève dans la fiche suivi, qui elle sert aux inaptitudes).
               
               - POSTURE INCONNU, PASSERELLES ET BUGS (Humble et Transparent - CRUCIAL) : Si la question porte sur un transfert d'élève complexe (ex: inter-académique, changement d'établissement en cours d'année), sur les structures de sections sportives (SSS), la création de profils profs, ou sur un code d'erreur/incident technique absent de tes textes (ex: Erreur 502, serveurs Cyclades vides, message de session "Une autre interface iPackEPS est déjà utilisée"), INTERDICTION ABSOLUE d'extrapoler, d'inventer des parcours de menus ou de créer de fausses fiches. Admets simplement de façon brève que cette procédure administrative ou technique dépasse les fiches de support enseignant iPackEPS et dépend de décisions académiques, du rectorat (Siècle/STSWeb) ou d'un nettoyage de cookies/cache du navigateur. Oriente proprement vers le correspondant iPack ou la direction.

            Rédige un guide ou tutoriel technique extrêmement rigoureux, structuré, adapté à ces postures et clair pour aider le collègue enseignant."""
        elif st.session_state.active_module == "examens":
            consigne_ia = f"Tu es l'assistant officiel examens et spécialiste de l'outil Santorin. {consigne_commune} Rédige une réponse réglementaire complète."
        elif st.session_state.active_module == "securite":
            consigne_ia = f"""Tu es l'assistant juridique suprême en Sécurité, Responsabilité et Droit de l'Éducation en EPS. {consigne_commune}
            
            Tu devez STRICTEMENT appliquer et faire respecter les verrous légaux et constitutionnels français suivants, même si les extraits du web se montrent imprécis :
            
            1. COUVERTURE ET SUBSTITUTION DE L'ÉTAT (LOI DE 1937) : Rappelle systématiquement qu'en cas d'accident scolaire (défaut de surveillance, blessure), la responsabilité civile de l'enseignant de l'enseignement public est COUVERTE par l'État. En vertu de l'article L. 911-4 du Code de l'éducation (loi du 5 avril 1937), l'État se substitue au membre de l'enseignement. L'enseignant bénéficie de droit de la Protection Fonctionnelle (loi du 13 juillet 1983) : l'institution prend en charge sa défense, sauf en cas de faute personnelle lourde détachable du service (ex: état d'ébriété, abandon volontaire de poste).
            
            2. CERTIFICAT MÉDICAL DES MINEURS : Depuis la loi du 7 décembre 2020 et son décret d'application de 2021, le certificat médical d'aptitude à la pratique sportive est PUREMENT ET SIMPLEMENT SUPPRIMÉ pour les mineurs en milieu scolaire. Les élèves sont légalement présumés aptes pour les cours obligatoires d'EPS. L'enseignant n'a ni le droit ni l'obligation d'exiger un certificat d'aptitude. C'est à la famille de fournir un certificat médical d'inaptitude s'il y a une contre-indication.
            
            3. LIBERTÉ PÉDAGOGIQUE ET PROJETS LOCAUX : L'enseignant d'EPS dispose de sa liberté pédagogique (Article L. 912-1 du Code de l'éducation). Il a parfaitement le droit d'introduire des formes de pratique modernes ou alternatives (comme le Parkour ou le Freerun) en tant que situations d'apprentissage au sein d'un cycle disciplinaire classique (comme la Gymnastique), dès lors que les exigences de sécurité et d'obligation de moyens (parade, tapis) sont respectées, même si le nom spécifique de cette variante n'est pas écrit textuellement dans le projet EPS de l'établissement.
            
            4. SÉCURITÉ SUR LE TERRAIN (MÉTHODE ET PLACEMENT) : L'enseignant est soumis à une obligation de moyens. Il commet une faute simple de surveillance s'il rompt délibérément le contrôle visuel direct de manière prolongée et non sécurisée. En cours obligatoire, il est réglementairement seul face à sa classe entière, sans quota d'adultes requis, y compris en extérieur.
            
            Rédige une analyse froide, protectrice mais lucide pour le collègue. Interdiction absolue d'inventer de faux numéros de décrets."""
        else:
            consigne_ia = f"""Tu es l'assistant de recherche globale en EPS, expert de la réglementation de l'Éducation Nationale et du fonctionnement associatif. {consigne_commune} 
            
            Tu devez STRICTEMENT respecter les règles métiers suivantes :
            1. PROGRAMMES LYCÉE (SECONDE/PREMIÈRE) : Il n'existe AUCUN barème national chiffré ou mathématique imposé par le ministère pour les classes de Seconde et Première. L'évaluation est exclusivement LOCALE (projet EPS). Ne confonds pas avec le Collège (Cycle 4).
            2. CONTESTATION DE NOTE ET SOUVERAINETÉ : En CCF (Baccalauréat), c'est le Jury Académique, présidé par le Recteur, qui est constitutionnellement seul souverain pour arrêter la note définitive (Article L. 331-1 du Code de l'éducation). Une demande de double correction par un parent d'élève est juridiquement irrecevable.
            3. VERROU DE COMPÉTENCE SUR LES SECTIONS SPORTIVES SCOLAIRES (SSS) : Tout projet d'ouverture, de fermeture ou de bascule de discipline d'une section sportive relève de choix de carte scolaire rectorale et du Conseil d'Administration de l'établissement. Ce n'est pas une question d'outils d'évaluation ou d'application iPackEPS. Invite immédiatement l'utilisateur à se tourner vers le chef d'établissement et le calendrier de campagne du rectorat sans broder de manipulation technique fictive."""

        response_web = Settings.llm.complete(consigne_ia)
        
        formatted_answer = f"""
        <div class="{color_card}">
            <strong>{badge_title} :</strong><br><br>
            <div style="color: #FFFFFF !important; font-weight: 400 !important; font-family: sans-serif;">
                {response_web.text}
            </div>
        </div>
        """

    st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
    st.rerun()
