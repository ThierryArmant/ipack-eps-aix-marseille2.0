import datetime
import os
import re
import smtplib
import requests  # 👈 Ajouté ici
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
        # Affiche l'erreur dans la console si le réseau bloque
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
    # Tutos historiques / examens :
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
    # Tutos amont & cas complexes iPackEPS :
    "Depot_referentiels_iPackEPS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Depot_referentiels_iPackEPS.mp4",
    "Saisie_protocoles_iPackEPS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Saisie_protocoles_iPackEPS.mp4",
    "Protocoles_adaptes_iPackEPS.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Protocoles_adaptes_iPackEPS.mp4",
    "Extraction_notes_Santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Extraction_notes_Santorin.mp4",
    # 🆕 Nouveaux tutos version 2026.2.x :
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
        background-color: rgba(15, 23, 42, 0.9) !important; 
        color: #94A3B8 !important; 
        border: 1px solid rgba(255,255,255,0.05) !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
        height: 55px !important; 
        display: inline-flex !important; 
        align-items: center !important; 
        justify-content: center !important; 
        text-align: center !important; 
    }}

    button[kind="primary"] {{ 
        background-color: rgba(16, 185, 129, 0.85) !important; 
        color: #FFFFFF !important; 
        border: 1px solid #10B981 !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
        box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.6) !important; 
        font-weight: 700 !important; 
        height: 55px !important; 
        display: inline-flex !important; 
        align-items: center !important; 
        justify-content: center !important; 
        text-align: center !important; 
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

    /* STYLE AÉRÉ DES LISTES PAS À PAS */
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

    /* FORCER LE TEXTE DU FORMULAIRE EN BLANC ÉCLATANT */
    div[data-testid="stForm"] label p, div[data-testid="stForm"] span, div[data-testid="stForm"] label {{
        color: #FFFFFF !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
    }}

    /* ZOOM FLUIDE IMAGE 5 */
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
    # Surveillance des fichiers de consignes principaux
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
    # Charge la mémoire souveraine spécifique aux examens & Santorin
    docs_santorin.extend(charger_consignes_examens())
    
    # 🌟 AJOUT : On injecte aussi ipack.txt pour que les correctifs de nuit profitent à Santorin !
    docs_santorin.extend(charger_consignes_ipack())
    
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
# 🔔 VEILLE AUTOMATIQUE TAVILY (Avec gestion de la date et expiration 7 jours)
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
                        " mises à jour ont été détectées sur les sites officiels"
                        " concernant les examens ou l'EPS. Pensez à vérifier si une"
                        " nouvelle circulaire DEC a été publiée."
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
                    " mises à jour ont été détectées sur les sites officiels"
                    " concernant les examens ou l'EPS. Pensez à vérifier si une"
                    " nouvelle circulaire DEC a été publiée."
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
    liens = st.session_state.get("liens_veille_dec", [])

    liens_html = ""
    for item in liens:
        titre = item.get("title", "Document officiel")
        url = item.get("url", "#")
        liens_html += f'<li><a href="{url}" target="_blank" style="color: #60A5FA; text-decoration: underline; font-weight: 500;">{titre}</a></li>'

    if not liens_html:
        liens_html = (
            "<li>Aucun lien direct extrait, consultez les portails ci-dessous.</li>"
        )

    st.markdown(
        f"""
    <div style="background-color: rgba(15, 23, 42, 0.85) !important; backdrop-filter: blur(12px); border-left: 6px solid #FFB020; padding: 14px 18px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);">
        <div style="display: flex; align-items: flex-start; gap: 12px;">
            <span style="font-size: 22px; margin-top: 2px;">🚨</span>
            <div style="width: 100%;">
                <strong style="color: #FFB020 !important; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Veille réglementaire mensuelle — Détectée le {date_alerte}</strong>
                <div style="color: #F1F5F9 !important; font-size: 13.5px; margin-top: 6px; line-height: 1.5;">
                    De nouvelles informations ou mises à jour ont été détectées. 
                    <div style="margin-top: 4px; font-weight: 600; color: #F8FAFC;">Documents ciblés :</div>
                    <ul style="margin: 4px 0 8px 20px; padding: 0;">
                        {liens_html}
                    </ul>
                    <div style="margin-top: 8px; padding-top: 6px; border-top: 1px solid rgba(255, 255, 255, 0.1); font-size: 13px;">
                        🌐 <b>Accès rapides aux portails :</b> 
                        <a href="https://eduscol.education.fr" target="_blank" style="color: #38BDF8; text-decoration: underline; margin-right: 8px;">Eduscol</a> | 
                        <a href="https://www.education.gouv.fr" target="_blank" style="color: #38BDF8; text-decoration: underline; margin-left: 8px;">Ministère de l'Éducation Nationale</a>
                    </div>
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
prompt = None
with st.form(key="form_question_hub", clear_on_submit=True):
    st.markdown(
        "<div style='color: #38BDF8; font-weight: 700; font-size: 13px; margin-bottom: 2px;'>🎯 ÉTAPE 2 : SÉLECTIONNEZ VOTRE 🎓 PUBLIC CIBLE (Pour permettre une réponse ajustée)</div>",
        unsafe_allow_html=True
    )
    niveau_scolaire = st.radio(
        "Niveau",
        ["Collège (DNB)", "Lycée Général & Techno", "Lycée Pro / CAP"],
        horizontal=True,
        label_visibility="collapsed",
    )

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
            "🚀 Poser", use_container_width=True, type="primary"
        )

    if bouton_envoyer and prompt_brut.strip():
        prompt = prompt_brut.strip()
        st.session_state.niveau_actif_form = niveau_scolaire
# ======================================================================
# 8. BANNIÈRES D'AVERTISSEMENT OU D'ORIENTATION (PLACÉES SOUS LA SAISIE)
# ======================================================================
if st.session_state.active_module == "textes":
    st.markdown(
        """
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-top: 5px; margin-bottom: 12px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            ⚠️ <strong>Avertissement –</strong> Bien que basées sur les textes officiels, ces réponses ne remplacent pas les autorités académiques. En cas de doute juridique ou de sinistre, contactez impérativement : <strong>Votre Chef d'établissement, votre Secrétariat d'examen, ou votre IA-IPR.</strong>
        </span>
    </div>
    """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-top: 5px; margin-bottom: 12px; line-height: 1.5;">
        <div style="color: #38BDF8; font-weight: 800; font-size: 14px; text-align: center; margin-bottom: 12px; letter-spacing: 0.5px;">🎯 OÙ POSER VOTRE QUESTION ?</div>
        <div style="display: flex; gap: 20px; color: #FCD34D; font-size: 13px;">
            <div style="flex: 1; border-right: 1px solid #334155; padding-right: 20px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">🛠️ Menu iPackEPS (Toute l'année)</strong><br>
                <span style="color: #FCD34D !important;">Technique de terrain : configuration modules professeurs, classes, élèves, groupes, APPN, SSS...</span><br>
                <div style="margin-top: 8px; padding: 5px 8px; background-color: rgba(248, 113, 113, 0.15); border-left: 3px solid #F87171; border-radius: 4px;">
                    <span style="color: #F87171 !important; font-weight: 800;">⚠️ IMPORTANT INAPTITUDES :</span><br>
                    <span style="color: #FFFFFF !important; font-size: 12px;">Toutes les questions sur les certificats médicaux, dispenses et saisies d'inaptitude se posent TOUJOURS ici !</span>
                </div>
            </div>
            <div style="flex: 1; padding-left: 5px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">📊 Menu Examens & Santorin (Fin d'année)</strong><br>
                <span style="color: #FCD34D !important;">Administration des examens : remontée officielle du Bac/DNB, correction numérique sur Esterel/Arena, arbitrages de la CAHPN.</span><br>
                <div style="margin-top: 8px; padding: 5px 8px; background-color: rgba(56, 189, 248, 0.15); border-left: 3px solid #38BDF8; border-radius: 4px;">
                    <span style="color: #38BDF8 !important; font-weight: 800;">💡 Déblocage situation complexe &amp; Besoin d'informations :</span><br>
                    <span style="color: #FFFFFF !important; font-size: 12px;">Boutons grisés, lots bloqués ou questions de calcul de notes ? L'IA s'appuie sur les fiches de la DEC pour vous guider sereinement.</span>
                </div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ======================================================================
# 9. TRAITEMENT RAG & FLUX DE MESSAGES (VERSION DÉFINITIVE & SÉCURISÉE)
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

        texte_brut = ""
        extraits_doc = ""
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

        # ⚡ DÉTECTIONS D'INVARIANTS INSTITUTIONNELS CRITIQUES (EN DUR)
        est_college = any(w in p_low for w in ["6e", "5e", "4e", "3e", "collège", "college"])

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
                    "lot", "lots", "examen", "examens", "bac", "cap", "brevet", 
                    "mayotte", "academie", "académie"
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

        est_sss = any(w in p_low for w in ["sss", "section sportive", "reconduction", "fermeture sss"])

        est_cas_direct = (
            (mode != "textes") 
            and (
                est_date 
                or est_sujet_secours 
                or est_cap_3epreuves 
                or est_deplacer_candidat
            )
        ) or est_tasa

        # 🚀 RECHERCHE RAG LOCALE (SI PAS DE CAS DIRECT)
        if openai_api_key and not est_cas_direct:
            try:
                if mode == "examens":
                    for n in retriever_santorin.retrieve(prompt):
                        extraits_doc += f"{n.node.text}\n\n"
                elif mode == "ipack":
                    for n in retriever_ipack.retrieve(prompt):
                        extraits_doc += f"{n.node.text}\n\n"
                elif mode == "textes":
                    for n in retriever_textes.retrieve(prompt):
                        extraits_doc += f"{n.node.text}\n\n"
            except Exception:
                pass

        # 🎯 TRAITEMENT DES INVARIANTS EN DUR
        if est_date:
            texte_brut = """<h3>📅 CALENDRIER OFFICIEL DES EXAMENS & SAISIE DES NOTES</h3>
<ul>
  <li><strong>Principe réglementaire :</strong> Les dates butoirs de saisie des notes, de remontée des résultats et de clôture des serveurs (Santorin / Cyclades) sont fixées annuellement par le calendrier officiel publié au <strong>Bulletin Officiel (BO)</strong> et précisées par la circulaire de la Division des Examens et Concours (DEC) de votre académie.</li>
  <li>👉 <strong>Consultez le calendrier officiel</strong> publié par votre académie de rattachement pour toute confirmation ou mise à jour.</li>
</ul>"""
            badge, color_card = "📅 CALENDRIER OFFICIEL", ("santorin-card" if mode == "examens" else "general-card")

        elif est_tasa:
            texte_brut = """<h3>🏊 CADRE RÉGLEMENTAIRE - TEST D'APTITUDE AU SAUVETAGE AQUATIQUE (TASA)</h3>
<ul>
  <li><strong>Texte de référence officiel :</strong> Circulaire en vigueur.</li>
  <li><strong>Obligation de qualification :</strong> Obligatoire pour tout enseignant d'EPS (concours, contractuels, détachements) dès la nomination.</li>
  <li><strong>Protocole technique (100m en continu) :</strong> Respect strict des exigences réglementaires (nage libre, apnées et recherche de mannequin).</li>
  <li><strong>Tenue stricte :</strong> Maillot de bain uniquement (combinaison, lunettes et pince-nez formellement interdits).</li>
</ul>"""
            badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

        elif est_sujet_secours:
            texte_brut = """<h3>⚠️ AUCUN SUJET ÉCRIT DE SECOURS EN EPS</h3>
<ul>
  <li><strong>Règle nationale absolue :</strong> En EPS (CCF ou ponctuel), il n'existe <strong>aucun sujet écrit ou papier</strong> à imprimer sur iPackEPS, Santorin ou Cyclades. L'évaluation est 100 % pratique.</li>
  <li><strong>Élève absent justifié (ABJ) :</strong> Organisation obligatoire d'une <strong>Épreuve de substitution</strong> (rattrapage de l'épreuve motrice sur le terrain) avant la fermeture des serveurs académiques.</li>
  <li><strong>Élève inapte médicalement :</strong> Saisie du statut <strong>[DISP]</strong> sur présentation d'un certificat médical officiel conforme.</li>
</ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif est_cap_3epreuves:
            texte_brut = """<h3>⚠️ ALERTE : PROTOCOLE CAP STRICT À 2 ÉPREUVES</h3>
<ul>
  <li><strong>Réglementation stricte :</strong> En CAP, le CCF repose <strong>STRICTEMENT sur 2 épreuves</strong> issues de 2 champs d'apprentissage distincts.</li>
  <li><strong>Bloqueur Santorin :</strong> Toute saisie d'une 3ᵉ note est bloquée par l'interface et entraînera le rejet immédiat du protocole par la CAHPN.</li>
  <li><strong>Procédure :</strong> Configurez votre classe en mode groupe sur iPackEPS et supprimez la 3ᵉ épreuve excédentaire.</li>
</ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif est_deplacer_candidat:
            texte_brut = """<h3>📋 DÉPLACEMENT D'UN CANDIDAT OU RÉAFFECTATION DE LOT SUR SANTORIN</h3>
<ul>
  <li><strong>Distinction clé :</strong> Ne pas confondre la « réaffectation d'un lot » entier et le « déplacement d'un candidat » d'un lot vers un autre.</li>
  <li><strong>Règle absolue :</strong> L'enseignant n'a aucun droit ni possibilité de déplacer lui-même un candidat d'un lot à un autre sur Santorin.</li>
  <li><strong>Procédure :</strong> Corrigé via <strong>Cyclades</strong> pour l'affectation ou manipulation directe du correcteur dans Santorin.</li>
</ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        else:
            if mode == "examens":
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            elif mode == "ipack":
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
            else:
                badge, color_card = "⚖️ SÉCURITÉ & CADRE JURIDIQUE", "securite-card"

            contexte_complet_ia = f"""
CONTEXTE DOCUMENTAIRE OFFICIEL LOCAL :
{extraits_doc}

{verites_terrain_pierre}
"""
            niveau_actuel_form = st.session_state.get("niveau_actif_form", "Collège (DNB)")

            consigne_ia = f"""Tu es un expert institutionnel chevronné, type IA-IPR EPS, rigoureux et pragmatique.
NIVEAU SCOLAIRE CIBLÉ : {niveau_actuel_form}

RÈGLES DE LECTURE INTELLIGENTE & SÉCURITÉ :
1. ANALYSE SÉMANTIQUE FINE : Fais preuve de discernement. Si l'utilisateur emploie un vocabulaire courant ou impropre de terrain (par exemple : "saisir des notes", "noter les élèves"), mais que les extraits documentaires décrivent l'équivalent technique réel dans l'outil (par exemple : la gestion des degrés d'acquisition des compétences AFL au collège, ou le paramétrage des protocoles de CCF au lycée), tu ne dois PAS bloquer. Tu dois accueillir la question avec pédagogie, recadrer gentiment sur la réalité de l'outil à partir des documents, et fournir les chemins d'accès exacts qui y figurent.
2. INTERDICTION D'INVENTER : Il est formellement interdit d'inventer des menus, des fonctionnalités ou des procédures qui n'apparaissent pas dans les extraits documentaires.
3. CLAUSE DE REPLI STRICTE : La phrase de repli ci-dessous ne doit être déclenchée QUE si le sujet abordé est totalement absent des documents fournis ou sans rapport avec l'application. Si elle doit être déclenchée, réponds mot pour mot et UNIQUEMENT par cette phrase exacte :
"Désolé, je ne suis pas en mesure de vous répondre avec certitude sur ce point précis. Je vous propose de vous rapprocher directement du SAV à l'adresse : ipackeps@ac-aix-marseille.fr"

3. 📺 TUTO VIDÉO (DÉCLENCHEURS) :
- Si la question porte sur les SSS, inclus si pertinent : Evolution_et_fermeture_SSS.mp4 ou Signature_chef_etablissement_SSS.mp4
- Pour les autres manipulations techniques, inclus le nom exact du fichier associé si pertinent parmi la liste officielle : (import_eleves_pronote.mp4, Configuration_classes_import_eleves.mp4, affecter_eleves_dans_groupes.mp4, Generer_importer_fichier_groupes_cyclades.mp4, verification_affectation_protocoles_cyclades.mp4, creer_convocations_enseignants.mp4, Distribution_lots_santorin.mp4, Distribution_manuelle_lots_santorin.mp4, Saisie_notes_Santorin.mp4, Verrouiller_lot_santorin.mp4, Deverrouiller_lots_santorin.mp4, Ajouter_evaluateur_lot_santorin.mp4, Depot_referentiels_iPackEPS.mp4, Saisie_protocoles_iPackEPS.mp4, Protocoles_adaptes_iPackEPS.mp4, Extraction_notes_Santorin.mp4, Import_documents_glisser_deposer.mp4, Import_automatique_eleves.mp4, Actualisation_equipe_classes.mp4, Gestion_inventaire_EPI_photos.mp4, Controle_dates_CM_CAHPN.mp4, Export_zip_documents_certificatifs.mp4, Export_profs_externes_cyclades.mp4).

{contexte_complet_ia}

QUESTION DE L'UTILISATEUR :
{prompt}
"""
            if not est_cas_direct:
                try:
                    response = Settings.llm.complete(consigne_ia)
                    texte_brut = response.text
                except Exception as e:
                    texte_brut = f"Erreur de traitement IA : {str(e)}"

        # 🛡️ SÉCURITÉ PROGRAMMATIQUE SSS
        if est_sss and "Evolution_et_fermeture_SSS.mp4" not in texte_brut:
            texte_brut += "\n\n📺 Tutoriel associé : Evolution_et_fermeture_SSS.mp4"

        # 🧹 NETTOYAGES HTML
        texte_brut = texte_brut.replace("```html", "").replace("```HTML", "").replace("```", "")
        
        re_links = re.sub(
            r"\[([^\]]+)\]\((https?://[^\)]+)\)",
            r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">\1</a>',
            texte_brut,
        )
        texte_brut = re_links

        texte_nettoye = texte_brut.replace("\r\n", "\n").replace("\r", "\n")
        texte_final = texte_nettoye.replace("<p>", "").replace("</p>", "<br>")
        texte_final = re.sub(r"\n{3,}", "\n\n", texte_final)
        texte_final = texte_final.replace("\n", "<br>")

        # 🎯 Récupération dynamique du niveau sélectionné dans le formulaire
        niveau_actuel_form = st.session_state.get("niveau_actif_form", "Collège (DNB)")

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

        # Enregistrement pour la ronde de nuit de 2h du matin
        log_interaction(prompt, texte_brut)

        st.session_state.messages_hub.append(
            {"role": "assistant", "type": "text", "content": formatted_answer}
        )

        # 📺 INTÉGRATION DES VIDÉOS TUTOS ASSOCIÉES
        for video_name, video_url in VIDEOS_TUTOS.items():
            if video_name in texte_final:
                if est_dnb and "santorin" in video_name.lower():
                    continue
                st.session_state.messages_hub.append(
                    {"role": "assistant", "type": "video", "content": video_url}
                )

# AFFICHAGE DES MESSAGES (PERSISTANCE)
if "messages_hub" in st.session_state and st.session_state.messages_hub:
    st.markdown('<div style="margin-top: 15px;">', unsafe_allow_html=True)
    for m in st.session_state.messages_hub:
        with st.chat_message(m["role"]):
            if m.get("type") == "video":
                st.video(m["content"])
            else:
                st.markdown(m["content"], unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
