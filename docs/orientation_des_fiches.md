# Orientation courte et rédaction documentaire

Sur iPackEPS et Examens, lorsque le fournisseur principal est configuré, un petit modèle d’orientation compare les descriptions des fiches avant le filtre historique de priorité. Il ne rédige aucune réponse métier. Le fournisseur principal reçoit ensuite le contenu détaillé des fiches retenues et conserve tous les contrôles de preuve.

Le contexte public, l’onglet et l’académie sont transmis sans réinterprétation automatique. Chaque description comprend un objet, des extraits de présentation, de conditions et de limites, et précise qu’elle est partielle. Les descriptions sont extraites localement : aucun appel pour résumer la banque entière. Une recherche complémentaire locale peut retrouver une fiche moins prioritaire ou une section située dans un fichier composite.

Bornes : quatorze descriptions au plus, quatorze mille caractères de prompt, quatre fiches retenues au plus, une tentative d’orientation, vingt secondes de délai et six cents jetons de sortie au plus. La question n’est jamais tronquée pour tenir dans cette borne : une longue demande conserve le circuit antérieur. Les textes détaillés retenus ne sont pas coupés pour satisfaire le budget d’orientation.

Un choix ambigu conserve les branches proposées ; le rédacteur doit vérifier les conditions complètes et demander seulement la précision indispensable. Aucune fiche pertinente sélectionnée : réserve documentaire, sans rédaction sur une fiche voisine. Erreur technique, identifiant inventé ou JSON invalide : retour au circuit documentaire antérieur, sans nouvelle tentative d’orientation.

Les tentatives et jetons sont séparés entre `selection` et `generation`. Une sélection réussie n’est pas comptée comme une utilisation du secours de rédaction. Le secours technique existant reste actif pour le fournisseur de rédaction. Les comparateurs privés existants et l’onglet Textes conservent leur parcours, afin de ne pas élargir l’expérience réglementaire sans mesure.

Activation par défaut dans les deux onglets concernés. Retour au fonctionnement antérieur : secret `ORIENTATION_FICHES = "legacy"`. Les parcours guidés et réponses documentaires sans génération ne déclenchent aucun appel d’orientation. Les résultats du rejeu administrateur restent séparés du journal des collègues.

Le choix d’un identifiant ne prouve jamais l’applicabilité juridique d’une fiche. Les contrôles et une mesure réelle restent nécessaires ; aucun taux de fiabilité garanti.
