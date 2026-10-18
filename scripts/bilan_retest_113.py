#!/usr/bin/env python3
"""Valide un fichier de résultats privés, sans API et sans afficher les questions."""
import argparse, csv, collections, pathlib, sys

def load(path):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True)
    parser.add_argument("--results", required=True, help="CSV privé : n;nouveau_verdict;nouvelle_reponse")
    args = parser.parse_args()
    original, results = load(args.original), load(args.results)
    if len(original) != 113:
        sys.exit("Échec : exactement 113 questions originales sont requises.")
    ids = [str(r["n"]).strip() for r in original]
    if len(set(ids)) != 113:
        sys.exit("Échec : identifiants originaux non uniques.")
    allowed = {"correct", "partiel", "faux", "erreur_technique"}
    by_id = {}
    for row in results:
        ident = str(row.get("n", "")).strip()
        if ident not in ids or ident in by_id:
            sys.exit("Échec : identifiant inconnu ou doublon dans les résultats.")
        verdict = str(row.get("nouveau_verdict", "")).strip().lower()
        if verdict not in allowed:
            sys.exit("Échec : verdict invalide pour une ligne.")
        if not str(row.get("nouvelle_reponse", "")).strip() and verdict != "erreur_technique":
            sys.exit("Échec : réponse absente pour une ligne.")
        by_id[ident] = row
    counts = collections.Counter(str(r.get("nouveau_verdict", "")).strip().lower() for r in results)
    print(f"Rejouées et évaluées : {len(results)}/113")
    print("Répartition :", ", ".join(f"{k}={counts[k]}" for k in sorted(allowed)))
    print(f"Restantes : {113-len(results)}")
    print("Attention : ce script valide et résume les résultats fournis ; il ne lance pas le HUB.")
if __name__ == "__main__":
    main()
