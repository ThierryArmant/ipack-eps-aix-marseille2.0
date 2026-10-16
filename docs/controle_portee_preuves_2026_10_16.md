# Contrôle commun de portée des preuves — 16 octobre 2026

## Cause reproduite

La réponse « il n'est pas nécessaire » est acceptée par `validate_claims` lorsqu'elle cite la ligne réelle de la fiche APPN « Les références ci-dessous ne prescrivent pas universellement… ». Les contrôles de cohérence et d'extraction conditionnelle antérieurs ne détectent rien. Cette reproduction locale démontre la faille du contrôle ; elle ne prétend pas remplacer la trace de sélection du modèle en production.

Les citations littérales prouvent que la preuve existe et le contrôle lexical qu'elle partage le vocabulaire. Aucun des deux ne prouve que sa portée et sa modalité autorisent la conclusion. Le contrôle conditionnel précédent traitait surtout des situations de notation et de SHN. Ajouter des consignes de rédaction seules n'avait pas suffi lors des reprises en ligne.

## Correction partagée

`evidence_logic.py` ne contient aucun sujet EPS, matériel ou réponse attendue. Il contrôle trois erreurs explicites :

- absence d'obligation universelle transformée en absence de nécessité pour le cas particulier ;
- suffisance d'un dispositif déduite du seul fait qu'aucun minimum chiffré n'est fixé ;
- absence de nécessité affirmée alors qu'une autre affirmation sur le même objet dit que cette nécessité reste à apprécier.

Les limites explicites des passages sont transmises avant génération sous forme de contraintes liées aux identifiants de preuves. Après génération, le programme vérifie les conclusions et leurs preuves dans le circuit commun Textes / Examens / iPackEPS. Il ne remplace pas la conclusion par une réponse enregistrée. Un échec emprunte l'unique réparation déjà existante ; un second échec empêche l'affichage comme réponse confirmée et déclenche le repli documentaire existant.

Les traces conservent les contraintes, les rejets initiaux/finals et le nom du contrôle. Un passage supplémentaire établissant explicitement une dispense reste utilisable. Les affirmations déjà correctement conditionnées et les dispenses directement documentées doivent rester acceptées. Aucune augmentation systématique du nombre d'appels IA.

## Validation et limites

Tests sur plusieurs objets fictifs, le défaut réel, le maintien d'une dispense explicite, la distinction d'objets différents, les trois modes, la réparation, l'absence d'affichage d'un échec répété et le maintien d'un seul appel sur réponse correcte.

Il s'agit de contrôles linguistiques conservateurs et ciblés, pas d'un moteur complet de raisonnement juridique. Ils ne prouvent pas toutes les implications sémantiques et ne garantissent pas la complétude d'une réponse : l'omission d'un contrôle d'assurage ou d'un délai doit rester surveillée. Les contrôles en ligne sont nécessaires après publication ; leurs résultats ne peuvent être déduits des tests locaux.
