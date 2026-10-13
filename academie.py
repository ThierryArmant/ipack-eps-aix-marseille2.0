"""Académie de l'utilisateur : le hub contient des consignes propres à Aix-Marseille.

Pour un utilisateur d'une autre académie, ces consignes doivent être présentées comme
des consignes d'Aix-Marseille, à vérifier auprès de sa propre division des examens,
jamais comme des règles générales (voir docs/portee_academique_2026-10-13.md).
"""
import json
from pathlib import Path

AIX = "Aix-Marseille"

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
    nom = academie if academie not in ("Autre", "Établissement français à l'étranger") else None
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
    lieu = ("dans votre académie de rattachement" if academie in ("Autre", "Établissement français à l'étranger")
            else f"dans l'académie de {academie}")
    return ("Attention : cette réponse repose sur une consigne de l'académie d'Aix-Marseille. "
            f"{lieu[0].upper() + lieu[1:]}, vérifiez-la auprès de votre division des examens et de votre inspection EPS.")


def adresse_assistance(academie):
    return ASSISTANCE_IPACK.get(academie or AIX, "")
