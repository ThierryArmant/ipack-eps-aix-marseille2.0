import base64
import datetime
import os
import re
import smtplib
import unicodedata
import requests
import streamlit as st
from email.mime.text import MIMEText
from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# ======================================================================
# 🔧 OUTILS DE NORMALISATION ET DE DÉTECTION DE MOTS-CLÉS
# ======================================================================
def normaliser(txt):
    """Minuscule + suppression des accents (é -> e, ù -> u, etc.)."""
    txt = unicodedata.normalize("NFD", txt.lower())
    return "".join(c for c in txt if unicodedata.category(c) != "Mn")


_MOTS_NEUTRES_SUJET = {
    "ipack", "ipackeps", "comment", "pourquoi", "quand", "alors", "aussi", "avoir", "faire", "faut", "dois", "doit",
    "peux", "peut", "veux", "vous", "nous", "elle", "elles", "leur", "leurs", "mais", "avec", "sans", "dans", "pour",
    "cette", "cela", "celui", "cette", "mes", "tous", "tout", "toute", "toutes", "merci", "bonjour", "cordialement",
    "question", "probleme", "trouve", "toujours", "encore", "apres", "avant", "puis", "etre", "sont", "suis", "etait",
    # mots présents dans presque toutes les fiches : ils ne prouvent pas qu'on parle du même sujet
    "eleve", "eleves", "groupe", "groupes", "classe", "classes", "apsa", "apsas", "dossier", "dossiers",
}


def _mots_sujet(txt):
    """Mots porteurs de sens d'un texte, ramenés à leurs 4 premières lettres (sans accents) pour tolérer pluriels et conjugaisons."""
    mots = re.findall(r"[a-z0-9]+", normaliser(re.sub(r"<[^>]+>", " ", txt)))
    return {m[:4] for m in mots if len(m) >= 4 and m not in _MOTS_NEUTRES_SUJET}


def sujet_different(precision, question_precedente, reponse_precedente):
    """
    True si le texte saisi dans la zone de précision est en réalité une NOUVELLE question,
    sans rapport avec l'échange précédent (aucun mot porteur de sens en commun).
    Dans ce cas on la traite comme une question neuve, sans lui accoler l'ancien échange.
    """
    mots_precision = _mots_sujet(precision)
    if len(mots_precision) < 3:
        return False  # trop court pour juger : on considère que c'est bien une précision
    mots_avant = _mots_sujet(question_precedente + " " + reponse_precedente)
    communs = mots_precision & mots_avant
    return len(communs) == 0 or (len(communs) / len(mots_precision)) < 0.15


def contient(txt, motifs):
    """True si au moins un motif (expression régulière) est trouvé dans txt."""
    return any(re.search(m, txt) for m in motifs)


def contient_mot_cle(texte, mots):
    """
    Recherche de mots-clés sans faux positifs :
    - les mots courts (3 caractères ou moins : ps, ms, cp, cap, bac, loi, eps...)
      doivent être des mots entiers (évite que "ps" matche "temps" ou "cap" matche "capacité") ;
    - les mots plus longs sont cherchés en sous-chaîne (tolère pluriels et variantes).
    """
    for m in mots:
        if len(m) <= 3:
            if re.search(r"(?<!\w)" + re.escape(m) + r"(?!\w)", texte):
                return True
        elif m in texte:
            return True
    return False


# ======================================================================
# 📊 CONFIGURATION GOOGLE SHEETS LOGS (QUESTIONS HUB)
# ======================================================================
WEBHOOK_URL = (
    "https://script.google.com/macros/s/AKfycbyVq8_DCLnAyrr7xEUw1Xbdze0Lm1S-P6RHlXJPE2CmaBD39lpFfQjpuHQhxmL0z3bJ/exec"
)


def _texte_simple_pour_journal(texte):
    """Retire la mise en forme (balises HTML, gras Markdown) pour que la réponse soit lisible dans le Google Sheet."""
    import re as _re, html as _html
    t = str(texte or "")
    t = _re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h[1-6]>|</div>", "\n", t)
    t = _re.sub(r"(?i)<li[^>]*>", "- ", t)
    t = _re.sub(r"<[^>]+>", "", t)
    t = t.replace("**", "").replace("`", "")
    t = _html.unescape(t)
    t = _re.sub(r"[ \t]+\n", "\n", t)
    t = _re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def log_interaction(question, reponse, mode="", contexte="", niveau=""):
    reponse = _texte_simple_pour_journal(reponse)
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
import html as html_lib

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
# NB : "Import_automatique_eleves.mp4" est cité dans certains textes ci-dessous
# mais n'a pas encore d'URL dans ce dictionnaire. Ajoutez la ligne suivante
# quand vous aurez le lien :
#     "Import_automatique_eleves.mp4": "https://...",
VIDEOS_TUTOS = {

    "Manipulations_Nouvelle_Annee_iPackEPS.mp4": "https://youtu.be/do_8PVQDuqE",
    "import_eleves_pronote.mp4": "https://www.youtube.com/watch?v=RlScDjd8kHk",
    "Configurer_Classes_Sports_Etudes.mp4": "https://youtu.be/AEXIn3d6K6U",
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
    "Protocoles_adaptes_iPackEPS.mp4": "https://youtu.be/CUybrlkTtJ0",
    "Extraction_notes_Santorin.mp4": "https://youtu.be/KooSwcy4gAA",
    "Import_documents_glisser_deposer.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Import_documents_glisser_deposer.mp4",
    "Configuration_classes_import_eleves.mp4": "https://www.youtube.com/watch?v=tu8J1RBUTwk",
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
    "Gestion_dossier_APPN.mp4": "https://youtu.be/RUlrS0a1YA0",
    "Gestion_groupes_iPackEPS.mp4": "https://youtu.be/4mqx_sWqSbE",
    "Sequences_apprentissage_groupes.mp4": "https://youtu.be/y4Woi0RY50I",
    "Apsa_certificatives_CAP.mp4": "https://youtu.be/zypGSbpJFnU",
    "Declaration_projet_APPN.mp4": "https://youtu.be/f_BVPpLeC8w",
    "Validation_chef_APPN.mp4": "https://youtu.be/2iSTkzR0fns",
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
# 💬 PRÉCISION UNIQUE : le hub répond à une question, il ne converse pas.
# Si la question était mal formulée, le collègue peut la préciser UNE fois ; on ne garde que cet échange.
NB_RELANCES_MAX = 1
if "dernier_echange" not in st.session_state:
    st.session_state.dernier_echange = None

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


# ✅ Liens officiels affichés sous les réponses de l'onglet Textes (aucun appel à l'IA, aucun token).
# Clé = nom du fichier dans data/ ; valeur = (libellé affiché, [(texte du lien, adresse), ...]).
# Pour ajouter un lien : ajouter une ligne ici. Sans entrée, le document s'affiche en texte simple.
SOURCES_REFERENCE = {
    "programmes_officiels_eps.txt": (
        "Programmes officiels d'EPS (collège et lycée)",
        [
            ("Programmes cycles 2, 3 et 4 (BO spécial n°11, 26 nov. 2015)", "https://www.education.gouv.fr/bo/15/Special11/MENE1526483A.htm"),
            ("Programme EPS lycée GT (BO spécial n°1, 22 janv. 2019)", "https://www.education.gouv.fr/bo/19/Special1/MENE1901574A.htm"),
        ],
    ),
    "complement_obligations_service_eps.txt": (
        "Obligations de service des professeurs d'EPS (décret 2014-940)",
        [("Circulaire d'application (BO)", "https://www.education.gouv.fr/bo/15/Hebdo14/MENH1506031C.htm")],
    ),
    "complement_natation_scolaire.txt": (
        "Natation scolaire et savoir-nager",
        [
            ("Circulaire 2017-127 (natation)", "https://ent2d.ac-bordeaux.fr/disciplines/eps/wp-content/uploads/sites/33/2018/09/Enseignement-de-la-natation-Circulaire-n%C2%B0-2017-127-du-22-8-2017.pdf"),
            ("Aisance aquatique (BO 2022)", "https://www.education.gouv.fr/bo/22/Hebdo9/MENE2129643N.htm"),
        ],
    ),
    "matrice_AFL_lycee.txt": (
        "Matrice des AFL du lycée (programmes 2019)",
        [("Programme EPS lycée GT (BO spécial n°1, 22 janv. 2019)", "https://www.education.gouv.fr/bo/19/Special1/MENE1901574A.htm")],
    ),
    "prog_apsa_lycee_tronc_commun.txt": (
        "Programmation des APSA au lycée (tronc commun)",
        [("Programme EPS lycée GT (BO spécial n°1, 22 janv. 2019)", "https://www.education.gouv.fr/bo/19/Special1/MENE1901574A.htm")],
    ),
    "programmes_college_2015_carte_mentale.txt": (
        "Programmes du collège 2015 (carte mentale)",
        [("Programmes cycles 2, 3 et 4 (BO spécial n°11, 26 nov. 2015)", "https://www.education.gouv.fr/bo/15/Special11/MENE1526483A.htm")],
    ),
}


def libelle_source(node_with_score):
    """Nom lisible (avec liens officiels si connus) du document d'où provient un extrait."""
    try:
        md = node_with_score.node.metadata or {}
    except Exception:
        return None
    titre = md.get("title")
    url = md.get("url")
    if titre and url:
        return f'<a href="{url}" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">{titre}</a>'
    if titre:
        return str(titre)
    src = md.get("source")
    if src:
        cle = str(src)
        m = re.search(r"\(([^()]+\.txt)\)\s*$", cle)
        if m:
            cle = m.group(1)
        if cle in SOURCES_REFERENCE:
            libelle, liens = SOURCES_REFERENCE[cle]
            html = libelle
            if liens:
                html += " — " + " · ".join(
                    f'<a href="{u}" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">{t}</a>'
                    for t, u in liens
                )
            return html
        nom = re.sub(r"\.txt$", "", cle, flags=re.IGNORECASE).replace("_", " ").strip()
        return nom[:1].upper() + nom[1:]
    return None


def obtenir_cle_fichier():
    mtimes = []
    for fp in ["data/examens/memoire_examens_santorin.txt", "ipack.txt", "data/textes/partenariats_defense_citoyennete.txt"]:
        if os.path.exists(fp):
            try:
                mtimes.append(os.path.getmtime(fp))
            except Exception:
                pass
    for fp in ["data/programmes_officiels_eps.txt"]:
        if os.path.exists(fp):
            mtimes.append(os.path.getmtime(fp))
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


# ======================================================================
# DÉCOUPAGE DE LA MÉMOIRE PAR FICHE (iPackEPS et Examens)
# Avant : les fichiers étaient coupés en gros blocs de longueur fixe, chaque bloc mêlant plusieurs
# questions-réponses sans rapport. L'IA recevait 10 blocs fourre-tout et piochait la mauvaise fiche.
# Maintenant : une question-réponse (ou une situation) = un passage, précédé du titre de son article.
# Rien ne change dans la façon de remplir les fichiers .txt.
# ======================================================================
_RE_SEP = re.compile(r"^\s*[=\-]{10,}\s*$")
_RE_TITRE = re.compile(r"^(#{2,4}\s+\S|=== .+|TITRE\s*:\s*\S|\[(ARTICLE|SITUATION|SECTION|PROCÉDURE|PROCEDURE|DOC_REF|ERREUR|DIAGNOSTIC|OPTION)\b)")
_RE_QR = re.compile(r"^\s*-\s*Q\d+\b")
_RE_UNITE = re.compile(r"^([*\-•]\s+\S|\d+\.\s+\S|\s+[*\-]\s+\*\*Question\s*\d+)")


def decouper_en_fiches(texte, taille_bloc_entier=2200, taille_cible=1200):
    """
    Découpe une base documentaire en « fiches » cohérentes au lieu de blocs de longueur fixe :
    - un titre (###, [ARTICLE ...], [SITUATION ...], ligne soulignée) ouvre une nouvelle fiche ;
    - dans un article à questions/réponses (- Q1 / - R1), chaque question-réponse devient une fiche ;
    - un long passage sans questions/réponses est regroupé par puces, sans jamais couper une puce ;
    - chaque fiche commence par le titre de son article, pour rester compréhensible seule.
    """
    lignes = texte.replace("\r\n", "\n").split("\n")
    n = len(lignes)

    # 1) Repérage des titres
    est_titre = [False] * n
    for i, l in enumerate(lignes):
        if _RE_SEP.match(l):
            continue
        if _RE_TITRE.match(l):
            est_titre[i] = True
        elif l.strip() and i + 1 < n and _RE_SEP.match(lignes[i + 1]) and (i == 0 or _RE_SEP.match(lignes[i - 1]) or not lignes[i - 1].strip()):
            est_titre[i] = True

    # 2) Blocs = un titre + son contenu (les lignes de séparation sont ignorées)
    blocs, titre, corps = [], "", []
    for i, l in enumerate(lignes):
        if _RE_SEP.match(l):
            continue
        if est_titre[i]:
            if any(c.strip() for c in corps):
                blocs.append((titre, corps))
            elif titre:
                # titre sans contenu (ex. [SECTION ...]) : il sert de chapeau au titre suivant
                l = titre + " — " + l.lstrip("# ").strip()
            titre, corps = l.lstrip("# ").strip(), []
        else:
            corps.append(l)
    if any(c.strip() for c in corps):
        blocs.append((titre, corps))

    def _fiche(titre, lignes_corps):
        corps_txt = "\n".join(lignes_corps).strip()
        if not corps_txt:
            return None
        return (titre + "\n" + corps_txt).strip() if titre else corps_txt

    fiches = []
    for titre, corps in blocs:
        a_des_qr = any(_RE_QR.match(l) for l in corps)
        longueur = sum(len(l) + 1 for l in corps)

        if not a_des_qr and longueur <= taille_bloc_entier:
            f = _fiche(titre, corps)
            if f:
                fiches.append(f)
            continue

        # Découpage en unités
        unites, courante = [], []
        for l in corps:
            debut = _RE_QR.match(l) if a_des_qr else _RE_UNITE.match(l)
            if debut and any(c.strip() for c in courante):
                unites.append(courante)
                courante = []
            courante.append(l)
        if any(c.strip() for c in courante):
            unites.append(courante)

        if a_des_qr:
            # une question-réponse = une fiche ; le texte d'introduction de l'article = une fiche
            for u in unites:
                f = _fiche(titre, u)
                if f:
                    fiches.append(f)
        else:
            # Fiche « Question / Réponses par public » trop longue : la question est rappelée en tête de chaque morceau
            rappel = []
            if unites and "**Question**" in "\n".join(unites[0]) and len(unites) > 1:
                rappel, unites = unites[0], unites[1:]
            paquet, taille = list(rappel), 0
            for u in unites:
                t = sum(len(l) + 1 for l in u)
                if taille and taille + t > taille_cible:
                    f = _fiche(titre, paquet)
                    if f:
                        fiches.append(f)
                    paquet, taille = list(rappel), 0
                paquet.extend(u)
                taille += t
            f = _fiche(titre, paquet)
            if f:
                fiches.append(f)

    # 3) Suppression des doublons exacts
    vues, uniques = set(), []
    for f in fiches:
        cle = re.sub(r"\s+", " ", f)
        if cle not in vues:
            vues.add(cle)
            uniques.append(f)
    return uniques


def charger_dossier_txt_securise(chemin_dossier, par_fiche=False):
    docs_trouves = []
    if os.path.exists(chemin_dossier) and os.path.isdir(chemin_dossier):
        for nom_fichier in os.listdir(chemin_dossier):
            if nom_fichier.lower().endswith(".txt"):
                chemin_complet = os.path.join(chemin_dossier, nom_fichier)
                try:
                    with open(
                        chemin_complet, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        contenu = f.read()
                    morceaux = [contenu]
                    if par_fiche:
                        try:
                            morceaux = decouper_en_fiches(contenu) or [contenu]
                        except Exception:
                            # En cas de souci de découpage, on retombe sur l'ancien fonctionnement (fichier entier)
                            morceaux = [contenu]
                    for morceau in morceaux:
                        docs_trouves.append(
                            Document(
                                text=morceau,
                                metadata={"source": nom_fichier},
                            )
                        )
                except Exception:
                    pass
    return docs_trouves


@st.cache_resource(max_entries=1, show_spinner=False)
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
    docs_santorin.extend(charger_dossier_txt_securise("data/examens", par_fiche=True))
    # memoire_examens_santorin.txt est déjà dans data/examens : on ne le recharge plus une 2e fois en un seul bloc
    # (il apparaissait en double dans les passages transmis à l'IA).
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(
        similarity_top_k=10
    )


@st.cache_resource(max_entries=1, show_spinner=False)
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
    docs_ipack.extend(charger_dossier_txt_securise("data/ipack", par_fiche=True))
    docs_ipack.extend(charger_consignes_ipack())
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(
        similarity_top_k=10
    )


@st.cache_resource(max_entries=1, show_spinner=False)
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
    # ✅ AJOUT : programmes officiels d'EPS (collège & lycées) rattachés à la partie Réglementation
    fp_prog = "data/programmes_officiels_eps.txt"
    if os.path.exists(fp_prog):
        try:
            with open(fp_prog, "r", encoding="utf-8", errors="ignore") as f:
                docs_textes.append(
                    Document(
                        text=f.read(),
                        metadata={"source": "programmes_officiels_eps.txt"},
                    )
                )
        except Exception:
            pass
    if os.path.exists("data/textes/premier_degré"):
        docs_textes.extend(charger_dossier_txt_securise("data/textes/premier_degré"))
    docs_textes.extend(charger_consignes_ipack())
    return VectorStoreIndex.from_documents(docs_textes, recursive=True).as_retriever(
        similarity_top_k=10
    )


@st.cache_resource(max_entries=1, show_spinner=False)
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
        similarity_top_k=10
    )


timestamp_fichier = obtenir_cle_fichier()
# ✅ AJOUT : recherche complémentaire PAR MOTS. La recherche « par le sens » ratait parfois la fiche qui contient
# pourtant les mots mêmes de la question (ex. « Santorin refuse ma note à virgule ») parce que d'autres fiches lui
# ressemblaient davantage. On repère donc aussi les fiches dont le titre, les mots-clés ou les questions types
# partagent des mots RARES avec la question, et on les transmet à l'IA en plus.
def _racines_mots(txt):
    """Mots utiles d'un texte, réduits à leurs 6 premières lettres (verrouiller / verrouillage -> verrou)."""
    return {m[:6] for m in re.findall(r"[a-z0-9]{3,}", normaliser(txt)) if m not in _MOTS_NEUTRES_SUJET}


@st.cache_resource(max_entries=1, show_spinner=False)
def initialiser_recherche_mots(cle_fremt):
    import math
    bases = {}
    for nom, dossier in (("santorin", "data/examens"), ("ipack", "data/ipack")):
        fiches = []
        try:
            for d in charger_dossier_txt_securise(dossier, par_fiche=True):
                lignes = (d.text or "").split("\n")
                entete = [lignes[0]] + [l for l in lignes[1:] if re.match(r"\s*-\s*(Mots-cl|Formulations|Q\d* ?:)", l)][:8]
                racines = _racines_mots(" ".join(entete))
                if racines:
                    fiches.append((d.text, racines))
        except Exception:
            fiches = []
        frequence = {}
        for _, racines in fiches:
            for r in racines:
                frequence[r] = frequence.get(r, 0) + 1
        n = max(len(fiches), 1)
        poids = {r: math.log(1 + n / c) for r, c in frequence.items()}
        bases[nom] = (fiches, poids)
    return bases


def chercher_par_mots(bases, nom, question, maximum=3):
    """Fiches de la base `nom` qui partagent le plus de mots rares avec la question (au moins deux)."""
    fiches, poids = bases.get(nom, ([], {}))
    q = _racines_mots(question)
    if re.search(r"\d,\d", question):
        q.add("virgul")  # une note écrite « 4,5 » : la fiche utile parle de « virgule »
    q = {r for r in q if r in poids}
    if len(q) < 2:
        return []
    total = sum(poids[r] for r in q)
    resultats = []
    for texte, racines in fiches:
        communs = q & racines
        if len(communs) >= 2:
            score = sum(poids[r] for r in communs)
            if score >= 0.35 * total:
                resultats.append((score, texte))
    resultats.sort(key=lambda x: -x[0])
    return [t for _, t in resultats[:maximum]]


retriever_santorin = initialiser_base_santorin(timestamp_fichier)
try:
    recherche_mots = initialiser_recherche_mots(timestamp_fichier)
except Exception:
    recherche_mots = {}
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

# On lit l'état actuel de la session (sécurisé)
module_actif = st.session_state.get("active_module")

titre_affiche = label_titres.get(
    module_actif,
    "⚠️ EN ATTENTE DE SÉLECTION DU CONTEXTE CI-DESSOUS ⬇️"
)
st.markdown(
    f'<div class="column-title-top"><span class="instruction">⚙️ ÉTAPE 1 : CHOISISSEZ LE CONTEXTE DE VOTRE QUESTION</span><span class="mode-actuel">{titre_affiche}</span></div>',
    unsafe_allow_html=True,
)

col_b1, col_b2, col_b3 = st.columns(3, gap="small")

# 🔒 LE VERROU EST ICI : On définit la couleur en dur AVANT de créer les boutons
btn_ip_type = "primary" if module_actif == "ipack" else "secondary"
btn_ex_type = "primary" if module_actif == "examens" else "secondary"
btn_se_type = "primary" if module_actif == "textes" else "secondary"

with col_b1:
    if st.button(
        "🛠️ iPackEPS",
        use_container_width=True,
        key="btn_ip",
        type=btn_ip_type,
    ):
        st.session_state.active_module = "ipack"
        st.session_state.contexte_valide = True
        st.session_state.public_valide = False
        st.session_state.messages_hub = []
        st.session_state.dernier_echange = None
        st.rerun()
        
with col_b2:
    if st.button(
        "📊 Examens &\nSantorin",
        use_container_width=True,
        key="btn_ex",
        type=btn_ex_type,
    ):
        st.session_state.active_module = "examens"
        st.session_state.contexte_valide = True
        st.session_state.public_valide = False
        st.session_state.messages_hub = []
        st.session_state.dernier_echange = None
        st.rerun()
        
with col_b3:
    if st.button(
        "🔒 Sécurité &\nCadres Règl.",
        use_container_width=True,
        key="btn_se",
        type=btn_se_type,
    ):
        st.session_state.active_module = "textes"
        st.session_state.contexte_valide = True
        st.session_state.public_valide = False
        st.session_state.messages_hub = []
        st.session_state.dernier_echange = None
        st.rerun()

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
                        "🔺 Décrivez votre problème en une phrase complète : ce que vous faites, où ça bloque, le message affiché..."
                    ),
                    label_visibility="collapsed",
                )
            with col_submit:
                bouton_envoyer = st.form_submit_button(
                    "🚀 Poser la question", use_container_width=True, type="primary"
                )

            if bouton_envoyer and prompt_brut.strip():
                prompt = prompt_brut.strip()
                
                # --- INJECTION DU SABLIER ICI ---
                with st.spinner("⏳ Recherche dans la base documentaire et analyse de la réponse en cours..."):
                    # On stocke temporairement la question dans la session pour déclencher la suite
                    st.session_state.current_prompt = prompt

# ======================================================================
# 9. TRAITEMENT RAG & FLUX DE MESSAGES
# ======================================================================
prompt_a_traiter = st.session_state.get("current_prompt", None)

if prompt_a_traiter:
    prompt = prompt_a_traiter
    
    # 🛡️️ SÉCURITÉ ANTI-DOUBLON ABSOLUE
    if "current_prompt" in st.session_state:
        del st.session_state.current_prompt

    _messages_precedents = list(st.session_state.get("messages_hub") or [])
    st.session_state.messages_hub = []

    # 💬 RELANCE : le collègue a choisi de préciser sa question précédente.
    # On réunit sa question d'origine et sa précision : la recherche dans la base se fait sur les deux,
    # à neuf (les passages de la question précédente ne sont pas réutilisés).
    relance_ctx = st.session_state.pop("relance_ctx", None)
    question_affichee = prompt
    ctx_onglet = relance_ctx  # onglet et public de la question précédente (conservés dans tous les cas)
    if relance_ctx and relance_ctx.get("origine") != "courte" and sujet_different(prompt, relance_ctx["question"], relance_ctx["reponse"]):
        # Le collègue a tapé une NOUVELLE question dans la zone de précision : on la traite comme une question neuve,
        # dans le même onglet et pour le même public, sans lui accoler l'ancien échange (ni coût supplémentaire, ni mélange).
        relance_ctx = None
    if relance_ctx:
        prompt = f"{relance_ctx['question']} — Précision : {prompt}"
        # AFFICHAGE UNIQUEMENT : la question et la réponse précédentes restent à l'écran au-dessus de la précision
        # (sans leurs vidéos). Cela ne change rien à ce qui est envoyé à l'IA, qui ne reçoit que le dernier échange.
        st.session_state.messages_hub = [m for m in _messages_precedents if m.get("type") != "video"]

    st.session_state.messages_hub.append({
        "role": "user",
        "type": "text",
        "content": f"<span style='color: white;'>{question_affichee}</span>",
    })
    
    # --- SPINNER NATIF STREAMLIT (ZÉRO DOUBLE BARRE / ZÉRO GLITCH) ---
    with st.spinner("⏳ Recherche dans la base documentaire et analyse en cours..."):
        
        mode = st.session_state.active_module
        if ctx_onglet:
            # une relance (ou une nouvelle question saisie dans la zone de précision) reste dans l'onglet de la question d'origine
            mode = ctx_onglet["mode"]
        p_low = prompt.lower()
        # Version sans accents, utilisée par les détections robustes (singulier/pluriel, accents oubliés)
        p_norm = normaliser(prompt)
        
        niveau_actuel_form = st.session_state.get("niveau_actif_form", "Collège (DNB)")
        if ctx_onglet:
            niveau_actuel_form = ctx_onglet["niveau"]
        origine_reponse = "ia"
        bloc_echange_precedent = ""
        consigne_relance_finale = ""

        onglets_noms = {
            "ipack": "l'onglet Assistance Technique iPackEPS (Gestion du CCF)",
            "examens": "l'onglet Réglementation Examens & Santorin (Copies Numérisées)",
            "textes": "l'onglet Sécurité & Responsabilité Juridique (Textes Officiels)",
        }
        contexte_choisi_nom = onglets_noms.get(mode, "un onglet de l'application")

        # Valeurs par défaut : ces variables sont utilisées dans la mise en forme finale,
        # y compris dans le cas "hors-sujet" où elles ne sont pas recalculées plus bas.
        est_college = False
        # ✅ CORRECTION : sans cette valeur par défaut, une question hors-sujet posée dans l'onglet Textes faisait planter le hub
        sources_consultees = []
        fiches_diag = []   # (titre de la fiche, score) : passages transmis à l'IA, affichés en mode admin uniquement
        erreur_rag = ""
        reponse_en_dur_ecartee = ""
        est_dnb = False
        est_sss = False
        est_shn = False
        texte_brut = ""
        badge, color_card = "INFORMATION", "general-card"

        # ==================================================================
        # 1. DÉFINITION DES MOTS-CLÉS PÉDAGOGIQUES (DÉCLENCHEURS RAG)
        # ==================================================================
        mots_cles_intention_peda = [
            "cycle", "séance", "seance", "situation", "apprentissage", "échauffement", "echauffement",
            "barème", "bareme", "grille", "afl", "afc", "compétence", "competence",
            "socle", "programme", "programmes", "didactique", "pédagogie", "pedagogie",
            "comment enseigner", "comment évaluer", "comment evaluer", "comment noter sur le terrain",
            "quel exercice", "quels exercices", "critère", "critères", "repère", "repères"
        ]

        # ==================================================================
        # 2. DISJONCTEUR DE SÉCURITÉ : DÉTECTION DES SUJETS HORS-SUJET
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
                "appn", "tasa", "sauvetage", 
                "sécurité", "securite", "matériel", "materiel", "epi", "fauchon", 
                "responsabilité", "responsabilite", "circulaire", "officiel", 
                "textes", "loi", "décret", "arrete", "arrêté", "recteur", "rectrice", 
                "ia-ipr", "ipr", "sanction", "exclusion", "accident", "unss", 
                "fonction publique", "direction", "chef d'établissement",
                "psc1", "psc", "secourisme", "secours", "cdsg", "jdc", "cadets"
            ] + mots_cles_intention_peda + [
                # ✅ AJOUT : vocabulaire de la réglementation / sécurité EPS (évite de bloquer des questions légitimes)
                "élève", "élèves", "professeur", "professeurs", "enseignant", "enseignants", "stagiaire", "titulaire",
                "contractuel", "remplaçant", "remplacement", "absence", "congé", "inspection", "inspecteur", "carrière",
                "gymnase", "vestiaire", "vestiaires", "piscine", "natation", "nager", "baignade", "bassin", "plongée",
                "voile", "escalade", "ski", "vtt", "vélo", "randonnée", "montagne", "course d'orientation", "orientation",
                "canoë", "kayak", "équitation", "boxe", "judo", "combat", "tir à l'arc", "trampoline", "gymnastique",
                "acrosport", "danse", "athlétisme", "rugby", "football", "basket", "volley", "badminton", "tennis", "golf",
                "sortie", "sorties", "voyage", "séjour", "encadrement", "encadrer", "surveillance", "surveiller",
                "assurance", "assurer", "agrément", "autorisation", "parents", "famille", "intervenant", "intervenants",
                "bénévole", "vacataire", "blessure", "blessé", "blessée", "défibrillateur", "dae", "vol", "perte",
                "dégradation", "règlement", "réglementation", "réglementaire", "juridique", "tribunal", "faute", "pénal",
                "obligation", "obligations", "décharge", "association sportive", "établissement", "chef", "cpe",
                "inapte", "inaptitude", "dispense", "dispensé", "certificat", "médical", "handicap", "ulis", "inclusion",
                "harcèlement", "laïcité", "tenue", "religieux", "discipline", "exclu", "exclure", "évaluation", "notation",
                "programme", "programmes", "socle", "enseignement", "option", "spécialité", "installation", "équipement",
                "entretien", "vérification", "agrès", "savoir nager", "savoir rouler", "stage", "formation", "concours",
                "capeps", "agrégation", "médecin", "infirmier", "infirmière", "premiers secours", "protocole",
            ]
            
            # ✅ CORRECTION : les mots courts (ps, ms, cp, cap, bac, loi, eps...) sont cherchés
            # en mots entiers, pour qu'ils ne matchent plus à l'intérieur d'autres mots ("temps", "capacité"...)
            # Comparaison sans accents : "eleve" ou "élève" donnent le même résultat
            est_totalement_hors_sujet = not contient_mot_cle(p_norm, [normaliser(m) for m in mots_cles_eps_admin])

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
            badge, color_card = "⚖️️ HORS-SUJET", "securite-card"
            origine_reponse = "hors"
        else:
            texte_brut = ""
            extraits_doc = ""
            sources_consultees = []
            badge, color_card = "INFORMATION", "general-card"

            verites_terrain_pierre = ""
            try:
                for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
                    if os.path.exists(fp):
                        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                            verites_terrain_pierre += f"\n--- REGLES DE PIERRE ---\n" + f.read() + "\n"
            except Exception:
                pass

            # ✅ CORRECTION : mots courts (6e, 5e, cap, bac, lp, lgt...) cherchés en mots entiers
            est_college = contient_mot_cle(p_low, ["6e", "5e", "4e", "3e", "collège", "college", "dnb", "brevet", "lsu"])
            est_clairement_lycee = contient_mot_cle(p_low, ["santorin", "ccf", "terminale", "cyclades", "epxcs", "bac", "cap", "lycée", "lycee", "lgt", "lp"])
            
            est_premier_degre = contient_mot_cle(p_low, [
                "tps", "ps", "ms", "gs", "cp", "ce1", "ce2", "cm1", "cm2", 
                "maternelle", "élémentaire", "elementaire", "atsem", "directeur d'école", "ien"
            ])

            if est_college and not est_clairement_lycee:
                contexte_actif = "college"
            else:
                contexte_actif = mode

            # ==================================================================
            # 3. LISTE DES DISJONCTEURS PYTHON
            # ==================================================================
            # ✅ CORRECTION 1 : Le disjoncteur Pronote/Ecole Directe est élargi aux mots "extraire" et "groupes"
            est_import_pronote = (mode == "ipack" and any(w in p_low for w in ["pronote", "ecole directe", "ecoledirecte", "ecole direct"]) and any(w in p_low for w in ["import", "importer", "extraire", "extraction", "élève", "eleve", "classe", "classes", "groupe", "groupes"]))
            # ✅ CORRECTION : la règle se déclenchait dès que la question contenait le mot « note » (ex. « note minimum de 16/20 »),
            # y compris dans l'onglet Textes. Il faut maintenant une vraie intention de saisie, dans l'onglet iPackEPS.
            est_saisir_notes = (
                mode == "ipack" and not est_import_pronote
                and contient(p_norm, [r"\bsaisi", r"\brentrer\b", r"\bentrer\b", r"\bmettre\b", r"carnet", r"coefficient", r"ponderation", r"\bnoter\b"])
                and contient(p_norm, [r"\bnotes?\b"])
                and not any(w in p_low for w in ["santorin", "cyclades", "protocole", "sequence", "séquence", "référentiel", "referentiel", "bloqu", "unss", "podium", "championnat", "texte officiel"])
            )
            est_connexion = (any(w in p_low for w in ["connecter", "connexion", "accéder", "acceder"]) and any(w in p_low for w in ["cyclades", "santorin", "imag'in", "imagin", "arena", "plateforme"]))
            # ✅ CORRECTION : « je me connecte à Santorin mais je ne vois aucun lot » recevait la fiche « accès par ARENA ».
            # La personne est déjà connectée : son problème (lots, élèves, protocoles absents) part à la recherche documentaire.
            est_connexion = est_connexion and not contient(p_norm, [r"\blots?\b", r"ne vois", r"vois (aucun|pas|rien|plus)", r"\baucune?s?\b", r"n'?apparai", r"apparai(t|ssent) pas"])
            est_date = ((not est_college) and any(phrase in p_low for phrase in ["quel est le calendrier", "quelles sont les dates", "date butoir de", "date de fermeture", "calendrier officiel"]) and any(w in p_low for w in ["saisie", "note", "notes", "fermeture", "santorin", "cyclades", "lot", "lots", "examen", "examens", "bac", "cap", "brevet"]))
            est_dnb = (mode != "textes") and any(w in p_low for w in ["dnb", "brevet", "collège", "college"]) and not any(w in p_low for w in ["bac", "lycée", "lycee", "cap"])
            est_sujet_secours = "sujet" in p_low and any(w in p_low for w in ["secours", "papier", "imprimer"])
            est_cap_3epreuves = (mode == "examens" and "cap" in p_low and any(w in p_low for w in ["3 épreuves", "3 notes", "trois épreuves", "trois notes"]))
            est_tasa = mode == "textes" and "tasa" in p_low
            est_unss = any(w in p_low for w in ["unss", "championnat de france", "championnats de france", "jeune juge", "jeunes juges", "jeune arbitre", "jeunes arbitres", "podium unss"])
            est_deplacer_candidat = (mode != "textes" and any(w in p_low for w in ["déplacer", "deplacer", "déplacement", "deplacement"]) and any(w in p_low for w in ["candidat", "élève", "eleve"]) and "lot" in p_low)
            est_eleve_arrivant = (mode != "textes" and any(w in p_low for w in ["arrive", "arrivant", "arrivée", "en cours d'année", "cours d annee"]) and any(w in p_low for w in ["élève", "eleve", "ccf", "examen", "groupe"]))
            est_apsa_etablissement_vs_nationale = (any(w in p_low for w in ["apsa établissement", "apsa etablissement", "liste nationale"]) and any(w in p_low for w in ["valide", "invalide", "relais", "sauts", "lancers", "statistiques", "cyclades"]))
            est_verrouiller_lot = (mode == "examens" and any(w in p_low for w in ["comment verrouiller", "je veux verrouiller", "pour verrouiller", "verrouiller mon lot", "verrouiller mes lots"]) and not any(w in p_low for w in ["déverrouiller", "deverrouiller", "incohérences", "incoherence", "erreur", "impossible", "candidature"]))
            # ✅ CORRECTION : « ferme » se déclenchait sur « fermeture des serveurs » ; mots entiers désormais, et une demande
            # d'extraction / export des notes n'est pas une demande de déverrouillage.
            est_deverrouiller_lot = (
                mode == "examens"
                and (contient(p_norm, [r"deverrouill", r"cadenas", r"\bferme(e|s|es)?\b", r"modifier (une |la |ma |mes )?notes?", r"\bverrouille(e|s|es)?\b"]))
                and any(w in p_low for w in ["santorin", "lot", "copie"])
                and not contient(p_norm, [r"extrai", r"extraction", r"\bexport", r"telecharg", r"\bcsv\b", r"excel", r"tableur", r"recapitulatif"])
                and not est_verrouiller_lot
            )
            est_dispense_totale = (mode != "textes" and any(w in p_low for w in ["dispensé", "dispense", "inapte", "inaptitude"]) and any(w in p_low for w in ["total", "toute l'année", "toute l'annee", "pour l'année", "pour l'annee", "toutes les épreuves", "toutes les epreuves"]))
            est_exclusion = (mode != "textes" and any(w in p_low for w in ["exclusion", "conseil de discipline", "exclu", "sanction"]) and any(w in p_low for w in ["ccf", "épreuve", "epreuve", "note", "rattrapage"]))
            est_aucun_eleve = (mode == "ipack" and any(w in p_low for w in ["aucun élève", "aucun eleve", "pas d'élève", "pas d'eleve", "liste vide", "aucun candidat"]))
            est_referentiels_rentree = (mode == "ipack" and any(phrase in p_low for phrase in ["configurer les référentiels de rentrée", "déclarer les apsa de rentrée", "dépôt initial des référentiels", "campagne de rentrée"]))
            est_sss = any(w in p_low for w in ["sss", "section sportive", "reconduction", "fermeture sss"])
            est_eppcs = (mode == "ipack" and any(w in p_low for w in ["eppcs", "specialite eps", "spécialité eps"]) and any(w in p_low for w in ["depot", "déposer", "fiche", "fiches", "certificative", "certificatives", "premiere", "première"]))
            est_shn = any(w in p_low for w in ["shn", "sportif de haut niveau", "haut niveau", "ppf", "sportifs de haut niveau"])
            est_creation_groupe = (mode == "ipack" and any(w in p_low for w in ["groupe", "groupes"]) and any(w in p_low for w in ["mélanger", "melanger", "plusieurs classes", "pas à la classe", "correspondent pas", "inter-classe", "interclasse", "barrette", "décloison", "decloison"]) and not any(w in p_low for w in ["eppcs", "sss", "ulis", "section sportive", "association sportive"]))
            est_ressaisie_rentree = (mode == "ipack" and any(w in p_low for w in ["resaisir", "ressaisir", "tout refaire", "effacer", "année dernière", "annee derniere", "recommencer"]) and any(w in p_low for w in ["données", "donnees", "l'an dernier", "an dernier", "tout"]))
            # ✅ AJOUT : même question posée autrement (« la structure est-elle reconduite d'une année sur l'autre ? », « est-ce conservé ? »).
            # Les questions sur la reconduction d'une SSS ou d'un protocole ne sont pas concernées.
            est_ressaisie_rentree = est_ressaisie_rentree or (
                mode == "ipack"
                and contient(p_norm, [r"reconduit", r"d.une annee (sur|a) l.autre", r"chaque (nouvelle )?annee", r"annee suivante", r"\bconserv", r"\bgarde(e|es|s)?\b", r"\bresaisi", r"\bressaisi"])
                and contient(p_norm, [r"structure", r"donnee", r"\bsaisi", r"etablissement", r"\beple\b", r"configuration", r"parametrage", r"\btout\b"])
                and not contient(p_norm, [r"\bsss\b", r"section sportive", r"protocole", r"referentiel", r"\bnotes?\b", r"appn"])
            )
            # ✅ CORRECTION : une question longue ou qui décrit un problème (projet annuel, APSA, bug, message d'erreur)
            # n'est pas une demande générale « comment gérer une SSS » : elle part au RAG pour une réponse précise.
            est_gestion_sss_ou_sport = (mode == "ipack" and any(w in p_low for w in ["sport etude", "sport-etude", "section sportive", "sss"]) and any(w in p_low for w in ["gerer", "gérer", "configurer", "créer", "creer"]) and len(prompt) < 200 and not any(w in p_low for w in ["projet", "bilan", "apsa", "bug", "erreur", "message", "fonctionn", "me dit", "tourne en rond"]))
            est_dossier_peda = any(w in p_low for w in ["dossier peda", "dossier pédagogique", "ou est mon dossier", "où est mon dossier"])
            est_sss_bloque = (mode == "ipack" and any(w in p_low for w in ["sss", "section sportive"]) and any(w in p_low for w in ["droit", "créer", "creer", "autorise", "bloque", "pas"]) and not any(w in p_low for w in ["projet annuel", "projet", "bilan", "apsa"]))
            # ✅ AJOUT : « j'ai créé mes groupes de section mais le Projet Annuel SSS dit qu'il n'y a pas de groupe SSS / pas d'APSA ».
            # Réponse fixe tirée des articles 17 (R2, R9), 31 (R2) et 111 d'ipack.txt : le RAG oubliait la cause principale (type SSS non activé).
            est_sss_projet_sans_groupe = (mode == "ipack" and any(w in p_low for w in ["sss", "section sportive"]) and any(w in p_low for w in ["projet annuel", "projet sss", "projet de section", "bilan sss", "bilan annuel"]) and any(w in p_low for w in ["groupe", "apsa"]) and any(w in p_low for w in ["pas cr", "pas de groupe", "aucun groupe", "aucune apsa", "pas d'apsa", "n'apparaît", "n'apparait", "apparaît pas", "apparait pas", "me dit", "m'indique", "bug", "tourne en rond", "pas fonctionn", "inactif", "inactive", "grisé", "grise"]))
            # ✅ AJOUT : question technique (iPackEPS / Cyclades / Santorin) posée par erreur dans l'onglet Textes.
            # La base « Textes » ne contient pas ces procédures : l'IA répondait quand même, à côté. On renvoie vers le bon onglet.
            _logiciel_cite = any(w in p_low for w in ["ipack", "cyclades", "santorin"])
            _geste_logiciel = any(w in p_low for w in ["bouton", "menu", "grisé", "grise", "cliquer", "clique", "importer", "import ", "exporter", "export ", "générer", "generer", "fichier", "configurer", "paramétrer", "parametrer", "message d'erreur", "bug", "connexion", "connecter"])
            _protocole_technique = ("protocole" in p_low and any(w in p_low for w in ["test du protocole", "test de protocole", "invalide", "rejeté", "rejete", "bloqué", "bloque", "certifiable", "certificative", "déclaré", "declare"]))
            _signal_fort = any(w in p_low for w in ["dossier eps", "dossier certificatif", "mon lot", "mes lots", "cadenas", "emploi du temps ipack"])
            est_mauvais_onglet = (mode == "textes" and (_signal_fort or _protocole_technique or (_logiciel_cite and _geste_logiciel)))
            est_mauvais_onglet_examens = est_mauvais_onglet and any(w in p_low for w in ["santorin", "mon lot", "mes lots", "cadenas", "copie", "saisie des notes", "saisir les notes", "saisir mes notes"])
            est_dates_ccf = (mode in ["ipack", "examens"] and any(w in p_low for w in ["date", "dates", "période", "periode", "calendrier"]) and any(w in p_low for w in ["ccf", "séquence", "sequence", "évaluation", "evaluation", "trimestre"]))
            # ✅ CORRECTION : « où définir les périodes de mes séquences d'apprentissage ? » recevait cette réponse sur les dates
            # de CCF, avec le menu [Séquences] / [Protocoles]. Le manuel (article 16) indique [Dossiers] > [Dossier EPS] > [Périodes] :
            # la question part donc à la recherche documentaire. Idem pour une demande de date LIMITE (fixée par la DEC).
            if est_dates_ccf and (
                (contient(p_norm, [r"periodes?"]) and "apprentissage" in p_norm and not contient(p_norm, [r"\bccf\b"]))
                or contient(p_norm, [r"date limite", r"dates limites", r"jusqu.a quand", r"jusqu.a quelle date", r"avant quelle date", r"dernier delai"])
            ):
                est_dates_ccf = False
            est_equipe_eps = (mode == "ipack" and any(w in p_low for w in ["enseignant", "enseignants", "professeur", "professeurs", "prof", "profs", "équipe", "equipe", "collègue", "collegue"]) and any(w in p_low for w in ["ajouter", "ajout", "manque", "manquant", "pas sur", "absent", "actualiser"]))
            est_doc_synthese = (mode == "ipack" and any(w in p_low for w in ["97%", "97 %", "synthèse", "synthese", "voie générale", "voie generale", "voie pro"]) and any(w in p_low for w in ["attente", "bloqué", "bloque", "dépôt", "depot", "manque", "0 0 1"]))
            # ✅ AJOUT (historique des questions) : 5 questions sur ce document, 1 seule déclenchait la réponse.
            # « en quoi consiste », « où trouver le modèle », « qu'est-ce que le fichier synthèse »... et aussi dans l'onglet Examens.
            est_doc_synthese = est_doc_synthese or (
                mode in ("ipack", "examens")
                and contient(p_norm, [r"synthese"])
                and contient(p_norm, [r"\bdoc\b", r"document", r"fichier", r"dossier", r"modele"])
                and contient(p_norm, [r"voie (general|techno|pro)", r"etablissement", r"ipack", r"referen", r"depot", r"deposer", r"97"])
            )
            # ✅ CORRECTION : détection robuste des élèves inactifs / partis / inexistants.
            # - texte sans accents (p_norm), radicaux et mots entiers (singulier ET pluriel : "eleve" / "eleves")
            # - ajout de "inexistant", "fantôme", "radié", "n'est plus", "sortir", etc.
            # - exclusion des questions de groupe (déjà traitées ailleurs)
            est_eleves_inactifs = (
                mode == "ipack"
                and contient(p_norm, [r"\beleves?\b", r"\bcandidats?\b", r"\bfiches?\b"])
                and contient(p_norm, [
                    r"inexist", r"inactif", r"\bpartis?\b", r"quitt", r"radie",
                    r"fantome", r"en trop", r"n'?est plus", r"plus dans",
                    r"\bsortir\b", r"\bsortis?\b", r"retirer", r"enlever", r"supprim", r"disparai"
                ])
                and not contient(p_norm, [r"groupes?\b"])
            )
            # ✅ CORRECTION : seuls les mots vraiment pédagogiques bloquent le RAG
            # (avant : "cycle", "situation", "programme", "grille"... bloquaient des questions iPackEPS légitimes)
            mots_peda_stricts = [
                "séance", "seance", "échauffement", "echauffement", "didactique", "pédagogie", "pedagogie",
                "comment enseigner", "comment évaluer", "comment evaluer", "quel exercice", "quels exercices",
                "comment noter sur le terrain",
            ]
            est_question_pedagogique = (
                mode != "textes" 
                and any(w in p_low for w in mots_peda_stricts)
                and not any(w in p_low for w in ["groupe", "classe", "import", "pronote", "lot", "santorin", "cyclades", "paramètre", "configurer", "protocole", "dossier eps", "apsa", "sequence", "séquence", "référentiel", "referentiel", "certificati", "dossier"])
                # ✅ CORRECTION : « comment évaluer un sportif de haut niveau au bac ? » était renvoyé comme question pédagogique.
                # Une question d'examen (bac, CAP, CCF, épreuve, haut niveau, dispense) n'est pas de la pédagogie de terrain.
                and not est_shn
                and not contient(p_norm, [r"\bbac\b", r"baccalaur", r"\bcap\b", r"\bccf\b", r"\bexamens?\b", r"\bepreuves?\b", r"dispens", r"inapt"])
            )

            # ✅ INTERRUPTEURS MIS EN VEILLE (revue du 6 octobre 2026, validée par T. Armant).
            # Ces réponses toutes faites étaient vagues ou donnaient un chemin de menu différent du tutoriel officiel,
            # alors que la base documentaire contient désormais la procédure exacte. Elles passaient DEVANT la base :
            # le collègue recevait la moins bonne des deux réponses. On laisse donc la base répondre.
            # Pour en réactiver un : retirer simplement sa ligne ci-dessous (le texte de la réponse est conservé plus bas).
            est_import_pronote = False        # « paramètres d'importation » -> la base donne [Dossier EPS] > [Élèves] > [Importer un fichier Pronote]
            est_verrouiller_lot = False       # bouton « en bas » -> le tutoriel dit [Verrouiller] en haut à droite
            est_dates_ccf = False             # « [Séquences] ou [Protocoles] selon l'affichage » -> chemin exact dans la base
            est_creation_groupe = False       # « [Classes / Groupes] » -> [Dossier EPS] > [Groupes] puis [Élèves]
            est_gestion_sss_ou_sport = False  # « onglet [Mes Élèves] » -> [Dossier EPS] > [Élèves] ; dossier Sports-Études à part
            est_aucun_eleve = False           # actualisation dans [Élèves] -> en réalité [Classes] > importation des élèves
            est_eleves_inactifs = False       # même chemin que ci-dessus
            est_referentiels_rentree = False  # « cochez les champs d'apprentissage » -> procédure exacte dans la base
            est_equipe_eps = False            # ne parlait pas de l'intervenant extérieur (cas du vacataire)

            est_cas_direct = (
                (mode != "textes") 
                and (
                    est_connexion or est_date or est_sujet_secours or est_cap_3epreuves or est_deplacer_candidat
                    or est_eleve_arrivant or est_apsa_etablissement_vs_nationale or est_verrouiller_lot
                    or est_deverrouiller_lot or est_dispense_totale or est_saisir_notes or est_exclusion
                    or est_aucun_eleve or est_referentiels_rentree or est_import_pronote or est_sss_bloque or est_sss_projet_sans_groupe
                    or est_gestion_sss_ou_sport or est_dossier_peda or est_creation_groupe or est_ressaisie_rentree
                    or est_dates_ccf or est_equipe_eps or est_doc_synthese or est_eleves_inactifs
                    or est_question_pedagogique
                )
            ) or est_tasa or est_unss or est_mauvais_onglet

            # ✅ AJOUT : question trop courte (3 mots ou moins) sans réponse directe connue.
            # Avant, ce filtre était confié à l'IA : un appel complet (consignes + 10 passages) pour répondre « reformulez ».
            # Il est maintenant fait ici, sans appel à l'IA, donc sans coût.
            est_question_trop_courte = (not est_cas_direct) and len(prompt.split()) <= 3
            if est_question_trop_courte:
                est_cas_direct = True

            # 💬 RELANCE après une réponse EN DUR : resservir la même réponse fixe ne servirait à rien.
            # On coupe donc les disjoncteurs pour ce tour et on laisse l'IA compléter, avec la réponse précédente sous les yeux.
            # (Après « pouvez-vous préciser ? » ou « je ne dispose pas de l'information », rien n'est coupé et rien n'est rappelé à l'IA.)
            # ✅ CORRECTION : après une réponse de l'IA, les réponses en dur restent ACTIVES. Si la précision en déclenche une
            # (ex. « ...ou je dois tout resaisir ? »), c'est une information nouvelle, fiable et gratuite : on la sert.
            if relance_ctx and relance_ctx.get("origine") == "direct":
                for _nom_flag in [k for k in list(globals()) if k.startswith("est_")]:
                    if _nom_flag not in ("est_college", "est_dnb", "est_premier_degre", "est_clairement_lycee", "est_sss", "est_shn", "est_totalement_hors_sujet", "est_mauvais_onglet", "est_mauvais_onglet_examens"):
                        globals()[_nom_flag] = False
                est_cas_direct = est_mauvais_onglet
            if relance_ctx and relance_ctx.get("origine") in ("direct", "ia") and not est_cas_direct:
                bloc_echange_precedent = (
                    "RÉPONSE DÉJÀ DONNÉE À CET UTILISATEUR JUSTE AVANT (elle ne l'a pas débloqué) :\n"
                    + relance_ctx["reponse"]
                    + "\n"
                )
                # Placée tout à la fin des consignes : c'est là que l'IA en tient le mieux compte.
                consigne_relance_finale = (
                    "\n3. RÈGLE DE RELANCE (PRIORITAIRE) : l'utilisateur a déjà reçu la « RÉPONSE DÉJÀ DONNÉE » ci-dessus et elle ne l'a pas débloqué. "
                    "INTERDICTION de la répéter ou de la reformuler. Réponds uniquement à la précision qu'il vient d'apporter, "
                    "à partir du CONTEXTE DOCUMENTAIRE OFFICIEL LOCAL. "
                    "Si le contexte ne contient aucune information nouvelle par rapport à la réponse déjà donnée, réponds STRICTEMENT : "
                    "\"Je n'ai pas d'information plus précise dans ma base sur ce point. Plutôt que de répéter la réponse précédente, "
                    "je vous invite à contacter l'assistance en indiquant ce que vous avez déjà essayé et le message exact affiché.\"\n"
                )

            if est_question_trop_courte:
                origine_reponse = "courte"
            elif est_mauvais_onglet:
                origine_reponse = "onglet"
            elif est_cas_direct:
                origine_reponse = "direct"

            # ==================================================================
            # 4. APPEL AU RAG (BASE DOCUMENTAIRE) POUR L'IA
            # ==================================================================
            def _recherche_documentaire():
                """Cherche les passages utiles dans les bases pour la question en cours.
                Renvoie (extraits pour l'IA, sources affichables, fiches pour le diagnostic admin, message d'erreur)."""
                _extraits, _sources, _diag, _erreur, _vus = [], [], [], "", set()

                # ✅ AJOUT : beaucoup de fiches de la FAQ donnent une réponse PAR EXAMEN (« Réponse Lycée GT Bac »,
                # « Réponse Lycée Pro Bac / Lycée Pro CAP », « Réponse Lycée Pro CAP », « Réponse Collège DNB »), chacune dans
                # son propre passage. L'IA piochait parfois la réponse d'un autre examen (ex. CAP : 2 épreuves, servie pour
                # une question sur le bac pro : 3 épreuves). On écarte donc ici les réponses qui visent un autre examen que
                # celui de la question (ou, à défaut, que celui du public sélectionné).
                _cibles = set()
                if re.search(r"\bbac(calaureat)?s? ?pro\b|baccalaureat professionnel|\bbacs? professionnels?\b", p_norm):
                    _cibles.add("pro")
                if re.search(r"\bcap\b", p_norm):
                    _cibles.add("cap")
                if re.search(r"\b(dnb|brevet|college|collegiens?|sixiemes?|cinquiemes?|quatriemes?|troisiemes?|6e|5e|4e|3e)\b", p_norm) or (est_college and not est_clairement_lycee):
                    _cibles.add("dnb")
                if re.search(r"bac(calaureat)? ?(general|techno|gt)\b|\blgt\b|voie (generale|techno)", p_norm):
                    _cibles.add("gt")
                if not _cibles:
                    _cibles = {"Collège (DNB)": {"dnb"}, "Lycée Général & Techno": {"gt"}, "Lycée Pro / CAP": {"pro", "cap"}}.get(niveau_actuel_form, set())

                def _autre_examen(txt):
                    """Vrai si le passage ne contient que des réponses destinées à d'autres examens que celui visé."""
                    if not _cibles:
                        return False
                    _etiquettes = re.findall(r"R[ée]ponse\s+((?:Lyc[ée]e|Coll[èe]ge)[^*:\n]*)", txt)
                    if not _etiquettes:
                        return False
                    _vises = set()
                    for _e in _etiquettes:
                        _e = normaliser(_e)
                        if "gt" in _e:
                            _vises.add("gt")
                        if "pro bac" in _e:
                            _vises.add("pro")
                        if "cap" in _e:
                            _vises.add("cap")
                        if "college" in _e or "dnb" in _e:
                            _vises.add("dnb")
                    return bool(_vises) and not (_vises & _cibles)

                # ✅ AJOUT : au collège il n'y a ni Cyclades ni Santorin. Sans ce garde-fou, une question de collège sur le
                # dossier EPS recevait des fiches d'export vers Cyclades et l'IA les recopiait.
                _college_hors_examen = niveau_actuel_form == "Collège (DNB)" and not re.search(
                    r"cyclades|santorin|imagin|examen|ccf|certificat|protocole|referentiel|dnb|brevet", p_norm)

                def _ajouter_par_mots(nom_base, etiquette="", maximum=3):
                    for _txt in chercher_par_mots(recherche_mots, nom_base, prompt, maximum):
                        _cle = re.sub(r"\s+", " ", _txt)[:300]
                        if _cle in _vus or _autre_examen(_txt):
                            continue
                        if _college_hors_examen and re.search(r"cyclades|santorin|imag.?in", normaliser(_txt[:500])):
                            continue
                        _vus.add(_cle)
                        _extraits.append((etiquette + " " if etiquette else "") + _txt)
                        _diag.append(("[mots] " + (etiquette + " " if etiquette else "") + _txt.strip().split("\n")[0][:100], None))

                def _ajouter(retriever, etiquette="", avec_sources=False, avec_diag=False, maximum=None):
                    if not retriever:
                        return
                    _nodes = retriever.retrieve(prompt)
                    if maximum:
                        _nodes = _nodes[:maximum]
                    for n in _nodes:
                        _txt = n.node.text or ""
                        _cle = re.sub(r"\s+", " ", _txt)[:300]
                        if _cle in _vus:
                            continue  # même passage présent dans deux bases : transmis une seule fois
                        if _autre_examen(_txt):
                            continue  # réponse rédigée pour un autre examen que celui de la question
                        if _college_hors_examen and re.search(r"cyclades|santorin|imag.?in", normaliser(_txt[:500])):
                            continue  # question de collège sans rapport avec les examens : pas de fiche Cyclades / Santorin
                        _vus.add(_cle)
                        _extraits.append((etiquette + " " if etiquette else "") + _txt)
                        if avec_sources:
                            _sources.append((libelle_source(n), getattr(n, "score", None)))
                        if avec_diag:
                            _diag.append(((etiquette + " " if etiquette else "") + _txt.strip().split("\n")[0][:110], getattr(n, "score", None)))

                try:
                    if niveau_actuel_form == "1er degré":
                        _ajouter(retriever_textes, "[Référentiel Textes Officiels 1er Degré]", avec_sources=True)
                        _ajouter(retriever_peda, "[Référentiel Pédagogique 1er Degré]", avec_sources=True)
                    elif mode == "textes":
                        _ajouter(retriever_textes, "[Textes Officiels & Juridiques / Partenariats]", avec_sources=True)
                        if any(w in p_low for w in mots_cles_intention_peda):
                            _ajouter(retriever_peda, "[Référentiel Pédagogique]", avec_sources=True)
                    elif mode == "examens":
                        _ajouter_par_mots("santorin", maximum=3)
                        _ajouter_par_mots("ipack", "[Base iPackEPS]", maximum=2)
                        _ajouter(retriever_santorin, avec_diag=True, maximum=8)
                        # ✅ AJOUT : beaucoup de fiches Santorin / Cyclades sont rangées dans ipack.txt (livret Santorin, FAQ examens,
                        # cas d'élèves : arrivée en cours d'année, 2 notes sur 3, haut niveau...). Depuis l'onglet Examens elles étaient
                        # introuvables : l'IA inventait alors des menus ou restait dans le vague. On va aussi les chercher, à parts égales.
                        _ajouter(retriever_ipack, "[Base iPackEPS]", avec_diag=True, maximum=8)
                    elif mode == "ipack":
                        _ajouter_par_mots("ipack", maximum=3)
                        _ajouter(retriever_ipack, avec_diag=True)
                        if not _college_hors_examen:
                            _ajouter_par_mots("santorin", "[Base Examens & Santorin]", maximum=2)
                            _ajouter(retriever_santorin, "[Base Examens & Santorin]", avec_diag=True, maximum=4)
                    else:
                        _ajouter(retriever_peda, "[Référentiel Pédagogique & Programmes]")
                except Exception as e_rag:
                    # ✅ CORRECTION : l'erreur était avalée en silence ; l'IA recevait alors un contexte vide et répondait
                    # « je ne dispose pas de la procédure ». Elle est maintenant notée (visible en mode admin et dans les journaux).
                    _erreur = str(e_rag)
                    print(f"Erreur de recherche documentaire : {_erreur}")
                return ("".join(e + "\n\n" for e in _extraits), _sources, _diag, _erreur)

            if openai_api_key and not est_cas_direct:
                extraits_doc, sources_consultees, fiches_diag, erreur_rag = _recherche_documentaire()

            besoin_ia = False  # passe à True si aucune réponse en dur ne convient : c'est alors l'IA qui répond

            # ==================================================================
            # 5. TEXTES BRUTS POUR LES DISJONCTEURS (CAS DIRECTS)
            # ==================================================================
            if est_question_trop_courte:
                texte_brut = """<h3>✍️ POUVEZ-VOUS PRÉCISER VOTRE QUESTION ?</h3>
<p>Votre demande est trop courte pour que je retrouve la bonne fiche. Pour une réponse précise du premier coup, décrivez en une ou deux phrases :</p>
<ul>
  <li><strong>ce que vous cherchez à faire</strong> (par exemple : créer un groupe, saisir des notes, exporter vers Cyclades) ;</li>
  <li><strong>ce que vous avez déjà fait</strong> et à quel endroit vous êtes bloqué ;</li>
  <li><strong>le message exact affiché</strong> à l'écran, s'il y en a un.</li>
</ul>
<p><strong>Exemple :</strong> « J'ai créé mes groupes de section sportive, mais le projet annuel SSS m'indique qu'il n'y a aucun groupe de type SSS. »</p>"""
                badge, color_card = "INFORMATION", "general-card"

            elif est_mauvais_onglet and not (est_tasa or est_unss):
                if est_mauvais_onglet_examens:
                    onglet_conseille = "Réglementation Examens & Santorin"
                    objet_onglet = "la saisie des notes, les lots et les copies dans Santorin"
                else:
                    onglet_conseille = "Assistance Technique iPackEPS"
                    objet_onglet = "la configuration d'iPackEPS (groupes, APSA, protocoles, export vers Cyclades)"
                texte_brut = f"""<h3>🔀 CETTE QUESTION RELÈVE D'UN AUTRE ONGLET</h3>
<p><strong>Pourquoi je ne réponds pas ici :</strong> vous êtes dans l'onglet « Sécurité & Responsabilité Juridique (Textes Officiels) », qui ne consulte que les textes réglementaires. Votre question porte sur {objet_onglet} : les procédures correspondantes ne sont pas dans cette base, et une réponse donnée ici risquerait d'être fausse.</p>
<p><strong>Que faire :</strong> revenez à l'étape 1, choisissez l'onglet <strong>« {onglet_conseille} »</strong>, gardez le même public, et reposez la même question.</p>"""
                badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

            elif est_import_pronote:
                texte_brut = """<h3>📥 IMPORTATION DES GROUPES ET ÉLÈVES DEPUIS PRONOTE / ECOLE DIRECTE</h3>
<p><strong>Principe :</strong> L'importation des données d'élèves depuis votre logiciel de vie scolaire permet d'initialiser vos classes rapidement dans iPackEPS.</p>
<p><strong>Procédure :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Rendez-vous dans les paramètres d'importation de votre établissement sur iPackEPS.</li>
  <li><strong>[Étape 2]</strong> Chargez le fichier d'export généré par votre logiciel de vie scolaire (Pronote, École Directe).</li>
  <li><strong>[Étape 3]</strong> Validez l'importation pour peupler vos listes d'élèves.</li>
</ol>
📺 Tutoriel associé : import_eleves_pronote.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_connexion:
                texte_brut = """<h3>🌐 ACCÈS AUX PLATEFORMES PROFESSIONNELLES (CYCLADES, SANTORIN, IMAG'IN)</h3>
<p><strong>Règle d'or absolue :</strong> Aucun enseignant ou personnel ne se connecte par un site web académique public (type site grand public de l'académie).</p>
<p><strong>Portail d'accès unique :</strong> L'accès à TOUTES les applications professionnelles et d'examen se fait IMPÉRATIVEMENT et exclusivement par le portail professionnel institutionnel <strong>ARENA</strong> (ou l'intranet académique) à l'aide de vos identifiants professionnels (e-mail académique + mot de passe).</p>"""
                badge, color_card = "🌐 ACCÈS INSTITUTIONNEL", ("santorin-card" if mode == "examens" else "general-card")

            elif est_saisir_notes:
                texte_brut = """<h3>⚠️ RÈGLE FONDAMENTALE : iPACKEPS N'EST PAS UN CARNET DE NOTES</h3>
<p><strong>Règle absolue :</strong> iPackEPS n'est en aucun cas un carnet de notes ou un logiciel de notation. Il est <strong>strictement impossible</strong> d'y saisir des notes.</p>
<p><strong>Outil dédié :</strong> Utilisez exclusivement Pronote, ÉcoleDirecte ou le LSU selon votre niveau.</p>"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_date:
                texte_brut = """<h3>📅 CALENDRIER OFFICIEL DES EXAMENS & SAISIE DES NOTES</h3>
<p><strong>Principe réglementaire :</strong> Les dates butoirs de saisie des notes et de clôture des serveurs (Santorin / Cyclades) sont fixées annuellement par le calendrier officiel publié au Bulletin Officiel (BO) et précisées par la circulaire DEC de votre académie.</p>"""
                badge, color_card = "📅 CALENDRIER OFFICIEL", ("santorin-card" if mode == "examens" else "general-card")

            elif est_tasa:
                # ✅ CORRECTION : le "<" est remplacé par "&lt;" pour ne pas être interprété comme une balise HTML
                texte_brut = """<h3>🏊 CADRE RÉGLEMENTAIRE - TEST D'APTITUDE AU SAUVETAGE AQUATIQUE (TASA)</h3>
<p><strong>Obligation de qualification :</strong> Obligatoire pour tout enseignant d'EPS dès sa nomination.</p>
<p><strong>Protocole technique :</strong> 100m en continu &lt; 3 min 45 s avec parcours spécifique et recherche de mannequin.</p>"""
                badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

            elif est_sujet_secours:
                texte_brut = """<h3>⚠️ PAS DE SUJET DE SECOURS EN EPS</h3>
<p><strong>NON :</strong> il n'existe pas de sujet de secours en EPS. Cela figurait dans d'anciens textes, ce n'est plus le cas. Il n'y a pas non plus de sujet écrit ou papier : l'évaluation est pratique.</p>"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_cap_3epreuves:
                texte_brut = """<h3>⚠️ CAP : UN ENSEMBLE CERTIFICATIF À 2 ÉPREUVES, PAS 3</h3>
<p><strong>NON :</strong> en CAP, le CCF repose sur <strong>2 épreuves</strong> relevant de 2 champs d'apprentissage différents. Réglementairement, il n'est pas possible d'affecter des candidats de CAP sur un ensemble certificatif à 3 épreuves.</p>
<p><strong>Pratique à ne pas suivre :</strong> inscrire les candidats sur 3 épreuves pour garder les 2 meilleures notes n'est pas autorisé.</p>"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_eleve_arrivant:
                texte_brut = """<h3>📋 ÉLÈVE ARRIVANT EN COURS D'ANNÉE (EXAMEN)</h3>
<p><strong>Le point à ne pas manquer :</strong> si l'élève arrive <strong>après</strong> l'association des candidats aux protocoles, il n'a pas de protocole et n'apparaît dans aucun lot. Il faut repasser par Cyclades, puis redistribuer.</p>
<ol>
  <li><strong>[Étape 1]</strong> Dans <strong>Cyclades</strong>, lui affecter un protocole.</li>
  <li><strong>[Étape 2]</strong> Dans <strong>Santorin</strong>, procéder à une nouvelle distribution automatique des lots : l'élève apparaît alors dans le lot de son enseignant.</li>
</ol>"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_apsa_etablissement_vs_nationale:
                texte_brut = """<h3>⚠️ ERREUR DE SAISIE : APSA ÉTABLISSEMENT VS LISTE NATIONALE (BAC GT)</h3>
<p><strong>Le problème :</strong> Déclarer une activité en "APSA établissement" au lieu de l'activité de la "liste nationale" bloque la validation du protocole par iPackEPS et fausse les statistiques académiques sur Cyclades.</p>
<p><strong>Procédure de résolution exacte :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Retournez dans le module <strong>[Dossiers] > [Dossier EPS] > [APSA]</strong>.</li>
  <li><strong>[Étape 2]</strong> Sélectionnez dans le tableau de gauche l'activité de la liste nationale correspondante (ex: <em>[Courses]</em>).</li>
  <li><strong>[Étape 3]</strong> Déclarez-la certificative en Lycée pour remplacer l'APSA établissement erronée.</li>
</ol>"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_verrouiller_lot:
                texte_brut = """<h3>🔒 VERROUILLAGE D'UN LOT DE CORRECTION SUR SANTORIN</h3>
<p><strong>Principe :</strong> Une fois la saisie de toutes les notes et des statuts terminée, vous devez verrouiller votre lot pour figer les données avant transmission.</p>
<p><strong>Procédure :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Depuis votre espace de correction sur Santorin, accédez au lot concerné.</li>
  <li><strong>[Étape 2]</strong> Revérifiez que toutes vos notes et statuts d'absence sont correctement saisis.</li>
  <li><strong>[Étape 3]</strong> Validez l'action de clôture/verrouillage du lot en bas de l'interface.</li>
</ol>
📺 Tutoriel associé : Verrouiller_lot_santorin.mp4"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_deverrouiller_lot:
                texte_brut = """<h3>🔒 CADENAS ET DÉVERROUILLAGE DE LOT SUR SANTORIN</h3>
<p><strong>Règle d'or absolue :</strong> L'enseignant correcteur n'a AUCUN droit ni habilitation pour déverrouiller lui-même un lot de copies numériques fermé sur Santorin.</p>
<p><strong>Procédure de déverrouillage (Direction) :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Signalez l'erreur à votre Chef d'établissement ou au secrétariat d'examen.</li>
  <li><strong>[Étape 2]</strong> La direction se connecte à sa console <strong>Santorin-Direction</strong> (Menu "Liste des lots").</li>
  <li><strong>[Étape 3]</strong> Elle clique directement sur le cadenas pour le basculer de "fermé" à "ouvert".</li>
</ol>
<p><em>Ne contactez pas la DEC pour cela : le déverrouillage fait partie des prérogatives du chef d'établissement.</em></p>
📺 Tutoriel associé : Deverrouiller_lots_santorin.mp4"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_dispense_totale:
                texte_brut = """<h3>🏥 ÉLÈVE INAPTE SUR TOUTE LA PÉRIODE DE CERTIFICATION : QUE SAISIR ?</h3>
<p><strong>Dans Santorin :</strong> sur la fiche de l'élève, choisissez le statut <strong>« Dispensé » (DI)</strong> pour <strong>chacune des APSA</strong> du protocole (DI + DI + DI en bac, DI + DI en CAP), puis écrivez dans le champ <strong>Appréciations</strong> la mention « inapte à l'année ». Cliquez sur <strong>[Enregistrer]</strong>.</p>
<p><strong>À ne pas confondre :</strong> « Dispensé » (inaptitude médicale justifiée par un certificat) n'est pas « Absent ». Une absence non justifiée donne 0/20 ; une dispense ne donne aucune note.</p>
<p><strong>Certificat médical :</strong> il se déclare et se dépose dans iPackEPS, menu <strong>[Mes Élèves] &gt; [Visualisation]</strong>, onglet <strong>[Inaptitudes]</strong> ; il sera contrôlé par la commission académique.</p>
<p><strong>Aucune note n'est saisie dans iPackEPS :</strong> les notes et les statuts d'examen se saisissent uniquement dans Santorin.</p>"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_exclusion:
                texte_brut = """<h3>⚠️ ÉLÈVE EXCLU DE L'ÉTABLISSEMENT PENDANT LA PÉRIODE D'ÉVALUATION</h3>
<p>Un candidat exclu de l'établissement, qui n'a pas pu se présenter à l'épreuve pour cette raison, est <strong>dispensé</strong> de l'épreuve : son exclusion pendant la période d'évaluation constitue un cas de force majeure. On ne lui met pas zéro.</p>"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_aucun_eleve:
                texte_brut = """<h3>⚠️ PROBLÈMES D'IMPORT SIÈCLE / ARENA À LA RENTRÉE</h3>
<p><strong>Origine du blocage :</strong> Le message "Aucun élève dans cet établissement" provient généralement d'un décalage de synchronisation entre la base administrative (SIÈCLE) et le portail ARENA.</p>
<p><strong>Procédure de résolution :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Assurez-vous auprès du secrétariat que la bascule administrative de rentrée a bien été validée au niveau académique.</li>
  <li><strong>[Étape 2]</strong> Rendez-vous dans <strong>[Dossiers] > [Dossier EPS] > [Élèves]</strong>.</li>
  <li><strong>[Étape 3]</strong> Cliquez sur le bouton pour lancer une actualisation manuelle de l'importation.</li>
</ol>
📺 Tutoriel associé : Import_automatique_eleves.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_referentiels_rentree:
                texte_brut = """<h3>📋 CONFIGURATION DES RÉFÉRENTIELS ET APSA CERTIFICATIVES (RENTRÉE)</h3>
<p><strong>Impératif de septembre :</strong> Dès la rentrée, vous devez configurer les APSA certificatives de vos classes de lycée.</p>
<p><strong>Procédure iPackEPS :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Accédez au menu <strong>[Dossiers] > [Dossier EPS] > [APSA]</strong>.</li>
  <li><strong>[Étape 2]</strong> Cochez les champs d'apprentissage correspondant à votre établissement.</li>
  <li><strong>[Étape 3]</strong> Cochez les épreuves retenues pour vos cycles de certification annuels.</li>
</ol>
📺 Tutoriel associé : Depot_referentiels_iPackEPS.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_deplacer_candidat:
                texte_brut = """<h3>📋 DÉPLACER UN CANDIDAT D'UN LOT À UN AUTRE DANS SANTORIN</h3>
<p><strong>Qui :</strong> le chef d'établissement, ou l'enseignant référent Santorin de l'établissement. Un enseignant qui n'est pas référent ne peut pas le faire lui-même.</p>
<p><strong>Chemin :</strong> <strong>[Distribution]</strong> > <strong>[Lots]</strong> > <strong>[Candidats]</strong> > <strong>[Déplacer vers un lot existant]</strong>.</p>
📺 Tutoriel associé : Deplacer_eleves_lots_santorin.mp4"""
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

            elif est_sss_projet_sans_groupe:
                texte_brut = """<h3>🧩 PROJET ANNUEL SSS : « AUCUN GROUPE DE TYPE SSS » OU « AUCUNE APSA ASSOCIÉE »</h3>
<p><strong>Ce n'est pas un bug :</strong> les rubriques [Projets Annuels SSS] et [Bilan SSS] ne s'activent que si iPackEPS trouve au moins un groupe dont le <strong>type est SSS</strong>, avec <strong>une APSA associée</strong>. Un groupe créé avec le type EPS ne compte pas : inutile d'essayer cette voie.</p>
<p><strong>Vérifications à faire dans l'ordre :</strong></p>
<ol>
  <li><strong>[Étape 1] Le type SSS vous est-il proposé ?</strong> Dans <strong>[Dossiers] > [Dossier EPS] > [Groupes]</strong>, ouvrez votre groupe de section et regardez son type. Si le type [SSS] n'est pas proposé ou est refusé, la cause est là : ce type est bloqué par défaut tant que le recteur n'a pas validé l'ouverture de la section et que le responsable iPackEPS de l'académie n'a pas activé votre établissement (liste mise à jour chaque année). Faites alors un simple signalement par mail à votre responsable iPackEPS ou à votre IPR pour que l'établissement soit activé.</li>
  <li><strong>[Étape 2] Une seule APSA par groupe SSS.</strong> iPackEPS n'accepte qu'une APSA par groupe SSS. Si votre section travaille plusieurs activités, créez manuellement une APSA portant le nom de l'ensemble (par exemple « Football-Musculation ») dans <strong>[Dossiers] > [Dossier EPS] > [APSA]</strong>, puis associez-la au groupe SSS.</li>
  <li><strong>[Étape 3] La bonne année scolaire.</strong> Les groupes ne sont pas reconduits d'une année sur l'autre : ils doivent être reconfigurés à chaque rentrée, puis les élèves répartis dedans (la liste des APSA, elle, est conservée). Vérifiez sur le tableau de bord que vous êtes bien sur l'année en cours.</li>
  <li><strong>[Étape 4] Terminer le Dossier EPS avant le projet.</strong> Le projet de section reprend les élèves placés dans la SSS, les créneaux SSS de l'emploi du temps et les professeurs qui encadrent. Complétez donc groupes, APSA, élèves, équipements sportifs et emploi du temps, puis retournez dans <strong>[Dossiers] > [Dossier SSS] > [Projet Annuel]</strong>.</li>
</ol>
<p><strong>Si tout est conforme et que le message persiste :</strong> écrivez à votre responsable iPackEPS en précisant le nom du groupe, son type et l'APSA associée.</p>
📺 Tutoriel associé : Gestion_groupes_iPackEPS.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_sss_bloque:
                texte_brut = """<h3>⚠️ BLOCAGE CRÉATION GROUPE SSS</h3>
<p><strong>Règle institutionnelle :</strong> La création d’un groupe de type SSS nécessite obligatoirement que le recteur ait validé la demande. Par défaut, iPackEPS bloque la création de ce type de groupe.</p>
<p><strong>Procédure de déblocage :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Vérifiez que le recteur a bien validé la demande d'ouverture de votre section sportive.</li>
  <li><strong>[Étape 2]</strong> Faites un simple signalement par e-mail à votre responsable iPackEPS ou à votre IPR pour que votre établissement soit activé dans le système.</li>
</ol>
📺 Tutoriel associé : Evolution_et_fermeture_SSS.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
                
            elif est_ressaisie_rentree:
                texte_brut = """<h3>🔄 FAUT-IL TOUT RESAISIR CHAQUE ANNÉE DANS iPACKEPS ?</h3>
<p><strong>Règle d'or iPackEPS :</strong> <strong>NON, il ne faut pas tout resaisir !</strong> L'essentiel des données saisies l'année précédente est automatiquement conservé par l'application.</p>
<p><strong>Ce qui est conservé :</strong></p>
<ul>
  <li>Les données générales de l'établissement et la structure globale.</li>
  <li>Vos compétences, spécialités sportives et l'historique des référentiels.</li>
  <li>La liste générale des APSA programmées.</li>
</ul>
<p><strong>Ce qu'il faut actualiser (ou réinitialiser) pour la rentrée :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Votre service et vos fonctions (remis à zéro à chaque rentrée : nombre d'heures, décharges, choix du rôle de coordonnateur).</li>
  <li><strong>[Étape 2]</strong> L'équipe EPS (actualisation de la liste des collègues connectés).</li>
  <li><strong>[Étape 3]</strong> L'organisation des classes et l'importation des nouveaux élèves.</li>
  <li><strong>[Étape 4]</strong> Les dates de séquences des APSA et la configuration des groupes pour l'année en cours.</li>
</ol>
📺 Tutoriel vidéo associé : Manipulations_Nouvelle_Annee_iPackEPS.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_creation_groupe:
                texte_brut = """<h3>👥 CRÉATION DE GROUPES INTER-CLASSES (EX: 2 GROUPES DE 24 POUR 48 ÉLÈVES)</h3>
<p><strong>Principe iPackEPS :</strong> iPackEPS gère les groupes d'enseignement en s'appuyant sur structures importées. Pour répartir vos élèves de deux classes (ex: 32 et 16) en deux groupes équilibrés de 24, la gestion des effectifs se fait via la ventilation des listes d'élèves.</p>
<p><strong>Procédure exacte :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Allez dans le module <strong>[Dossiers] > [Dossier EPS] > [Classes / Groupes]</strong> pour vérifier que vos classes d'origine (Terminale) sont bien toutes importées.</li>
  <li><strong>[Étape 2]</strong> Créez vos deux structures de groupes personnalisées (ex: <em>Groupe EPS 1</em> et <em>Groupe EPS 2</em>) en leur assignant le niveau Terminale.</li>
  <li><strong>[Étape 3]</strong> Rendez-vous dans le sous-menu d'affectation des élèves (ou module de répartition des effectifs selon votre version).</li>
  <li><strong>[Étape 4]</strong> Sélectionnez tour à tour les élèves de vos classes d'origine pour les basculer et les répartir manuellement dans <em>Groupe EPS 1</em> (24 élèves) et <em>Groupe EPS 2</em> (24 élèves) jusqu'à épuisement des effectifs.</li>
</ol>
📺 Tutoriel associé : affecter_eleves_dans_groupes.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_unss:
                texte_brut = """<h3>🛑 RESTRICTION DOCUMENTAIRE - DISPOSITIFS UNSS</h3>
<p><strong>Règlement :</strong> Pour des raisons de droits d'auteur, aucun texte, circulaire ou document spécifique à l'UNSS ne figure dans la base de cet assistant.</p>
<p><strong>Recommandation :</strong> Pour toute question relative aux équivalences (Jeunes Juges, podiums), veuillez vous référer directement aux textes officiels en vigueur ou consulter votre hiérarchie.</p>"""
                badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

            elif est_gestion_sss_ou_sport:
                texte_brut = """<h3>⚙️ GESTION TECHNIQUE ET ADMINISTRATIVE DES SSS ET SPORT-ÉTUDES</h3>
<p><strong>Règle fondamentale :</strong> iPackEPS distingue rigoureusement la gestion administrative des SSS de la configuration des groupes Sport-Études.</p>
<p><strong>Procédure 1 : Gestion administrative des SSS</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Accédez à <strong>[Dossiers] > [Dossier SSS]</strong>.</li>
  <li><strong>[Étape 2]</strong> Complétez les ouvertures, projets annuels ou bilans.</li>
</ol>
<p><strong>Procédure 2 : Configuration des groupes Sport-Études</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Accédez à <strong>[Dossiers] > [Dossier EPS] > [Groupes]</strong>.</li>
  <li><strong>[Étape 2]</strong> Affectez vos élèves dans l'onglet <strong>[Mes Élèves]</strong>.</li>
</ol>
📺 Tutoriel associé : Configurer_Classes_Sports_Etudes.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_eppcs:
                # Réponse rédigée par T. Armant et confirmée par un collègue (oct. 2026) : aucun dépôt EPPCS en Première, référentiels l'année suivante.
                # Non issue d'un texte officiel : à revoir si iPackEPS ou l'IA-IPR indiquent autre chose.
                texte_brut = """<h3>📋 EPPCS (ENSEIGNEMENT DE SPÉCIALITÉ) : RÈGLE DE PREMIÈRE</h3><p><strong>Règle fondamentale :</strong> L'EPPCS (Éducation Physique, Pratiques et Culture Sportives) est un enseignement de spécialité de la voie générale. Il ne fonctionne <strong>pas par CCF</strong> et ne relève pas du tronc commun géré par iPackEPS.</p><p><strong>Procédure en classe de Première :</strong></p><ol><li><strong>[Étape 1]</strong> Aucune commission académique de certification et <strong>aucun dépôt de fiches certificatives</strong> de type CCF n'est attendu en classe de Première pour cette spécialité.</li><li><strong>[Étape 2]</strong> Vous ne devez absolument rien déposer sur iPackEPS concernant l'EPPCS en Première. Les référentiels de l'EPPCS devront être déposés sur IPACKEPS l'année d'après</li><li><strong>[Étape 3]</strong> L'évaluation certificative interviendra exclusivement en fin de classe de Terminale sous forme d'une épreuve terminale nationale (écrit + oral avec prestation physique).</li></ol>"""
                badge, color_card = "🛠️️ ASSISTANCE iPACKEPS", "general-card"

            elif est_dossier_peda:
                texte_brut = """<h3>📂 ACCÈS AUX RESSOURCES ET DOSSIERS PÉDAGOGIQUES</h3>
<p><strong>Emplacement :</strong> Les documents et cadrages pédagogiques de référence sont centralisés dans l'onglet <strong>[Sécurité & Cadre Réglementaire / Pédagogie]</strong> de l'application.</p>
<p><strong>Rappel d'usage :</strong> Pour interroger le Hub sur les programmes, utilisez des mots-clés ciblés (ex: programmes, cycles, compétences).</p>"""
                badge, color_card = "📚 ESPACE PÉDAGOGIQUE", "general-card"

            elif est_dates_ccf:
                texte_brut = """<h3>📅 CONFIGURATION DES DATES DE CCF ET DES SÉQUENCES</h3>
<p><strong>Principe iPackEPS :</strong> Pour que les protocoles de certification de vos classes soient valides, vous devez définir les dates de vos séquences d'enseignement et d'évaluation pour chaque groupe.</p>
<p><strong>Procédure exacte :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Connectez-vous à iPackEPS via le portail ARENA.</li>
  <li><strong>[Étape 2]</strong> Allez dans le menu <strong>[Dossiers] > [Dossier EPS] > [Séquences]</strong> (ou <strong>[Protocoles]</strong> selon l'affichage).</li>
  <li><strong>[Étape 3]</strong> Sélectionnez le groupe ou la classe concernée.</li>
  <li><strong>[Étape 4]</strong> Saisissez les dates de début et de fin pour chaque séquence ou période de CCF.</li>
  <li><strong>[Étape 5]</strong> Enregistrez vos modifications.</li>
</ol>
📺 Tutoriel associé : Saisie_protocoles_iPackEPS.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
                
            elif est_equipe_eps:
                texte_brut = """<h3>👥 ACTUALISATION DE L'ÉQUIPE EPS (ENSEIGNANT MANQUANT)</h3>
<p><strong>Règle institutionnelle :</strong> Il est strictement impossible de créer "manuellement" un profil enseignant (en tapant son nom) dans iPackEPS. Les comptes remontent obligatoirement de la base académique (STS-Web).</p>
<p><strong>Procédure de mise à jour :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Allez dans le menu <strong>[Dossiers] > [Dossier EPS] > [Équipe EPS]</strong>.</li>
  <li><strong>[Étape 2]</strong> Cliquez sur le bouton d'actualisation ou d'importation des enseignants.</li>
  <li><strong>[Étape 3]</strong> Si l'enseignant n'apparaît toujours pas (cas très fréquent en cité scolaire), c'est que le secrétariat de l'établissement ne l'a pas affecté à la bonne structure dans <strong>STS-Web</strong>. Contactez votre direction pour régulariser l'affectation.</li>
</ol>
📺 Tutoriel associé : Actualisation_equipe_classes.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"

            elif est_doc_synthese:
                texte_brut = """<h3>⚠️ FICHIER SYNTHÈSE ÉTABLISSEMENT (« DOC SYNTHÈSE ») ET BLOCAGE À 97%</h3>
<p><strong>De quoi s'agit-il ?</strong> C'est le document officiel académique qui récapitule les protocoles d'évaluation de votre établissement. Il n'y a pas de modèle à remplir : il se présente comme un export PDF généré automatiquement ou une trame tableur fournie par la DEC.</p>
<p><strong>Explication du message d'erreur :</strong> L'affichage "0 0 1 Doc Synthèse en attente" et un dossier bloqué à 97% est un <strong>comportement tout à fait normal</strong> d'iPackEPS. Cela signifie que l'intégralité de vos saisies pédagogiques est correcte.</p>
<p><strong>Que manque-t-il ?</strong> Le système attend simplement le téléversement final du document académique de synthèse (généralement un export PDF officiel ou une trame tableur fournie par la DEC). <strong>Vous ne devez en aucun cas créer un document vous-même.</strong></p>
<p><strong>Procédure de dépôt :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> Récupérez le document officiel généré pour votre établissement.</li>
  <li><strong>[Étape 2]</strong> Allez dans le menu <strong>[Dossiers] > [Dossier EPS] > [Dépôt des référentiels]</strong> (ou [Dépôts]).</li>
  <li><strong>[Étape 3]</strong> Téléversez le fichier. Votre dossier passera alors à 100% et pourra être transmis.</li>
</ol>
📺 Tutoriel associé : Depot_referentiels_iPackEPS.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
            
            elif est_eleves_inactifs:
                texte_brut = """<h3>📋 GESTION DES ÉLÈVES INACTIFS OU PARTIS</h3>
<p><strong>Règle fondamentale :</strong> Ne cherchez jamais à supprimer, masquer ou décocher manuellement la fiche d'un élève inactif ou parti depuis l'interface ou l'onglet de visualisation. iPackEPS ne comporte aucune option de suppression manuelle individuelle.</p>
<p><strong>Procédure de mise à jour :</strong></p>
<ol>
  <li><strong>[Étape 1]</strong> La liste des élèves dans iPackEPS est le reflet strict de la base administrative de l'établissement (SIÈCLE).</li>
  <li><strong>[Étape 2]</strong> L'actualisation de la base administrative (ou un nouvel import / actualisation de la liste des élèves via iPackEPS) régularisera automatiquement l'effectif.</li>
  <li><strong>[Étape 3]</strong> L'élève inactif ou parti disparaîtra alors de vos listes de manière totalement automatisée.</li>
</ol>
📺 Tutoriel associé : Import_automatique_eleves.mp4"""
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
            
            elif est_question_pedagogique:
                texte_brut = """<h3>🛑 REDIRECTION REQUISE : QUESTION PÉDAGOGIQUE</h3>
<p>Votre question relève de la pédagogie de terrain, de l'animation d'une séance ou de la didactique d'une APSA.</p>
<p>L'onglet actuel est <strong>strictement réservé à la configuration technique et informatique</strong> des logiciels (iPackEPS, Santorin, Cyclades).</p>
<p>👉 Veuillez reposer votre question dans l'onglet <strong>[Sécurité & Cadres Régl.]</strong> (Étape 1, en haut de la page). Cet espace est connecté à la base documentaire des programmes officiels et des ressources Éduscol.</p>"""
                badge, color_card = "⚖️ HORS PÉRIMÈTRE TECHNIQUE", "securite-card"

            # ==================================================================
            # 6. GESTION DE LA RÉPONSE DE L'IA (LLM) SI AUCUN DISJONCTEUR NE S'EST ACTIVÉ
            # ==================================================================
            else:
                besoin_ia = True

            # ==================================================================
            # 5 bis. ARBITRE DES RÉPONSES EN DUR
            # ✅ AJOUT : une réponse en dur se déclenche sur des mots-clés. Elle partait donc aussi quand la question
            # portait sur AUTRE CHOSE (ex. « au stade sans wifi, est-ce que je perds mes notes ? » recevait
            # « iPackEPS n'est pas un carnet de notes » ; « puis-je supprimer un élève dispensé toute l'année ? »
            # recevait la fiche sur le statut DISP). Un contrôle très court demande à l'IA si la réponse en dur
            # traite bien la demande. Si non, la question part à la recherche documentaire. En cas d'erreur du
            # contrôle, la réponse en dur est conservée (comportement d'avant).
            # ==================================================================
            if (not besoin_ia) and texte_brut and openai_api_key and not est_question_trop_courte and not est_mauvais_onglet:
                try:
                    _resume_dur = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", texte_brut)).strip()[:900]
                    _verdict = Settings.llm.complete(
                        "Tu contrôles un assistant destiné aux professeurs d'EPS.\n"
                        "QUESTION DU PROFESSEUR :\n" + prompt + "\n\n"
                        "RÉPONSE TOUTE PRÊTE ENVISAGÉE :\n" + _resume_dur + "\n\n"
                        "Cette réponse toute prête traite-t-elle précisément ce que le professeur demande "
                        "(même sujet ET même difficulté) ?\n"
                        "Réponds NON si la question porte sur un autre problème, sur un message d'erreur, un cas particulier "
                        "ou une conséquence que la réponse toute prête n'aborde pas, ou si elle ne répond pas à ce qui est demandé.\n"
                        "Réponds par un seul mot : OUI ou NON."
                    ).text.strip().upper()
                    if _verdict.startswith("NON"):
                        reponse_en_dur_ecartee = _resume_dur[:90]
                        texte_brut = ""
                        besoin_ia = True
                        origine_reponse = "ia"
                except Exception as e_arbitre:
                    print(f"Erreur de l'arbitre des réponses en dur : {e_arbitre}")

            if besoin_ia and openai_api_key and not extraits_doc:
                extraits_doc, sources_consultees, fiches_diag, erreur_rag = _recherche_documentaire()

            if besoin_ia:
                if contexte_actif == "college":
                    badge, color_card = "📚 COLLÈGE & CONTRÔLE CONTINU (LSU)", "general-card"
                elif mode == "examens":
                    badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
                elif mode == "ipack":
                    badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
                else:
                    badge, color_card = "⚖️ SÉCURITÉ, JURIDIQUE & PÉDAGOGIE", "securite-card"

                if mode == "textes":
                    directive_onglet = """
                    3. ⚖️ SPÉCIFICITÉ ONGLET TEXTES, SÉCURITÉ ET PÉDAGOGIE :
                        - 🧠 ARBITRAGE D'INTENTION (TRÈS IMPORTANT) :
                            * 📚 SI la question est PÉDAGOGIQUE (comment enseigner, barèmes, situations, programmes, gestion de classe) : Réponds EN TANT QU'EXPERT PÉDAGOGIQUE. Donne des conseils concrets de terrain, des repères didactiques, des exemples d'exercices ou d'AFL. Ne parle PAS de textes juridiques ou d'accidents si ce n'est pas le sujet.
                            * ⚖️ SI la question est JURIDIQUE ou SÉCURITAIRE (Accident, APPN, litige) : La réponse s'ouvre sur le double rappel protecteur (obligation de moyens renforcée, art. L. 911-4).
                            * 👔 SI la question concerne la CARRIÈRE (Inspection, note) : Applique le droit de la fonction publique, sans mentionner l'art. L. 911-4.
                        - DOCTRINE APPN & TAUX D'ENCADREMENT : Pour toute activité de pleine nature, encadrement strict et registre des EPI.
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
                    - VIDÉO DE LA FICHE : si la fiche du contexte sur laquelle repose ta réponse contient une ligne « - Vidéo : » suivie d'une adresse, termine ta réponse par « 📺 Tutoriel associé : » suivi de cette adresse, recopiée telle quelle. Une seule vidéo, celle de la fiche utilisée, jamais celle d'une autre fiche.
                    - Ne cite un tutoriel vidéo QUE si son nom correspond clairement à la manipulation que ta réponse explique. Dans le doute, ou si ta réponse n'est pas une manipulation dans un logiciel (règle, explication, réponse négative, renvoi vers un service), n'en cite AUCUN : un tutoriel sans rapport induit le collègue en erreur. Jamais plus d'un tutoriel. Liste officielle des fichiers (import_eleves_pronote.mp4, Configuration_classes_import_eleves.mp4, affecter_eleves_dans_groupes.mp4, Generer_importer_fichier_groupes_cyclades.mp4, verification_affectation_protocoles_cyclades.mp4, creer_convocations_enseignants.mp4, Distribution_lots_santorin.mp4, Distribution_manuelle_lots_santorin.mp4, Saisie_notes_Santorin.mp4, Verrouiller_lot_santorin.mp4, Deverrouiller_lots_santorin.mp4, Ajouter_evaluateur_lot_santorin.mp4, Depot_referentiels_iPackEPS.mp4, Saisie_protocoles_iPackEPS.mp4, Protocoles_adaptes_iPackEPS.mp4, Gestion_groupes_iPackEPS.mp4 (gestion des groupes EPS/AS/SSS), Sequences_apprentissage_groupes.mp4 (séquences d'apprentissage des groupes), Apsa_certificatives_CAP.mp4 (APSA certificatives en CAP), Declaration_projet_APPN.mp4 (déclaration d'un projet APPN), Extraction_notes_Santorin.mp4, Import_documents_glisser_deposer.mp4, Import_automatique_eleves.mp4, Actualisation_equipe_classes.mp4, Gestion_inventaire_EPI_photos.mp4, Controle_dates_CM_CAHPN.mp4, Export_zip_documents_certificatifs.mp4, Export_profs_externes_cyclades.mp4, EDT_Introduction.mp4, EDT_Creation_Suppression.mp4, EDT_Semaines_A_B.mp4, EDT_Verification_Alertes.mp4, Manipulations_Nouvelle_Annee_iPackEPS.mp4).
                    """
                else:
                    bloc_video_consigne = ""

                # ✅ CHAMPS D'APPRENTISSAGE : l'IA se trompait de champ dès que la question citait plusieurs activités
                # (« badminton, tennis de table et escalade : même champ »). Le code reconnaît donc lui-même les activités
                # citées et donne leur champ à l'IA, qui n'a plus à deviner.
                faits_champs = ""
                verdict_champs = ""
                if not est_college:
                    # ✅ La table « activité → champ » n'est plus écrite dans le code : elle est lue dans config/activites_champs.csv,
                    # un simple fichier à mettre à jour quand la liste nationale change (aucune modification du programme).
                    _APSA_CHAMPS = []
                    try:
                        with open("config/activites_champs.csv", encoding="utf-8") as _f_champs:
                            for _ligne in _f_champs:
                                _ligne = _ligne.strip()
                                if not _ligne or _ligne.startswith("#") or _ligne.lower().startswith("activite"):
                                    continue
                                _a, _, _c = _ligne.partition(";")
                                if _a.strip() and _c.strip().isdigit():
                                    _APSA_CHAMPS.append((_a.strip().lower(), int(_c.strip())))
                    except Exception:
                        _APSA_CHAMPS = []
                    import unicodedata as _ud
                    _q_simple = "".join(ch for ch in _ud.normalize("NFD", prompt.lower()) if _ud.category(ch) != "Mn").replace("\u2019", "'").replace("-", " ")
                    _trouvees = [(nom, ca) for nom, ca in _APSA_CHAMPS if re.search(r"\b" + re.escape(nom), _q_simple)]
                    # ✅ DEMI-FOND : la même activité peut être enseignée pour la performance (CA1) ou pour l'entretien de soi (CA5).
                    # Si le collègue ne l'a pas précisé, on lui pose la question au lieu de deviner ; sa précision fixe ensuite le champ.
                    _demande_precision_champ = False
                    if any(nom.startswith("demi") for nom, _ca in _trouvees):  # « demi fond » (le tiret est remplacé par un espace)
                        if re.search(r"entretien|\bca ?5\b|champ 5", _q_simple):
                            _trouvees = [(nom, 5 if nom.startswith("demi") else ca) for nom, ca in _trouvees]
                        elif not re.search(r"performance|\bca ?1\b|champ 1", _q_simple):
                            _demande_precision_champ = re.search(r"protocole|ensemble certificatif|meme |possible|valable|ca passe|compatible|champ", _q_simple) is not None
                    if _demande_precision_champ:
                        verdict_champs = ("<p><strong>Pouvez-vous préciser</strong> s'il s'agit du demi-fond dans sa partie <strong>entretien (CA5)</strong> "
                                          "ou <strong>performance (CA1)</strong> ?</p>"
                                          "<p>La réponse en dépend : c'est ce que l'élève apprend et ce qui est évalué qui fixe le champ d'apprentissage, pas le nom de l'activité. "
                                          "Écrivez simplement « performance » ou « entretien » dans la zone de précision ci-dessous.</p>")
                    elif len(_trouvees) >= 2:
                        _par_champ = {}
                        for nom, ca in _trouvees:
                            _par_champ.setdefault(ca, []).append(nom)
                        _lignes = [f"- {nom} : champ d'apprentissage {ca}" for nom, ca in _trouvees]
                        _memes = [" et ".join(noms) + f" (champ {ca})" for ca, noms in _par_champ.items() if len(noms) > 1]
                        if _memes:
                            _concl = "Activités du MÊME champ, donc impossibles ensemble dans un même protocole d'examen : " + " ; ".join(_memes) + ". Les autres activités citées sont dans un champ différent."
                        else:
                            _concl = "Ces activités sont toutes dans des champs DIFFÉRENTS : elles peuvent figurer ensemble dans un protocole d'examen."
                        # Question du type « ces activités dans le même protocole, est-ce possible ? » : le verdict est calculé
                        # ici et remplace la réponse de l'IA, qui se trompait encore de champ malgré les faits fournis.
                        if re.search(r"protocole|ensemble certificatif|meme |possible|valable|ca passe|compatible", _q_simple):
                            _detail = " ; ".join(f"{nom} (champ {ca})" for nom, ca in _trouvees)
                            if _memes:
                                verdict_champs = ("<p><strong>NON :</strong> " + " ; ".join(_memes) + " relèvent du même champ d'apprentissage. "
                                                  "Un protocole d'examen ne peut pas contenir deux épreuves du même champ : gardez-en une seule et complétez avec une activité d'un autre champ.</p>"
                                                  "<p>Champs des activités citées : " + _detail + ".</p>")
                            else:
                                verdict_champs = ("<p><strong>OUI :</strong> ces activités relèvent de champs d'apprentissage différents, elles peuvent figurer dans le même protocole d'examen.</p>"
                                                  "<p>Champs des activités citées : " + _detail + ".</p>"
                                                  "<p>Rappel : 3 épreuves de 3 champs différents au baccalauréat, 2 épreuves de 2 champs différents au CAP.</p>")
                        faits_champs = ("FAITS VÉRIFIÉS PAR LE PROGRAMME (ils priment sur tout le reste, ne les contredis jamais) — champs d'apprentissage au lycée des activités citées dans la question :\n"
                                        + "\n".join(_lignes) + "\n" + _concl + "\n")

                # ✅ COLLÈGE : une question sur le zéro ou l'absence recevait la règle des circulaires du CAP et du bac pro.
                if "coll" in str(niveau_actuel_form).lower() and re.search(r"z[ée]ro|absen|\b0\b", prompt.lower()):
                    faits_champs += ("FAIT VÉRIFIÉ PAR LE PROGRAMME (il prime sur tout le reste) — la question concerne le COLLÈGE : les circulaires du CAP, "
                                     "du baccalauréat professionnel et du baccalauréat général (« absence non justifiée = zéro ») ne s'appliquent PAS au collège et ne doivent pas être citées. "
                                     "Au collège, on ne met pas zéro pour une absence à une évaluation ordinaire : si la moyenne n'est pas représentative, mention « En attente », "
                                     "évaluations supplémentaires, puis évaluation de remplacement. Le zéro n'est attribué que pour une absence NON justifiée à l'évaluation de remplacement. "
                                     "Texte : note de service du 2 septembre 2025 (Bulletin officiel du 4 septembre 2025).\n")

                contexte_complet_ia = f"""
{faits_champs}
CONTEXTE DOCUMENTAIRE OFFICIEL LOCAL :
{extraits_doc}

{verites_terrain_pierre}
"""

                consigne_ia = f"""Tu es l'assistant IA officiel en Éducation Physique et Sportive (EPS).
Ton expertise couvre deux grands domaines :
1. L'ingénierie pédagogique et didactique (programmes, évaluation, construction de cycles).
2. La réglementation institutionnelle, juridique et logicielle (iPackEPS, Santorin, examens).

======================================================================
ÉTAPE 0 : RESTRICTION DE RECHERCHE (ZÉRO INTERNET / ZÉRO TAVILY)
======================================================================
INTERDICTION ABSOLUE d'utiliser des outils de recherche web externes (Tavily, Google, bing, etc.).
Tu dois construire ta réponse STRICTEMENT et UNIQUEMENT à partir du "CONTEXTE DOCUMENTAIRE OFFICIEL LOCAL" fourni ci-dessous. Si la réponse n'y est pas, dis simplement que tu ne disposes pas de l'information dans ta base locale.

======================================================================
ÉTAPE 1 : FILTRAGE PRIMAIRE ET GESTION DES PRÉMISSES (PRIORITÉ ABSOLUE)
======================================================================
Avant d'analyser le fond, tu dois impérativement passer la question au crible de ces filtres.

1. LE FILTRE DE LONGUEUR (ANTI-REQUÊTE VIDE) :
- Si la question comporte 3 mots ou moins, réponds STRICTEMENT : "Pouvez-vous reformuler votre question en l'étayant davantage afin que je puisse vous apporter une aide précise et adaptée à votre contexte ?"

2. LE FILTRE DES FAUSSES PRÉMISSES (ANTI-ÉVITEMENT) :
- INTERDICTION ABSOLUE d'ouvrir une réponse par des phrases toutes faites de type "Aucun texte réglementaire n'impose..." sauf si l'utilisateur énonce explicitement une obligation fausse et absurde. Pour toute question normale de type "Comment faire..." ou "Que faire si...", réponds directement et constructivement sans formule négative parasite.

======================================================================
ÉTAPE 2 : IDENTIFICATION DU PUBLIC ET DU CONTEXTE CIBLE
======================================================================
Cible sélectionnée par l'utilisateur : {niveau_actuel_form}
Contexte d'onglet actif : {contexte_choisi_nom}
{directive_onglet}

1. LE PRINCIPE DE FLEXIBILITÉ INTELLIGENTE :
- Si l'utilisateur pose une question sur le DNB alors qu'il est dans l'onglet "Examens/Lycée", traite la question sous l'angle du DNB. Le sujet réel de la question prime toujours sur l'erreur de choix d'onglet de l'utilisateur.

2. LE PRINCIPE DE RÉALITÉ DES PUBLICS (INVARIANTS INSTITUTIONNELS) :
- PREMIER DEGRÉ (Maternelle/Élémentaire) : AUCUN CCF, AUCUN Santorin/Cyclades, AUCUN DNB. Évaluation via le LSU. 
- COLLÈGE (6e à 3e, SEGPA, ULIS, Prépa-métiers) : AUCUN CCF, AUCUNE APSA certificative, AUCUN protocole Santorin/Cyclades. Évaluation exclusivement par contrôle continu et LSU.
- LYCÉE (Voie GT, Pro, CAP) : Cadre strict du CCF. Évaluation via Cyclades et Santorin.

======================================================================
ÉTAPE 3 : ARBRE DE DÉCISION DES LOGICIELS ET RÈGLE DE MORT
======================================================================
1. LA RÈGLE ZÉRO DES BLOCAGES STRUCTURELS :
- Si l'utilisateur signale un rejet de protocole ou une impossibilité de saisir : INTERDICTION de répondre "contactez la direction". Donne la procédure de nettoyage dans iPackEPS et l'alignement dans Cyclades.

2. SANTORIN : CADENAS ET VERROUILLAGES :
- Un enseignant ne peut PAS déverrouiller un lot. Cette action relève EXCLUSIVEMENT du Chef d'établissement depuis sa console "Santorin-Direction".

3. GESTION DES INTERFACES ET ZÉRO INVENTION (RÈGLE DE MORT ABSOLUE) :
- Tu as l'INTERDICTION FORMELLE d'inventer des noms de menus, des boutons, des cases à cocher ou des onglets.
- LIRE D'ABORD LES 3 PREMIÈRES LIGNES DE CHAQUE FICHE : avant de rédiger, lis pour chaque fiche du contexte son titre et les deux lignes qui suivent (mots-clés, formulations, « Réponse courte »). Elles disent de quoi parle la fiche et quelle est sa réponse. Retiens la fiche dont le titre correspond vraiment à la question posée (même examen, même niveau, même logiciel) et écarte celles qui parlent d'autre chose. Si la fiche retenue contient une ligne « Réponse courte », ta réponse commence par cette réponse, sans la contredire.
- PRÉCISION DES CHEMINS : quand le contexte donne le nom exact d'un menu, d'un onglet ou d'un bouton, recopie-le tel quel entre crochets. N'écris JAMAIS une tournure floue comme « l'onglet qui permet de… », « la section prévue à cet effet », « le champ approprié » ou « les icônes peuvent signaler… » : soit tu donnes le nom exact et ce qu'il affiche, soit tu ne mentionnes pas l'élément.
- TEXTES OFFICIELS EN GRAS : quand le contexte cite la référence d'un texte officiel (loi, article de code, décret, arrêté, circulaire, note de service, Bulletin officiel, avec sa date ou son numéro), termine ta réponse par une ligne « Texte de référence : » suivie de cette référence en gras (**...**), recopiée telle quelle. Seuls comptent les textes officiels : un guide, un tutoriel, un support de formation, un site académique ou le titre d'une fiche (« SITUATION : … ») ne sont PAS des textes de référence et ne doivent jamais figurer sur cette ligne. Ne cite QUE les références écrites dans le contexte : n'invente jamais un numéro, une date ou un article, et si le contexte n'en donne aucune, n'écris pas cette ligne.
- Le contexte documentaire est invisible pour l'utilisateur : ne lui dis JAMAIS de « consulter la fiche … », « voir la fiche … » ou « se reporter au tutoriel dédié ». Si le contexte renvoie à une autre fiche, donne directement l'information utile si elle figure dans le contexte ; sinon n'en parle pas.
- Tu dois t'appuyer en priorité sur le "CONTEXTE DOCUMENTAIRE OFFICIEL LOCAL" fourni ci-dessous pour répondre aux procédures. 
- Si l'information figure dans le contexte (même avec des synonymes comme "départ", "inactif" ou "actualisation"), utilise-la pour guider l'utilisateur.
- Si plusieurs procédures du contexte semblent proches, choisis UNIQUEMENT celle dont la cause correspond exactement au symptôme décrit par l'utilisateur. Ne mélange jamais deux procédures différentes dans une même réponse et n'ajoute aucune étape (menu, bouton, vérification) qui ne figure pas mot pour mot dans le contexte.
- UNE RÉPONSE NÉGATIVE EST UNE RÉPONSE : si le contexte dit que l'action est impossible, que l'enseignant ne peut pas la faire lui-même, qu'il n'existe pas de bouton / de compte / de procédure, que le problème est connu et sans conséquence, ou qu'il faut s'adresser à un autre service ou consulter un autre document (circulaire, calendrier de la DEC...), alors c'est LA réponse : donne-la clairement, avec l'explication du contexte. Ne réponds surtout pas que tu ne disposes pas de la procédure.
- La phrase d'absence est réservée au cas où AUCUN passage du contexte ne parle du sujet de la question. Dans ce seul cas, ta seule et unique réponse autorisée est : "Je suis désolé, mais je ne dispose pas de la procédure exacte dans ma base de données locale pour répondre à cette demande. Veuillez contacter l'assistance académique."
- N'écris JAMAIS cette phrase d'absence après avoir donné une réponse, même partielle : soit tu réponds, soit tu écris cette phrase seule.
- Il est strictement interdit d'utiliser tes connaissances générales extérieures pour deviner comment fonctionne iPackEPS.

4. SIGLES (ZÉRO INVENTION) :
- Écris les sigles tels quels (DEC, AFLP, APSA...). N'ajoute JAMAIS entre parenthèses la signification d'un sigle, sauf si elle figure mot pour mot dans le glossaire ci-dessous ou dans le contexte documentaire.
- Glossaire officiel : APSA = Activités Physiques, Sportives et Artistiques ; AFL = Attendus de Fin de Lycée (voie générale et technologique) ; AFLP = Attendus de Fin de Lycée Professionnel (voie professionnelle et CAP) ; CCF = Contrôle en Cours de Formation ; DEC = Division des Examens et Concours ; CAHPN = Commission Académique d'Harmonisation et de Proposition de Notes ; SHN = Sportif de Haut Niveau ; SSS = Section Sportive Scolaire ; LSU = Livret Scolaire Unique ; DNB = Diplôme National du Brevet.
- En voie générale et technologique on parle d'AFL ; en voie professionnelle et en CAP on parle d'AFLP. N'emploie pas l'un pour l'autre.

5. QUI FAIT QUOI (NE JAMAIS INVERSER LES RÔLES) :
- Attribue chaque action à la personne indiquée par le contexte : enseignant, coordonnateur EPS, secrétariat, chef d'établissement, DEC. Ne fais jamais faire à l'enseignant une action que le contexte réserve au chef d'établissement ou au secrétariat (créer une mission dans Imag'in, cliquer sur le picto PDF, distribuer ou déverrouiller un lot, importer dans Cyclades...). Dis à l'enseignant ce qu'il doit DEMANDER et à qui.
- Si le contexte précise ce que l'enseignant n'a PAS à faire ou ne peut pas faire, dis-le en premier.

6. FIDÉLITÉ AU CONTEXTE (ZÉRO BRODERIE) :
- Commence par répondre à la question posée, en une phrase complète qui reprend ses mots et donne la conclusion (exemples : « Vous pouvez évaluer seul, car... », « Vous ne perdez pas vos notes : ... », « Il ne faut pas ouvrir plusieurs onglets, car... »). N'ouvre pas la réponse par un « Oui » ou un « Non » isolé : établis d'abord la conclusion à partir du contexte, et vérifie que ta première phrase dit la même chose que le reste de ta réponse.
- N'ajoute aucune étape de remplissage (« vérifiez votre connexion », « contactez votre correspondant », « assurez-vous que tout est correct ») si elle ne figure pas dans le contexte. Une réponse courte et exacte vaut mieux qu'une procédure rallongée.
- PAS DE RÉPONSE VAGUE : n'écris jamais de généralités qui ne s'appuient sur aucun passage (« assurez-vous que la note est valide », « respectez les procédures de votre établissement », « prenez en compte la situation de l'élève »). Si le contexte ne traite qu'une partie de la question, réponds précisément à cette partie et dis en une phrase ce que ta base ne précise pas.
- Pour un texte réglementaire (décret, circulaire, note de service), rapporte ce que dit le contexte sans commenter ses intentions ni ses bénéfices supposés (« plus de flexibilité », « plus équitable »...).
- Les passages du contexte précédés de [Base iPackEPS] ou [Base Examens & Santorin] viennent de l'autre base documentaire : ils ont la même valeur que les autres.
- CHEMINS DE MENU : ne donne un chemin de menu que s'il figure dans le contexte, et donne-le sans le nuancer. Les formules « généralement », « en général », « normalement », « il se peut que » devant un menu ou un bouton sont interdites : si le chemin exact n'est pas dans le contexte, dis ce que le contexte permet de dire et précise que le chemin exact n'est pas dans ta base.
- Ne recopie pas une phrase du contexte qui traite d'un cas particulier que le professeur n'a pas évoqué (autre examen, autre nombre d'épreuves, autre logiciel).
- SYMPTÔME À PLUSIEURS CAUSES : si les détails de la question désignent une seule cause, ne donne que celle-là. Si plusieurs causes du contexte peuvent expliquer ce que décrit le professeur (exemple : une note refusée peut venir de la virgule à la place du point, ou de l'AFL1 non saisi), présente-les toutes, une ligne chacune, avec ce qu'il faut vérifier, sans mélanger leurs étapes.

7. PORTÉE DES RÈGLES (NE PAS TRANSPOSER D'UN EXAMEN À L'AUTRE) :
- Le public sélectionné par le professeur figure à l'ÉTAPE 2. Une règle du contexte qui précise sa portée (baccalauréat général et technologique, baccalauréat professionnel, CAP, DNB, collège) ne vaut que pour cette portée.
- Ne transpose jamais une règle du bac général et technologique à la voie professionnelle ou au CAP (ni l'inverse) : AFL / AFLP, nombre d'épreuves, co-évaluation, textes de référence diffèrent. Si le contexte ne contient la règle que pour un autre public que celui du professeur, dis-le clairement (« le texte dont je dispose concerne le bac général et technologique ; je n'ai pas le texte équivalent pour la voie professionnelle ») et renvoie à la DEC ou à l'inspection, sans affirmer que la règle s'applique.

- LE PUBLIC « Lycée Pro / CAP » REGROUPE DEUX EXAMENS DIFFÉRENTS : le baccalauréat professionnel (ensemble de 3 épreuves, 3 champs d'apprentissage) et le CAP (2 épreuves, 2 champs d'apprentissage). Repère l'examen nommé dans la question (« bac pro », « terminale bac pro », « CAP ») et prends la réponse de CET examen : une « Réponse Lycée Pro CAP » ne vaut pas pour le bac pro, et une « Réponse Lycée Pro Bac » ne vaut pas pour le CAP. Si la question ne précise pas l'examen, donne les deux réponses en les distinguant clairement.
- N'ÉTENDS PAS UNE RÈGLE À UN CAS VOISIN : une absence, un refus de passer l'épreuve, un abandon en cours d'épreuve, une blessure, une dispense sont des situations différentes, traitées différemment. N'écris jamais « cela s'applique également à... » si le contexte ne le dit pas. Si le contexte ne traite que le cas voisin, dis-le et n'affirme rien pour le cas posé.
- QUESTION EN PLUSIEURS PARTIES : si le professeur pose deux questions (« où... et comment... »), réponds à chacune séparément, chacune à partir de son propre passage du contexte ; ne réponds pas à la seconde avec le passage de la première. Si le contexte ne couvre qu'une des deux, dis-le.

8. MÉMO PERMANENT (VRAI MÊME SI LE CONTEXTE N'EN PARLE PAS) :
- DATES ET DÉLAIS : toute date limite (dépôt des référentiels, saisie des protocoles, import des classes, saisie ou verrouillage des notes, commissions) DÉPEND DE CHAQUE ACADÉMIE : elle est fixée chaque année par la DEC et l'inspection pédagogique de l'académie de l'utilisateur. Des collègues d'autres académies utilisent aussi cet assistant : ne présente JAMAIS une date, un calendrier ou un contact comme étant celui « d'Aix-Marseille », écris « votre académie ». À une question « jusqu'à quand », « avant quelle date », « date limite », ne réponds JAMAIS que tu ne disposes pas de la procédure et n'invente JAMAIS de date : explique que la date est fixée chaque année par la circulaire académique et le calendrier de la DEC de son académie (les dates diffèrent d'une académie à l'autre), qu'il faut les consulter ou interroger le secrétariat des examens de l'établissement, puis, si le contexte la contient, rappelle la manipulation concernée. Ne cite jamais la date d'une autre académie.
- ACCÈS : iPackEPS, Cyclades, Imag'in et Santorin s'ouvrent uniquement depuis le portail ARENA, avec les identifiants académiques. Il n'existe pas de compte ni de mot de passe propre à iPackEPS ou à Santorin.
- RÉPARTITION DES RÔLES POUR LES EXAMENS : le coordonnateur EPS prépare APSA, référentiels, groupes et protocoles dans iPackEPS ; le chef d'établissement (ou son secrétariat) exporte vers Cyclades, importe, réaffecte les protocoles, distribue et déverrouille les lots ; l'enseignant vérifie ses élèves, saisit ses notes par AFL ou AFLP et verrouille son lot.

======================================================================
ÉTAPE 4 : ARBRE DE DÉCISION JURIDIQUE ET SÉCURITÉ (LIGNE ROUGE)
======================================================================
- En cas de danger physique ou de matériel défectueux avéré, l'action immédiate est l'arrêt de l'activité.

======================================================================
ÉTAPE 5 : FORMATAGE ET INSTRUCTIONS DE CLÔTURE
======================================================================
{contexte_complet_ia}

{bloc_echange_precedent}
QUESTION DE L'UTILISATEUR (public sélectionné : {niveau_actuel_form}) :
{prompt}

RAPPEL AVANT DE RÉPONDRE : réponds pour CE public. Si un passage du contexte donne des réponses différentes selon le public (« Réponse Lycée GT Bac », « Réponse Lycée Pro Bac / Lycée Pro CAP », « Réponse Collège DNB »), utilise uniquement celle qui correspond au public sélectionné ou à l'examen cité dans la question. Une règle prévue pour un autre examen ne s'applique pas.

MÉTHODE D'ANALYSE & RÈGLES DE RÉPONSE :
1. ANALYSE DU PÉRIMÈTRE : Réponds avec précision, clarté et rigueur.
2. STRUCTURE & MISE EN PAGE :
    - Rends une réponse bien structurée et claire.
    - FORMAT PAS-À-PAS : uniquement quand le contexte décrit une manipulation en plusieurs étapes, utilise des balises explicites entre crochets et en gras : <strong>[Étape 1]</strong>, <strong>[Étape 2]</strong>, etc., en reprenant les étapes du contexte, dans l'ordre, sans en ajouter. Quand la réponse est une règle, une explication ou une réponse négative, réponds en quelques phrases, SANS étapes.
    - Utilise des listes à puces ou ordonnées HTML propres (`<ul>`, `<ol>`, `<li>`).
{directive_onglet}
{bloc_video_consigne}
{consigne_relance_finale}"""

                try:
                    response = Settings.llm.complete(consigne_ia)
                    texte_brut = response.text
                    if verdict_champs:
                        texte_brut = verdict_champs
                except Exception as e:
                    texte_brut = f"Erreur de traitement IA : {str(e)}"

        # ==================================================================
        # 7. MISE EN FORME FINALE, LOG ET AFFICHAGE
        # ✅ CORRECTION MAJEURE : ce bloc était auparavant DANS le "else" (cas non hors-sujet).
        # Résultat : la réponse "HORS PÉRIMÈTRE INSTITUTIONNEL" n'était jamais affichée
        # ni enregistrée dans le Google Sheet. Il est maintenant exécuté dans tous les cas.
        # ==================================================================

        # ✅ L'IA entourait parfois le nom du tutoriel d'un lien inventé (https://example.com/...). On ne garde que le nom du fichier.
        texte_brut = re.sub(r"<a\s[^>]*>\s*([A-Za-z0-9_.-]+\.mp4)\s*</a>", r"\1", texte_brut, flags=re.IGNORECASE)

        # ✅ « Texte de référence » : on ne garde la ligne que si elle cite un vrai texte officiel (l'IA y mettait parfois
        # un titre de fiche ou une phrase). « Tutoriel associé » : on ne garde que les vrais fichiers .mp4 et adresses YouTube.
        def _garder_ligne(_l):
            if re.match(r"\s*(\*\*)?Texte de r[ée]f[ée]rence", _l, flags=re.IGNORECASE):
                return bool(re.search(r"d[ée]cret|circulaire|note de service|arr[êe]t[ée]|\bloi\b|code de|article [LRD]\b|bulletin officiel|\bB\.?O\.?\b|\bNOR\b", _l, flags=re.IGNORECASE)) and "SITUATION" not in _l
            if re.search(r"Tutoriel\s+(vid[ée]o\s+)?associ[ée]\s*:", _l, flags=re.IGNORECASE):
                return bool(re.search(r"\.mp4|youtu\.?be", _l, flags=re.IGNORECASE))
            return True
        texte_brut = "\n".join(_l for _l in str(texte_brut).split("\n") if _garder_ligne(_l))

        # 🧹 NETTOYAGE DES VIDÉOS POUR LE COLLÈGE (DNB)
        if est_college or est_dnb:
            texte_brut = re.sub(r"[a-zA-Z0-9_.-]+\.mp4", "", texte_brut, flags=re.IGNORECASE)
            texte_brut = re.sub(r"santorin", "LSU / dossier scolaire", texte_brut, flags=re.IGNORECASE)

        # ✅ CORRECTION : le tuto ajouté dépend du sujet (avant : toujours « Evolution_et_fermeture_SSS »,
        # un fichier introuvable sur le site des tutoriels, et sans rapport avec un projet annuel ou un bilan)
        if est_sss:
            if "projet annuel" in p_low or "projet" in p_low:
                video_sss = "Projet_annuel_SSS.mp4"
            elif "bilan" in p_low:
                video_sss = "Bilan_annuel_SSS.mp4"
            elif "ouvr" in p_low:
                # ✅ CORRECTION : « nous voulons ouvrir une section » (sans le mot « ouverture ») recevait le tutoriel de fermeture
                video_sss = "Demande_ouverture_SSS.mp4"
            elif "groupe" in p_low:
                video_sss = "Gestion_groupes_iPackEPS.mp4"
            else:
                video_sss = "Evolution_et_fermeture_SSS.mp4"
            if not re.search(r"[A-Za-z0-9_]+_SSS\.mp4", texte_brut):
                texte_brut += "\n\n📺 Tutoriel associé : " + video_sss

        # ✅ CORRECTION : le tutoriel « classes Sports-Études » était ajouté à toute réponse parlant de haut niveau,
        # y compris dans l'onglet Examens (saisie du 20/20 dans Santorin), où il n'a aucun rapport. Onglet iPackEPS seulement.
        if est_shn and mode == "ipack":
            texte_brut = texte_brut.replace("Saisie_protocoles_iPackEPS.mp4", "Configurer_Classes_Sports_Etudes.mp4")
            texte_brut = texte_brut.replace("Generer_importer_fichier_groupes_cyclades.mp4", "Configurer_Classes_Sports_Etudes.mp4")
            if "Configurer_Classes_Sports_Etudes.mp4" not in texte_brut:
                texte_brut += "\n\n📺 Tutoriel associé : Configurer_Classes_Sports_Etudes.mp4"

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

        # ✅ CORRECTION D'AFFICHAGE : le gras Markdown **texte** de l'IA devenait des astérisques visibles
        texte_brut = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", texte_brut, flags=re.DOTALL)
        # ✅ CORRECTION D'AFFICHAGE : un mot entre balises <code> apparaissait en pavé blanc illisible (ex. « DISP »),
        # et les accents graves `[Menu]` de l'IA restaient visibles. Les deux deviennent du gras.
        texte_brut = re.sub(r"<code>(.*?)</code>", r"<strong>\1</strong>", texte_brut, flags=re.DOTALL | re.IGNORECASE)
        texte_brut = re.sub(r"`([^`\n]+)`", r"<strong>\1</strong>", texte_brut)

        texte_nettoye = texte_brut.replace("\r\n", "\n").replace("\r", "\n")
        texte_final = (
            texte_nettoye.replace("<p>", "")
            .replace("</p>", "<br>")
        )
        # ✅ CORRECTION D'AFFICHAGE : les retours à la ligne situés entre les balises de liste
        # (<ol>, <ul>, <li>) devenaient des <br> placés dans la liste, que le navigateur affichait
        # comme des puces ou des numéros vides. On les retire avant la conversion en <br>.
        _balises_bloc = r"(?:ol|ul|li|h3|h4)"
        texte_final = re.sub(r"[ \t]*\n\s*(?=</?" + _balises_bloc + r"\b)", "", texte_final)
        texte_final = re.sub(r"(</?" + _balises_bloc + r"\b[^>]*>)[ \t]*\n\s*", r"\1", texte_final)
        texte_final = re.sub(r"\n{3,}", "\n\n", texte_final)
        texte_final = texte_final.replace("\n", "<br>")

        phrase_contexte = (
            f"<div style='font-size: 12.5px; color: #94A3B8; margin-bottom: 10px; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 5px;'>📍 <em>Vous avez choisi de poser votre question dans {contexte_choisi_nom} — Contexte : <b>{niveau_actuel_form}</b>.</em></div>"
        )

        footer_assistance = (
            "<div style='margin-top: 14px; padding: 10px; background-color: rgba(250, 204, 21, 0.1); color: #FDE047; border-radius: 6px; font-size: 12.5px; border: 1px solid rgba(250, 204, 21, 0.3);'>"
            "<strong>« IA en apprentissage constant, je peux parfois trébucher sur les subtilités juridiques ou didactiques malgré le soin apporté à ma copie. "
            "À l'image de mes aînés, je vous invite vivement à croiser et vérifier cette réponse avec les textes officiels ou votre hiérarchie. »</strong>"
            "</div>"
        ) if mode == "textes" else (
            "<div style='margin-top: 14px; padding-top: 8px; border-top: 1px dashed rgba(255,255,255,0.15); font-size: 12.5px; color: #CBD5E1;'>"
            "Bien entendu si ma réponse ne vous a pas aidé vous pouvez toujours contacter l'assistance "
            "<a href='mailto:ipackeps@ac-aix-marseille.fr' style='color: #38BDF8 !important; text-decoration: underline;'>ipackeps@ac-aix-marseille.fr</a>"
            "</div>"
        )

        # ✅ AJOUT : onglet Textes, on montre sur quels documents s'appuie la réponse
        bloc_sources = ""
        if mode == "textes":
            # On ne garde que les documents proches du meilleur résultat (évite d'afficher des sources peu pertinentes)
            scores = [sc for _, sc in sources_consultees if sc is not None]
            meilleur = max(scores) if scores else None
            vus = []
            for lib, sc in sources_consultees:
                if not lib or lib in vus:
                    continue
                if meilleur is not None and sc is not None and sc < 0.9 * meilleur:
                    continue
                vus.append(lib)
            if vus:
                bloc_sources = (
                    "<div style='margin-top: 14px; padding: 8px 10px; border-left: 3px solid #38BDF8; font-size: 12.5px; color: #CBD5E1;'>"
                    "<strong>📚 Documents de référence consultés pour cette réponse :</strong><br>"
                    + "<br>".join("• " + v for v in vus[:5])
                    + "</div>"
                )

        # 🔎 DIAGNOSTIC (MODE ADMIN UNIQUEMENT) : quelles fiches la recherche a transmises à l'IA pour cette question.
        # Sert à comprendre un « je ne dispose pas de la procédure » : fiche absente de la liste = problème de recherche ;
        # fiche présente = l'IA l'a reçue mais ne s'en est pas servie. Les collègues ne voient jamais ce bloc.
        bloc_diag = ""
        if st.session_state.get("is_admin", False) and origine_reponse == "ia":
            lignes_diag = [
                "• " + html_lib.escape(t) + (f" <em>({sc:.2f})</em>" if isinstance(sc, (int, float)) else "")
                for t, sc in fiches_diag
            ] or ["Aucune fiche transmise à l'IA."]
            if erreur_rag:
                lignes_diag.insert(0, "⚠️ Erreur pendant la recherche : " + html_lib.escape(erreur_rag))
            if reponse_en_dur_ecartee:
                lignes_diag.insert(0, "↪️ Réponse en dur écartée par l'arbitre : " + html_lib.escape(reponse_en_dur_ecartee) + "…")
            bloc_diag = (
                "<div style='margin-top: 14px; padding: 8px 10px; border-left: 3px solid #F59E0B; font-size: 12px; color: #CBD5E1;'>"
                "<strong>🔎 Admin — fiches transmises à l'IA :</strong><br>" + "<br>".join(lignes_diag) + "</div>"
            )

        formatted_answer = (
            f'<div class="{color_card}">{phrase_contexte}<strong>{badge} :</strong><br>{texte_final}{bloc_sources}{bloc_diag}{footer_assistance}</div>'
        )

        log_interaction(
            question=("[RELANCE] " + prompt) if relance_ctx else prompt, 
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

        # ✅ Les fiches rédigées d'après les vidéos donnent l'adresse de la vidéo (« - Vidéo : https://... ») et non un nom
        # de fichier .mp4 : sans ce bloc, la vidéo n'était plus affichée sous la réponse.
        if mode != "textes" and not est_dnb:
            _deja = {m["content"] for m in st.session_state.messages_hub if m.get("type") == "video"}
            for _url in re.findall(r"https?://(?:www\.)?(?:youtu\.be/|youtube\.com/watch\?v=)[A-Za-z0-9_-]{6,}", texte_final)[:1]:
                if _url not in _deja:
                    st.session_state.messages_hub.append(
                        {"role": "assistant", "type": "video", "content": _url}
                    )

        # Une réponse « je ne dispose pas... » n'est pas une réponse à compléter : la précision sera traitée comme
        # une question complétée, sans consigne « ne répète pas » (qui poussait l'IA à refuser une seconde fois).
        if origine_reponse == "ia" and re.search(r"je ne dispose pas|pouvez-vous reformuler|je n'ai pas d'information plus pr", texte_brut, flags=re.IGNORECASE):
            origine_reponse = "vide"

        # 💬 On mémorise uniquement cet échange (texte brut, tronqué), pour une éventuelle relance.
        _nb_relances = (relance_ctx["relances"] + 1) if relance_ctx else 0
        if origine_reponse in ("ia", "direct", "courte", "vide") and _nb_relances < NB_RELANCES_MAX:
            _reponse_texte = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", texte_brut)).strip()
            st.session_state.dernier_echange = {
                "question": prompt[:1200],
                "reponse": _reponse_texte[:1500],
                "mode": mode,
                "niveau": niveau_actuel_form,
                "origine": origine_reponse,
                "relances": _nb_relances,
            }
        else:
            st.session_state.dernier_echange = None

        st.session_state.reset_steps = True
        st.rerun()

if "messages_hub" in st.session_state and st.session_state.messages_hub:
    st.markdown('<div style="margin-top: 15px;">', unsafe_allow_html=True)
    # 1) La question et la réponse d'abord (les vidéos sont affichées plus bas, après la zone de précision)
    for m in st.session_state.messages_hub:
        if m.get("type") == "video":
            continue
        with st.chat_message(m["role"]):
            st.markdown(m["content"], unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 2) 💬 RELANCE BORNÉE : proposée juste sous la réponse, à l'initiative du collègue uniquement.
    _echange = st.session_state.get("dernier_echange")
    if _echange:
        _titre_relance = (
            "✍️ Complétez votre question ici (elle sera ajoutée à la précédente)"
            if _echange["origine"] in ("courte", "vide")
            else "💬 Cette réponse ne vous débloque pas ? Précisez votre situation, ou posez une autre question sur ce même onglet"
        )
        st.markdown(
            f"<div style='margin-top: 14px; margin-bottom: 8px; padding: 12px 14px; background: linear-gradient(135deg, #1E293B, #0F172A); "
            f"border: 1px solid #38BDF8; border-radius: 8px; font-size: 13.5px; color: #F1F5F9; line-height: 1.5;'>"
            f"<strong style='color: #38BDF8;'>{_titre_relance}</strong><br>"
            "Une seule précision est possible. Pour changer d'onglet ou de public, choisissez de nouveau un contexte à l'étape 1.</div>",
            unsafe_allow_html=True,
        )
        with st.form(key="form_relance_hub", clear_on_submit=True):
            col_rel_input, col_rel_submit = st.columns([5, 1])
            with col_rel_input:
                relance_brute = st.text_input(
                    "Précision :",
                    placeholder="Ce que vous avez fait, où ça bloque, le message exact affiché...",
                    label_visibility="collapsed",
                )
            with col_rel_submit:
                bouton_relance = st.form_submit_button("💬 Préciser", use_container_width=True)
            if bouton_relance and relance_brute.strip():
                st.session_state.relance_ctx = dict(_echange)
                st.session_state.dernier_echange = None
                st.session_state.current_prompt = relance_brute.strip()
                st.rerun()

    # 3) Les tutoriels vidéo en dernier : ainsi la zone de précision reste visible juste sous la réponse
    for m in st.session_state.messages_hub:
        if m.get("type") == "video":
            with st.chat_message(m["role"]):
                st.video(m["content"])
