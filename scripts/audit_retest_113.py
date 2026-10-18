#!/usr/bin/env python3
"""Diagnostic de routage documentaire sans appel IA ni modification du HUB."""
import argparse
import csv
import sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.input.resolve() == args.output.resolve():
        p.error("Entrée et sortie doivent être distinctes")
    try:
        import knowledge_catalog as kc
    except ImportError:
        sys.exit("Lancer depuis la racine du dépôt avec les dépendances du HUB installées.")
    with args.input.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)
    required = {"question", "mode", "public", "verdict"}
    if not rows or not required.issubset(rows[0]):
        sys.exit("CSV absent, vide ou colonnes attendues manquantes.")
    if len(rows) != 113:
        sys.exit(f"113 questions attendues, {len(rows)} trouvées : abandon.")
    out = []
    for i, row in enumerate(rows, 1):
        q, public, mode = row["question"], row["public"], row["mode"]
        try:
            titles = kc.priority_titles(q, public, mode)
            status = "ok"
            if not isinstance(titles, str):
                titles = str(titles)
        except Exception as e:
            titles, status = "", type(e).__name__
        out.append({"n": row.get("n", str(i)), "mode": mode,
                    "public": public, "verdict_initial": row["verdict"],
                    "routage_status": status, "titres_prioritaires": titles})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), delimiter=";")
        w.writeheader()
        w.writerows(out)
    print(f"Diagnostic documentaire : {len(out)} questions, 0 appel IA. Sortie : {args.output}")
    print("ATTENTION : aucun retest de réponse IA n'a été réalisé.")

if __name__ == "__main__":
    main()
