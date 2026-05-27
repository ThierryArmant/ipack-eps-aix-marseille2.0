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
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
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
            La correction partagée ou multiple permits à plusieurs évaluateurs/correcteurs d'intervenir sur un même lot de copies. 
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
    
    with st.spinner("Je recherche les documents et ressources pédagogiques..."):
        extraits_doc = ""
        mode = st.session_state.active_module
        
        mots_terrain = ["fiche", "evaluation", "évaluation", "grille", "bareme", "barème", "cycle", "seance", "séance", "apsa", "volley", "hand", "basket", "badminton", "relais", "natation", "escalade", "gym", "college", "collège"]
        est_demande_fiche = any(mot in prompt.lower() for mot in mots_terrain)
        
        verites_terrain_pierre = ""
        try:
            for fichier in os.listdir("."):
                if fichier.endswith((".txt", ".md")) and "pierre" in fichier.lower():
                    with open(fichier, "r", encoding="utf-8") as f:
                        verites_terrain_pierre += f"\n--- REGLES DIRECTES ({fichier}) ---\n" + f.read() + "\n"
        except:
            pass
        
        # 1. MOTEUR WEB (Tavily)
        if tavily_api_key:
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
                    requete_blindee = f"site:ipackeps.ac-creteil.fr/spip.php?rubrique4 {prompt}"
                    domains = ["ipackeps.ac-creteil.fr"]
                    exclude = ["youtube.com"]
                
                elif mode == "peda":
                    requete_blindee = f"{prompt} évaluation fiche filetype:pdf"
                    domains = domaine_eps_france
                
                elif est_demande_fiche:
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

        # 2. CONTEXTE LOCAL
        if openai_api_key:
            try:
                if mode == "examens":
                    for n in retriever_santorin.retrieve(prompt): extraits_doc += f"Santorin/Examen: {n.node.text}\n\n"
                elif mode == "ipack":
                    for n in retriever_ipack.retrieve(prompt): extraits_doc += f"DOCUMENT OFFICIEL IPACKEPS : {n.node.text}\n\n"
                elif mode == "textes":
                    for n in retriever_textes.retrieve(prompt): extraits_doc += f"Cadre Réglementaire/Sécurité : {n.node.text}\n\n"
                elif mode == "peda":
                    for n in retriever_peda.retrieve(prompt): extraits_doc += f"Ma base pédagogique (Fiche/Éval) : {n.node.text}\n\n"
            except: pass

        # 3. IDENTITÉ ET PERSONNALITÉ (FILTRE PIERRE CADRÉ)
        règles_or = "RÈGLES D'OR : 1. Loi 1937 (Substitution État). 2. Règle 11 (Structure=Mairie/EPI=Prof). 3. Examens = Mission impérative."
        filtre_pierre = (
            "\n\nMÉTHODE DE RÉPONSE EN 3 PARTIES OBLIGATOIRE (Le 'Filtre Pierre' Ultra-Scannable) :\n"
            "Tu dois STRICTEMENT structurer ta réponse finale selon le plan et les titres exacts suivants. "
            "Interdiction absolue de faire des paragraphes denses. Utilise un format aéré, percutant et très visuel :\n\n"
            "### 1. ANALYSE DES RISQUES\n"
            "- Utilise des listes à puces avec un émoji d'alerte (🛑, ⚠️ ou ⚖️) suivi d'un ancrage en gras qualifiant le risque (ex: 🛑 **Bloquer l'export d'examen** : explications).\n\n"
            "### 2. PROCÉDURE TECHNIQUE\n"
            "- Déroule les actions de terrain de manière chronologique.\n"
            "- Commence impérativement CHAQUE étape par une flèche '➔ Étape X (Titre court) : '.\n"
            "- Mets TOUJOURS en gras et entre crochets les boutons ou modules réels de l'interface logicielle (ex: **[Mes Élèves]**, **[Saisir une inaptitude]**).\n"
            "- S'il y a une interdiction absolue ou un point de sécurité critique, isole-le avec un émoji visible (ex: ⚠️ **ALERTE SÉCURITÉ** : ...).\n\n"
            "### 3. PROTECTION FONCTIONNELLE\n"
            "- Utilise des listes à puces avec des émojis de dossiers/sécurité (📁, 🔓) suivis d'une notion forte en gras (ex: 📁 **Traçabilité** : rappel de la couverture juridique).\n\n"
            "Priorité maximale à la scannabilité graphique immédiate pour un professeur d'EPS."
        )
        badge = "INFORMATION"
        color_card = "general-card"
        
        if mode == "ipack":
            consigne_ia = (
                f"{règles_or}{filtre_pierre}\n"
                "ROLE : Tu es l'expert informatique et technique iPackEPS pour l'académie d'Aix-Marseille. Tu exclus tout blabla pédagogique.\n"
                f"CONSIGNES INTERNES PRIORITAIRES (À LIRE ET APPLIQUER ABSOLUMENT) :\n{verites_terrain_pierre}\n\n"
                
                "🧠 EXTRACTION ET LIEN CHIRURGICAL DIRECT :\n"
                "1. Scanne le 'Contexte' pour trouver le TITRE EXACT du paragraphe écrit par l'utilisateur (ex: 'Sélection de votre établissement' ou 'Choix de l’année scolaire').\n"
                "2. À la fin de ta réponse, sous le titre '### 3. PROTECTION FONCTIONNELLE', tu as l'obligation stricte de générer un lien ultra-précis qui va faire défiler la page du navigateur directement sur ce titre.\n"
                "3. Formate le lien de conclusion EXACTEMENT selon ces modèles en remplaçant 'TITRE_NETTOYÉ' par le titre trouvé où chaque espace est remplacé par %20 (ex: Sélection%20de%20votre%20établissement) :\n"
                "   - Pour un sujet de début d'année/connexion : [📥 Cliquer ici pour ouvrir l'article exact sur iPackEPS](https://ipackeps.ac-creteil.fr/spip.php?rubrique2#:~:text=TITRE_NETTOYÉ)\n"
                "   - Pour un sujet de gestion de classes/APSA/évaluations : [📥 Cliquer ici pour ouvrir l'article exact sur iPackEPS](https://ipackeps.ac-creteil.fr/spip.php?rubrique4#:~:text=TITRE_NETTOYÉ)\n\n"
                
                "CRITICAL IPACK RULES:\n"
                "- SAISIE INAPTITUDE : Interdiction absolue de taper 'IN' ou 'DI' dans les cases de notes. Passage obligatoire par 'Gestion/Suivi des élèves' > 'Fiche élève' > 'Saisir une inaptitude'.\n"
                "- DEMI-FOND BAC GT : Distinction obligatoire entre l'épreuve nationale 'Courses' et l'activité d'établissement 'Course de demi-fond'. Interdiction stricte de créer des protocoles à 2 épreuves, le protocole Bac GT doit rester réglementaire.\n"
                "- SUPPRESSION DE PROTOCOLE : Le bouton 'Supprimer' direct n'existe pas dans l'onglet Protocoles. Pour faire disparaître un protocole, il faut obligatoirement supprimer ou désaffecter les Groupes et les séquences d'apprentissage qui lui sont rattachés en amont.\n"
                "- RÉPARTITION DANS LES GROUPES : L'action se fait exclusivement via le module 'Mes élèves'. Attention, l'option textuelle 'Placement des élèves dans les groupes' n'existe pas dans l'interface.\n"
                "- DÉPÔT CERTIFICAT MÉDICAL : Dissocier la saisie simple de l'inaptitude (Fiche élève > Onglet Inaptitudes) du téléversement des pièces justificatives pour la commission qui se fait dans [Dossiers] > [Dossier Certificatif] > [Dépôt des documents pour la commission].\n"
                "- NOTE UNIQUE CCF : iPackEPS bloque le calcul automatique. Le dossier doit être transmis manuellement au Jury Académique via Cyclades.\n\n"
                
                "🛑 VERROU ANTI-HALLUCINATION :\n"
                "Si le document fourni dans le 'Contexte' ci-dessous prétend qu'il fait de proposer un choix aux élèves à la séance 3 ou 4, de créer des groupes 'Lancer/Saut/Course' en cours de route ou d'adapter les protocoles après coup, TU DOIS IGNORER ET REJETER CE CONTEXTE. C'est une erreur réglementaire majeure.\n"
                "Tu as l'obligation stricte de répondre que cette PROCÉDURE EST IMPOSSIBLE ET INTERDITE. Les protocoles CCF sont verrouillés en début d'année dans Cyclades et iPackEPS ne permet aucune modification rétroactive des choix d'épreuves.\n\n"
                
                "MISSION : Réponds STRICTEMENT à la question posée. Génère le lien porte-à-porte avec le fragment #:~:text= en convertissant les espaces en %20. Utilise obligatoirement la structure du Filtre Pierre (1. Analyse des risques, 2. Procédure technique avec étapes fléchées '→', 3. Protection fonctionnelle).\n"
                "VIDÉOS : N'affiche des liens YouTube que s'ils sont explicitement présents dans le contexte. Ne génère aucun lien fictif.\n\n"
                f"Contexte : {extraits_doc}\nQuestion : {prompt}"
            )
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

        elif mode == "examens":
            consigne_ia = (
                f"{règles_or}{filtre_pierre}\n"
                "ROLE : Tu es l'expert administratif et technique Santorin, Cyclades et Imag'in pour l'académie d'Aix-Marseille. Interdiction absolue de parler de pédagogie.\n"
                f"CONSIGNES INTERNES PRIORITAIRES (À LIRE ET APPLIQUER ABSOLUMENT) :\n{verites_terrain_pierre}\n\n"
                
                "CRITICAL EPS EXAM RULES (AIX-MARSEILLE):\n"
                "- DATE LIMITE : La date butoir impérative de saisie pour Aix-Marseille est le 30 mai 2026 au soir (et non le 9 juin).\n"
                "- AFLP GRISÉS / INACTIFS : Le problème vient de Santorin. L'utilisateur a oublié de cliquer sur le bouton spécifique 'Choisir les AFLP' pour activer la grille de saisie. Ce n'est pas un problème de droits d'accès.\n"
                "- ACCÈS REMPLAÇANT : L'étape n°1 absolue est la vérification de la génération de sa convocation dans IMAG'IN. Sans convocation générée (PDF créé), les droits Santorin ne s'ouvriront jamais.\n"
                "- BOUTON AJOUTER GRISÉ / RETRAITE / REMPLAÇANT : Le bouton [Ajouter] pour un 2ème correcteur est en panne. Interdiction absolue de dire à l'utilisateur de cliquer sur [Ajouter]. Tu dois obligatoirement expliquer la procédure de contournement : 1. Aller dans le détail du lot du 1er correcteur. 2. Ouvrir l'onglet [Candidats]. 3. Tout sélectionner. 4. Cliquer sur **[Déplacer vers un nouveau lot]**. 5. Choisir le correcteur remplaçant dans la fenêtre du bas.\n"
                "- AUCUN LOT À CORRIGER : Le Chef d'établissement doit obligatoirement lancer en premier lieu la 'Distribution automatique' dans Santorin. La distribution manuelle ne vient qu'en second recours si le lot est incomplet.\n"
                "- INDISPONIBILITÉ INSTALLATIONS : Situation de 'Cas exceptionnel / Force majeure'. Interdiction stricte de saisir une inaptitude médicale ('IN' ou 'DI'). Après accord écrit de la CAHN, l'enseignant doit utiliser le bouton officiel **[CE]** (Cas Exceptionnel) sur Santorin pour neutraliser l'épreuve et clore le lot.\n"
                "- LOT COLLÈGUE MANQUANT : Vérifier l'état des services et forcer la synchronisation en finalisant sa convocation d'évaluateur dans IMAG'IN.\n"
                "- PROTOCOLE ADAPTÉ EN COURS D'ANNÉE : Obligation de relancer une 'Distribution automatique des lots' dans Santorin une fois les candidats rattachés au protocole adapté.\n"
                "- ÉLÈVE MANQUANT SANTORIN : Préciser d'abord que le candidat est invisible car il n'est rattaché à aucun groupe. La seule procédure est de l'affecter à un groupe dans Cyclades, puis faire une distribution manuelle dans Santorin (le bouton 'Ajouter un élève' dans Santorin n'est pas fonctionnel).\n"
                "- SPORTIF DE HAUT NIVEAU (SHN) : La validation de la note de 20/20 s'appuie réglementairement sur l'équivalence du Champ d'Apprentissage (CA) correspondant.\n"
                "- ÉLÈVE TRANSFÉRÉ (APSA DIFFÉRENTES) : Interdiction de modifier le protocole de l'établissement ou de réévaluer l'élève sur les épreuves passées. Les notes d'origine sont sanctuarisées. Le professeur évalue la 3ème épreuve sur papier et le chef d'établissement demande à la DEC un 'Protocole Individuel Dérogatoire' dans Cyclades pour fusion manuelle par le rectorat.\n\n"
                
                "🛑 VERROU ANTI-HALLUCINATION :\n"
                "Si un document fourni dans le 'Contexte' ci-dessous prétend qu'il faut aller dans l'onglet [Correcteurs] et cliquer sur le bouton [Ajouter] pour intégrer un évaluateur, TU DOIS IGNORER ET REJETER CE CONTEXTE. Ce bouton est en panne au niveau national.\n"
                "Tu as l'obligation stricte d'appliquer et de décrire la procédure de contournement avec le bouton **[Déplacer vers un nouveau lot]** détaillée dans tes règles ci-dessus. Ne mentionne jamais le bouton [Ajouter] comme une solution fonctionnelle.\n\n"
                
                "MISSION : Réponds STRICTEMENT à la question posée en t'appuyant sur les règles ci-dessus. Utilise obligatoirement la structure du Filtre Pierre (1. Analyse des risques, 2. Procédure technique avec étapes fléchées '→', 3. Protection fonctionnelle).\n"
                f"Contexte additionnel: {extraits_doc}\nQuestion: {prompt}"
            )
            badge, color_card = "📊 RÉGLEMENTATION SANTORIN", "santorin-card"

        elif mode == "textes":
            consigne_ia = (
                f"{règles_or}\n"
                "ROLE : Expert juridique et administratif (Droit public scolaire).\n"
                "POSTURE : Froid, factuel, impersonnel. Zéro conseil. Zéro verbiage.\n\n"
                
                "STRUCTURE OBLIGATOIRE :\n"
                "<h3>1. QUALIFICATION</h3> (Qualification juridique précise des faits).\n"
                "<h3>2. TEXTE OFFICIEL</h3> (Citation textuelle intégrale du Code/Article/Date).\n"
                "<h3>3. CONCLUSION</h3> (Décision procédurale binaire. Argumentation basée sur la loi).\n"
                "<h3>4. FONDEMENT LÉGAL</h3> (Extrait du texte de loi justifiant la décision).\n\n"
                
                "DIRECTIVES :\n"
                "- Ne pas dépasser 150 mots.\n"
                "- Si la loi ne prévoit pas d'exception, ne pas en inventer.\n"
                "- Si le chef d'établissement demande une illégalité, acter le refus basé sur le Code.\n\n"
                
                f"Contexte fourni : {extraits_doc}\nQuestion utilisateur : {prompt}"
            )
            badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

        elif mode == "peda":
            consigne_ia = (
                f"ROLE : Tu es un expert pédagogique de haut niveau en EPS (IA-IPR). Tu as accès à cette liste d'académies : {domaine_eps_france}.\n"
                "MISSION : Réponds sous forme de FICHE TECHNIQUE SÉQUENCÉE, ULTRA-DÉTAILLÉE, rigoureuse sur le plan institutionnel et directement exploitable sur le terrain.\n"
                "FORMATAGE HTML STRICT (Interdiction absolue de Markdown) :\n"
                "1. Utilise uniquement <h3> pour les titres.\n"
                "2. Utilise <ul> et <li> pour toutes les listes (pas de tirets).\n"
                "3. Utilise <br> pour les sauts de ligne simples.\n\n"
                
                "RÈGLE IMPÉRATIVE SUR LES LIENS PÉDAGOGIQUES (ANTI-LIENS MORTS) :\n"
                "1. Interdiction absolue d'inventer des URL directes vers des fichiers PDF ou Excel spécifiques, ils finissent toujours en erreur 404.\n"
                "2. Tu as l'obligation stricte de générer les 3 liens HTML exacts ci-dessous. Tu dois obligatoirement remplacer 'NOM_APSA' par l'activité demandée en minuscules (ex: gymnastique, badminton, acrosport).\n"
                "3. Tu dois obligatoirement remplacer 'DOMAINE1' et 'DOMAINE2' par les domaines d'académies de la liste (ex: eps.ac-creteil.fr), et '[Nom1]'/'[Nom2]' par le nom de l'académie (ex: Créteil). INTERDICTION d'écrire les variables brutes.\n"
                "Construis obligatoirement ces 3 liens de recherche dynamiques au format HTML exact suivant :<br>"
                "1. <a href='https://edubase.eduscol.education.fr/recherche?q=NOM_APSA' target='_blank'>📥 Fiche NOM_APSA - Base Nationale ÉDUBASE EPS</a><br>"
                "2. <a href='https://www.google.com/search?q=site:DOMAINE1+NOM_APSA+fiche+evaluation+EPS' target='_blank'>📥 Fiche NOM_APSA - Académie de [Nom1]</a><br>"
                "3. <a href='https://www.google.com/search?q=site:DOMAINE2+NOM_APSA+fiche+evaluation+EPS' target='_blank'>📥 Fiche NOM_APSA - Académie de [Nom2]</a><br>\n\n"

                 # 🌐 BLOC INSTITUTIONNEL
                "<h3>🌐 ANCRAGE INSTITUTIONNEL</h3>"
                "<ul>"
                "<li><strong>Domaines du Socle Commun :</strong> [Citer explicitement les domaines engagés, ex: Domaine 1 (Langages), Domaine 2 (Méthodes), Domaine 3 (Citoyen), etc.]</li>"
                "<li><strong>Compétences Générales EPS :</strong> [Développer sa motricité, S'approprier des méthodes, Partager des règles/valeurs, Maintenir sa santé, S'approprier une culture]</li>"
                "<li><strong>Compétences Attendu de Fin de Cycle (AFC) :</strong> [Formuler textuellement le ou les AFC officiels du cycle concerné en lien avec l'activité]</li>"
                "</ul>"
                
                "STRUCTURE IMPÉRATIVE À REMPLIR AVEC PRÉCISION :\n"
                "<h3>📋 INTITULÉ DE LA FICHE</h3><strong>Activité exacte, Champ d'Apprentissage (CA) et niveau de classe</strong><br>"
                "<h3>🌐 ANCRAGE INSTITUTIONNEL</h3><ul><li><strong>Domaines du Socle Commun :</strong> [domaines]</li><li><strong>Compétences Générales EPS :</strong> [compétences]</li><li><strong>Attendus de Fin de Cycle (AFC) :</strong> [AFC]</li></ul>"
                "<h3>🎯 OBJECTIFS PÉDAGOGIQUES DE LA SÉQUENCE</h3><ul><li>Objectifs moteurs et intentions tactiques spécifiques</li></ul>"
                "<h3>🏃‍♂️ CADRE SÉCURITÉ & AMÉNAGEMENT</h3><ul><li>Consignes de sécurité passive/active et gestion de l'espace</li></ul>"
                "<h3>🛠️ SITUATIONS D'APPRENTISSAGE ET DE TEST</h3><ul><li>Description de la situation, variables, aménagement, score parlant et règles d'action</li></ul>"
                "<h3>📊 CRITÈRES D'ÉVALUATION ET OBSERVABLES</h3><ul><li>Indicateurs quantitatifs (statistiques, ratios) et qualitatifs (motricité, choix) pour valider les niveaux de maîtrise</li></ul>"
                "<h3>💾 RESSOURCES ACADÉMIQUES</h3>(Insère ici les 3 liens HTML générés ci-dessus, aucun texte brut passif autorisé)<br>"
                f"\nContexte : {extraits_doc}\nQuestion : {prompt}"
            )
            badge, color_card = "🎓 PÉDAGOGIE EPS", "peda-card"
            
        # 4. EXÉCUTION ET RENDU HTML
        response = Settings.llm.complete(consigne_ia)
        texte_brut = response.text
        
        texte_brut = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">\1</a>', texte_brut)
        
        youtube_links = re.findall(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11}))', texte_brut)

        if mode == "peda":
            texte_final = texte_brut.replace("\n", "").replace("\r", "").replace("<p>", "").replace("</p>", "<br>")
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br>{texte_final}</div>'
        
        elif mode == "textes":
            texte_final = texte_brut.replace(chr(10), "<br>") # <--- Le "e" est restauré ici !
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_final}</div>'
            
        else:
            texte_final = texte_brut.replace(chr(10), "<br>")
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_final}</div>'
            
        else:
            texte_final = texte_brut.replace(chr(10), "<br>")
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_final}</div>'
            
        st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
        
        for link in youtube_links:
            st.session_state.messages_hub.append({"role": "assistant", "content": f"st.video('{link[0]}')"})
        st.rerun()
