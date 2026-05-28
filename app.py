import streamlit as st 
import os
import pandas as pd
import requests
import re
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
    st.session_state.active_module = "peda"  

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

# Utilisation d'une chaîne classique sans "f" pour utiliser des accolades CSS normales { }
css_pur = """
    <style>
    /* Règle de sécurité : Force le blanc sur tout le texte des cartes */
    .santorin-card *, .general-card *, .securite-card * { 
        color: #FFFFFF !important; 
    }

    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 2rem !important; 
        padding-left: 1.5rem !important; 
        padding-right: 1.5rem !important; 
        max-width: 920px !important; 
    }
    
    .stApp { background-image: url('__URL_FOND__') !important; background-size: cover !important; background-attachment: fixed !important; }
    header[data-testid="stHeader"] { display: none !important; }
    
    /* Structure du Bandeau Supérieur Principal Réorganisé et Optimisé */
    .hub-header { 
        background-color: #1E293B; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 10px 20px; 
        height: 85px !important; 
        margin-bottom: 15px !important; 
        border-radius: 8px; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3); 
    }
    
    /* Bloc titre équilibré avec décalage de sécurité pour éviter le collage à droite */
    .hub-title {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        flex-grow: 1;
        padding-right: 35px; 
    }
    
    /* Ligne du titre principal */
    .title-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
    }
    
    .hub-title h1 { 
        color: white !important; 
        margin: 0 !important; 
        font-size: 28px !important; 
        font-weight: 800 !important; 
        line-height: 1.2 !important;
        letter-spacing: 0.5px;
    }
    
    /* Badge vert émeraude agrandi et bien visible */
    .badge-visiteur { 
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
    }
    
    /* Style du Sous-titre nettoyé */
    .hub-title p { 
        color: #94A3B8 !important; 
        margin: 0 !important;
        margin-top: -1px !important; 
        font-size: 13px !important; 
        text-transform: uppercase; 
        font-weight: bold !important;
        line-height: 1.1 !important; 
        letter-spacing: 0.5px;
    }

    /* Barres d'informations Supérieures et Inférieures */
    .column-title-top { 
        color: #FFFFFF; 
        text-align: center; 
        margin-bottom: 12px !important; 
        background-color: #1E293B; 
        border-radius: 6px !important; 
        padding: 8px 10px; 
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
        line-height: 1.4;
    }
    .column-title-top .instruction {
        font-size: 11px !important;
        font-weight: 500;
        text-transform: uppercase;
        color: #94A3B8 !important;
        letter-spacing: 0.5px;
        display: block;
        margin-bottom: 2px;
    }
    .column-title-top .mode-actuel {
        font-size: 14px !important; 
        font-weight: 700;
        color: #FFFFFF !important;
        display: block;
    }

    .column-title-bottom { 
        text-align: center; 
        margin-top: 12px !important;
        margin-bottom: 15px !important; 
        background-color: rgba(30, 41, 59, 0.8); 
        border-radius: 6px !important; 
        padding: 8px 12px; 
        border: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 11px !important; 
        color: #FCD34D !important; 
        font-weight: 500;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.15);
    }
    
    /* Boutons Inactifs - Alignement et hauteur forcés */
    button[kind="secondary"] { 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        color: #94A3B8 !important; 
        border: 1px solid rgba(255,255,255,0.05) !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
        padding: 2px 10px !important;
        transition: all 0.3s ease;
        height: 60px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        white-space: normal !important;
    }

    /* Boutons Actifs - Alignement et hauteur forcés */
    button[kind="primary"] {
        background-color: rgba(16, 185, 129, 0.85) !important;
        color: #FFFFFF !important;
        border: 1px solid #10B981 !important;
        border-radius: 8px !important; 
        font-size: 13px !important; 
        padding: 2px 10px !important;
        box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.6) !important;
        font-weight: 700 !important;
        height: 60px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        white-space: normal !important;
    }
    
    /* BOUTON NETTOYER - Protection contre l'alignement des boutons du haut */
    div.element-container:has(.nettoyer-wrapper) + div.element-container button {
        background-color: rgba(220, 38, 38, 0.45) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(220, 38, 38, 0.6) !important;
        border-radius: 8px !important;
        padding: 7px 10px !important;
        width: 100% !important;
        height: 38px !important;
    }
    div.element-container:has(.nettoyer-wrapper) + div.element-container button:hover {
        background-color: rgba(220, 38, 38, 0.65) !important;
    }
    
    /* CARTES DE RÉPONSE */
    .santorin-card, .general-card, .securite-card, .peda-card { 
        background-color: rgba(15, 23, 42, 0.45) !important; 
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        padding: 18px; 
        border-radius: 8px; 
        margin-bottom: 16px; 
        box-shadow: 0px 6px 20px rgba(0,0,0,0.5);
    }
    .santorin-card { border-left: 6px solid #38BDF8 !important; } 
    .general-card { border-left: 6px solid #10B981 !important; } 
    .securite-card { border-left: 6px solid #EF4444 !important; } 
    .peda-card { border-left: 6px solid #8B5CF6 !important; } 
    
    .santorin-card p, .general-card p, .securite-card p, .santorin-card div, .general-card div, .securite-card div, .santorin-card span, .general-card span, .securite-card span, .santorin-card li, .general-card li, .securite-card li { 
        color: #FFFFFF !important; 
        font-size: 15px !important; 
        line-height: 1.6 !important; 
        font-weight: 400 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }
    
    /* ⚡ RE-CALIBRAGE COMPACT DU MODE PÉDAGOGIE */
    .peda-card h3 {
        font-size: 15px !important; 
        margin-top: 14px !important; 
        margin-bottom: 4px !important; 
        color: #C084FC !important; 
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.9);
    }
    .peda-card ul {
        margin-top: 2px !important;
        margin-bottom: 6px !important;
        padding-left: 20px !important;
    }
    .peda-card li, .peda-card div, .peda-card span, .peda-card p {
        font-size: 14px !important; 
        line-height: 1.4 !important; 
        color: #FFFFFF !important;
        margin-bottom: 3px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }
    .peda-card strong {
        color: #FCD34D !important; 
    }

    .santorin-card strong, .general-card strong, .securite-card strong {
        font-weight: 700 !important; 
        color: #FFFFFF !important;
    }

    .santorin-card a, .general-card a, .securite-card a, .santorin-card a *, .general-card a *, .securite-card a *, .peda-card a, .peda-card a * {
        color: #FFB020 !important; 
        text-decoration: underline !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.9) !important;
    }
    .santorin-card a:hover, .general-card a:hover, .securite-card a:hover, .peda-card a:hover {
        color: #FCD34D !important;
    }
    
    /* Bulle Utilisateur */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) { 
        background-color: rgba(255, 255, 255, 0.15) !important; 
        backdrop-filter: blur(6px) !important;
        border-radius: 14px 14px 0px 14px !important; 
        margin-left: 15% !important; 
    }
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
    
    /* FORCE LE BLANC DANS LE CHAT */
    div[data-testid="stChatMessage"] * { color: #FFFFFF !important; }
    
    /* RESTAURATION DE LA COULEUR DES LIENS SANS TOUCHER AU RESTE */
    div[data-testid="stChatMessage"] a, div[data-testid="stChatMessage"] a * {
        color: #FFB020 !important;
        text-decoration: underline !important;
        font-weight: 600 !important;
    }
    div[data-testid="stChatMessage"] a:hover {
        color: #FCD34D !important;
    }
    
    </style> 
""".replace('__URL_FOND__', f"{github_url}{img_fond}")
st.markdown(css_pur, unsafe_allow_html=True)

# ======================================================================
# 4. CONFIGURATION DE L'INTELLIGENCE ARTIFICIELLE & DES BASES DE DOCUMENTS
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    # Nettoyage du doublon 'if' + Augmentation des max_tokens pour le souffle de l'IA
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, max_tokens=4000, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

def obtenir_cle_fichier():
    chemin_dossier = "pierre"
    if os.path.exists(chemin_dossier) and os.path.isdir(chemin_dossier):
        try:
            mtimes = [os.path.getmtime(os.path.join(chemin_dossier, f)) for f in os.listdir(chemin_dossier) if f.endswith((".txt", ".md"))]
            return max(mtimes) if mtimes else 0.0
        except Exception:
            return 0.0
    return 0.0

def charger_consignes_pierre():
    chemin_dossier = "pierre"
    documents_charges = []
    if os.path.exists(chemin_dossier) and os.path.isdir(chemin_dossier):
        try:
            for fichier in os.listdir(chemin_dossier):
                if fichier.endswith((".txt", ".md")):
                    with open(os.path.join(chemin_dossier, fichier), "r", encoding="utf-8") as f:
                        contenu_fichier = f.read()
                    documents_charges.append(Document(text=contenu_fichier, metadata={"source": f"Notes de Pierre - {fichier}"}))
            return documents_charges
        except Exception:
            return []
    return []

@st.cache_resource
def initialiser_base_santorin(cle_fremt):
    docs_santorin = [
        Document(
            text="""Fiche Mémo - Correction Partagée Santorin (DEC / Assistance). 
            La correction partagée ou multiple permits à several évaluateurs/correcteurs d'intervenir sur un même lot de copies. 
            Dans Santorin, un chef d'établissement peut ajouter manuellement un deuxième évaluateur ou correcteur à un lot via le portail Arena / Cyclades. 
            Procédure : Aller dans l'onglet 'Lots', cliquer sur 'Voir le détail', aller sur l'onglet 'Correcteurs' then cliquer sur le bouton 'Ajouter'.
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
            Accès à la Base École de Santorin (environnement de test/formation), fiches d'aide à la connexion, procedures d'urgence en cas de page manquante ou copie mal numérisée.""",
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
    docs_santorin.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_ipack(cle_fremt):
    docs_ipack = [
        Document(
            text="""Portail Pilote iPackEPS - Académie de Créteil. 
            iPackEPS is the official application for managing PE evaluations and CCF.""",
            metadata={"title": "Portail Officiel iPackEPS - Académie de Créteil", "url": "https://eps.ac-creteil.fr/"}
        ),
        Document(
            text="""Guide Pratique Utilisateur de l'interface Professeur iPackEPS - Académie de Normandie.
            SAISIE DES CERTIFICATS MÉDICAUX & DISPENSES : La saisie des inaptitudes se fait UNIQUEMENT dans le menu 'Gestion/Suivi des élèves' > 'Fiche élève' > 'Saisir une inaptitude'. RÈGLE IMPÉRATIVE : On ne peut jamais taper directement 'IN' ou 'DI' à la main dans la case d'une note brute, le statut est généré automatiquement par l'application.
            RÈGLE DU CERTIFICAT MIXTE ET ABSENCE AU BAC : Pour valider le CCF de l'épreuve d'EPS au Baccalauréat, la réglementation nationale impose que l'élève dispose d'au moins DEUX notes valides dans deux épreuves de familles différentes.""",
            metadata={"title": "Guide Utilisateur Interface Professeur iPackEPS (PDF)", "url": "https://eps.ac-normandie.fr/IMG/pdf/guide_utilisateur_professeur-2.pdf"}
        ),
        Document(
            text="""Note Technique de Liaison Examens / Cyclades / Santorin - Académie de Versailles.
            Rappelle qu'une absence injustifiée équivaut à 0/20 et compte réglementairement comme une note prise en compte, alors qu'une inaptitude médicale validée neutralise l'épreuve.""",
            metadata={"title": "Note d'Information iPackEPS - Session Examens (PDF)", "url": "https://eps.ac-versailles.fr/IMG/pdf/2025_10_08_info_ipackeps_octobre_2025_-_lyc_cfa.pdf"}
        ),
        Document(
            text="""SITUATIONS RÉGLEMENTAIRES COMPLEXES ET CAS PARTICULIERS (SÉCURITÉ ET INTERFACES) :
            1. CONFLIT MÉDICAL (ANNULATION DE DISPENSE) : Si un certificat d'inaptitude totale annuelle est invalidé en cours d'année, la seule procedure is de MODIFIER LA DATE DE FIN du certificat dans l'onglet Inaptitudes pour l'arrêter juste avant le début du trimestre de reprise.
            2. NOTE UNIQUE À L'ANNÉE : Si un élève se blesse et n'a qu'une seule note au lieu de deux au CCF, iPackEPS blocks the automatic calculation. Le dossier est transmis au Jury Académique via Cyclades.
            3. BOUTON CHANGEMENT D'ACTIVITÉ GRISÉ : Si l'interface refuse de modifier l'activité ou l'option d'un élève pour le trimestre, c'est qu'une note a déjà été saisie. Pour débloquer informatiquement le bouton, l'enseignant doit obligatoirement se rendre dans le menu 'Saisie des notes' de l'activité actuelle, effacer manuellement la note saisie pour rendre la case totalement vide (pas de zéro, juste du vide), puis enregistrer. Le bouton de modification dans la fiche élève sera alors instantanément dégrisé.""",
            metadata={"title": "Fiche des Cas Complexes et Arbitrages Jurys", "url": "https://eps.ac-creteil.fr/"}
        )
    ]
    docs_ipack.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_textes(cle_fremt):
    docs_textes = [
        Document(
            text="""Base de données réglementaire globale pour les textes de lois, décrets officiels et circulaires de sécurité d'un établissement scolaire du second degré.""",
            metadata={"title": "Référentiel National Textes et Lois", "url": "https://www.legifrance.gouv.fr/"}
        )
    ]
    docs_textes.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_textes).as_retriever(similarity_top_k=5)

# Initialisation sécurisée par le cache avec surveillance du fichier de Pierre
timestamp_fichier = obtenir_cle_fichier()
retriever_santorin = initialiser_base_santorin(timestamp_fichier)
retriever_ipack = initialiser_base_ipack(timestamp_fichier)
retriever_textes = initialiser_base_textes(timestamp_fichier)
retriever_peda = retriever_ipack

@st.cache_resource
def initialiser_base_concours(cle_fremt):
    os.makedirs("data/bibli_concours", exist_ok=True)
    try:
        reader = SimpleDirectoryReader("data/bibli_concours")
        docs_concours = reader.load_data()
        if not docs_concours:
            docs_concours = [Document(text="Base Concours EPS initialisée. En attente des fiches de sessions.")]
        return VectorStoreIndex.from_documents(docs_concours).as_retriever(similarity_top_k=3)
    except Exception:
        dummy = [Document(text="Erreur ou absence de fichiers dans data/bibli_concours.")]
        return VectorStoreIndex.from_documents(dummy).as_retriever(similarity_top_k=1)

# Lignes à mettre juste après tes autres déclenchements de retrievers :
retriever_concours = initialiser_base_concours(timestamp_fichier)

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
# 6. EN-TÊTE DU TABLEAU DE BORD (SYNCHRONISÉ AVEC LES CLÉS)
# ======================================================================
label_titres = {
    "ipack": "🛠️ Mode Actif : Assistance Technique iPackEPS (Gestion du CCF & Inaptitudes)",
    "examens": "📊 Mode Actif : Réglementation Examens & Santorin (Copies Numérisées & Jurys)",
    "peda": "🔍 Mode Actif : Questions Pédagogiques, Didactiques & Pratiques de Terrain",
    "textes": "🔒 Mode Actif : Sécurité & Responsabilité Juridique (Textes Officiels & Risques APPN)"
}

if "active_module" not in st.session_state:
    st.session_state.active_module = "peda"

titre_affiche = label_titres.get(st.session_state.active_module, "🔍 Mode Actif : Questions Pédagogiques")

st.markdown(f"""
    <div class="column-title-top">
        <span class="instruction">⚙️ Choisissez le contexte de votre question ci-dessous</span>
        <span class="mode-actuel">{titre_affiche}</span>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 7. BOUTONS DE CONTEXTE ALIGNÉS SUR 4 COLONNES (AVEC AVATARS ET HAUTEUR FIXE)
# ======================================================================
col_b1, col_b2, col_b3, col_b4 = st.columns(4, gap="small")

with col_b1:
    if st.button("🛠️ iPackEPS", use_container_width=True, key="btn_ip", type="primary" if st.session_state.active_module == "ipack" else "secondary"):
        st.session_state.active_module = "ipack"
        st.session_state.messages_hub = []
        st.rerun()

with col_b2:
    if st.button("📊 Examens &\nSantorin", use_container_width=True, key="btn_ex", type="primary" if st.session_state.active_module == "examens" else "secondary"):
        st.session_state.active_module = "examens"
        st.session_state.messages_hub = []
        st.rerun()

with col_b3:
    if st.button("🔍 Pédagogie &\nDidactique", use_container_width=True, key="btn_ge", type="primary" if st.session_state.active_module == "peda" else "secondary"):
        st.session_state.active_module = "peda"
        st.session_state.messages_hub = []
        st.rerun()

with col_b4:
    if st.button("🔒 Sécurité &\nCadres Règl.", use_container_width=True, key="btn_se", type="primary" if st.session_state.active_module == "textes" else "secondary"):
        st.session_state.active_module = "textes"
        st.session_state.messages_hub = []
        st.rerun()

# ======================================================================
# 7B. MESSAGES D'AVERTISSEMENT DYNAMIQUES AVEC BANDEAU D'AIGUILLAGE PIERRE
# ======================================================================
if st.session_state.active_module == "textes":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            ⚠️ <strong>Avertissement – Bien que basées sur les textes officiels, ces réponses ne remplacent pas les autorités académiques. En cas de doute juridique ou de sinistre, contactez impérativement : <strong>Votre Chef d'établissement, votre Secrétariat d'examen, ou votre IA-IPR.</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.active_module == "peda":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            💡 <strong>Exemples de recherches dans cet onglet :</strong> Projets pédagogiques, compétences visées, fonctionnement de l'AS / UNSS, gestion de classe, ressources par APSA, projets transversaux (SRE, Savoir Rouler, etc.).
        </span>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px; line-height: 1.5;">
        <div style="color: #38BDF8; font-weight: 800; font-size: 14px; text-align: center; margin-bottom: 12px; letter-spacing: 0.5px;">
            🎯 OÙ POSER VOTRE QUESTION ?
        </div>
        <div style="display: flex; gap: 20px; color: #FCD34D; font-size: 13px;">
            <div style="flex: 1; border-right: 1px solid #334155; padding-right: 20px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">🛠️ Menu iPackEPS (Toute l'année)</strong><br>
                <span style="color: #FCD34D !important;">Technique de terrain : configuration de l'application, création des groupes, saisie des notes brutes.</span><br>
                <div style="margin-top: 8px; padding: 5px 8px; background-color: rgba(248, 113, 113, 0.15); border-left: 3px solid #F87171; border-radius: 4px;">
                    <span style="color: #F87171 !important; font-weight: 800;">⚠️ IMPORTANT INAPTITUDES :</span><br>
                    <span style="color: #FFFFFF !important; font-size: 12px;">Toutes les questions sur les certificats médicaux, dispenses et saisies d'inaptitude se posent TOUJOURS ici, dans le menu iPackEPS !</span>
                </div>
            </div>
            <div style="flex: 1; padding-left: 5px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">📊 Menu Examens & Santorin (Fin d'année)</strong><br>
                <span style="color: #FCD34D !important;">Administration des examens : remontée officielle des notes du Bac/DNB, correction des lots de copies numériques sur Arena, arbitrages des Jurys Académiques.</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ======================================================================
# 8. ZONE D'ACTION (ARCHITECTURE SÉCURISÉE & TEXTE LUMINEUX)
# ======================================================================
col_action_clear, col_action_input = st.columns([1, 4.5], gap="small")

with col_action_clear:
    st.markdown('<div class="nettoyer-wrapper"></div>', unsafe_allow_html=True)
    if st.button("🧹 Nettoyer", key="clear_all"):
        st.session_state.messages_hub = []
        st.rerun()

with col_action_input:
    prompt = st.chat_input("Posez votre question institutionnelle, technique ou juridique ici...", key="chat_main")

st.markdown("""
    <div style="background-color: #1E293B; padding: 12px 20px; border-radius: 6px; box-shadow: 0px 4px 8px rgba(0,0,0,0.2); margin-top: 10px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: center; line-height: 1.4;">
        <span style="color: #FCD34D; font-weight: 700; font-size: 13px;">
            ⚠️ 💡 ATTENTION :
        </span>
        <span style="color: #FFFFFF; font-weight: 500; font-size: 13px; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">
            Pour des raisons pratiques et de mise à jour, votre assistant ne mémorise pas le fil de la conversation. Posez vos questions une par une après les avoir nettoyées.
        </span>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 9. FLUX DE MESSAGES ET TRAITEMENT IA (CONSOLIDATION FINALE - MULTI-VIDÉOS)
# ======================================================================
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        if isinstance(m["content"], str) and m["content"].startswith("st.video("):
            exec(m["content"])
        else:
            st.markdown(m["content"], unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

domaine_eps_france = [
    "eduscol.education.gouv.fr", "eps.ac-aix-marseille.fr", "edubase.eduscol.education.fr" , "eps.ac-amiens.fr", "eps.ac-besancon.fr", 
    "eps.ac-bordeaux.fr", "eps.ac-normandie.fr", "eps.ac-clermont.fr", "eps.ac-corse.fr", 
    "eps.ac-creteil.fr", "eps.ac-dijon.fr", "eps.ac-grenoble.fr", "eps.ac-lille.fr", 
    "eps.ac-limoges.fr", "eps.ac-lyon.fr", "eps.ac-montpellier.fr", "eps.ac-nancy-metz.fr", 
    "eps.ac-nantes.fr", "eps.ac-nice.fr", "eps.ac-orleans-tours.fr", "eps.ac-paris.fr", 
    "eps.ac-poitiers.fr", "eps.ac-reims.fr", "eps.ac-rennes.fr", "pedagogie.ac-strasbourg.fr", 
    "eps.ac-toulouse.fr", "eps.ac-versailles.fr", "eps.ac-guadeloupe.fr", "eps.ac-guyane.fr", 
    "eps.ac-martinique.fr", "eps.ac-mayotte.fr", "eps.ac-reunion.fr"
]

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": f"<span style='color: white;'>{prompt}</span>"})
    
    # Le spinner englobe bien toute la chaîne de traitement
    with st.spinner("Je recherche les documents et ressources pédagogiques..."):
        extraits_doc = ""
        mode = st.session_state.active_module
        
        prompt_lower = prompt.lower()
        # Détection immédiate du contexte Concours prioritaire
        est_demande_concours = any(x in prompt_lower for x in ["agreg", "greg", "agrégation", "capeps", "concours", "écrit 1", "écrit 2", "sujet de 20", "sujet 20"])
        
        mots_terrain = ["fiche", "evaluation", "évaluation", "grille", "bareme", "barème", "cycle", "seance", "séance", "apsa", "volley", "hand", "basket", "badminton", "relais", "natation", "escalade", "gym", "college", "collège"]
        est_demande_fiche = any(mot in prompt_lower for mot in mots_terrain)
        
        verites_terrain_pierre = ""
        try:
            for fichier in os.listdir("."):
                if fichier.endswith((".txt", ".md")) and "pierre" in fichier.lower():
                    with open(fichier, "r", encoding="utf-8") as f:
                        verites_terrain_pierre += f"\n--- REGLES DIRECTES ({fichier}) ---\n" + f.read() + "\n"
        except:
            pass
        
        # 1. MOTEUR WEB (Tavily) - Désactivé en mode Concours pour éviter la pollution de PDF
        if tavily_api_key and not est_demande_concours:
            try:
                domains = domaine_eps_france
                requete_blindee = prompt
                exclude = []
                tavily_deja_execute = False

                if mode == "textes":
                    mot_cle = prompt.lower()
                    expressions_inutiles = [
                        "je cherche un texte officiel pour savoir si", "je cherche un texte sur le", 
                        "je cherche un texte sur la", "je cherche un texte sur", "pour savoir si j'ai le droit de",
                        "est-ce que j'ai le droit de", "ai-je le droit de", "est-ce qu'il existe un texte",
                        "trouve moi le texte sur", "trouve moi une circulaire sur", "trouve moi", 
                        "recherche le texte sur", "texte officiel sur", "circulaire concernant", "circulaire sur"
                    ]
                    for exp in expressions_inutiles:
                        mot_cle = mot_cle.replace(exp, "")
                    for verbe in ["savoir si", "refuser une", "refuser un", "concerne le", "concerne la"]:
                        mot_cle = mot_cle.replace(verbe, "")
                    mot_cle = mot_cle.strip() if mot_cle.strip() else prompt

                    domains_prioritaires = ["pedagogie.ac-aix-marseille.fr", "legifrance.gouv.fr", "education.gouv.fr", "eduscol.education.gouv.fr"]
                    requete_blindee = f"EPS {mot_cle} loi laïcité code de l'éducation circulaire décret arrêté BO"
                    
                    payload = {
                        "api_key": tavily_api_key, 
                        "query": requete_blindee, 
                        "search_depth": "advanced", 
                        "include_domains": domains_prioritaires
                    }
                    
                    res = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
                    results = res.json().get("results", []) if res.status_code == 200 else []
                    
                    if not results:
                        payload["include_domains"] = domaine_eps_france
                        res = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
                        results = res.json().get("results", []) if res.status_code == 200 else []
                    
                    for item in results: 
                        extraits_doc += f"Source Web ({item['title']}): {item['content']} - URL: {item['url']}\n\n"
                    
                    tavily_deja_execute = True
                
                elif mode == "examens":
                    requete_blindee = f"{prompt} réglementation examen Santorin Cyclades"
                    domains = ["education.gouv.fr"] + domaine_eps_france
                
                elif mode == "ipack":
                    requete_blindee = f"rubrique4 {prompt}"
                    domains = ["ipackeps.ac-creteil.fr"]
                    exclude = ["youtube.com"]
                
                elif mode == "peda" or est_demande_fiche:
                    requete_blindee = f"{prompt} évaluation fiche filetype:pdf"
                    domains = domaine_eps_france
                
                else:
                    requete_blindee = f"{prompt} EPS programme officiel"
                    domains = ["eduscol.education.gouv.fr", "unss.org"]

                if not tavily_deja_execute:
                    payload = {
                        "api_key": tavily_api_key, 
                        "query": requete_blindee, 
                        "search_depth": "advanced", 
                        "include_domains": domains
                    }
                    if exclude:
                        payload["exclude_domains"] = exclude
                    
                    res = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
                    if res.status_code == 200:
                        for item in res.json().get("results", []): 
                            extraits_doc += f"Source Web ({item['title']}): {item['content']} - URL: {item['url']}\n\n"
            except: 
                pass

        # ======================================================================
        # 2. CONTEXTE LOCAL & BIBLIOTHÈQUE CONCOURS SOUVERAINE (BLOC 2 VERROUILLÉ)
        # ======================================================================
        if openai_api_key:
            try:
                if est_demande_concours:
                    # Stockage direct des compositions rédigées par Pierre pour neutraliser les bugs serveurs
                    base_corrections_pierre = {
                        "2022": """
                        <h3>BIBLIOTHÈQUE CONCOURS - CORRECTION AGRÉGATION INTERNE 2022 (ÉCRIT 1)</h3>
                        <strong>Sujet : L’Éducation Physique et Sportive face aux enjeux de santé publique de 1967 à nos jours : de la préservation du capital corporel des élèves à l’éducation à la responsabilité sanitaire.</strong><br><br>
                        
                        <h3>1. DÉCODAGE DE LA TENSION DIALECTIQUE</h3>
                        En 1967, la santé est envisagée sous un angle purement biologique et mécanique. L'école doit fortifier et redresser le capital corporel de l'élève (vision instrumentaliste du corps-machine). De nos jours, la santé est globale (physique, mentale, sociale - définition de l'OMS). L'enjeu est d'éduquer à la responsabilité sanitaire : l'élève devient l'acteur lucide de sa propre gestion de vie physique (savoir s'auto-réguler, faire des choix autonomes). La tension réside dans le passage d'une santé subie et mécaniste à une santé choisie et comportementale.<br><br>
                        
                        <h3>2. PROBLÉMATIQUE DE COPIE MAJORE</h3>
                        De 1967 à nos jours, l'EPS est passée d'une logique de normalisation hygiéniste à une propédeutique de l'autonomie sanitaire. En adossant le traitement didactique des activités sportives à des compétences méthodologiques et sociales, la discipline a transformé l'effort physique : hier moyen de redressement et de sélection des corps, il est devenu aujourd'hui un objet de réflexion et d'auto-régulation, permettant à chaque élève de construire un habitus de pratique durable et responsable face aux dérives sédentaires contemporaines.<br><br>
                        
                        <h3>3. DÉROULEMENT DU PLAN ARGUMENTÉ ET ILLUSTRATIONS</h3>
                        <ul>
                        <li><strong>PARTIE I (1967 - Fin 1970) : La santé mesurée par l'efficience motrice. Développer le capital corporel par le rendement sportif.</strong><br>
                        - <i>Thèse</i> : La santé est synonyme de normalité morphologique et de puissance aérobie pour répondre à la modernisation de la société.<br>
                        - <i>Ancrages</i> : 📚 J. Pineau (1990) et l'hygiénisme sportif. 📚 G. Vigarello (1985) et le passage du corps redressé au corps performant.<br>
                        - <i>Textes</i> : 📜 IO de 1967 (développement des facteurs de la conduite).<br>
                        - <i>Terrain (Demi-fond / CA1)</i> : 🎯 Test du Cooper (12 minutes). L'enseignant chronomètre au sifflet et impose une allure standardisée pour toute la classe. L'élève subit l'effort, la note est indexée sur la performance brute du barème national.<br><br>
                        </li>
                        <li><strong>PARTIE II (Années 1980 - Fin 1990) : La scolarisation de la santé. De la performance subie à la gestion méthodique de l'effort.</strong><br>
                        - <i>Thèse</i> : L'intégration à l'Éducation Nationale (1981) intellectualise la discipline. La santé devient un Savoir. On apprend à l'élève à connaître ses limites.<br>
                        - <i>Ancrages</i> : 📚 A. Hébrard (1986) et les habitudes de pratique pour la vie future. 📚 J. Marsenach (1991) et la pédagogie de résolution de problème.<br>
                        - <i>Textes</i> : 📜 Loi de 1989 (élève au centre), 📜 Programmes Collège 1996 (le citoyen qui gère sa vie physique).<br>
                        - <i>Terrain (Course en Durée / CA1)</i> : 🎯 Utilisation des tables de VMA. L'élève court à 80% de sa vitesse sur un contrat de régularité (plots tous les 50m) et apprend à prendre ses pulsations cardiaques à la carotide à la fin de l'effort.<br><br>
                        </li>
                        <li><strong>PARTIE III (Années 2000 - 2026) : L'ère de la responsabilité sanitaire. L'avènement du CA5 et la littératie physique.</strong><br>
                        - <i>Thèse</i> : Face à l'explosion de la sédentarité, l'État commande une EPS protectrice. Le CA5 valide une performance de soi adossée à une conscience fine des postures de sécurité.<br>
                        - <i>Ancrages</i> : 📚 D. Delignières (2019) et l'engagement lucide. 📚 N. Solal (2012) et la construction d'un habitus durable.<br>
                        - <i>Textes</i> : 📜 Programmes Collège 2015 (Domaine 3 du socle), 📜 Programmes Lycée 2019 (AFL 2 : réguler sa charge au regard des indicators).<br>
                        - <i>Terrain (Musculation / CA5 Lycée)</i> : 🎯 Mobile Entretien. L'élève conçoit sa séance (4x10 à 65% sur presse). Le partenaire (AFL 3) valide les trajectoires et pare. L'élève ajuste ses séries de manière autonome en croisant sa Fréquence Cardiaque et son échelle de ressenti de l'effort (RPE / Échelle de Borg).
                        </li>
                        </ul>
                        """,
                        
                        "2025": """
                        <h3>BIBLIOTHÈQUE CONCOURS - CORRECTION AGRÉGATION INTERNE 2025 (ÉCRIT 2)</h3>
                        <strong>Sujet : En quoi la diversité des parcours de formation des élèves en EPS (du cycle 3 au lycée) interroge-t-elle la conception des projets de cycle et le choix des situations d'apprentissage ?</strong><br><br>
                        
                        <h3>1. DÉGAGEAGE DE LA TENSION DIALECTIQUE</h3>
                        Le sujet impose de penser la cohérence verticale du parcours face aux hétérogénéités et aux ruptures de programmation entre cycles. La tension centrale réside dans l'obligation d'assurer une transformation motrice commune et évaluable (les attendus des programmes) tout en prenant en compte la singularité et la discontinuité des parcours réels des élèves.<br><br>
                        
                        <h3>2. PROBLÉMATIQUE DE COPIE MAJORE</h3>
                        La diversité des parcours, loin d'être un obstacle à la standardisation, constitue le moteur d'une rationalisation didactique de l'EPS. Du cycle 3 au lycée, elle impose de concevoir des projets de cycle centrés sur des profils de transformation prioritaires. Cette adaptabilité se traduit sur le terrain par des situations d'apprentissage à variables d'action multiples, permettant à chaque élève, quel que soit son vécu antérieur, de s'engager de manière lucide et d'atteindre les niveaux de maîtrise certifiés.<br><br>
                        
                        <h3>3. DÉROULEMENT DU PLAN ARGUMENTÉ ET ILLUSTRATIONS</h3>
                        <ul>
                        <li><strong>PARTIE I : Du Cycle 3 au Cycle 4 : Stabiliser les fondamentaux moteurs face aux ruptures de la liaison école-collège.</strong><br>
                        - <i>Thèse</i> : L'arrivée au collège révèle des disparités massives dues à la fragilité de l'EPS au 1er degré. Le projet de cycle sert de matrice de remobilisation.<br>
                        - <i>Ancrages</i> : 📚 J. Horoks (2018) et la liaison cycle 3. 📚 M. Durand (1987) et la coordination motrice générale préalable.<br>
                        - <i>Textes</i> : 📜 Programmes de 2015 (Continuité école/collège), Domaines 1 et 2 du Socle.<br>
                        - <i>Terrain (Volley-Ball / CA4)</i> : 🎯 Constat de 40% de novices en 4ème. Situation en 3vs3 avec score parlant. Les élèves fragiles ont droit à un joker (ballon bloqué 1 seconde) pour organiser l'attaque, les experts frappent en touches directes. Tous valident le Domaine 2.<br><br>
                        </li>
                        <li><strong>PARTIE II : Du Cycle 4 au Lycée : S'appuyer sur les acquis méthodologiques pour engager l'élève dans des choix de mobiles autonomes.</strong><br>
                        - <i>Thèse</i> : Au lycée, la diversité est institutionnalisée par les menus de CCF. Le projet de cycle doit être capacitant et mobiliser les outils d'auto-régulation.<br>
                        - <i>Ancrages</i> : 📚 D. Delignières (2019) et l'autonomie. 📚 C. Sève (2012) et le passage à l'auto-régulation des ressources.<br>
                        - <i>Textes</i> : 📜 Programmes Lycée 2019 (AFL 2 : concevoir et réguler, AFL 3 : rôles sociaux).<br>
                        - <i>Terrain (Musculation / CA5 Lycée)</i> : 🎯 Projet articulé autour de 3 parcours types (Tonification, Volume, Postural). L'élève choisit son mobile et ses charges en utilisant un carnet de bord croisant l'Échelle de Borg (RPE) et son calcul de charge max. L'effort est personnalisé, le parcours est valorisé.<br><br>
                        </li>
                        <li><strong>PARTIE III : La prise en compte des parcours singuliers : L'inclusion et l'adaptation réglementaire comme sommets de la responsabilité enseignante.</strong><br>
                        - <i>Thèse</i> : La diversité culmine avec les élèves à besoins particuliers ou inaptes. Le projet de cycle impose une accessibilité didactique pour garantir l'équité sans exclusion.<br>
                        - <i>Ancrages</i> : 📚 A. Marcellini (2005) et l'inclusion corporelle. 📚 É. Dugas (2004) et la modification des règles génératrices du jeu.<br>
                        - <i>Textes</i> : 📜 Loi Handicap de 2005, aménagement des examens officiels et neutralisation médicale via iPackEPS.<br>
                        - <i>Terrain (Course d'Orientation / CA2)</i> : 🎯 Intégration d'un élève inapte moteur des membres inférieurs en Terminale. L'enseignant conçoit une carte spécifique avec un parcours 'O-Précision' (identification des balises par choix d'azimut depuis des chemins carrossables). Le critère d'évaluation n'est pas la vitesse mais la justesse stratégique. L'inclusion est absolue.
                        </li>
                        </ul>
                        """,
                        
                        "2023": """
                        <h3>BIBLIOTHÈQUE CONCOURS - CORRECTION CAPEPS EXTERNE 2023 (ÉCRIT 1)</h3>
                        <strong>Sujet : L'EPS et l'école : comment la discipline a-t-elle défendu sa place et sa légitimité institutionnelle au sein du système éducatif de 1981 à nos jours ?</strong><br><br>
                        
                        <h3>1. DÉCODAGE DE LA TENSION DIALECTIQUE</h3>
                        En 1981, l'EPS rejoint l'Éducation Nationale. Pour défendre sa place, elle a dû prouver qu'elle n'était pas une simple récréation sportive mais une matière évaluable, sérieuse et noble. La tension réside dans l'oscillation historique entre s'aligner sur les codes scolaires traditionnels (au risque d'une intellectualisation) et affirmer sa spécificité corporelle unique.<br><br>
                        
                        <h3>2. PROBLÉMATIQUE DE COPIE MAJORE</h3>
                        De 1981 à nos jours, l'EPS a conquis sa légitimité en opérant une double mutation : d'une part, en se conformant aux exigences de l'école (programmes par compétences, CCF aux examens, alignement sur le Socle) ; d'autre part, en affirmant sa contribution sociétale irremplaçable comme la seule matière capable d'articuler transformation motrice, santé publique face à la sédentarité et apprentissage de la citoyenneté républicaine en actes.<br><br>
                        
                        <h3>3. DÉROULEMENT DU PLAN ARGUMENTÉ ET ILLUSTRATIONS</h3>
                        <ul>
                        <li><strong>PARTIE I (1981 - Début 1990) : La légitimation par la normalisation scolaire et la didactisation.</strong><br>
                        - <i>Thèse</i> : Rattachée au MEN, l'EPS doit formaliser ce qu'elle fait apprendre. C'est l'apparition des savoirs scolaires issus de la recherche didactique.<br>
                        - <i>Ancrages</i> : 📚 J. Marsenach (1991) et la formulation des objectifs. 📚 M. Hébrard (1986) et l'obligation d'évaluer pour être pris au sérieux.<br>
                        - <i>Textes</i> : 📜 Décret d'intégration du 28 mai 1981, 📜 Loi d'orientation de 1989.<br>
                        - <i>Terrain (Volley-ball / CA4)</i> : 🎯 On passe du jeu brut au traitement didactique. L'élève remplit des fiches d'observation sur la rupture de l'échange et est évalué sur sa capacité à organiser l'attaque depuis la zone arrière. La discipline fait réfléchir.<br><br>
                        </li>
                        <li><strong>PARTIE II (Milieu 1990 - Années 2000) : La légitimation par l'évaluation officielle aux examens nationaux.</strong><br>
                        - <i>Thèse</i> : Pour être noble, une matière doit compter pour les diplômes. L'EPS ancre sa légitimité en créant le CCF au Brevet et au Baccalauréat.<br>
                        - <i>Ancrages</i> : 📚 Y. Combaz (2010) et la sociologie de l'évaluation standardisée. 📚 F. Gleyse (2007) et la figure de l'enseignant-évaluateur.<br>
                        - <i>Textes</i> : 📜 Arrêtés de 1993 et 1995 (généralisation du CCF au Bac), 📜 Programmes Nationaux de 1996.<br>
                        - <i>Terrain (Course d'Orientation / CA2)</i> : 🎯 Épreuve du Baccalauréat. La note croise la vitesse et la justesse méthodologique. L'élève est noté sur la pertinence de ses choix d'itinéraires sur la carte. Une notation indiscutable qui valide la rigueur de la matière.<br><br>
                        </li>
                        <li><strong>PARTIE III (Années 2010 - 2026) : La légitimation sociétale. L'EPS comme pilier républicain et de santé publique.</strong><br>
                        - <i>Thèse</i> : Face aux crises (sédentarité, écrans), l'État énumère l'EPS en bouclier sanitaire et civique. Elle s'aligne sur le Socle commun en faisant vivre la fraternité.<br>
                        - <i>Ancrages</i> : 📚 D. Delignières (2020) et l'utilité vitale de l'EPS face à l'inactivité. 📚 A. Michel (2016) et l'apport de l'EPS aux domaines du Socle.<br>
                        - <i>Textes</i> : 📜 Programmes Collège 2015 (liaison Socle), 📜 Programmes Lycée 2019 (AFL autonomie).<br>
                        - <i>Terrain (Demi-fond / CA1)</i> : 🎯 Préparation au Bac. Classe inclusive où les dispensés gèrent les outils numériques de régulation. Évaluation indexée sur la capacité de l'élève à respecter à 0,5 km/h près le projet de course qu'il a lui-même planifié (AFL2). L'EPS produit des citoyens autonomes.
                        </li>
                        </ul>
                        """
                    }
                    
                    # Détection de l'année ciblée dans la question
                    annee_detectee = None
                    for annee in base_corrections_pierre.keys():
                        if annee in prompt_lower:
                            annee_detectee = annee
                            break
                    
                    # Rendu ultra-rapide et souverain
                    if annee_detectee:
                        extraits_doc = base_corrections_pierre[annee_detectee]
                    else:
                        # Recherche sémantique de secours si pas d'année écrite
                        for n in retriever_concours.retrieve(prompt + " Sujet Rapport Jury"):
                            extraits_doc += f"{n.node.text}\n\n"
                    
                    badge, color_card = "🏆 CONCOURS (AGREG / CAPEPS)", "peda-card"

                elif mode == "examens":
                    for n in retriever_santorin.retrieve(prompt): extraits_doc += f"Santorin/Examen: {n.node.text}\n\n"
                elif mode == "ipack":
                    for n in retriever_ipack.retrieve(prompt): extraits_doc += f"DOCUMENT OFFICIEL IPACKEPS : {n.node.text}\n\n"
                elif mode == "textes":
                    mot_cle_local = prompt.lower()
                    for exp in expressions_inutiles: mot_cle_local = mot_cle_local.replace(exp, "")
                    for n in retriever_textes.retrieve(mot_cle_local.strip()): extraits_doc += f"Cadre Réglementaire/Sécurité : {n.node.text}\n\n"
                elif mode == "peda":
                    if est_lycee:
                        for n in retriever_peda.retrieve(prompt + " AFL Lycée"):
                            extraits_doc += f"Référentiel Lycée (AFL) : {n.node.text}\n\n"
                    else:
                        for n in retriever_peda.retrieve(prompt + " Collège programmes 2015"):
                            extraits_doc += f"Base collège (Programme 2015) : {n.node.text}\n\n"
            except: 
                pass

        # 3. IDENTITÉ ET PERSONNALITÉ (FILTRE PIERRE CADRÉ)
        règles_or = "RÈGLES D'OR : 1. Loi 1937 (Substitution État). 2. Règle 11 (Structure=Mairie/EPI=Prof). 3. Examens = Mission impérative."
        filtre_pierre = (
            "\n\nMÉTHODE DE RÉPONSE EN 3 PARTIES OBLIGATOIRE (Le 'Filtre Pierre' Ultra-Scannable) :\n"
            "Tu dois STRICTEMENT structurer ta réponse finale selon le plan et les titres exacts suivants. "
            "Interdiction absolue de faire des paragraphes denses. Utilise un format aéré, percutant et très visuel :\n\n"
            "### 1. ANALYSE DES RISQUES\n"
            "- Utilise des listes à puces avec un émoji d'alerte (🛑, ⚠️ ou ⚖️) suivi d'un ancrage en gras qualifiant le risque.\n\n"
            "### 2. PROCÉDURE TECHNIQUE\n"
            "- Déroule les actions de terrain de manière chronologique.\n"
            "- Commence impérativement CHAQUE étape par une flèche '➔ Étape X (Titre court) : '.\n"
            "- Mets TOUJOURS en gras et entre crochets les boutons ou modules réels de l'interface logicielle.\n"
            "- S'il y a une interdiction absolue ou un point de sécurité critique, isole-le avec un émoji visible.\n\n"
            "### 3. PROTECTION FONCTIONNELLE\n"
            "- Utilise des listes à puces avec des émojis de dossiers/sécurité (📁, 🔓) suivis d'une notion forte en gras.\n\n"
            "Priorité maximale à la scannabilité graphique immédiate pour un professeur d'EPS."
        )
        if not est_demande_concours:
            badge = "INFORMATION"
            color_card = "general-card"

        consigne_commune_pierre = f"\n⚠️ SOURCE DE VÉRITÉ ABSOLUE INTERNE (Priorité Maximale) :\n{verites_terrain_pierre}\n\n"

        # ======================================================================
        # 4. EXÉCUTION ET RENDU HTML (ADOUCI CONTRE LE VERROU COPYRIGHT)
        # ======================================================================
        if est_demande_concours:
            consigne_ia_concours = (
                f"Tu es l'inspecteur d'académie expert. Prends les notes de synthèse de terrain fournies ci-dessous "
                f"et mets-les en valeur en appliquant le formatage HTML requis pour le tableau de bord "
                f"(utilise uniquement <h3> pour les grands titres, <br> pour aérer, et <ul> / <li> pour les listes d'arguments. Aucun paragraphe dense, pas de markdown).\n"
                f"Restitue l'ensemble des concepts didactiques, des auteurs et des exemples d'APSA présents dans le document.\n\n"
                f"Notes à intégrer : {extraits_doc}"
            )
            response = Settings.llm.complete(consigne_ia_concours)
        else:
            response = Settings.llm.complete(consigne_ia)
            
        texte_brut = response.text
        
        texte_brut = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">\1</a>', texte_brut)
        
        youtube_links = re.findall(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11}))', texte_brut)

        # Rendu différencié pour isoler le concours du nettoyage agressif du texte final
        if est_demande_concours:
            texte_final = texte_brut.replace(chr(10), "<br>")
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_final}</div>'
        elif mode == "peda":
            texte_final = texte_brut.replace("\n", "").replace("\r", "").replace("<p>", "").replace("</p>", "<br>")
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br>{texte_final}</div>'
        else:
            texte_final = texte_brut.replace(chr(10), "<br>")
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_final}</div>'
            
        st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
        
        for link in youtube_links:
            st.session_state.messages_hub.append({"role": "assistant", "content": f"st.video('{link[0]}')"})
        st.rerun()
