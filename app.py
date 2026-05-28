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
# 9. FLUX DE MESSAGES ET TRAITEMENT IA (CONSOLIDATION FINALE ET SÉCURISÉE)
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
        est_lycee = any(x in prompt_lower for x in ["lycée", "lycee", "bac", "terminale", "première", "premiere", "seconde", "cap", "bac pro"])
        
        expressions_inutiles = [
            "je cherche un texte officiel pour savoir si", "je cherche un texte sur le", 
            "je cherche un texte sur la", "je cherche un texte sur", "pour savoir si j'ai le droit de",
            "est-ce que j'ai le droit de", "ai-je le droit de", "est-ce qu'il existe un texte",
            "trouve moi le texte sur", "trouve moi une circulaire sur", "trouve moi", 
            "recherche le texte sur", "texte officiel sur", "circulaire concernant", "circulaire sur"
        ]
        
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
                    mot_cle = prompt_lower
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
                    base_corrections_pierre = {
                        "agreg_2025_ecrit1": """
                        <h3>BIBLIOTHÈQUE CONCOURS - CORRECTION AGRÉGATION INTERNE 2025 (ÉCRIT 1)</h3>
                        <strong>Sujet : De 1967 à nos jours, comment l’Éducation Physique et Sportive a-t-elle concilié l’impératif de sécurité des élèves et la recherche d’une motricité audacieuse et performante ?</strong><br><br>
                        <h3>1. DÉCODAGE DE LA TENSION DIALECTIQUE</h3>La tension réside dans le fait que l'EPS a dû prouver qu'elle pouvait scolariser le risque sportif sans éteindre l'engagement moteur. La sécurité n'est pas le frein de l'audace, mais sa condition de possibilité.<br><br>
                        <h3>2. PROBLÉMATIQUE DE COPIE MAJORE</h3>L'EPS est passée d'une sécurité passive et externalisée (prise en charge par l'enseignant) à une sécurité active et partagée (internalisée par l'élève via des rôles sociaux), faisant de la gestion du risque un objet d'enseignement pour libérer l'audace.<br><br>
                        <h3>3. DÉROULEMENT DU PLAN</h3>
                        <ul>
                        <li><strong>PARTIE I (1967-1970) :</strong> Sécurité externe. 📚 B. Jeu (1977). 🎯 Gymnastique où le prof parade physiquement au saut de cheval. Sécurité passive.</li>
                        <li><strong>PARTIE II (1980-1990) :</strong> Sécurité active. 📚 J.P. Dégal (1994). 🎯 Escalade en CA2 où les pairs gèrent le nœud de huit et l'assurage en 5 temps.</li>
                        <li><strong>PARTIE III (2000-2026) :</strong> Engagement lucide. 📚 D. Delignières (2019). 🎯 Acrosport en CA3 où la note collective intègre la rigueur du pareur actif (AFL3).</li>
                        </ul>
                        """,
                        
                        "agreg_2025_ecrit2": """
                        <h3>BIBLIOTHÈQUE CONCOURS - CORRECTION AGRÉGATION INTERNE 2025 (ÉCRIT 2)</h3>
                        <strong>Sujet : En quoi la diversité des parcours de formation des élèves en EPS (du cycle 3 au lycée) interroge-t-elle la conception des projets de cycle et le choix des situations d'apprentissage ?</strong><br><br>
                        <h3>1. DÉGAGEAGE DE LA TENSION DIALECTIQUE</h3>Assurer une transformation motrice commune et évaluable tout en gérant la discontinuité des parcours réels.<br><br>
                        <h3>2. PROBLÉMATIQUE DE COPIE MAJORE</h3>La diversité des parcours constitue le moteur d'une rationalisation didactique de l'EPS. Du cycle 3 au lycée, elle impose de concevoir des projets de cycle centrés sur des profils de transformation prioritaires.<br><br>
                        <h3>3. DÉROULEMENT DU PLAN</h3>
                        <ul>
                        <li><strong>PARTIE I :</strong> Liaison Cycle 3. 📚 J. Horoks (2018). 🎯 Volley avec option ballon bloqué pour les novices.</li>
                        <li><strong>PARTIE II :</strong> Autonomie au Lycée. 📚 D. Delignières (2019). 🎯 Musculation en CA5 régulée à l'indice RPE de Borg.</li>
                        <li><strong>PARTIE III :</strong> Parcours singuliers. 📚 É. Dugas (2004). 🎯 CO en 'O-Précision' pour inclure un élève inapte moteur.</li>
                        </ul>
                        """,
                        
                        "capeps_2025": """
                        <h3>BIBLIOTHÈQUE CONCOURS - CORRECTION CAPEPS EXTERNE 2025 (ÉCRIT 1)</h3>
                        <strong>Sujet : La prise en compte de la diversité culturelle et sociale des élèves dans l'histoire de l'EPS de 1967 à nos jours.</strong><br><br>
                        <h3>1. DÉGAGEAGE DE LA TENSION DIALECTIQUE</h3>Opposition entre l'uniformisation par le sport d'élite (IO 1967) et l'obligation de différencier pour l'équité (Socle commun).<br><br>
                        <h3>2. PROBLÉMATIQUE DE COPIE MAJORE</h3>L'EPS est passée d'une acculturation sportive uniformisante à une inclusion équitable valorisant la diversité comme richesse.<br><br>
                        <h3>3. DÉROULEMENT DU PLAN</h3>
                        <ul>
                        <li><strong>PARTIE I (1967-1970) :</strong> Illusion universaliste. 📚 P. Arnaud (1983). 🎯 Gymnastique notée sur le code de pointage rigide.</li>
                        <li><strong>PARTIE II (1980-1990) :</strong> Formes de pratiques scolaires. 📚 J. Marsenach (1991). 🎯 Rugby/Volley en ZEP avec règles adoucies.</li>
                        <li><strong>PARTIE III (2000-2026) :</strong> Justice sociale. 📚 Y. Combaz (2010). 🎯 Danse en Lycée Pro notée sur la composition artistique (AFL2) et le rôle de spectateur (AFL3).</li>
                        </ul>
                        """,
                        
                        "capeps_2023": """
                        <h3>BIBLIOTHÈQUE CONCOURS - CORRECTION CAPEPS EXTERNE 2023 (ÉCRIT 1)</h3>
                        <strong>Sujet : Sa légitimité institutionnelle au sein du système éducatif de 1981 à nos jours.</strong><br><br>
                        <h3>3. DÉROULEMENT DU PLAN</h3>
                        <ul>
                        <li><strong>PARTIE I (1981-1990) :</strong> 📚 J. Marsenach (1991). 🎯 Volley-ball didactisé.</li>
                        <li><strong>PARTIE II (1990-2000) :</strong> 📚 Y. Combaz (2010). 🎯 Course d'orientation au Bac (CCF).</li>
                        <li><strong>PARTIE III (2010-2026) :</strong> 📚 D. Delignières (2020). 🎯 Demi-fond synchrone AFL2.</li>
                        </ul>
                        """,
                        
                        "agreg_2022": """
                        <h3>BIBLIOTHÈQUE CONCOURS - CORRECTION AGRÉGATION INTERNE 2022 (ÉCRIT 1)</h3>
                        <strong>Sujet : L’Éducation Physique et Sportive face aux enjeux de santé publique de 1967 à nos jours.</strong><br><br>
                        <h3>3. DÉROULEMENT DU PLAN</h3>
                        <ul>
                        <li><strong>PARTIE I (1967-1970) :</strong> 📚 J. Pineau (1990). 🎯 Test du Cooper subit au sifflet.</li>
                        <li><strong>PARTIE II (1980-1990) :</strong> 📚 A. Hébrard (1986). 🎯 Table de VMA et pulsations carotides.</li>
                        <li><strong>PARTIE III (2000-2026) :</strong> 📚 D. Delignières (2019). 🎯 Musculation en CA5 et régulation Borg.</li>
                        </ul>
                        """
                    }
                    
                    cle_cible = None
                    if "2025" in prompt_lower:
                        if "capeps" in prompt_lower:
                            cle_cible = "capeps_2025"
                        else:
                            cle_cible = "agreg_2025_ecrit1" if "ecrit 1" in prompt_lower or "écrit 1" in prompt_lower else "agreg_2025_ecrit2"
                    elif "2023" in prompt_lower:
                        cle_cible = "capeps_2023"
                    elif "2022" in prompt_lower:
                        cle_cible = "agreg_2022"
                    
                    if cle_cible and cle_cible in base_corrections_pierre:
                        extraits_doc = base_corrections_pierre[cle_cible]
                    else:
                        for n in retriever_concours.retrieve(prompt + " Sujet Rapport Jury"):
                            extraits_doc += f"{n.node.text}\n\n"
                    
                    badge, color_card = "🏆 CONCOURS (AGREG / CAPEPS)", "peda-card"

                elif mode == "examens":
                    for n in retriever_santorin.retrieve(prompt): extraits_doc += f"Santorin/Examen: {n.node.text}\n\n"
                elif mode == "ipack":
                    for n in retriever_ipack.retrieve(prompt): extraits_doc += f"DOCUMENT OFFICIEL IPACKEPS : {n.node.text}\n\n"
                elif mode == "textes":
                    mot_cle_local = prompt_lower
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

        # ======================================================================
        # 3. IDENTITÉ ET PERSONNALITÉ (RESTAURATION DE TOUTE LA LOGIQUE INTERNE)
        # ======================================================================
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
        
        consigne_commune_pierre = f"\n⚠️ SOURCE DE VÉRITÉ ABSOLUE INTERNE (Priorité Maximale) :\n{verites_terrain_pierre}\n\n"

        # RECONSTRUCTION DES TEMPLATES INDIVIDUELS CONGÉDIÉS PAR ERREUR
        if not est_demande_concours:
            if mode == "ipack":
                liens_utiles = {
                    "rubrique2": "- [📥 Ouvrir la rubrique 2 de documentation (Structures / EDT) sur iPackEPS](https://ipackeps.ac-creteil.fr/spip.php?rubrique2)",
                    "rubrique4": "- [📥 Ouvrir la rubrique 4 de documentation (Notes / Inaptitudes) sur iPackEPS](https://ipackeps.ac-creteil.fr/spip.php?rubrique4)",
                    "rubrique7": "- [📥 Ouvrir la rubrique 7 de documentation (Examens / CCF) sur iPackEPS](https://ipackeps.ac-creteil.fr/spip.php?rubrique7)",
                    "video_inapt": "- [🎥 Cliquer ici pour voir le tutoriel vidéo : Déclaration / Suivi des inaptitudes](https://youtu.be/34w4Z6dd1dM)",
                    "video_import": "- [🎥 Cliquer ici pour voir le tutoriel vidéo : Import d'élèves depuis Pronote](https://youtu.be/RlScDjd8kHk)",
                    "video_proto": "- [🎥 Cliquer ici pour voir le tutoriel vidéo : Configuration et Gestion des Protocoles](https://youtu.be/Bq7_ooQuZtU)"
                }
                liens_selectionnes = []
                if any(x in prompt_lower for x in ["cap", "bac", "examen", "ccf", "protocole", "épreuve", "supprimer", "effacer", "retirer", "groupe", "répartir", "affecte"]):
                    liens_selectionnes.extend([liens_utiles["video_proto"], liens_utiles["rubrique7"]])
                elif any(x in prompt_lower for x in ["import", "xml", "pronote", "doublon", "classe", "nouvel élève", "introuvable", "manuellement", "ajouter un élève"]):
                    liens_selectionnes.extend([liens_utiles["video_import"], liens_utiles["rubrique2"]])
                elif any(x in prompt_lower for x in ["inapte", "dispense", "bless", "note", "bloqu", "certificat", "médical", "cm"]):
                    liens_selectionnes.extend([liens_utiles["video_inapt"], liens_utiles["rubrique4"]])
                else:
                    liens_selectionnes.extend([liens_utiles["rubrique4"], liens_utiles["rubrique7"]])
                
                bloc_liens_dynamique = "\n".join(liens_selectionnes)
                
                consigne_ia = (
                    f"{règles_or}{filtre_pierre}{consigne_commune_pierre}\n"
                    "ROLE : Tu es l'expert informatique iPackEPS. Tu es un moteur d'extraction strict et froid. Tu n'inventes RIEN.\n\n"
                    "STRUCTURE DE RÉPONSE NON NÉGOCIABLE :\n"
                    "### 1. ANALYSE DES RISQUES INFRA / TECHNIQUE\n"
                    "### 2. PROCÉDURE TECHNIQUE DE RÉSOLUTION\n"
                    "### 3. SOURCES, ARTICLES ET TUTORIELS ÉDITEUR\n\n"
                    "🛑 CONSIGNES DE SÉCURITÉ DE RÉDACTION ET RÈGLES INTERNES :\n"
                    "1. INTERDICTION ABSOLUE d'inventer des boutons de création manuelle d'élèves.\n"
                    "2. Pour la section 3, copie-coller STRICTEMENT le bloc de liens fourni ci-dessous.\n\n"
                    f"🎯 BLOC DE LIENS OFFICIELS À COPIER-COLLER EN SECTION 3 :\n{bloc_liens_dynamique}\n\n"
                    f"Contexte RAG : {extraits_doc}\nQuestion du professeur : {prompt}"
                )
                badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

            elif mode == "examens":
                liens_utiles = {
                    "webinaire_eps": "- [📥 Télécharger le Webinaire Officiel IA-IPR (Guide pas-à-pas Santorin EPS Aix-Marseille)](https://www.pedagogie.ac-aix-marseille.fr/upload/docs/application/pdf/2024-03/webinaire_utilisation_de_santorin.pdf)",
                    "portail_santorin": "- [🌐 Accéder au Portail d'assistance et Fiches Mémo Santorin Académique](https://www.ac-aix-marseille.fr/santorin)",
                    "base_ecole": "- [🧪 Accéder à la Base École Santorin (Plateforme officielle de simulation)](https://santorin-ecole.phm.education.gouv.fr/inscription/correcteur)"
                }
                liens_selectionnes = []
                if any(x in prompt_lower for x in ["simul", "entraîn", "test", "école", "faux", "s'exercer"]):
                    liens_selectionnes.extend([liens_utiles["base_ecole"], liens_utiles["webinaire_eps"]])
                elif any(x in prompt_lower for x in ["absent", "dispense", "inapte", "neutralis", "substitution", "bless", "aflp"]):
                    liens_selectionnes.extend([liens_utiles["webinaire_eps"], liens_utiles["portail_santorin"]])
                else:
                    liens_selectionnes.extend([liens_utiles["webinaire_eps"], liens_utiles["portail_santorin"]])
                
                bloc_liens_dynamique = "\n".join(liens_selectionnes)
                
                consigne_ia = (
                    f"{règles_or}{filtre_pierre}{consigne_commune_pierre}\n"
                    "ROLE : Expert certificateur EPS (Examens, CCF, Santorin, Cyclades). Tu es un moteur d'extraction strict et froid.\n\n"
                    "STRUCTURE DE RÉPONSE NON NÉGOCIABLE :\n"
                    "### 1. ANALYSE DES RISQUES\n"
                    "### 2. PROCÉDURE TECHNIQUE\n"
                    "### 3. CADRE OFFICIEL ET RECOMMANDATIONS\n\n"
                    "🛑 CONSIGNES DE SÉCURITÉ DE RÉDACTION AND VERROUS ABSOLUS :\n"
                    "1. DATE LIMITE SANTORIN 2026 : Rappelle obligatoirement que la date limite absolue de saisie des notes dans Santorin pour la session 2026 est fixée au 30 mai 2026 au soir.\n"
                    "2. INTERDICTION D'ALERTES DE SÉCURITÉ : Pas de sous-titres 'ALERTE SÉCURITÉ'.\n\n"
                    f"🎯 BLOC DE LIENS OFFICIELS À COPIER-COLLER EN SECTION 3 :\n{bloc_liens_dynamique}\n\n"
                    f"Contexte RAG : {extraits_doc}\nQuestion du professeur : {prompt}"
                )
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

           elif mode == "textes":
                    mot_cle_local = prompt.lower()
                    for exp in expressions_inutiles: mot_cle_local = mot_cle_local.replace(exp, "")
                    
                    # BIEN JOUNÉ : Blindage chirurgical pour le cas des ASA de l'Enseignant-Élu
                    if any(x in prompt_lower for x in ["tasa", "asa", "autorisation speciale", "absence elu"]):
                        extraits_doc = """
                        <h3>CADRE RÉGLEMENTAIRE - AUTORISATIONS SPÉCIALES D'ABSENCE (ASA) ENSEIGNANT-ÉLU</h3>
                        <strong>Bénéficiaire : Fonctionnaire de l'État exerçant un mandat de Conseiller Municipal (Loi CGCT).</strong><br><br>
                        
                        <h3>1. DROITS AUX ASA ET PLAFOND TRIMESTRIEL</h3>
                        <ul>
                        <li><strong>Articles L. 2123-1 Il et suivants du CGCT :</strong> Le conseiller municipal qui n'en bénéficie pas au titre de ses fonctions exécutives a droit à un crédit d'heures forfaitaire trimestriel pour l'exercice de son mandat (calculé selon la taille de la commune, ex: Gargas).</li>
                        <li><strong>Droit d'absence pour séances plénières :</strong> L'administration est tenue de laisser le temps nécessaire à l'élu pour assister aux conseils municipaux et aux réunions des commissions officielles dont il est membre (sur présentation de la convocation officielle).</li>
                        </ul>
                        
                        <h3>2. LE VERROU DE LA NÉCESSITÉ DE SERVICE</h3>
                        <ul>
                        <li><strong>Arbitrage Rectorat / Chef d'établissement :</strong> Contrairement aux décharges de droit, l'octroi d'une ASA reste soumis à la réserve réglementaire des <strong>nécessités de service</strong> (continuité des cours d'EPS, sécurité des élèves). L'administration peut motiver un refus si l'absence désorganise gravement le service.</li>
                        <li><strong>Décompte et compensation :</strong> Les heures d'absences liées aux ASA ne sont pas rémunérées et ne donnent pas lieu à récupération systématique, sauf accord spécifique ou aménagement d'emploi du temps validé par le Chef d'établissement.</li>
                        </ul>
                        
                        <h3>3. PROTECTION JURIDIQUE ET PROTOCOLE DE SÉCURITÉ</h3>
                        <ul>
                        <li>📁 <strong>Traçabilité administrative :</strong> Le professeur doit déposer sa demande d'ASA accompagnée de sa convocation officielle au moins <strong>8 jours à l'avance</strong> via le secrétariat de direction.</li>
                        <li>🔓 <strong>Couverture en cas de sinistre :</strong> Dès lors que l'ASA est accordée par le Recteur ou le Chef d'établissement par délégation, l'absence est dite "régulière". L'enseignant est couvert administrativement dans ses déplacements liés au mandat.</li>
                        </ul>
                        """
                    else:
                        # Si ce n'est pas une question d'ASA, le RAG classique fouille tes fichiers textes sécurité
                        for n in retriever_textes.retrieve(mot_cle_local.strip()): 
                            extraits_doc += f"Cadre Réglementaire/Sécurité : {n.node.text}\n\n"
                            
                    consigne_ia = (
                        f"{règles_or}{filtre_pierre}{consigne_commune_pierre}\n"
                        "ROLE : Tu es l'expert juridique du Code de l'Éducation. Tu structures et mets en valeur les notes ci-dessous.\n"
                        "FORMATAGE : Utilise uniquement des <h3> pour les titres, <br> pour aérer et les listes <ul> / <li>. Aucun dièse (#).\n\n"
                        f"Contexte Juridique Local : {extraits_doc}\nQuestion : {prompt}"
                    )
                    badge, color_card = "⚖️ TEXTES OFFICIELS", "general-card"

            elif mode == "peda":
                niveau_affiche = "Lycée (Baccalauréat / CAP)" if est_lycee else "Cycle 4 (Collège)"
                label_attendu = "Attendus de Fin de Lycée (AFL 1, 2, 3)" if est_lycee else "Attendus de Fin de Cycle 4 (AFC)"
                label_competence = "Compétences d'Échauffement et d'Entraînement" if est_lycee else "Compétences visées pendant le cycle"

                ca_nom = "CA1 (Performance optimale)"
                if est_lycee:
                    ca_attendus = "AFL 1 (Moteur) : Produire la meilleure performance possible à une échéance donnée. Choisir et combiner des techniques efficaces, réguler l'allure et stabiliser les appuis.<br>AFL 2 (Méthodologique) : Choisir, concevoir et conduire un engagement corporel pour s'engager dans un programme de préparation ou d'entraînement.<br>AFL 3 (Social) : Assumer de manière autonome les rôles de juge, de starter et de chronométreur officiel. Respecter le protocole de mesure."
                    ca_competences = "Concevoir et stabiliser des techniques efficaces. Planifier et réguler sa charge d'entraînement. Gérer la pression de la mesure officielle."
                else:
                    ca_attendus = "Produire une performance optimale, mesurable à une échéance donnée. Réaliser des efforts et enchaîner plusieurs actions motrices dans différentes familles pour aller plus vite, plus longtemps, plus haut, plus loin. Assumer les rôles sociaux."
                    ca_competences = "Gérer ses ressources pour produire la meilleure performance possible. Se préparer, planifier et s'entraîner individuellement ou collectivement."
                
                if any(x in prompt_lower for x in ["volley", "basket", "hand", "foot", "rugby", "badminton", "tennis", "ping", "boxe", "lutte", "combat"]):
                    ca_nom = "CA4 (Affrontement collectif ou interindividuel)"
                    if est_lycee:
                        ca_attendus = "AFL 1 (Moteur) : En situation d'opposition, réaliser des actions décisives en situation favorable pour faire basculer le rapport de force.<br>AFL 2 (Méthodologique) : Observer, recueillir des données et ajuster son projet en temps réel.<br>AFL 3 (Social) : Co-arbitrer de manière rigoureuse, respecter scrupuleusement les partenaires."
                        ca_competences = "Construire un jeu d'intention. Maîtriser le changement de statut attaquant/défenseur."
                    else:
                        ca_attendus = "En situation d'opposition réelle et équilibrée, réaliser des actions décisives en situation favorable pour faire basculer le rapport de force."
                        ca_competences = "Rechercher le gain de la rencontre par un projet prenant en compte le rapport de force."
                elif any(x in prompt_lower for x in ["gym", "acro", "danse", "step", "cirque"]):
                    ca_nom = "CA3 (Prestation corporelle artistique ou acrobatique)"
                    if est_lycee:
                        ca_attendus = "AFL 1 (Moteur) : Composer et interpréter une séquence corporelle de haute maîtrise devant un public.<br>AFL 2 (Méthodologique) : Utiliser des procédés de composition complexes.<br>AFL 3 (Social) : Assumer un jugement argumenté, tenir le rôle de pareur."
                        ca_competences = "Stabiliser des formes corporelles complexes. Maîtriser les risques."
                    else:
                        ca_attendus = "Mobiliser ses capacités expressives et acrobatiques pour imaginer, composer et interpréter une séquence corporelle devant un public."
                        ca_competences = "Élaborer et réaliser un projet pour provoquer une émotion."
                elif any(x in prompt_lower for x in ["muscu", "step", "fitness", "entretien", "ressources", "ca5"]):
                    ca_nom = "CA5 (Développement de soi et entretien de la santé)"
                    ca_attendus = "AFL 1 (Moteur) : Produire et enchaîner des formes de travail adaptées.<br>AFL 2 (Méthodologique) : Concevoir, réguler et ajuster sa charge de travail (RPE/Borg).<br>AFL 3 (Social) : Assumer les rôles de partenaire d'entraînement."
                    ca_competences = "Identifier ses limites et mobiles. Maîtriser les postures de sécurité."    
                elif any(x in prompt_lower for x in ["escalade", "orientation", " co ", "vtt", "kayak", "randonnée"]):
                    ca_nom = "CA2 (Environnements variés)"
                    if est_lycee:
                        ca_attendus = "AFL 1 (Moteur) : Conduire un déplacement optimisé, fluide et adapté.<br>AFL 2 (Méthodologique) : Prévoir, gérer l'itinéraire, le matériel de sécurité.<br>AFL 3 (Social) : Assurer la sécurité absolue de son partenaire."
                        ca_competences = "Maîtriser les techniques de réchappe et d'assurage dynamique."
                    else:
                        ca_attendus = "Réussir un déplacement planifié dans un milieu naturel ou recréé. Gérer ses ressources."
                        ca_competences = "Choisir et conduire un déplacement adapté. Évaluer les risques."

                consigne_ia = (
                    f"ROLE : Tu es un expert pédagogique de haut niveau en EPS (IA-IPR). Tu es rigoureux et factuel.\n"
                    f"Tu rédiges une fiche de cycle complète pour le niveau : {niveau_affiche}.\n"
                    f"CHAMP CIBLÉ : {ca_nom}\n"
                    f"TEXTE OFFICIEL À INJECTER : {ca_attendus}\n"
                    f"COMPÉTENCES À INJECTER : {ca_competences}\n\n"
                    "🎯 DIRECTIVES DE RÉDACTION IMPÉRATIVES :\n"
                    "1. Dans la section 'ANCRAGE INSTITUTIONNEL', affiche textuellement le texte officiel fourni ci-dessus sans modifier une seule virgule.\n"
                    "2. Dans la section 'SITUATIONS D'APPRENTISSAGE', adapte la complexité au niveau demandé.\n"
                    "3. Dans la section 'CRITÈRES D'ÉVALUATION', propose un barème chiffré sur 20 points.\n"
                    "4. Dans la section 'PROGRESSION CHRONOLOGIQUE', planifie une programmation cohérente séance par séance de la séance 1 à la séance 8.\n\n"
                    "FORMATAGE HTML STRICT ET OBLIGATOIRE (Interdiction absolue de Markdown) :\n"
                    "Utilise uniquement <h3> pour les titres, <br> pour aérer, et les balises <ul> / <li> pour les listes.\n\n"
                    "RÈGLE DES LIENS RECHERCHE DYNAMIQUES :\n"
                    "Génère obligatoirement les 4 liens HTML exacts ci-dessous (NOM_APSA en minuscules, DOMAINE1 à remplacer par un vrai serveur académique).\n"
                    "1. <a href='https://edubase.eduscol.education.fr/recherche?q=NOM_APSA' target='_blank'>📥 Fiche NOM_APSA - Base Nationale ÉDUBASE EPS</a><br>\n"
                    "2. <a href='https://www.google.com/search?q=site:pedagogie.ac-aix-marseille.fr+conservatoire+NOM_APSA' target='_blank'>🎥 NOM_APSA - Banque de vidéos et fiches du Conservatoire EPS Aix-Marseille</a><br>\n"
                    "3. <a href='https://www.google.com/search?q=site:DOMAINE1+NOM_APSA+fiche+evaluation+EPS' target='_blank'>📥 Fiche NOM_APSA - Fiches d'évaluation Académie de [Nom1]</a><br>\n"
                    "4. <a href='https://www.google.com/search?q=site:pedagogie.ac-aix-marseille.fr+NOM_APSA+projet+cycle' target='_blank'>🌐 NOM_APSA - Projets de cycle homologués Aix-Marseille</a><br>\n\n"
                    "STRUCTURE DU RENDU FINAL SÉQUENCÉ :\n"
                    "<h3>📋 INTITULÉ DE LA FICHE D'ÉVALUATION PRÊTE À L'EMPLOI</h3>"
                    f"<strong>Activité : [Nom] | Champ d'Apprentissage ({ca_nom.split(' ')[0]}) | Niveau : {niveau_affiche}</strong><br><br>"
                    "<h3>🌐 ANCRAGE INSTITUTIONNEL</h3>"
                    "<ul>"
                    f"<li><strong>{label_attendu} :</strong><br>" + ca_attendus + "</li>"
                    f"<li><strong>{label_competence} :</strong><br>" + ca_competences + "</li>"
                    "</ul>"
                    "<h3>🎯 OBJECTIFS PÉDAGOGIQUES DE LA SÉQUENCE</h3><ul><li>[Intentions tactiques et transformations motrices]</li></ul>"
                    "<h3>🏃‍♂️ CADRE SÉCURITÉ & AMÉNAGEMENT DU TERRAIN</h3><ul><li>[Consignes de sécurité passive et active]</li></ul>"
                    "<h3>🛠️ SITUATIONS D'APPRENTISSAGE ET DE TEST PROTOCOLÉE</h3>"
                    "<ul>"
                    "<li><strong>Dispositif et aménagement du milieu :</strong> [Description]</li>"
                    "<li><strong>Règles du jeu et score parlant :</strong> [Consignes]</li>"
                    "<li><strong>Ciblage des compétences :</strong> [Détailler comment la situation valide les AFL ou domaines ciblés]</li>"
                    "</ul>"
                    "<h3>📅 PROGRESSION CHRONOLOGIQUE DU CYCLE (6 À 8 SÉANCES)</h3>"
                    "<ul><li>[Progression détaillée de la séance 1 à la séance 8]</li></ul>"
                    "<h3>📊 CRITÈRES D'ÉVALUATION ET GRILLE DE NOTATION NUMÉRIQUE (/20)</h3>"
                    "<ul><li>[Découpage chiffré précis et observables de terrain]</li></ul>"
                    "<h3><h3>💾 BANQUE DE RESSOURCES NUMÉRIQUES ET VIDEOS</h3>"
                    "(Insère ici les 4 liens HTML générés dynamiquement, aucun texte brut passif autorisé)<br>"
                    f"\nContexte RAG : {extraits_doc}\nQuestion du professeur : {prompt}"
                )
                badge, color_card = "🎓 PÉDAGOGIE EPS", "peda-card"

        # ======================================================================
        # 4. EXÉCUTION ET RENDU HTML (REMASTÉRISÉ SANS CONFLIT DE VARIABLE)
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
