# -*- coding: utf-8 -*-

BASE_CONNAISSANCES = [
    {
        "categorie": "🌐 Accès, Connexion & Synchronisation",
        "declencheur": "Je ne trouve pas l'onglet ou l'icône iPackEPS sur mon portail Arena / Estérel...",
        "reponse_bot": """Bonjour ! Pas de panique, c'est le grand classique. L'icône met parfois un peu de temps à s'activer ou ta session a simplement besoin d'un petit coup de boost.

⚙️ **La manipulation magique :**
1. Connecte-toi sur ton interface **ESTEREL**.
2. Clique sur le bouton **« Aide »** en haut.
3. Sélectionne **« Synchro manuelle »**.
4. **Rafraîchis ta page** (`F5`).

*Note : Si l'icône reste introuvable, c'est que ton établissement n'a pas encore fait remonter ta structure ou ton installation administrative au Rectorat. Vérifie ce point avec ton secrétariat.*"""
    },
    {
        "categorie": "🌐 Accès, Connexion & Synchronisation",
        "declencheur": "Message d'erreur rouge : 'L'Établissement n'a pas été trouvé dans la base de données' (Accès Direction)",
        "reponse_bot": """Bonjour ! C'est une anomalie connue qui remonte lorsque les données de l'établissement sont incomplètes au niveau du Rectorat.

⚙️ **Ce qu'il faut faire :**
* **Ne bloquez pas :** Malgré la présence de ce message d'erreur visuel, vous pouvez tout de même accéder et travailler normalement sur votre établissement dans l'application.
* Le problème a été signalé aux services informatiques (DRASI) pour lier correctement votre code UAI."""
    },
    {
        "categorie": "🌐 Accès, Connexion & Synchronisation",
        "declencheur": "Message d'erreur rouge : 'Aucun Admin_Professeur trouvé pour cet Etablissement'",
        "reponse_bot": """Bonjour ! Ce message apparaît lorsque l'application tente d'actualiser l'équipe mais qu'aucun enseignant référent n'a encore été initialisé ou validé dans la base pour cet établissement.

⚙️ **L'action de terrain :**
* Les enseignants rattachés à des classes à examens doivent obligatoirement renseigner au préalable le formulaire d'enquête académique pour déclencher la création de leur profil.
* Dès que le premier profil est injecté par le support, le bouton **« Actualiser »** fonctionnera instantanément sans message d'erreur."""
    },
    {
        "categorie": "🌐 Accès, Connexion & Synchronisation",
        "declencheur": "Mon interface n'affiche pas l'accès spécifique 'IPR / Conseiller Technique' pour consulter le département",
        "reponse_bot": """Salut ! C'est un ajustement de droits au niveau du portail global. L'accès spécifique aux fonctionnalités IPR (pour guider les dossiers SSS du département) est parfois instable lors des vagues de déploiement.

⚙️ **La manipulation :**
* Tente une déconnexion complète, nettoie les cookies de ton navigateur, puis force une synchronisation manuelle via le bouton **« Aide »** d'Estérel.
* Si l'écran se fige ou si l'accès disparaît, pas d'inquiétude : une relance collective est en cours auprès de la DSI pour stabiliser les profils des conseillers techniques. En attendant, privilégie les échanges directs par mail avec les coordonnateurs."""
    },
    {
        "categorie": "🌐 Accès, Connexion & Synchronisation",
        "declencheur": "Nous n'arrivons plus du tout à nous connecter à l'application Estérel (erreur réseau / serveur)",
        "reponse_bot": """Bonjour ! Si l'accès global à Estérel est coupé ou inaccessible, cela relève d'une maintenance ou d'un incident technique sur les serveurs académiques généraux, et non d'iPackEPS.

⚙️ **L'action de terrain :**
* Prenez patience et retentez un peu plus tard.
* L'inspection est informée de ces difficultés d'accès temporaires et **les dates limites de transmission des dossiers seront bien évidemment adaptées** en conséquence pour ne pénaliser personne."""
    },
    {
        "categorie": "📝 Données Établissement & Référentiels",
        "declencheur": "Le nom du chef d'établissement, des adjoints ou de l'agent comptable est erroné ou obsolète (RAMSESE)",
        "reponse_bot": """Bonjour ! Pas d'inquiétude, l'application iPackEPS aspire automatiquement ces coordonnées depuis la base nationale **RAMSESE** des établissements. Il est techniquement impossible de modifier ces noms manuellement dans l'application.

⚙️ **L'action de terrain :**
* Demandez au secrétariat de direction d'envoyer un message à la **DIASEP** au rectorat pour mettre à jour le référentiel RAMSESE.
* **Rassurez votre équipe :** Ce décalage purement administratif n'est absolument pas bloquant pour le traitement des examens et la validation du CCF."""
    },
    {
        "categorie": "📝 Données Établissement & Référentiels",
        "declencheur": "Mon ancienneté ou ma date d'entrée dans l'établissement est fausse dans 'Ma fiche prof'",
        "reponse_bot": """Bonjour ! C'est un petit décalage historique lié à la remontée des données des bases académiques.

⚙️ **L'action de terrain :**
* **Ne perdez pas de temps avec ça :** Ces erreurs de profil n'ont strictement aucun impact sur vos saisies, vos élèves ou la validation des examens.
* La priorité absolue est mise sur la saisie des protocoles. Vous pourrez faire rectifier votre dossier auprès de votre secrétariat d'établissement dans un second temps."""
    },
    {
        "categorie": "📝 Données Établissement & Référentiels",
        "declencheur": "La saisie du registre des équipements de protection individuelle (EPI) est-elle obligatoire ?",
        "reponse_bot": """Bonjour ! Si votre établissement utilise déjà un autre outil ou un logiciel externe pour gérer le registre de vos EPI, **la double saisie sur iPackEPS n'est absolument pas obligatoire**. Vous pouvez ignorer ce module en toute sérénité."""
    },
    {
        "categorie": "🏃‍♂️ APSA, Référentiels (FCA) & Certifications",
        "declencheur": "Nous programmons du Demi-fond ET du Relais, mais l'application n'affiche qu'un onglet 'Courses'",
        "reponse_bot": """C'est le grand casse-tête de la rentrée ! Au niveau académique, l'application regroupe toutes les épreuves athlétiques de course sous l'activité unique « Courses ».

⚙️ **L'astuce de terrain :**
1. **Surtout, ne créez pas une fausse 'APSA établissement'** pour ruser, car cela répond à d'autres contraintes réglementaires et va bloquer le système.
2. Fusionnez informatiquement vos deux fiches FCA de course en **un seul et unique fichier PDF**.
3. Déposez ce fichier unique sous l'onglet national **« Courses »**.
4. **Précisez en commentaire** avant la transmission de votre dossier certificatif les épreuves de courses réellement programmées. L'inspection dispose de votre historique et fera la validation."""
    },
    {
        "categorie": "🏃‍♂️ APSA, Référentiels (FCA) & Certifications",
        "declencheur": "Je veux sélectionner mon APSA (ex: Cross-training, Marche), mais le bouton bascule 'Certificative' est bloqué",
        "reponse_bot": """Bonjour ! Pour qu'une APSA déclarée apparaisse dans votre dossier certificatif des examens, elle doit d'avance être activée à la racine de votre dossier EPS.

⚙️ **La manipulation :**
* Allez dans le menu **« Dossier EPS ➔ APSA »**.
* Trouvez votre activité dans la liste nationale ou académique.
* Basculez le bouton **« Certificative » sur OUI**. Elle s'ouvrira immédiatement pour vos dépôts de fiches FCA et vos groupes.
* *Rappel : Choisir une épreuve purement 'établissement' nécessite une validation préalable écrite de l'inspection.*"""
    },
    {
        "categorie": "🏃‍♂️ APSA, Référentiels (FCA) & Certifications",
        "declencheur": "L'application indique que le dossier est incomplet (ex: 97%) tant qu'on n'a pas rempli le 'fichier de synthèse'",
        "reponse_bot": """Pas de panique ! L'application iPackEPS propose des modules très vastes qui vont bien au-delà des strictes exigences des examens.

⚙️ **La règle d'or :**
* **Ignorez le fichier de synthèse de l'établissement** et les emplois du temps complets des classes non concernées par les examens.
* Pour la commission académique (CAHN), **seule la validation et la transmission des dossiers certificatifs (les lignes de vos classes de Terminales) sont attendues**. Ne tenez pas compte des pourcentages manquants si vos lignes d'examens sont bien validées au vert."""
    },
    {
        "categorie": "🏃‍♂️ APSA, Référentiels (FCA) & Certifications",
        "declencheur": "Est-ce que les notes de contrôle continu (moyennes de l'année) comptent pour le Bac EPS ?",
        "reponse_bot": """Bonjour ! La règle reste inchangée : **seule la note finale issue des épreuves du CCF de Terminale remonte sur Cyclades** (avec son coefficient 6). Les notes moyennes du contrôle continu classique de l'année ne sont pas prises en compte pour l'obtention du Baccalauréat EPS."""
    },
    {
        "categorie": "📊 Gestion des Classes & Protocoles (Bac, CAP, SSS)",
        "declencheur": "Un collègue (temps partagé / vacataire) n'apparaît pas dans la liste pour lui affecter des classes",
        "reponse_bot": """Bonjour ! iPackEPS est synchronisé avec les bases RH du Rectorat. Si un collègue n'apparaît pas dans votre liste d'équipe, c'est qu'il n'est rattaché informatiquement qu'à son établissement principal.

⚙️ **L'action de terrain :**
* Le secrétariat de votre établissement d'accueil doit obligatoirement procéder à son **installation administrative officielle** dans les bases de l'établissement.
* Les données remontent automatiquement au Rectorat et une synchronisation a lieu **chaque jour** pour mettre l'équipe à jour. Vous ne pouvez pas forcer l'ajout manuel d'un enseignant EN s'il n'a pas d'affectation administrative valide sur l'établissement."""
    },
    {
        "categorie": "📊 Gestion des Classes & Protocoles (Bac, CAP, SSS)",
        "declencheur": "En CAP, nous enseignons 3 activités mais les élèves n'en choisissent que 2. Blocage en classe entière.",
        "reponse_bot": """C'est normal. Les ensembles certificatifs réglementaires en CAP sont obligatoirement composés de **2 épreuves strictement**. Le système rejette le dossier si vous déclarez 3 APSA sur une classe entière.

⚙️ **L'astuce de terrain :**
1. Dans le menu 'Organisation des classes', basculez votre classe de CAP en **mode groupe** (même si vous êtes le seul enseignant).
2. Créez autant de protocoles qu'il y a de combinaisons de 2 épreuves possibles parmi vos 3 activités (Ex: si vous faites A, B et C, créez un protocole A-B, un protocole A-C, et un protocole B-C).
3. Répartissez vos élèves dans ces différents protocoles en début d'année selon les épreuves qu'ils passeront au final."""
    },
    {
        "categorie": "📊 Gestion des Classes & Protocoles (Bac, CAP, SSS)",
        "declencheur": "Comment gérer mes classes à double niveau ou mes options (1ère/Terminale Option ou Section Euro) ?",
        "reponse_bot": """Bonjour ! L'application iPackEPS est construite sur une logique purement **certificative du CCF examens**.

⚙️ **La règle à suivre :**
* Seuls les élèves de Terminale concernés par l'évaluation d'un examen cette année doivent être saisis.
* S'il s'agit d'un groupe d'option évalué uniquement dans le cadre du contrôle continu global (bulletins de l'établissement) et non du CCF officiel du Bac, **il n'est pas nécessaire de créer ce groupe dans iPackEPS**. Concentrez-vous uniquement sur les Terminales rattachés à un examen officiel."""
    },
    {
        "categorie": "📊 Gestion des Classes & Protocoles (Bac, CAP, SSS)",
        "declencheur": "Nous avons une classe de 'Seconde Prépa' (Prépa-Métiers) qui n'existe pas dans la liste",
        "reponse_bot": """Bonjour ! Pas de blocage : la qualification d'une classe de seconde de ce type ne comporte aucun enjeu pour les examens terminaux.

⚙️ **L'action :**
* Vous pouvez la qualifier de **« Seconde Générale »** dans le menu déroulant pour contourner le blocage et continuer vos saisies. L'anomalie a été signalée aux développeurs pour intégrer cette nomenclature."""
    },
    {
        "categorie": "📊 Gestion des Classes & Protocoles (Bac, CAP, SSS)",
        "declencheur": "J'ai créé mes protocoles d'activités adaptées (ex: Marche/Pétanque) mais l'application refuse de les valider",
        "reponse_bot": """Bonjour ! Les ensembles contenant des épreuves adaptées bénéficient d'un assouplissement des règles de composition, mais le moteur de vérification doit en être informé.

⚙️ **Le point à vérifier :**
* Allez dans votre récapitulatif des APSA, éditez votre activité et assurez-vous de cocher explicitement la case **« Adaptée »** dans ses propriétés (dans le tableau de droite). Une fois déclarée comme 'Adaptée', les contraintes se relâchent et vos protocoles se valideront immédiatement."""
    },
    {
        "categorie": "📊 Gestion des Classes & Protocoles (Bac, CAP, SSS)",
        "declencheur": "Section Sportive Scolaire (SSS) : Mes groupes sont créés, mais la bascule automatique affiche 'zéro élève'",
        "reponse_bot": """Bonjour ! C'est un petit problème classique lors du transfert automatique des structures de l'établissement.

⚙️ **Les points à vérifier :**
1. Assurez-vous que l'intitulé et la nomenclature de vos groupes sur iPackEPS sont **strictement identiques** à ceux configurés sur Pronote ou les bases administratives de l'établissement.
2. **Règle d'or : Chaque élève ne peut appartenir qu'à un seul et unique groupe.** Si un élève s'est retrouvé coché par erreur dans deux listes différentes, le système de bascule se bloque par sécurité et affiche un total de zéro. Nettoyez vos listes d'élèves !"""
    },
    {
        "categorie": "🛠️ Problèmes Techniques & Imports Cyclades",
        "declencheur": "Erreur systématique en essayant d'importer le fichier CSV des élèves depuis Pronote",
        "reponse_bot": """Bonjour ! C'est un bug technique identifié au niveau du module d'importation de fichiers externes lorsque les bases académiques reçoivent de gros volumes.

⚙️ **L'action du terrain :**
* Le problème a été remonté aux équipes de développement nationales pour correctif.
* Ne cherchez pas à forcer l'importation de masse des listes d'élèves tant que les structures administratives globales de l'établissement ne sont pas totalement stabilisées et synchronisées avec le Rectorat."""
    },
    {
        "categorie": "🛠️ Problèmes Techniques & Imports Cyclades",
        "declencheur": "J'ai validé ou enregistré par erreur un dossier SSS, impossible de faire machine arrière",
        "reponse_bot": """Bonjour ! Sur l'interface, certaines validations de dossiers ou enregistrements de statuts sont verrouillés pour garantir l'historique officiel et ne peuvent pas être annulés directement.

⚙️ **L'action :**
* Si un message ou un dossier incomplet a été validé par erreur, vous ne pouvez pas le supprimer vous-même. Envoyez directement un mail explicatif aux coordonnateurs du dispositif pour qu'ils effectuent la correction ou rejettent le dossier manuellement depuis leur interface de contrôle."""
    },
    {
        "categorie": "🛠️ Problèmes Techniques & Imports Cyclades",
        "declencheur": "Blocage sur un groupe mixte (Voie Générale + Technologique) : 'Les élèves ne suivent pas la même scolarité'",
        "reponse_bot": """Bonjour ! C'est une contrainte technique rigide imposée par l'interfaçage avec **Cyclades**. Cyclades sépare strictement les candidats selon leur série et leur scolarité pour générer les numéros de lots d'examen.

⚙️ **La solution de terrain :**
* Vous ne pouvez pas fusionner des élèves de filières différentes dans un même groupe d'examen sur l'application. Vous devez configurer votre structure de classe de manière à scinder vos protocoles ou créer des sous-groupes distincts respectant les filières (Générale d'un côté, Technologique de l'autre) afin de coller aux exigences de remontée de Cyclades."""
    },
    {
        "categorie": "🛠️ Problèmes Techniques & Imports Cyclades",
        "declencheur": "Erreur 'Message trop volumineux' en essayant d'envoyer la documentation d'aide par mail",
        "reponse_bot": """Bonjour ! C'est un blocage classique de serveur de messagerie (Erreur 554 5.2.3). Les guides complets d'utilisation d'iPackEPS contiennent beaucoup d'images et pèsent lourd (parfois plus de 12 Mo), ce qui dépasse le plafond autorisé par les serveurs de l'Enseignement Agricole ou du Ministère de l'Écologie.

⚙️ **L'astuce :**
* N'envoyez pas les fichiers PDF lourds en pièces jointes. Envoyez-leur directement l'adresse du site de l'académie de référence où tous les tutoriels et replays de visio sont hébergés et téléchargeables en ligne : **`https://ipackeps.ac-creteil.fr/spip.php?rubrique2`**. Ça passera instantanément !"""
    }
]
