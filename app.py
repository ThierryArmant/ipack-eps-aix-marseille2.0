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
    
    .title-row h1 { 
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
    
    /* BOUTON NETTOYER */
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
    
    /* CARTES DE RÉPONSE - ARCHITECTURE DES COULEURS DES ONGLETS */
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
    .securite-card { border-left: 6px solid #FF9F43 !important; } /* Orange Sécurité Contentieux */
    .peda-card { border-left: 6px solid #FFA502 !important; } /* Ambre Cadrage Pédagogique */
    
    .santorin-card p, .general-card p, .securite-card p, .santorin-card div, .general-card div, .securite-card div, .santorin-card span, .general-card span, .securite-card span, .santorin-card li, .general-card li, .securite-card li { 
        color: #FFFFFF !important; 
        font-size: 15px !important; 
        line-height: 1.6 !important; 
        font-weight: 400 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }
    
    /* 🛠️ FORCE UNIFORMÉMENT TOUS LES TITRES DES CARTES EN BLEU ÉLECTRIQUE LISIBLE */
    .santorin-card h3, .general-card h3, .securite-card h3, .peda-card h3 {
        color: #38BDF8 !important; /* Bleu ciel / Cyan Électrique ultra-net */
        font-size: 16px !important; 
        margin-top: 16px !important; 
        margin-bottom: 6px !important; 
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.9);
    }
    
    /* COMPACTAGE DE L'ONGLET PÉDAGOGIE AMBRE */
    .peda-card ul {
        margin-top: 2px !important;
        margin-bottom: 6px !important;
        padding-left: 20px !important;
    }
    .peda-card li, .peda-card div, .peda-card span, .peda-card p {
        font-size: 14px !important; 
        line-height: 1.4 !important; 
        color: #F8FAFC !important; /* Blanc doux cassé */
        margin-bottom: 3px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }

    .santorin-card strong, .general-card strong, .securite-card strong, .peda-card strong {
        font-weight: 700 !important; 
    }

    /* 🛠️ CARDINAL DE SURLIGNAGE : TOUTES LES RÉFÉRENCES JURIDIQUES ET TEXTES EN JAUNE-ORANGE */
    .law-highlight {
        background-color: rgba(255, 176, 32, 0.12) !important; /* Fond ambre transparent */
        color: #FFB020 !important; /* Couleur Jaune-Orange pure */
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid rgba(255, 176, 32, 0.4) !important;
        font-weight: 700 !important;
        display: inline-block;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.5) !important;
    }

    /* 🛠️ VERROU DE SÉCURITÉ CSS : FORCE LA VISIBILITÉ DES LIENS HYPERTEXTES EN AMBRE SUR TOUTES LES CARTES */
    div.santorin-card a, div.general-card a, div.securite-card a, div.peda-card a,
    div.santorin-card a *, div.general-card a *, div.securite-card a *, div.peda-card a * {
        color: #FFB020 !important; 
        text-decoration: underline !important;
        font-weight: 700 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.9) !important;
        display: inline !important;
    }
    div.santorin-card a:hover, div.general-card a:hover, div.securite-card a:hover, div.peda-card a:hover {
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

# --- 🛠️ ALIGNEMENT STRICT ET NETTOYAGE DU DÉTECTEUR DE CACHE ---
def obtenir_cle_fichier():
    mtimes = []
    
    for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
        if os.path.exists(fp):
            try: mtimes.append(os.path.getmtime(fp))
            except: pass
            
    chemin_textes = "data/textes/base_textes_officiels.txt"
    if os.path.exists(chemin_textes):
        try: mtimes.append(os.path.getmtime(chemin_textes))
        except: pass

    for f_peda in ["base_pedagogique_edubase.txt", "matrice_AFL_lycee.txt"]:
        if os.path.exists(f_peda):
            try: mtimes.append(os.path.getmtime(f_peda))
            except: pass

    if os.path.exists("data/peda") and os.path.isdir("data/peda"):
        try:
            for f in os.listdir("data/peda"):
                mtimes.append(os.path.getmtime(os.path.join("data/peda", f)))
        except: pass

    if os.path.exists("data/examens") and os.path.isdir("data/examens"):
        try:
            for f in os.listdir("data/examens"):
                mtimes.append(os.path.getmtime(os.path.join("data/examens", f)))
        except: pass
            
    return max(mtimes) if mtimes else 0.0

# --- 🛠️ CHARGEUR ÉTANCHE DU FICHIER DE RÈGLES RACINE ---
def charger_consignes_pierre():
    documents_charges = []
    for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
        if os.path.exists(fp):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    contenu_fichier = f.read()
                documents_charges.append(Document(text=contenu_fichier, metadata={"source": f"Règles de Pierre ({fp})"}))
            except Exception:
                pass
    return documents_charges

# --- 📊 BASE DE DONNÉES SANCTORIN SCOLAIRE SANCTUARISÉE ---
@st.cache_resource
def initialiser_base_santorin(cle_fremt):
    docs_santorin = [
        Document(
            text="""Fiche Mémo - Correction Partagée Santorin (DEC / Assistance). 
            La correction partagée ou multiple permet à several évaluateurs/correcteurs d'intervenir sur un même lot de copies. 
            Dans Santorin, un chef d'établissement peut ajouter manuellement un deuxième évaluateur ou correcteur à un lot via le portail Arena / Cyclades. 
            Procédure : Aller dans l'onglet 'Lots', cliquer sur 'Voir le détail', aller sur l'onglet 'Correcteurs' puis cliquer sur le bouton 'Ajouter'.
            Verrouillage : Lorsqu'un correcteur édite une copie, l'autre bascule temporairement en lecture seule.""",
            metadata={"title": "Fiche Mémo - Correction Partagée Santorin", "url": "https://assistance.ac-noumea.nc/IMG/pdf/fm_correction_partagee.pdf"}
        ),
        Document(
            text="""Fiche Mémo - Processus de Distribution de Lots Santorin en Établissement. 
            Gestion, paramétrage des tailles de groupes et distribution automatique ou manuelle des lots de copies numérisées vers les correcteurs by les coordonnateurs de l'établissement.""",
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
    
    if os.path.exists("data/examens") and os.path.isdir("data/examens"):
        try:
            docs_santorin.extend(SimpleDirectoryReader(input_dir="data/examens").load_data())
        except:
            pass
    elif os.path.exists("faq_evaluation_santorin.csv.csv"):
        try:
            with open("faq_evaluation_santorin.csv.csv", "r", encoding="utf-8", errors="ignore") as f:
                docs_santorin.append(Document(text=f.read(), metadata={"source": "faq_evaluation_santorin.csv.csv"}))
        except:
            pass

    docs_santorin.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=5)

# --- 🛠️ BASE DE DONNÉES IPACKEPS MÉTIER SANCTUARISÉE ---
@st.cache_resource
def initialiser_base_ipack(cle_fremt):
    docs_ipack = [
        Document(
            text="""Portail Pilote iPackEPS - Académie de Créteil. 
            iPackEPS is l'application officielle pour gérer les évaluations d'EPS et le CCF.""",
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
            1. CONFLIT MÉDICAL (ANNULATION DE DISPENSE) : Si un certificat d'inaptitude totale annuelle est invalidé en cours d'année, la seule procédure est de MODIFIER LA DATE DE FIN du certificat dans l'onglet Inaptitudes pour l'arrêter juste avant le début du trimestre de reprise.
            2. NOTE UNIQUE À L'ANNÉE : Si un élève se blesse et n'a qu'une seule note au lieu de deux au CCF, iPackEPS blocks le calcul automatique. Le dossier est transmis au Jury Académique via Cyclades.
            3. BOUTON CHANGEMENT D'ACTIVITÉ GRISÉ : Si l'interface refuse de modifier l'activité ou l'option d'un élève pour le trimestre, c'est qu'une note a déjà été saisie. Pour débloquer informatiquement le bouton, l'enseignant doit obligatoirement se rendre dans le menu 'Saisie des notes' de l'activité actuelle, effacer manuellement la note saisie pour rendre la case totalement vide (pas de zéro, juste du vide), puis enregistrer. Le bouton de modification dans la fiche élève sera alors instantanément dégrisé.""",
            metadata={"title": "Fiche des Cas Complexes et Arbitrages Jurys", "url": "https://eps.ac-creteil.fr/"}
        )
    ]
    docs_ipack.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=5)

# --- 🔒 CHARGEUR DE L'ONGLET TEXTES AJUSTÉ SUR TON CHEMIN STRICT ---
@st.cache_resource
def initialiser_base_textes(cle_fremt):
    docs_textes = [
        Document(
            text="""Base de données réglementaire globale pour les textes de lois, décrets officiels et circulaires de sécurité d'un établissement scolaire du second degré.""",
            metadata={"title": "Référentiel National Textes et Lois", "url": "https://www.legifrance.gouv.fr/"}
        )
    ]
    
    chemin_officiel = "data/textes/base_textes_officiels.txt"
    if os.path.exists(chemin_officiel):
        try:
            with open(chemin_officiel, "r", encoding="utf-8") as f:
                docs_textes.append(Document(text=f.read(), metadata={"title": "Bible Juridique EPS Intégrée"}))
        except:
            pass
            
    docs_textes.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_textes).as_retriever(similarity_top_k=5)

# --- 🔒 CHARGEUR ET VERROU SÉCURISÉ DE L'ONGLET PÉDAGOGIE ---
@st.cache_resource
def initialiser_base_peda(cle_fremt):
    docs_peda = []
    
    if os.path.exists("data/peda") and os.path.isdir("data/peda"):
        try:
            docs_peda.extend(SimpleDirectoryReader(input_dir="data/peda").load_data())
        except:
            try:
                for f_nom in os.listdir("data/peda"):
                    if f_nom.endswith((".txt", ".md")):
                        with open(os.path.join("data/peda", f_nom), "r", encoding="utf-8", errors="ignore") as file_src:
                            docs_peda.append(Document(text=file_src.read(), metadata={"source": f_nom}))
            except: pass
            
    for fichier_racine in ["base_pedagogique_edubase.txt", "matrice_AFL_lycee.txt"]:
        if os.path.exists(fichier_racine):
            try:
                with open(fichier_racine, "r", encoding="utf-8", errors="ignore") as file_src:
                    docs_peda.append(Document(text=file_src.read(), metadata={"source": fichier_racine}))
            except: pass
            
    if not docs_peda:
        docs_peda.append(Document(text="Base de données pédagogique par défaut.", metadata={"source": "system"}))
        
    return VectorStoreIndex.from_documents(docs_peda).as_retriever(similarity_top_k=5)

# --- INSTANCIATION DES MOTEURS SÉMANTIQUES (RACCORDEMENT DES TIMESTAMPS) ---
timestamp_fichier = obtenir_cle_fichier()
retriever_santorin = initialiser_base_santorin(timestamp_fichier)
retriever_ipack = initialiser_base_ipack(timestamp_fichier)
retriever_textes = initialiser_base_textes(timestamp_fichier)
retriever_peda = initialiser_base_peda(timestamp_fichier)

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
    "peda": "🔍 Mode Actif : Référentiels Institutionnels, APSA & Textes de Cadrage BO",
    "textes": "🔒 Mode Actif : SÉCURITÉ & Responsabilité Juridique (Textes Officiels & Risques APPN)"
}

if "active_module" not in st.session_state:
    st.session_state.active_module = "peda"

titre_affiche = label_titres.get(st.session_state.active_module, "🔍 Mode Actif : Référentiels Institutionnels")

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
    if st.button("🔍 Cadrage &\nRéférentiels", use_container_width=True, key="btn_ge", type="primary" if st.session_state.active_module == "peda" else "secondary"):
        st.session_state.active_module = "peda"
        st.session_state.messages_hub = []
        st.rerun()

with col_b4:
    if st.button("🔒 Sécurité &\nCadres Règl.", use_container_width=True, key="btn_se", type="primary" if st.session_state.active_module == "textes" else "secondary"):
        st.session_state.active_module = "textes"
        st.session_state.messages_hub = []
        st.rerun()

# ======================================================================
# 7B. MESSAGES D'AVERTISSEMENT DYNAMIQUES 
# ======================================================================
if st.session_state.active_module == "textes":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            ⚠️ <strong>Avertissement –</strong> Bien que basées sur les textes officiels, ces réponses ne remplacent pas les autorités académiques. En cas de doute juridique ou de sinistre, contactez impérativement : <strong>Votre Chef d'établissement, votre Secrétariat d'examen, ou votre IA-IPR.</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.active_module == "peda":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            💡 <strong>Rappel Institutionnel :</strong> Cet onglet extrait exclusivement les Champs d'Apprentissage (CA), compétences et Attendus des Bulletins Officiels (BO). La liberté pédagogique, la création de fiches locales et les choix de notation restent sous l'entière responsabilité des équipes d'établissement.
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
                <span style="color: #FCD34D !important;">Technique de terrain : configuration de l'application, création des groupes, Saisie des notes brutes.</span><br>
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
        st.cache_resource.clear()
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
# 9. FLUX DE MESSAGES ET TRAITEMENT IA 
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

expressions_inutiles = [
    "je cherche un texte officiel pour savoir si", "je cherche un texte sur le", 
    "je cherche un texte sur la", "je cherche un texte sur", "pour savoir si j'ai le droit de",
    "est-ce que j'ai le droit de", "ai-je le droit de", "est-ce qu'il existe un texte",
    "trouve moi le texte sur", "trouve moi une circulaire sur", "trouve moi", 
    "recherche le texte sur", "texte officiel sur", "circulaire concernant", "circulaire sur"
]

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": f"<span style='color: white;'>{prompt}</span>"})
    
    with st.spinner("Je recherche les documents et ressources pédagogiques..."):
        extraits_doc = ""
        mode = st.session_state.active_module
        prompt_lower_eval = prompt.lower()
        
        # 🔒 COÛTS INTERNES MAÎTRISÉS : Tavily désactivé (0€/requête), le Hub s'appuie à 100% sur le savoir local
        activer_web = False
        
        verites_terrain_pierre = ""
        try:
            if os.path.exists("get_par_pierre.txt"):
                with open("get_par_pierre.txt", "r", encoding="utf-8", errors="ignore") as f:
                    verites_terrain_pierre += "\n--- REGLES DIRECTES DE PIERRE ---\n" + f.read() + "\n"
            elif os.path.exists("gere_par_pierre.txt"):
                with open("gere_par_pierre.txt", "r", encoding="utf-8", errors="ignore") as f:
                    verites_terrain_pierre += "\n--- REGLES DIRECTES DE PIERRE ---\n" + f.read() + "\n"
        except:
            pass

        # ======================================================================
        # 🧠 LE SUPER CERVEAU : ROUTAGE SÉMANTIQUE ÉTANCHE PAR ONGLET (OPTION B)
        # ======================================================================
        if mode == "examens":
            choix_autorises = """
            - CALENDRIER : Le prof demande "quand", "jusqu'à quand" ou s'inquiète de la date butoir pour rendre ses notes.
            - SANTORIN_ERREUR_VALIDATION : Le prof a déjà validé/déposé ses examens Santorin, s'est trompé, et son lot est verrouillé ou clos.
            - SANTORIN_INAPTE_SIMPLE : Le prof veut savoir comment cocher/saisir une dispense (DI) ou un absent (AB) normal dans Santorin sans incident technique.
            - SANTORIN_GRISE : Le prof se plaint que les boutons, cases AFLP ou crayons de notation sont grisés/bloqués en lecture seule dans Santorin.
            - SANTORIN_BRICOLAGE : Le prof demande s'il peut forcer une note, faire un prorata ou s'il y a une seule note au CCF.
            - JURY_REMPLACEMENT : Un collègue est remplacé pour une sous-commission, un jury d'examen ou une réunion académique.
            - AUCUN_BLINDAGE : La question est générale ou demande une recherche classique dans les fichiers d'examens.
            """
        elif mode == "ipack":
            choix_autorises = """
            - CALENDRIER : Le prof demande la date limite de saisie des notes iPack.
            - IPACK_SSS : Un dossier ou bilan annuel est verrouillé par le chef d'établissement dans iPackEPS.
            - IPACK_GROUPES : Configuration, création, manipulation ou répartition des classes/groupes d'APSA dans iPackEPS.
            - IPACK_NOUVEL_ELEVE : Procédure informatique pour ajouter un nouvel élève arrivant en cours d'année dans iPackEPS via SIECLE.
            - AUCUN_BLINDAGE : La question est générale ou demande une recherche classique dans les fichiers iPack.
            """
        elif mode == "textes":
            choix_autorises = """
            - SECURITE_TASA : La question concerne spécifiquement la taxe, la responsabilité liée au transport ou les déclarations TASA.
            - AUCUN_BLINDAGE : La question concerne un autre texte juridique ou réglementaire de sécurité globale.
            """
        else:
            choix_autorises = "- AUCUN_BLINDAGE : Recherche pédagogique institutionnelle classique (APSA, fiches de cycle, CA)."

        intent_prompt = f"""
        Tu es l'aiguilleur master du Hub IA-EPS. Ton unique rôle est de lire la question d'un professeur d'EPS et de déterminer son INTENTION exacte.
        
        Question du professeur : "{prompt}"
        Onglet actif actuel choisi par le prof : {mode}

        Tu dois OBLIGATOIREMENT choisir ton mot-clé uniquement dans cette liste restrictive correspondant à l'onglet actif :
        {choix_autorises}

        Réponds STRICTEMENT par le mot-clé exact choisi dans cette liste, sans aucun autre mot. Aucun bonjour, aucune ponctuation.
        """
        
        try:
            intention = Settings.llm.complete(intent_prompt).text.strip()
        except:
            intention = "AUCUN_BLINDAGE"

        # Traduction de l'intention sémantique en variables d'exécution
        est_date_notes_direct = (intention == "CALENDRIER")
        est_erreur_validation_santorin = (intention == "SANTORIN_ERREUR_VALIDATION")
        est_inapte_santorin_direct = (intention == "SANTORIN_INAPTE_SIMPLE")
        est_grise_direct = (intention == "SANTORIN_GRISE")
        est_bricolage_note = (intention == "SANTORIN_BRICOLAGE")
        est_sss_direct = (intention == "IPACK_SSS")
        est_groupes_direct = (intention == "IPACK_GROUPES")
        est_nouvel_eleve_direct = (intention == "IPACK_NOUVEL_ELEVE")
        est_remplacement_reunion_direct = (intention == "JURY_REMPLACEMENT")
        est_tasa_direct = (intention == "SECURITE_TASA") or (mode == "textes" and "tasa" in prompt_lower_eval)
        
        # Pour les cas génériques Santorin
        est_santorin_direct = mode == "examens" and intention == "AUCUN_BLINDAGE" and any(x in prompt_lower_eval for x in ["appréciation", "appreciation", "commentaire", "aucun lot"])
        
        est_cas_blindé_racine = (est_date_notes_direct or est_erreur_validation_santorin or est_groupes_direct or est_nouvel_eleve_direct or est_bricolage_note or est_grise_direct or est_inapte_santorin_direct or est_remplacement_reunion_direct or est_santorin_direct or est_tasa_direct)
        # ======================================================================

        # 1. MOTEUR LOCAL EN PRIORITÉ ABSOLUE (Coût 0)
        extraits_locaux = ""
        if openai_api_key and not est_cas_blindé_racine:
            try:
                if mode == "examens":
                    for n in retriever_santorin.retrieve(prompt): 
                        extraits_locaux += f"Santorin/Examen: {n.node.text}\n\n"
                            
                elif mode == "ipack":
                    for n in retriever_ipack.retrieve(prompt): 
                        extraits_locaux += f"DOCUMENT OFFICIEL IPACKEPS : {n.node.text}\n\n"
                        
                elif mode == "textes":
                    mot_cle_local = prompt_lower_eval
                    for exp in expressions_inutiles: 
                        mot_cle_local = mot_cle_local.replace(exp, "")
                    requete_extraction = mot_cle_local.strip() if len(mot_cle_local.strip()) > 2 else prompt
                    for n in retriever_textes.retrieve(requete_extraction): 
                        extraits_locaux += f"Cadre Réglementaire/Sécurité : {n.node.text}\n\n"

                elif mode == "peda":
                    for n in retriever_peda.retrieve(prompt):
                        extraits_locaux += f"Ressource Pédagogique Locale : {n.node.text}\n\n"
            except: 
                pass

        extraits_doc += extraits_locaux

        # 2. DISJONCTEUR CASCADE : APPEL TAVILY CONDITIONNÉ (Désactivé par défaut)
        if tavily_api_key and activer_web and mode != "ipack" and not est_cas_blindé_racine and len(extraits_locaux.strip()) == 0:
            try:
                domains = domaine_eps_france
                requete_blindee = prompt
                res = requests.post("https://api.tavily.com/search", json={"api_key": tavily_api_key, "query": requete_blindee, "search_depth": "advanced", "include_domains": domains}, timeout=15)
                if res.status_code == 200:
                    for item in res.json().get("results", []): 
                        extraits_doc += f"Source Web ({item['title']}): {item['content']} - URL: {item['url']}\n\n"
            except: 
                pass

        # 3. STRUCTURES DE SORTIE ET ATTRIBUTIONS
        règles_or = "RÈGLES D'OR : 1. Loi 1937 (Substitution État). 2. Règle 11 (Structure=Mairie/EPI=Prof). 3. Examens = Mission impérative."
        filtre_pierre = (
            "\nMÉTHODE DE RENDU STRICT À RESPECTER SANS CONSEIL NI EMPATHIE :\n"
            "Tu as l'interdiction absolue de créer ou de faire figurer une section intitulée 'ANALYSE DES RISQUES' ou d'expliquer comment tu réfléchis.\n"
            "Tu devez attaquer directement par la procédure ou la réponse concrète, suivie des références réglementaires.\n"
            "Tu dois impérativement utiliser les balises <h3> pour structurer ton rendu final comme suit, sans utiliser la notation markdown ### :\n\n"
            "<h3>➔ PROCÉDURE TECHNIQUE</h3>\n"
            "- Déroule les actions concrètes de terrain de manière chronologique.\n"
            "- Surligne les boutons logiciels réels en gras et entre crochets.\n\n"
            "<h3>📁 PROTECTION FONCTIONNELLE ET RÉFÉRENCES</h3>\n"
            "- Liste les textes législatifs à l'appui (en utilisant impérativement les composants law-highlight).\n\n"
            "POSTURE DE L'IA : Haut fonctionnaire. Tu constates, tu ne justifies pas. Ton style est froid, décisoire et factuel."
        )
        badge = "INFORMATION"
        color_card = "general-card"

        consigne_commune_pierre = f"\n⚠️ SOURCE DE VÉRITÉ ABSOLUE INTERNE (Priorité Maximale) :\n{verites_terrain_pierre}\n\n"

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
            if any(x in prompt_lower_eval for x in ["cap", "bac", "examen", "ccf", "protocole", "épreuve", "supprimer", "effacer", "retirer", "groupe", "répartir", "affecte"]):
                liens_selectionnes.extend([liens_utiles["video_proto"], liens_utiles["rubrique7"]])
            elif any(x in prompt_lower_eval for x in ["import", "xml", "pronote", "doublon", "classe", "groupe", "constituer", "nouvel élève", "introuvable", "manuellement", "ajouter un élève"]):
                liens_selectionnes.extend([liens_utiles["video_import"], liens_utiles["rubrique2"]])
            elif any(x in prompt_lower_eval for x in ["inapte", "dispense", "bless", "note", "bloqu", "certificat", "médical", "cm"]):
                liens_selectionnes.extend([liens_utiles["video_inapt"], liens_utiles["rubrique4"]])
            else:
                liens_selectionnes.extend([liens_utiles["rubrique4"], liens_utiles["rubrique7"]])
            bloc_liens_dynamique = "\n".join(liens_selectionnes)

            consigne_ia = (
                f"{règles_or}{filtre_pierre}{consigne_commune_pierre}\n"
                "ROLE : Expert informatique iPackEPS. Tu n'inventes RIEN. Rendu direct et épuré de toute réflexion.\n\n"
                "STRUCTURE DE RÉPONSE DIRECTE :\n"
                "<h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>\n"
                "<h3>📁 SOURCES, ARTICLES ET TUTORIELS ÉDITEUR</h3>\n\n"
                "🎯 CAS BLINDÉS CONFIGURÉS :\n\n"
                "- CM / INAPTITUDE / DISPENSE ELEVE :\n"
                "<h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>\n"
                "➔ Étape 1 : Connectez-vous et cliquez sur le module **[Mes Élèves]**.\n"
                "➔ Étape 2 : Dans la liste, cliquez sur le nom de l'élève pour ouvrir sa **[Fiche élève]**.\n"
                "➔ Étape 3 : Repérez et ouvrez l'onglet ou la section **[Inaptitudes]**.\n"
                "➔ Étape 4 (Action) : Cliquez sur le bouton officiel **[Saisir une inaptitude]**.\n"
                "➔ Étape 5 (Saisie) : Renseignez scrupuleusement les dates de validité du certificat ainsi que les APSA spécifiquement visées par la dispense.\n"
                "➔ Étape 6 (Dépôt) : Téléversez le scan ou la capture photo du certificat médical officiel.\n"
                "➔ Étape 7 (Verrou d'arbitrage) : Pour la réactivation ultérieure des APSA lors des commissions d'arbitrage, modifiez la date de fin de l'inaptitude pour libérer informatiquement l'accès aux grilles de notation.\n"
                "⚠️ **SÉCURITÉ** : Ne tapez JAMAIS manuellement 'IN' ou 'DI' directement dans les grilles de notes brutes. La validation dans l'onglet dédié génère le statut automatiquement.\n\n"
                f"Contexte RAG : {extraits_doc}\n"
                f"Question du professeur : {prompt}"
            )
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

        elif mode == "examens":
            liens_utiles = {
                "webinaire_eps": "- [📥 Télécharger le Webinaire Officiel IA-IPR (Guide pas-à-pas Santorin EPS Aix-Marseille)](https://www.pedagogie.ac-aix-marseille.fr/upload/docs/application/pdf/2024-03/webinaire_utilisation_de_santorin.pdf)",
                "portail_santorin": "- [🌐 Accéder au Portail d'assistance et Fiches Mémo Santorin Académique](https://www.ac-aix-marseille.fr/santorin)",
                "base_ecole": "- [🧪 Accéder à la Base École Santorin (Plateforme officielle de simulation)](https://santorin-ecole.phm.education.gouv.fr/inscription/correcteur)"
            }
            liens_selectionnes = []
            if any(x in prompt_lower_eval for x in ["simul", "entraîn", "test", "école", "faux", "s'exercer"]):
                liens_selectionnes.extend([liens_utiles["base_ecole"], liens_utiles["webinaire_eps"]])
            elif any(x in prompt_lower_eval for x in ["absent", "dispense", "inapte", "neutralis", "substitution", "bless", "aflp", "verroui"]):
                liens_selectionnes.extend([liens_utiles["webinaire_eps"], liens_utiles["portail_santorin"]])
            else:
                liens_selectionnes.extend([liens_utiles["webinaire_eps"], liens_utiles["portail_santorin"]])
            bloc_liens_dynamique = "\n".join(liens_selectionnes)

            consigne_ia = (
                f"{règles_or}{filtre_pierre}{consigne_commune_pierre}\n"
                "ROLE : Expert certificateur EPS. Tu es un moteur d'extraction strict. Aucun commentaire sur ton propre processus.\n\n"
                "STRUCTURE DE RÉPONSE NON NÉGOCIABLE AVEC TITRES HTML :\n"
                "<h3>➔ PROCÉDURE TECHNIQUE</h3>\n"
                "<h3>📁 CADRAGE OFFICIEL ET RECOMMANDATIONS</h3>\n\n"
                f"Contexte RAG : {extraits_doc}\n"
                f"Question du professeur : {prompt}"
            )
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif mode == "textes":
            consigne_ia = f"""{règles_or}{filtre_pierre}{consigne_commune_pierre}
ROLE : Conseil Juridique du Rectorat. Aucun mot de politesse, d'empathie ou d'introduction réflexive.
🛑 DIRECTIVE DE SURLIGNAGE HTML : Enveloppe les mentions de lois dans : <span class="law-highlight">NOM DU TEXTE</span>.
STRUCTURE DU RENDU DIRECT :
<h3>➔ PROCÉDURE TECHNIQUE JURIDIQUE</h3>
<h3>📁 PROTECTION FONCTIONNELLE ET BOUCLIER LÉGISLATIF</h3>
Contexte Juridique Local : {extraits_doc}
Question de l'agent : {prompt}"""
            badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

        elif mode == "peda":
            est_lycee = any(x in prompt_lower_eval for x in ["lycée", "lycee", "bac", "terminale", "première", "premiere", "seconde", "cap", "bac pro"])
            niveau_affiche = "Lycée (Baccalauréat / CAP)" if est_lycee else "Cycle 4 (Collège)"
            label_attendu = "Attendus de Fin de Lycée (AFL 1, 2, 3)" if est_lycee else "Attendus de Fin de Cycle 4 (AFC)"
            label_competence = "Axe des compétences visées"
            ca_nom = "CA1 (Performance optimale à une échéance donnée)"
            ca_attendus = "Produire la meilleure performance possible..."
            ca_competences = "Concevoir et stabiliser des techniques..."
            
            mots_apsa = ["volley", "basket", "hand", "foot", "rugby", "badminton", "tennis", "ping", "boxe", "lutte", "gym", "acro", "danse", "step", "muscu", "fitness", "escalade", "orientation", "vtt", "kayak", "relais", "natation"]
            apsa_trouvee = "eps"
            for m in mots_apsa:
                if m in prompt_lower_eval: apsa_trouvee = m; break

            liens_html = f"1. <a href='https://edubase.eduscol.education.fr/recherche?q={apsa_trouvee}' target='_blank'>📥 Ressources {apsa_trouvee.upper()}</a>"

            consigne_ia = (
                f"<h3>📊 CADRAGE INSTITUTIONNEL ET RÉGLEMENTAIRE - {apsa_trouvee.upper()}</h3>"
                f"<strong>Niveau ciblé : {niveau_affiche} | Champ d'Apprentissage : {ca_nom}</strong><br><br>"
                f"Question du professeur : {prompt}"
            )
            badge, color_card = "🎓 CADRAGE EPS", "peda-card"
            
        # --- 🛡️ EXÉCUTION DU BLOC DES COMPOSANTS EN DUR SÉCURISÉS (COMPLETS) ---
        if est_tasa_direct:
            texte_brut = extraits_doc
            badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"
            
        elif est_date_notes_direct:
            texte_brut = """
            <h3>📊 CALENDRIER & DATES DE REMISE DES NOTES</h3>
            <strong>Statut administratif : Spécificités académiques locales.</strong><br><br>
            <h3>➔ RÈGLE INSTITUTIONNELLE FIXE</h3>
            <ul>
            <li><strong>Notification officielle :</strong> Les dates limites de saisie informatique étant différentes pour chaque académie de France, je ne suis pas en mesure de vous fournir une date fixe. Veuillez vous rapprocher de vos coordonnateurs d'établissement ou de votre secrétariat.</li>
            </ul>
            <h3>📁 CADRE OFFICIEL DE RÉFÉRENCE</h3>
            <ul>
            <li><strong>Source de vérité :</strong> Seuls les calendriers d'examen officiels émis par la Division des Examens et Concours (DEC) de votre académie et transmis par note interne par votre chef d'établissement font juridiquement foi.</li>
            </ul>
            """
            badge, color_card = ("📊 EXAMENS & SANTORIN" if mode == "examens" else "🛠️ PROTOCOLE IPACK"), ("santorin-card" if mode == "examens" else "general-card")
            
        elif est_erreur_validation_santorin:
            texte_brut = """
            <h3>📊 EXAMENS & SANTORIN : ERREUR DE SAISIE APRÈS VALIDATION DU LOT</h3>
            <strong>Statut administratif : Clôture définitive du lot par le correcteur.</strong><br><br>
            <h3>➔ PROCÉDURE TECHNIQUE & ADMINISTRATIVE D'URGENCE</h3>
            <ul>
            <li><strong>Étape 1 (Alerte Interne) :</strong> Ne tentez pas de manipuler ou forcer l'interface informatique. Prévenez immédiatement le secrétariat de direction de votre établissement (Chef d'établissement).</li>
            <li><strong>Étape 2 (Demande de déverrouillage) :</strong> Le chef d'établissement ou le coordonnateur principal doit contacter sans délai le gestionnaire de la Division des Examens et Concours (DEC) du Rectorat pour demander un <strong>[Renvoi en modification]</strong> ou un rejet informatique du lot.</li>
            <li><strong>Étape 3 (Correction) :</strong> Une fois que la DEC a libéré informatiquement le dossier, l'icône "crayon" redevient active dans votre tableau de bord Santorin. Vous pouvez alors écraser le statut erroné, saisir les points AFL réels de l'élève, puis valider à nouveau le lot.</li>
            <li>⚠️ <strong>Si la plateforme est close :</strong> Si les serveurs nationaux sont définitivement clos, consignez l'erreur manuellement sur votre bordereau papier signé et transmettez-le directement au <strong>Jury Académique d'Harmonisation</strong> via Cyclades pour correction lors des délibérations.</li>
            </ul>
            <h3>📁 CADRE OFFICIEL DE RÉFÉRENCE</h3>
            <ul>
            <li>📥 <a href="https://www.pedagogie.ac-aix-marseille.fr/upload/docs/application/pdf/2024-03/webinaire_utilisation_de_santorin.pdf" target="_blank" style="color: #FFB020 !important; text-decoration: underline; font-weight: bold;">Consulter les Directives de transmission DEC / DIEC Aix-Marseille</a></li>
            </ul>
            """
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif est_sss_direct:
            texte_brut = """
            <h3>🛠️ IPACKEPS : DOSSIER SSS OU BILAN ANNUEL VERROUILLÉ</h3>
            <strong>Statut du dossier : Lecture seule absolue (Verrouillage de sécurité suite à validation).</strong><br><br>
            <h3>➔ LA SEULE PROCÉDURE DE RÉSOLUTION RÉGLEMENTAIRE</h3>
            <ul>
            <li><strong>Étape 1 (Signalement) :</strong> Ne tentez pas de modifier les données locales. Contactez immédiatement votre <strong>Correspondant iPackEPS d'établissement / de bassin</strong> ou directement l'équipe de la mission académique des <strong>IA-IPR</strong>.</li>
            <li><strong>Étape 2 (Action Administrateur) :</strong> Seuls ces profils possèdent les droits master requis dans leur console de gestion pour appliquer la commande <strong>[Renvoyer en modification]</strong> ou <strong>[Débloquer le dossier]</strong>.</li>
            <li><strong>Étape 3 (Mise à jour) :</strong> L'action de l'administrateur fait redescendre informatiquement le dossier d'un niveau. L'enseignant retrouve instantanément son accès en écriture pour compléter son bilan ou ses grilles, puis soumet à nouveau le bloc complet pour signature finale du Chef d'établissement.</li>
            </ul>
            """
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

        elif est_groupes_direct:
            texte_brut = """
            <h3>🛠️ IPACKEPS : CONSTITUTION ET CONFIGURATION DES CLASSES ET DES GROUPES</h3>
            <strong>Nomenclature officielle : Étape logicielle obligatoire préalable à toute importation d'élèves.</strong><br><br>
            <h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>
            <ul>
            <li><strong>Étape 1 :</strong> Connectez-vous à votre console professeur iPackEPS et accédez au menu supérieur **[Dossiers]**.</li>
            <li><strong>Étape 2 :</strong> Allez dans **[Dossier EPS]** > **[Classes]** > **[Configuration des Classes]** pour associer chaque division pédagogique à son cycle d'enseignement officiel (ex: Terminale au CCF).</li>
            <li><strong>Étape 3 :</strong> Basculez sur l'onglet **[Organisation des Classes]** pour valider la répartition réglementaire (Générale, Technologique ou Professionnelle).</li>
            <li><strong>Étape 4 :</strong> Rendez-vous ensuite dans le module **[Mes Élèves]** pour peupler vos structures via l'injection de votre fichier d'extraction Pronote ou SIECLE.</li>
            </ul>
            <h3>📁 SOURCES, ARTICLES ET TUTORIELS ÉDITEUR</h3>
            <ul>
            <li>🎥 <a href="https://youtu.be/RlScDjd8kHk" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">Import d'élèves depuis Pronote</a></li>
            <li>📥 <a href="https://ipackeps.ac-creteil.fr/spip.php?rubrique2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">Accéder à la Rubrique 2 de la documentation officielle (Structures & Groupes)</a></li>
            </ul>
            """
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
            
        elif est_nouvel_eleve_direct:
            texte_brut = """
            <h3>🛠️ IPACKEPS : AJOUTER UN ÉLÈVE ARRIVANT EN COURS D'ANNÉE</h3>
            <strong>Nomenclature officielle : Interdiction absolue de création manuelle isolée dans l'application.</strong><br><br>
            <h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>
            <ul>
            <li><strong>Étape 1 (Mise à jour SIÈCLE) :</strong> Assurez-vous auprès du secrétariat de l'établissement que le nouvel élève a bien été enregistré et affecté dans sa classe sur la base nationale <strong>SIÈCLE</strong>.</li>
            <li><strong>Étape 2 (Extraction) :</strong> Générez ou demandez un nouveau fichier d'exportation des élèves (format XML ou CSV) depuis Pronote ou Écoles-Directe.</li>
            <li><strong>Étape 3 (Importation iPack) :</strong> Connectez-vous à iPackEPS, ouvrez le module **[Mes Élèves]** and cliquez sur le bouton officiel **[Importer un fichier d'élèves]**.</li>
            <li><strong>Étape 4 (Fusion des bases) :</strong> Téléversez votre nouveau fichier. L'application va détecter automatiquement le nouvel arrivant et l'ajouter à sa division sans altérer les notes des autres élèves.</li>
            </ul>
            <h3>📁 SOURCES, ARTICLES ET TUTORIELS ÉDITEUR</h3>
            <ul>
            <li>🎥 <a href="https://youtu.be/RlScDjd8kHk" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">Import d'élèves depuis Pronote</a></li>
            <li>📥 <a href="https://ipackeps.ac-creteil.fr/spip.php?rubrique2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">Accéder à la Rubrique 2 de la documentation officielle (Structures & Groupes)</a></li>
            </ul>
            """
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
            
        elif est_bricolage_note:
            texte_brut = """
            <h3>🛑 RÉGLEMENTATION CCF : CANDIDAT AVEC UNE SEULE NOTE VALIDE (NOTE UNIQUE)</h3>
            <strong>Cadre réglementaire national (Baccalauréat GT) : Impossibilité administrative de calcul automatique.</strong><br><br>
            <h3>➔ LA PROCÉDURE RÉGLEMENTAIRE STRICHTE</h3>
            <ul>
            <li><strong>Règle d'or :</strong> Au Baccalauréat GT, l'évaluation du CCF repose sur un ensemble d'APSA. Si un élève se blesse gravement et ne dispose au final que d'une **seule note valide** à l'année, l'application bloque le calcul.</li>
            <li><strong>Interdiction de forcer :</strong> Il est strictement interdit à l'enseignant de procéder à un "bricolage" ou à un calcul de moyenne manuel, de faire un prorata artificiel ou de taper une fausse note pour débloquer la case. Laissez la case de l'activité manquée totalement vide.</li>
            <li><strong>Saisie de l'inaptitude :</strong> Renseignez scrupuleusement le statut **[DI]** (Dispensé) ou Inapte dans l'onglet des inaptitudes pour justifier informatiquement l'absence de note sur les autres épreuves.</li>
            <li><strong>Arbitrage souverain :</strong> Le dossier d'évaluation complet de l'élève (note obtenue + justificatifs médicaux validés par le médecin scolaire) doit être obligatoirement transmis au <strong>Jury Académique d'Harmonisation</strong> via la DEC. C'est ce jury, lors de sa session finale, qui détient la compétence exclusive pour décider de valider la note unique comme note finale de l'examen ou de prononcer la neutralisation.</li>
            </ul>
            <h3>📁 CADRE OFFICIEL ET ACCOMPAGNEMENT</h3>
            <ul>
            <li>📥 <a href="https://pole-examens.github.io/tutoriels-examens/co/guide.html" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">Cliquez ici pour consulter le Guide Spécifique des Jurys - Pôle Examens</a></li>
            </ul>
            """
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        elif est_grise_direct:
            texte_brut = """
            <h3>📊 EXAMENS & SANTORIN : BOUTONS DE SAISIE OU CRAYONS GRISÉS</h3>
            <strong>Statut technique : Conflit d'édition en temps réel ou défaut d'arborescence.</strong><br><br>
            <h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>
            <ul>
            <li><strong>Cas 1 (Correction partagée - Le plus fréquent) :</strong> Si plusieurs évaluateurs/correcteurs sont affectés par le chef d'établissement sur un même lot de copies numérisées, dès qu'un enseignant ouvre ou édite le dossier d'un élève, la plateforme bascule instantanément en lecture seule (boutons grisés) pour tous les autres collègues afin d'éviter les collisions de données. <strong>Solution : Attendez simplement que votre collègue referme la copie ou se déconnecte de son espace.</strong></li>
            <li><strong>Cas 2 (Défaut de déploiement) :</strong> Les boutons de notation restent verrouillés tant que le lot d'examen n'est pas actif. <strong>Solution : Allez dans l'onglet [Lots], cliquez sur [Voir le détail], puis sélectionnez explicitement le nom du candidat pour débloquer les grilles.</strong></li>
            </ul>
            <h3>📁 CADRE OFFICIEL ET ACCOMPAGNEMENT</h3>
            <ul>
            <li>📥 <a href="https://pole-examens.github.io/tutoriels-examens/co/guide.html" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">Cliquez ici pour consulter le Guide Interactif Complet du Pôle Examens</a></li>
            </ul>
            """
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        elif est_inapte_santorin_direct:
            texte_brut = """
            <h3>📊 EXAMENS & SANTORIN : ÉLÈVES INAPTES ET ABSENTS AU CCF</h3>
            <strong>Cadre réglementaire académique : Saisie obligatoire des notes particulières dans l'interface de notation Santorin.</strong><br><br>
            <h3>➔ PROCÉDURE TECHNIQUE DE SAISIE (DIRECTIVES DIEC / DEC AIX-MARSEILLE)</h3>
            <ul>
            <li><strong>Étape 1 (Accès Mission) :</strong> Connectez-vous à votre espace Arena, ouvrez l'activité **[Portail d'accès aux missions]** puis sélectionnez votre mission active **[Notation EPS CCF]**.</li>
            <li><strong>Étape 2 (Ouverture du Lot) :</strong> Dans votre tableau de bord Santorin, ouvrez votre lot d'APSA et cliquez sur l'icône "crayon" d'accès à la notation du candidat concerné.</li>
            <li><strong>Étape 3 (Saisie de la Note Particulière) :</strong> Dans la zone de notation de l'APSA, n'entrez pas de points AFL, mais ouvrez le menu déroulant officiel des **[Notes particulières]** :</li>
            <ul>
                <li>🔹 <strong>Dispense (DI) :</strong> À sélectionner si l'élève présente un certificat médical d'inaptitude valide visé par l'établissement. Cela neutralise l'APSA (elle sort de la moyenne sans pénaliser l'élève).</li>
                <li>🔹 <strong>Absent (AB) :</strong> À sélectionner en cas d'absence non justifiée lors de l'évaluation officielle (génère informatiquement un zéro).</li>
                <li>🔹 <strong>Épreuve de substitution :</strong> À cocher si l'élève est officiellement renvoyé à la session de rattrapage réglementaire.</li>
            </ul>
            <li><strong>Étape 4 (Cas des SHN) :</strong> Pour les Sportifs de Haut Niveau, le clic sur le crayon ouvre un volet spécifique permettant d'appliquer la note réglementaire automatique de 20/20.</li>
            </ul>
            <h3>📁 CADRE OFFICIEL ET ACCOMPAGNEMENT</h3>
            <ul>
            <li>📥 <a href="https://www.pedagogie.ac-aix-marseille.fr/upload/docs/application/pdf/2024-03/webinaire_utilisation_de_santorin.pdf" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">Webinaire de Formation Officiel Santorin EPS (Académie d'Aix-Marseille)</a></li>
            </ul>
            """
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        elif est_remplacement_reunion_direct:
            texte_brut = """
            <h3>📊 EXAMENS & SANTORIN : REMPLACEMENT EN SOUS-COMMISSION / JURY ACADÉMIQUE</h3>
            <strong>Statut juridique : Ordre de mission nominatif impératif préalable à tout déplacement de l'agent.</strong><br><br>
            <h3>➔ PROCÉDURE TECHNIQUE & ADMINISTRATIVE IMMÉDIATE</h3>
            <ul>
            <li><strong>Étape 1 (Alerte Secrétariat) :</strong> Le secrétariat de direction de votre établissement doit contacter immédiatement votre gestionnaire d'examen au sein de la Division des Examens et Concours (DEC) du Rectorat.</li>
            <li><strong>Étape 2 (Régularisation nominative) :</strong> Demander l'émission urgente d'un modificatif officiel de convocation ou d'un ordre de mission exprès au nom de l'enseignant remplaçant. Cette pièce est indispensable pour valider sa couverture juridique (accidents de trajet) et le remboursement de ses frais via Chorus DT.</li>
            <li><strong>Étape 3 (Bascule Santorin / Imag'in) :</strong> Si le remplacement inclut des droits de notation, le secrétariat doit obligatoirement valider la suppléance sur l'application nationale Imag'in et éditer la convocation au format PDF pour injecter informatiquement ses accès vers Santorin.</li>
            </ul>
            <h3>📁 CADRE OFFICIEL ET RECOMMANDATIONS</h3>
            <ul>
            <li>📁 <span class="law-highlight">Code de l'éducation</span> : La participation aux jurys d'examens nationaux constitue une obligation statutaire pour les enseignants du second degré. L'exercice de cette mission de service public est strictement conditionné à la détention d'un titre de convocation régulier émis par l'autorité académique.</li>
            </ul>
            """
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        else:
            response = Settings.llm.complete(consigne_ia) 
            texte_brut = response.text
            if mode == "ipack" and 'bloc_liens_dynamique' in locals():
                texte_brut += f"\n\n<h3>📁 SOURCES, ARTICLES ET TUTORIELS ÉDITEUR</h3>\n{bloc_liens_dynamique}"
            elif mode == "examens" and 'bloc_liens_dynamique' in locals():
                texte_brut += f"\n\n<h3>📁 CADRE OFFICIEL ET RECOMMANDATIONS</h3>\n{bloc_liens_dynamique}"
        # --- FIN DU BLOC DE SÉCURITÉ EN DUR ---
        
        # Filtre Regex de sécurité pour forcer l'affichage orange des textes de loi si l'IA en oublie
        texte_brut = re.sub(r'(Article\s+\d+[-–\w]*|Loi\s+du\s+\d+\s+\w+\s+\d+|RGPD|Code\s+de\s+l\'éducation)', r'<span class="law-highlight">\1</span>', texte_brut)
        texte_brut = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">\1</a>', texte_brut)
        
        texte_final = texte_brut.replace("\n", "").replace("\r", "").replace("<p>", "").replace("</p>", "<br>").replace(chr(10), "<br>")
        formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br>{texte_final}</div>'
            
        st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
        
        # Détecteur et persistance vidéo dans l'historique de session
        youtube_links = re.findall(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11}))', texte_brut)
        for link in youtube_links:
            clean_link = link[0].split('"')[0].split("'")[0].strip()
            st.session_state.messages_hub.append({"role": "assistant", "content": f"st.video('{clean_link}')"})
            
        st.rerun()
