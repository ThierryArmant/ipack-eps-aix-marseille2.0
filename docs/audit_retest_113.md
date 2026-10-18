# Audit de régression — 113 questions (18 octobre 2026)

Cette branche est **isolée de main**. Elle ne modifie ni `app.py`, ni les fiches, ni les paramètres de Streamlit.

## Source de la mesure
113 questions (76 réponses partielles et 37 fausses), identifiées dans le fichier privé `reponses_partielles_ou_fausses_pour_claude.csv`. **Ne pas commiter ce CSV** : les questions et réponses de l'historique restent hors du dépôt public.

## Étape 1 — contrôle sans appel IA
Depuis la racine du dépôt, avec le CSV privé accessible localement :

```bash
python3 scripts/audit_retest_113.py --input /chemin/vers/reponses_partielles_ou_fausses_pour_claude.csv --output /chemin/prive/diagnostic_113.csv
```

Ce contrôle inspecte le routage documentaire du code actuel via `knowledge_catalog.priority_titles`. Il n'est **pas** un retest des réponses IA, et ne doit pas être compté comme tel.

## Étape 2 — retest réel
Le HUB effectue son traitement dans `app.py` (interface Streamlit, chargement des bases, récupération de passages et génération). Un appel direct à `knowledge_catalog` ne reproduit pas la réponse réelle. Avant toute campagne payante, isoler la fonction complète question → réponse dans un module testable, sans changer la logique ni multiplier les appels IA. L'exécuter avec les secrets existants dans un environnement autorisé et hors production, par lots de 3 puis 20, avec plafonnement des coûts et sauvegarde privée des résultats.

Ne pas mettre les secrets, questions, réponses ou résultats individuels dans les logs GitHub publics. Ne pas supposer que les secrets Streamlit sont disponibles dans GitHub Actions.

## Évaluation
Comparer les nouvelles réponses à la notation initiale (correct / partiel / faux / erreur technique), en vérifiant séparément les sources et la portée académique. Les 113 questions ayant toutes été initialement insuffisantes, le taux correct initial de ce sous-échantillon est 0 %, ce qui ne décrit pas le taux global du HUB.
