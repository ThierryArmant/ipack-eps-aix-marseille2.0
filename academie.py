"""Académie de l'utilisateur : le hub contient des consignes propres à Aix-Marseille.

Pour un utilisateur d'une autre académie, ces consignes doivent être présentées comme
des consignes d'Aix-Marseille, à vérifier auprès de sa propre division des examens,
jamais comme des règles générales (voir docs/portee_academique_2026-10-13.md).
"""
import json
from pathlib import Path

AIX = "Aix-Marseille"
NON_PRECISEE = "Non précisée"

ACADEMIES = [
    "Aix-Marseille", "Amiens", "Besançon", "Bordeaux", "Clermont-Ferrand", "Corse", "Créteil",
    "Dijon", "Grenoble", "Guadeloupe", "Guyane", "La Réunion", "Lille", "Limoges", "Lyon",
    "Martinique", "Mayotte", "Montpellier", "Nancy-Metz", "Nantes", "Nice", "Normandie",
    "Orléans-Tours", "Paris", "Poitiers", "Reims", "Rennes", "Strasbourg", "Toulouse",
    "Versailles", "Établissement français à l'étranger", "Autre",
]

# Adresse d'assistance iPackEPS connue par académie ; sinon renvoi à l'assistance de l'académie.
ASSISTANCE_IPACK = {
    "Aix-Marseille": "ipackeps@ac-aix-marseille.fr",
    "Créteil": "ipackeps@ac-creteil.fr",
}


def _charger_portee(chemin="config/portee_academique.json"):
    try:
        return json.loads(Path(chemin).read_text(encoding="utf-8")).get("fichiers", {})
    except (OSError, ValueError):
        return {}


FICHIERS_AIX = set(_charger_portee())


def titres_aix(catalogue):
    """Titres du catalogue dont la fiche contient une consigne propre à Aix."""
    return {md.get("title") for chemin, md in catalogue.items() if chemin in FICHIERS_AIX and md.get("title")}


def est_aix(academie):
    return (academie or AIX) == AIX


def note_academie(academie):
    """Consigne à transmettre au modèle quand l'utilisateur n'est pas d'Aix-Marseille ; vide sinon."""
    if est_aix(academie):
        return ""
    nom = academie if academie not in ("Autre", "Établissement français à l'étranger", NON_PRECISEE) else None
    texte = (
        f"Académie de l'utilisateur : {academie}. "
        "Les documents contiennent des consignes propres à l'académie d'Aix-Marseille : DIEC d'Aix-Marseille, "
        "bulletins académiques d'Aix, circuit iPackEPS → Cyclades → Santorin piloté par l'inspection d'Aix, "
        "portail ESTEREL, adresse ipackeps@ac-aix-marseille.fr, dates et calendriers d'Aix. "
        "Pour cet utilisateur, ne jamais les présenter comme applicables : les signaler comme « consigne de l'académie "
        "d'Aix-Marseille » et renvoyer à la division des examens et à l'inspection EPS "
        + (f"de l'académie de {nom}. " if nom else "de son académie de rattachement. ") +
        "Les textes nationaux (Bulletin officiel) et le fonctionnement des logiciels nationaux (Santorin, Cyclades, "
        "Imag'in, iPackEPS) restent valables."
    )
    if academie == "Nice":
        texte += (" Aix-Marseille et Nice forment une région académique ; les consignes de l'inspection EPS et le "
                  "circuit iPackEPS d'Aix ne sont pas pour autant confirmés pour Nice.")
    return texte


def avertissement_reponse_directe(academie):
    """Paragraphe affiché avant une réponse relue fondée sur une consigne d'Aix."""
    if est_aix(academie):
        return ""
    lieu = ("dans votre académie de rattachement" if academie in ("Autre", "Établissement français à l'étranger", NON_PRECISEE)
            else f"dans l'académie de {academie}")
    return ("Attention : cette réponse repose sur une consigne de l'académie d'Aix-Marseille. "
            f"{lieu[0].upper() + lieu[1:]}, vérifiez-la auprès de votre division des examens et de votre inspection EPS.")


def adresse_assistance(academie):
    return ASSISTANCE_IPACK.get(academie or AIX, "")


def academy_context(question, selected):
    """L'académie déclarée par le collègue prime sur le menu ; les exemples restent des exemples."""
    import re
    import unicodedata
    def norm(value):
        value = ''.join(c for c in unicodedata.normalize('NFKD', value.lower())
                        if not unicodedata.combining(c))
        return re.sub(r"[’']", "'", value).replace('-', ' ')
    q = norm(question)
    declared = []
    for name in ACADEMIES:
        if name in ('Autre', "Établissement français à l'étranger"):
            continue
        place = re.escape(norm(name)).replace(r'\ ', r'[\s-]+')
        pattern = (r"(?:je suis|j'enseigne|je travaille|nous sommes|nous travaillons|"
                   r"mon academie est|notre academie est|je depends)\s+"
                   r"(?:(?:dans|de|a|en)\s+)?(?:l'academie\s+(?:de|d')\s*)?" + place + r"\b")
        if re.search(pattern, q) or re.search(r"^\s*(?:(?:a|dans|pour)\s+)?(?:l\'|mon |notre )?academie\s+(?:de|d\')\s*" + place + r"\b", q):
            declared.append(name)
    if len(declared) != 1:
        return selected or AIX, ''
    effective = declared[0]
    notice = (f"Vous avez sélectionné {selected or AIX}, mais indiqué {effective} dans votre question. "
              f"La réponse tient compte de l'académie de {effective}.") if selected not in (None, NON_PRECISEE) and effective != selected else ''
    return effective, notice


def request_academy(question, mode, selected):
    """Le choix d'académie ne s'applique qu'au parcours Examens."""
    return academy_context(question, selected if mode == 'examens' else NON_PRECISEE)
