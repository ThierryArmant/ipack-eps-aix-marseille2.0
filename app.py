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
    .securite-card { border-left: 6px solid #FF9F43 !important; } 
    .peda-card { border-left: 6px solid #FFA502 !important; } 
    
    .santorin-card p, .general-card p, .securite-card p, .santorin-card div, .general-card div, .securite-card div, .santorin-card span, .general-card span, .securite-card span, .santorin-card li, .general-card li, .securite-card li { 
        color: #FFFFFF !important; 
        font-size: 15px !important; 
        line-height: 1.6 !important; 
        font-weight: 400 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }
    
    .santorin-card h3, .general-card h3, .securite-card h3, .peda-card h3 {
        color: #38BDF8 !important; 
        font-size: 16px !important; 
        margin-top: 16px !important; 
        margin-bottom: 6px !important; 
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
        color: #F8FAFC !important; 
        margin-bottom: 3px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }

    .santorin-card strong, .general-card strong, .securite-card strong, .peda-card strong {
        font-weight: 700 !important; 
    }

    .law-highlight {
        background-color: rgba(255, 176, 32, 0.12) !important; 
        color: #FFB020 !important; 
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid rgba(255, 176, 32, 0.4) !important;
        font-weight: 700 !important;
        display: inline-block;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.5) !important;
    }

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
    
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) { 
        background-color: rgba(255, 255, 255, 0.15) !important; 
        backdrop-filter: blur(6px) !important;
        border-radius: 14px 14px 0px 14px !important; 
        margin-left: 15% !important; 
    }
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
    
    div[data-testid="stChatMessage"] * { color: #FFFFFF !important; }
    
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

expressions_inutiles = ["de", "la", "le", "les", "des", "du", "un", "une", "pour", "sur", "en", "dans", "au", "aux"]

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=openai_api_key)

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
            for f in os.listdir("data/peda"): mtimes.append(os.path.getmtime(os.path.join("data/peda", f)))
        except: pass
    if os.path.exists("data/examens") and os.path.isdir("data/examens"):
        try:
            for f in os.listdir("data/examens"): mtimes.append(os.path.getmtime(os.path.join("data/examens", f)))
        except: pass
    return max(mtimes) if mtimes else 0.0

def charger_consignes_pierre():
    documents_charges = []
    for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
        if os.path.exists(fp):
            try:
                with open(fp, "r", encoding="utf-8") as f: documents_charges.append(Document(text=f.read(), metadata={"source": f"Règles de Pierre ({fp})"}))
            except: pass
    return documents_charges

def charger_dossier_txt_securise(chemin_dossier):
    """Lit les fichiers .txt un par un pour immuniser le lecteur contre les fichiers cachés d'OS"""
    docs_trouves = []
    if os.path.exists(chemin_dossier) and os.path.isdir(chemin_dossier):
        for nom_fichier in os.listdir(chemin_dossier):
            if nom_fichier.lower().endswith(".txt"):
                chemin_complet = os.path.join(chemin_dossier, nom_fichier)
                try:
                    with open(chemin_complet, "r", encoding="utf-8", errors="ignore") as f:
                        docs_trouves.append(Document(text=f.read(), metadata={"source": nom_fichier}))
                except:
                    pass  
    return docs_trouves

@st.cache_resource
def initialiser_base_santorin(cle_fremt):
    docs_santorin = [Document(text="Fiche Mémo - Correction Partagée Santorin (DEC). Spécifications techniques sur la correction multiple.", metadata={"title": "Correction Partagée", "url": "https://assistance.ac-noumea.nc/IMG/pdf/fm_correction_partagee.pdf"})]
    docs_santorin.extend(charger_dossier_txt_securise("data/examens"))
    docs_santorin.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_santorin).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_ipack(cle_fremt):
    docs_ipack = [Document(text="Guide Pratique iPackEPS - Saisie des structures trimestrielles et imports XML.", metadata={"title": "Guide iPackEPS", "url": "https://eps.ac-normandie.fr/IMG/pdf/guide_utilisateur_professeur-2.pdf"})]
    docs_ipack.extend(charger_dossier_txt_securise("data/ipack"))
    docs_ipack.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_ipack).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_textes(cle_fremt):
    docs_textes = [Document(text="Base de données réglementaire globale pour les textes de lois du second degré.", metadata={"title": "Légifrance", "url": "https://www.legifrance.gouv.fr/"})]
    docs_textes.extend(charger_dossier_txt_securise("data/textes"))
    docs_textes.extend(charger_consignes_pierre())
    return VectorStoreIndex.from_documents(docs_textes).as_retriever(similarity_top_k=5)

@st.cache_resource
def initialiser_base_peda(cle_fremt):
    docs_peda = charger_dossier_txt_securise("data/peda")
    if not docs_peda: docs_peda.append(Document(text="Base pédagogique vide", metadata={"source": "system"}))
    return VectorStoreIndex.from_documents(docs_peda).as_retriever(similarity_top_k=5)

timestamp_fichier = obtenir_cle_fichier()
retriever_santorin = initialiser_base_santorin(timestamp_fichier)
retriever_ipack = initialiser_base_ipack(timestamp_fichier)
retriever_textes = initialiser_base_textes(timestamp_fichier)
retriever_peda = initialiser_base_peda(timestamp_fichier)

# ======================================================================
# 5. BANDEAU SUPERIEUR REHAUSSÉ AVEC COMPTEUR
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
# 6. EN-TÊTE DU TABLEAU DE BORD
# ======================================================================
label_titres = {
    "ipack": "🛠️ Mode Actif : Assistance Technique iPackEPS (Gestion du CCF & Inaptitudes)",
    "examens": "📊 Mode Actif : Réglementation Examens & Santorin (Copies Numérisées & Jurys)",
    "peda": "🔍 Mode Actif : Référentiels Institutionnels, APSA & Textes de Cadrage BO",
    "textes": "🔒 Mode Actif : SÉCURITÉ & Responsabilité Juridique (Textes Officiels & Risques APPN)"
}

titre_affiche = label_titres.get(st.session_state.active_module, "🔍 Mode Actif : Référentiels Institutionnels")
st.markdown(f'<div class="column-title-top"><span class="instruction">⚙️ Choisissez le contexte de votre question ci-dessous</span><span class="mode-actuel">{titre_affiche}</span></div>', unsafe_allow_html=True)

# ======================================================================
# 7. BOUTONS DE CONTEXTE
# ======================================================================
col_b1, col_b2, col_b3, col_b4 = st.columns(4, gap="small")
with col_b1:
    if st.button("🛠️ iPackEPS", use_container_width=True, key="btn_ip", type="primary" if st.session_state.active_module == "ipack" else "secondary"):
        st.session_state.active_module = "ipack"; st.session_state.messages_hub = []; st.rerun()
with col_b2:
    if st.button("📊 Examens &\nSantorin", use_container_width=True, key="btn_ex", type="primary" if st.session_state.active_module == "examens" else "secondary"):
        st.session_state.active_module = "examens"; st.session_state.messages_hub = []; st.rerun()
with col_b3:
    if st.button("🔍 Cadrage &\nRéférentiels", use_container_width=True, key="btn_ge", type="primary" if st.session_state.active_module == "peda" else "secondary"):
        st.session_state.active_module = "peda"; st.session_state.messages_hub = []; st.rerun()
with col_b4:
    if st.button("🔒 Sécurité &\nCadres Règl.", use_container_width=True, key="btn_se", type="primary" if st.session_state.active_module == "textes" else "secondary"):
        st.session_state.active_module = "textes"; st.session_state.messages_hub = []; st.rerun()

# ======================================================================
# 7B. MESSAGES D'AVERTISSEMENT (VERROUILLÉS AVEC TRIPLES GUILLEMETS)
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
            💡 <strong>Rappel Institutionnel :</strong> Cet onglet extrait exclusivement les Champs d'Apprentissage (CA), compétences et Attendus des Bulletins Officiels (BO). La liberté pédagogique reste sous l'entière responsabilité des équipes d'établissement.
        </span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px; line-height: 1.5;">
        <div style="color: #38BDF8; font-weight: 800; font-size: 14px; text-align: center; margin-bottom: 12px; letter-spacing: 0.5px;">🎯 OÙ POSER VOTRE QUESTION ?</div>
        <div style="display: flex; gap: 20px; color: #FCD34D; font-size: 13px;">
            <div style="flex: 1; border-right: 1px solid #334155; padding-right: 20px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">🛠️ Menu iPackEPS (Toute l'année)</strong><br>
                <span style="color: #FCD34D !important;">Technique de terrain : configuration, groupes, Saisie des notes brutes.</span><br>
                <div style="margin-top: 8px; padding: 5px 8px; background-color: rgba(248, 113, 113, 0.15); border-left: 3px solid #F87171; border-radius: 4px;">
                    <span style="color: #F87171 !important; font-weight: 800;">⚠️ IMPORTANT INAPTITUDES :</span><br>
                    <span style="color: #FFFFFF !important; font-size: 12px;">Toutes les questions sur les certificats médicaux, dispenses et saisies d'inaptitude se posent TOUJOURS ici !</span>
                </div>
            </div>
            <div style="flex: 1; padding-left: 5px;">
                <strong style="color: #FFFFFF !important; font-size: 14px;">📊 Menu Examens & Santorin (Fin d'année)</strong><br>
                <span style="color: #FCD34D !important;">Administration des examens : remontée officielle du Bac/DNB, correction numérique sur Arena, arbitrages de la CAHPN.</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ======================================================================
# 8. ZONE D'ACTION
# ======================================================================
col_action_clear, col_action_input = st.columns([1, 4.5], gap="small")
with col_action_clear:
    st.markdown('<div class="nettoyer-wrapper"></div>', unsafe_allow_html=True)
    if st.button("🧹 Nettoyer", key="clear_all"): st.cache_resource.clear(); st.session_state.messages_hub = []; st.rerun()

with col_action_input: prompt = st.chat_input("Posez votre question institutionnelle, technique ou juridique ici...", key="chat_main")

st.markdown('<div style="background-color: #1E293B; padding: 12px 20px; border-radius: 6px; box-shadow: 0px 4px 8px rgba(0,0,0,0.2); margin-top: 10px; border: 1px solid rgba(255, 255, 255, 0.05); text-align: center; line-height: 1.4;"><span style="color: #FCD34D; font-weight: 700; font-size: 13px;">⚠️ 💡 ATTENTION :</span><span style="color: #FFFFFF; font-weight: 500; font-size: 13px; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);"> Pour des raisons pratiques, votre assistant ne mémorise pas le fil de la conversation. Posez vos questions une par une.</span></div>', unsafe_allow_html=True)

# ======================================================================
# 9. FLUX DE MESSAGES ET TRAITEMENT IA
# ======================================================================
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        if m.get("type") == "video": st.video(m["content"])
        else: st.markdown(m["content"], unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ======================================================================
        # 9. FLUX DE MESSAGES ET TRAITEMENT IA (VERSION FINALE BLINDÉE)
        # ======================================================================
        st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
        for m in st.session_state.messages_hub:
            with st.chat_message(m["role"]): 
                if m.get("type") == "video": st.video(m["content"])
                else: st.markdown(m["content"], unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if prompt:
            st.session_state.messages_hub.append({"role": "user", "type": "text", "content": f"<span style='color: white;'>{prompt}</span>"})
            with st.spinner("Je recherche les documents..."):
                mode = st.session_state.active_module
                texte_brut = ""
                extraits_doc = ""
                bloc_liens_dynamique = ""  # 🛡️ Initialisation de sécurité pour éviter le crash
                
                verites_terrain_pierre = ""
                try:
                    for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
                        if os.path.exists(fp):
                            with open(fp, "r", encoding="utf-8", errors="ignore") as f: 
                                verites_terrain_pierre += f"\n--- REGLES DIRECTES DE PIERRE ---\n" + f.read() + "\n"
                except: pass

                # Aiguillage technique
                intention = "AUCUN_BLINDAGE"
                if mode == "examens":
                    intent_prompt = f"""Tu es l'aiguilleur technique. Question : "{prompt}". Sélectionne uniquement si c'est une panne : CALENDRIER, SANTORIN_ERREUR_VALIDATION, SANTORIN_GRISE, JURY_REMPLACEMENT, ou AUCUN_BLINDAGE."""
                    try: intention = Settings.llm.complete(intent_prompt).text.strip()
                    except: intention = "AUCUN_BLINDAGE"
                elif mode == "ipack":
                    intent_prompt = f"""Tu es l'aiguilleur iPack. Détermine : IPACK_SSS, IPACK_GROUPES, IPACK_NOUVEL_ELEVE, ou AUCUN_BLINDAGE."""
                    try: intention = Settings.llm.complete(intent_prompt).text.strip()
                    except: intention = "AUCUN_BLINDAGE"

                # Définition des flags
                est_cas_blindé = intention in ["CALENDRIER", "SANTORIN_ERREUR_VALIDATION", "SANTORIN_GRISE", "JURY_REMPLACEMENT", "IPACK_SSS", "IPACK_GROUPES", "IPACK_NOUVEL_ELEVE"]

                # RAG (Si pas de blindage)
                if not est_cas_blindé:
                    try:
                        retriever = {"examens": retriever_santorin, "ipack": retriever_ipack, "textes": retriever_textes, "peda": retriever_peda}.get(mode)
                        if retriever:
                            for n in retriever.retrieve(prompt): extraits_doc += f"{n.node.text}\n\n"
                    except: pass

                # Logique de rendu
                if intention == "CALENDRIER":
                    texte_brut = "<h3>📊 CALENDRIER & DATES</h3>Seuls les calendriers de la DEC font foi. Rapprochez-vous de votre secrétariat."
                    badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
                elif intention == "SANTORIN_GRISE":
                    texte_brut = "<h3>📊 CASES GRISÉES</h3>Attendez que le collègue ferme sa session ou dépliez le lot dans [Lots] > [Détail]."
                    badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
                # ... (ajoute ici tes autres petits blocs blindés si besoin)
                else:
                    # Moteur IA expert
                    if mode == "examens": badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
                    elif mode == "ipack": badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
                    elif mode == "textes": badge, color_card = "⚖️ SÉCURITÉ & CADRE JURIDIQUE", "securite-card"
                    else: badge, color_card = "🔍 CADRAGE & RÉFÉRENTIELS BO", "peda-card"

                    consigne_ia = f"""Réponds à l'enseignant en t'appuyant STRICTEMENT sur : {extraits_doc}. {verites_terrain_pierre}
                    Directives : 1. Non ferme si le texte l'indique. 2. Pas d'invention. 3. Format HTML propre."""
                    try: texte_brut = Settings.llm.complete(consigne_ia).text
                    except Exception as e: texte_brut = f"Erreur : {str(e)}"
                    texte_brut += f"\n\n{bloc_liens_dynamique}"

                # Post-traitement et affichage
                texte_brut = re.sub(r'(Article\s+\d+)', r'<span class="law-highlight">\1</span>', texte_brut)
                formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br>{texte_brut.replace(chr(10), "<br>")}</div>'
                st.session_state.messages_hub.append({"role": "assistant", "type": "text", "content": formatted_answer})
                st.rerun()
