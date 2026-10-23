# Revue du parcours documentaire — 24 octobre 2026

Base publiée : 5084a56. Revue structurelle de app.py et lecture des portions actives de contexte, sélection, génération, validation, réparation et restitution, ainsi que des modules appelés. Cette revue n'est pas une certification exhaustive de chaque branche de l'application. Aucun accès aux secrets ni appel IA réel. Les CSV privés restent hors dépôt.

## Constats établis

| Étape | Constat | Conséquence |
|---|---|---|
| Contexte du rejeu | Académie isolée par ligne depuis 6e03c5b ; les derniers lots gardent Non précisée. | L'ancien héritage de session n'explique pas les erreurs récentes. |
| Fournisseur / sélection | Couplage fournisseur albert corrigé en 49b367b. ORIENTATION_FICHES continue de commander la politique. | Le parcours mini conserve le sélecteur GPT ; Textes reste hors shortlist. |
| Sélection | Même question 41 : D1/D2/D3 retenus dans un lot, D1 seul dans l'autre ; la fiche précise du calcul est alors omise. Question 44 : no_match_full_review provoque le parcours complet de secours. | Corpus identique et réglage identique ne garantissent pas des preuves identiques. Ne pas attribuer toute variation au seul rédacteur ou au moule. |
| Validation | Citations littérales, nature et recouvrement lexical sont contrôlés ; semantic_review reste False. | Une citation existante peut rester une justification incorrecte. |
| Silence documentaire | unsupported_certainty exigeait que toutes les phrases de toutes les preuves constituent une absence documentaire. Une règle positive voisine pouvait donc désactiver le contrôle d'une limite relative à une autre formalité. | Le passage co-évaluation + signature non démontrée laissait passer « signature non obligatoire ». Défaut reproduit et correction bornée ci-dessous. |
| Réparation | Une seule réparation documentaire supplémentaire ; elle repasse resolve et les mêmes contrôles. | Elle corrige des rejets détectés, pas les erreurs de sens non détectées. Aucun juge sémantique supplémentaire. |
| Restitution | navigation_restore copie des chemins depuis les preuves puis repasse resolve. Les erreurs non résolues conduisent à la réserve et aux extraits, pas à la publication de la proposition rejetée. | L'existence d'accepted_claims dans une trace de réserve ne signifie pas que ces affirmations ont été montrées. |
| Cache | app.py importe response_cache, mais aucune utilisation de answer_key/ANSWER_CACHE trouvée dans son AST. Les caches actifs de recherche et les chargeurs par empreinte sont distincts. | Aucun élément dans les lots ne prouve la réutilisation d'une ancienne réponse par ce cache. Ne pas proposer une purge comme explication établie. |
| Chargement | Le runtime de génération utilise une empreinte incluant claim_guards et documentary_review ; le chargeur de rejeu inclut son propre code. Aucun appel importlib.reload trouvé dans app.py. | Le correctif des contrôles est chargé par un nouveau runtime ; conserver l'isolation entre sessions. |

## Correction publiée avec cette revue

Contrôle complémentaire générique sur une limite explicite « ne suffit/permet pas à/de démontrer/confirmer une obligation/autorisation/interdiction/possibilité ». Il rapproche l'objet de cette limite et l'affirmation catégorique ; une règle explicite séparée sur le même objet reste recevable, une règle sur une autre opération ne suffit pas. Le contrôle fonctionne aussi si la preuve mêle faits positifs et limite documentaire. Il ne produit aucune réponse métier et n'appelle aucun modèle.

Six tests : formulation défaillante tirée des traces, réserve acceptable, prescription explicitement sourcée, règle sur une autre action, autre domaine (données archivées), passage par le validateur réel. Contrôle lexical borné : ne prouve pas l'implication sémantique générale et ne couvre pas toutes les paraphrases.

## Points encore ouverts

- Généralisation d'une condition propre à la spécialité vers l'enseignement commun (question 26) : le moule n'a pas suffi.
- Confusion des droits de déplacement d'un candidat et de réaffectation d'un lot (question 19).
- Recommandation de dépôt tardif et interlocuteurs non étayés (question 30).
- Stabiliser l'exposition des sources pertinentes au sélecteur sans réponse en dur ni empilement des consignes.
- Dans evidence_relation_errors, une réserve documentaire déclenche actuellement une sortie anticipée pour l'affirmation entière : une phrase mêlant décision et réserve mérite un contrôle au niveau des propositions. À traiter avec contre-exemples avant modification générale.
- La liste de fichiers empreintés du runtime n'inclut pas tous les modules transversaux (notamment evidence_logic/source_scope). Pas de panne liée établie ici ; examiner avant une future modification de ces dépendances.
- Les transformations de présentation après génération, les autres modules et les branches rares de app.py n'ont pas tous fait l'objet d'un essai d'interface. Aucun fonctionnement universellement sans bug n'est annoncé.

Albert reste suspendu. Ne pas lancer un nouveau lot massif pour valider cette revue. Le changement de contrôle devra être distingué du changement des fiches lors de la prochaine comparaison.

## Ajustement après le test réel de la question 40

Le rejeu utilisateur 0d02b4d a produit une réponse finale prudente mais deux appels de rédaction (10 417 jetons) : le contrôle ajouté a rejeté à tort « cela ne signifie pas qu'une double signature est obligatoire ». La négation porte ici sur la déduction, pas sur l'obligation elle-même. Ne pas considérer cette réparation comme une amélioration prouvée.

Ajustement : reconnaître les formes négatives de déduction (« ne signifie/implique/prouve/démontre/veut dire pas que ») dans la proposition concernée. Séparer les propositions aux ponctuations et connecteurs d'opposition ou conséquence pour qu'une réserve ne protège pas une conclusion catégorique voisine. Ne pas accepter pour autant « n'est pas obligatoire ». Neuf tests ciblés couvrent les deux sens, plusieurs paraphrases et une conclusion erronée après une réserve. Revalidation locale de la proposition initiale exacte du CSV privé : trois affirmations acceptées, zéro rejet ; aucun nouvel appel IA. Ce résultat déterministe ne garantit pas que tout futur brouillon sera identique ni exempt d'autres erreurs.
