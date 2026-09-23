import base64
import datetime
import os
import re
import smtplib
import requests
import streamlit as st
from email.mime.text import MIMEText
from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# ======================================================================
# 📊 CONFIGURATION GOOGLE SHEETS LOGS (QUESTIONS HUB)
# ======================================================================
WEBHOOK_URL = (
    "https://script.google.com/macros/s/AKfycbyVq8_DCLnAyrr7xEUw1Xbdze0Lm1S-P6RHlXJPE2CmaBD39lpFfQjpuHQhxmL0z3bJ/exec"
)


def log_interaction(question, reponse, mode="", contexte="", niveau=""):
    payload = {
        "question": question, 
        "reponse": reponse,
        "mode": mode,
        "contexte": contexte,
        "niveau": niveau
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Erreur de log Google Sheet : {e}")


# ======================================================================
# 🛡️ CONTOURNEMENT NLTK & IMPORT TAVILY
# ======================================================================
import nltk

try:
    nltk_data_dir = os.path.join(os.path.expanduser("~"), "nltk_data")
    os.makedirs(nltk_data_dir, exist_ok=True)
    nltk.data.path.append(nltk_data_dir)
    nltk.download("punkt", download_dir=nltk_data_dir, quiet=True)
    nltk.download("stopwords", download_dir=nltk_data_dir, quiet=True)
except Exception:
    pass

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

# ======================================================================
# 🚀 ZONE 1 : LE RÉPERTOIRE DES VIDÉOS (CONSTANTE GLOBALE)
# ======================================================================
VIDEOS_TUTOS = {
    "import_eleves_pronote.mp4": "https://www.youtube.com/watch?v=RlScDjd8kHk",
    "Configuration_classes_import_eleves.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Configuration_classes_import_eleves.mp4",
    "affecter_eleves_dans_groupes.mp4": "https://pole-examens.github.io/tutoriels-examens/res/affecter_eleves_dans_groupes.mp4",
    "Generer_importer_fichier_groupes_cyclades.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Generer_importer_fichier_groupes_cyclades.mp4",
    "verification_affectation_protocoles_cyclades.mp4": "https://pole-examens.github.io/tutoriels-examens/res/verification_affectation_protocoles_cyclades.mp4",
    "creer_convocations_enseignants.mp4": "https://pole-examens.github.io/tutoriels-examens/res/creer_convocations_enseignants.mp4",
    "Distribution_lots_santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Distribution_lots_santorin.mp4",
    "Distribution_manuelle_lots_santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Distribution_manuelle_lots_santorin.mp4",
    "Saisie_notes_Santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Saisie_notes_Santorin.mp4",
    "Verrouiller_lot_santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Verrouiller_lot_santorin.mp4",
    "Deverrouiller_lots_santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Deverrouiller_lots_santorin.mp4",
    "Ajouter_evaluateur_lot_santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Ajouter_evaluateur_lot_santorin.mp4",
    "Protocoles_adaptes_iPackEPS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Protocoles_adaptes_iPackEPS.mp4",
    "Extraction_notes_Santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Extraction_notes_Santorin.mp4",
    "Import_documents_glisser_deposer.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Import_documents_glisser_deposer.mp4",
    "Import_automatique_eleves.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Import_automatique_eleves.mp4",
    "Actualisation_equipe_classes.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Actualisation_equipe_classes.mp4",
    "Gestion_inventaire_EPI_photos.mp4": "https://www.youtube.com/watch?v=dpijdybbbWo",
    "Controle_dates_CM_CAHPN.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Controle_dates_CM_CAHPN.mp4",
    "Export_zip_documents_certificatifs.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Export_zip_documents_certificatifs.mp4",
    "Evolution_et_fermeture_SSS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Evolution_et_fermeture_SSS.mp4",
    "Signature_chef_etablissement_SSS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Signature_chef_etablissement_SSS.mp4",
    "Export_profs_externes_cyclades.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Export_profs_externes_cyclades.mp4",
    "Rapport_etat_serveurs.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Rapport_etat_serveurs.mp4",
    "Gestion_dossier_APPN.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Gestion_dossier_APPN.mp4",
    "Configuration_modules_SSS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Configuration_modules_SSS.mp4",
    "Depot_referentiels_iPackEPS.mp4": "https://youtu.be/T_-j01ovoA4",
    "Supprimer_apsas_non_certificatives.mp4": "https://youtu.be/ksCcLEe2lP8",
    "Saisie_protocoles_iPackEPS.mp4": "https://youtu.be/Bq7_ooQuZtU",
    "EDT_Introduction.mp4": "https://youtu.be/uCF9kxUDaI8",
    "EDT_Creation_Suppression.mp4": "https://youtu.be/8pHcZ4gw6go",
    "EDT_Semaines_A_B.mp4": "https://youtu.be/zi7K-hkYzig",
    "EDT_Verification_Alertes.mp4": "https://youtu.be/vnY5hfKzN08",
    "Gestion_remplacements.mp4": "https://youtu.be/C3gSSacJxNo",
    "Etablissements_etrangers_AEFE.mp4": "https://youtu.be/x8DzrCRL_D8",
    # --- NOUVEAUX TUTOS INTÉGRÉS DEPUIS LA DOCUMENTATION CRÉTEIL ---
    "Depot_documents_commission.mp4": "https://youtu.be/FZ1KSuuKkEA",
    "Proposer_dossier_commission.mp4": "https://youtu.be/JmhwQNyagOI",
    "Demande_ouverture_SSS.mp4": "https://youtu.be/SizZ4vGQ4nU",
    "Projet_annuel_SSS.mp4": "https://youtu.be/7yr1bFlvlFg",
    "Bilan_annuel_SSS.mp4": "https://youtu.be/iH54YEF_2XY",
    "Export_eleves_cyclades.mp4": "https://youtu.be/YoOC_CdOQ_I",
    "Controler_reaffecter_protocoles_cyclades.mp4": "https://youtu.be/0njoZigh_5w",
    "Creer_protocole_cours_annee.mp4": "https://youtu.be/57xZDq_vyDE",
    "Deplacer_eleves_lots_santorin.mp4": "https://youtu.be/WKbg51eUQVs",
    "Attribuer_second_correcteur_santorin.mp4": "https://youtu.be/fmMl82KkZt4",
    "Gestion_cas_exceptionnels_santorin.mp4": "https://youtu.be/E2VMoq7sLgI",
    "Export_fichier_notes_santorin.mp4": "https://youtu.be/KooSwcy4gAA",
    "Extraire_liste_inaptes_santorin.mp4": "https://youtu.be/3ThO5nLNzJg",
}

# ======================================================================
# 1. CONFIGURATION DE L'APPLICATION
# ======================================================================
st.set_page_config(
    page_title="Hub IA - EPS",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- INJECTION CSS POUR HARMONISER LES BULLES DE CHAT ---
st.markdown("""
<style>
/* Cibler toutes les bulles de chat (Utilisateur et IA) pour harmoniser le fond */
div[data-testid="stChatMessage"] {
    background-color: rgba(45, 45, 45, 0.85) !important; /* Couleur sombre translucide */
    color: white !important; /* Texte en blanc */
    border-radius: 10px; /* Bords arrondis */
    padding: 15px; /* Espace à l'intérieur de la bulle */
}

/* Forcer le texte de la question de l'utilisateur en blanc */
div[data-testid="stChatMessage"] p {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ======================================================================
# 2. GESTION DE LA MÉMOIRE ET DU COMPTEUR DE VISITES & ÉTATS DE VALIDATION
# ======================================================================
st.set_page_config(
    page_title="Hub IA - EPS",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ======================================================================
# 2. GESTION DE LA MÉMOIRE ET DU COMPTEUR DE VISITES & ÉTATS DE VALIDATION
# ======================================================================
if "messages_hub" not in st.session_state:
    st.session_state.messages_hub = []
if "active_module" not in st.session_state:
    st.session_state.active_module = None
if "niveau_actif_form" not in st.session_state:
    st.session_state.niveau_actif_form = None
if "contexte_valide" not in st.session_state:
    st.session_state.contexte_valide = False
if "public_valide" not in st.session_state:
    st.session_state.public_valide = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "reset_steps" not in st.session_state:
    st.session_state.reset_steps = False

# 🔄 RÉINITIALISATION TOTALE DES ÉTAPES POUR PERMETTRE UN NOUVEAU CHOIX DE CONTEXTE
if st.session_state.reset_steps:
    st.session_state.contexte_valide = False
    st.session_state.public_valide = False
    st.session_state.active_module = None
    st.session_state.niveau_actif_form = None
    st.session_state.reset_steps = False


def incrementer_et_obtenir_visites():
    fichier_compteur = "compteur_visites.txt"
    if not os.path.exists(fichier_compteur):
        try:
            with open(fichier_compteur, "w", encoding="utf-8") as f:
                f.write("1")
            return 1
        except Exception:
            return 1

    try:
        with open(fichier_compteur, "r", encoding="utf-8") as f:
            valeur = int(f.read().strip())

        if "visite_comptabilisee" not in st.session_state:
            valeur += 1
            with open(fichier_compteur, "w", encoding="utf-8") as f:
                f.write(str(valeur))
            st.session_state.visite_comptabilisee = True

        return valeur
    except Exception:
        return 1


nb_visites_reel = incrementer_et_obtenir_visites()

# ======================================================================
# 3. INTERFACE GRAPHIQUE ET CHARGEMENT LOCAL DES IMAGES (BASE64)
# ======================================================================
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

img_gauche = get_base64_image("image_7.png")
img_eps = get_base64_image("image_6.png")
img_droite = get_base64_image("image_5.png")
img_fond = get_base64_image("image_8.png")

css_pur = f"""
    <style>
    .santorin-card, .santorin-card *, .general-card, .general-card *, .securite-card, .securite-card * {{ 
        color: #FFFFFF !important;  
    }}

    .block-container {{ 
        padding-top: 0.5rem !important; 
        padding-bottom: 2rem !important; 
        padding-left: 1.5rem !important; 
        padding-right: 1.5rem !important; 
        max-width: 920px !important; 
    }}
    
    .stApp {{ background-image: url('data:image/png;base64,{img_fond}') !important; background-size: cover !important; background-attachment: fixed !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    
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
    
    .hub-title {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        flex-grow: 1;
        padding-right: 35px; 
    }}
    
    .title-row {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
    }}
    
    .title-row h1 {{ 
        color: white !important; 
        margin: 0 !important; 
        font-size: 28px !important; 
        font-weight: 800 !important; 
        line-height: 1.2 !important;
        letter-spacing: 0.5px;
    }}
    
    .badge-visiteur {{ 
        background-color: rgba(16, 185, 129, 0.2) !important; 
        color: #10B981 !important; 
        border: 1px solid rgba(16, 185, 129, 0.45) !important; 
        padding: 3px 12px !important; 
        border-radius: 20px !important; 
        font-size: 13px !important; 
        font-weight: 800 !important; 
        font-family: monospace !important;
    }}
    
    .hub-title p {{ 
        color: #94A3B8 !important; 
        margin: 0 !important; 
        margin-top: -1px !important; 
        font-size: 13px !important; 
        text-transform: uppercase; 
        font-weight: bold !important;
    }}

    .column-title-top {{ 
        color: #FFFFFF; 
        text-align: center; 
        margin-bottom: 12px !important; 
        background-color: #1E293B; 
        border-radius: 6px !important; 
        padding: 10px 12px; 
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2); 
    }}
    .column-title-top .instruction {{ 
        font-size: 13px !important; 
        font-weight: 800 !important; 
        text-transform: uppercase; 
        color: #FFFFFF !important; 
        display: block; 
        margin-bottom: 3px;
    }}
    .column-title-top .mode-actuel {{ 
        font-size: 14px !important; 
        font-weight: 800 !important; 
        color: #FFFFFF !important; 
        display: block; 
    }}

    button[kind="secondary"] {{ 
        background-color: #1E293B !important; 
        color: #FFFFFF !important; 
        border: 1px solid #334155 !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
        font-weight: 800 !important; 
        height: 55px !important; 
        display: inline-flex !important; 
        align-items: center !important; 
        justify-content: center !important; 
        text-align: center !important; 
    }}

    button[kind="primary"] {{ 
        background-color: #10B981 !important; 
        color: #FFFFFF !important; 
        border: 1px solid #059669 !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
        font-weight: 800 !important; 
        box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.4) !important; 
        height: 55px !important; 
        display: inline-flex !important; 
        align-items: center !important; 
        justify-content: center !important; 
        text-align: center !important; 
    }}
    
    div[data-testid="stRadio"] {{
        background-color: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 12px 15px !important;
        margin-bottom: 12px !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.4);
    }}

    div[data-testid="stRadio"] > label {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        margin-bottom: 8px !important;
    }}

    div[data-testid="stRadio"] div[role="radiogroup"] label p, 
    div[data-testid="stRadio"] div[role="radiogroup"] label span, 
    div[data-testid="stRadio"] div[role="radiogroup"] label {{
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
    }}
    
    .santorin-card, .general-card, .securite-card {{ 
        background-color: rgba(15, 23, 42, 0.45) !important; 
        backdrop-filter: blur(12px) !important; 
        -webkit-backdrop-filter: blur(12px) !important; 
        padding: 18px; 
        border-radius: 8px; 
        margin-bottom: 16px; 
        line-height: 1.6 !important;
    }}
    .santorin-card {{ border-left: 6px solid #38BDF8 !important; }} 
    .general-card {{ border-left: 6px solid #10B981 !important; }} 
    .securite-card {{ border-left: 6px solid #FF9F43 !important; }} 
    
    .santorin-card h3, .general-card h3, .securite-card h3 {{ 
        color: #38BDF8 !important; 
        font-size: 16px !important; 
        margin-top: 14px !important; 
        margin-bottom: 8px !important; 
        font-weight: 800 !important; 
        text-transform: uppercase; 
    }}
    .general-card h3 {{ color: #10B981 !important; }} 
    .securite-card h3 {{ color: #FF9F43 !important; }} 

    .santorin-card ul, .general-card ul, .securite-card ul,
    .santorin-card ol, .general-card ol, .securite-card ol {{
        margin-top: 6px !important;
        margin-bottom: 10px !important;
        padding-left: 22px !important;
    }}
    .santorin-card li, .general-card li, .securite-card li {{
        margin-bottom: 7px !important;
        line-height: 1.5 !important;
    }}

    .law-highlight {{ 
        background-color: rgba(255, 176, 32, 0.12) !important; 
        color: #FFB020 !important; 
        padding: 2px 6px; 
        border-radius: 4px; 
        border: 1px solid rgba(255, 176, 32, 0.4) !important; 
        font-weight: 700 !important; 
    }}

    div[data-testid="stForm"] {{
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 10px !important;
        margin-bottom: 12px !important;
    }}

    .img-zoomable {{
        transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1), box-shadow 0.3s ease;
        cursor: zoom-in;
        border-radius: 6px;
    }}
    .img-zoomable:hover {{
        transform: scale(3);
        transform-origin: top right;
        z-index: 999999;
        position: relative;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
    }}
    .img-zoomable:active {{
        transform: scale(4.5);
        transform-origin: top right;
        cursor: zoom-out;
    }}
    </style> 
"""
st.markdown(css_pur, unsafe_allow_html=True)


# ======================================================================
# 4. CONFIGURATION DE L'IA & CHARGEMENT DES BASES
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")
admin_secret_key = st.secrets.get("ADMIN_PASSWORD", "thierryAdmin2026")
tavily_client = None
if tavily_api_key and TavilyClient:
    try:
        tavily_client = TavilyClient(api_key=tavily_api_key)
    except Exception:
        pass

if openai_api_key:
    Settings.llm = OpenAI(
        model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key
    )
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small", api_key=openai_api_key
    )


def obtenir_cle_fichier():
    mtimes = []
    for fp in ["data/examens/memoire_examens_santorin.txt", "ipack.txt", "data/textes/partenariats_defense_citoyennete.txt"]:
        if os.path.exists(fp):
            try:
                mtimes.append(os.path.getmtime(fp))
            except Exception:
                pass
    chemin_textes = "data/textes/base_textes_officiels.txt"
    if os.path.exists(chemin_textes):
        try:
            mtimes.append(os.path.getmtime(chemin_textes))
        except Exception:
            pass
    for dossier in ["data/examens", "data/ipack", "data/textes", "data/peda", "data/textes/premier_degré"]:
        if os.path.exists(dossier) and os.path.isdir(dossier):
            try:
                for f in os.listdir(dossier):
                    mtimes.append(os.path.getmtime(os.path.join(dossier, f)))
            except Exception:
                pass
    return max(mtimes) if mtimes else 0.0


def charger_consignes_examens():
    documents_charges = []
    fp = "data/examens/memoire_examens_santorin.txt"
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                documents_charges.append(
                    Document(
                        text=f.read(),
                        metadata={"source": f"Mémoire Examens & Santorin ({fp})"},
                    )
                )
        except Exception:
            pass
    return documents_charges


def charger_consignes_ipack():
    documents_charges = []
    for fp in ["ipack.txt"]:
        if os.path.exists(fp):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    documents_charges.append(
                        Document(
                            text=f.read(),
                            metadata={"source": f"Règles iPackEPS ({fp})"},
                        )
                    )
            except Exception:
                pass
    return documents_charges


def charger_dossier_txt_securise(chemin_dossier):
    docs_trouves = []
    if os.path.exists(chemin_dossier) and os.path.isdir(chemin_dossier):
        for nom_fichier in os.listdir(chemin_dossier):
            if nom_fichier.lower().endswith(".txt"):
                chemin_complet = os.path.join(chemin_dossier, nom_fichier)
                try:
                    with open(
                        chemin_complet, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        docs_trouves.append(
                            Document(
                                text=f.read(),
                                metadata={"source": nom_fichier},
                            )
                        )
                except Exception:
                    pass
    return docs_trouves


@st.cache_resource
def initialiser_base_santorin(cle_fremt):
    docs_santorin = [
        Document(
            text=(
                "Fiche Mémo - Correction Partagée Santorin (DEC)."
                " Spécifications techniques sur la correction multiple."
            ),
            metadata={
                "title": "Correction Partagée",
                "url": (
                    "https://assistance.ac-noumea.nc/IMG/pdf/fm_correction_partagee.pdf"
                ),
            },
        )
    ]
    docs_santorin.extend(charger_dossier_txt_securise("data/examens"))
    docs_santorin.extend(charger_consignes_examens())
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(
        similarity_top_k=8
    )


@st.cache_resource
def initialiser_base_ipack(cle_fremt):
    docs_ipack = [
        Document(
            text=(
                "Guide Pratique iPackEPS - Saisie des structures"
                " trimestrielles, imports SIÈCLE / Pronote et gestion des"
                " statuts."
            ),
            metadata={
                "title": "Guide iPackEPS",
                "url": (
                    "https://eps.ac-normandie.fr/IMG/pdf/guide_utilisateur_professeur-2.pdf"
                ),
            },
        )
    ]
    docs_ipack.extend(charger_dossier_txt_securise("data/ipack"))
    docs_ipack.extend(charger_consignes_ipack())
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(
        similarity_top_k=8
    )


@st.cache_resource
def initialiser_base_textes(cle_fremt):
    docs_textes = [
        Document(
            text=(
                "Base de données réglementaire globale pour les textes de lois"
                " du second degré et du premier degré."
            ),
            metadata={
                "title": "Légifrance",
                "url": "https://www.legifrance.gouv.fr/",
            },
        )
    ]
    docs_textes.extend(charger_dossier_txt_securise("data/textes"))
    if os.path.exists("data/textes/premier_degré"):
        docs_textes.extend(charger_dossier_txt_securise("data/textes/premier_degré"))
    docs_textes.extend(charger_consignes_ipack())
    return VectorStoreIndex.from_documents(docs_textes, recursive=True).as_retriever(
        similarity_top_k=8
    )


@st.cache_resource
def initialiser_base_peda(cle_fremt):
    docs_peda = [
        Document(
            text=(
                "Base pédagogique officielle - Programmes collège, AFL lycée et ressources Edubase."
            ),
            metadata={
                "title": "Base Pédagogique EPS",
                "url": "https://eduscol.education.fr",
            },
        )
    ]
    docs_peda.extend(charger_dossier_txt_securise("data/peda"))
    return VectorStoreIndex.from_documents(docs_peda).as_retriever(
        similarity_top_k=8
    )


timestamp_fichier = obtenir_cle_fichier()
retriever_santorin = initialiser_base_santorin(timestamp_fichier)
retriever_ipack = initialiser_base_ipack(timestamp_fichier)
retriever_textes = initialiser_base_textes(timestamp_fichier)
retriever_peda = initialiser_base_peda(timestamp_fichier)


# ======================================================================
# 🔔 VEILLES AUTOMATIQUES TAVILY (DEC & ÉDUSCOL)
# ======================================================================
def verifier_veille_dec(tavily_client):
    if not tavily_client:
        return

    fichier_suivi = "dernier_check_dec.txt"
    fichier_date_alerte = "date_alerte_dec.txt"
    fichier_url_alerte = "url_alerte_dec.txt"
    mois_actuel = datetime.datetime.now().strftime("%Y-%m")
    aujourdhui = datetime.date.today()

    url_defaut = "https://www.ac-aix-marseille.fr"

    if os.path.exists(fichier_date_alerte) and os.path.exists(fichier_url_alerte):
        try:
            with open(fichier_date_alerte, "r", encoding="utf-8") as f:
                date_alerte_str = f.read().strip()
                date_alerte = datetime.datetime.strptime(date_alerte_str, "%Y-%m-%d").date()
            with open(fichier_url_alerte, "r", encoding="utf-8") as f:
                url_sauvegardee = f.read().strip()

            st.session_state.date_veille_dec = date_alerte.strftime("%d/%m/%Y")
            st.session_state.alerte_veille_dec = (
                f"🔔 **Veille réglementaire DEC** : De nouvelles informations ou mises à jour ont été détectées. "
                f"[🔗 Accéder à la page académique]({url_sauvegardee})"
            )
        except Exception:
            pass

    a_deja_ete_fait = False
    if os.path.exists(fichier_suivi):
        try:
            with open(fichier_suivi, "r", encoding="utf-8") as f:
                if f.read().strip() == mois_actuel:
                    a_deja_ete_fait = True
        except Exception:
            pass

    if not a_deja_ete_fait:
        url_trouvee = url_defaut
        try:
            recherche_veille = tavily_client.search(
                query=(
                    "circulaire examen EPS DEC Aix-Marseille mise à jour"
                    f" {datetime.datetime.now().year}"
                ),
                max_results=2,
                include_domains=["ac-aix-marseille.fr", "education.gouv.fr"],
            )
            results = recherche_veille.get("results")
            if results:
                url_trouvee = results[0].get("url", url_defaut)
        except Exception:
            pass

        try:
            with open(fichier_suivi, "w", encoding="utf-8") as f:
                f.write(mois_actuel)
            with open(fichier_date_alerte, "w", encoding="utf-8") as f:
                f.write(aujourdhui.strftime("%Y-%m-%d"))
            with open(fichier_url_alerte, "w", encoding="utf-8") as f:
                f.write(url_trouvee)
        except Exception:
            pass

        st.session_state.date_veille_dec = aujourdhui.strftime("%d/%m/%Y")
        st.session_state.alerte_veille_dec = (
            f"🔔 **Veille réglementaire DEC** : De nouvelles informations ou mises à jour ont été détectées sur le portail académique. "
            f"[🔗 Accéder à la page académique]({url_trouvee})"
        )


def verifier_veille_eduscol(tavily_client):
    if not tavily_client:
        return

    fichier_suivi = "dernier_check_eduscol.txt"
    fichier_date_alerte = "date_alerte_eduscol.txt"
    fichier_url_alerte = "url_alerte_eduscol.txt"
    mois_actuel = datetime.datetime.now().strftime("%Y-%m")
    aujourdhui = datetime.date.today()

    url_defaut = "https://eduscol.education.fr"

    if os.path.exists(fichier_date_alerte) and os.path.exists(fichier_url_alerte):
        try:
            with open(fichier_date_alerte, "r", encoding="utf-8") as f:
                date_alerte_str = f.read().strip()
                date_alerte = datetime.datetime.strptime(date_alerte_str, "%Y-%m-%d").date()
            with open(fichier_url_alerte, "r", encoding="utf-8") as f:
                url_sauvegardee = f.read().strip()

            st.session_state.date_veille_eduscol = date_alerte.strftime("%d/%m/%Y")
            st.session_state.alerte_veille_eduscol = (
                f"🔔 **Veille Éduscol** : De nouveaux textes ou ressources officielles en EPS ont été détectés. "
                f"[🔗 Consulter la ressource]({url_sauvegardee})"
            )
        except Exception:
            pass

    a_deja_ete_fait = False
    if os.path.exists(fichier_suivi):
        try:
            with open(fichier_suivi, "r", encoding="utf-8") as f:
                if f.read().strip() == mois_actuel:
                    a_deja_ete_fait = True
        except Exception:
            pass

    if not a_deja_ete_fait:
        url_trouvee = url_defaut
        try:
            recherche_veille = tavily_client.search(
                query=(
                    "EPS éducation physique et sportive nouveau texte officiel Eduscol"
                    f" {datetime.datetime.now().year}"
                ),
                max_results=2,
                include_domains=["eduscol.education.fr", "education.gouv.fr"],
            )
            results = recherche_veille.get("results")
            if results:
                url_trouvee = results[0].get("url", url_defaut)
        except Exception:
            pass

        try:
            with open(fichier_suivi, "w", encoding="utf-8") as f:
                f.write(mois_actuel)
            with open(fichier_date_alerte, "w", encoding="utf-8") as f:
                f.write(aujourdhui.strftime("%Y-%m-%d"))
            with open(fichier_url_alerte, "w", encoding="utf-8") as f:
                f.write(url_trouvee)
        except Exception:
            pass

        st.session_state.date_veille_eduscol = aujourdhui.strftime("%d/%m/%Y")
        st.session_state.alerte_veille_eduscol = (
            f"🔔 **Veille Éduscol** : De nouveaux textes ou ressources officielles ont été détectés. "
            f"[🔗 Consulter la ressource]({url_trouvee})"
        )

verifier_veille_dec(tavily_client)
verifier_veille_eduscol(tavily_client)

# ======================================================================
# 🔑 ZONE SECRÈTE ADMIN (SIDEBAR DISCRÈTE POUR VOIR LES VEILLES)
# ======================================================================
with st.sidebar:
    st.markdown("### ⚙️ Espace Administration")
    mot_de_passe_entre = st.text_input("Mot de passe admin", type="password")
    if mot_de_passe_entre == admin_secret_key:
        st.session_state.is_admin = True
        st.success("Mode Admin activé (Veilles visibles)")
    elif mot_de_passe_entre:
        st.error("Mot de passe incorrect")

# ======================================================================
# 5. BANDEAU SUPÉRIEUR
# ======================================================================
st.markdown(
    f"""
    <div class="hub-header">
        <div style="display: flex; align-items: center; width: 20%;">
            <img src="data:image/png;base64,{img_gauche}" height="60">
        </div>
        <div class="hub-title">
            <div class="title-row">
                <h1>HUB IA - EPS</h1>
                <span class="badge-visiteur">👁️ {nb_visites_reel}</span>
            </div>
            <p>ESPACE RESSOURCES &amp; ASSISTANCE NUMÉRIQUE</p>
        </div>
        <div style="display: flex; justify-content: flex-end; align-items: center; width: 25%; gap: 15px;">
            <img src="data:image/png;base64,{img_eps}" height="55">
            <img src="data:image/png;base64,{img_droite}" class="img-zoomable" height="55">
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

if st.session_state.get("is_admin", False):
    if "alerte_veille_dec" in st.session_state:
        date_alerte = st.session_state.get("date_veille_dec", "Récemment")
        texte_alerte_dec = st.session_state.get("alerte_veille_dec", "")
        
        lien_html_dec = ""
        match_dec = re.search(r'\[([^\]]+)\]\((https?://[^\)]+)\)', texte_alerte_dec)
        if match_dec:
            libelle_lien, url_lien = match_dec.groups()
            lien_html_dec = f'<br><a href="{url_lien}" target="_blank" style="color: #FFB020 !important; font-weight: bold; text-decoration: underline; display: inline-block; margin-top: 6px;">{libelle_lien}</a>'

        st.markdown(
            f"""
        <div style="background-color: rgba(15, 23, 42, 0.85) !important; backdrop-filter: blur(12px); border-left: 6px solid #FFB020; padding: 14px 18px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 22px; margin-top: 2px;">🚨</span>
                <div style="width: 100%;">
                    <strong style="color: #FFB020 !important; font-size: 14px; text-transform: uppercase;">Veille réglementaire DEC (Admin) — Détectée le {date_alerte}</strong>
                    <div style="color: #F1F5F9 !important; font-size: 13.5px; margin-top: 6px;">
                        De nouvelles informations ou mises à jour ont été détectées sur les portails officiels.
                        {lien_html_dec}
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if "alerte_veille_eduscol" in st.session_state:
        date_alerte_edu = st.session_state.get("date_veille_eduscol", "Récemment")
        texte_alerte_edu = st.session_state.get("alerte_veille_eduscol", "")

        lien_html_edu = ""
        match_edu = re.search(r'\[([^\]]+)\]\((https?://[^\)]+)\)', texte_alerte_edu)
        if match_edu:
            libelle_lien_edu, url_lien_edu = match_edu.groups()
            lien_html_edu = f'<br><a href="{url_lien_edu}" target="_blank" style="color: #38BDF8 !important; font-weight: bold; text-decoration: underline; display: inline-block; margin-top: 6px;">{libelle_lien_edu}</a>'

        st.markdown(
            f"""
        <div style="background-color: rgba(15, 23, 42, 0.85) !important; backdrop-filter: blur(12px); border-left: 6px solid #38BDF8; padding: 14px 18px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <span style="font-size: 22px; margin-top: 2px;">📘</span>
                <div style="width: 100%;">
                    <strong style="color: #38BDF8 !important; font-size: 14px; text-transform: uppercase;">Veille Éduscol (Admin) — Détectée le {date_alerte_edu}</strong>
                    <div style="color: #F1F5F9 !important; font-size: 13.5px; margin-top: 6px;">
                        De nouveaux textes ou ressources officielles ont été mis en ligne.
                        {lien_html_edu}
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

# ======================================================================
# 6. ÉTAPE 1 : CHOIX DU CONTEXTE (3 ONGLETS)
# ======================================================================
label_titres = {
    "ipack": (
        "🛠️ Mode Actif : Assistance Technique iPackEPS (Gestion du CCF &"
        " Inaptitudes)"
    ),
    "examens": (
        "📊 Mode Actif : Réglementation Examens & Santorin (Copies Numérisées &"
        " Jurys)"
    ),
    "textes": (
        "🔒 Mode Actif : SÉCURITÉ & Responsabilité Juridique (Textes Officiels &"
        " Risques APPN)"
    ),
}

titre_affiche = label_titres.get(
    st.session_state.active_module,
    "⚠️ EN ATTENTE DE SÉLECTION DU CONTEXTE CI-DESSOUS ⬇️"
)
st.markdown(
    '<div class="column-title-top"><span class="instruction">⚙️ ÉTAPE 1 : CHOISISSEZ LE CONTEXTE DE VOTRE QUESTION</span><span'
    f' class="mode-actuel">{titre_affiche}</span></div>',
    unsafe_allow_html=True,
)

col_b1, col_b2, col_b3 = st.columns(3, gap="small")
with col_b1:
    if st.button(
        "🛠️ iPackEPS",
        use_container_width=True,
        key="btn_ip",
        type=(
            "primary"
            if st.session_state.active_module == "ipack"
            else "secondary"
        ),
    ):
        st.session_state.active_module = "ipack"
        st.session_state.contexte_valide = True
        st.session_state.public_valide = False
        st.session_state.messages_hub = []
        st.rerun()
with col_b2:
    if st.button(
        "📊 Examens &\nSantorin",
        use_container_width=True,
        key="btn_ex",
        type=(
            "primary"
            if st.session_state.active_module == "examens"
            else "secondary"
        ),
    ):
        st.session_state.active_module = "examens"
        st.session_state.contexte_valide = True
        st.session_state.public_valide = False
        st.session_state.messages_hub = []
        st.rerun()
with col_b3:
    if st.button(
        "🔒 Sécurité &\nCadres Règl.",
        use_container_width=True,
        key="btn_se",
        type=(
            "primary"
            if st.session_state.active_module == "textes"
            else "secondary"
        ),
    ):
        st.session_state.active_module = "textes"
        st.session_state.contexte_valide = True
        st.session_state.public_valide = False
        st.session_state.messages_hub = []
        st.rerun()

# ======================================================================
# 🎯 BANNIÈRE DYNAMIQUE (REMPLACE "OÙ POSER" SI MODE TEXTES ACTIF)
# ======================================================================
if st.session_state.active_module == "textes":
    st.markdown(
        """
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-top: 10px; margin-bottom: 12px;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            ⚠️ <strong>Avertissement –</strong> En cas de doute juridique ou de sinistre, contactez impérativement : <strong>Votre Chef d'établissement, votre Secrétariat d'examen, ou votre IA-IPR.</strong>
        </span>
    </div>
    """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-top: 10px; margin-bottom: 12px;">
        <div style="color: #38BDF8; font-weight: 800; font-size: 14px; text-align: center; margin-bottom: 12px;">🎯 OÙ POSER VOTRE QUESTION ?</div>
        <div style="display: flex; gap: 20px; color: #FCD34D; font-size: 13px;">
            <div style="flex: 1; border-right: 1px solid #334155; padding-right: 20px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">🛠️ Menu iPackEPS (Toute l'année)</strong><br>
                <span>Configuration modules, classes, élèves, groupes, inaptitudes, dispenses...</span>
            </div>
            <div style="flex: 1; padding-left: 5px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">📊 Menu Examens &amp; Santorin</strong><br>
                <span>Remontée officielle Bac/DNB, correction numérique, arbitrages CAHPN, blocs de lots.</span>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ======================================================================
# 7. ÉTAPE 2 & 3 : PUBLIC CIBLE ET ZONE DE SAISIE (PARCOURS EN CASCADE)
# ======================================================================
prompt = None

if not st.session_state.contexte_valide:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1E293B, #0F172A); border: 2px dashed #38BDF8; padding: 20px; border-radius: 8px; text-align: center; margin-top: 15px; margin-bottom: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);">
            <span style="color: #38BDF8; font-weight: 800; font-size: 15px; display: block; margin-bottom: 6px;">
                🔒 SI VOUS AVEZ UNE AUTRE QUESTION
            </span>
            <span style="color: #F1F5F9; font-size: 13.5px;">
                Veuillez sélectionner le <strong>contexte (Étape 1)</strong> puis le public cible pour poser une nouvelle question.
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # 🎯 ÉTAPE 2 : SÉLECTION DU PUBLIC CIBLE (DÉVERROUILLÉE)
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #F59E0B, #D97706); padding: 14px 18px; border-radius: 8px; border: 2px solid #FCD34D; margin-top: 15px; margin-bottom: 10px; box-shadow: 0px 4px 15px rgba(245, 158, 11, 0.4);">
            <span style="color: #0F172A; font-weight: 900; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">🎯 ÉTAPE 2 : SÉLECTIONNEZ VOTRE PUBLIC CIBLE (Pour ajuster la réponse)</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    def valider_public():
        st.session_state.public_valide = True

    niveau_scolaire = st.radio(
        "Public cible",
        ["1er degré", "Collège (DNB)", "Lycée Général & Techno", "Lycée Pro / CAP"],
        horizontal=True,
        key="niveau_actif_form",
        label_visibility="collapsed",
        on_change=valider_public
    )

    if st.session_state.get("niveau_actif_form"):
        st.session_state.public_valide = True

    if not st.session_state.public_valide:
        st.markdown(
            """
            <div style="background-color: rgba(30, 41, 59, 0.8); border: 1px dashed #F59E0B; padding: 12px; border-radius: 8px; text-align: center; margin-top: 10px; margin-bottom: 12px;">
                <span style="color: #FCD34D; font-weight: bold; font-size: 13.5px;">
                    👆 Veuillez cocher votre <strong>Public Cible (Étape 2)</strong> ci-dessus pour déverrouiller la zone de question.
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # 🚀 ÉTAPE 3 : ZONE DE SAISIE DE LA QUESTION
        st.markdown(
            """
            <div class="column-title-top" style="margin-top: 15px;">
                <span class="instruction">🚀 ÉTAPE 3</span>
                <span class="mode-actuel">POSEZ VOTRE QUESTION</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form(key="form_question_hub", clear_on_submit=True):
            col_input, col_submit = st.columns([5, 1])
            with col_input:
                prompt_brut = st.text_input(
                    "Question :",
                    placeholder=(
                        "🔺 Saisissez votre question ici en tenant compte du niveau sélectionné..."
                    ),
                    label_visibility="collapsed",
                )
            with col_submit:
                bouton_envoyer = st.form_submit_button(
                    "🚀 Poser la question", use_container_width=True, type="primary"
                )

            if bouton_envoyer and prompt_brut.strip():
                prompt = prompt_brut.strip()

# ======================================================================
# 9. TRAITEMENT RAG & FLUX DE MESSAGES
# ======================================================================
if prompt:
    st.session_state.messages_hub = []

    st.session_state.messages_hub.append({
        "role": "user",
        "type": "text",
        "content": f"<span style='color: white;'>{prompt}</span>",
    })
    with st.spinner("Je consulte la documentation officielle..."):
        mode = st.session_state.active_module
        p_low = prompt.lower()
        
        niveau_actuel_form = st.session_state.get("niveau_actif_form", "Collège (DNB)")

        onglets_noms = {
            "ipack": "l'onglet Assistance Technique iPackEPS (Gestion du CCF)",
            "examens": "l'onglet Réglementation Examens & Santorin (Copies Numérisées)",
            "textes": "l'onglet Sécurité & Responsabilité Juridique (Textes Officiels)",
        }
        contexte_choisi_nom = onglets_noms.get(mode, "un onglet de l'application")

        # ==================================================================
        # 🛡️ DISJONCTEUR DE SÉCURITÉ : DÉTECTION DES SUJETS HORS-SUJET
        # (DÉSACTIVÉ POUR iPACKEPS ET EXAMENS POUR ÉVITER TOUT BLOCAGE)
        # ==================================================================
        if mode in ["ipack", "examens"]:
            est_totalement_hors_sujet = False
        else:
            mots_cles_eps_admin = [
                "ipack", "iPackEPS", "santorin", "cyclades", "arena", "pronote", 
                "ecoledirecte", "lsu", "imag'in", "imagin", "esterel", "siècle", "siecle",
                "dnb", "brevet", "bac", "cap", "ccf", "cahpn", "cahn", 
                "protocole", "protocoles", "lot", "lots", "saisie", "saisir", 
                "verrouillage", "verrouiller", "déverrouillage", "deverrouiller", 
                "évaluation", "evaluation", "note", "notes", "dispense", "dispensé",
                "inaptitude", "inapte", "candidat", "candidats", "jury", "jurys",
                "collège", "college", "lycée", "lycee", "maternelle", 
                "élémentaire", "elementaire", "segpa", "ulis", "terminale", 
                "tps", "ps", "ms", "gs", "cp", "ce1", "ce2", "cm1", "cm2", 
                "sss", "section sportive", "prépa-métiers", "prepa-metiers",
                "eps", "sport", "sports", "apsa", "relais", "handball", 
                "activite", "activites", "sauts", "lancers", "courses", 
                "appn", "tasa", "sauvetage", "pédagogie", "pedagogie", 
                "programme", "programmes", "afl", "afc", "socle",
                "sécurité", "securite", "matériel", "materiel", "epi", "fauchon", 
                "responsabilité", "responsabilite", "circulaire", "officiel", 
                "textes", "loi", "décret", "arrete", "arrêté", "recteur", "rectrice", 
                "ia-ipr", "ipr", "sanction", "exclusion", "accident", "unss", 
                "compétence", "competence", "fonction publique", "direction", "chef d'établissement",
                "psc1", "psc", "secourisme", "secours", "cdsg", "jdc", "cadets"
            ]
            est_totalement_hors_sujet = not any(mot in p_low for mot in mots_cles_eps_admin)

        if est_totalement_hors_sujet:
            rappel_hs = (
                "<div style='margin-bottom: 14px; padding: 10px; background-color: rgba(250, 204, 21, 0.1); color: #FDE047; border-radius: 6px; font-size: 12.5px; border: 1px solid rgba(250, 204, 21, 0.3);'>"
                "⚠️ <strong>Rappel :</strong> Cette assistance numérique est fournie à titre indicatif. La réponse ci-dessous devra être vérifiée et croisée avec les textes officiels en vigueur ou validée par votre hiérarchie (Chef d'établissement / IA-IPR / DEC)."
                "</div>"
            )
            texte_brut = rappel_hs + """<h3>🛑 HORS PÉRIMÈTRE INSTITUTIONNEL</h3>
<ul>
  <li><strong>Champ de compétence :</strong> Votre question semble étrangère aux domaines traités par cet assistant (Éducation Physique et Sportive, gestion administrative iPackEPS, examens et concours, ou réglementation juridique et institutionnelle).</li>
  <li><strong>Restriction d'usage :</strong> En tant qu'assistant numérique spécialisé, je ne suis pas programmé pour traiter des requêtes extérieures à ces périmètres professionnels.</li>
  <li><strong>Recommandation :</strong> Pour toute autre thématique, veuillez utiliser un outil généraliste ou vous référer directement aux services compétents de votre hiérarchie.</li>
</ul>"""
            badge, color_card = "⚖️ HORS-SUJET", "securite-card"
        else:
            texte_brut = ""
            extraits_doc = ""
            badge, color_card = "INFORMATION", "general-card"

            verites_terrain_pierre = ""
            try:
                for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
                    if os.path.exists(fp):
                        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                            verites_terrain_pierre += f"\n--- REGLES DE PIERRE ---\n" + f.read() + "\n"
            except Exception:
                pass

            est_college = any(w in p_low for w in ["6e", "5e", "4e", "3e", "collège", "college", "dnb", "brevet", "lsu"])
            est_clairement_lycee = any(w in p_low for w in ["santorin", "ccf", "terminale", "cyclades", "epxcs", "bac", "cap"])
            
            est_premier_degre = any(w in p_low for w in [
                "tps", "ps", "ms", "gs", "cp", "ce1", "ce2", "cm1", "cm2", 
                "maternelle", "élémentaire", "elementaire", "atsem", "directeur d'école", "ien"
            ])

            if est_college and not est_clairement_lycee:
                contexte_actif = "college"
            else:
                contexte_actif = mode

            est_import_pronote = (
                mode == "ipack"
                and "pronote" in p_low
                and any(w in p_low for w in ["import", "élève", "eleve", "classe", "classes"])
            )

            est_saisir_notes = (
                not est_import_pronote
                and any(w in p_low for w in ["saisir", "saisie", "noter", "note", "notes", "carnet"]) 
                and any(w in p_low for w in ["note", "notes"])
                and not any(w in p_low for w in ["santorin", "cyclades"])
                and mode != "examens" 
            )

            est_connexion = (
                any(w in p_low for w in ["connecter", "connexion", "accéder", "acceder"]) 
                and any(w in p_low for w in ["cyclades", "santorin", "imag'in", "imagin", "arena", "plateforme"])
            )

            est_date = (
                (not est_college) 
                and any(
                    phrase in p_low for phrase in [
                        "quel est le calendrier", "quelles sont les dates", "date butoir de", 
                        "date de fermeture", "calendrier officiel"
                    ]
                ) 
                and any(
                    w in p_low for w in [
                        "saisie", "note", "notes", "fermeture", "santorin", "cyclades", 
                        "lot", "lots", "examen", "examens", "bac", "cap", "brevet"
                    ]
                )
            )

            est_dnb = (mode != "textes") and any(w in p_low for w in ["dnb", "brevet", "collège", "college"]) and not any(w in p_low for w in ["bac", "lycée", "lycee", "cap"])
            est_sujet_secours = "sujet" in p_low and any(w in p_low for w in ["secours", "papier", "imprimer"])
            est_cap_3epreuves = (
                mode == "examens"
                and "cap" in p_low
                and any(w in p_low for w in ["3 épreuves", "3 notes", "trois épreuves", "trois notes"])
            )
            est_tasa = mode == "textes" and "tasa" in p_low

            est_unss = any(w in p_low for w in [
                "unss", "championnat de france", "championnats de france", 
                "jeune juge", "jeunes juges", "jeune arbitre", "jeunes arbitres", "podium unss"
            ])

            est_deplacer_candidat = (
                mode != "textes"
                and any(w in p_low for w in ["déplacer", "deplacer", "déplacement", "deplacement"])
                and any(w in p_low for w in ["candidat", "élève", "eleve"])
                and "lot" in p_low
            )

            est_eleve_arrivant = (
                mode != "textes"
                and any(w in p_low for w in ["arrive", "arrivant", "arrivée", "en cours d'année", "cours d annee", "nouvel", "nouvelle"])
                and any(w in p_low for w in ["élève", "eleve", "ccf", "examen", "groupe"])
            )

            est_apsa_etablissement_vs_nationale = (
                any(w in p_low for w in ["apsa établissement", "apsa etablissement", "liste nationale"])
                and any(w in p_low for w in ["valide", "invalide", "relais", "sauts", "lancers", "statistiques", "cyclades"])
            )

            est_verrouiller_lot = (
                mode == "examens"
                and any(w in p_low for w in ["comment verrouiller", "je veux verrouiller", "pour verrouiller", "verrouiller mon lot", "verrouiller mes lots"])
                and not any(w in p_low for w in ["déverrouiller", "deverrouiller", "incohérences", "incoherence", "erreur", "impossible", "candidature"])
            )

            est_deverrouiller_lot = (
                mode == "examens"
                and (
                    any(w in p_low for w in ["déverrouiller", "deverrouiller", "cadenas", "fermé", "ferme", "modifier note"])
                    or "verrouillé" in p_low
                )
                and any(w in p_low for w in ["santorin", "lot", "copie"])
                and not est_verrouiller_lot
            )

            est_dispense_totale = (
                mode != "textes"
                and any(w in p_low for w in ["dispensé", "dispense", "inapte", "inaptitude"])
                and any(w in p_low for w in ["total", "année", "annee", "toutes les épreuves", "toutes les epreuves"])
            )

            est_exclusion = (
                mode != "textes"
                and any(w in p_low for w in ["exclusion", "conseil de discipline", "exclu", "sanction"])
                and any(w in p_low for w in ["ccf", "épreuve", "epreuve", "note", "rattrapage"])
            )

            est_aucun_eleve = (
                mode == "ipack"
                and any(w in p_low for w in ["aucun élève", "aucun eleve", "pas d'élève", "pas d'eleve", "siècle", "siecle", "arena"])
            )

            est_referentiels_rentree = (
                mode == "ipack"
                and any(
                    phrase in p_low for phrase in [
                        "configurer les référentiels de rentrée",
                        "déclarer les apsa de rentrée",
                        "dépôt initial des référentiels",
                        "campagne de rentrée"
                    ]
                )
            )

            est_sss = any(w in p_low for w in ["sss", "section sportive", "reconduction", "fermeture sss"])
            
            est_sss_bloque = (
                mode == "ipack"
                and any(w in p_low for w in ["sss", "section sportive"])
                and any(w in p_low for w in ["droit", "créer", "creer", "autorise", "autorise", "bloque", "pas"])
            )

            est_cas_direct = (
                (mode != "textes") 
                and (
                    est_connexion
                    or est_date 
                    or est_sujet_secours 
                    or est_cap_3epreuves 
                    or est_deplacer_candidat
                    or est_eleve_arrivant
                    or est_apsa_etablissement_vs_nationale
                    or est_verrouiller_lot
                    or est_deverrouiller_lot
                    or est_dispense_totale
                    or est_saisir_notes
                    or est_exclusion
                    or est_aucun_eleve
                    or est_referentiels_rentree
                    or est_import_pronote
                    or est_sss_bloque
                )
            ) or est_tasa or est_unss

            if openai_api_key and not est_cas_direct:
                try:
                    if niveau_actuel_form == "1er degré":
                        if retriever_textes:
                            nodes_bruts = retriever_textes.retrieve(prompt)
                            for n in nodes_bruts:
                                extraits_doc += f"[Référentiel Textes Officiels 1er Degré] {n.node.text}\n\n"
                        if retriever_peda:
                            nodes_peda = retriever_peda.retrieve(prompt)
                            for n in nodes_peda:
                                extraits_doc += f"[Référentiel Pédagogique 1er Degré] {n.node.text}\n\n"
                    else:
                        if mode == "textes":
                            if retriever_textes:
                                nodes_bruts = retriever_textes.retrieve(prompt)
                                for n in nodes_bruts:
                                    extraits_doc += f"[Textes Officiels & Juridiques / Partenariats] {n.node.text}\n\n"
                            if retriever_peda and any(w in p_low for w in ["programme", "cycle", "competence", "afl", "afc", "socle", "pedagogie"]):
                                nodes_peda = retriever_peda.retrieve(prompt)
                                for n in nodes_peda:
                                    extraits_doc += f"[Référentiel Pédagogique] {n.node.text}\n\n"
                        elif mode == "examens":
                            if retriever_santorin:
                                nodes_bruts = retriever_santorin.retrieve(prompt)
                                for n in nodes_bruts:
                                    extraits_doc += f"{n.node.text}\n\n"
                        elif mode == "ipack":
                            if retriever_ipack:
                                nodes_bruts = retriever_ipack.retrieve(prompt)
                                for n in nodes_bruts:
                                    extraits_doc += f"{n.node.text}\n\n"
                        else:
                            if retriever_peda:
                                nodes_peda = retriever_peda.retrieve(prompt)
                                for n in nodes_peda:
                                    extraits_doc += f"[Référentiel Pédagogique & Programmes] {n.node.text}\n\n"
                except Exception:
                    pass

            if est_import_pronote:
                texte_brut = """<h3>📥 IMPORTATION DES LISTES D'ÉLÈVES DEPUIS PRONOTE</h3>
<ul>
  <li><strong>Principe :</strong> L'importation des données d'élèves depuis Pronote permet d'initialiser vos classes rapidement en début d'année dans iPackEPS.</li>
  <li><strong>Manipulation :</strong> Rendez-vous dans les paramètres d'importation de votre établissement pour charger le fichier exporté.</li>
</ul>
📺 Tutoriel associé : import_eleves_pronote.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_connexion:
                texte_brut = """<h3>🌐 ACCÈS AUX PLATEFORMES PROFESSIONNELLES (CYCLADES, SANTORIN, IMAG'IN)</h3>
<ul>
  <li><strong>Règle d'or absolue :</strong> Aucun enseignant ou personnel ne se connecte par un site web académique public (type site grand public de l'académie).</li>
  <li><strong>Portail d'accès unique :</strong> L'accès à TOUTES les applications professionnelles et d'examen se fait IMPÉRATIVEMENT et exclusivement par le portail professionnel institutionnel <strong>ARENA</strong> (ou l'intranet académique de type Esterel) à l'aide de vos identifiants professionnels (e-mail académique + mot de passe).</li>
</ul>"""
                badge, color_card = "🌐 ACCÈS INSTITUTIONNEL", ("santorin-card" if mode == "examens" else "general-card")

            elif est_saisir_notes:
                texte_brut = """<h3>⚠️ RÈGLE FONDAMENTALE : iPACKEPS N'EST PAS UN CARNET DE NOTES</h3>
<ul>
  <li><strong>Règle absolue :</strong> iPackEPS n'est en aucun cas un carnet de notes ou un logiciel de notation. Il est <strong>strictement impossible</strong> d'y saisir des notes.</li>
  <li><strong>Outil dédié :</strong> Utilisez exclusivement Pronote, ÉcoleDirecte ou le LSU selon votre niveau.</li>
</ul>"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_date:
                texte_brut = """<h3>📅 CALENDRIER OFFICIEL DES EXAMENS & SAISIE DES NOTES</h3>
<ul>
  <li><strong>Principe réglementaire :</strong> Les dates butoirs de saisie des notes et de clôture des serveurs (Santorin / Cyclades) sont fixées annuellement par le calendrier officiel publié au Bulletin Officiel (BO) et précisées par la circulaire DEC de votre académie.</li>
</ul>"""
                badge, color_card = "📅 CALENDRIER OFFICIEL", ("santorin-card" if mode == "examens" else "general-card")

            elif est_tasa:
                texte_brut = """<h3>🏊 CADRE RÉGLEMENTAIRE - TEST D'APTITUDE AU SAUVETAGE AQUATIQUE (TASA)</h3>
<ul>
  <li><strong>Obligation de qualification :</strong> Obligatoire pour tout enseignant d'EPS dès sa nomination.</li>
  <li><strong>Protocole technique :</strong> 100m en continu < 3 min 45 s avec parcours spécifique et recherche de mannequin.</li>
</ul>"""
                badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

            elif est_sujet_secours:
                texte_brut = """<h3>⚠️ AUCUN SUJET ÉCRIT DE SECOURS EN EPS</h3>
<ul>
  <li><strong>Règle nationale absolue :</strong> En EPS, il n'existe <strong>aucun sujet écrit ou papier</strong>. L'évaluation est 100 % pratique.</li>
  <li><strong>Élève absent :</strong> Organisation obligatoire d'une épreuve de substitution (rattrapage de l'épreuve motrice) avant fermeture des serveurs.</li>
</ul>"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_cap_3epreuves:
                texte_brut = """<h3>⚠️ ALERTE : PROTOCOLE CAP STRICT À 2 ÉPREUVES</h3>
<ul>
  <li><strong>Réglementation stricte :</strong> En CAP, le CCF repose <strong>STRICTEMENT sur 2 épreuves</strong> issus de 2 champs d'apprentissage distincts.</li>
  <li><strong>Bloqueur Santorin :</strong> Toute saisie d'une 3ᵉ note est bloquée automatiquement par l'interface. Nettoyez le protocole dans iPackEPS.</li>
</ul>"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_eleve_arrivant:
                texte_brut = """<h3>📋 GESTION D'UN ÉLÈVE ARRIVANT EN COURS D'ANNÉE</h3>
<ul>
  <li><strong>Règle d'or pour l'enseignant :</strong> Aucune manipulation informatique, aucun "bricolage" local ni import de fichier n'est à faire de votre côté dans iPackEPS pour les examens nationaux. iPackEPS ne gère pas les listes d'examens nationaux sur Santorin.</li>
  <li><strong>Action obligatoire (Secrétariat / Direction) :</strong> 
    <ol>
      <li>Le secrétariat de l'établissement doit associer l'élève au protocole d'examen dans <strong>Cyclades</strong> (via l'interface administrative).</li>
      <li>Le chef d'établissement se connecte à la console <strong>Santorin-Direction</strong> pour effectuer une distribution manuelle (glisser-déposer) du candidat vers votre lot de correction.</li>
    </ol>
  </li>
  <li><strong>Délai de synchronisation :</strong> La prise en compte est effective sous 12h à 24h après l'action administrative en amont.</li>
</ul>
📺 Tutoriel associé : Distribution_manuelle_lots_santorin.mp4"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_apsa_etablissement_vs_nationale:
                texte_brut = """<h3>⚠️ ERREUR DE SAISIE : APSA ÉTABLISSEMENT VS LISTE NATIONALE (BAC GT)</h3>
<ul>
  <li><strong>Le problème :</strong> Déclarer une activité en "APSA établissement" au lieu de l'activité de la "liste nationale" (ex: Courses, Sauts, Lancers) bloque la validation du protocole par iPackEPS (exigence d'a minima 2 ou 3 activités de la liste nationale selon la voie) et fausse les statistiques académiques sur Cyclades.</li>
  <li><strong>Procédure de résolution exacte :</strong>
    <ol>
      <li>Retournez dans le module <strong>[Dossiers] > [Dossier EPS] > [APSA]</strong>.</li>
      <li>Sélectionnez dans le tableau de gauche l'activité de la liste nationale correspondante (ex: <em>[Courses]</em>).</li>
      <li>Déclarez-la certificative en Lycée pour remplacer l'APSA établissement erronée.</li>
    </ol>
  </li>
</ul>"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_verrouiller_lot:
                texte_brut = """<h3>🔒 VERROUILLAGE D'UN LOT DE CORRECTION SUR SANTORIN</h3>
<ul>
  <li><strong>Principe :</strong> Une fois la saisie de toutes les notes et des statuts terminée et vérifiée, vous devez procéder au verrouillage de votre lot pour figer les données avant transmission définitive.</li>
  <li><strong>Manipulation :</strong> Depuis votre espace de correction sur Santorin, accédez au lot concerné et validez l'action de clôture/verrouillage.</li>
</ul>
📺 Tutoriel associé : Verrouiller_lot_santorin.mp4"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_deverrouiller_lot:
                texte_brut = """<h3>🔒 CADENAS ET DÉVERROUILLAGE DE LOT SUR SANTORIN</h3>
<ul>
  <li><strong>Règle d'or absolue :</strong> L'enseignant correcteur n'a AUCUN droit ni habilitation pour déverrouiller lui-même un lot de copies numériques fermé sur Santorin.</li>
  <li><strong>Action obligatoire (Direction) :</strong> La manipulation relève exclusivement du Chef d'établissement depuis sa console <strong>Santorin-Direction</strong> (Menu "Liste des lots" -> clic direct sur le cadenas pour basculer de fermé à ouvert).</li>
  <li><strong>Interdiction formelle :</strong> Ne contactez surtout pas la DEC (Division des Examens et Concours) pour cela, c'est une action locale et autonome de l'établissement.</li>
</ul>
📺 Tutoriel associé : Deverrouiller_lots_santorin.mp4"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_dispense_totale:
                texte_brut = """<h3>🏥 GESTION D'UNE INAPTITUDE / DISPENSE TOTALE DE CERTIFICATION</h3>
<ul>
  <li><strong>Cadre réglementaire :</strong> Une inaptitude médicale couvrant <strong>l'intégralité du cycle de certification</strong> (dispense totale) ne relève pas d'une absence ponctuelle ni d'une épreuve différée.</li>
  <li><strong>Saisie administrative :</strong> Le dossier doit faire l'objet du statut réglementaire de dispense globale (ex: <code>DISP</code> sur les blocs concernés) conformément aux directives de la note de service des examens.</li>
  <li><strong>Attention au zéro :</strong> Ne jamais assimiler une dispense totale et officielle à une absence injustifiée (pas de zéro éliminatoire). Le dossier sera examiné par la CAHPN.</li>
</ul>"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_exclusion:
                texte_brut = """<h3>⚠️ EXCLUSION TEMPORAIRE EN PÉRIODE DE CCF (ABSENCE CONTRAINTE)</h3>
<ul>
  <li><strong>Cadre juridique :</strong> Une exclusion temporaire prononcée par un conseil de discipline n'est en aucun cas une inaptitude médicale. Elle ne doit jamais être assimilée à un statut <strong>[DISP]</strong> ni sanctionnée par un zéro éliminatoire pour absence injustifiée.</li>
  <li><strong>Nature de l'absence :</strong> Il s'agit d'une absence administrative et disciplinaire contrainte par l'institution.</li>
  <li><strong>Obligation de rattrapage :</strong> L'équipe pédagogique a l'obligation légale de programmer une <strong>épreuve différée</strong> dès le retour de l'élève, impérativement avant la date de clôture des serveurs académiques (Santorin / Cyclades).</li>
</ul>"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_aucun_eleve:
                texte_brut = """<h3>⚠️ PROBLÈMES D'IMPORT SIÈCLE / ARENA À LA RENTRÉE</h3>
<ul>
  <li><strong>Origine du blocage :</strong> Le message "Aucun élève dans cet établissement" au mois de septembre provient généralement d'un décalage de synchronisation entre la base administrative de l'établissement (SIÈCLE) et le portail académique ARENA.</li>
  <li><strong>Vérification amont :</strong> Assurez-vous auprès du secrétariat de direction que la bascule administrative de rentrée a bien été effectuée et validée au niveau académique.</li>
  <li><strong>Action iPackEPS :</strong> Rendez-vous dans <strong>[Dossiers] > [Dossier EPS] > [Élèves]</strong> et lancez une actualisation manuelle de l'importation.</li>
</ul>
📺 Tutoriel associé : Import_automatique_eleves.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_referentiels_rentree:
                texte_brut = """<h3>📋 CONFIGURATION DES RÉFÉRENTIELS ET APSA CERTIFICATIVES (RENTRÉE)</h3>
<ul>
  <li><strong>Impératif de septembre :</strong> Dès les premiers jours de la rentrée, vous devez déclarer et configurer les APSA certificatives de vos classes de lycée (CAP, Bac Pro, Bac GT) dans iPackEPS.</li>
  <li><strong>Procédure iPackEPS :</strong> Accédez au menu <strong>[Dossiers] > [Dossier EPS] > [APSA]</strong>, cochez les champs d'apprentissage et les épreuves retenues pour vos cycles de certification annuels.</li>
  <li><strong>Sécurisation :</strong> Cette étape en amont est indispensable pour valider la structure des groupes avant le dépôt officiel des référentiels auprès des services académiques à l'automne.</li>
</ul>
📺 Tutoriel associé : Depot_referentiels_iPackEPS.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_deplacer_candidat:
                texte_brut = """<h3>📋 DÉPLACEMENT D'UN CANDIDAT OU RÉAFFECTATION DE LOT SUR SANTORIN</h3>
<ul>
  <li><strong>Règle absolue :</strong> L'enseignant n'a aucun droit ni possibilité de déplacer lui-même un candidat d'un lot à un autre sur Santorin.</li>
  <li>Corriger l'affectation dans <strong>Cyclades</strong> puis relancer une distribution automatique, ou utiliser l'option d'affectation directe depuis le lot si l'habilitation le permet.</li>
</ul>
📺 Tutoriel associé : Distribution_manuelle_lots_santorin.mp4
📺 Tutoriel associé : Ajouter_evaluateur_lot_santorin.mp4"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_sss_bloque:
                texte_brut = """<h3>⚠️ BLOCAGE CRÉATION GROUPE SSS</h3>
<ul>
  <li><strong>Règle institutionnelle :</strong> La création d’un groupe de type SSS (Section Sportive Scolaire) nécessite obligatoirement que le recteur ait validé la demande d’ouverture de votre section. Par défaut, iPackEPS n’autorise pas la création de ce type de groupe.</li>
  <li><strong>Mise à jour académique :</strong> Chaque année, le responsable iPackEPS de l'académie met à jour la liste des nouvelles SSS autorisées.</li>
  <li><strong>Action requise :</strong> Si votre dossier a bien été validé par le recteur mais que l'application bloque toujours, <strong>faites un simple signalement par e-mail à votre responsable iPackEPS ou à votre IPR</strong> pour que votre établissement soit activé dans le système. Aucune action locale dans les menus ne pourra contourner ce verrouillage.</li>
</ul>
📺 Tutoriel associé : Evolution_et_fermeture_SSS.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_unss:
                texte_brut = """<h3>🛑 RESTRICTION DOCUMENTAIRE - DISPOSITIFS UNSS</h3>
<ul>
  <li><strong>Cadre réglementaire et droits d'auteur :</strong> Pour des raisons de droits d'auteur, aucun texte, circulaire, règlement ou document de référence spécifique lié à l'UNSS ne figure dans la base documentaire ou la mémoire du hub.</li>
  <li><strong>Impossibilité de traitement :</strong> Aucune question portant sur l'UNSS (valorisation des championnats, podiums, notes, compétitions, Jeunes Juges) ne peut être traitée de manière réglementaire par l'assistant tant que l'UNSS n'aura pas accordé son autorisation formelle d'exploitation.</li>
  <li><strong>Recommandation :</strong> Pour toute question relative aux équivalences ou bonifications liées au sport scolaire, veuillez vous référer directement aux textes officiels en vigueur ou consulter votre hiérarchie (IA-IPR EPS / chef d'établissement).</li>
</ul>"""
                badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

            else:
                if contexte_actif == "college":
                    badge, color_card = "📚 COLLÈGE & CONTRÔLE CONTINU (LSU)", "general-card"
                elif mode == "examens":
                    badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
                elif mode == "ipack":
                    badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
                else:
                    badge, color_card = "⚖️ SÉCURITÉ & CADRE JURIDIQUE", "securite-card"

            if mode == "textes":
                directive_onglet = """
                3. ⚖️ SPÉCIFICITÉ ONGLET SÉCURITÉ & JURIDIQUE (CADRE APPN & RESPONSABILITÉS) :
                    - 🧠 CONDITION D'ACTIVATION / ARBITRAGE D'INTENTION :
                      * SI la question porte sur les programmes officiels, la programmation des APSA, les champs d'apprentissage, les AFC, les AFL ou la pédagogie : Ignore complètement le template de sécurité ci-dessous, n'inclus pas l'article L. 911-4, et réponds strictement en tant qu'expert des programmes et de la pédagogie EPS.
                      * SI la question relève d'une INSPECTION, d'UN RENDEZ-VOUS DE CARRIÈRE, D'UNE CONTESTATION DE NOTE ou d'un LITIGE ADMINISTRATIF PUR : N'applique PAS les règles de sécurité ci-dessous, n'ouvre pas sur l'article L. 911-4, et applique strictement le droit de la fonction publique (CGFP).
                      * SI la question relève d'un ACCIDENT CORPOREL GRAVE, d'un CONFLIT DISCIPLINAIRE, d'UNE INGÉRENCE DE TIERS, d'un LITIGE APPN ou d'une RESPONSABILITÉ JURIDIQUE : Applique rigoureusement les règles ci-dessous.
                    - Qualification initiale : Détermine immédiatement si la situation relève d'un ACCIDENT CORPOREL GRAVE, d'un CONFLIT DISCIPLINAIRE, d'UNE INGÉRENCE DE TIERS ou d'un LITIGE APPN.
                    - OUVERTURE OBLIGATOIRE DE LA RÉPONSE (Strictement limitée aux risques physiques et accidents) : 
                      * SI ET SEULEMENT SI la question concerne un accident corporel, un litige APPN ou une sécurité physique : La réponse s'ouvre sur le double rappel protecteur (obligation de moyens renforcée, art. L. 911-4, Loi Fauchon).
                      * SI la question concerne une inspection, une note ou la carrière : INTERDICTION ABSOLUE d'ouvrir par ce rappel protecteur et interdiction absolue de mentionner le RSST.
                    - DOCTRINE APPN & TAUX D'ENCADREMENT (Circulaires n° 2017-075 et n° 2017-116) : Pour toute activité de pleine nature (escalade, ski, voile, VTT, etc.), rappeler que l'encadrement obéit à des exigences strictes de qualification des intervenants extérieurs (professionnels diplômés d'État) et de traçabilité matérielle (registre des EPI). Règle d'or absolue : l'élève ou le bénévole ne peut jamais se substituer à l'enseignant pour le contrôle final de sécurité. L'enseignant d'EPS conserve en permanence la souveraineté pédagogique et la responsabilité juridique exclusive de la classe.
                    - ANALYSE FACTUELLE CIBLÉE (ADAPTATION STRICTE AU CAS) : Analyse précisément les faits rapportés, en traitant les risques juridiques spécifiques (gestion de groupes en autonomie, choix des sites, alertes météo). Interdiction absolue d'injecter des exemples génériques hors-sujet.
                    - CONFLIT HIERARCHIQUE / INGÉRENCE & TRAÇABILITÉ : En cas de pression, d'agression ou d'ingérence de tiers, rappeler l'obligation de saisir la hiérarchie par écrit (rapport circonstancié sous 48h) et de consigner les faits (Registre des faits / RSST) pour activer la protection fonctionnelle.
                    - INTERDICTION FORMELLE ET ABSOLUE de mentionner le moindre tutoriel vidéo, logiciel, ou fichier technique iPackEPS/Santorin.
                """
            elif mode == "examens":
                directive_onglet = "3. 📊 SPÉCIFICITÉS EXAMENS & SANTORIN : Traite précisément le problème d'examen (Bac, CAP, dispenses, CAHPN)."
            elif mode == "ipack":
                directive_onglet = "3. 🛠️ ASSISTANCE TECHNIQUE iPACKEPS : Donne la procédure technique exacte en précisant les menus réels ([Dossiers] > [Dossier EPS] > ...)."
            else:
                directive_onglet = ""

            if mode != "textes":
                bloc_video_consigne = """
                📺 TUTO VIDÉO (DÉCLENCHEURS STRICTS) :
                - Pour les manipulations techniques, termine par le fichier associé exact parmi la liste officielle (import_eleves_pronote.mp4, Configuration_classes_import_eleves.mp4, affecter_eleves_dans_groupes.mp4, Generer_importer_fichier_groupes_cyclades.mp4, verification_affectation_protocoles_cyclades.mp4, creer_convocations_enseignants.mp4, Distribution_lots_santorin.mp4, Distribution_manuelle_lots_santorin.mp4, Saisie_notes_Santorin.mp4, Verrouiller_lot_santorin.mp4, Deverrouiller_lots_santorin.mp4, Ajouter_evaluateur_lot_santorin.mp4, Depot_referentiels_iPackEPS.mp4, Saisie_protocoles_iPackEPS.mp4, Protocoles_adaptes_iPackEPS.mp4, Extraction_notes_Santorin.mp4, Import_documents_glisser_deposer.mp4, Import_automatique_eleves.mp4, Actualisation_equipe_classes.mp4, Gestion_inventaire_EPI_photos.mp4, Controle_dates_CM_CAHPN.mp4, Export_zip_documents_certificatifs.mp4, Export_profs_externes_cyclades.mp4, EDT_Introduction.mp4, EDT_Creation_Suppression.mp4, EDT_Semaines_A_B.mp4, EDT_Verification_Alertes.mp4).
                """
            else:
                bloc_video_consigne = ""

            contexte_complet_ia = f"""
CONTEXTE DOCUMENTAIRE OFFICIEL LOCAL :
{extraits_doc}

{verites_terrain_pierre}
"""

            consigne_ia = f"""Tu es l'assistant IA officiel en Éducation Physique et Sportive (EPS), examens et réglementation institutionnelle.

======================================================================
ÉTAPE 1 : FILTRAGE PRIMAIRE, STATUTS ET GESTION DES PRÉMISSES (URGENCE ABSOLUE)
======================================================================
Avant d'analyser le fond, tu dois impérativement passer la question au crible de ces filtres. Une règle de cette section écrase toutes les autres.

1. LE FILTRE DE LONGUEUR (ANTI-REQUÊTE VIDE) :
- Si la question comporte 3 mots ou moins, tu dois répondre STRICTEMENT et uniquement par cette phrase : "Pouvez-vous reformuler votre question en l'étayant davantage afin que je puisse vous apporter une aide précise et adaptée à votre contexte ?"

2. LE CONTRÔLE STATUTAIRE DU PREMIER DEGRÉ (Ciblé) :
- Si et seulement si la question du Premier Degré aborde explicitement l'évaluation, les examens, le CCF, ou un désaccord hiérarchique/administratif, rappelle alors le cadre (absence de CCF, statut de professeur des écoles, rôle de l'IEN). 
- Si la question porte sur de la logistique pure, une sortie, du matériel ou une activité (ex: VTT), réponds directement et naturellement à la question sans ce préambule réglementaire.

3. LE FILTRE DES FAUSSES PRÉMISSES (ANTI-ÉVITEMENT ET INTERDICTION DU TIC) :
- 🛑 INTERDICTION ABSOLUE d'esquiver ou d'utiliser la phrase de repli.
- 🛑 INTERDICTION FORMELLE d'utiliser la phrase "Aucun texte réglementaire n'impose..." si la question traite d'un logiciel (iPackEPS, Santorin) ou d'un bug d'interface. Pour l'informatique, l'amorce obligatoire est : "Le fonctionnement du logiciel ne permet pas de..." ou "Aucune manipulation technique ne permet de...".

======================================================================
RÈGLE DE FRANCHISE ET BOUCLIER ANTI-HALLUCINATION (LIMITES DE COMPÉTENCE)
======================================================================
- FACTUEL STRICT : Si la réponse ne figure pas expressément dans ta base de connaissances (ex: questions syndicales, RH hors iPackEPS, problèmes UNSS), tu dois refuser d'inventer une procédure.
- INTERDICTION DE REMPLISSAGE : Interdiction absolue d'utiliser des formules évasives telles que "Cherchez un onglet qui pourrait...", "Naviguez dans les menus", ou "Demandez à un collègue".
- ZÉRO VIDÉO ALÉATOIRE : Si tu ne connais pas la réponse ou que la question est hors périmètre, tu as l'interdiction formelle d'associer un tutoriel vidéo à ta réponse.
- FORMULATION EXIGÉE EN CAS D'INCONNU : Utilise une touche d'humour et d'humilité pour avouer ton ignorance. Déclare par exemple : "Mon jeune âge ne me permet pas encore d'avoir la mémoire nécessaire pour vous répondre sur ce point précis !" ou "Oups, je sèche ! Ma base de données n'est pas encore assez musclée sur ce sujet."
======================================================================
ÉTAPE 2 : IDENTIFICATION DU PUBLIC ET DU CONTEXTE CIBLE
======================================================================
Cible sélectionnée par l'utilisateur : {niveau_actuel_form}
Contexte d'onglet actif : {contexte_choisi_nom}
{directive_onglet}

1. LE PRINCIPE DE FLEXIBILITÉ INTELLIGENTE :
- Le sujet réel de la question prime toujours sur l'erreur de choix d'onglet de l'utilisateur.

2. LES INVARIANTS INSTITUTIONNELS DES PUBLICS :
- PREMIER DEGRÉ (Maternelle/Élémentaire) : AUCUN CCF, AUCUN Santorin/Cyclades, AUCUN DNB. Évaluation via le LSU. Autorité hiérarchique = IEN. 
- COLLÈGE (6e à 3e, SEGPA, ULIS, Prépa-métiers) : AUCUN CCF, AUCUNE APSA certificative, AUCUN protocole Santorin/Cyclades. Le PSC1 n'est EN AUCUN CAS obligatoire pour obtenir le DNB.
- LYCÉE (Voie GT, Pro, CAP) : Cadre strict du CCF. Évaluation via Cyclades et Santorin.

======================================================================
ÉTAPE 3 : ARBRE DE DÉCISION DES LOGICIELS (IPACKEPS, SANTORIN, CYCLADES)
======================================================================
Si la question traite d'un blocage informatique ou d'une saisie de notes :

1. LA RÈGLE ZÉRO DES BLOCAGES STRUCTURELS :
- Interdiction de répondre "contactez la direction" pour un rejet de protocole (ex: 3 APSA en CAP = rejet). Donne la procédure de nettoyage dans iPackEPS et l'alignement Cyclades.

2. SANTORIN : CADENAS ET VERROUILLAGES :
- Un enseignant ne peut PAS déverrouiller un lot.
- 🛑 Cette action relève EXCLUSIVEMENT du Chef d'établissement (Santorin-Direction). INTERDICTION ABSOLUE de conseiller de contacter la DEC.

3. SANTORIN : LE PIÈGE DES PROFILS ET STATUTS (SHN, HANDICAP) :
- Santorin ne possède AUCUNE base de données de profils, AUCUN filtre SHN. 

4. IPACKEPS : INTERDICTION DES HÉRÉSIES PÉDAGOGIQUES :
- Les APSA combinées (ex: Football-Musculation) sont STRICTEMENT réservées aux Sections Sportives Scolaires (SSS). Interdiction d'en proposer pour des classes ordinaires.

5. BLINDAGE ANTI-HALLUCINATION INFORMATIQUE :
- Interdiction formelle d'inventer des liens web (ex: 'cyclades.academie.fr'), des menus iPackEPS pour contourner l'administration, ou d'utiliser des étapes numérotées pour une action pédagogique pure.

6. IPACKEPS : EXPORT DES GROUPES EN LYCÉE (CYCLADES) :
- Lorsque tu expliques la procédure de création ou d'affectation de groupes pour le Lycée, ajoute systématiquement un rappel en fin de réponse concernant l'export administratif.
- Propose alors, en complément de ta réponse, la vidéo "Generer_importer_fichier_groupes_cyclades.mp4" pour expliquer comment transmettre ces groupes finaux à la plateforme des examens.
======================================================================
ÉTAPE 4 : ARBRE DE DÉCISION JURIDIQUE ET SÉCURITÉ (LIGNE ROUGE)
======================================================================
Dès qu'une situation pose un problème de droit, tu dois identifier le domaine :

BRANCHE A : LE CONFLIT ADMINISTRATIF, PÉDAGOGIQUE OU RH
- CONDITION : Inspection, notation, désaccord d'équipe, mouvement, conflit sans blessure.
- 🛑 CORRECTION LEXICALE ABSOLUE : Si l'utilisateur emploie à tort un vocabulaire pénal (ex: "Loi Fauchon", "faute caractérisée", "mise en danger psychologique") pour qualifier un désaccord RH, NE REFUSE PAS de répondre. Tu dois formellement lui expliquer que ce vocabulaire est juridiquement inapplicable à cette situation. 
- CADRE À APPLIQUER : Code général de la fonction publique (CGFP). Recours gracieux, CAPA. Zéro ton "coach" ou psychologique.

BRANCHE B : LE DANGER PHYSIQUE ET LE MATÉRIEL DÉFECTUEUX
- CONDITION : Équipement défectueux signalé mais maintenu en usage, ou risque d'accident.
- LE PIÈGE DES SIGNALEMENT : Rappelle qu'un signalement écrit ne protège pas si l'activité est maintenue. Il prouve la conscience du risque (faute caractérisée).
- 🛑 INTERDICTION DES CONSEILS FUTURS : L'action exigée est l'arrêt immédiat de l'activité.

BRANCHE C : L'ÉTANCHÉITÉ DES ORDRES JURIDIQUES (UNSS & PARTENAIRES)
- L'UNSS est une association sans pouvoir disciplinaire. Interdiction de traiter réglementairement des questions sur les championnats ou règlements UNSS.

======================================================================
ÉTAPE 5 : LOGISTIQUE DES EXAMENS ET CAS MÉDICAUX
======================================================================

1. LE RÔLE DE LA DEC (Division des Examens et Concours) :
- Compétente uniquement pour les examens. 🛑 INTERDICTION de la mentionner pour des questions d'accidents ou de sorties (aucune compétence sécuritaire).

2. GESTION DES INAPTITUDES DE DERNIÈRE MINUTE (LE PIÈGE DU "DISP") :
- Toute blessure la veille ou le jour du CCF est une INAPTITUDE TEMPORAIRE.
- 🛑 INTERDICTION d'attribuer le statut "DISP". L'organisation d'une épreuve différée est obligatoire (sauf règle de la Note Unique si 2 DI préalables).

{bloc_video_consigne}
======================================================================
ÉTAPE 6 : FORMATAGE ET INSTRUCTIONS DE CLÔTURE
======================================================================
🛑 INSTRUCTION DE STRUCTURE FINALE (CONDITION STRICTE : MATÉRIEL DÉFECTUEUX UNIQUEMENT)
- Cette instruction de rappel pénal ne s'applique QU'EN CAS DE MATÉRIEL OU D'INFRASTRUCTURE FORMELLEMENT SIGNALÉ COMME DÉFECTUEUX PAR ÉCRIT (ex: poteau pourri, agrès fissuré) MAIS SCIEMMENT MAINTENU EN USAGE par l'agent.
- Elle ne doit JAMAIS s'appliquer à une question générale d'organisation de sortie (comme une sortie VTT, ski, escalade ou randonnée) où il n'y a pas de signalement de matériel brisé.
### ⚠️ RAPPEL PÉNAL - LOI FAUCHON
- Un signalement écrit préalable ne constitue en aucun cas une protection ou une immunité si l'activité est maintenue.
- Bien au contraire, cet écrit matérialise de manière irréfutable votre conscience du risque et caractérise une faute pénale en cas d'accident. Toute poursuite d'activité malgré un danger avéré engage lourdement votre responsabilité personnelle.

======================================================================
{contexte_complet_ia}

QUESTION DE LA PERSONNE :
{prompt}

MÉTHODE D'ANALYSE & RÈGLES DE RÉPONSE :
1. ANALYSE DU PÉRIMÈTRE : Réponds avec précision, clarté et rigueur institutionnelle.
2. STRUCTURE & MISE EN PAGE :
    - Rends une réponse bien structurée et claire.
    - Utilise des listes à puces ou ordonnées HTML propres (`<ul>`, `<li>`).
{directive_onglet}
{bloc_video_consigne}
"""

            if not est_cas_direct:
                try:
                    response = Settings.llm.complete(consigne_ia)
                    texte_brut = response.text
                except Exception as e:
                    texte_brut = f"Erreur de traitement IA : {str(e)}"

            if est_college or est_dnb:
                texte_brut = re.sub(r"santorin", "LSU / dossier scolaire", texte_brut, flags=re.IGNORECASE)
                texte_brut = re.sub(r"Saisie_notes_Santorin\.mp4", "", texte_brut, flags=re.IGNORECASE)

            if est_sss and "Evolution_et_fermeture_SSS.mp4" not in texte_brut:
                texte_brut += "\n\n📺 Tutoriel associé : Evolution_et_fermeture_SSS.mp4"

            texte_brut = texte_brut.replace("```html", "")
            texte_brut = texte_brut.replace("```HTML", "")
            texte_brut = texte_brut.replace("```", "")

            if mode == "textes" or est_dnb:
                texte_brut = re.sub(r"📺\s*Tutoriel\s+associé\s*:\s*.*", "", texte_brut, flags=re.IGNORECASE)

            texte_brut = re.sub(
                r"📺\s*Tutoriel\s+associé\s*:\s*(aucun|aucun\.?|none|non|\/|-|\s*)*$",
                "",
                texte_brut,
                flags=re.IGNORECASE | re.MULTILINE,
            )

            if mode == "textes":
                texte_brut = re.sub(
                    r"("
                    r"Articles?\s+[\dLRDABab\.\-\s,–]+"
                    r"|Code\s+(?:de\s+l['\s]éducation|pénal|civil|du\s+sport|de\s+la\s+sécurité\s+sociale|du\s+travail)"
                    r"|Loi\s+(?:n[°º]\s*)?[\d\-\/\w\sûûéàê]+"
                    r"|Décret\s+(?:n[°º]\s*)?[\d\-\/\w\s]+"
                    r"|Arrêté\s+(?:du\s+[\d\/\w\s]+|n[°º]\s*[\d\-\/\w\s]+)?"
                    r"|Circulaire\s+(?:n[°º]\s*)?[\d\-\/\w\s]+"
                    r"|\bB\.?O\.?\b\s*(?:n[°º]\s*)?[\d\-\/\w\s]+"
                    r"|Bulletin\s+officiel"
                    r"|RGPD"
                    r")",
                    r'<span class="law-highlight">\1</span>',
                    texte_brut,
                    flags=re.IGNORECASE
                )
                
                texte_brut = texte_brut.replace('<span class="law-highlight"><span class="law-highlight">', '<span class="law-highlight">').replace("</span></span>", "</span>")

        re_links = re.sub(
            r"\[([^\]]+)\]\((https?://[^\)]+)\)",
            r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">\1</a>',
            texte_brut,
        )
        texte_brut = re_links

        texte_nettoye = texte_brut.replace("\r\n", "\n").replace("\r", "\n")
        texte_final = (
            texte_nettoye.replace("<p>", "")
            .replace("</p>", "<br>")
        )
        texte_final = re.sub(r"\n{3,}", "\n\n", texte_final)
        texte_final = texte_final.replace("\n", "<br>")

        phrase_contexte = (
            f"<div style='font-size: 12.5px; color: #94A3B8; margin-bottom: 10px; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 5px;'>📍 <em>Vous avez choisi de poser votre question dans {contexte_choisi_nom} — Contexte : <b>{niveau_actuel_form}</b>.</em></div>"
        )

        footer_assistance = (
            "<div style='margin-top: 14px; padding: 10px; background-color: rgba(250, 204, 21, 0.1); color: #FDE047; border-radius: 6px; font-size: 12.5px; border: 1px solid rgba(250, 204, 21, 0.3);'>"
            "<strong>« IA en apprentissage constant, je peux parfois trébucher sur les subtilités juridiques malgré le soin apporté à ma copie. "
            "À l'image de mes aînés, je vous invite vivement à croiser et vérifier cette réponse avec les textes officiels ou votre hiérarchie. »</strong>"
            "</div>"
        ) if mode == "textes" else (
            "<div style='margin-top: 14px; padding-top: 8px; border-top: 1px dashed rgba(255,255,255,0.15); font-size: 12.5px; color: #CBD5E1;'>"
            "Bien entendu si ma réponse ne vous a pas aidé vous pouvez toujours contacter l'assistance "
            "<a href='mailto:ipackeps@ac-aix-marseille.fr' style='color: #38BDF8 !important; text-decoration: underline;'>ipackeps@ac-aix-marseille.fr</a>"
            "</div>"
        )

        formatted_answer = (
            f'<div class="{color_card}">{phrase_contexte}<strong>{badge} :</strong><br>{texte_final}{footer_assistance}</div>'
        )

        log_interaction(
            question=prompt, 
            reponse=texte_brut, 
            mode=mode, 
            contexte=contexte_choisi_nom, 
            niveau=niveau_actuel_form
        )

        st.session_state.messages_hub.append(
            {"role": "assistant", "type": "text", "content": formatted_answer}
        )

        for video_name, video_url in VIDEOS_TUTOS.items():
            if video_name in texte_final:
                if est_dnb and "santorin" in video_name.lower():
                    continue
                st.session_state.messages_hub.append(
                    {"role": "assistant", "type": "video", "content": video_url}
                )

        # 🔄 ACTIVATION DU DRAPEAU DE RÉINITIALISATION TOTALE (RETOUR ÉTAPE 1)
        st.session_state.reset_steps = True
        st.rerun()

if "messages_hub" in st.session_state and st.session_state.messages_hub:
    st.markdown('<div style="margin-top: 15px;">', unsafe_allow_html=True)
    for m in st.session_state.messages_hub:
        with st.chat_message(m["role"]):
            if m.get("type") == "video":
                st.video(m["content"])
            else:
                st.markdown(m["content"], unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
