# INCIDENT HUB IA EPS — 20 novembre 2026 — coordination Claude / GPT

## Priorité
Rétablir la fiabilité et la réactivité du HUB en production. Gel des nouvelles fonctions et des enrichissements documentaires jusqu'à validation. Ne pas modifier les fiches, leurs empreintes ou les règles métier dans ce correctif.

## Constat utilisateur (journal du 20/11)
- 08:32, iPack / Lycée GT, dépôt de référentiels sans emploi du temps : réponse issue de 3 fiches, trace modèles `gpt-4o-mini, gpt-oss-120b`, durée IA 26,621 s.
- 09:40, iPack / Lycée GT, groupes d'option : réponse issue de 2 fiches, mêmes modèles, durée IA 17,059 s.
- Ces deux exemples ne prouvent pas à eux seuls une réponse réglementaire fausse. Ils attestent en revanche le double moteur et la latence. Vérifier les réponses avec les sources avant de les qualifier d'erreurs.

## Diagnostic code
Dans app.py, le commentaire et le modèle de base indiquent « Mini seul », mais la branche `_albert_redige_voulu` forçait True pour les collègues. Avec `ALBERT_API_KEY`, AlbertWithFallback était donc activé. Le choix administrateur était également coché par défaut.

## Correctif isolé proposé par GPT (PR à valider)
- Utilisateurs ordinaires : Mini seul par défaut pour la rédaction, sans activation automatique d'Albert.
- Administrateur : case Albert décochée par défaut ; essai explicite encore possible.
- Aucun changement au catalogue, aux fiches, aux réponses fixes, aux sources, aux index, aux secrets ni à la veille.
- Ne pas fusionner sans tests de non-régression et comparaison des journaux.

## Répartition proposée — éviter les modifications concurrentes
**Claude** : analyser les régressions récentes du moteur et les deux réponses iPack ci-dessus ; identifier les commits et les causes, mesurer les appels et durées ; ne pas toucher à app.py tant que cette PR est ouverte ; déposer ses constats ici ou dans une section datée du journal de coordination.

**GPT** : responsable de cette PR de stabilisation du choix du rédacteur, des tests et du contrôle GitHub ; pas de modification des fiches iPack.

**Thierry** : valider uniquement après tests et essai de production.

## Critères de sortie
1. Tous les tests GitHub passent.
2. Les deux questions iPack ci-dessus donnent une réponse fidèle aux fiches, avec un seul rédacteur effectif et sans Albert par défaut.
3. Mesurer les temps, les modèles et les erreurs sur au moins dix questions de référence, dont Examens et Textes.
4. Vérifier la version déployée Streamlit, la journalisation et l'absence de changement involontaire dans les autres onglets.
5. En cas d'échec, revenir au commit stable identifié par les tests, sans écraser le travail parallèle.

**Important :** ce fichier transmet les consignes de coordination à Claude via GitHub ; il ne garantit pas que Claude l'a lu ni accepté.
