# Coordination urgente — régressions HUB IA EPS — 20/11/2026

**Pour Claude et GPT — priorité de diagnostic.**

Thierry indique que la réponse iPackEPS transmise le 20/11 était **juste auparavant** ; il constate maintenant des erreurs fréquentes et demande une restauration de la fiabilité.

**Décision immédiate :** ne pas assimiler la présence de `gpt-4o-mini` et `gpt-oss-120b` à une panne ; ne pas désactiver Albert sans preuve. GPT a annulé sa tentative de désactivation dans la branche de la PR #66 (app.py remis identique à main). La PR #66 n'est pas une correction validée et ne doit pas être fusionnée en l'état.

**Claude :** analyser les changements récents du moteur, les réponses de référence et les échecs réels ; noter ici les commits suspects, questions reproduites, sources et propositions. Ne pas éditer app.py en parallèle de GPT sans annonce préalable dans ce journal.

**GPT :** assurer le suivi du diagnostic, construire des tests de non-régression sur les questions validées, vérifier les contrôles avant toute modification du moteur. Ne pas modifier les fiches ou le catalogue sans cause démontrée.

**Référence validée par Thierry :** question « comment déclarer mes groupes d'option ? », onglet iPack, Lycée GT. La réponse citait deux fiches sur les groupes d'option et les doubles niveaux. Autre exemple transmis : dépôt de référentiels sans emploi du temps. Les traces des deux réponses comportaient deux modèles et 17,059 s / 26,621 s de durée IA, mais ces mesures ne suffisent pas à établir une régression.

**Protocole :** 1. recueillir les questions qui se trompent maintenant ; 2. comparer réponses avant/après à fiches constantes ; 3. localiser le commit responsable ; 4. écrire un test reproductible ; 5. appliquer un correctif isolé ; 6. tests et validation par Thierry avant fusion.

Écrire les nouveaux constats dans ce document avec date et signature, sans écraser les constats de l'autre intervenant.
