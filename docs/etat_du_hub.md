# État du hub : à lire avant toute intervention

Mis à jour le 18 novembre 2026. Cette page résume ce qui est en place, ce qui a été mesuré et ce qui a déjà été
essayé puis écarté. Elle remplace, pour la reprise, `docs/reprise_projet.md` (13 octobre) et
`docs/reprise_pour_gpt_2026-10-18.md`, qui décrivent l'ancien moteur. Le détail daté reste dans
`docs/journal_coordination.md`.

Règle d'usage : ne rien proposer sur le moteur avant d'avoir lu la section 4. Mettre cette page à jour quand une
mesure, une décision ou un abandon change ce qu'elle dit.

## 1. Règles fixées par le responsable du hub

- **Règle de fonctionnement, permanente :** une erreur se corrige en complétant et en ordonnant les fiches, pour que le hub retrouve seul la réponse à toute la famille de questions du même ordre. Jamais de réponse toute prête écrite pour une question, jamais de consigne adressée au modèle dans une fiche (« ne pas confondre », « répondre que… »), jamais de règle de routage ajoutée pour une seule question. Test avant d'écrire une ligne : servirait-elle à une autre question sur le même écran ou la même règle ? Sinon, elle n'entre pas.
- Le hub répond seul à une question. Pas de conversation suivie, pas de parcours guidé à questions successives.
  Si la question ne précise pas sa situation : réponse au cas le plus courant, puis boutons pour l'autre cas.
- La force attendue : un pas à pas avec les menus entre crochets et une phrase d'explication par étape. Les « autres
  cas » non demandés ne s'affichent pas sous la réponse.
- Coût : deux appels par question au plus (une sélection, une rédaction). Le rédacteur gratuit est un choix de budget.
- Sources : le site d'assistance iPackEPS de Créteil fait foi pour iPackEPS ; les textes officiels tranchent toute
  contradiction, y compris face à une réponse d'assistance. Aucune fiche que l'on n'a pas pu vérifier.
- Aucune note ne se saisit dans iPackEPS. Les dates dépendent de chaque académie et ne s'affichent jamais comme
  nationales. Rien sur l'UNSS. `data/bibli_concours` reste neutralisé. Pas de contenu de séance ni de cycle.
- Ce qui change chaque année (référentiels, listes d'activités, textes d'examen) vit dans des fichiers remplaçables,
  jamais en dur dans le code. Les réponses en dur sont réduites au minimum.
- Les corrections se poussent directement sur `main`, par petits commits, fiches et programme séparés.

## 2. Motorisation en place (chemin réel d'une question)

1. `app.py` : refus hors périmètre, public et onglet, quelques réponses directes (la plupart sont éteintes).
2. `document_retrieval.py` : jusqu'à 10 documents, dans cet ordre : fiches prioritaires du catalogue
   (`config/catalogue_documents.json`, motifs de mots), recherche par mots, recherche par le sens.
3. `exact_source_answer.py` : un appel au modèle de sélection (Mini). Il lit les documents entiers et rend une
   source principale, des compléments et les identifiants des passages à afficher. Un passage est une ligne de fiche.
4. `short_answer.py` : un appel au modèle de rédaction (Albert, `gpt-oss-120b`). Il ne reçoit que les passages
   retenus et rend des phrases, chacune avec les numéros des passages qui la justifient.
5. Contrôle du code, phrase par phrase : menu, interlocuteur, nombre, date, portée académique, objet absent de la
   fiche. Une phrase refusée est retirée ; si rien ne reste, le hub affiche « je n'ai pas trouvé » et les extraits.
6. Affichage : réponse courte, ligne « Accès à la fonctionnalité » recopiée de la fiche, extraits repliés, liens.
7. Journal : une ligne dans la feuille « questions hub » et une trace JSON complète par question dans Drive.

Dans le code, le rédacteur est encore marqué « en pause » (`ALBERT_PAUSED`) et passe par l'autorisation prévue
pour les essais. L'ancien moteur « Conditions / Démarches » reste présent, utilisé seulement si l'administrateur
décoche le mode documenté.

## 3. Mesures

| Date | Lot | Résultat |
|---|---|---|
| 13 octobre | 2e mesure, 50 questions | 74 % justes, 10 % fausses |
| 17 octobre | 3e mesure, 50 questions, trois onglets | 64 % justes, 14 % fausses |
| 25 octobre | Lot B 50, sélection et rédaction par Mini | 76 % |
| 25 octobre | Lot B 50, Albert seul (cherche et rédige) | 72 %, 1 fausse |
| 26 octobre | Lot B 50, Mini choisit, Albert rédige, format court | 82 % |
| 26 octobre | Même moteur, format pas à pas | 72 %, puis 80 %, puis 86 % après corrections |
| 26 octobre | Onglet Textes, 50 questions | 76 % |
| 26 octobre | 111 questions jamais vues | 68 % ; 59 % sur de vraies FAQ |
| 10 au 14 novembre | 10 questions réelles de collègues | 3 justes |

Les lots servent aussi à corriger : leurs scores surestiment le niveau réel. La référence utile est le taux sur des
questions jamais vues et sur les questions réelles.

## 4. Déjà essayé et écarté (ne pas reproposer sans mesure nouvelle)

- Le rédacteur lit plus que les passages retenus : rédaction sur les sources entières, « pool commun », rédacteur qui
  cherche seul. Résultat : boutons et droits inventés, cadrage faux (CCF et ponctuel présentés comme deux étapes).
- Comparateurs E (consigne d'isolation des procédures) et F (plan de contexte en un appel de plus) : pas de gain.
- Grille de complétude, relevé préparatoire avant rédaction, « contrat » expérimental : plus coûteux, sans progrès.
- Vingt passages au lieu de dix : pas de gain, retour à dix.
- Cache de réponses : retiré le 14 octobre.
- Question de précision posée sous la réponse : retirée, elle générait des fautes.
- « Moule commun » ajouté en fin de fiche (action, objet, attendu) : ne suffit pas, et un paragraphe ajouté après
  une FAQ peut être rattaché à la dernière réponse.
- Fiches reprises d'autres académies sans lecture directe : retirées.

## 5. Ce que montrent les traces réelles (50 traces, 29 octobre au 14 novembre)

- La mécanique tient : 46 sélections valides sur 47, 41 réponses rédigées, aucune panne de fournisseur.
- Les contrôles refusent 13 % des phrases (27 sur 211). Ils ont raison le plus souvent.
- La rédaction prend 16 secondes en médiane, la sélection 1,6.
- Dans 20 réponses sur 47, une même fiche occupe au moins 3 des 10 places du contexte.
- Les erreurs sont des erreurs de sens, dans cet ordre de fréquence :
  1. bonne fiche, mauvais passage retenu (phrase de renvoi, question voisine d'une FAQ) ;
  2. bonne fiche absente des 10 documents ;
  3. fiche manquante ;
  4. étape juste refusée par un contrôle.

## 6. Méthode qui a donné des résultats

- Partir de la trace réelle de la question, et situer l'étape fautive : recherche, sélection, rédaction, contrôle
  ou fiche manquante. Une réponse lue sans sa trace ne suffit pas.
- Corriger la fiche en cause, pas le moteur : la réponse complète d'un cas tient dans un seul passage, sans renvoi
  (« ci-dessous », « voir le diagnostic »), avec les mots réels du collègue et les menus entre crochets.
- Après toute modification de fiche : `python portee_registre.py --write`, empreinte dans
  `docs/audit_fiches/registre.json`, puis `python3 -m unittest discover -s tests`.
- Aucun nouveau motif de mots pour une seule question quand la fiche peut porter la correction.
- Une modification du moteur se juge sur le rejeu du lot B (référence : 86 %) et sur des questions réelles.

## 7. Chantiers ouverts

- Fiches manquantes, en attente d'une réponse vérifiée : jauge « liste APSA à 0 % », redirection en boucle vers le
  portail académique, baignade en sortie avec un assistant d'éducation titulaire du BNSSA, lieu de dépôt du
  procès-verbal du conseil d'administration pour une section sportive.
- Doublons sur la synchronisation manuelle du portail (trois fiches proches).
- Recherche : une même fiche limitée à deux des dix places (18 novembre, eaa677d). En ligne, non mesuré : à juger sur rejeu réel de l'onglet iPackEPS, annulation par `git revert eaa677d` si moins bon.
- Le hub ne sait pas dire « je n'ai pas d'information » quand aucune fiche ne traite du sujet : il recolle des fiches voisines (cas du 18 novembre, élève rejeté en acrosport). Fiche harcèlement entre élèves ajoutée ; le défaut général reste ouvert.
- Capeps (épreuves, programme) : hors des bases depuis la neutralisation de `data/bibli_concours` ; réponse fixe à décider par le responsable.
- `requirements.txt` ne fixe aucune version (proposé le 2 novembre, non fait).
- Ménage du code (ancien moteur, essais administrateur, réponses en dur éteintes) : à faire seulement après une
  mesure stable, par petits commits.
