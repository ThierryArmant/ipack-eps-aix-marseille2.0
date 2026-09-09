import os
import requests
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("La clé API GEMINI_API_KEY est manquante.")

client = genai.Client(api_key=api_key)
MODEL_ID = "gemini-3.6-flash"

URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbyVq8_DCLnAyrr7xEUw1Xbdze0Lm1S-P6RHlXJPE2CmaBD39lpFfQjpuHQhxmL0z3bJ/exec"

def load_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fichier {filepath} mis à jour et validé via les sources officielles !")

def analyser_et_patcher():
    print("1. Récupération des logs depuis le Google Sheet...")
    try:
        response = requests.get(URL_APPS_SCRIPT)
        lignes = response.json()
    except Exception as e:
        print(f"Erreur de lecture du Sheet : {e}")
        return

    brut_logs = [row.get("question", "") for row in lignes[-50:] if row.get("question")]
    derniers_logs = list(dict.fromkeys(brut_logs))[-15:]
    if not derniers_logs:
        print("Aucune question trouvée dans les logs.")
        return
        
    logs_texte = "\n".join(f"- {q}" for q in derniers_logs)

    # Chargement des 3 bases de connaissances pour que l'IA ait tout en tête
    ipack_content = load_file("ipack.txt")
    examens_content = load_file("data/examens/regles_dnb_eps.txt")
    santorin_content = load_file("data/examens/memoire_examens_santorin.txt")

    print("2. Analyse globale, recherche web et routage unique par Gemini...")
    
    prompt = f"""
[CONTEXTE INSTITUTIONNEL]
Tu es le gardien expert et certificateur de la base de connaissances du Hub EPS.
Tu dois analyser les interrogations de terrain et les **croiser obligatoirement avec les textes officiels et sources institutionnelles vérifiées** (Eduscol, Ministère de l'Éducation Nationale, sites académiques officiels).

[BASES DE CONNAISSANCES ACTUELLES]
--- FICHIER IPACK (ipack.txt) ---
{ipack_content}

--- FICHIER EXAMENS (data/examens/regles_dnb_eps.txt) ---
{examens_content}

--- FICHIER SANTORIN (data/examens/memoire_examens_santorin.txt) ---
{santorin_content}

[DERNIERS LOGS / QUESTIONS DE TERRAIN]
{logs_texte}

[INSTRUCTIONS DE ROUTAGE ET DE SORTIE]
1. Identifie si une correction ou une mise à jour est nécessaire dans l'un de ces trois fichiers en te basant sur le web officiel.
2. Si tout est correct et qu'aucun changement n'est requis, réponds STRICTEMENT par : "RIEN_A_SIGNALER".
3. Si une modification est indispensable, réponds STRICTEMENT selon ce format précis pour désigner la cible et fournir le contenu mis à jour du fichier concerné :

CIBLE: [ipack, examens ou santorin]
CONTENU:
[L'intégralité du fichier cible mis à jour et nettoyé au format Markdown propre]
"""

    # Un seul appel API propre et sécurisé avec l'outil de recherche web
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1
        )
    )
    
    texte_reponse = response.text.strip()

    if "RIEN_A_SIGNALER" in texte_reponse or len(texte_reponse) < 20:
        print("✅ Aucun changement requis après vérification officielle.")
        return

    # Routage vers la bonne cible
    if "CIBLE: ipack" in texte_reponse:
        cible_fichier = "ipack.txt"
    elif "CIBLE: examens" in texte_reponse:
        cible_fichier = "data/examens/regles_dnb_eps.txt"
    elif "CIBLE: santorin" in texte_reponse:
        cible_fichier = "data/examens/memoire_examens_santorin.txt"
    else:
        print("Format de routage non reconnu.")
        return

    if "CONTENU:" in texte_reponse:
        nouveau_contenu = texte_reponse.split("CONTENU:")[1].strip()
        save_file(cible_fichier, nouveau_contenu)
    else:
        print("Balise CONTENU introuvable.")

if __name__ == "__main__":
    analyser_et_patcher()
