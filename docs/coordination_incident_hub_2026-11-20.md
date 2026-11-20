# Coordination urgente — régressions HUB IA EPS — 20/11/2026

**Pour Claude et GPT — priorité de diagnostic.**

Thierry indique que la réponse iPackEPS transmise le 20/11 était **juste auparavant** ; il constate maintenant des erreurs fréquentes et demande une restauration de la fiabilité.

**Décision immédiate :** ne pas assimiler la présence de `gpt-4o-mini` et `gpt-oss-120b` à une panne ; ne pas désactiver Albert sans preuve. GPT a annulé sa tentative de désactivation dans la branche de la PR #66 (app.py remis identique à main). La PR #66 n'est pas une correction validée et ne doit pas être fusionnée en l'état.

**Claude :** analyser les changements récents du moteur, les réponses de référence et les échecs réels ; noter ici les commits suspects, questions reproduites, sources et propositions. Ne pas éditer app.py en parallèle de GPT sans annonce préalable dans ce journal.

**GPT :** assurer le suivi du diagnostic, construire des tests de non-régression sur les questions validées, vérifier les contrôles avant toute modification du moteur. Ne pas modifier les fiches ou le catalogue sans cause démontrée.

**Référence validée par Thierry :** question « comment déclarer mes groupes d'option ? », onglet iPack, Lycée GT. La réponse citait deux fiches sur les groupes d'option et les doubles niveaux. Autre exemple transmis : dépôt de référentiels sans emploi du temps. Les traces des deux réponses comportaient deux modèles et 17,059 s / 26,621 s de durée IA, mais ces mesures ne suffisent pas à établir une régression.

**Protocole :** 1. recueillir les questions qui se trompent maintenant ; 2. comparer réponses avant/après à fiches constantes ; 3. localiser le commit responsable ; 4. écrire un test reproductible ; 5. appliquer un correctif isolé ; 6. tests et validation par Thierry avant fusion.

Écrire les nouveaux constats dans ce document avec date et signature, sans écraser les constats de l'autre intervenant.

## 20/11/2026 19 h — Claude : constats et proposition

**Rejeu en ligne (version fc44b6c), questions humaines de la banque « Banque propre »**
- « comment remplir mes listes de non nageurs » (iPack, collège) : **insuffisante**. La réponse propose de créer un groupe « non-nageurs » et d'imprimer les attestations. Elle ne cite pas l'enquête natation du [Dossier Natation], où les non-nageurs sont pourtant comptés (transcriptions vidéo, section « enquête natation »).
- « Je veux supprimer un groupe mais iPackEPS refuse. Dans quel ordre… » (iPack, collège) : **générique**. Les menus cités ([EDT], [Élèves], [Groupes]) ne sont pas des chemins réels. La fiche « Suppression bloquée » est elle-même vague (« le corpus décrit… »). C'est une lacune de la fiche.
- « Certains protocoles créés dans IPACK n'apparaissent pas dans CYCLADES » (Examens, LGT) : **correcte** (étiquette verte, APSA certificative, refus de la commission, protocole complet).

**Moteur : un seul changement depuis le 15/11, eaa677d (deux places au plus par fiche)**
- Il a été mis en service le 18/11 sans mesure. La condition notée dans le journal le 18/11 était de l'annuler si le rejeu réel est moins bon.
- Défaut constaté dans `_ajouter` : `_retenus += 1` s'exécute avant la mise en attente. Un fragment mis en attente consomme donc le quota de sa base. Il ne revient qu'à la fin, et seulement s'il reste une place.
- Effet attendu : quand la bonne fiche a plusieurs passages utiles (cas des fiches longues issues des vidéos, comme Natation ou Groupes), seuls deux passages arrivent jusqu'au choix des sources. La recette précise peut donc manquer.
- Le catalogue ne change rien pour les questions du 20/11 : les mêmes fiches prioritaires sont sélectionnées en f8b6c38 et en 55065b7.

**Non prouvé à ce stade**
- Les traces d'avant le 18/11 montrent 10 identifiants de sources par question. Je n'ai pas encore comparé, question par question, avec les traces d'après le 18/11.
- Certaines faiblesses relèvent des fiches, pas du moteur : la fiche « Suppression bloquée » et les listes de non-nageurs.

**Proposition (en attente de la validation de Thierry)**
1. `git revert eaa677d` : un seul commit, `document_retrieval.py` revient à l'état du 15/11, aucune fiche ni consigne n'est touchée. Il est prêt en local, non poussé.
2. Rejouer les mêmes questions sur le hub après redémarrage, et comparer.
3. Si l'amélioration n'apparaît pas, rétablir eaa677d (un nouveau revert) et chercher ailleurs.

— Claude

## 20/11/2026 19 h 55 — Claude : revert de eaa677d poussé
- Validé par Thierry à 19 h 49.
- Seul `document_retrieval.py` change : il revient à l'état du 15/11, et tests/test_places_par_fiche.py est retiré.
- 1 417 tests OK.
- Étape suivante : redémarrage de l'app, puis rejeu des mêmes questions (non-nageurs, suppression d'un groupe, protocoles absents de Cyclades, groupes d'option, référentiels sans emploi du temps).
- GPT : ne pas réintroduire de plafond par fiche sans mesure sur rejeu réel.

— Claude
