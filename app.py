import os
import re
from llama_index.core import Document, Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import pandas as pd
import requests
import streamlit as st

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
# 1. CONFIGURATION DE L'APPLICATION (IMPÉRATIVEMENT EN PREMIER)
# ======================================================================
st.set_page_config(
    page_title="Hub IA - EPS", layout="wide", initial_sidebar_state="collapsed"
)

# ======================================================================
# 2. GESTION DE LA MÉMOIRE ET DU COMPTEUR DE VISITES FIABLE (PROTÉGÉ)
# ======================================================================
if "messages_hub" not in st.session_state:
  st.session_state.messages_hub = []
if "active_module" not in st.session_state:
  st.session_state.active_module = "ipack"


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

    if "visite_comptabilisee" not in st.session_state:
      valeur += 1
      with open(fichier_compteur, "w") as f:
        f.write(str(valeur))
      st.session_state.visite_comptabilisee = True

    return valeur
  except:
    return 1


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
    .santorin-card, .santorin-card *, .general-card, .general-card *, .securite-card, .securite-card *, .peda-card, .peda-card * { 
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
    
    .hub-title {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        flex-grow: 1;
        padding-right: 35px; 
    }
    
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
    
    .badge-visiteur { 
        background-color: rgba(16, 185, 129, 0.2) !important; 
        color: #10B981 !important; 
        border: 1px solid rgba(16, 185, 129, 0.45) !important; 
        padding: 3px 12px !important; 
        border-radius: 20px !important; 
        font-size: 13px !important; 
        font-weight: 800 !important; 
        font-family: monospace !important;
    }
    
    .hub-title p { 
        color: #94A3B8 !important; 
        margin: 0 !important; 
        margin-top: -1px !important; 
        font-size: 13px !important; 
        text-transform: uppercase; 
        font-weight: bold !important;
    }

    .column-title-top { 
        color: #FFFFFF; 
        text-align: center; 
        margin-bottom: 12px !important; 
        background-color: #1E293B; 
        border-radius: 6px !important; 
        padding: 8px 10px; 
        box-shadow: 0px 4px 8px rgba(0,0,0,0.2);
    }
    .column-title-top .instruction {
        font-size: 11px !important;
        font-weight: 500;
        text-transform: uppercase;
        color: #94A3B8 !important;
        display: block;
    }
    .column-title-top .mode-actuel {
        font-size: 14px !important; 
        font-weight: 700;
        color: #FFFFFF !important;
        display: block;
    }

    button[kind="secondary"] { 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        color: #94A3B8 !important; 
        border: 1px solid rgba(255,255,255,0.05) !important; 
        border-radius: 8px !important; 
        font-size: 13px !important; 
        height: 60px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }

    button[kind="primary"] {
        background-color: rgba(16, 185, 129, 0.85) !important;
        color: #FFFFFF !important;
        border: 1px solid #10B981 !important;
        border-radius: 8px !important; 
        font-size: 13px !important; 
        box-shadow: 0px 0px 15px rgba(16, 185, 129, 0.6) !important;
        font-weight: 700 !important;
        height: 60px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .santorin-card, .general-card, .securite-card, .peda-card { 
        background-color: rgba(15, 23, 42, 0.45) !important; 
        backdrop-filter: blur(12px) !important; 
        -webkit-backdrop-filter: blur(12px) !important; 
        padding: 18px; 
        border-radius: 8px; 
        margin-bottom: 16px; 
    }
    .santorin-card { border-left: 6px solid #38BDF8 !important; } 
    .general-card { border-left: 6px solid #10B981 !important; } 
    .securite-card { border-left: 6px solid #FF9F43 !important; } 
    .peda-card { border-left: 6px solid #FFA502 !important; } 
    
    .santorin-card h3, .general-card h3, .securite-card h3, .peda-card h3 {
        color: #38BDF8 !important; 
        font-size: 16px !important; 
        margin-top: 16px !important; 
        font-weight: 800 !important; 
        text-transform: uppercase; 
    }
    .peda-card h3 { color: #FFA502 !important; }
    .general-card h3 { color: #10B981 !important; }
    .securite-card h3 { color: #FF9F43 !important; }

    .law-highlight {
        background-color: rgba(255, 176, 32, 0.12) !important; 
        color: #FFB020 !important; 
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid rgba(255, 176, 32, 0.4) !important;
        font-weight: 700 !important;
    }
    </style> 
""".replace(
    '__URL_FOND__', f'{github_url}{img_fond}'
)
st.markdown(css_pur, unsafe_allow_html=True)

# ======================================================================
# 4. CONFIGURATION DE L'IA & CHARGEMENT DES BASES
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

expressions_inutiles = [
    "de",
    "la",
    "le",
    "les",
    "des",
    "du",
    "un",
    "une",
    "pour",
    "sur",
    "en",
    "dans",
    "au",
    "aux",
]

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
      except:
        pass
  chemin_textes = "data/textes/base_textes_officiels.txt"
  if os.path.exists(chemin_textes):
    try:
      mtimes.append(os.path.getmtime(chemin_textes))
    except:
      pass
  for f_peda in [
      "base_pedagogique_edubase.txt",
      "matrice_AFL_lycee.txt",
      "programmes_college_2015_carte_mentale.txt",
  ]:
    if os.path.exists(f_peda):
      try:
        mtimes.append(os.path.getmtime(f_peda))
      except:
        pass
  for dossier in ["data/peda", "data/examens", "data/ipack", "data/textes"]:
    if os.path.exists(dossier) and os.path.isdir(dossier):
      try:
        for f in os.listdir(dossier):
          mtimes.append(os.path.getmtime(os.path.join(dossier, f)))
      except:
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
                  text=f.read(), metadata={"source": f"Règles de Pierre ({fp})"}
              )
          )
      except:
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
                Document(text=f.read(), metadata={"source": nom_fichier})
            )
        except:
          pass
  return docs_trouves


@st.cache_resource
def initialiser_base_santorin(cle_fremt):
  docs_santorin = [
      Document(
          text=(
              "Fiche Mémo - Correction Partagée Santorin (DEC). Spécifications"
              " techniques sur la correction multiple."
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
      similarity_top_k=6
  )


@st.cache_resource
def initialiser_base_ipack(cle_fremt):
  docs_ipack = [
      Document(
          text=(
              "Guide Pratique iPackEPS - Saisie des structures trimestrielles et"
              " imports XML."
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
      similarity_top_k=5
  )


@st.cache_resource
def initialiser_base_textes(cle_fremt):
  docs_textes = [
      Document(
          text=(
              "Base de données réglementaire globale pour les textes de lois du"
              " second degré."
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
      similarity_top_k=6
  )


@st.cache_resource
def initialiser_base_peda(cle_fremt):
  docs_peda = charger_dossier_txt_securise("data/peda")
  if not docs_peda:
    docs_peda.append(
        Document(text="Base pédagogique vide", metadata={"source": "system"})
    )
  return VectorStoreIndex.from_documents(docs_peda).as_retriever(
      similarity_top_k=7
  )


timestamp_fichier = obtenir_cle_fichier()
retriever_santorin = initialiser_base_santorin(timestamp_fichier)
retriever_ipack = initialiser_base_ipack(timestamp_fichier)
retriever_textes = initialiser_base_textes(timestamp_fichier)
retriever_peda = initialiser_base_peda(timestamp_fichier)


def qualifier_requete_rag(prompt_brut, module_actif):
  """Agent de pré-lecture IA : traduit l'intention humaine en une requête technique chirurgicale pour le RAG."""
  prompt_analyse = f"""Tu es l'analyseur sémantique d'un moteur documentaire expert en Éducation Physique et Sportive (EPS).
L'utilisateur a posé cette question dans le module « {module_actif} » :
« {prompt_brut} »

Ta mission :
1. Détecte le problème réel sous-jacent (ex: inscription SIÈCLE, élèves orphelins non associés à un protocole, synchronisation Cyclades/Santorin, droits Imag'in PDF, cadenas co-évaluation, AFC vs AFL, dispense vs certificat médical, sortie 2 minibus 2 profs sans surveillance, ratio falaise escalade, responsabilité chef établissement, accident).
2. Identifie les logiciels ou cadres juridiques concernés : SIÈCLE, Pronote, iPackEPS, Cyclades, Imag'in, Santorin, LSU/DNB, Bac GT, Bac Pro, CAP, Code de l'éducation, Loi Fauchon, L. 911-4, Circulaires de sécurité.
3. Reformule la question sous la forme de 4 à 8 mots-clés techniques exacts pour maximiser la pertinence de la recherche vectorielle.

Renvoie UNIQUEMENT les mots-clés séparés par des espaces, sans phrase d'introduction ni ponctuation :"""
  try:
    mots_cles = Settings.llm.complete(prompt_analyse).text.strip()
    return mots_cles if mots_cles else prompt_brut
  except:
    return prompt_brut


# ======================================================================
# 5. BANDEAU SUPÉRIEUR REHAUSSÉ
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
            <img src="{github_url}{img_droite}" height="55">
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# ======================================================================
# 6. EN-TÊTE DU TABLEAU DE BORD
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
    "peda": (
        "🔍 Mode Actif : Les programmes (Référentiels, CA & BO)"
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
    '<div class="column-title-top"><span class="instruction">⚙️ Choisissez le'
    " contexte de votre question ci-dessous</span><span"
    f' class="mode-actuel">{titre_affiche}</span></div>',
    unsafe_allow_html=True,
)

# ======================================================================
# 7. BOUTONS DE CONTEXTE
# ======================================================================
col_b1, col_b2, col_b3, col_b4 = st.columns(4, gap="small")
with col_b1:
  if st.button(
      "🛠️ iPackEPS",
      use_container_width=True,
      key="btn_ip",
      type=(
          "primary" if st.session_state.active_module == "ipack" else "secondary"
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
      "🔍 Les programmes",
      use_container_width=True,
      key="btn_ge",
      type=(
          "primary" if st.session_state.active_module == "peda" else "secondary"
      ),
  ):
    st.session_state.active_module = "peda"
    st.session_state.messages_hub = []
    st.rerun()
with col_b4:
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
# 7B. MESSAGES D'AVERTISSEMENT
# ======================================================================
if st.session_state.active_module == "textes":
  st.markdown(
      """
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            ⚠️ <strong>Avertissement –</strong> Bien que basées sur les textes officiels, ces réponses ne remplacent pas les autorités académiques. En cas de doute juridique ou de sinistre, contactez impérativement : <strong>Votre Chef d'établissement, votre Secrétariat d'examen, ou votre IA-IPR.</strong>
        </span>
    </div>
    """,
      unsafe_allow_html=True,
  )
elif st.session_state.active_module == "peda":
  st.markdown(
      """
    <div style="background-color: #1e293b; padding: 12px; border-radius: 8px; border: 1px solid #334155; text-align: center; margin-bottom: 15px; line-height: 1.5;">
        <span style="color: #fbbf24; font-weight: 500; font-size: 14px;">
            💡 <strong>Rappel Institutionnel :</strong> Cet onglet extrait exclusivement les Champs d'Apprentissage (CA), compétences et Attendus des Bulletins Officiels (BO). La liberté pédagogique reste sous l'entière responsabilité des équipes d'établissement.
        </span>
    </div>
    """,
      unsafe_allow_html=True,
  )
else:
  st.markdown(
      """
    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px; line-height: 1.5;">
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
                <span style="color: #FCD34D !important;">Administration des examens : remontée officielle du Bac/DNB, correction numérique sur Arena, arbitrages de la CAHPN.</span><br>
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
# 8. ZONE D'ACTION (ÉPURÉE & 100% LARGEUR)
# ======================================================================
prompt = st.chat_input(
    "Posez votre question institutionnelle, technique ou juridique ici...",
    key="chat_main",
)

# ======================================================================
# 9. FLUX DE MESSAGES ET ARBITRAGE HYBRIDE INTÉGRAL (SÉCURISÉ)
# ======================================================================
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
for m in st.session_state.messages_hub:
  with st.chat_message(m["role"]):
    if m.get("type") == "video":
      st.video(m["content"])
    else:
      st.markdown(m["content"], unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

if prompt:
  # 🔄 Remise à zéro pour traiter chaque question de manière isolée
  st.session_state.messages_hub = []

  st.session_state.messages_hub.append({
      "role": "user",
      "type": "text",
      "content": f"<span style='color: white;'>{prompt}</span>",
  })
  with st.spinner("Je recherche les documents et textes officiels..."):
    mode = st.session_state.active_module

    texte_brut = ""
    extraits_doc = ""
    badge, color_card = "INFORMATION", "general-card"

    # Détermination textuelle du nom de l'onglet pour la phrase de contexte
    onglets_noms = {
        "ipack": "l'onglet Assistance Technique iPackEPS (Gestion du CCF)",
        "examens": (
            "l'onglet Réglementation Examens & Santorin (Copies Numérisées)"
        ),
        "peda": "l'onglet Les programmes (Référentiels, CA & BO)",
        "textes": (
            "l'onglet Sécurité & Responsabilité Juridique (Textes Officiels)"
        ),
    }
    contexte_choisi_nom = onglets_noms.get(mode, "un onglet de l'application")

    verites_terrain_pierre = ""
    try:
      for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
        if os.path.exists(fp):
          with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            verites_terrain_pierre += (
                f"\n--- REGLES DIRECTES DE PIERRE ---\n" + f.read() + "\n"
            )
    except:
      pass

    # 🧠 AIGUILLEUR MINIMALISTE INTERCEPTANT UNIQUEMENT LES PANNES CRITIQUES BLOQUANTES
    intention = "AUCUN_BLINDAGE"
    if mode == "examens":
      intent_prompt = f"""Tu es l'aiguilleur technique du Hub Examens EPS. Détermine l'intention : "{prompt}"
            Sélectionne un mot-clé UNIQUEMENT parmi ceux-ci :
            - DNB_COLLEGE : Toute question mentionnant le Brevet, DNB, collège, note d'examen collège, ou remontée DEC au collège.
            - SUJET_SECOURS : Demande de sujet écrit, sujet papier, impression ou sujet de secours pour rattrapage.
            - CAP_3_EPREUVES : Mention explicite de 3 épreuves ou 3 notes en CAP.
            - CALENDRIER : Demande explicite de date limite pour le Lycée/Bac/Santorin (hors DNB).
            - SANTORIN_ERREUR_VALIDATION : Le lot est déjà validé définitivement par le prof et l'écran est clos.
            - SANTORIN_GRISE : Cases/crayons grisés, problème de co-évaluation simultanée (cadenas).
            - JURY_REMPLACEMENT : Problème d'ordre de mission, convocation Chorus ou prof remplaçant non visible.
            - AUCUN_BLINDAGE : Tout le reste (AFL, notation, dispense, inaptitude, élèves manquants Cyclades, cas particuliers).
            """
      try:
        intention = Settings.llm.complete(intent_prompt).text.strip()
      except:
        intention = "AUCUN_BLINDAGE"
    elif mode == "ipack":
      intent_prompt = f"""Tu es l'aiguilleur d'iPackEPS. Détermine l'intention : "{prompt}"
            - IPACK_SSS : Le dossier SSS ou le bilan annuel est verrouillé en lecture seule par la direction.
            - IPACK_GROUPES : Procédure pas-à-pas pour configurer les classes/groupes ou imports XML Pronote.
            - IPACK_NOUVEL_ELEVE : Procédure pour injecter un nouvel élève arrivant via SIÈCLE.
            - AUCUN_BLINDAGE : Toute autre question.
            """
      try:
        intention = Settings.llm.complete(intent_prompt).text.strip()
      except:
        intention = "AUCUN_BLINDAGE"

    est_dnb_direct = intention == "DNB_COLLEGE" or (
        mode == "examens"
        and ("dnb" in prompt.lower() or "brevet" in prompt.lower())
    )
    est_sujet_secours_direct = intention == "SUJET_SECOURS" or (
        "sujet" in prompt.lower() and "secours" in prompt.lower()
    )
    est_cap_3epreuves_direct = intention == "CAP_3_EPREUVES" or (
        mode == "examens"
        and "cap" in prompt.lower()
        and ("3 épreuves" in prompt.lower() or "3 notes" in prompt.lower())
    )
    est_date_notes_direct = intention == "CALENDRIER" and not est_dnb_direct
    est_erreur_validation_santorin = intention == "SANTORIN_ERREUR_VALIDATION"
    est_grise_direct = intention == "SANTORIN_GRISE"
    est_remplacement_reunion_direct = intention == "JURY_REMPLACEMENT"
    est_sss_direct = intention == "IPACK_SSS"
    st_groupes_direct = intention == "IPACK_GROUPES"
    est_nouvel_eleve_direct = intention == "IPACK_NOUVEL_ELEVE"
    est_tasa_direct = mode == "textes" and "tasa" in prompt.lower()

    est_cas_blindé_racine = (
        est_dnb_direct
        or est_sujet_secours_direct
        or est_cap_3epreuves_direct
        or est_date_notes_direct
        or est_erreur_validation_santorin
        or est_grise_direct
        or est_remplacement_reunion_direct
        or est_sss_direct
        or st_groupes_direct
        or est_nouvel_eleve_direct
        or est_tasa_direct
    )

    # 🧠 PRE-PROCESSING SÉMANTIQUE & RECHERCHE VECTORIELLE RAG
    if openai_api_key and not est_cas_blindé_racine:
      requete_ciblee = qualifier_requete_rag(prompt, mode)
      try:
        if mode == "examens":
          for n in retriever_santorin.retrieve(requete_ciblee):
            extraits_doc += f"{n.node.text}\n\n"
        elif mode == "ipack":
          for n in retriever_ipack.retrieve(requete_ciblee):
            extraits_doc += f"{n.node.text}\n\n"
        elif mode == "textes":
          mot_cle_local = requete_ciblee.lower()
          for exp in expressions_inutiles:
            mot_cle_local = mot_cle_local.replace(exp, "")
          for n in retriever_textes.retrieve(
              mot_cle_local.strip()
              if len(mot_cle_local.strip()) > 2
              else requete_ciblee
          ):
            extraits_doc += f"{n.node.text}\n\n"
        elif mode == "peda":
          for n in retriever_peda.retrieve(requete_ciblee):
            extraits_doc += f"{n.node.text}\n\n"
      except:
        pass

    # ======================================================================
    # 🎯 ROUTAGE DU RENDU FINAL
    # ======================================================================
    if est_tasa_direct:
      texte_brut = extraits_doc
      badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"

    elif est_dnb_direct:
      texte_brut = """<h3>📊 COLLÈGE & DNB : AUCUN CCF NI NOTE D'EXAMEN SUR 20</h3>
<ul>
  <li><strong>Règle d'or nationale :</strong> Il n'existe <strong>aucune épreuve terminale</strong>, <strong>aucun CCF</strong> et <strong>aucune note sur 20 transmise à la DEC</strong> pour l'EPS au Diplôme National du Brevet.</li>
  <li><strong>Modalités d'évaluation :</strong> L'évaluation repose exclusivement sur le contrôle continu trimestriel et la validation des compétences du socle commun (SCCC / AFC) enregistrées sur le <strong>Livret Scolaire Unique (LSU)</strong>.</li>
  <li><strong>Aucun protocole Santorin :</strong> Les collèges ne sont pas concernés par les remontées de notes sur Santorin ni par les dates limites d'examen de la DEC.</li>
</ul>"""
      badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

    elif est_sujet_secours_direct:
      texte_brut = """<h3>⚠️ AUCUN SUJET ÉCRIT DE SECOURS EN EPS</h3>
<ul>
  <li><strong>Règle nationale absolue :</strong> En EPS (CCF ou ponctuel), il n'existe <strong>aucun sujet écrit ou papier</strong> à imprimer sur iPackEPS, Santorin ou Cyclades. L'évaluation est 100 % pratique.</li>
  <li><strong>Élève absent justifié (ABJ) :</strong> Organisation obligatoire d'une <strong>Épreuve de substitution</strong> (rattrapage de l'épreuve motrice sur le terrain) avant la fermeture des serveurs.</li>
  <li><strong>Élève inapte médicalement :</strong> Saisie du statut <strong>[DISP]</strong> sur présentation d'un certificat médical officiel conforme.</li>
</ul>"""
      badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

    elif est_cap_3epreuves_direct:
      texte_brut = """<h3>⚠️ ALERTE : PROTOCOLE CAP STRICT À 2 ÉPREUVES</h3>
<ul>
  <li><strong>Réglementation stricte (Circulaire du 27 août 2025) :</strong> En CAP, le CCF repose <strong>STRICTEMENT sur 2 épreuves</strong> issues de 2 champs d'apprentissage distincts.</li>
  <li><strong>Bloqueur Santorin :</strong> Toute saisie d'une 3ᵉ note est bloquée par l'interface et entraînera le rejet immédiat du protocole par la CAHPN.</li>
  <li><strong>Procédure :</strong> Configurez votre classe en mode groupe sur iPackEPS et supprimez la 3ᵉ épreuve excédentaire.</li>
</ul>"""
      badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

    elif est_date_notes_direct:
      texte_brut = """<h3>📊 CALENDRIER & DATES LIMITES SANTORIN 2026</h3>
<strong>Statut administratif : Échéances officielles de clôture des serveurs.</strong><br>
<ul>
  <li><strong>Académie d'Aix-Marseille :</strong> 30 mai 2026 au soir.</li>
  <li><strong>Académie de Créteil :</strong> 9 juin 2026 au soir.</li>
  <li><strong>Établissements en Rythme Sud (AEFE / Hémisphère Sud) :</strong> Session décalée sur octobre / novembre / décembre (la date du 30 mai ne s'applique pas).</li>
  <li><strong>Autres académies :</strong> Se référer impérativement au calendrier émis par votre Division des Examens et Concours (DEC).</li>
</ul>"""
      badge, color_card = (
          ("📊 EXAMENS & SANTORIN" if mode == "examens" else "🛠️ PROTOCOLE IPACK"),
          ("santorin-card" if mode == "examens" else "general-card"),
      )

    elif est_erreur_validation_santorin:
      texte_brut = """<h3>📊 SANTORIN : ERREUR DE SAISIE APRÈS VALIDATION</h3>
<strong>Statut administratif : Clôture définitive du lot par le correcteur.</strong><br>
<ul>
  <li><strong>Étape 1 :</strong> Ne tentez pas de forcer l'interface. Prévenez immédiatement le secrétariat de direction de votre établissement.</li>
  <li><strong>Étape 2 :</strong> Le chef d'établissement contacte le gestionnaire de la Division des Examens et Concours (DEC) pour demander un <strong>[Renvoi en modification]</strong>.</li>
  <li><strong>Étape 3 :</strong> Après déblocage DEC, le chef d'établissement déverrouille le lot dans sa console, permettant à l'enseignant de rectifier la saisie.</li>
</ul>
<br>📺 <strong>Tutoriel de déblocage :</strong> Deverrouiller_lots_santorin.mp4 (Processus inverse de clôture : Verrouiller_lot_santorin.mp4)"""
      badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

    elif est_sss_direct:
      texte_brut = """<h3>🛠️ IPACKEPS : DOSSIER SSS OU BILAN VERROUILLÉ</h3>
<strong>Statut : Lecture seule absolue.</strong><br>
Contactez immédiatement votre Correspondant iPackEPS de bassin ou l'équipe des IA-IPR. Seuls ces profils possèdent les droits master pour appliquer la commande <strong>[Renvoyer en modification]</strong>."""
      badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

    elif st_groupes_direct:
      texte_brut = """<h3>🛠️ IPACKEPS : CONFIGURATION DES CLASSES ET GROUPES</h3>
<ul>
  <li><strong>Étape 1 :</strong> Accédez au menu supérieur <strong>[Dossiers]</strong>.</li>
  <li><strong>Étape 2 :</strong> Allez dans <strong>[Dossier EPS]</strong> > <strong>[Classes]</strong> > <strong>[Configuration des Classes]</strong>.</li>
  <li><strong>Étape 3 :</strong> Importez le fichier d'extraction Pronote ou SIÈCLE dans le module <strong>[Mes Élèves]</strong>.</li>
</ul>
<br>📺 <strong>Tutoriels d'accompagnement :</strong> Configuration_classes_import_eleves.mp4 et affecter_eleves_dans_groupes.mp4"""
      badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

    elif est_nouvel_eleve_direct:
      texte_brut = """<h3>🛠️ IPACKEPS : AJOUTER UN ÉLÈVE ARRIVANT</h3>
L'élève doit être obligatoirement enregistré dans <strong>SIÈCLE</strong> par le secrétariat de direction.
Effectuez ensuite une mise à jour via un nouvel import XML/CSV depuis Pronote pour l'intégrer automatiquement dans iPackEPS sans écraser vos notes existantes.
<br><br>📺 <strong>Tutoriel d'accompagnement :</strong> import_eleves_pronote.mp4"""
      badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

    elif est_grise_direct:
      texte_brut = """<h3>📊 EXAMENS & SANTORIN : CASES OU CRAYONS GRISÉS (CADENAS)</h3>
<ul>
  <li><strong>Correction partagée simultanée :</strong> Si un collègue co-évaluateur édite le lot, l'interface bascule automatiquement en lecture seule. <strong>Solution : Demandez-lui de fermer sa session Arena.</strong></li>
  <li><strong>Lot non déplié :</strong> Allez dans [Lots] > [Voir le détail] et cliquez sur le nom exact du candidat pour activer les curseurs d'AFL.</li>
</ul>
<br>📺 <strong>En cas de besoin de transfert de lot :</strong> Ajouter_evaluateur_lot_santorin.mp4"""
      badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

    elif est_remplacement_reunion_direct:
      texte_brut = """<h3>📊 EXAMENS : REMPLACEMENT EN JURY & DROITS SANTORIN</h3>
Le secrétariat d'établissement doit enregistrer la suppléance sur <strong>Imag'in</strong> et IMPÉRATIVEMENT cliquer sur le picto <strong>[PDF]</strong> de la convocation. C'est cette action technique qui pousse instantanément l'identité et les droits d'écriture du professeur vers Santorin.
<br><br>📺 <strong>Tutoriel de gestion des convocations :</strong> creer_convocations_enseignants.mp4"""
      badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

    else:
      if mode == "examens":
        badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
      elif mode == "ipack":
        badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
      elif mode == "textes":
        badge, color_card = "⚖️ SÉCURITÉ & CADRE JURIDIQUE", "securite-card"
      else:
        badge, color_card = "🔍 LES PROGRAMMES", "peda-card"

      if mode == "examens" and not extraits_doc.strip():
        texte_brut = (
            "Désolé, je ne trouve pas cette règle spécifique dans ma mémoire"
            " locale d'examen. Veuillez vous rapprocher de votre direction ou"
            " de votre IA-IPR EPS."
        )
      else:
        consigne_ia = f"""Tu es l'assistant IA référent expert pour l'Éducation Physique et Sportive (EPS), la réglementation administrative, la responsabilité juridique et les programmes officiels de l'académie d'Aix-Marseille.
Tu réponds à TOUTE demande ou procédure avec une précision chirurgicale, SANS DÉTOUR, EN CITANT SYSTÉMATIQUEMENT LES TEXTES OFFICIELS.

CONTEXTE DE RÉFÉRENCE SOUVERAIN (SOURCE DE VÉRITÉ ABSOLUE) :
{extraits_doc}
{verites_terrain_pierre}

QUESTION DE L'UTILISATEUR :
{prompt}

CADRE UNIVERSEL D'ANALYSE ET DE RÉPONSE (OBLIGATOIRE POUR TOUTE SITUATION) :

1. 🎯 ATTAQUE DIRECTE & VERDICT OPÉRATIONNEL (Ligne 1) :
   - Formule le verdict sans préambule :
     * Situation / Projet de sortie : "❌ **VERDICT : NON CONFORME - REFUS OBLIGATOIRE DU CHEF D'ÉTABLISSEMENT EN L'ÉTAT**" ou "✅ **VERDICT : CONFORME SOUS RÉSERVE DES OBLIGATIONS SUIVANTES**".
     * Procédure technique / Examen : "⚙️ **STATUT TECHNIQUE : [Nom de la procédure exacte]**".
     * Cas médical / Inaptitude : "📋 **CADRE MÉDICAL : [Recevable / Irrecevable]**".

2. ⚖️ CITATION STRICTE DES TEXTES OFFICIELS :
   - CITE SYSTÉMATIQUEMENT les sources juridiques et réglementaires appropriées :
     * Responsabilité civile de l'État : Article L. 911-4 du Code de l'éducation (Loi du 5 avril 1937).
     * Responsabilité pénale / Faute non intentionnelle : Loi Fauchon du 10 juillet 2000 / Article 121-3 du Code pénal.
     * Surveillance et sécurité : Circulaire n° 97-178 du 18 septembre 1997 (surveillance des élèves), Circulaire n° 2017-116 du 6 octobre 2017 (encadrement des APPN).
     * Inaptitudes médicales : Articles R. 312-2 à R. 312-6 du Code de l'éducation et Décret n° 88-977 (certificat médical type).
     * Voyages scolaires & sorties : Circulaire n° 2023-052 du 13 juin 2023 (organisation des sorties et voyages scolaires).
     * Certifications & CCF : Circulaire du 02 avril 2025 (Bac Pro), Circulaire du 27 août 2025 (CAP), Arrêté du 28 avril 2022 (Bac GT), Article D. 312-1 (Collège/DNB), BO n°30 du 29 juillet 2021 (redoublement).
     * Statut des enseignants / AS : Décret n° 2014-460 du 7 mai 2014 (obligations de service et forfait 3h AS).
     * Égalité et barèmes : Jurisprudence constante du Conseil d'État sur les barèmes physiologiquement adaptés en CA1.

3. 🔍 AUDIT DES RATIOS, DES COMPÉTENCES ET DES RISQUES :
   - Calcule et vérifie systématiquement :
     * Logistique / Transport : Nombre de conducteurs vs nombre d'adultes requis pour la surveillance des passagers à bord (ex: 2 minibus pour 2 adultes = 2 conducteurs = 0 adulte pour surveiller l'arrière et 0 relais volant = faute caractérisée).
     * Taux d'encadrement en APPN : Compétence exclusive du professeur d'EPS sur les activités à environnement spécifique (escalade falaise, eau vive, ski, VTT). Un accompagnateur non diplômé (ex: professeur d'autre discipline) assure la co-surveillance de la vie collective mais n'a aucune qualification pour valider un amarrage, parer ou intervenir en paroi.
     * Chaîne de secours : Respect strict du déclenchement des secours (15 / 18 / 112 à l'étranger). Interdiction formelle du transport d'élève blessé dans un véhicule personnel.

4. 📋 PROTOCOLE DE MISE EN CONFORMITÉ (ÉTAPES CHIRURGICALES) :
   - Détaille les pièces administratives et actions obligatoires :
     * Sortie / Voyage : Vote du Conseil d'Administration (CA), Ordres de Mission (OM), Autorisation de Sortie du Territoire (AST Cerfa + CNI parent signataire), Carte Européenne d'Assurance Maladie (CEAM pour étranger), assurance transport tous risques avec rachat de franchise, 3e adulte conducteur/surveillant.
     * Gestion d'examen : Chaîne SIÈCLE ➔ iPackEPS ➔ Cyclades ➔ Imag'in (génération du PDF) ➔ Santorin.
     * Inaptitude : Certificat médical officiel obligatoire (mot des parents nul), aménagement ou statut DISP.

5. 🛑 RESPECT STRICT DES CYCLES & VOCABULAIRE :
   - Collège (Cycles 3 et 4) = Uniquement CA1, CA2, CA3 et CA4. Le CA5 N'EXISTE PAS au collège. Termes exclusifs : **Attendus de Fin de Cycle (AFC)** et **Socle Commun (SCCC)**.
   - Lycée (Voie GT & Voie Pro) = **Attendus de Fin de Lycée (AFL)** ou AFLP en Bac Pro.
   - Si un enseignant demande des AFL pour le collège, recadre immédiatement en précisant qu'il s'agit d'AFC.

6. 🚫 CADRAGE PÉDAGOGIQUE STRICT (ONGLET LES PROGRAMMES) :
   - Gabarit APSA obligatoire : Champ d'Apprentissage (CA), Intitulé officiel BO, Attendus officiels extraits du texte.
   - CA3 : Rappeler obligatoirement sa double dimension « prestation artistique et/ou acrobatique ».

7. 📊 SPÉCIFICITÉS CCF & SANTORIN (ONGLET EXAMENS) :
   - Note Unique (Bac GT) : Cocher [Dispensé] sur les 2 épreuves non évaluées, note normale sur l'APSA évaluée + commentaire circonstancié obligatoire dans Santorin pour la CAHPN.
   - Remplacement en jury : Clic obligatoire sur l'icône [PDF] dans Imag'in pour pousser les droits vers Santorin (creer_convocations_enseignants.mp4).
   - Bac Pro : Clic préalable obligatoire sur le bouton [Choisir les AFLP] pour cocher les AFLP 3 à 6.
   - CAP : Protocole strict à 2 épreuves (rejet immédiat si 3 notes).
   - Raccourci clavier Santorin : Saisie directe au pavé numérique + validation [Entrée] ou passage à l'AFL suivant via [Tab] (retour via [Maj + Tab]). Statut rapide via touche [D] pour DISP ou [A] pour ABI/ABJ.
   - Clôture de lot grisée : Nécessite 100 % des statuts saisis (astuce bascule affichage 100 candidats).

8. 👥 STRUCTURES HORS-SIÈCLE & ÉTRANGER (AEFE) :
   - Inscription et association manuelles dans Cyclades (MEMO-Associer-eleves-protocole-Etab-v1.0.pdf).
   - Rythme Sud : Session décalée en fin d'année civile (date du 30 mai non applicable).

9. 📐 FORMAT DE SORTIE VISUEL :
   - Utilise EXCLUSIVEMENT des listes à puces HTML (<ul>, <li>), des retours à la ligne (<br>), et des balises <strong> pour les mots-clés et textes de loi. Zéro bloc de texte compact.

10. 📺 MENTION DES VIDÉOS & LIENS :
   - Écris UNIQUEMENT le nom du fichier en texte brut (ex : "📺 Tutoriel associé : Generer_importer_fichier_groupes_cyclades.mp4"). Jamais de lien Markdown local.
   - N'insère de lien Markdown que pour les URLs absolues en "https://".

11. 🛑 BLINDAGE ANTI-HORS-SUJET :
   - Si la question est loufoque ou sans rapport avec l'EPS, réponds STRICTEMENT : "Le Hub IA - EPS est un outil exclusivement dédié à l'accompagnement réglementaire, technique et pédagogique de la discipline. Votre demande sort du cadre d'exercice et de certification des enseignants d'Éducation Physique et Sportive."
"""
        try:
          response = Settings.llm.complete(consigne_ia)
          texte_brut = response.text
        except Exception as e:
          texte_brut = f"Erreur de traitement IA : {str(e)}"

    # Traitements de surface et filtres regex pour les références juridiques
    texte_brut = re.sub(
        r"(Article\s+L?\.?\s*\d+[-–\w]*|Loi\s+du\s+\d+\s+\w+\s+\d+|Loi\s+Fauchon|RGPD|Code\s+de"
        r" l\'éducation|Code\s+pénal|Circulaire\s+du\s+\d+\s+\w+\s+\d+|Circulaire\s+n°\s*[\d-]+|Décret\s+n°\s*[\d-]+|Arrêté\s+du\s+\d+\s+\w+\s+\d+|BO\s+n°\s*\d+)",
        r'<span class="law-highlight">\1</span>',
        texte_brut,
    )
    texte_brut = texte_brut.replace(
        '<span class="law-highlight"><span class="law-highlight">',
        '<span class="law-highlight">',
    ).replace("</span></span>", "</span>")
    re_links = re.sub(
        r"\[([^\]]+)\]\((https?://[^\)]+)\)",
        r'<a href="\2" target="_blank" style="color: #FFB020 !important;'
        r' text-decoration: underline;">\1</a>',
        texte_brut,
    )
    texte_brut = re_links

    texte_final = (
        texte_brut.replace("\n", "")
        .replace("\r", "")
        .replace("<p>", "")
        .replace("</p>", "<br>")
        .replace(chr(10), "<br>")
    )

    # Construction de la réponse avec la phrase de contexte en premier plan
    phrase_contexte = (
        "<div style='font-size: 12.5px; color: #94A3B8; margin-bottom: 10px;"
        " border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom:"
        f" 5px;'>📍 <em>Vous avez choisi de poser votre question dans {contexte_choisi_nom}.</em></div>"
    )
    formatted_answer = (
        f'<div class="{color_card}">{phrase_contexte}<strong>{badge}'
        f" :</strong><br>{texte_final}</div>"
    )

    st.session_state.messages_hub.append(
        {"role": "assistant", "type": "text", "content": formatted_answer}
    )

    # ======================================================================
    # 🚀 ZONE 2 : DÉTECTEUR AUTOMATIQUE DE CAPSULES VIDÉOS (DEPUIS TEXTE FINAL)
    # ======================================================================
    for video_name, video_url in VIDEOS_TUTOS.items():
      if video_name in texte_final:
        st.session_state.messages_hub.append(
            {"role": "assistant", "type": "video", "content": video_url}
        )

    st.rerun()
