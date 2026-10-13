# Journal de coordination — Hub IA - EPS

Tableau de liaison entre la **partie fiches** (fiches, catalogue, registres, tests associés) et la **partie programme** (`app.py`, `documentary_review.py`, `source_scope.py`, consignes du modèle, tests en ligne).

## Règles
- Avant tout travail : `git pull`, puis lire ce journal (au moins les entrées récentes).
- Après chaque commit poussé : ajouter une entrée **en haut** de la section « Entrées », au format ci-dessous.
- Ne pas modifier les fichiers de l'autre partie sans l'avoir annoncé ici et obtenu son accord.
- Dépôt public : aucun mot de passe, aucun secret, aucune question de la série de mesure ni corrigé, aucun nom de collègue ni d'établissement, aucun nom d'outil d'intelligence artificielle.
- Contexte général et règles du projet : `docs/reprise_projet.md`.

## Format d'une entrée
```
### AAAA-MM-JJ HH:MM — partie fiches | partie programme — commit abc1234
Fait : …
Constaté : …
Attendu de l'autre partie : … (ou « rien »)
```

## État courant
- Version candidate pour la mesure : 4488e07 (à confirmer en ligne, puis à figer).
- Série de réserve (14 questions), après reprises : 11 correctes, 3 partielles (R04, R06, R14), 0 fausse ; environ 1 appel par question. Ces questions ont servi à corriger : le chiffre surestime le niveau réel.
- Prochaine étape : vérifier R04 en ligne, figer la version, puis passer la série de mesure de 50 questions (posée par l'enseignant, notée par la partie fiches ; série conservée hors dépôt, empreinte dans `docs/empreinte_serie_mesure_2026-10-13.md`).

## Entrées

### 2026-10-13 18:35 — partie fiches — commit 4488e07
Fait : fiche inaptitude bac GT déclenchée aussi par « arrêt, certificat, blessure » avec deux notes (cas R04), cas du professeur en arrêt exclu ; ligne Sigles ajoutée. Priorité inchangée : en priorité 300, elle évinçait d'autres fiches validées (d3 DI+DI+14, d6, gt_regles_decisives). Test ajouté. 247 tests passent.
Constaté : reprise des 7 questions sur 85c8a9b : R02, R05, R07, R08, R09, R12 correctes en 1 appel ; R04 partielle (« validation par l'autorité académique » inventée, fiche du ponctuel citée).
Attendu de l'autre partie : rien. Après redéploiement, faire reposer R04.

### 2026-10-13 18:22 — partie programme — commit 85c8a9b
Fait : contrôle lexical des passages sans ratio (au moins 2 racines communes) ; repli documentaire explicite au lieu du message d'erreur (68a41bc, 3809bd9, 7eab344).

### 2026-10-13 15:28 — partie fiches — commits 48dc513, 61bc1f2
Fait : trois fiches de situation en priorité 300 dans `data/examens/situations_2026_10_13/` (absence en CAP, bac pro inapte avec deux notes, établissement hors SIECLE) ; exclusion « deux notes » sur la fiche bac pro « une seule évaluation » ; registre des natures à 447 fiches (retouche du compte dans `tests/test_source_scope.py`).
