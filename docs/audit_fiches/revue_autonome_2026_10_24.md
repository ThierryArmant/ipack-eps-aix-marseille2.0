# Revue autonome iPackEPS / Cyclades / Santorin / Examens

Base publiée : 82f7efc. Travail sans appel IA ni rejeu payant ; Albert demeure suspendu. Les changements locaux antérieurs sont conservés. La revue ne certifie pas toutes les sources et ne prétend pas avoir transcrit l'audio des visites.

## Défaut transversal confirmé et corrigé

`source_scope.scoped_segments` supprimait les lignes commençant par « Portée : », en même temps que les métadonnées bibliographiques. Or ces lignes portent parfois une restriction métier. Exemple réel : la fiche iPack 164 réserve le choix des AFLP au bac professionnel et au CAP, excluant explicitement le bac GT. La restriction n'était pas conservée comme preuve du rédacteur, même lorsque le fichier source était bien chargé.

Conserver désormais ces lignes comme passages, avec offsets exacts et attribution habituelle. 66 des 435 fichiers iPackEPS et Examens inventoriés contiennent au moins une telle ligne. Le contrôle couvre la copie jusque dans le paquet compact destiné au modèle. Cela garantit sa disponibilité dans le document transmis, pas que le modèle la respectera ni que tous les documents seront sélectionnés.

Autre défaut préventivement traité : `source_scope` et `evidence_logic` n'appartenaient pas à l'ensemble immuable de génération. Ils y sont intégrés avec leurs imports relatifs. Modifier l'une de ces dépendances crée un nouveau paquet ; les sessions déjà en cours conservent leur paquet précédent. Test de changement de source et d'identité des imports, sans rechargement global d'un module partagé.

## Copies reprises

- iPack 023 : l'activation « Certificative » ne suffit pas à prouver le droit ou l'obligation de déposer. Séparer visibilité, référentiel académique, épreuve d'établissement et EPPCS ; reprendre les conditions des réponses écrites déjà présentes.
- FCA liste académique : expliciter l'alternative établissement ; une absence de la liste n'interdit pas, à elle seule, le dépôt. Aucun nouveau droit inventé.
- iPack 003 : retirer l'instruction de routage adressée à l'IA ; borner les nombres d'épreuves au cadre ordinaire, distinguer AFL / AFLP et référentiel académique / établissement. Remplacer le mois universel de janvier par les deux préalables du circuit Aix déjà documentés. Ne pas déduire un droit exclusif d'export du chef à partir d'un relevé de l'espace professeur.
- Mémoire Santorin 004 : supprimer le « principe absolu » et distinguer composition ordinaire, contrôles adaptés et message logiciel. La règle des trois champs au bac pro a été vérifiée dans MENE2505383C, B.1, et conservée ; elle n'était pas à remplacer par deux champs. Les adaptations relèvent notamment de B.3.
- iPack 151 : borner le bac GT au CCF ordinaire ; distinguer la recommandation disciplinaire des trois APSA au DNB d'une condition nationale automatique d'attribution du diplôme, en reprenant les fiches DNB communes existantes et leurs références de session.

- Dossier certificatif lycée : borner le bouton « Certificative » à l'enseignement commun ; l'EPPCS ne doit pas être coché certificatif selon la réponse écrite confirmée par les développeurs déjà dans correspondant_03. Le groupe EPPCS permet le dépôt de sa FCA. La fiche de visite mélangeait ces conditions.

Ces six fiches restent `a_confirmer` pour la revue documentaire complète. L'empreinte périmée du diagnostic Santorin est aussi corrigée dans le registre après comparaison avec son contenu publié identique. Aucune autre version de ce fichier n'est écrasée.

## Questions inédites et contre-exemples

Trois lacunes du raccordement prioritaire ont été reproduites et corrigées dans le catalogue existant : deux collèges/deux lycées et changement de site ; attestation ASNS pour un seul élève ; association manuelle des candidats à leur protocole Cyclades. Contrôles négatifs : mutation, création de groupes, impression ASNS collective, association d'APSA aux groupes, CFA hors SIECLE. Aucun nouveau document métier et aucune réponse métier en dur.

Ces essais portent sur le vrai raccordement local, sans recherche vectorielle ni modèle. L'absence d'une priorité ne démontrait donc pas l'absence de toute fiche dans une réponse en ligne.

## Contrôle reproductible et limites

`python -m scripts.audit_corpus_offline --output /tmp/corpus.json` vérifie les 435 fichiers inventoriés : fichier vide, caractères corrompus, marqueurs de troncature éditoriale, empreinte de suivi et présence des lignes de contenu dans les preuves. Titres et métadonnées bibliographiques restent exclus de la comparaison ; les restrictions « Portée : » sont contrôlées. Les originaux dont `retrieval_enabled` est faux restent identifiés séparément. Aucun signal automatique n'est promu en validation factuelle.

Résultat local après correction : zéro anomalie sur ces contrôles mécaniques. Cela ne signifie pas zéro erreur sémantique. La question 26, notamment, a montré une inversion de condition par le modèle : les corrections des copies et la conservation de portée doivent encore être évaluées sur une réponse réelle. La relecture source par source de toutes les prescriptions n'est pas clôturée.

## Objectif de 90 %

Mesurer sur un lot fixe et représentatif de questions, avec même modèle, contexte et version de corpus. Une réponse compte comme réussie si elle répond à l'action demandée, conserve les préalables et étapes nécessaires, respecte diplôme/régime/académie et ne contient aucune consigne injustifiée. Une réserve correcte peut réussir une question réellement non documentée ; une réserve évitable n'est pas un succès. Pour 50 questions, 45 doivent remplir tous ces critères, et les erreurs critiques doivent être signalées séparément.

Le taux des tests de code, le nombre de passages acceptés et l'absence de rejet ne mesurent pas ce taux. Aucun chiffre de 90 % atteint n'est annoncé. Ne pas lancer de lot payant pour compléter ce bilan sans instruction explicite : les contrôles de ce travail sont locaux.
