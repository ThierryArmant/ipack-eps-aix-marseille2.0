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
    
    /* Boutons Inactifs */
    button[kind="secondary"] { 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        color: #94A3B8 !important; 
        border: 1px solid rgba(255,255,255,0.05) !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
        padding: 12px 10px !important;
        transition: all 0.3s ease;
    }

    /* Boutons Actifs */
    button[kind="primary"] {
        background-color: rgba(16, 185, 129, 0.85) !important;
        color: #FFFFFF !important;
        border: 1px solid #10B981 !important;
        border-radius: 8px !important; 
        font-size: 13px !important; 
        padding: 12px 10px !important;
        box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.6) !important;
        font-weight: 700 !important;
    }
    
    /* BOUTON NETTOYER */
    div.element-container:has(.nettoyer-wrapper) + div.element-container button {
        background-color: rgba(220, 38, 38, 0.45) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(220, 38, 38, 0.6) !important;
        border-radius: 8px !important;
        padding: 7px 10px !important;
        width: 100% !important;
    }
    div.element-container:has(.nettoyer-wrapper) + div.element-container button:hover {
        background-color: rgba(220, 38, 38, 0.65) !important;
    }
    
    /* CARTES DE RÉPONSE */
    .santorin-card, .general-card, .securite-card { 
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
    
    .santorin-card p, .general-card p, .securite-card p, .santorin-card div, .general-card div, .securite-card div, .santorin-card span, .general-card span, .securite-card span, .santorin-card li, .general-card li, .securite-card li { 
        color: #FFFFFF !important; 
        font-size: 15px !important; 
        line-height: 1.6 !important; 
        font-weight: 400 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }
    .santorin-card strong, .general-card strong, .securite-card strong {
        font-weight: 700 !important; 
        color: #FFFFFF !important;
    }

    .santorin-card a, .general-card a, .securite-card a, .santorin-card a *, .general-card a *, .securite-card a * {
        color: #FFB020 !important; 
        text-decoration: underline !important;
        font-weight: 600 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.9) !important;
    }
    .santorin-card a:hover, .general-card a:hover, .securite-card a:hover {
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
    
    /* LIGNE AJOUTÉE POUR FORCER LE BLANC DANS LE CHAT */
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

# Fonction pour obtenir la date de modification du fichier pour vider le cache automatiquement s'il change
def obtenir_cle_fichier():
    chemin = "gere_par_pierre.txt"
    if os.path.exists(chemin):
        return os.path.getmtime(chemin)
    return 0.0

# Lecture dynamique sans cache pour prendre en compte tes modifs immédiatement
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

# BASE DE CONNAISSANCES FIXE : EXAMENS & SANTORIN
@st.cache_resource
def initialiser_base_santorin(cle_fremt):
    docs_santorin = [
        Document(
            text="""Fiche Mémo - Correction Partagée Santorin (DEC / Assistance). 
            La correction partagée ou multiple permet à plusieurs évaluateurs/correcteurs d'intervenir sur un même lot de copies. 
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

# BASE DE CONNAISSANCES FIXE : IPACKEPS
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

# BASE DE CONNAISSANCES FIXE : TEXTES & CADRES RÉGLEMENTAIRES
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
    "general": "🔍 Mode Actif : Questions Pédagogiques, Didactiques & Pratiques de Terrain",
    "textes": "🔒 Mode Actif : Sécurité & Responsabilité Juridique (Textes Officiels & Risques APPN)"
}

# Initialisation par sécurité si active_module n'existe pas
if "active_module" not in st.session_state:
    st.session_state.active_module = "general"

# Utilisation de .get() pour éviter le plantage si la clé n'est pas dans le dictionnaire
titre_affiche = label_titres.get(st.session_state.active_module, "🔍 Mode Actif : Questions Pédagogiques")

st.markdown(f"""
    <div class="column-title-top">
        <span class="instruction">⚙️ Choisissez le contexte de votre question ci-dessous</span>
        <span class="mode-actuel">{titre_affiche}</span>
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
    if st.button("Examens\n& Santorin", use_container_width=True, key="btn_ex", type="primary" if st.session_state.active_module == "examens" else "secondary"):
        st.session_state.active_module = "examens"
        st.session_state.messages_hub = []
        st.rerun()

with col_b3:
    if st.button("🔍 Pédagogie &\nDidactique", use_container_width=True, key="btn_ge", type="primary" if st.session_state.active_module == "general" else "secondary"):
        st.session_state.active_module = "general"
        st.session_state.messages_hub = []
        st.rerun()

with col_b4:
    if st.button("Sécurité &\nCadres Règl.", use_container_width=True, key="btn_se", type="primary" if st.session_state.active_module == "textes" else "secondary"):
        st.session_state.active_module = "textes"
        st.session_state.messages_hub = []
        st.rerun()

# ======================================================================
# 7B. MESSAGES D'AVERTISSEMENT DYNAMIQUES (SOUS LES BOUTONS)
# ======================================================================
if st.session_state.active_module == "textes":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            ⚠️ <strong>Avertissement important – Limites du module IA :</strong> Cet outil est un assistant numérique destiné à faciliter vos recherches documentaires. Bien que ses règles d'analyse soient strictes, les réponses générées ne se substituent en aucun cas aux textes officiels.<br>
            Pour toute question d'ordre juridique ou en cas de sinistre, rapprochez-vous impérativement de : <strong>Votre Chef d'établissement, votre Secrétariat d'examen, ou votre IA-IPR.</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.active_module == "general":
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            💡 <strong>Exemples de recherches dans cet onglet :</strong> Projets pédagogiques, compétences visées, fonctionnement de l'AS / UNSS, gestion de classe, ressources par APSA, projets transversaux (SRE, Savoir Rouler, etc.).
        </span>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            ⚠️ <strong>Conseil Flux Mixtes :</strong> Certaines questions touchent à la fois à la technique (iPackEPS) et à la réglementation (Santorin). N'hésitez pas à tester votre recherche dans ces deux onglets pour croiser les sources.
        </span>
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

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": f"<span style='color: white;'>{prompt}</span>"})
    
    with st.spinner("Je réfléchis à la meilleure réponse pour toi..."):
        extraits_doc = ""
        mode = st.session_state.active_module
        
        # 1. MOTEUR WEB (Tavily)
        if tavily_api_key:
            try:
                if mode == "textes":
                    requete_blindee = f"{prompt} jurisprudence administrative responsabilité commune EPS"
                    domains = ["legifrance.gouv.fr", "education.gouv.fr", "eduscol.education.gouv.fr"]
                elif mode == "examens":
                    requete_blindee = f"{prompt} réglementation examen Santorin Cyclades"
                    domains = ["education.gouv.fr", "pedagogie.ac-aix-marseille.fr", "eps.ac-creteil.fr"]
                elif mode == "ipack":
                    requete_blindee = f"site:ipackeps.ac-creteil.fr/spip.php?rubrique4 {prompt}"
                    domains = ["ipackeps.ac-creteil.fr"]
                    exclude = ["youtube.com"]
                elif mode == "peda":
                    requete_blindee = f"{prompt} fiche pédagogique EPS cycle 4 filetype:pdf"
                    domains = ["eduscol.education.gouv.fr", "eps.ac-versailles.fr", "eps.ac-creteil.fr", "pedagogie.ac-aix-marseille.fr"]
                else:
                    requete_blindee = f"{prompt} EPS programme officiel"
                    domains = ["eduscol.education.gouv.fr", "unss.org"]
                
                payload = {"api_key": tavily_api_key, "query": requete_blindee, "search_depth": "advanced", "include_domains": domains}
                if mode == "ipack": payload["exclude_domains"] = exclude
                
                res = requests.post("https://api.tavily.com/search", json=payload, timeout=15)
                if res.status_code == 200:
                    for item in res.json().get("results", []): 
                        extraits_doc += f"Source Web ({item['title']}): {item['content']}\n\n"
            except: pass

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
                    for n in retriever_peda.retrieve(prompt): extraits_doc += f"Référentiel Pédagogique EPS : {n.node.text}\n\n"
            except: pass

        # 3. IDENTITÉ ET PERSONNALITÉ (FILTRE PIERRE)
        règles_or = "RÈGLES D'OR : 1. Loi 1937 (Substitution État). 2. Règle 11 (Structure=Mairie/EPI=Prof). 3. Examens = Mission impérative."
        filtre_pierre = (
            "\n\nMÉTHODE DE RÉPONSE OBLIGATOIRE (Le 'Filtre Pierre') :\n"
            "1. ANALYSE DES RISQUES : Identifie l'impact sur outils tiers (Pronote, Cyclades, Mairie).\n"
            "2. PROCÉDURE TECHNIQUE : Utilise des étapes fléchées (→).\n"
            "3. PROTECTION FONCTIONNELLE : Indique la traçabilité et l'écrit nécessaire."
        )
        
        if mode == "ipack":
            consigne_ia = (
                f"{règles_or}{filtre_pierre}\nTu es l'expert technique iPackEPS.\n"
                "MATRICE D'EXTRACTION : Si le sujet concerne 'classe' ou 'edt', tu DOIS inclure en fin de réponse : "
                "'Tutoriel officiel à consulter : https://youtu.be/tu8J1RBUTwk'\n"
                "CONSIGNE SÉCURITÉ : Ne JAMAIS FORCER LA SUPPRESSION (fusionner ou ajuster les dates).\n"
                f"Contexte : {extraits_doc}\nQuestion : {prompt}"
            )
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
        elif mode == "examens":
            consigne_ia = f"{règles_or}{filtre_pierre}\nTu es l'expert Santorin/Cyclades.\nCanva: [Acteur|Action|Conséquence].\nContexte: {extraits_doc}\nQuestion: {prompt}"
            badge, color_card = "📊 RÉGLEMENTATION SANTORIN", "santorin-card"
        elif mode == "textes":
            consigne_ia = f"{règles_or}{filtre_pierre}\nTu es l'expert juridique EPS.\nCanva: 1. SITUATION, 2. ARBITRAGE (Règle 11), 3. RECOURS.\nContexte: {extraits_doc}\nQuestion: {prompt}"
            badge, color_card = "⚖️ CADRE JURIDIQUE", "securite-card"
        elif mode == "peda":
            consigne_ia = (
                f"{règles_or}{filtre_pierre}\nTu es l'Expert Pédagogique EPS.\n"
                "MISSION : Tu parcours les sites académiques pour trouver des fiches pédagogiques prêtes à l'emploi.\n"
                "RÈGLE D'OR : Si tu trouves un document, affiche le lien direct de téléchargement (URL).\n"
                "CANVA : 1. Compétences (Cycle 4), 2. Situation, 3. Indicateurs de réussite.\n"
                f"Contexte : {extraits_doc}\nQuestion : {prompt}"
            )
            badge, color_card = "🔍 CONSEILLER PÉDAGOGIQUE", "general-card"
        else:
            consigne_ia = f"{règles_or}{filtre_pierre}\nTu es l'Expert Pédagogique EPS.\nContexte: {extraits_doc}\nQuestion: {prompt}"
            badge, color_card = "🔍 CONSEILLER PÉDAGOGIQUE", "general-card"

        # 4. EXÉCUTION ET RENDU HTML
        response = Settings.llm.complete(consigne_ia)
        texte_brut = response.text
        
        # EXTRACTION MULTIPLE (re.findall capture TOUS les liens)
        youtube_links = re.findall(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11}))', texte_brut)
        
        # Traitement tableaux
        if "|" in texte_brut and "---" in texte_brut:
            lignes = [l.strip() for l in texte_brut.split("\n") if l.strip()]
            html_table = '<table style="width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; background-color: rgba(30, 41, 59, 0.7); border-radius: 8px; overflow: hidden;">'
            est_entete = True
            for ligne in lignes:
                if ligne.startswith("|") and not any(c in ligne for c in ["---", "==="]):
                    cells = [c.strip() for c in ligne.split("|")[1:-1]]
                    html_table += "<tr>"
                    for cell in cells:
                        if est_entete: html_table += f'<th style="background-color: #38BDF8 !important; color: #0F172A !important; padding: 10px; text-align: left; font-size: 14px;">{cell}</th>'
                        else: html_table += f'<td style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #FFFFFF !important; font-size: 14px;">{cell}</td>'
                    html_table += "</tr>"
                    est_entete = False
            html_table += "</table>"
            texte_brut = re.sub(r'\|.*\|(\n\|.*\|)*', html_table, texte_brut)

        texte_html = texte_brut.replace(chr(10), "<br>")
        formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_html}</div>'
        st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
        
        # AFFICHAGE MULTIPLE DES VIDÉOS (ton filet de sécurité)
        for link in youtube_links:
            st.session_state.messages_hub.append({"role": "assistant", "content": f"st.video('{link[0]}')"})
        
        st.rerun()
