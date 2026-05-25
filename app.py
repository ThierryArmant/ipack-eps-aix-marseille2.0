import streamlit as st
import os
import pandas as pd
import requests
import re
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

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
    /* Force le blanc sur tout le texte des cartes */
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
    
    .hub-title h1 { 
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
        line-height: 1 !important;
        display: inline-block;
        box-shadow: 0px 0px 8px rgba(16, 185, 129, 0.2);
    }
    
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
    
    /* Boutons Inactifs */
    button[kind="secondary"] { 
        background-color: rgba(15, 23, 42, 0.9) !important; 
        color: #94A3B8 !important; 
        border: 1px solid rgba(255,255,255,0.05) !important; 
        border-radius: 8px !important; 
        font-size: 12px !important; 
        padding: 0px 4px !important;
        height: 44px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        transition: all 0.3s ease;
    }

    /* Boutons Actifs */
    button[kind="primary"] {
        background-color: rgba(16, 185, 129, 0.85) !important;
        color: #FFFFFF !important;
        border: 1px solid #10B981 !important;
        border-radius: 8px !important; 
        font-size: 12px !important; 
        padding: 0px 4px !important;
        height: 44px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
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
    .santorin-card strong, .general-card strong, .securite-card strong { font-weight: 700 !important; }

    .santorin-card a, .general-card a, .securite-card a * {
        color: #FFB020 !important; 
        text-decoration: underline !important;
        font-weight: 600 !important;
    }
    
    /* Bulle Utilisateur */
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) { 
        background-color: rgba(255, 255, 255, 0.15) !important; 
        backdrop-filter: blur(6px) !important;
        border-radius: 14px 14px 0px 14px !important; 
        margin-left: 15% !important; 
    }
    div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
    div[data-testid="stChatMessage"] * { color: #FFFFFF !important; }

    /* ANCRAGE GHOST EN BAS À GAUCHE DISCRET SUR LE PARQUET */
    div[data-testid="stExpander"] {
        position: fixed !important;
        bottom: 12px !important;
        left: 16px !important;
        width: auto !important;
        min-width: 250px !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        z-index: 999999 !important;
        margin: 0 !important;
    }
    div[data-testid="stExpander"] summary p {
        color: rgba(148, 163, 184, 0.4) !important;
        font-weight: 700 !important;
        font-size: 11px !important;
    }
    div[data-testid="stExpander"] summary:hover p { color: #38BDF8 !important; }
    div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {
        font-size: 11px !important;
        font-family: monospace !important;
        color: rgba(56, 189, 248, 0.7) !important;
    }
    </style>
""".replace('__URL_FOND__', f"{github_url}{img_fond}")

st.markdown(css_pur, unsafe_allow_html=True)

# ======================================================================
# 4. CONFIGURATION DE L'INTELLIGENCE ARTIFICIELLE & LECTURE DU CERVEAU
# ======================================================================
openai_api_key = st.secrets.get("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY")

if openai_api_key:
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0, api_key=openai_api_key)

def trouver_chemin_pierre():
    for ch in ["gere_par_pierre.txt", "data/gere_par_pierre.txt"]:
        if os.path.exists(ch): return ch
    return None

chemin_detecte = trouver_chemin_pierre()
contenu_global_pierre = ""
status_radar = "❌ ERREUR : Fichier 'gere_par_pierre.txt' introuvable."

if chemin_detecte:
    for encodage in ["utf-8", "utf-8-sig", "latin-1", "utf-16", "cp1252"]:
        try:
            with open(chemin_detecte, "r", encoding=encodage) as f:
                texte_charge = f.read()
            if texte_charge.strip():
                contenu_global_pierre = texte_charge
                status_radar = f"📁 CERVEAU EMBARQUÉ : {len(contenu_global_pierre)} caractères actifs."
                break
        except: continue

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
    "peda": "🔍 Mode Actif : Questions Pédagogiques, Didactiques & Pratiques de Terrain",
    "textes": "🔒 Mode Actif : Sécurité & Responsabilité Juridique (Textes Officiels & Risques APPN)"
}

titre_affiche = label_titres.get(st.session_state.active_module, "🔍 Mode Actif : Questions Pédagogiques")

st.markdown(f"""
    <div class="column-title-top">
        <span class="instruction">⚙️ Choisissez le contexte de votre question ci-dessous</span>
        <span class="mode-actuel">{titre_affiche}</span>
    </div>
""", unsafe_allow_html=True)

# ======================================================================
# 7. BOUTONS DE CONTEXTE
# ======================================================================
col_b1, col_b2, col_b3, col_b4 = st.columns(4, gap="small")

with col_b1:
    if st.button("🛠️ iPackEPS", use_container_width=True, key="btn_ip", type="primary" if st.session_state.active_module == "ipack" else "secondary"):
        st.session_state.active_module = "ipack"
        st.session_state.messages_hub = []
        st.rerun()

with col_b2:
    if st.button("📊 Examens & Santorin", use_container_width=True, key="btn_ex", type="primary" if st.session_state.active_module == "examens" else "secondary"):
        st.session_state.active_module = "examens"
        st.session_state.messages_hub = []
        st.rerun()

with col_b3:
    if st.button("🔍 Pédagogie & Didactique", use_container_width=True, key="btn_ge", type="primary" if st.session_state.active_module == "peda" else "secondary"):
        st.session_state.active_module = "peda"
        st.session_state.messages_hub = []
        st.rerun()

with col_b4:
    if st.button("🔒 Sécurité & Réglementation", use_container_width=True, key="btn_se", type="primary" if st.session_state.active_module == "textes" else "secondary"):
        st.session_state.active_module = "textes"
        st.session_state.messages_hub = []
        st.rerun()

# ======================================================================
# 8. ZONE D'ACTION
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
# 9. FLUX DE MESSAGES ET TRAITEMENT IA INTEGRAL (SANS DECOUPAGE)
# ======================================================================
st.markdown('<div style="margin-top: 20px;">', unsafe_allow_html=True)
for m in st.session_state.messages_hub:
    with st.chat_message(m["role"]): 
        if isinstance(m["content"], str) and m["content"].startswith("VIDEO_URL:"):
            st.video(m["content"].replace("VIDEO_URL:", "").strip())
        else:
            st.markdown(m["content"], unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if prompt:
    st.session_state.messages_hub.append({"role": "user", "content": f"<span style='color: white;'>{prompt}</span>"})
    
    with st.spinner("Analyse immédiate de la base de connaissances..."):
        extraits_doc = ""
        mode = st.session_state.active_module
        
        # 1. MOTEUR WEB EN APPOINT (Tavily)
        if tavily_api_key:
            try:
                domaine_eps_france = ["eduscol.education.gouv.fr"]
                payload = {"api_key": tavily_api_key, "query": prompt, "search_depth": "advanced", "include_domains": domaine_eps_france}
                res = requests.post("https://api.tavily.com/search", json=payload, timeout=10)
                if res.status_code == 200:
                    for item in res.json().get("results", []): 
                        extraits_doc += f"Source Web ({item['title']}): {item['content']} - URL: {item['url']}\n\n"
            except: pass

        # 2. INJECTION INTEGRALE FORCEE DU CERVEAU DE PIERRE (100% FIABLE)
        if contenu_global_pierre.strip():
            extraits_doc += f"\n--- MEMOIRE ADMINISTRATIVE INTEGRALE DE PIERRE ---\n{contenu_global_pierre}\n"

        # 3. DIRECTIVES DE POSTURE IA
        règles_or = "RÈGLES D'OR : 1. Loi 1937 (Substitution État). 2. Règle 11 (Structure=Mairie/EPI=Prof). 3. Examens = Mission impérative."
        filtre_pierre = (
            "\n\nMÉTHODE DE RÉPONSE OBLIGATOIRE (Le 'Filtre Pierre') :\n"
            "1. ANALYSE DES RISQUES : Identifie l'impact sur outils tiers ou blocages de protocoles.\n"
            "2. PROCÉDURE TECHNIQUE : Utilise des étapes fléchées (→).\n"
            "3. PROTECTION FONCTIONNELLE : Indique la traçabilité administrative."
        )
        
        consigne_extraction_video = (
            "\n\n🎥 DIRECTIVE STRICTE DE SELECTION VIDÉO :\n"
            "- Parcoure la Mémoire de Pierre ci-dessus.\n"
            "- Trouve le ou les liens YouTube associés au sujet.\n"
            "- Inclus-le impérativement à la fin au format Markdown : '[Regarder le tutoriel vidéo associé](URL)'.\n"
            "- INTERDICTION : N'invente jamais d'URL ou de texte générique."
        )
        
        if mode == "ipack":
            consigne_ia = f"{règles_or}{filtre_pierre}\nTu es l'expert technique iPackEPS.{consigne_extraction_video}\n\nContexte : {extraits_doc}\nQuestion : {prompt}"
            badge, color_card = "🛠️ PROTOCOLE IPACK", "general-card"
        elif mode == "examens":
            consigne_ia = f"{règles_or}{filtre_pierre}\nTu es l'expert Santorin/Cyclades.\nCanva: [Acteur|Action|Conséquence].{consigne_extraction_video}\n\nContexte: {extraits_doc}\nQuestion: {prompt}"
            badge, color_card = "📊 RÉGLEMENTATION SANTORIN", "santorin-card"
        elif mode == "textes":
            consigne_ia = f"{règles_or}{filtre_pierre}\nTu es l'expert juridique EPS.\nCanva: 1. SITUATION, 2. ARBITRAGE, 3. RECOURS.{consigne_extraction_video}\n\nContexte: {extraits_doc}\nQuestion: {prompt}"
            badge, color_card = "⚖️ CADRE JURIDIQUE", "securite-card"
        else:
            consigne_ia = f"{règles_or}{filtre_pierre}\nTu es l'Expert Pédagogique EPS.\nContexte: {extraits_doc}\nQuestion : {prompt}"
            badge, color_card = "🔍 CONSEILLER PÉDAGOGIQUE", "general-card"

        # 4. EXÉCUTION
        response = Settings.llm.complete(consigne_ia)
        texte_brut = response.text
        
        youtube_links = re.findall(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11}))', texte_brut)
        texte_brut = re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2" target="_blank" style="color: #FFB020 !important; text-decoration: underline;">\1</a>', texte_brut)
        
        # CONVERTISSEUR DE TABLEAUX
        lignes_originales = texte_brut.split("\n")
        lignes_transformees = []
        en_dans_tableau = False
        est_entete_tableau = True
        
        for l_actuelle in lignes_originales:
            l_nettoye = l_actuelle.strip()
            if l_nettoye.startswith("|") and l_nettoye.count("|") >= 2:
                if "---" in l_nettoye: continue
                if not en_dans_tableau:
                    en_dans_tableau = True
                    lignes_transformees.append('<table style="width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px; background-color: rgba(30, 41, 59, 0.7); border-radius: 8px; overflow: hidden; border: 1px solid rgba(56, 189, 248, 0.3);">')
                    est_entete_tableau = True
                cellules = [c.strip() for c in l_nettoye.split("|")][1:]
                if cellules and cellules[-1] == "": cellules.pop()
                ligne_html = "<tr>"
                for cell in cellules:
                    if est_entete_tableau:
                        ligne_html += f'<th style="background-color: #38BDF8 !important; color: #0F172A !important; padding: 12px 10px; text-align: left; font-size: 14px; font-weight: 700; border-bottom: 2px solid #0284C7;">{cell}</th>'
                    else:
                        ligne_html += f'<td style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #FFFFFF !important; font-size: 14px;">{cell}</td>'
                ligne_html += "</tr>"
                lignes_transformees.append(ligne_html)
                est_entete_tableau = False
            else:
                if en_dans_tableau:
                    lignes_transformees.append("</table>")
                    en_dans_tableau = False
                lignes_transformees.append(l_actuelle)
                
        if en_dans_tableau: lignes_transformees.append("</table>")
            
        texte_brut = "\n".join(lignes_transformees)
        texte_html = texte_brut.replace(chr(10), "<br>")
        formatted_answer = f'<div class="{color_card}"><strong>{badge} :</strong><br><br>{texte_html}</div>'
        st.session_state.messages_hub.append({"role": "assistant", "content": formatted_answer})
        
        for link in youtube_links:
            st.session_state.messages_hub.append({"role": "assistant", "content": f"VIDEO_URL:{link[0]}"})
        
        st.rerun()

# ======================================================================
# 10. ZONE TECHNIQUE GHOST (DISCRÈTE EN BAS À GAUCHE)
# ======================================================================
with st.expander("🛠️"):
    st.write(status_radar)
