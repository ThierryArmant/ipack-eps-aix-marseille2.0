# Lecture documentaire des réponses Examens — 13 octobre 2026

Les tests en ligne des lots 5 et 6 ont montré des conclusions contradictoires, des conditions omises et des procédures de guides attribuées au Bulletin officiel.

## Changements

- Dans `_recherche_documentaire`, une fiche exclusive arrête la recherche complémentaire mais conserve les fiches de situation déjà sélectionnées dans le niveau de priorité 300 ou supérieur, lorsqu’elles précèdent une synthèse moins prioritaire. Les compléments généraux de priorité inférieure restent exclus ; le comportement iPackEPS reste inchangé. Auparavant le retour ne conservait que la dernière fiche : pour EX091, la fiche présentant les deux saisies possibles était perdue. Le diagnostic `knowledge_catalog.priority_context` conservait cette fiche : le diagnostic et le contexte réellement transmis divergeaient.
- Les réponses générées dans l'onglet Examens passent par une relecture IA avec la question, les mêmes documents et le brouillon. Cette relecture reconstruit les conditions, les alternatives, l'opération et les rôles, puis vérifie les attributions de sources et la cohérence de la conclusion.
- Aucune règle d'examen, réponse attendue ou identifiant de banque n'est inscrit dans la relecture. Elle renvoie du texte généré depuis les documents courants. Catalogue, fiches et réponses en dur inchangés.

## Limites

La relecture ajoute un appel au modèle pour chaque réponse Examens générée, donc de la latence et un coût supplémentaire. Elle peut encore se tromper ; les tests unitaires ne démontrent pas la justesse réglementaire de ses sorties. Une relecture vide échoue explicitement, au lieu de publier silencieusement le brouillon.

Les tests vérifient la conservation effective des deux branches dans le vrai routage d'app.py, la transmission des documents à la relecture et le traitement d'une sortie vide. La série de réserve demeure intacte. Des retests en ligne sont nécessaires avant de conclure à une amélioration.

La relecture produit les passages justificatifs avant la réponse finale, en JSON. Le programme vérifie que les passages cités existent littéralement dans les documents. Cette vérification de présence ne prouve pas la bonne interprétation ni le rattachement à la source : les retests restent indispensables. Les preuves ne sont pas affichées à l’utilisateur.

Les variations typographiques des preuves (apostrophes, gras, espaces) sont tolérées, sans reformulation de leurs mots. Une sortie sans preuve présente est reprise une fois contre les mêmes documents ; si le second contrôle échoue, le brouillon non vérifié ne sera pas publié. Ce cas ajoute exceptionnellement un troisième appel au modèle.
