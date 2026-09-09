import os
import requests
from google import genai

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
    print(f"Fichier {filepath} mis à jour et validé avec succès !")

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

    ipack_content = load_file("ipack.txt")
    examens_content = load_file("data/examens/regles_dnb_eps.txt")
    santorin_content = load_file("data/examens/memoire_examens_santorin.txt")

    print("2. Analyse globale et audit strict par Gemini...")
    
    prompt = f"""
[CONTEXTE INSTITUTIONNEL]
Tu es le gardien expert, rigoureux et certificateur de la base de connaissances du Hub EPS.
Ton rôle est d'analyser les interrogations de terrain sans jamais céder aux erreurs ou aux fausses rumeurs formulées par les utilisateurs.

[BASES DE CONNAISSANCES ACTUELLES]
--- FICHIER IPACK (ipack.txt) ---
{ipack_content}

--- FICHIER EXAMENS (data/examens/regles_dnb_eps.txt) ---
{examens_content}

--- FICHIER SANTORIN (data/examens/memoire_examens_santorin.txt) ---
{santorin_content}

[DERNIERS LOGS / QUESTIONS DE TERRAIN]
{logs_texte}

[INSTRUCTIONS DE CONTRÔLE ET DE ROUTAGE]
1. **FILTRE ANTI-ERREUR** : Si un utilisateur exprime une idée fausse (ex: demande d'autoriser la pluri-affectation interdite en CCF), rejette-la catégoriquement. Ne modifie les fichiers qu'en cas de vrai vide technique ou réglementaire avéré et conforme aux textes officiels.
2. **ZÉRO CONTRADICTION** : Toute modification doit s'intégrer harmonieusement sans contredire la doctrine en place.
3. **SORTIE** : Si tout est correct ou si les logs ne nécessitent aucun correctif officiel, réponds STRICTEMENT par : "RIEN_A_SIGNALER".
4. Sinon, réponds STRICTEMENT selon ce format précis :

CIBLE: [ipack, examens ou santorin]
CONTENU:
[L'intégralité du fichier cible mis à jour, unifié et nettoyé au format Markdown propre]
"""

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt
    )
    
    texte_reponse = response.text.strip()

    if "RIEN_A_SIGNALER" in texte_reponse or len(texte_reponse) < 20:
        print("✅ Aucun changement requis. Tout est carré !")
        return

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
