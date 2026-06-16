import os
from pypdf import PdfReader

def extraire_pdf_to_utf8(nom_pdf, dossier_destination):
    if not os.path.exists(nom_pdf):
        print(f"Erreur : Le fichier {nom_pdf} est introuvable.")
        return

    os.makedirs(dossier_destination, exist_ok=True)
    nom_sortie = os.path.join(dossier_destination, "base_officielle_santorin_marseille.txt")
    
    print(f"Extraction de {nom_pdf} en cours...")
    reader = PdfReader(nom_pdf)
    
    with open(nom_sortie, "w", encoding="utf-8") as f:
        # Écriture de la directive de souveraineté en tête de fichier pour le RAG
        f.write("======================================================================\n")
        f.write("BASE DOCUMENTAIRE OFFICIELLE - NOTATION EPS CCF (DIEC AIX-MARSEILLE)\n")
        f.write("======================================================================\n\n")
        
        for i, page in enumerate(reader.pages):
            texte_page = page.extract_text()
            f.write(f"--- RÈGLES OFFICIELLES SANTORIN - SECTION EXTRAITE {i+1} ---\n")
            f.write(texte_page)
            f.write("\n\n")
            
    print(f"Succès ! Fichier texte UTF-8 généré ici : {nom_sortie}")

# Exécution de l'extraction
extraire_pdf_to_utf8(
    nom_pdf="SANTORIN - bac 2024 - Gestion de la notation EPS CCF (2).pdf",
    dossier_destination="data/examens"
)
