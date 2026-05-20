import streamlit as st
import os
import pandas as pd
import requests
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.memory import ChatMemoryBuffer

# ======================================================================
# 1. CONFIGURATION DE L'APPLICATION (IMPÉRATIVEMENT EN PREMIER)
# ======================================================================
st.set_page_config(
    page_title="Hub IA - EPS", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ======================================================================
# 2. GESTION DE LA MÉMOIRE ET DU COMPTEUR DE VISITES FIABLE (PROTÉGÉ)
# ======================================================================
if "messages_hub" not in st.session_state:
    st.session_state.messages_hub = []
if "active_module" not in st.session_state:
    st.session_state.active_module = "general"  

def incrementer_et_obtenir_visites():
    fichier_compteur = "compteur_visites.txt"
    if not os.path.exists(fichier_compteur):
        try:
            with open(fichier_compteur, "w") as f:
                f.write("1")
            return 1
        except:
            return 1
    
    try:
        with open(fichier_compteur, "r") as f:
            valeur = int(f.read().strip())
        
        # On incrémente uniquement au premier chargement de la session utilisateur
        if "visite_comptabilisee" not in st.session_state:
            valeur += 1
            with open(fichier_compteur, "w") as f:
                f.write(str(valeur))
            st.session_state.visite_comptabilisee = True
            
        return valeur
    except:
        return 1

# Récupération du score réel sans risque de plantage
nb_visites_reel = incrementer_et_obtenir_visites()

# ======================================================================
# 3. INTERFACE GRAPHIQUE ET CONFIGURATION DES LIENS IMAGES
# ======================================================================
img_gauche = "image_7.png"
img_eps = "image_6.png" 
img_droite = "image_5.png"
img_fond = "image_8.png"

github_url = f"https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USERNAME')}/{st.secrets.get('GITHUB_REPO')}/main/"

st.markdown(f"""
    <style>
    .block-container {{ 
        padding-top: 0.5rem !important; 
        padding-bottom: 2rem !important; 
        padding-left: 1.5rem !important; 
        padding-right: 1.5rem !important; 
        max-width: 920px !important; 
    }}
    
    .stApp {{ background-image: url('{github_url}{img_fond}') !important; background-size: cover !important; background-attachment: fixed !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    
    /* Structure du Bandeau Supérieur Principal Réorganisé et Optimisé */
    .hub-header {{ 
        background-color: #1E293B; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 10px 20px; 
        height: 85px !important; 
        margin-bottom: 15px !important; 
        border-radius: 8px; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3); 
    }}
    
    /* Bloc titre équilibré avec décalage de sécurité pour éviter le collage à droite */
    .hub-title {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        flex-grow: 1;
        padding-right: 35px; 
    }}
    
    /* Ligne du titre principal */
    .title-row {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
    }}
    
    .hub-title h1 {{ 
        color: white !important; 
        margin: 0 !important; 
        font-size: 28px !important; 
        font-weight: 800 !important; 
        line-height: 1.2 !important;
        letter-spacing: 0.5px;
    }}
    
    /* Badge vert émeraude agrandi et bien visible */
    .badge-visiteur {{ 
        background-color: rgba(16, 185, 129, 0.2) !important; 
        color: #10B981 !important; 
        border: 1px solid rgba(16, 185, 129, 0.45) !important; 
        padding: 3px 12px !important; 
        border-radius: 20px !important; 
        font-size: 13px !important; 
        font-weight: 800 !important; 
        font-family: monospace !important;
        line-height: 1 !important;
        display: inline-block;
        box-shadow: 0px 0px 8px rgba(16, 185, 129, 0.2);
    }}
    
    /* Sous-titre remonté, mis en gras et calé */
    .hub-title p {{ 
        color: #94A3B8 !important; 
        margin: 0 !important;
        margin-top: -1px !important; 
        font-size: 13px !important; 
        text-transform: uppercase; 
        font-weight: bold !important;
        line-height: 1.1 !important; 
        letter-spacing: 0.5px;
    }}
    
    /* Encadré Sélection du Contexte */
    .context-container {{
        background-color: rgba(30, 41, 59, 0.5) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        padding: 14px 18px 18px 18px !important; 
        border-radius: 12px !important;
        margin-bottom: 18px !important;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.4);
    }}

    /* Barre Bleue Centrale */
    .column-title {{ 
        color: #FFFFFF; 
        text-align: center; 
        margin-bottom: 15px !important; 
        background-color: #1E293B; 
        border-radius: 6px !important; 
        padding: 8px 10px; 
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
        line-height: 1.4;
    }}
    .column-title .instruction {{
        font-size: 11px !important;
        font-weight: 500;
        text-transform: uppercase;
        color: #94A3B8 !important;
        letter-spacing: 0.5px;
        display: block;
        margin-bottom: 2px;
    }}
    .column-title .mode-actuel {{
        font-size: 14px !important; 
        font-weight: 700;
        color: #FFFFFF !important;
        display: block;
    }}
    
    /* Boutons Inactifs */
    button[kind="secondary"] {{ 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        color: #94A3B8 !important; 
        border: 1px solid rgba(255,255,255,0.05) !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
        padding: 12px 10px !important;
        transition: all 0.3s ease;
    }}

    /* Boutons Actifs */
    button[kind="primary"] {{
        background-color: rgba(16, 185, 129, 0.85) !important;
        color: #FFFFFF !important;
        border: 1px solid #10B981 !important;
        border-radius: 8px !important; 
        font-size: 13px !important; 
        padding: 12px 10px !important;
        box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.6) !important;
        font-weight: 700 !important;
    }}
    
    /* BOUTON NETTOYER */
    div.element-container:has(.nettoyer-wrapper) + div.element-container button {{
        background-color: rgba(220, 38, 38, 0.45) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(220, 38, 38, 0.6) !important;
        border-radius: 8px !important;
        padding: 7px 10px !important;
        width: 100% !important;
    }}
    div.element-container:has(.nettoyer-wrapper) + div.element-container button:hover {{
        background-color: rgba(220, 38, 38, 0.65) !important;
    }}
    
    /* CARTES DE RÉPONSE */
    .santorin-card, .general-card {{ 
        background-color: rgba(15, 23, 42, 0.45) !important; 
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 18px; 
        border-radius: 8px; 
        margin-bottom: 16px; 
        box-shadow: 0px 6px 20px rgba(0,0,0,0.5);
    }}
    .santorin-card {{ border-left: 6px solid #38BDF8 !important; }} 
    .general-card {{ border-left: 6px solid #10B981 !important; }} 
    
    .santorin-card p, .general-card p, .santorin-card div, .general-card div, .santorin-card span, .general-card span, .santorin-card li, .general-card li {{ 
        color: #FFFFFF !important; 
        font-size: 15px !important; 
        line-height: 1.6 !important; 
        font-weight: 400 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }}
    .santorin-card strong, .general-card strong {{
        font-weight: 700 !important; 
        color: #FFFFFF !important;
    }}

    .santorin-card a, .general-card a, .santorin-card a *, .general-card a * {{
        color: #FFB020 !important; 
        text-decoration: underline !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.9) !important;
    }}
    .santorin-card a:hover, .general-card a:hover {{
        color: #FCD34D !important;
    }}
    
    /* Bulle Utilisateur */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {{ 
        background-color: rgba(255, 255, 255, 0.15) !important; 
        backdrop-filter: blur(6px) !important;
        border-radius: 14px 14px 0px 14px !important; 
        margin-left: 15% !important; 
    }}
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] {{ display: none !important; }}
    </style>
""", unsafe_allow_html=True)

# ======================================================================
# 4. CONFIGURATION DE L'INTELLIGENCE ARTIFICIELLE & DES BASES DE DOCUMENTS
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

# BASE DE CONNAISSANCES FIXE : EXAMENS & SANTORIN
@st.cache_resource
def initialiser_base_santorin():
    docs_santorin = [
        Document(
            text="""Fiche Mémo - Correction Partagée Santorin (DEC / Assistance). 
            La correction partagée ou multiple permet à plusieurs évaluateurs/correcteurs d'intervenir sur un même lot de copies. 
            Dans Santorin, un chef d'établissement peut ajouter manuellement un deuxième évaluateur ou correcteur à un lot via le portail Arena / Cyclades. 
            Procédure : Aller dans l'onglet 'Lots', cliquer sur 'Voir le détail', aller sur l'onglet 'Correcteurs' puis cliquer sur le bouton 'Ajouter'.
            Verrouillage : Lorsqu'un correcteur édite une copie, l'autre bascule temporairement en lecture seule.""",
            metadata={"title": "Fiche Mémo - Correction Partagée Santorin", "url": "https://assistance.ac-noumea.nc/IMG/pdf/fm_correction_partagee.pdf"}
        ),
        Document(
            text="""Fiche Mémo - Processus de Distribution de Lots Santorin en Établissement. 
            Gestion, paramétrage des tailles de groupes et distribution automatique ou manuelle des lots de copies numérisées vers les correcteurs par les coordonnateurs de l'établissement.""",
            metadata={"title": "Fiche Mémo - Processus de Distribution de Lots", "url": "https://assistance.ac-noumea.nc/IMG/pdf/fic18-fichememo-etablissement-distribuer.pdf"}
        ),
        Document(
            text="""Guide Utilisateur Santorin - Ouvrir, annoter et corriger une copie numérisée. 
            Tutoriel pas-à-pas : liste des candidats anonymisés, outils d'annotation intégrés (surlignage, stylo, commentaires), saisie des notes par question ou globale, validation du lot. Utilisation de la messagerie interne (icône enveloppe) pour contacter les coordonnateurs.""",
            metadata={"title": "Guide Utilisateur - Ouvrir et corriger une copie avec Santorin", "url": "https://pedagogie.ac-orleans-tours.fr/documents/pdf/lettres_tutoriels_ouvrir_et_corriger_une_copie_avec_santorin__2_.pdf"}
        ),
        Document(
            text="""Portail d'assistance et ressources Dématérialisation Académie de Bordeaux. 
            Accès à la Base École de Santorin (environnement de test/formation), fiches d'aide à la connexion, procédures d'urgence en cas de page manquante ou copie mal numérisée.""",
            metadata={"title": "Portail Dématérialisation - Académie de Bordeaux", "url": "https://www.ac-bordeaux.fr/dematerialisation-126581"}
        ),
        Document(
            text="""Espace d'aide et tutoriels Santorin - Académie de Lille. 
            Guides d'utilisation pour le DNB, le Baccalauréat et les BTS. Procédures pour s'enregistrer, traiter les lots et demander des corrections d'affectation via l'enveloppe de communication.""",
            metadata={"title": "Espace d'Aide Santorin - Académie de Lille", "url": "https://pedagogie.ac-lille.fr/lettres/aide-santorin/"}
        ),
        Document(
            text="""Guide technique d'installation de Santorin Scan. 
            Documentation sur l'installation, le paramétrage des scanners physiques en établissement, les protocoles réseaux et la configuration des serveurs d'échange sécurisés.""",
            metadata={"title": "Guide d'Installation Santorin Scan", "url": "https://www.toutatice.fr/toutatice-portail-cms-nuxeo/binary/Guide_Installation+scanner_v2.0.4.pdf"}
        )
    ]
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=2)

# BASE DE CONNAISSANCES FIXE : IPACKEPS (TOTALEMENT SÉCURISÉE AVEC LES CAS COMPLEXES)
@st.cache_resource
def initialiser_base_ipack():
    docs_ipack = [
        Document(
            text="""Portail Pilote iPackEPS - Académie de Créteil. 
            iPackEPS est l'application officielle de gestion des évaluations d'EPS et du CCF. Le portail de Créteil fournit les notes de mise à jour techniques, l'interfaçage avec les bases élèves (fichiers XML de l'administration) et les règles de gestion des cas particuliers (dispenses, inaptitudes partielles ou totales).""",
            metadata={"title": "Portail Officiel iPackEPS - Académie de Créteil", "url": "https://eps.ac-creteil.fr/"}
        ),
        Document(
            text="""Guide Pratique Utilisateur de l'interface Professeur iPackEPS - Académie de Normandie.
            Ce manuel complet décrit l'interface enseignant. Il explique pas à pas comment gérer l'importation des structures de classes, le suivi pédagogique, et la configuration des fiches de notation pour le contrôle continu. 
            SAISIE DES CERTIFICATS MÉDICAUX & DISPENSES : La saisie des inaptitudes se fait UNIQUEMENT dans le menu 'Gestion/Suivi des élèves' > 'Fiche élève' > 'Saisir une inaptitude' en renseignant les dates exactes du certificat médical et les restrictions. RÈGLE IMPÉRATIVE : On ne peut jamais taper directement 'IN' ou 'DI' à la main dans la case d'une note brute, le statut est généré automatiquement par l'application suite à la saisie du certificat.
            RÈGLE DU CERTIFICAT MIXTE ET ABSENCE AU BAC : Pour valider le CCF de l'épreuve d'EPS au Baccalauréat, la réglementation nationale impose que l'élève dispose d'au moins DEUX notes valides dans deux épreuves de familles différentes. Si un élève est absent injustifié (note 0/20) à une épreuve et inapte à une autre, le calcul automatique d'iPackEPS va bloquer car le quota des 2 notes n'est pas atteint. L'application générera alors une alerte pour exporter le dossier vers Cyclades afin que le jury statue sur une dispense ou un passage en examen ponctuel.""",
            metadata={"title": "Guide Utilisateur Interface Professeur iPackEPS (PDF)", "url": "https://eps.ac-normandie.fr/IMG/pdf/guide_utilisateur_professeur-2.pdf"}
        ),
        Document(
            text="""Note Technique de Liaison Examens / Cyclades / Santorin - Académie de Versailles.
            Document officiel détaillant la bascule des données et la remontée des protocoles de CCF pour la session des examens. Explique les règles de transmission des dispenses, des inaptitudes à l'examen, et la synchronisation avec les serveurs de correction nationaux. Rappelle qu'une absence injustifiée équivaut à 0/20 et compte réglementairement comme une note prise en compte, alors qu'une inaptitude médicale validée neutralise l'épreuve.""",
            metadata={"title": "Note d'Information iPackEPS - Session Examens (PDF)", "url": "https://eps.ac-versailles.fr/IMG/pdf/2025_10_08_info_ipackeps_octobre_2025_-_lyc_cfa.pdf"}
        ),
        Document(
            text="""Manuel Complet d'Exploitation et d'Arborescence iPackEPS - Académie de Besançon.
            Guide pas-à-pas reprenant l'intégralité de l'arborescence des modules iPack : configuration de la Fiche professeur, création du Dossier EPS de l'établissement, suivi individuel dans l'onglet 'Gestion des élèves' et saisie des dispenses médicales.""",
            metadata={"title": "Guide d'Utilisation Complet iPackEPS (PDF)", "url": "https://eps.ac-besancon.fr/wp-content/uploads/sites/36/2022/11/IPack-EPS-Guide-dutilisation-interface-professeur.pdf"}
        ),
        Document(
            text="""RÈGLES MÉTIERS AVANCÉES - EXAMENS EPS ET CALCULS IPACKEPS :
            1. ABSENCE VS INAPTITUDE : Une absence injustifiée donne la note de 0/20 (qui compte dans l'examen). Une absence médicale génère le statut INAPTE (IN) qui neutralise l'épreuve. Ne jamais saisir 0 pour un motif médical.
            2. ABANDON EN COURS D'ÉPREUVE : Si un élève se blesse pendant le CCF, soit l'enseignant a assez d'éléments pour noter, soit l'épreuve est neutralisée pour cause de blessure et l'élève est envoyé en session de rattrapage.
            3. SYNCHRONISATION DES ÉLÈVES : Les enseignants ne peuvent pas créer d'élèves manuellement pour les examens. Toutes les listes et dispenses officielles proviennent de l'administration de l'établissement (fichiers XML de Siècle/Cyclades) via une mise à jour du secrétariat.
            4. INAPTITUDE TOTALE ANNUELLE : Un élève inapte total à l'année voit l'épreuve d'EPS neutralisée (Statut Dispensé DI final). Toutes les périodes doivent être couvertes par le certificat médical dans l'onglet Inaptitudes d'iPackEPS.""",
            metadata={"title": "Règles Métiers et Alertes iPackEPS", "url": "https://eps.ac-creteil.fr/"}
        ),
        Document(
            text="""SITUATIONS RÉGLEMENTAIRES COMPLEXES ET CAS PARTICULIERS (SÉCURITÉ ET INTERFACES) :
            1. CONFLIT MÉDICAL (ANNULATION DE DISPENSE) : Si un certificat d'inaptitude totale annuelle est invalidé en cours d'année par le médecin scolaire, l'élève redevient apte pour la période restante (ex: T3). RÈGLE DE SÉCURITÉ ABSOLUE : Il ne faut JAMAIS supprimer le certificat initial dans iPackEPS, sinon le T1 et le T2 basculent en absence injustifiée (0/20). La seule procédure est de MODIFIER LA DATE DE FIN du certificat dans l'onglet Inaptitudes pour l'arrêter juste avant le début du trimestre de reprise. L'élève aura une note unique en fin d'année, et le dossier sera arbitré par le Jury Académique.
            2. NOTE UNIQUE À L'ANNÉE : Si un élève se blesse et ne dispose que d'une seule note au lieu de deux au CCF, iPackEPS bloque le calcul automatique. L'enseignant ne doit rien forcer. Le dossier is transmis au Jury Académique via Cyclades, qui décidera soit de valider la note unique, soit d'envoyer l'élève en examen ponctuel en septembre.
            3. ÉLÈVE TRANSFÉRÉ (CHANGEMENT DE LYCÉE) : Les notes de CCF du lycée d'origine ne migrent pas automatiquement. Le prof doit récupérer le relevé officiel via le secrétariat et utiliser la fonction 'Saisie des notes hors établissement' dans iPackEPS pour intégrer l'épreuve externe.
            4. INAPTITUDE AU PROTOCOLE ADAPTÉ : Si l'inaptitude partielle d'un élève l'empêche même de suivre le protocole adapté de l'établissement, il doit être basculé informatiquement en statut 'Inapte Total' pour la période concernée.
            5. SPORTIFS DE HAUT NIVEAU (SHN) : Les élèves SHN ne sont pas dispensés du Bac EPS. En cas de compétition le jour du CCF, ils doivent obligatoirement être basculés sur une session de Rattrapage dans iPackEPS.""",
            metadata={"title": "Fiche des Cas Complexes et Arbitrages Jurys", "url": "https://eps.ac-creteil.fr/"}
        )
    ]
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=2)

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
# 6. BOUTONS DE CONTEXTE
# ======================================================================
col_b1, col_b2, col_b3 = st.columns(3, gap="small")

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

# ======================================================================
# 7. BARRE DE TITRE CENTRALE AVEC NOTE DE VIGILANCE FLUX MIXTES
# ======================================================================
label_titres = {
    "ipack": "🛠️ Mode Actif : Assistance Technique iPackEPS (Gestion du CCF & Inaptitudes)",
    "examens": "📊 Mode Actif : Réglementation Examens & Santorin (Copies Numérisées & Jurys)",
    "general": "🔍 Mode Actif : Recherche Transversale Globale (Multi-Académies)"
}

st.markdown(f"""
    <div class="column-title">
        <span class="instruction">⚙️ Choisissez le contexte de votre question ci-dessus</span>
        <span class="mode-actuel">{label_titres[st.session_state.active_module]}</span>
        <div style="margin-top: 6px; font-size: 11px; color: #FCD34D !important; font-weight: 500; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 4px;">
            ⚠️ <strong>Conseil Flux Mixtes :</strong> Si votre problématique concerne à la fois iPackEPS et Santorin (ex: bascule de notes ou dispenses), n'hésitez pas à poser votre question dans les deux modules pour obtenir l'expertise technique ET réglementaire dédiée.
        </div>
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
    prompt = st.chat_input("Posez votre question institutionnelle ou technique ici...", key="chat_main")

# ======================================================================
# 9. FLUX DE MESSAGES ET TRAITEMENT IA (AVEC SÉCURISATION DES LIENS)
# ======================================================================
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        st.markdown(m["content"], unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": f"<span style='color: white; font-weight: normal;'>{prompt}</span>"})
    
    glossaire_loi = ["bo", "boen", "jo", "jorf", "journal officiel", "texte", "textes", "officiel", "officiels", "circulaire", "circulaires", "decret", "décret", "decrets", "décrets", "loi", "lois", "arrete", "arrêté", "arretes", "arrêtés", "reglementation", "réglementation"]
    
    prompt_mots = prompt.lower().split()
    contient_terme_loi = any(mot in glossaire_loi for mot in prompt_mots) or "journal officiel" in prompt.lower()

    if st.session_state.active_module == "ipack":
        query_recherche = f"{prompt} iPackEPS"
        domaines_recherche = ["ipackeps.ac-creteil.fr", "eps.ac-creteil.fr", "eps.ac-normandie.fr", "eps.ac-versailles.fr"]
        texte_spinner = "Fouille de la base technique..."
        color_card = "general-card"
        badge_title = "🛠️ PROTOCOLE TECHNIQUE"
        instruction_date = "Pas de restriction de date pour le support technique."
    elif st.session_state.active_module == "examens":
        query_recherche = f"{prompt} examen EPS santorin"
        domaines_recherche = [
            "eduscol.education.gouv.fr", 
            "pedagogie.ac-aix-marseille.fr", 
            "eps.ac-creteil.fr", 
            "siec.education.fr",
            "pole-examens.github.io",
            "assistance.ac-noumea.nc"
        ]
        texte_spinner = "Analyse réglementaire..."
        color_card = "santorin-card"
        badge_title = "📊 REGLEMENTATION & EXAMENS"
        instruction_date = "Exclus l'UNSS. Garde les textes de référence nationaux."
    else:
        query_recherche = prompt 
        domaines_recherche = [
            "eps.ac-aix-marseille.fr",
            "pedagogie.ac-aix-marseille.fr", 
            "eduscol.education.gouv.fr", 
            "eps.enseigne.ac-lyon.fr", 
            "eps.ac-creteil.fr"
        ]
        texte_spinner = "Recherche multi-académies..."
        color_card = "general-card"
        badge_title = "🔍 RÉSULTATS DE RECHERCHE"
        
        if contient_terme_loi:
            instruction_date = "L'utilisateur recherche un texte de loi ou une pièce réglementaire historique ou officielle. LAISSE LES DATES LIBRES, accepte les textes anciens fondateurs."
        else:
            instruction_date = "L'utilisateur pose une question de pratique courante, pédagogique ou logistique. APPLIQUE UNE LIMITE STRICTE A 2020. Ignore tout document, projet ou ressource d'avant 2020."

    with st.spinner(texte_spinner):
        extraits_doc = ""
        
        # 1. Requête sur les documents internes stockés en cache (Santorin OU iPack)
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

        # 2. Requête complémentaire Web externe via l'API Tavily
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

        # Construction finale de la consigne (Prompt Engineering pour forcer l'affichage des liens)
        consigne_commune = f"""Analyse rigoureusement les documents et extraits du web mis à ta disposition ci-dessous :
        {extraits_doc}
        
        Réponds précisément à cette question : '{prompt}'.
        
        CRITÈRES DE FILTRAGE ET DE FORME IMPÉRATIFS : 
        1. Rédige une réponse claire, fluide et structurée.
        2. Tu dois OBLIGATOIREMENT lister l'intégralité des sources et documents officiels consultés à la toute fin de ta réponse sous forme de liens hypertextes cliquables au format Markdown exact : [Nom du document / de la source officielle](URL). Exemple attendu : [Guide de l'interface Professeur (PDF)](https://eps.ac-normandie.fr/IMG/pdf/guide_utilisateur_professeur-2.pdf).
        3. Interdiction absolue d'inventer des URL. Utilise uniquement les adresses exactes situées entre parenthèses dans le texte fourni ci-dessus.
        4. GESTION DES DATES : {instruction_date}"""

        if st.session_state.active_module == "ipack":
            consigne_ia = f"Tu es l'assistant technique iPackEPS. {consigne_commune} Crée un tutoriel ou guide précis basé sur les sources."
        elif st.session_state.active_module == "examens":
            consigne_ia = f"Tu es l'assistant officiel examens et spécialiste de l'outil Santorin. {consigne_commune} Rédige une réponse réglementaire complète en lissant les fiches mémos correspondantes avec leurs liens."
        else:
            consigne_ia = f"Tu es l'assistant de recherche globale. {consigne_commune} Donne une réponse claire et liste uniquement les URL utiles selon la règle de date."

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
