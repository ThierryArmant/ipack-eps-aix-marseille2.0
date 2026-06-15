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
        prompt_lower = prompt.lower()
        
        mots_terrain = ["fiche", "evaluation", "évaluation", "grille", "bareme", "barème", "cycle", "seance", "séance", "apsa", "volley", "hand", "basket", "badminton", "relais", "natation", "escalade", "gym", "college", "collège"]
        est_demande_fiche = any(mot in prompt_lower for mot in mots_terrain)
        
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
        
        # 1. MOTEUR WEB (Tavily)
        if tavily_api_key:
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

                elif mode == "examens":
                    requete_blindee = f"{prompt} réglementation examen Santorin Cyclades"
                    domains = ["education.gouv.fr"] + domaine_eps_france
                
                elif mode == "ipack":
                    requete_blindee = f"rubrique4 {prompt}"
                    domains = ["ipackeps.ac-creteil.fr"]
                    exclude = ["youtube.com"]
                
                elif mode == "peda":
                    requete_blindee = f"{prompt} programme officiel EPS attendus de fin de cycle"
                    domains = domaine_eps_france
                
                elif est_demande_fiche:
                    requete_blindee = f"{prompt} EPS programme officiel"
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
                    veut_appreciations = any(x in prompt_lower for x in ["appréciation", "appreciation", "commentaire", "texte obligatoire"])
                    a_bug_de_lot = any(x in prompt_lower for x in ["aucun lot", "pas de lot", "lot manquant", "lot invisible", "boccaccini"])

                    if veut_appreciations:
                        extraits_doc = """
                        <h3>📊 EXAMENS & SANTORIN : LA RÈGLE DES APPRÉCIATIONS</h3>
                        <strong>Statut réglementaire : Facultatif (Idée reçue du terrain).</strong><br><br>
                        <h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>
                        <ul>
                        <li> Saisissez uniquement les notes d'AFL. Laissez la case appréciation VIDE pour les élèves ordinaires.</li>
                        <li><strong>Exception Obligatoire :</strong> Le commentaire devient STRICTEMENT OBLIGATOIRE uniquement pour justifier un statut d'alerte, une notation atypique ou un aménagement (ex: un élève avec 2 dispenses + 1 note, ou basculé en statut DI).</li>
                        </ul>
                        """
                    elif a_bug_de_lot:
                        extraits_doc = """
                        <h3>📊 EXAMENS & SANTORIN : PROTOCOLE "AUCUN LOT À CORRIGER"</h3>
                        <strong>Statut de l'erreur : Problème d'aiguillage Direction / DIEC.</strong><br><br>
                        <h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION CÔTÉ DIRECTION</h3>
                        <ul>
                        <li><strong>Étape 1 (Vérification Imag'in) :</strong> Le Chef d'établissement doit vérifier que vous possédez bien une mission active de type 'Notation EPS CCF'.</li>
                        <li><strong>Étape 2 (Le Clic PDF Master) :</strong> Lors de l'affectation, le chef doit OBLIGATOIREMENT cliquer sur le picto PDF dans son espace Imag'in. C'est ce clic précis qui pousse votre nom vers Santorin.</li>
                        <li><strong>Étape 3 (Distribution) :</strong> Le chef doit ensuite aller sur son tableau de bord Santorin et lancer la 'Distribution automatique' (ou manuelle si votre mail Cyclades diffère de votre mail Imag'in) pour créer votre lot.</li>
                        </ul>
                        """
                    else:
                        for n in retriever_santorin.retrieve(prompt): 
                            extraits_doc += f"Santorin/Examen: {n.node.text}\n\n"
                            
                elif mode == "ipack":
                    est_dossier_verrouille_chef = any(x in prompt_lower for x in ["validé par le chef", "valide par le chef", "chef d'établissement", "chef d'etablissement",
                        "oublie le bilan", "oublié le bilan", "plus l'accès", "plus l'acces", "plus la main", 
                        "modifier après validation", "redonner la main", "verrouillé sss", "bloqué sss", "débloquer sss"])
                    
                    if est_dossier_verrouille_chef:
                        extraits_doc = """
                        <h3>PROTOCOLE DE SÉCURITÉ - DOSSIER VERROUILLÉ APRÈS VALIDATION CHEF</h3>
                        <strong>Statut du dossier : Lecture seule absolue (Verrouillage institutionnel).</strong><br><br>
                        <h3>➔ LA SEULE PROCÉDURE DE RÉSOLUTION RÉGLEMENTAIRE</h3>
                        <ul>
                        <li><strong>Étape 1 (Alerte) :</strong> Contactez immédiatement votre <strong>Correspondant iPackEPS d'établissement / de bassin</strong> ou l'équipe des <strong>IA-IPR</strong>.</li>
                        <li><strong>Étape 2 (Action Administrateur) :</strong> Seuls ces profils possèdent les droits master dans leur console de gestion pour utiliser la commande <strong>[Renvoyer en modification]</strong> ou <strong>[Débloquer le dossier]</strong>.</li>
                        <li><strong>Étape 3 (Reprise en main) :</strong> L'action de l'administrateur fait redescendre le dossier d'un niveau. Le prof retrouve son accès en écriture pour compléter son bilan, puis soumet à nouveau le tout pour signature finale du Chef.</li>
                        </ul>
                        """
                    else:
                        for n in retriever_ipack.retrieve(prompt): 
                            extraits_doc += f"DOCUMENT OFFICIEL IPACKEPS : {n.node.text}\n\n"
                        
                elif mode == "textes":
                    mot_cle_local = prompt_lower
                    for exp in expressions_inutiles: 
                        mot_cle_local = mot_cle_local.replace(exp, "")
                    
                    requete_extraction = mot_cle_local.strip() if len(mot_cle_local.strip()) > 2 else prompt
                    try:
                        for n in retriever_textes.retrieve(requete_extraction): 
                            extraits_doc += f"Cadre Réglementaire/Sécurité : {n.node.text}\n\n"
                    except:
                        pass

                elif mode == "peda":
                    for n in retriever_peda.retrieve(prompt):
                        extraits_doc += f"Ressource Pédagogique Locale : {n.node.text}\n\n"
            except: 
                pass

        # 3. IDENTITÉ ET PERSONNALITÉ (FILTRE PIERRE OPTIMISÉ POUR COUVRIR TOUTE L'IA ET CACHER SA CURIOSITÉ)
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
            
            if any(x in prompt_lower for x in ["cap", "bac", "examen", "ccf", "protocole", "épreuve", "supprimer", "effacer", "retirer", "groupe", "répartir", "affecte"]):
                liens_selectionnes.extend([liens_utiles["video_proto"], liens_utiles["rubrique7"]])
            elif any(x in prompt_lower for x in ["import", "xml", "pronote", "doublon", "classe", "groupe", "constituer", "nouvel élève", "introuvable", "manuellement", "ajouter un élève"]):
                liens_selectionnes.extend([liens_utiles["video_import"], liens_utiles["rubrique2"]])
            elif any(x in prompt_lower for x in ["inapte", "dispense", "bless", "note", "bloqu", "certificat", "médical", "cm"]):
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
                "- SUPPRIMER / EFFACER / RETIRER UN PROTOCOLE :\n"
                "<h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>\n"
                "➔ Étape 1 : Allez dans **[Dossiers]** > **[Dossier EPS]** > **[Séquences d'Apprentissage]** et supprimez toutes les séquences liées au groupe concerné.\n"
                "➔ Étape 2 : Allez dans le module **[Mes Élèves]**, ouvrez le groupe et videz-le en décochant manuellement tous les élèves affectés.\n"
                "➔ Étape 3 : Une fois le groupe totalement vide, sans aucune séquence ni note brute résiduelle, le protocole se désactive informatiquement et peut être archivé ou supprimé depuis le menu **[Dossier Certificatif]** > **[Protocoles d'évaluation]**.\n\n"
                "- RÉPARTIR / AFFECTER LES ÉLÈVES DANS LES GROUPES :\n"
                "<h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>\n"
                "➔ Étape 1 : Accédez exclusivement au module **[Mes Élèves]**.\n"
                "➔ Étape 2 : Dans le panneau de configuration, sélectionnez l'onglet **[Classes]** ou **[Groupes]**.\n"
                "➔ Étape 3 : Cochez manuellement les cases individuelles en bout de ligne pour chaque élève à attribuer.\n"
                "➔ Étape 4 : Utilisez le bouton d'affectation collective **[Ajouter au groupe]** après avoir sélectionné votre groupe cible dans le menu déroulant.\n"
                "⚠️ **RÈGLE d'ÉTANCHÉITÉ** : Ne jamais mélanger des élèves de la filière Générale et de la filière Technologique dans un même groupe d'évaluation.\n\n"
                "🎯 BLOC DE LIENS OFFICIELS À COPIER-COLLER :\n{bloc_liens_dynamique}\n\n"
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
            
            if any(x in prompt_lower for x in ["simul", "entraîn", "test", "école", "faux", "s'exercer"]):
                liens_selectionnes.extend([liens_utiles["base_ecole"], liens_utiles["webinaire_eps"]])
            elif any(x in prompt_lower for x in ["absent", "dispense", "inapte", "neutralis", "substitution", "bless", "aflp"]):
                liens_selectionnes.extend([liens_utiles["webinaire_eps"], liens_utiles["portail_santorin"]])
            else:
                liens_selectionnes.extend([liens_utiles["webinaire_eps"], liens_utiles["portail_santorin"]])

            bloc_liens_dynamique = "\n".join(liens_selectionnes)

            consigne_ia = (
                f"{règles_or}{filtre_pierre}{consigne_commune_pierre}\n"
                "ROLE : Expert certificateur EPS. Tu es un moteur d'extraction strict. Aucun commentaire sur ton propre processus.\n\n"
                "STRUCTURE DE RÉPONSE DIRECTE :\n"
                "<h3>➔ PROCÉDURE TECHNIQUE</h3>\n"
                "<h3>📁 CADRAGE OFFICIEL ET RECOMMANDATIONS</h3>\n\n"
                "🎯 CAS BLINDÉS EXAMENS :\n\n"
                "- REMPLAÇANT / ACCÈS REMPLAÇANT :\n"
                "<h3>➔ PROCÉDURE TECHNIQUE</h3>\n"
                "➔ Étape 1 (Convocation) : Le secrétariat doit éditer la convocation officielle du remplaçant dans IMAG'IN et cliquer sur l'icône 'PDF'. C'est cette édition qui transmet informatiquement ses droits vers Santorin.\n"
                "➔ Étape 2 (Ouverture) : Déclenchement automatique de l'ouverture des accès de l'espace numérique ARENA de l'intervenant.\n"
                "➔ Étape 3 (Lots) : Attribution finale et apparition des droits de correction sur les lots correspondants dans son tableau de bord Santorin personnel.\n\n"
                "🎯 BLOC DE LIENS OFFICIELS À COPIER-COLLER :\n{bloc_liens_dynamique}\n\n"
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
- Actions immédiates étape par étape coulées sur le terrain.

<h3>📁 PROTECTION FONCTIONNELLE ET BOUCLIER LÉGISLATIF</h3>
- Cadre de défense de l'agent (en utilisant impérativement les balises law-highlight).

--- CAPSULE ÉTANCHE ---
Contexte Juridique Local : {extraits_doc}
Question de l'agent : {prompt}
"""
            badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

        elif mode == "peda":
            est_lycee = any(x in prompt_lower for x in ["lycée", "lycee", "bac", "terminale", "première", "premiere", "seconde", "cap", "bac pro"])
            
            niveau_affiche = "Lycée (Baccalauréat / CAP)" if est_lycee else "Cycle 4 (Collège)"
            label_attendu = "Attendus de Fin de Lycée (AFL 1, 2, 3)" if est_lycee else "Attendus de Fin de Cycle 4 (AFC)"
            label_competence = "Axe des compétences visées"

            ca_nom = "CA1 (Performance optimale à une échéance donnée)"
            if est_lycee:
                ca_attendus = "AFL 1 (Moteur) : Produire la meilleure performance possible à une échéance donnée. Choisir et combiner des techniques efficaces, réguler l'allure et stabiliser les appuis.<br>AFL 2 (Méthodologique) : Choisir, concevoir et conduire un engagement corporel pour s'engager dans un programme de préparation ou d'entraînement.<br>AFL 3 (Social) : Assumer de manière autonome les rôles de juge, de starter et de chronométreur officiel. Respecter le protocole de mesure."
                ca_competences = "Concevoir et stabiliser des techniques efficaces. Planifier et réguler sa charge d'entraînement. Gérer la pression de la mesure officielle."
            else:
                ca_attendus = "Produire une performance optimale, mesurable à une échéance donnée. Réaliser des efforts et enchaîner plusieurs actions motrices dans différentes familles pour aller plus vite, plus longtemps, plus haut, plus loin. Assumer les rôles sociaux (juge, chronométreur)."
                ca_competences = "Gérer ses ressources pour Unicode la meilleure performance possible. Se préparer, planifier et s'entraîner individuellement ou collectivement."
            
            if any(x in prompt_lower for x in ["volley", "basket", "hand", "foot", "rugby", "badminton", "tennis", "ping", "boxe", "lutte", "combat"]):
                ca_nom = "CA4 (Affrontement collectif ou interindividuel)"
                if est_lycee:
                    ca_attendus = "AFL 1 (Moteur) : En situation d'opposition, réaliser des actions décisives en situation favorable pour faire basculer le rapport de force (smash, tir, démarquage).<br>AFL 2 (Méthodologique) : Observer, recueillir des données statistiques et anticiper les choix tactiques adverses pour ajuster son projet de jeu en temps réel.<br>AFL 3 (Social) : Co-arbitrer de manière rigoureuse, respecter scrupuleusement les partenaires, les adversaires et les officiels, et accepter le résultat."
                    ca_competences = "Construire un jeu d'intention. Maîtriser le changement de statut attaquant/défenseur. Assurer le déroulement éthique de la rencontre."
                else:
                    ca_attendus = "En situation d'opposition réelle et équilibrée, réaliser des actions décisives en situation favorable pour faire basculer le rapport de force. Être solidaire, coopérer et co-arbitrer."
                    ca_competences = "Rechercher le gain de la rencontre par un projet prenant en compte le rapport de force. S'adapté rapidement au changement de statut."
            
            elif any(x in prompt_lower for x in ["gym", "acro", "danse", "step", "cirque"]):
                ca_nom = "CA3 (Prestation corporelle artistique ou acrobatique)"
                if est_lycee:
                    ca_attendus = "AFL 1 (Moteur) : Composer et interpréter une séquence corporelle de haute maîtrise devant un public. Mobiliser ses capacités expressives et acrobatiques.<br>AFL 2 (Méthodologique) : Utiliser des procédés de composition complexes (unisson, cascade, contrastes) et des outils numériques de régulation pour ajuster la création.<br>AFL 3 (Social) : Assumer un jugement argumenté en référence à un code de pointage, tenez le rôle de pareur (sécurité active) et s'intégrer dans un projet de troupe."
                    ca_competences = "Stabiliser des formes corporelles complexes. Maîtriser les risques et l'esthétique du geste. Formuler un avis critique technique."
                else:
                    ca_attendus = "Mobiliser ses capacités expressives et acrobatiques pour imaginer, composer et interpréter une séquence corporelle devant un public. Participer activement au projet du groupe."
                    ca_competences = "Élaborer et réaliser un projet pour provoquer une émotion ou un message. Utiliser des procédés simples de composition."

            elif any(x in prompt_lower for x in ["muscu", "step", "fitness", "entretien", "ressources", "ca5"]):
                ca_nom = "CA5 (Développement de soi et entretien de la santé)"
                ca_attendus = "AFL 1 (Moteur) : Produire and enchaîner des formes de travail adaptées pour réaliser un projet de développement ou d'entretien de soi (charges en musculation, blocs d'allures en course).<br>AFL 2 (Méthodologique) : Concevoir, réguler et ajuster sa charge de travail et ses temps de récupération en fonction des indicateurs de l'effort (fréquence cardiaque, ressentis) et de son mobile personnel.<br>AFL 3 (Social) : Assumer les rôles de partenaire d'entraînement (conseiller, parer, encourager) et d'observateur. Recueillir des données objectives sur l'effort du camarade."
                ca_competences = "Identification de ses limites et ses mobiles personnels. Maîtriser les postures de sécurité et d'efficience. Analyser ses bilans d'entraînement."    
            
            elif any(x in prompt_lower for x in ["escalade", "orientation", " co ", "vtt", "kayak", "randonnée"]):
                ca_nom = "CA2 (Environnements variés)"
                if est_lycee:
                    ca_attendus = "AFL 1 (Moteur) : Conduire un displacement optimisé, fluide et adapté aux caractéristiques et à l'incertitude du milieu naturel ou recréé.<br>AFL 2 (Méthodologique) : Prévoir, gérer l'itinéraire, le matériel de sécurité et la planification de la trajectoire (lecture de carte, boussole, nœuds).<br>AFL 3 (Social) : Assurer la sécurité absolue de son partenaire (assurage dynamique, parade), co-gérer les crises ou renoncements et respecter la charte éco-citoyenne."
                    ca_competences = "Maîtriser les techniques de réchappe et d'assurage dynamique. Adapter sa vitesse au relief. Respecter la charte éco-citoyenne."
                else:
                    ca_attendus = "Réussir un déplacement planifié dans un milieu naturel ou recréé. Gérer ses ressources pour assurer un parcours sécurisé. Assurer la sécurité du groupe."
                    ca_competences = "Choisir et conduire un déplacement adapté. Prévoir et gérer son déplacement ainsi que le retour. Évaluer les risques."

            mots_apsa = ["volley", "basket", "hand", "foot", "rugby", "badminton", "tennis", "ping", "boxe", "lutte", "gym", "acro", "danse", "step", "muscu", "fitness", "escalade", "orientation", "vtt", "kayak", "relais", "natation"]
            apsa_trouvee = "eps"
            for m in mots_apsa:
                if m in prompt_lower:
                    apsa_trouvee = m
                    break

            liens_html = (
                f"1. <a href='https://edubase.eduscol.education.fr/recherche?q={apsa_trouvee}' target='_blank'>📥 Ressources {apsa_trouvee.upper()} - Base Nationale ÉDUBASE EPS</a><br>"
                f"2. <a href='https://www.google.com/search?q=site:pedagogie.ac-aix-marseille.fr+conservatoire+{apsa_trouvee}' target='_blank'>🎥 {apsa_trouvee.upper()} - Banque de vidéos et fiches du Conservatoire EPS Aix-Marseille</a><br>"
                f"3. <a href='https://www.google.com/search?q=site:education.gouv.fr+{apsa_trouvee}+bulletin+officiel' target='_blank'>🌐 {apsa_trouvee.upper()} - Bulletins Officiels Nationaux sur éducation.gouv.fr</a><br>"
                f"4. <a href='https://www.google.com/search?q=site:pedagogie.ac-aix-marseille.fr+{apsa_trouvee}+projet+cycle' target='_blank'>🌐 {apsa_trouvee.upper()} - Cadres de repères institutionnels Académiques</a><br>"
            )

            consigne_ia = (
                "ROLE : Assistant technique d'extraction institutionnelle. Rendu direct et épuré. Remplis uniquement la structure HTML :\n\n"
                f"<h3>📊 CADRAGE INSTITUTIONNEL ET RÉGLEMENTAIRE - {apsa_trouvee.upper()}</h3>"
                f"<strong>Niveau ciblé : {niveau_affiche} | Champ d'Apprentissage : {ca_nom}</strong><br><br>"
                "<h3>🌐 TEXTES OFFICIELS & REPERES DU BULLETIN OFFICIEL (BO)</h3>"
                "<ul>"
                f"<li><strong>{label_attendu} :</strong><br>{ca_attendus}</li>"
                f"<li><strong>{label_competence} :</strong><br>{ca_competences}</li>"
                "</ul>"
                "<h3>🔍 RESPONSABILITÉ ET CADRE ACADÉMIQUE D'ÉVALUATION</h3>"
                "<ul><li>La conception des fiches de cycle et les critères appartiennent souverainement à l'équipe pédagogique d'établissement sous la supervision des IA-IPR.</li></ul>"
                "<h3>🔍 RESSOURCES EMBARQUÉES ET OUTILS NUMÉRIQUES HOMOLOGUÉS</h3>"
                f"{liens_html}\n\n"
                "--- BARRIÈRE ---\n"
                f"Question du professeur : {prompt}"
            )
            badge, color_card = "🎓 CADRAGE EPS", "peda-card"
            
    # 4. EXÉCUTION ET RENDU HTML
        # --- BLOC DE SÉCURITÉ ULTRA-CIBLÉ (IMMUNE AUX POLLUTIONS WEB) ---
        prompt_lower_eval = prompt.lower()
        est_tasa_direct = mode == "textes" and "tasa" in prompt_lower_eval
        
        est_sss_direct = mode == "ipack" and any(x in prompt_lower_eval for x in [
            "validé par le chef", "valide par le chef", "chef d'établissement", "chef d'etablissement",
            "oublie le bilan", "oublié le bilan", "plus la main", "verrouillé sss", "bloqué sss", "débloquer sss"
        ])
        
        # SÉCURISATION CALENDRIER : Verrou absolu sur les questions de dates et d'échéances pour couper court aux hallucinations
        est_date_notes_direct = any(x in prompt_lower_eval for x in ["date", "quand", "calendrier", "remise", "butoir", "limite", "échéance", "echeance"]) and any(x in prompt_lower_eval for x in ["note", "saisie", "saisir", "rendre", "remettre", "clôture", "cloture", "clore", "lot", "copie", "santorin", "ipack"])
        
        est_santorin_direct = mode == "examens" and any(x in prompt_lower_eval for x in [
            "appréciation", "appreciation", "commentaire", "texte obligatoire", 
            "aucun lot", "pas de lot", "lot manquant", "lot invisible", "boccaccini"
        ])
        
        est_groupes_direct = mode == "ipack" and any(x in prompt_lower_eval for x in [
            "constituer", "creer groupe", "créer groupe", "groupe classe", "groupe-classe", "former mes groupes", "groupes classes"
        ])
        
        est_nouvel_eleve_direct = mode == "ipack" and any(x in prompt_lower_eval for x in [
            "arriv", "nouveau", "nouvel", "ajouter un eleve", "ajouter un élève", "eleve inconnu", "élève inconnu", "nouvelle liste"
        ])
        
        est_bricolage_note = mode == "examens" and any(x in prompt_lower_eval for x in [
            "forcer la note", "prorata", "calculer la note", "bloque les cases", "une seule note", "seule note"
        ])
        
        est_grise_direct = mode == "examens" and any(x in prompt_lower_eval for x in [
            "grisé", "grise", "bloqué", "bloque", "case vide", "pas cliquer", "bouton actif", "boutons aflp"
        ])
        
        est_inapte_santorin_direct = mode == "examens" and any(x in prompt_lower_eval for x in [
            "inapte", "dispense", "dispensé", "sans note", "rien à inscrire", "rien a inscrire", "bordereau"
        ])
        
        est_remplacement_reunion_direct = mode == "examens" and any(x in prompt_lower_eval for x in ["remplace", "remplaç", "remplac"]) and any(x in prompt_lower_eval for x in ["réunion", "reunion", "commission", "convocation", "convoqu"])

        if est_tasa_direct or est_sss_direct:
            texte_brut = extraits_doc.replace("<h3>1. RÈGLE D'OR DE L'ARBORESCENCE IPACK</h3>", "").replace("<h3>1. ANALYSE DES RISQUES INFRA / TECHNIQUE</h3>", "")
            
        elif est_date_notes_direct:
            texte_brut = """
            <h3>📊 CALENDRIER & DATES DE REMISE DES NOTES</h3>
            <strong>Statut administratif : Spécificités académiques locales.</strong><br><br>
            
            <h3>➔ RÈGLE INSTITUTIONNELLE FIXE</h3>
            <ul>
            <li><strong>Notification officielle :</strong> Les dates étant différentes pour chaque académie, je ne suis pas en mesure de vous répondre. Rapprochez-vous de vos correspondants pour avoir cette information.</li>
            </ul>
            
            <h3>📁 CADRE OFFICIEL DE RÉFÉRENCE</h3>
            <ul>
            <li><strong>Source de vérité :</strong> Seuls les calendriers émis par la Division des Examens et Concours (DEC) de votre académie de rattachement et transmis par votre chef d'établissement font foi.</li>
            </ul>
            """
            badge, color_card = ("📊 EXAMENS & SANTORIN" if mode == "examens" else "🛠️ PROTOCOLE IPACK"), ("santorin-card" if mode == "examens" else "general-card")
            
        elif est_groupes_direct:
            texte_brut = """
            <h3>🛠️ IPACKEPS : CONSTITUTION DES CLASSES ET DES GROUPES</h3>
            <strong>Nomenclature officielle : Configuration obligatoire avant tout import d'élèves.</strong><br><br>
            
            <h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>
            <ul>
            <li><strong>Étape 1 (Initialisation) :</strong> Connectez-vous à votre console et accédez au menu supérieur **[Dossiers]**.</li>
            <li><strong>Étape 2 (Nomenclature) :</strong> Allez dans **[Dossier EPS]** > **[Classes]** > **[Configuration des Classes]** pour associer chaque division à son cycle d'enseignement.</li>
            <li><strong>Étape 3 (Filières) :</strong> Basculez sur l'onglet **[Organisation des Classes]** pour valider la répartition réglementaire (Générale, Technologique ou Professionnelle).</li>
            <li><strong>Étape 4 (Peuplement) :</strong> Rendez-vous dans le module **[Mes Élèves]** pour injecter votre fichier d'extraction Pronote ou SIECLE.</li>
            </ul>
            
            <h3>📁 SOURCES, ARTICLES ET TUTORIELS ÉDITEUR</h3>
            <ul>
            <li>🎥 <a href="https://youtu.be/RlScDjd8kHk" target="_blank" style="color: #FFB020 !important; text-decoration: underline; font-weight: bold;">Cliquer ici pour voir le tutoriel vidéo : Import d'élèves depuis Pronote</a></li>
            <li>📥 <a href="https://ipackeps.ac-creteil.fr/spip.php?rubrique2" target="_blank" style="color: #FFB020 !important; text-decoration: underline; font-weight: bold;">Accéder à la Rubrique 2 de la documentation officielle (Structures & Groupes)</a></li>
            </ul>
            """
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
            
        elif est_nouvel_eleve_direct:
            texte_brut = """
            <h3>🛠️ IPACKEPS : AJOUTER UN ÉLÈVE ARRIVANT</h3>
            <strong>Nomenclature officielle : Interdiction absolue de création manuelle isolée dans l'application.</strong><br><br>
            
            <h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>
            <ul>
            <li><strong>Étape 1 (Mise à jour SIÈCLE) :</strong> Assurez-vous auprès du secrétariat de l'établissement que le nouvel élève a bien été enregistré et affecté dans sa classe sur la base nationale <strong>SIÈCLE</strong>.</li>
            <li><strong>Étape 2 (Extraction) :</strong> Générez ou demandez un nouveau fichier d'exportation des élèves (format XML ou CSV) depuis Pronote ou Écoles-Directe.</li>
            <li><strong>Étape 3 (Importation iPack) :</strong> Connectez-vous à iPackEPS, ouvrez le module **[Mes Élèves]** et cliquez sur le bouton officiel **[Importer un fichier d'élèves]**.</li>
            <li><strong>Étape 4 (Fusion des bases) :</strong> Téléversez votre nouveau fichier. L'application va détecter automatiquement le nouvel arrivant et l'ajouter à sa division sans altérer les notes des autres élèves.</li>
            </ul>
            
            <h3>📁 SOURCES, ARTICLES ET TUTORIELS ÉDITEUR</h3>
            <ul>
            <li>🎥 <a href="https://youtu.be/RlScDjd8kHk" target="_blank" style="color: #FFB020 !important; text-decoration: underline; font-weight: bold;">Cliquer ici pour voir le tutoriel vidéo : Import d'élèves depuis Pronote</a></li>
            <li>📥 <a href="https://ipackeps.ac-creteil.fr/spip.php?rubrique2" target="_blank" style="color: #FFB020 !important; text-decoration: underline; font-weight: bold;">Accéder à la Rubrique 2 de la documentation officielle (Structures & Groupes)</a></li>
            </ul>
            """
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
            
        elif est_bricolage_note:
            texte_brut = """
            <h3>🛑 RÉGLEMENTATION CCF : INTERDICTION DE FORCER OU BRICOLER UNE NOTE</h3>
            <strong>Statut juridique : Non-conformité majeure entraînant l'annulation de l'épreuve.</strong><br><br>
            <h3>➔ LA PROCÉDURE RÉGLEMENTAIRE REQUISE (CÔTÉ ENSEIGNANT)</h3>
            <ul>
            <li><strong>Étape 1 (Pas de forcing) :</strong> Ne cherchez pas à remplir artificiellement la case Badminton ou l'APSA manquante. Laissez l'interface verrouillée.</li>
            <li><strong>Étape 2 (Statut Médical) :</strong> Si l'élève est officiellement inapte pour cause de blessure constatée, son statut médical doit être saisi en 'DI' (Dispensé) ou 'Inapte' dans l'onglet des inaptitudes.</li>
            <li><strong>Étape 3 (Remontée administrative) :</strong> Le dossier d'un élève ne disposant que d'une seule note valide à l'année doit être obligatoirement transmis au <strong>Jury Académique</strong> via Cyclades pour arbitrage final.</li>
            </ul>
            <br>
            <h3>📁 CADRE OFFICIEL ET ACCOMPAGNEMENT</h3>
            <ul>
            <li>📥 <a href="https://pole-examens.github.io/tutoriels-examens/co/guide.html" target="_blank" style="color: #FFB020 !important; text-decoration: underline; font-weight: bold;">Cliquez ici pour consulter le Guide Interactif Complet du Pôle Examens</a></li>
            </ul>
            """
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        elif est_grise_direct:
            texte_brut = """
            <h3>📊 EXAMENS & SANTORIN : BOUTONS OU CASES GRISÉES</h3>
            <strong>Statut technique : Conflit de modification ou défaut de sélection de lot.</strong><br><br>
            
            <h3>➔ PROCÉDURE TECHNIQUE DE RÉSOLUTION</h3>
            <ul>
            <li><strong>Cas 1 (Correction partagée - Le plus fréquent) :</strong> Si plusieurs évaluateurs sont affectés au même lot de copies numérisées, dès qu'un collègue ouvre ou édite le dossier d'un élève, l'interface bascule en lecture seule (boutons grisés) pour tous les autres correcteurs. <strong>Solution : Attendez que votre collègue ferme la copie ou se déconnecte.</strong></li>
            <li><strong>Cas 2 (Défaut de sélection active) :</strong> Les cases restent bridées tant que le lot n'est pas déplié. <strong>Solution : Allez dans l'onglet [Lots], cliquez sur [Voir le détail], puis sélectionnez le nom du candidat pour activer la grille.</strong></li>
            </ul>
            
            <h3>📁 CADRE OFFICIEL ET ACCOMPAGNEMENT</h3>
            <ul>
            <li>📥 <a href="https://pole-examens.github.io/tutoriels-examens/co/guide.html" target="_blank" style="color: #FFB020 !important; text-decoration: underline; font-weight: bold;">Cliquez ici pour consulter le Guide Interactif Complet du Pôle Examens</a></li>
            </ul>
            """
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        elif est_inapte_santorin_direct:
            texte_brut = """
            <h3>📊 EXAMENS & SANTORIN : ÉLÈVES INAPTES ET ABSENTS AU CCF</h3>
            <strong>Cadre réglementaire académique : Saisie obligatoire des notes particulières dans l'interface de notation.</strong><br><br>
            
            <h3>➔ PROCÉDURE TECHNIQUE DE SAISIE (DIRECTIVES DIEC / DEC AIX-MARSEILLE)</h3>
            <ul>
            <li><strong>Étape 1 (Accès Mission) :</strong> Connectez-vous à Arena, ouvrez l'activité **[Portail d'accès aux missions]** puis sélectionnez votre mission **[Notation EPS CCF]**.</li>
            <li><strong>Étape 2 (Ouverture du Lot) :</strong> Dans votre tableau de bord Santorin, ouvrez votre lot d'APSA et cliquez sur l'icône "crayon" d'accès à la notation du candidat concerné.</li>
            <li><strong>Étape 3 (Saisie de la Note Particulière) :</strong> Dans la zone de notation de l'APSA, n'entrez pas de points AFL, mais ouvrez le menu déroulant officiel des **[Notes particulières]** :</li>
            <ul>
                <li>🔹 <strong>Dispense (DI) :</strong> À sélectionner si l'élève présente un certificat médical d'inaptitude valide. Cela neutralise l'APSA (elle sort de la moyenne sans pénaliser l'élève).</li>
                <li>🔹 <strong>Absent (AB) :</strong> À sélectionner en cas d'absence non justifiée lors de l'évaluation (vaut note zéro).</li>
                <li>🔹 <strong>Épreuve de substitution :</strong> À cocher si l'élève est renvoyé à la session de rattrapage (motif : *Inapte* ou *Force majeure*).</li>
            </ul>
            <li><strong>Étape 4 (Cas des SHN) :</strong> Pour les Sportifs de Haut Niveau, le clic sur le crayon ouvre un volet spécifique permettant d'appliquer la note réglementaire de 20/20.</li>
            </ul>
            
            <h3>📁 CADRE OFFICIEL ET ACCOMPAGNEMENT</h3>
            <ul>
            <li>📥 <a href="https://www.pedagogie.ac-aix-marseille.fr/upload/docs/application/pdf/2024-03/webinaire_utilisation_de_santorin.pdf" target="_blank" style="color: #FFB020 !important; text-decoration: underline; font-weight: bold;">Cliquez ici pour télécharger le Webinaire de Formation Officiel Santorin EPS (Académie d'Aix-Marseille)</a></li>
            </ul>
            """
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        elif est_remplacement_reunion_direct:
            texte_brut = """
            <h3>📊 EXAMENS & SANTORIN : REMPLACEMENT EN SOUS-COMMISSION / JURY</h3>
            <strong>Statut juridique : Ordre de mission nominatif impératif avant tout déplacement.</strong><br><br>
            
            <h3>➔ PROCÉDURE TECHNIQUE & ADMINISTRATIVE IMMÉDIATE</h3>
            <ul>
            <li><strong>Étape 1 (Alerte Secrétariat) :</strong> Le secrétariat de direction de l'établissement doit contacter immédiatement le gestionnaire de l'examen au sein de la Division des Examens et Concours (DEC) du Rectorat.</li>
            <li><strong>Étape 2 (Régularisation nominative) :</strong> Demander l'émission d'un modificatif officiel de convocation ou d'un ordre de mission exprès au nom de l'enseignant remplaçant pour valider sa couverture juridique (accidents de trajet) et ses frais Chorus DT.</li>
            <li><strong>Étape 3 (Bascule Santorin / Imag'in) :</strong> Si le remplacement inclut la notation, le secrétariat doit valider la suppléance sur Imag'in et cliquer sur l'icône [PDF] pour injecter les accès de l'agent.</li>
            </ul>
            
            <h3>📁 CADRE OFFICIEL ET RECOMMANDATIONS</h3>
            <ul>
            <li>📁 <span class="law-highlight">Code de l'éducation</span> : La participation aux jurys d'examens nationaux constitue une obligation statutaire. L'exercice de cette mission is conditionné à la détention d'un titre de convocation régulier émis par l'autorité académique.</li>
            </ul>
            """
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        else:
            response = Settings.llm.complete(consigne_ia) 
            texte_brut = response.text
        # --- FIN DU BLOC DE SÉCURITÉ ---
        
        # Filtre Regex de sécurité pour forcer l'affichage orange des textes de loi si l'IA en oublie
        texte_brut = re.sub(r'(Article\s+\d+[-–\w]*|Loi\s+du\s+\d+\s+\w+\s+\d+|RGPD|Règlement\s+général\s+sur\s+les\s+données|Code\s+de\s+l\'éducation|Code\s+civil|Loi\s+du\s+15\s+mars\s+2004)', r'<span class="law-highlight">\1</span>', texte_brut)
        texte_brut = texte_brut.replace('<span class="law-highlight"><span class="law-highlight">', '<span class="law-highlight">').replace('</span></span>', '</span>')
        
        texte_brut = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">\1</a>', texte_brut)
        
        # 🧼 FILTRE MASTER DE PROTECTION : Supprime toute trace de réflexion ou de justifications sémantiques de l'IA
        lignes_nettoyees = []
        for ligne in texte_brut.split("<br>"):
            if any(p in ligne.lower() for p in ["analyse des risques", "pourquoi je réponds", "en tant qu'ia", "consignes cachées", "voici la structure"]):
                continue
            lignes_nettoyees.append(ligne)
        texte_brut = "<br>".join(lignes_nettoyees)
        
        # Capture des liens YouTube sécurisée
        youtube_links = re.findall(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11}))', texte_brut)

        # Rendu visuel propre et direct
        if mode == "peda" or est_tasa_direct or est_sss_direct or est_santorin_direct or est_groupes_direct or est_nouvel_eleve_direct or est_grise_direct or est_bricolage_note or est_inapte_santorin_direct or est_remplacement_reunion_direct or est_date_notes_direct:
            texte_final = texte_brut.replace("\n", "").replace("\r", "").replace("<p>", "").replace("</p>", "<br>")
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br>{texte_final}</div>'
        else:
            texte_final = texte_brut.replace(chr(10), "<br>")
            formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_final}</div>'
            
        st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
        
        for link in youtube_links:
            st.video(link[0])
        st.rerun()
