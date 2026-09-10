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


def log_interaction(question, reponse):
    payload = {"question": question, "reponse": reponse}
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
    "import_eleves_pronote.mp4": "https://pole-examens.github.io/tutoriels-examens/res/import_eleves_pronote.mp4",
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
    "Depot_referentiels_iPackEPS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Depot_referentiels_iPackEPS.mp4",
    "Saisie_protocoles_iPackEPS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Saisie_protocoles_iPackEPS.mp4",
    "Protocoles_adaptes_iPackEPS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Protocoles_adaptes_iPackEPS.mp4",
    "Extraction_notes_Santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Extraction_notes_Santorin.mp4",
    "Import_documents_glisser_deposer.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Import_documents_glisser_deposer.mp4",
    "Import_automatique_eleves.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Import_automatique_eleves.mp4",
    "Actualisation_equipe_classes.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Actualisation_equipe_classes.mp4",
    "Gestion_inventaire_EPI_photos.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Gestion_inventaire_EPI_photos.mp4",
    "Controle_dates_CM_CAHPN.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Controle_dates_CM_CAHPN.mp4",
    "Export_zip_documents_certificatifs.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Export_zip_documents_certificatifs.mp4",
    "Evolution_et_fermeture_SSS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Evolution_et_fermeture_SSS.mp4",
    "Signature_chef_etablissement_SSS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Signature_chef_etablissement_SSS.mp4",
    "Export_profs_externes_cyclades.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Export_profs_externes_cyclades.mp4",
}

# ======================================================================
# 1. CONFIGURATION DE L'APPLICATION
# ======================================================================
st.set_page_config(
    page_title="Hub IA - EPS",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ======================================================================
# 2. GESTION DE LA MÉMOIRE ET DU COMPTEUR DE VISITES
# ======================================================================
if "messages_hub" not in st.session_state:
    st.session_state.messages_hub = []
if "active_module" not in st.session_state:
    st.session_state.active_module = "ipack"
if "niveau_actif_form" not in st.session_state:
    st.session_state.niveau_actif_form = "Collège (DNB)"


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
# 3. INTERFACE GRAPHIQUE ET STYLES CSS
# ======================================================================
img_gauche = "image_7.png"
img_eps = "image_6.png"
img_droite = "image_5.png"
img_fond = "image_8.png"

github_url = f"https://raw.githubusercontent.com/{st.secrets.get('GITHUB_USERNAME', '')}/{st.secrets.get('GITHUB_REPO', '')}/main/"

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
    
    .stApp {{ background-image: url('{github_url}{img_fond}') !important; background-size: cover !important; background-attachment: fixed !important; }}
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
        padding: 8px 10px; 
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2); 
    }}
    .column-title-top .instruction {{ 
        font-size: 11px !important; 
        font-weight: 500; 
        text-transform: uppercase; 
        color: #94A3B8 !important; 
        display: block; 
    }}
    .column-title-top .mode-actuel {{ 
        font-size: 14px !important; 
        font-weight: 700; 
        color: #FFFFFF !important; 
        display: block; 
    }}

    button[kind="secondary"] {{ 
        background-color: #1E293B !important; 
        color: #94A3B8 !important; 
        border: 1px solid #334155 !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
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
        box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.4) !important; 
        font-weight: 700 !important; 
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

    /* Injection automatique du titre turquoise tout en haut de la bannière des choix */
    div[data-testid="stRadio"]::before {{
        content: "🎯 SÉLECTIONNEZ VOTRE PUBLIC CIBLE (Pour ajuster la réponse)";
        display: block;
        color: #38BDF8 !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        margin-bottom: 8px !important;
    }}

    div[data-testid="stRadio"] label p, 
    div[data-testid="stRadio"] label span, 
    div[data-testid="stRadio"] label {{
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
    for fp in ["data/examens/memoire_examens_santorin.txt", "ipack.txt"]:
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
    for dossier in ["data/examens", "data/ipack", "data/textes"]:
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
                " du second degré."
            ),
            metadata={
                "title": "Légifrance",
                "url": "https://www.legifrance.gouv.fr/",
            },
        )
    ]
    docs_textes.extend(charger_dossier_txt_securise("data/textes"))
    docs_textes.extend(charger_consignes_ipack())
    return VectorStoreIndex.from_documents(docs_textes).as_retriever(
        similarity_top_k=8
    )


timestamp_fichier = obtenir_cle_fichier()
retriever_santorin = initialiser_base_santorin(timestamp_fichier)
retriever_ipack = initialiser_base_ipack(timestamp_fichier)
retriever_textes = initialiser_base_textes(timestamp_fichier)


# ======================================================================
# 🔔 VEILLE AUTOMATIQUE TAVILY
# ======================================================================
def verifier_veille_dec(tavily_client):
    if not tavily_client:
        return

    fichier_suivi = "dernier_check_dec.txt"
    fichier_date_alerte = "date_alerte_dec.txt"
    mois_actuel = datetime.datetime.now().strftime("%Y-%m")
    aujourdhui = datetime.date.today()

    if os.path.exists(fichier_date_alerte):
        try:
            with open(fichier_date_alerte, "r", encoding="utf-8") as f:
                date_alerte_str = f.read().strip()
                date_alerte = datetime.datetime.strptime(
                    date_alerte_str, "%Y-%m-%d"
                ).date()

                if (aujourdhui - date_alerte).days <= 7:
                    st.session_state.date_veille_dec = date_alerte.strftime("%d/%m/%Y")
                    st.session_state.alerte_veille_dec = (
                        "🔔 Veille réglementaire mensuelle : De nouvelles informations ou"
                        " mises à jour ont été détectées sur les sites officiels."
                    )
                    return
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
        try:
            recherche_veille = tavily_client.search(
                query=(
                    "circulaire examen EPS DEC Aix-Marseille mise à jour"
                    f" {datetime.datetime.now().year}"
                ),
                max_results=2,
                include_domains=["eduscol.education.fr", "education.gouv.fr"],
            )

            with open(fichier_suivi, "w", encoding="utf-8") as f:
                f.write(mois_actuel)

            if recherche_veille.get("results"):
                with open(fichier_date_alerte, "w", encoding="utf-8") as f:
                    f.write(aujourdhui.strftime("%Y-%m-%d"))

                st.session_state.date_veille_dec = aujourdhui.strftime("%d/%m/%Y")
                st.session_state.alerte_veille_dec = (
                    "🔔 Veille réglementaire mensuelle : De nouvelles informations ou"
                    " mises à jour ont été détectées sur les portails officiels."
                )
        except Exception:
            pass


verifier_veille_dec(tavily_client)

# ======================================================================
# 5. BANDEAU SUPÉRIEUR
# ======================================================================
st.markdown(
    f"""
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
            <img src="{github_url}{img_droite}" class="img-zoomable" height="55">
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

if "alerte_veille_dec" in st.session_state:
    date_alerte = st.session_state.get("date_veille_dec", "Récemment")
    st.markdown(
        f"""
    <div style="background-color: rgba(15, 23, 42, 0.85) !important; backdrop-filter: blur(12px); border-left: 6px solid #FFB020; padding: 14px 18px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);">
        <div style="display: flex; align-items: flex-start; gap: 12px;">
            <span style="font-size: 22px; margin-top: 2px;">🚨</span>
            <div style="width: 100%;">
                <strong style="color: #FFB020 !important; font-size: 14px; text-transform: uppercase;">Veille réglementaire mensuelle — Détectée le {date_alerte}</strong>
                <div style="color: #F1F5F9 !important; font-size: 13.5px; margin-top: 6px;">
                    De nouvelles informations ou mises à jour ont été détectées sur les portails officiels.
                </div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ======================================================================
# 6. EN-TÊTE DU TABLEAU DE BORD & BOUTONS DE CONTEXTE (3 ONGLETS)
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
    "🛠️ Mode Actif : Assistance Technique iPackEPS (Gestion du CCF & Inaptitudes)",
)
st.markdown(
    '<div class="column-title-top"><span class="instruction">⚙️ Étape 1 :'
    " Choisissez le contexte de votre question</span><span"
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
        st.session_state.messages_hub = []
        st.rerun()

# ======================================================================
# 7. ZONE DE SAISIE INTÉGRÉE & SÉLECTEUR DE NIVEAU
# ======================================================================
niveau_scolaire = st.radio(
    "Niveau",
    ["Collège (DNB)", "Lycée Général & Techno", "Lycée Pro / CAP"],
    horizontal=True,
    label_visibility="collapsed",
    key="niveau_actif_form",
)

prompt = None
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
# 8. BANNIÈRES D'AVERTISSEMENT OU D'ORIENTATION
# ======================================================================
if st.session_state.active_module == "textes":
    st.markdown(
        """
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-top: 5px; margin-bottom: 12px;">
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
    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-top: 5px; margin-bottom: 12px;">
        <div style="color: #38BDF8; font-weight: 800; font-size: 14px; text-align: center; margin-bottom: 12px;">🎯 OÙ POSER VOTRE QUESTION ?</div>
        <div style="display: flex; gap: 20px; color: #FCD34D; font-size: 13px;">
            <div style="flex: 1; border-right: 1px solid #334155; padding-right: 20px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">🛠️ Menu iPackEPS (Toute l'année)</strong><br>
                <span>Configuration modules, classes, élèves, groupes, inaptitudes, dispenses...</span>
            </div>
            <div style="flex: 1; padding-left: 5px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">📊 Menu Examens &amp; Santorin (Fin d'année)</strong><br>
                <span>Remontée officielle Bac/DNB, correction numérique, arbitrages CAHPN, blocs de lots.</span>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

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

        texte_brut = ""
        extraits_doc = ""
        extraits_web = ""
        badge, color_card = "INFORMATION", "general-card"

        onglets_noms = {
            "ipack": "l'onglet Assistance Technique iPackEPS (Gestion du CCF)",
            "examens": "l'onglet Réglementation Examens & Santorin (Copies Numérisées)",
            "textes": "l'onglet Sécurité & Responsabilité Juridique (Textes Officiels)",
        }
        contexte_choisi_nom = onglets_noms.get(mode, "un onglet de l'application")

        verites_terrain_pierre = ""
        try:
            for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
                if os.path.exists(fp):
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        verites_terrain_pierre += f"\n--- REGLES DE PIERRE ---\n" + f.read() + "\n"
        except Exception:
            pass

        est_college = any(w in p_low for w in ["6e", "5e", "4e", "3e", "collège", "college"])

        est_saisir_notes = (
            any(w in p_low for w in ["saisir", "saisie", "noter", "note", "notes", "carnet"]) 
            and any(w in p_low for w in ["note", "notes"])
            and not any(w in p_low for w in ["santorin", "cyclades"])
            and mode != "examens" 
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

        est_deplacer_candidat = (
            mode != "textes"
            and any(w in p_low for w in ["déplacer", "deplacer", "déplacement", "deplacement"])
            and any(w in p_low for w in ["candidat", "élève", "eleve"])
            and "lot" in p_low
        )

        # ⚡ DÉTECTION PROGRAMMATIQUE : EXCLUSION DISCIPLINAIRE (CCF)
        est_exclusion = (
            mode != "textes"
            and any(w in p_low for w in ["exclusion", "conseil de discipline", "exclu", "sanction"])
            and any(w in p_low for w in ["ccf", "épreuve", "epreuve", "note", "rattrapage"])
        )

        # ⚡ DÉTECTION PROGRAMMATIQUE : PROBLÈME IMPORT SIÈCLE / AUCUN ÉLÈVE (RENTRÉE)
        est_aucun_eleve = (
            mode == "ipack"
            and any(w in p_low for w in ["aucun élève", "aucun eleve", "pas d'élève", "pas d'eleve", "siècle", "siecle", "arena"])
        )

        # ⚡ DÉTECTION PROGRAMMATIQUE : DÉPÔT RÉFÉRENTIELS & APSA (RENTRÉE)
        est_referentiels_rentree = (
            mode == "ipack"
            and any(w in p_low for w in ["référentiel", "referentiel", "apsa certificative", "déclarer apsa", "dépôt référentiel"])
        )

        est_sss = any(w in p_low for w in ["sss", "section sportive", "reconduction", "fermeture sss"])

        est_cas_direct = (
            (mode != "textes") 
            and (
                est_date 
                or est_sujet_secours 
                or est_cap_3epreuves 
                or est_deplacer_candidat
                or est_saisir_notes
                or est_exclusion
                or est_aucun_eleve
                or est_referentiels_rentree
            )
        ) or est_tasa

        if openai_api_key and not est_cas_direct:
            try:
                if mode == "examens":
                    nodes_bruts = retriever_santorin.retrieve(prompt)
                    for n in nodes_bruts:
                        extraits_doc += f"{n.node.text}\n\n"
                elif mode == "ipack":
                    nodes_bruts = retriever_ipack.retrieve(prompt)
                    for n in nodes_bruts:
                        extraits_doc += f"{n.node.text}\n\n"
                elif mode == "textes":
                    nodes_bruts = retriever_textes.retrieve(prompt)
                    for n in nodes_bruts:
                        extraits_doc += f"{n.node.text}\n\n"
            except Exception:
                pass

        if tavily_client and mode == "textes" and not est_cas_direct:
            try:
                response_tavily = tavily_client.search(
                    query=prompt,
                    max_results=3,
                    include_domains=["legifrance.gouv.fr", "eduscol.education.fr", "education.gouv.fr"],
                )
                for res in response_tavily.get("results", []):
                    extraits_web += f"Source Officielle Web ({res.get('title')}) - {res.get('url')}:\n{res.get('content')}\n\n"
            except Exception:
                pass

        # ROUTAGE DES CAS DIRECTS (ZONE 9)
        if est_saisir_notes:
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
  <li><strong>Réglementation stricte :</strong> En CAP, le CCF repose <strong>STRICTEMENT sur 2 épreuves</strong> issues de 2 champs d'apprentissage distincts.</li>
  <li><strong>Bloqueur Santorin :</strong> Toute saisie d'une 3ᵉ note est bloquée automatiquement par l'interface. Nettoyez le protocole dans iPackEPS.</li>
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

        else:
            if mode == "examens":
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            elif mode == "ipack":
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
            else:
                badge, color_card = "⚖️ SÉCURITÉ & CADRE JURIDIQUE", "securite-card"

        directive_onglet = ""
        if mode == "textes":
            directive_onglet = """
3. ⚖️ SPÉCIFICITÉ ABSOLUE ONGLET SÉCURITÉ & JURIDIQUE :
   - Détermine si la situation relève d'un accident survenu, d'une responsabilité ou d'un cadre réglementaire amont.
   - INTERDICTION FORMELLE ET ABSOLUE de mentionner le moindre tutoriel vidéo, logiciel, ou fichier technique iPackEPS/Santorin (ce module traite exclusivement de droit, de jurisprudences et de textes officiels).
   - CONFLIT HIÉRARCHIQUE / PRESSION : Rappeler les voies de recours et la saisine des autorités compétentes (IA-IPR EPS).
"""
        elif mode == "examens":
            directive_onglet = "3. 📊 SPÉCIFICITÉS EXAMENS & SANTORIN : Traite précisément le problème d'examen (Bac, CAP, dispenses, CAHPN)."
        elif mode == "ipack":
            directive_onglet = "3. 🛠️ ASSISTANCE TECHNIQUE iPACKEPS : Donne la procédure technique exacte en précisant les menus réels ([Dossiers] > [Dossier EPS] > ...)."

        contexte_complet_ia = f"""
CONTEXTE DOCUMENTAIRE OFFICIEL LOCAL :
{extraits_doc}

SOURCES OFFICIELLES WEB :
{extraits_web}

{verites_terrain_pierre}
"""

        # 🚨 PROMPT SYSTÈME AVEC TON SOCLE DE SÉCURITÉ INTÉGRÉ EXACTEMENT EN 8 POINTS
        consigne_ia = f"""Tu es l'assistant IA officiel en Éducation Physique et Sportive (EPS), examens et réglementation institutionnelle.

    🎯 PUBLIC CIBLE SÉLECTIONNÉ PAR L'UTILISATEUR : {niveau_actuel_form}
    (Tu dois impérativement adapter ta réponse, tes références réglementaires et ton analyse en fonction de ce niveau précis).

    🚨 [ RÈGLE ZÉRO - PRIORITÉ ABSOLUE & ANTIDOTE AUX RÉPONSES BATEAUX ] :
    Dès qu'un utilisateur signale un blocage, un rejet de protocole, un message d'erreur ou une impossibilité de saisir des notes (Santorin / Cyclades) :
    - INTERDICTION FORMELLE DE DIRE "contactez la direction" ou "vérifiez vos notes" si la cause est un blocage structurel ou réglementaire.
    - Tu dois IMMÉDIATEMENT analyser la contradiction mathématique de la réglementation (ex: CAP = 2 épreuves max) et donner la procédure technique exacte de nettoyage dans iPackEPS / Cyclades.

    🚨 SOCLE DE SÉCURITÉ ET INVARIANTS INSTITUTIONNELS (RÈGLES ABSOLUES - ZÉRO TOLÉRANCE) :
    1. PRINCIPE DE RÉALITÉ DES PUBLICS :
    - Collège (6e, 5e, 4e, 3e, y compris 3e prépa-métiers, SEGPA, ULIS, peu importe l'établissement d'hébergement) : AUCUN CCF, AUCUNE APSA certificative, AUCUN protocole Santorin ou Cyclades. Évaluation exclusivement par contrôle continu et LSU (Socle commun). Si l'utilisateur évoque une 3e (même en Lycée Pro), rejette l'export Cyclades/CCF et impose le LSU.
    - Lycée (Terminale Bac GT, Bac Pro, CAP) : Cadre réglementaire strict du CCF.
    2. INTERDICTION DES HÉRÉSIES PÉDAGOGIQUES :
    - Les APSA combinées (ex: Football-Musculation) sont STRICTEMENT réservées aux Sections Sportives Scolaires (SSS). Interdiction formelle d'en proposer pour une classe ordinaire.
    3. INCOMPÉTENCE HIERARCHIQUE DES CHEFS D'ÉTABLISSEMENT :
    - Le chef d'établissement n'a AUCUNE autorité ni compétence sur les jurys de bac, la modification des notes d'examens nationaux ou la gestion des tiers correcteurs (tierce correction). Tout litige relève de la Division des Examens et Concours (DEC).
    4. GESTION DES FAUSSES PRÉMISSES :
    - Si un utilisateur demande une action impossible (CCF en collège, APSA combinée en classe normale, validation de correcteur de bac par le proviseur), rectifie la prémisse dès la première phrase, rappelle la règle réglementaire exacte, et donne la bonne marche à suivre. N'active jamais la règle du hors-sujet global pour une question d'EPS erronée.
    5. CLOISONNEMENT STRICT DES ACTEURS INSTITUTIONNELS :
    - Dans l'onglet "Sécurité & Cadre Juridique", INTERDICTION ABSOLUE de mentionner la DEC (Division des Examens et Concours), que ce soit pour dire de la contacter ou de ne pas la contacter. La DEC n'a aucun rôle dans les accidents, la responsabilité ou les sorties scolaires (seuls le Chef d'établissement, le Recteur et la DSDEN sont compétents).
    6. GESTION OPÉRATIONNELLE DES LOTS ET VERROUILLAGES SUR SANTORIN (HABILITATION & CADENAS) :
    - Un enseignant n'a PAS les droits de déverrouiller un lot de copies numériques depuis son profil de correcteur.
    - La manipulation relève EXCLUSIVEMENT du Chef d'établissement depuis sa console de direction sur Santorin (Menu "Liste des lots" -> clic direct sur le cadenas pour basculer de fermé à ouvert).
    - INTERDICTION FORMELLE ET ABSOLUE de mentionner la DEC (Division des Examens et Concours) pour ce cas. C'est une action locale et autonome de l'établissement. L'assistant doit explicitement dire à l'enseignant de se rapprocher de sa direction.
    7. GESTION STRICTE DES INAPTITUDES MÉDICALES DE DERNIÈRE MINUTE (INTERDICTION DU "DISP" HÂTIF) :
    - Toute blessure ou inaptitude médicale survenant à l'approche ou le jour d'une épreuve certificative (CCF) unique est une INAPTITUDE TEMPORAIRE.
    - Il est FORMELLEMENT INTERDIT d'attribuer immédiatement le statut "DISP" de dernière minute : l'organisation d'une ÉPREUVE DIFFÉRÉE est obligatoire.
    - ⚠️ EXCEPTION VITALE (PROFIL NOTE UNIQUE / DISPENSES MULTIPLES) : Cette règle de l'épreuve différée de dernière minute ne s'applique PAS lorsqu'un dossier présente un profil de dispenses multiples combinées à une note unique (ex: DI + DI + 14). Dans ce cas, l'élève a raté deux épreuves en amont (couvertes par des DI officiels) et a une note valide sur la troisième : on applique strictement la procédure de la note unique (saisir les deux statuts DISP/DI, saisir la note réelle, et rédiger le commentaire obligatoire pour la CAHPN).
    - 🛡️ DÉFINITION OFFICIELLE : CAHPN / CAHN = Commission Académique d'Harmonisation et de Proposition de Notes (interdiction stricte de toute autre interprétation).
    8. 🧠 FLEXIBILITÉ CONTEXTUELLE & ARBITRAGE INTELLIGENT :
    - L'utilisateur a posé sa question dans {contexte_choisi_nom}. Cependant, analyse toujours en priorité la nature intrinsèque de la question (par exemple : si la question concerne le collège ou le DNB, elle relève du contrôle continu et du LSU, même si l'onglet actif est par erreur celui des examens/lycée).
    - En cas de décalage entre l'onglet sélectionné et le domaine réel de la question, ne t'enferme pas aveuglément dans l'erreur de l'onglet : recadre le sujet avec souplesse et pédagogie, sans blocage.
    9. 📜 OBLIGATION D'ANCRAGE JURIDIQUE & CITATION DES TEXTES :
    - Pour toute question relevant de la responsabilité, de la discipline, des accidents ou du cadre réglementaire (notamment dans l'onglet Sécurité & Cadre Juridique), tu DOIS obligatoirement citer les sources textuelles exactes : articles précis du Code de l'éducation, du Code pénal, du Code civil, ou circulaires de référence.
    - Interdiction absolue de rédiger une réponse de sens commun ou de simple bon sens : chaque règle énoncée doit être liée à son fondement juridique institutionnel.
{contexte_complet_ia}

QUESTION DE L'UTILISATEUR :
{prompt}

MÉTHODE D'ANALYSE & RÈGLES DE RÉPONSE :
1. ANALYSE DU PÉRIMÈTRE : Réponds avec précision, clarté et rigueur institutionnelle.
2. STRUCTURE & MISE EN PAGE :
    - Rends une réponse bien structurée et claire.
    - Utilise des listes à puces ou ordonnées HTML propres (`<ul>`, `<li>`).
{directive_onglet}
3. 📺 TUTO VIDÉO (DÉCLENCHEURS STRICTS) :
    - Pour les manipulations techniques, termine par le fichier associé exact parmi la liste officielle (import_eleves_pronote.mp4, Configuration_classes_import_eleves.mp4, affecter_eleves_dans_groupes.mp4, Generer_importer_fichier_groupes_cyclades.mp4, verification_affectation_protocoles_cyclades.mp4, creer_convocations_enseignants.mp4, Distribution_lots_santorin.mp4, Distribution_manuelle_lots_santorin.mp4, Saisie_notes_Santorin.mp4, Verrouiller_lot_santorin.mp4, Deverrouiller_lots_santorin.mp4, Ajouter_evaluateur_lot_santorin.mp4, Depot_referentiels_iPackEPS.mp4, Saisie_protocoles_iPackEPS.mp4, Protocoles_adaptes_iPackEPS.mp4, Extraction_notes_Santorin.mp4, Import_documents_glisser_deposer.mp4, Import_automatique_eleves.mp4, Actualisation_equipe_classes.mp4, Gestion_inventaire_EPI_photos.mp4, Controle_dates_CM_CAHPN.mp4, Export_zip_documents_certificatifs.mp4, Export_profs_externes_cyclades.mp4).
"""

        if not est_cas_direct:
            try:
                response = Settings.llm.complete(consigne_ia)
                texte_brut = response.text
            except Exception as e:
                texte_brut = f"Erreur de traitement IA : {str(e)}"

        if est_sss and "Evolution_et_fermeture_SSS.mp4" not in texte_brut:
            texte_brut += "\n\n📺 Tutoriel associé : Evolution_et_fermeture_SSS.mp4"

        texte_brut = texte_brut.replace("```html", "").replace("```HTML", "").replace("```", "")

        if mode == "textes" or est_dnb:
            texte_brut = re.sub(r"📺\s*Tutoriel\s+associé\s*:\s*.*", "", texte_brut, flags=re.IGNORECASE)

        texte_brut = re.sub(
            r"📺\s*Tutoriel\s+associé\s*:\s*(aucun|aucun\.?|none|non|\/|-|\s*)*$",
            "",
            texte_brut,
            flags=re.IGNORECASE | re.MULTILINE,
        )

        texte_brut = re.sub(
            r"(Article\s+\d+[-–\w]*|Loi\s+du\s+\d+\s+\w+\s+\d+|RGPD|Code\s+de l\'éducation)",
            r'<span class="law-highlight">\1</span>',
            texte_brut,
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

        footer_assistance = ""
        if mode in ["ipack", "examens"]:
            footer_assistance = (
                "<div style='margin-top: 14px; padding-top: 8px; border-top: 1px dashed rgba(255,255,255,0.15); font-size: 12.5px; color: #CBD5E1;'>Bien entendu si ma réponse ne vous a pas aidé vous pouvez toujours contacter l'assistance <a href='mailto:ipackeps@ac-aix-marseille.fr' style='color: #38BDF8 !important; text-decoration: underline;'>ipackeps@ac-aix-marseille.fr</a></div>"
            )

        formatted_answer = (
            f'<div class="{color_card}">{phrase_contexte}<strong>{badge} :</strong><br>{texte_final}{footer_assistance}</div>'
        )

        log_interaction(prompt, texte_brut)

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

if "messages_hub" in st.session_state and st.session_state.messages_hub:
    st.markdown('<div style="margin-top: 15px;">', unsafe_allow_html=True)
    for m in st.session_state.messages_hub:
        with st.chat_message(m["role"]):
            if m.get("type") == "video":
                st.video(m["content"])
            else:
                st.markdown(m["content"], unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
