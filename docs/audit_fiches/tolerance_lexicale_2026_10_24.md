# Tolérance lexicale et protection des réussites — 24 octobre 2026

Base : f79cb52. Intervention transversale sur la recherche et deux faux rejets reproduits, sans nouvelle fiche métier ni réponse prédéfinie. Aucun changement de fournisseur, température ou plafond d’appels ; Albert reste en pause.

## Diagnostic préalable

Les essais privés ont montré une distinction essentielle : une erreur peut venir du contenu, du choix des sources, du choix d’un passage, de sa reformulation ou du contrôle. Retrouver la bonne fiche ne suffit pas. Dix contextes présentent une réponse utile et un échec ; cinq rapprochements ont les mêmes fichiers transmis, sans garantir des passages identiques. Un ancien cas a un prompt de rédaction identique, avec une réponse utile de mini et une liste vide d’Albert : aucun plafond de longueur n’est démontré.

Les 188 essais tracés couvrent 100 formulations / 107 contextes ; leur classement manuel reste provisoire. Les groupes d’étude privés de 100 utiles et 100 problématiques sont construits pour comparer les profils, pas mesurer un taux de 50 %. Le groupe problématique comprend 68 échecs/réserves et 32 partiels ; 26 cas historiques n’ont pas de trace détaillée et ne permettent pas d’attribuer une cause au code. Ne pas les présenter comme 100 erreurs factuelles prouvées. Les répétitions et différences de modèles/versions interdisent de tirer un taux général de ces lots.

## Changements bornés

- `knowledge_catalog.normalise` réduit les espaces successifs et insécables à un espace pour les comparaisons. L’accentuation était déjà normalisée. La question originale, les documents et les citations ne sont pas réécrits.
- Un vocabulaire explicite de mots métier longs de recherche permet de reconnaître une permutation de deux lettres adjacentes (`protocloe`, `rempalcer`). Une variante qui correspondrait à plusieurs termes est ignorée. Les nombres, sigles, diplômes, négations et qualificatifs médicaux ne sont pas corrigés. Pas de distance floue illimitée, pas de dictionnaire général appliqué à toutes les paroles du professeur. Cette tolérance ne comprend pas toutes les fautes et n’est pas une nouvelle compréhension sémantique ; elle évite des pertes avant la recherche par le sens déjà disponible.
- Le contrôle de situation reconnaît `course` et `courses`. Dans le cas observé, les cinq étapes étaient rejetées parce que leurs preuves contenaient Courses alors que la question comportait course au singulier. Le faux rejet a été reproduit en conservant chaque affirmation et sa preuve ; changer le seul singulier faisait disparaître les cinq rejets. Un sujet sans rapport reste rejeté.
- Le contrôle de non-équivalence sépare aussi le deux-points lorsqu’il cherche un préalable explicitement obligatoire dans la preuve. Une phrase disant que les classes et élèves doivent déjà être présents, suivie après le deux-points d’une limite sur l’absence de synchronisation automatique, ne perd plus ce préalable. Les vraies obligations tirées d’une simple non-équivalence restent rejetées.

Il n’y a pas de levée globale du contrôle des conditions. Les distinctions avant/après, temporaire/permanente, CAP/bac GT et association/distribution restent distinctes. La recherche et la preuve ne sont pas synonymes : reconnaître une formulation approchante ne valide pas la conduite à tenir.

## Validation

- Cinq nouveaux tests ciblés : cas de saisie réalistes, espaces insécables, transpositions, conservation des faits/codes, singulier et contre-exemple hors sujet, préalable explicite versus obligation non prouvée, distinctions métier.
- Suite complète : **1083 tests réussis en 49,429 s** ; compilation et diff vérifiés.
- Sur les 100 formulations distinctes de l’ensemble tracé, mêmes fiches prioritaires pour les questions originales avant/après : **aucun changement de routage observé**.
- Sur les 100 réponses utiles choisies comme protection, **aucun nouveau rejet** des contrôles de situation/logique modifiés ; 98 ont des affirmations contrôlables, deux sont des réponses directes sans cette structure. Cela ne prouve ni leur exactitude exhaustive ni une nouvelle rédaction modèle.
- Audit hors IA de 369 variantes sur ces 100 formulations : avant, changement de priorités pour 34 variantes à espaces doubles et 31 à espaces insécables ; un changement de contrôle pour course/courses. Après, aucun de ces changements sur ce même jeu. Ce sont des fonctions de routage/contrôle, pas 369 réponses générées ni la preuve que chaque ancienne priorité était idéale.
- Les erreurs synthétiques protocloe et rempalcer retrouvent les priorités de la formulation correcte. D’autres fautes, par exemple une substitution dans un mot court, ne sont pas couvertes ; les tests l’exigent explicitement pour éviter une correction arbitraire.

Les fichiers privés de diagnostic, réponses, traces et mesures détaillées ne sont pas publiés. Aucun appel aux modèles du hub ni rejeu payant. Aucun audio exploité.

## Limites et suite

Il ne faut pas extrapoler ces résultats en 80 ou 90 % d’aide utile. Les autres défauts des 20 derniers cas restent à traiter séparément : ambiguïtés des modules SSS, preuve du dépôt d’annexes, phrase inversée au collège, limites qui font perdre une orientation correcte, et différences de conditions dans les protocoles adaptés. Les modifications ne prétendent pas régler ces cas.

La prochaine comparaison doit porter sur une version identifiée, les mêmes contextes et mini seul. Les anciens résultats f79cb52 restent conservés ; ne pas les fusionner silencieusement avec ceux de cette nouvelle version. Ne pas relancer automatiquement les 500 questions.
