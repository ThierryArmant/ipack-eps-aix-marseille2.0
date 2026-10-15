# Reprise du projet — Hub IA - EPS (état au 13 octobre 2026, fin de journée)

À lire en premier par toute personne ou tout assistant qui reprend le travail. Le suivi au jour le jour est dans `docs/journal_coordination.md`.

## Adresses
- Dépôt : https://github.com/ThierryArmant/ipack-eps-aix-marseille2.0 (branche `main`, poussée directe, sans branche ni demande de fusion ; historique conservé)
- Hub en ligne : https://assistant-ia-eps-aix-m.streamlit.app/ (la version déployée s'affiche sous le titre)

## Répartition du travail
- **Partie fiches** : contenu des fiches (`data/`), catalogue (`config/catalogue_documents.json`), métadonnées de portée (`config/nature_sources.json`, `config/portee_academique.json`), tests associés.
- **Partie programme** : code de réponse (`app.py`, `documentary_review.py`), consignes du modèle, tests en ligne.
- Chacun ne modifie pas la partie de l'autre sans le prévenir. Toujours faire `git pull` avant de commencer.

## Règles de travail
- Revenir aux fiches : les réponses en dur restent l'exception (10 garde-fous ; au plus 12, voir `tests/test_routage_reponses_directes.py` et `docs/consigne_reponses_en_dur_2026-10-12.md`). Ne jamais en créer une pour faire passer une question de test.
- Ne garder que le factuel et vérifiable ; écrire les mises en garde à l'affirmative.
- Ne pas généraliser la pratique d'une académie à une autre. Aucune date académique inventée.
- Dépôt public : aucun nom de collègue ni d'établissement dans les fiches.
- Dans les documents destinés aux collègues, ne citer aucun outil d'intelligence artificielle.
- Le coût compte : viser un appel au modèle par question (un second seulement si la vérification échoue).

## État
- Modes Examens et iPackEPS : réponse appuyée sur les fiches spécifiques (priorité 300). Un appel de rédaction ; un second seulement si la vérification mécanique des passages échoue (`documentary_review.py`). Étiquettes de source fixées par le programme à partir de `config/nature_sources.json` (`source_scope.py`). Le cache de réponses est désactivé dans app.py depuis le 14 octobre : chaque soumission est traitée indépendamment.
- Choix de l'académie obligatoire avant la question (`academie.py`) ; hors Aix-Marseille, les passages listés dans `config/portee_academique.json` sont envoyés au modèle précédés de « [Consigne de l'académie d'Aix-Marseille — non confirmée pour …] ». Ce registre se régénère avec `python portee_registre.py --write` après toute modification de fiche.
- Interface : parcours en trois étapes dans un panneau unique (contexte, académie et public, question).
- Coût : avant le passage à un appel, EX290 consommait 3 appels et environ 17 000 jetons d'entrée. À remesurer en ligne (compteur sous chaque réponse).

## Prochaines étapes
1. Vérifier EX290 en ligne avec Aix-Marseille puis Créteil : décision correcte, étiquettes de source, compteur à 1 appel.
2. Figer une version (numéro de commit), sans modification pendant la mesure.
3. Mesure : série de réserve (14 questions), puis série de 50 questions conservée hors dépôt ; empreinte dans `docs/empreinte_serie_mesure_2026-10-13.md`. Notation correcte / partielle / fausse, coût relevé.
4. Questions à faire trancher par la DIEC : `docs/questions_a_trancher_diec.md`.
5. Circulaire EPS 2027 d'Aix à paraître : fiches à reprendre dans `docs/mise_a_jour_circulaire_eps_2027.md`.

## Documents utiles
- `docs/lecture_sources_2026-10-13.md` : fonctionnement de la relecture des réponses Examens.
- `docs/portee_academique_2026-10-13.md` : cahier des charges du choix d'académie.
- `docs/audit-lot*-examens-*.md` : résultats des campagnes de test.
