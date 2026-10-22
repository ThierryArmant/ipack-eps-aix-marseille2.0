# Orientation courte et rédaction documentaire

Sur iPackEPS et Examens, lorsque le fournisseur principal est configuré, un petit modèle d’orientation compare les descriptions des fiches avant le filtre historique de priorité. Il ne rédige aucune réponse métier. Le fournisseur principal reçoit ensuite le contenu détaillé des fiches retenues et conserve tous les contrôles de preuve.

Le contexte public, l’onglet et l’académie sont transmis sans réinterprétation automatique. Chaque description comprend un objet, des extraits de présentation, de conditions et de limites, et précise qu’elle est partielle. Les descriptions sont extraites localement : aucun appel pour résumer la banque entière. Une recherche complémentaire locale peut retrouver une fiche moins prioritaire ou une section située dans un fichier composite.

Bornes : quatorze descriptions au plus, quatorze mille caractères de prompt, quatre fiches retenues au plus, une tentative d’orientation, vingt secondes de délai et six cents jetons de sortie au plus. La question n’est jamais tronquée pour tenir dans cette borne : une longue demande conserve le circuit antérieur. Les textes détaillés retenus ne sont pas coupés pour satisfaire le budget d’orientation.

Un choix ambigu conserve les branches proposées ; le rédacteur doit vérifier les conditions complètes et demander seulement la précision indispensable. Orientation sans correspondance : relecture des preuves complètes par le rédacteur, car une description partielle ne démontre pas que la fiche ne répond pas ; aucune autorisation ni procédure ne peut être déduite de cette incertitude. Erreur technique, identifiant inventé ou JSON invalide : retour au circuit documentaire antérieur, sans nouvelle tentative d’orientation.

Les tentatives et jetons sont séparés entre `selection` et `generation`. Une sélection réussie n’est pas comptée comme une utilisation du secours de rédaction. Le secours technique existant reste actif pour le fournisseur de rédaction. Les comparateurs privés existants et l’onglet Textes conservent leur parcours, afin de ne pas élargir l’expérience réglementaire sans mesure.

Activation par défaut dans les deux onglets concernés. Retour au fonctionnement antérieur : secret `ORIENTATION_FICHES = "legacy"`. Les parcours guidés et réponses documentaires sans génération ne déclenchent aucun appel d’orientation. Les résultats du rejeu administrateur restent séparés du journal des collègues.

Le choix d’un identifiant ne prouve jamais l’applicabilité juridique d’une fiche. Les contrôles et une mesure réelle restent nécessaires ; aucun taux de fiabilité garanti.

## Compatibilité de l’opération et des conditions

Le même appel d’orientation déclare désormais, pour chaque identifiant retenu, si l’opération est directe, voisine ou incertaine et si les conditions sont établies, inconnues ou incompatibles. Le programme valide ce contrat : une fiche déclarée voisine ou incompatible ne reste pas dans la sélection orientée. Une incertitude impose un statut ambigu, même si le sélecteur avait annoncé un choix certain. Les déclarations sont conservées dans la trace administrateur ; elles restent des jugements du modèle, jamais des preuves.

Si tous les choix proposés sont incompatibles, la lecture complète antérieure reste disponible avec une réserve explicite sur le risque de procédure voisine. Une description partielle ne justifie pas à elle seule un refus définitif. Le rédacteur doit présenter les alternatives documentées sous conditions ou demander uniquement la précision qui change la procédure. Aucun fait manquant ni réponse métier n’est ajouté par le programme. Aucun appel ni budget supplémentaire n’est créé.

Validation locale : contrats, exclusions, préservation de la branche compatible, ambiguïté et transmission au rédacteur. Une mesure en ligne reste nécessaire pour établir un gain de fiabilité ; les tests avec réponses simulées ne prouvent pas la justesse des choix d’un modèle réel.

Les extraits proches de la question sont choisis parmi les lignes de contenu, y compris le texte des articles. Les intitulés de sous-procédures et les termes peu répétés dans une fiche aident à distinguer une action précise d’une introduction générale. Ce classement reste local, sous le budget existant ; il ne garantit ni la récupération de la bonne fiche ni sa sélection par le modèle.

Lorsque l’orientation est active, l’exclusivité d’une notice ne coupe plus la recherche complémentaire avant comparaison. La notice reste candidate ; les procédures complémentaires gardent les filtres de portée et le plafond documentaire existants. Sur iPackEPS, la recherche locale par mots précède les compléments réglementaires. L’ancien circuit garde son arrêt anticipé par défaut.
