import datetime
import os
import re
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
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
  for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
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


def charger_consignes_pierre():
  documents_charges = []
  for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
    if os.path.exists(fp):
      try:
        with open(fp, "r", encoding="utf-8") as f:
          documents_charges.append(
              Document(
                  text=f.read(),
                  metadata={"source": f"Règles de Pierre ({fp})"},
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
  docs_santorin.extend(charger_consignes_pierre())
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
  docs_ipack.extend(charger_consignes_pierre())
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
  docs_textes.extend(charger_consignes_pierre())
  return VectorStoreIndex.from_documents(docs_textes).as_retriever(
      similarity_top_k=8
  )


timestamp_fichier = obtenir_cle_fichier()
retriever_santorin = initialiser_base_santorin(timestamp_fichier)
retriever_ipack = initialiser_base_ipack(timestamp_fichier)
retriever_textes = initialiser_base_textes(timestamp_fichier)


# ======================================================================
# 🔔 VEILLE AUTOMATIQUE TAVILY (Sans e-mail - Alerte visuelle)
# ======================================================================
def verifier_veille_dec(tavily_client):
  if not tavily_client:
    return

  fichier_suivi = "dernier_check_dec.txt"
  mois_actuel = datetime.datetime.now().strftime("%Y-%m")

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
        texte_alerte = (
            "🔔 Veille réglementaire mensuelle : De nouvelles informations ou"
            " mises à jour ont été détectées sur les sites officiels concernant"
            " les examens ou l'EPS. Pensez à vérifier si une nouvelle"
            " circulaire DEC a été publiée."
        )
        st.session_state.alerte_veille_dec = texte_alerte
    except Exception:
      pass


# Lancement du contrôle mensuel automatique au démarrage
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

# 🚨 BANDEAU DE VEILLE (Affiché uniquement si une nouveauté est détectée ce mois-ci)
if "alerte_veille_dec" in st.session_state:
  st.warning(st.session_state.alerte_veille_dec, icon="🚨")
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
# 7. ZONE DE SAISIE INTÉGRÉE (DIRECTEMENT COLLÉE SOUS LES BOUTONS)
# ======================================================================
prompt = None
with st.form(key="form_question_hub", clear_on_submit=True):
    col_input, col_submit = st.columns([5, 1])
    with col_input:
        prompt_brut = st.text_input(
            "Question :",
            placeholder=(
                "🔺 Sélectionnez le module concerné avant de saisir votre"
                " question..."
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
# 9. TRAITEMENT RAG & FLUX DE MESSAGES (AFFICHÉ SOUS LA SAISIE)
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

        # ⚡ DÉTECTIONS D'INVARIANTS INSTITUTIONNELS CRITIQUES
        est_college = any(w in p_low for w in ["6e", "5e", "4e", "3e", "collège", "college"])

        est_date = (not est_college) and any(
            phrase in p_low for phrase in [
                "quel est le calendrier", "quelles sont les dates", "date butoir de", 
                "date de fermeture", "calendrier officiel"
            ]
        ) and any(
            w in p_low for w in [
                "saisie", "note", "notes", "fermeture", "santorin", "cyclades", 
                "lot", "lots", "examen", "examens", "bac", "cap", "brevet", 
                "mayotte", "academie", "académie"
            ]
        )

        est_dnb = (mode != "textes") and any(w in p_low for w in ["dnb", "brevet", "collège", "college"]) and not any(w in p_low for w in ["bac", "lycée", "lycee", "cap"])

        est_sujet_secours = "sujet" in p_low and any(w in p_low for w in ["secours", "papier", "imprimer"])

        est_cap_3epreuves = (
            mode == "examens"
            and "cap" in p_low
            and any(w in p_low for w in ["3 épreuves", "3 notes", "trois épreuves", "trois notes"])
        )

        est_tasa = mode == "textes" and "tasa" in p_low

        # ⚡ ROUTAGE RACCOURCI
        est_cas_direct = ((mode != "textes") and (est_date or est_dnb or est_sujet_secours or est_cap_3epreuves)) or est_tasa

        # 🚀 RECHERCHE RAG LOCALE
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

        # 🌐 RECHERCHE WEB TAVILY
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

        # 🎯 ROUTAGE DU RENDU DIRECT
        if est_date:
            texte_brut = """<h3>📅 CALENDRIER OFFICIEL DES EXAMENS & SAISIE DES NOTES</h3>
<ul>
  <li><strong>Principe réglementaire :</strong> Les dates butoirs de saisie des notes, de remontée des résultats et de clôture des serveurs (Santorin / Cyclades) sont fixées annuellement par le calendrier officiel publié au <strong>Bulletin Officiel (BO)</strong> et précisées par la circulaire de la Division des Examens et Concours (DEC) de votre académie.</li>
  <li>👉 <strong>Consultez le calendrier officiel</strong> publié par votre académie de rattachement pour toute confirmation ou mise à jour.</li>
</ul>"""
            badge, color_card = "📅 CALENDRIER OFFICIEL", ("santorin-card" if mode == "examens" else "general-card")

        elif est_tasa:
            texte_brut = """<h3>🏊 CADRE RÉGLEMENTAIRE - TEST D'APTITUDE AU SAUVETAGE AQUATIQUE (TASA 2026)</h3>
<ul>
  <li><strong>Texte de référence officiel :</strong> Circulaire du 9 mars 2026 (abrogeant celle de 2019).</li>
  <li><strong>Obligation de qualification :</strong> Obligatoire pour tout enseignant d'EPS (concours, contractuels, détachements) dès la nomination.</li>
  <li><strong>Protocole technique (100m en continu < 3 min 45 s) :</strong>
    <ul>
      <li>Longueur 1 (0-25m) : Départ plongé obligatoire + nage libre en surface.</li>
      <li>Longueur 2 (25-50m) : Nage libre avec 7,50m d'apnée complète sous l'eau.</li>
      <li>Longueur 3 (50-75m) : Nage libre avec 7,50m d'apnée complète sous l'eau.</li>
      <li>Longueur 4 (75-100m) : Recherche d'un mannequin à 2,50m de profondeur et remorquage sur le dos sur 25m (visage hors de l'eau).</li>
    </ul>
  </li>
  <li><strong>Tenue stricte :</strong> Maillot de bain uniquement (combinaison, lunettes et pince-nez formellement interdits).</li>
</ul>"""
            badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

        elif est_dnb:
            texte_brut = """<h3>📊 COLLÈGE & DNB : AUCUN CCF NI PROTOCOLE CERTIFICATIF</h3>
<ul>
  <li><strong>Règle d'or nationale :</strong> Il n'existe <strong>aucune épreuve terminale</strong>, <strong>aucun CCF</strong>, <strong>aucune case certificative</strong> et <strong>aucune note sur 20 transmise à la DEC</strong> pour l'EPS au Diplôme National du Brevet.</li>
  <li><strong>Modalités d'évaluation :</strong> L'évaluation repose exclusivement sur le contrôle continu trimestriel et la validation des compétences du socle commun (SCCC / AFC) enregistrées sur le <strong>Livret Scolaire Unique (LSU)</strong>.</li>
  <li><strong>Sur iPackEPS &amp; Santorin :</strong> Les collèges ne paramètrent aucun protocole certificatif et ne sont concernés par aucune remontée de copies ou de lots sur Santorin.</li>
</ul>"""
            badge, color_card = ("📊 COLLÈGE & DNB" if mode == "examens" else "🛠️ ASSISTANCE iPACKEPS"), ("santorin-card" if mode == "examens" else "general-card")

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
  <li><strong>Réglementation stricte (Circulaire du 27 août 2025) :</strong> En CAP, le CCF repose <strong>STRICTEMENT sur 2 épreuves</strong> issues de 2 champs d'apprentissage distincts.</li>
  <li><strong>Bloqueur Santorin :</strong> Toute saisie d'une 3ᵉ note est bloquée par l'interface et entraînera le rejet immédiat du protocole par la CAHPN.</li>
  <li><strong>Procédure :</strong> Configurez votre classe en mode groupe sur iPackEPS et supprimez la 3ᵉ épreuve excédentaire.</li>
</ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        else:
            if mode == "examens":
                badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            elif mode == "ipack":
                badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
            else:
                badge, color_card = "⚖️ SÉCURITÉ & CADRE JURIDIQUE", "securite-card"

        # 📋 DIRECTIVES SPÉCIFIQUES PAR ONGLETS
        directive_onglet = ""
        if mode == "textes":
            directive_onglet = """
3. ⚖️ SPÉCIFICITÉ ONGLET SÉCURITÉ & JURIDIQUE :
   - Détermine si la situation est un ACCIDENT SURVENU ou un PROJET EN AMONT.
   - CONFLIT HIERARCHIQUE / INGÉRENCE DU CHEF D'ÉTABLISSEMENT : En cas de tentative de modification unilatérale des notes de CCF ou d'évaluation par la direction, rappeler que l'enseignant ne doit pas céder, consigner les faits par écrit, et saisir directement l'autorité académique compétente (IA-IPR EPS / DEC).
   - Rédige STRICTEMENT selon ce plan :
     🏛️ <strong>Textes officiels de référence & Extraits applicables :</strong> Citer nommément les articles pertinents (L. 911-4 du Code de l'éducation, art. 121-3 du Code Pénal / Loi Fauchon, Circulaire APPN 2017-075, L. 134-1 CGFP).
     ⚖️ <strong>Analyse de la situation & Conduite à tenir :</strong>
     * <strong>1. Qualification des responsabilités :</strong> Volet civil (substitution de l'État) et Volet pénal (faute caractérisée).
     * <strong>2. Démarches administratives concrètes :</strong> Saisir le chef d'établissement, rédiger un rapport circonstancié, et demander la protection fonctionnelle auprès du Recteur d'académie (via le service juridique du rectorat).
"""
        elif mode == "examens":
            directive_onglet = """3. 📊 SPÉCIFICITÉS EXAMENS & SANTORIN :
        - Traite précisément le problème d'examen posé en exploitant les règles de gestion (Bac GT, Bac Pro, CAP, dispenses, CAHPN, jurys, calendrier DEC).
        - DISTINCTION SUR LES VERROUILLAGES : Verrouillage interne (établissement) vs Verrouillage académique définitif (DEC)."""
        elif mode == "ipack":
            directive_onglet = """
3. 🛠️ ASSISTANCE TECHNIQUE iPACKEPS :
   - Donne la procédure technique exacte en précisant les menus réels ([Dossiers] > [Dossier EPS] > ...).
"""

        contexte_complet_ia = f"""
CONTEXTE DOCUMENTAIRE OFFICIEL LOCAL :
{extraits_doc}

SOURCES OFFICIELLES WEB (LÉGIFRANCE / ÉDUSCOL) :
{extraits_web}

{verites_terrain_pierre}
"""

        # 🛡️ LE SOCLE DE SÉCURITÉ INVARIABLE ET CENTRALISÉ
        consigne_ia = f"""Tu es l'assistant IA officiel en Éducation Physique et Sportive (EPS), examens et réglementation institutionnelle.

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

{contexte_complet_ia}

QUESTION DE L'UTILISATEUR :
{prompt}

MÉTHODE D'ANALYSE & RÈGLES DE RÉPONSE :
1. ANALYSE DU PÉRIMÈTRE : Réponds avec précision, clarté et rigueur institutionnelle.
2. STRUCTURE & MISE EN PAGE :
   - Rends une réponse TRÈS AÉRÉE, pas à pas, ligne par ligne.
   - Utilise impérativement des listes à puces ou ordonnées HTML (<ol>, <ul>, <li>).
   - Mettre les éléments d'interface et mots-clés en gras (<strong>...</strong>).
{directive_onglet}
3. 📺 TUTO VIDÉO (DÉCLENCHEURS STRICTS - SILENCE ABSOLU SI HORS SUJET) :
   - Termine par "📺 Tutoriel associé : nom_du_fichier.mp4" UNIQUEMENT si la question porte explicitement sur l'une de ces manipulations techniques exactes (import_eleves_pronote.mp4, Configuration_classes_import_eleves.mp4, affecter_eleves_dans_groupes.mp4, Generer_importer_fichier_groupes_cyclades.mp4, verification_affectation_protocoles_cyclades.mp4, creer_convocations_enseignants.mp4, Distribution_lots_santorin.mp4, Distribution_manuelle_lots_santorin.mp4, Saisie_notes_Santorin.mp4, Verrouiller_lot_santorin.mp4, Deverrouiller_lots_santorin.mp4, Ajouter_evaluateur_lot_santorin.mp4).
   - INTERDICTION FORMELLE d'écrire le mot "tutoriel", "aucun", "néant" ou d'afficher une ligne vidéo si le sujet n'est pas l'une de ces manipulations techniques. Le texte doit s'arrêter net après la conclusion.
"""

        if not est_cas_direct:
            try:
                response = Settings.llm.complete(consigne_ia)
                texte_brut = response.text
            except Exception as e:
                texte_brut = f"Erreur de traitement IA : {str(e)}"

        # 🧹 NETTOYAGES & FORMATAGE HTML
        texte_brut = texte_brut.replace("```html", "").replace("```HTML", "").replace("```", "")

        # 🛑 GUILLOTINE ANTI-TUTO POUR L'ONGLET JURIDIQUE : Supprime tout ce qui ressemble à un tuto si on est en mode texte
        if mode == "textes":
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
            .replace("\n", "<br>")
        )
        texte_final = re.sub(r"(<br>\s*){3,}", "<br><br>", texte_final)

        phrase_contexte = (
            f"<div style='font-size: 12.5px; color: #94A3B8; margin-bottom: 10px; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 5px;'>📍 <em>Vous avez choisi de poser votre question dans {contexte_choisi_nom}.</em></div>"
        )

        footer_assistance = ""
        if mode in ["ipack", "examens"]:
            footer_assistance = (
                "<div style='margin-top: 14px; padding-top: 8px; border-top: 1px dashed rgba(255,255,255,0.15); font-size: 12.5px; color: #CBD5E1;'>Bien entendu si ma réponse ne vous a pas aidé vous pouvez toujours contacter l'assistance <a href='mailto:ipackeps@ac-aix-marseille.fr' style='color: #38BDF8 !important; text-decoration: underline;'>ipackeps@ac-aix-marseille.fr</a></div>"
            )

        formatted_answer = (
            f'<div class="{color_card}">{phrase_contexte}<strong>{badge} :</strong><br>{texte_final}{footer_assistance}</div>'
        )

        st.session_state.messages_hub.append(
            {"role": "assistant", "type": "text", "content": formatted_answer}
        )

        for video_name, video_url in VIDEOS_TUTOS.items():
            if video_name in texte_final:
                st.session_state.messages_hub.append(
                    {"role": "assistant", "type": "video", "content": video_url}
                )

# AFFICHAGE DES MESSAGES ET DES VIDÉOS (Désormais hors du if prompt pour persister à l'écran)
if "messages_hub" in st.session_state and st.session_state.messages_hub:
    st.markdown('<div style="margin-top: 15px;">', unsafe_allow_html=True)
    for m in st.session_state.messages_hub:
        with st.chat_message(m["role"]):
            if m.get("type") == "video":
                st.video(m["content"])
            else:
                st.markdown(m["content"], unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
