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
# 🚀 ZONE 1 : LE RÉPERTOIRE DES VIDÉOS (CONSTANTE GLOBALE)
# ======================================================================
VIDEOS_TUTOS = {
    "import_eleves_pronote.mp4": "https://pole-examens.github.io/tutoriels-examens/res/import_eleves_pronote.mp4",
    "Configuration_classes_import_eleves.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Configuration_classes_import_eleves.mp4",
    "affecter_eleves_dans_groupes.mp4": "https://pole-examens.github.io/tutoriels-examens/res/affecter_eleves_dans_groupes.mp4",
    "Generer_importer_fichier_groupes_cyclades.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Generer_importer_fichier_groupes_cyclades.mp4",
    "creer_convocations_enseignants.mp4": "https://pole-examens.github.io/tutoriels-examens/res/creer_convocations_enseignants.mp4",
    "Distribution_lots_santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Distribution_lots_santorin.mp4",
    "Distribution_manuelle_lots_santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Distribution_manuelle_lots_santorin.mp4",
    "Verrouiller_lot_santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Verrouiller_lot_santorin.mp4",
    "Deverrouiller_lots_santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Deverrouiller_lots_santorin.mp4",
    "Ajouter_evaluateur_lot_santorin.mp4": "https://pole-examens.github.io/tutoriels-examens/res/Ajouter_evaluateur_lot_santorin.mp4"
}

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
    
    div.element-container:has(.nettoyer-wrapper) + div.element-container button {
        background-color: rgba(220, 38, 38, 0.45) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(220, 38, 38, 0.6) !important;
        border-radius: 8px !important;
        width: 100% !important;
        height: 38px !important;
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
""".replace('__URL_FOND__', f"{github_url}{img_fond}")
st.markdown(css_pur, unsafe_allow_html=True)

# ======================================================================
# 4. CONFIGURATION DE L'IA & LECTEUR CHIRURGICAL DES BASES
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
# 5. BANDEAU SUPERIEUR REHAUSSÉ
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
# 7B. MESSAGES D'AVERTISSEMENT
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
                <span style="color: #FCD34D !important;">Administration des examens : remontée officielle du Bac/DNB, correction numérique sur Arena, arbitrages de la CAHPN.</span><br>
                <div style="margin-top: 8px; padding: 5px 8px; background-color: rgba(56, 189, 248, 0.15); border-left: 3px solid #38BDF8; border-radius: 4px;">
                    <span style="color: #38BDF8 !important; font-weight: 800;">💡 Déblocage situation complexe &amp; Besoin d'informations :</span><br>
                    <span style="color: #FFFFFF !important; font-size: 12px;">Boutons grisés, lots bloqués ou questions de calcul de notes ? L'IA s'appuie sur les fiches de la DEC pour vous guider sereinement.</span>
                </div>
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
# 9. FLUX DE MESSAGES ET ARBITRAGE HYBRIDE INTEGRAL (SÉCURISÉ)
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
        badge, color_card = "INFORMATION", "general-card"
        bloc_liens_dynamique = ""
        
        # Détermination textuelle du nom de l'onglet pour la phrase de contexte
        onglets_noms = {
            "ipack": "l'onglet Assistance Technique iPackEPS (Gestion du CCF)",
            "examens": "l'onglet Réglementation Examens & Santorin (Copies Numérisées)",
            "peda": "l'onglet Référentiels Institutionnels, CA & Activités BO",
            "textes": "l'onglet Sécurité & Responsabilité Juridique (Textes Officiels)"
        }
        contexte_choisi_nom = onglets_noms.get(mode, "un onglet de l'application")
        
        verites_terrain_pierre = ""
        try:
            for fp in ["get_par_pierre.txt", "gere_par_pierre.txt"]:
                if os.path.exists(fp):
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f: 
                        verites_terrain_pierre += f"\n--- REGLES DIRECTES DE PIERRE ---\n" + f.read() + "\n"
        except: pass

        # 🧠 AIGUILLEUR MINIMALISTE INTERCEPTANT UNIQUEMENT LES PANNES TECHNIQUES D'INTERFACE
        intention = "AUCUN_BLINDAGE"
        if mode == "examens":
            intent_prompt = f"""Tu es l'aiguilleur technique du Hub. Détermine l'intention de cette question : "{prompt}"
            Sélectionne un mot-clé UNIQUEMENT si la question correspond strictement à l'une de ces pannes d'interface :
            - CALENDRIER : Demande explicite de date limite ou fermeture nationale des serveurs.
            - SANTORIN_ERREUR_VALIDATION : Le prof a déjà cliqué sur valider son lot et l'écran est bloqué/clos.
            - SANTORIN_GRISE : Boutons ou crayons grisés, problème de co-évaluation/correction partagée (cadenas).
            - JURY_REMPLACEMENT : Problème d'ordre de mission (OM), convocation Chorus ou prof remplaçant invisible.
            - SUJET_SECOURS : Demande d'impression, de téléchargement ou de recherche de sujet d'examen ou sujet écrit de secours.
            - AUCUN_BLINDAGE : TOUT LE RESTE (Réglementation, AFL, notation, dispense, inaptitude, cas d'élèves, élèves mutés, redoublants).
            """
            try: intention = Settings.llm.complete(intent_prompt).text.strip()
            except: intention = "AUCUN_BLINDAGE"
        elif mode == "ipack":
            intent_prompt = f"""Tu es l'aiguilleur d'iPackEPS. Détermine l'intention : "{prompt}"
            - IPACK_SSS : Le dossier SSS ou le bilan annuel est verrouillé en lecture seule by la direction.
            - IPACK_GROUPES : Procédure pas-à-pas pour configurer les classes/groupes ou imports XML Pronote.
            - IPACK_NOUVEL_ELEVE : Procédure pour injecter un nouvel élève arrivant via SIÈCLE.
            - AUCUN_BLINDAGE : Toute autre question générale.
            """
            try: intention = Settings.llm.complete(intent_prompt).text.strip()
            except: intention = "AUCUN_BLINDAGE"

        est_date_notes_direct = (intention == "CALENDRIER")
        est_erreur_validation_santorin = (intention == "SANTORIN_ERREUR_VALIDATION")
        est_grise_direct = (intention == "SANTORIN_GRISE")
        est_remplacement_reunion_direct = (intention == "JURY_REMPLACEMENT")
        est_sujet_secours_direct = (intention == "SUJET_SECOURS")
        est_sss_direct = (intention == "IPACK_SSS")
        st_groupes_direct = (intention == "IPACK_GROUPES")
        est_nouvel_eleve_direct = (intention == "IPACK_NOUVEL_ELEVE")
        est_tasa_direct = (mode == "textes" and "tasa" in prompt.lower())
        
        est_cas_blindé_racine = (est_date_notes_direct or est_erreur_validation_santorin or est_grise_direct or est_remplacement_reunion_direct or est_sujet_secours_direct or est_sss_direct or st_groupes_direct or est_nouvel_eleve_direct or est_tasa_direct)

        # Interrogation vectorielle RAG (Pour toutes les questions réglementaires)
        if openai_api_key and not est_cas_blindé_racine:
            try:
                if mode == "examens":
                    for n in retriever_santorin.retrieve(prompt): extraits_doc += f"{n.node.text}\n\n"
                elif mode == "ipack":
                    for n in retriever_ipack.retrieve(prompt): extraits_doc += f"{n.node.text}\n\n"
                elif mode == "textes":
                    mot_cle_local = prompt.lower()
                    for exp in expressions_inutiles: mot_cle_local = mot_cle_local.replace(exp, "")
                    for n in retriever_textes.retrieve(mot_cle_local.strip() if len(mot_cle_local.strip()) > 2 else prompt): extraits_doc += f"{n.node.text}\n\n"
                elif mode == "peda":
                    for n in retriever_peda.retrieve(prompt): extraits_doc += f"{n.node.text}\n\n"
            except: pass

        # ======================================================================
        # 🎯 ROUTAGE FINAL DU RENDU (AVEC INJECTION DES BULLES EN DUR & MP4)
        # ======================================================================
        if est_tasa_direct:
            texte_brut = extraits_doc; badge, color_card = "⚖️ TEXTES OFFICIELS", "securite-card"
            
        elif est_date_notes_direct:
            texte_brut = "<h3>📊 CALENDRIER & DATES DE REMISE DES NOTES</h3><strong>Statut administratif : Spécificités académiques locales.</strong><br>Les dates limites de saisie étant différentes pour chaque académie, rapprochez-vous de vos coordonnateurs ou de votre secrétariat de direction. Seuls les calendriers émis par la Division des Examens et Concours (DEC) font foi."
            badge, color_card = ("📊 EXAMENS & SANTORIN" if mode == "examens" else "🛠️ PROTOCOLE IPACK"), ("santorin-card" if mode == "examens" else "general-card")
            
        elif est_erreur_validation_santorin:
            texte_brut = """<h3>📊 EXAMENS & SANTORIN : ERREUR DE SAISIE APRÈS VALIDATION</h3><strong>Statut administratif : Clôture définitive du lot par le correcteur.</strong><br><ul><li><strong>Étape 1 :</strong> Ne tentez pas de manipuler l'interface. Prévenez immédiatement le secrétariat de direction de votre établissement (Chef d'établissement).</li><li><strong>Étape 2 :</strong> Le chef d'établissement doit contacter le gestionnaire de la Division des Examens et Concours (DEC) pour demander un <strong>[Renvoi en modification]</strong>.</li><li>⚠️ Après arbitrage de la commission, le chef d'établissement déverrouille le lot informatique, permettant ainsi au professeur de saisir la note définitive arrêtée.</li></ul><br>📺 <strong>Tutoriel de déblocage :</strong> Deverrouiller_lots_santorin.mp4 (Processus inverse de clôture : Verrouiller_lot_santorin.mp4)"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif est_sss_direct:
            texte_brut = "<h3>🛠️ IPACKEPS : DOSSIER SSS OU BILAN VERROUILLÉ</h3><strong>Statut : Lecture seule absolue.</strong><br>Contactez immédiatement votre Correspondant iPackEPS de bassin ou l'équipe des IA-IPR. Seuls ces profils possèdent les droits master pour appliquer la commande <strong>[Renvoyer en modification]</strong>."
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"

        elif st_groupes_direct:
            texte_brut = "<h3>🛠️ IPACKEPS : CONFIGURATION DES CLASSES ET GROUPES</h3>➔ Étape 1 : Accédez au menu supérieur **[Dossiers]**.<br>➔ Étape 2 : Allez dans **[Dossier EPS]** > **[Classes]** > **[Configuration des Classes]**.<br>➔ Étape 3 : Importez le fichier d'extraction Pronote ou SIÈCLE dans le module **[Mes Élèves]**.<br><br>📺 <strong>Tutoriels d'accompagnement :</strong> Configuration_classes_import_eleves.mp4 et affecter_eleves_dans_groupes.mp4"
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
            
        elif est_nouvel_eleve_direct:
            texte_brut = "<h3>🛠️ IPACKEPS : AJOUTER UN ÉLÈVE ARRIVANT</h3>L'élève doit être enregistré dans <strong>SIÈCLE</strong> par le secrétariat. Effectuez ensuite une mise à jour via un nouvel import XML/CSV depuis Pronote pour l'intégrer automatiquement sans écraser vos notes.<br><br>📺 <strong>Tutoriel d'accompagnement :</strong> import_eleves_pronote.mp4"
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
            
        elif est_grise_direct:
            texte_brut = """<h3>📊 EXAMENS & SANTORIN : CASES OU CRAYONS GRISÉS</h3><ul><li><strong>Correction partagée :</strong> Si un collègue édite le lot, l'interface bascule en lecture seule. <strong>Solution : Attendez qu'il ferme sa session Arena.</strong></li><li><strong>Lot non déplié :</strong> Allez dans [Lots] > [Voir le détail] et cliquez sur le nom du candidat pour activer la grille de notation.</li></ul><br>📺 <strong>En cas de besoin de co-évaluation ou de transfert :</strong> Ajouter_evaluateur_lot_santorin.mp4"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        elif est_remplacement_reunion_direct:
            texte_brut = "<h3>📊 EXAMENS : REMPLACEMENT EN JURY</h3>L'établissement doit enregistrer la suppléance sur **Imag'in** et générer le PDF de convocation. C'est ce clic technique qui transmet instantanément vos droits d'écriture vers Santorin.<br><br>📺 <strong>Tutoriel de gestion des convocations :</strong> creer_convocations_enseignants.mp4"
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"

        elif est_sujet_secours_direct:
            texte_brut = """<h3>⚠️ CONFIGURATION EXAMEN : PAS DE SUJET ÉCRIT EN EPS</h3><strong>Règle de gestion nationale :</strong> En Éducation Physique et Sportive (CCF ou épreuve ponctuelle), il n'existe <strong>aucun sujet de secours papier ou écrit</strong> à télécharger ou à imprimer depuis iPackEPS ou Cyclades.<br><br><ul><li><strong>S'il s'agit d'un élève absent justifié (ABJ) :</strong> Il ne faut pas lui imprimer un sujet papier, mais organiser une <strong>Épreuve de substitution</strong> (rattrapage de l'évaluation motrice sur le terrain) avant le verrouillage des notes.</li><li><strong>S'il s'agit des grilles d'évaluation de l'équipe :</strong> Elles se trouvent dans votre projet pédagogique EPS d'établissement. Aucun sujet externe n'est fourni par la DEC.</li></ul>"""
            badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            
        else:
            if mode == "examens": badge, color_card = "📊 EXAMENS & SANTORIN", "santorin-card"
            elif mode == "ipack": badge, color_card = "🛠️ ASSISTANCE iPACKEPS", "general-card"
            elif mode == "textes": badge, color_card = "⚖️ SÉCURITÉ & CADRE JURIDIQUE", "securite-card"
            else: badge, color_card = "🔍 CADRAGE & RÉFÉRENTIELS BO", "peda-card"

            if mode == "examens" and not extraits_doc.strip():
                texte_brut = "Désolé, je ne trouve pas cette règle spécifique dans ma mémoire locale d'examen. Veuillez vous rapprocher de votre direction ou de votre IA-IPR EPS."
            else:
                consigne_ia = f"""Tu es l'assistant IA référent expert pour les examens EPS de l'académie d'Aix-Marseille.
                Réponds de façon claire, structurée et chirurgicale à l'enseignant en t'appuyant STRICTEMENT sur le contexte fourni.
                
                CONTEXTE DE RÉFÉRENCE LOCAL (SOURCE DE VÉRITÉ ABSOLUE) :
                {extraits_doc}
                {verites_terrain_pierre}
                
                QUESTION DE L'ENSEIGNANT :
                {prompt}
                
                DIRECTIVES COMPORTEMENTALES STRICTES :
                1. Ta réponse doit s'aligner à 100% sur les extraits fournis. Si le contexte mentionne une procédure spécifique (comme le cas de la 'NOTE UNIQUE' où il faut cocher [Dispensé] pour les épreuves manquantes et ajouter obligatoirement un commentaire de justification dans Santorin), tu dois IMPÉRATIVEMENT détailler ces étapes techniques et ces obligations à l'enseignant. Ne résume pas le protocole.
                2. 🔒 PRINCIPE DE NON-EXTRAPOLATION : Ne propose JAMAIS de solution technique, pédagogique ou de rattrapage de ton propre chef. Si le contexte fourni ne mentionne pas explicitement qu'une action ou une épreuve supplémentaire est autorisée, considère qu'elle est interdite. Renvoie systématiquement vers l'arbitrage de la CAHPN ou du Chef d'établissement.
                3. 🛑 DEMANDE DE REFORMULATION : N'active cette directive QUE si la question contient strictement des formules syntaxiques brutes (ex: "DI+DI+14") ou des suites de sigles collés par des opérateurs (+, /, -) sans texte autour. Si la question est rédigée en français clair avec des mots entiers (ex: "absence justifiée", "dispensé", "une seule note"), tu dois IMPÉRATIVEMENT y répondre normalement en appliquant la règle de la "Note Unique" présente dans ton contexte, sans bloquer l'utilisateur."
                4. Discrimine les filières (Bac GT, Bac Pro, CAP, DNB/Collège). Au collège, rappelle que le CCF n'existe pas.
                5. Utilise des puces HTML (<ul>, <li>) et des mots en gras (<strong>) pour isoler les étapes. Pas de balise <html> globale.
                6. 📺 MENTION DES VIDÉOS : Si le contexte de référence contient un nom de fichier vidéo en `.mp4` (ex: Distribution_manuelle_lots_santorin.mp4), tu dois IMPÉRATIVEMENT l'écrire textuellement dans ta réponse pour que l'interface active le lecteur vidéo compagnon.
                7. 🛑 BLINDAGE ANTI-PIÈGE / HORS-SUJET : Si la question de l'utilisateur est loufoque, provocatrice, ou totalement déconnectée de la gestion, de la réglementation, de la sécurité ou de la pédagogie de l'EPS (ex: recettes de cuisine, questions de culture générale générale, blagues, programmation informatique pure sans lien avec l'EPS), tu dois IMPÉRATIVEMENT répondre cette phrase exacte et rien d'autre : "Le Hub IA - EPS est un outil exclusivement dédié à l'accompagnement réglementaire, technique et pédagogique de la discipline. Votre demande sort du cadre d'exercice et de certification des enseignants d'Éducation Physique et Sportive."
                """
                try:
                    response = Settings.llm.complete(consigne_ia)
                    texte_brut = response.text
                except Exception as e:
                    texte_brut = f"Erreur de traitement IA : {str(e)}"

        # Traitements de surface et filtres regex
        texte_brut = re.sub(r'(Article\s+\d+[-–\w]*|Loi\s+du\s+\d+\s+\w+\s+\d+|RGPD|Code\s+de\s+l\'éducation)', r'<span class="law-highlight">\1</span>', texte_brut)
        texte_brut = texte_brut.replace('<span class="law-highlight"><span class="law-highlight">', '<span class="law-highlight">').replace('</span></span>', '</span>')
        re_links = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">\1</a>', texte_brut)
        texte_brut = re_links
        
        texte_final = texte_brut.replace("\n", "").replace("\r", "").replace("<p>", "").replace("</p>", "<br>").replace(chr(10), "<br>")
        
        # Construction de la réponse avec la phrase de contexte en premier plan
        phrase_contexte = f"<div style='font-size: 12.5px; color: #94A3B8; margin-bottom: 10px; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 5px;'>📍 <em>Vous avez choisi de poser votre question dans {contexte_choisi_nom}.</em></div>"
        formatted_answer = f'<div class="{color_card}">{phrase_contexte}<strong>{badge} :</strong><br>{texte_final}</div>'
        
        st.session_state.messages_hub.append({"role": "assistant", "type": "text", "content": formatted_answer})
        
        # ======================================================================
        # 🚀 ZONE 2 : DÉTECTEUR AUTOMATIQUE DE CAPSULES VIDÉOS (DEPUIS TEXTE FINAL)
        # ======================================================================
        for video_name, video_url in VIDEOS_TUTOS.items():
            if video_name in texte_final:
                st.session_state.messages_hub.append({"role": "assistant", "type": "video", "content": video_url})
                
        st.rerun()
