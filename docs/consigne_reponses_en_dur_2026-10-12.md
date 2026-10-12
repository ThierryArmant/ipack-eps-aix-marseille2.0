# Réponses en dur : règle de travail (12 octobre 2026)

## Principe
Le hub répond à partir des fiches, que l'IA lit, croise et adapte à la question.
Une réponse en dur s'affiche telle quelle, sans adaptation au diplôme ni à la formulation : elle reste l'exception.

## Quand une réponse du hub est fausse ou incomplète
1. Corriger ou compléter la fiche (formulations des collègues, étapes, portée, source datée).
2. Si la bonne fiche n'est pas transmise, ajuster ses motifs dans le catalogue (injection prioritaire), sans réponse en dur.
3. Écrire les mises en garde à l'affirmative (« Oui, il faut l'associer… ») : une tournure « ne jamais répondre que… » est reprise à contresens.
4. Ne jamais créer une réponse en dur pour faire passer une question de la banque de test.

## Garde-fous conservés en réponse en dur (11)
Seulement quand l'erreur aurait de lourdes conséquences et que le modèle l'a déjà commise, ou pour empêcher d'inventer une date ou une fonction :
- dates : échéances 2027 non publiées (`audit_faq_2026_10_12/j5`), dates des protocoles (`aix_protocoles_2026`), délai d'activité établissement (`activite_etablissement_delai_aix`) ;
- fonctions inventées : version ou installation d'iPackEPS (`acces_ipackeps_problemes`, 2 réponses), mode hors connexion (`ipack_hors_ligne`), vidéo dans iPackEPS (`ipack_301`), mot de passe administrateur (`administrateur_acces`) ;
- règles stables déjà mal traitées : inscription « APTE » à Aix (`aix_inscriptions_2027_gt`), zéro au DNB pour absence non justifiée (`regles_dnb_eps`), taux d'encadrement des sorties (`sorties_encadrement_2024`).

Le test `tests/test_routage_reponses_directes.py` échoue au-delà de 12 réponses en dur.

## Conversion du 12 octobre
61 réponses en dur sont redevenues des fiches : leur texte est dans le fichier de la fiche, transmis en priorité à l'IA.
Les tests vérifient désormais ce que l'IA reçoit (`knowledge_catalog.priority_context`, `delivered_text`, `priority_titles`), et non un texte figé.
