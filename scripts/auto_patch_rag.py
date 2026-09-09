import os
import requests
from google import genai

# Configuration de l'API Gemini avec le nouveau SDK officiel
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("La clé API GEMINI_API_KEY est manquante.")

client = genai.Client(api_key=api_key)
MODEL_ID = "gemini-3.6-flash"  # Modèle standard moderne supporté par le nouveau SDK

# Ton URL Google Apps Script pour récupérer les logs
URL_APPS_SCRIPT = "https://script.google.com/macros/s/AKfycbyVq8_DCLnAyrr7xEUw1Xbdze0Lm1S-P6RHlXJPE2CmaBD39lpFfQjpuHQhxmL0z3bJ/exec"

def load_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def sauver_patch(cible, contenu_patch):
    print(f"3. Écriture de la correction dans le fichier cible : {cible}...")
    contenu_actuel = load_file(cible)
    
    nouveau_contenu = contenu_actuel + f"\n\n======================================================================\nAJOUT AUTOMATIQUE (MULTIRAG - {cible})\n======================================================================\n{contenu_patch}\n"

    with open(cible, "w", encoding="utf-8") as f:
        f.write(nouveau_contenu)
    print(f"Fichier {cible} mis à jour avec succès !")

def analyser_et_patcher():
    print("1. Récupération des logs depuis Google Sheets...")
    try:
        response = requests.get(URL_APPS_SCRIPT)
        lignes = response.json()
    except Exception as e:
        print(f"Erreur de lecture du Sheet : {e}")
        return

    derniers_logs = [row.get("question", "") for row in lignes[-30:] if row.get("question")]
    if not derniers_logs:
        print("Aucune question trouvée dans les logs.")
        return
        
    logs_texte = "\n".join(f"- {q}" for q in derniers_logs)

    fichiers_ref = {
        "ipack": "ipack.txt",
        "examens": "data/examens/regles_dnb_eps.txt",
        "santorin": "data/examens/memoire_examens_santorin.txt"
    }

    print("2. Analyse intelligente et routage chirurgical par Gemini (Multi-RAG à 3 branches)...")
    prompt = f"""
[CONTEXTE]
Tu es l'IA auditrice de la "Ronde de nuit" pour Le Hub (assistant EPS, Collège, Lycée, iPackEPS, Santorin).
Ton rôle unique est d'analyser les logs récents pour corriger, enrichir et combler les angles morts de nos bases de connaissances.

[RÈGLES D'OR DE LA RONDE DE NUIT]
1. FILTRE DES ÉCHECS EN PRIORITÉ ABSOLUE : Analyse d'abord les interactions où le Hub a déclenché la clause de repli vers le SAV (ipackeps@ac-aix-marseille.fr) ou a émis une réponse d'incertitude. Ce sont les zones de friction critiques de terrain.
2. RÉSOLUTION OBLIGATOIRE : Pour chaque échec identifié, formule clairement la question bloquante, rédige la réponse technique, administrative ou procédurale exacte (en respectant l'étanchéité Collège/Lycée), et formate-la sous la forme d'un article ou d'une situation normée.
3. FILTRE ANTI-DOUBLON : Ne duplique pas une information déjà présente dans nos bases. 

[DERNIERS LOGS UTILISATEURS]
{logs_texte}

[CONSIGNES DE ROUTAGE ET DE SORTIE]
Tu dois déterminer si une mise à jour est nécessaire dans l'une de nos 3 cibles :
- `ipack` (application iPackEPS, outils, tableaux, scripts)
- `examens` (réglementation, textes officiels, épreuves, DNB, CCF)
- `santorin` (gestion des examens, copies, notes, plateformes Santorin/Cyclades)

Si une correction est indispensable, réponds STRICTEMENT selon ce format précis :
CIBLE: [ipack, examens ou santorin]
CONTENU:
[Le paragraphe au format Markdown propre prêt à être ajouté]

Si tout est déjà couvert ou qu'aucun correctif n'est nécessaire, réponds strictement par : "RIEN_A_SIGNALER".
"""
    
    # Appel de l'API avec la nouvelle syntaxe moderne du SDK google-genai
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt
    )
    texte_reponse = response.text.strip()
    
    if "RIEN_A_SIGNALER" in texte_reponse or len(texte_reponse) < 20:
        print("Aucun nouveau patch nécessaire. Tout est carré !")
        return

    cle_cible = None
    if "CIBLE: ipack" in texte_reponse:
        cle_cible = "ipack"
    elif "CIBLE: examens" in texte_reponse:
        cle_cible = "examens"
    elif "CIBLE: santorin" in texte_reponse:
        cle_cible = "santorin"
    else:
        print("Format de routage non reconnu par l'IA.")
        return

    cible_fichier = fichiers_ref.get(cle_cible)

    if "CONTENU:" in texte_reponse:
        contenu_patch = texte_reponse.split("CONTENU:")[1].strip()
    else:
        print("Balise CONTENU introuvable.")
        return

    if not contenu_patch:
        print("Le patch généré est vide.")
        return

    sauver_patch(cible_fichier, contenu_patch)

if __name__ == "__main__":
    analyser_et_patcher()
