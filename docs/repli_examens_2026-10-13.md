# Repli documentaire des réponses Examens — 13 octobre 2026

Intervention limitée à `app.py`, `documentary_review.py` et leurs tests. Aucune modification des fiches, du catalogue, des registres ou du routage.

## Comportement

Si la réponse Examens reste rejetée après la réparation autorisée, le lecteur voit « Réponse non confirmée », avec un renvoi au service des examens de son académie. Le programme peut afficher un extrait littéral identifié parmi les documents effectivement transmis au modèle. Ce document est présenté comme une documentation retrouvée à vérifier pour la situation, pas comme une décision confirmée.

Le repli conserve les étiquettes de source et les réserves académiques. Il ne coupe pas une condition au milieu ; un extrait limité est annoncé comme incomplet. Sans document partageant le vocabulaire de la question, seul le message de non-confirmation est affiché. Une erreur réseau utilise le même repli, sans exposer le contenu de l'exception.

Les affirmations générées partiellement validées ne sont pas affichées : leur présence ne prouve pas que les conditions indispensables ont été conservées. Une réponse de repli n'entre pas dans le cache des réponses validées.

## Traces

Le seuil lexical est inchangé. Les rejets précisent les racines recherchées, les racines communes, le taux de couverture et le seuil. Les affirmations acceptées lors du premier appel sont désormais conservées dans le diagnostic, même si une réparation échoue ensuite.

Les traces complètes demeurent réservées à la session administrateur. Les quatre traces du passage public de réserve n'ont pas été conservées : un nouveau passage administrateur produira de nouvelles traces, pas les traces originales. Aucun assouplissement du contrôle ne peut être justifié par les seuls messages d'erreur publics.

## Validation et limites

244 tests passent après intégration des corrections de fiches de `61bc1f2` ; compilation Python et contrôle des espaces réussis. Les tests couvrent notamment la publication de réponses incomplètes, une erreur réseau contenant un secret, les réserves hors Aix, l'absence de document pertinent, une condition trop longue et le diagnostic lexical.

Ce changement rend l'échec compréhensible et fournit une documentation de recours ; il ne corrige ni la sélection des fiches ni la justesse sémantique du modèle. Un extrait pertinent reste à vérifier pour le cas. La validation en ligne doit être consignée avec la version affichée avant tout nouveau gel pour la mesure.
