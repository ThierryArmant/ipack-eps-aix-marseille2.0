# Comparaison de modèles — administration

La clé est lue côté serveur depuis `st.secrets["ALBERT_API_KEY"]`, uniquement dans le bloc administrateur. Elle n'est jamais intégrée au dépôt, à une question, à une trace de génération ou à un téléchargement. Le parcours des collègues conserve `MODELE_IA` et `OPENAI_API_KEY`.

## Utilisation

1. Ouvrir le comparateur administrateur.
2. Cliquer sur « Charger les modèles Albert accessibles — sans génération ». Cela effectue uniquement `GET /v1/models`, avec la clé présente dans les secrets. La liste est conservée dans cette session ; un changement de clé invalide cette liste.
3. Choisir « D — Albert, mêmes fiches que A » et un modèle de génération accessible. Un identifiant exact peut être saisi si le modèle n'est pas dans la liste. Le secret facultatif `ALBERT_MODEL` préremplit cet identifiant.
4. Choisir le contexte, saisir une question, puis lancer explicitement le test.
5. Lire les deux réponses, les sources et les traces, puis télécharger le résultat privé.

## Périmètre du test

A et D partagent la même recherche initiale, la question originale, le contexte effectif, les consignes et les contrôles documentaires. D ne lance ni interprétation B ni détection du doute C. Les guides, clarifications préalables et réponses documentaires directes sont traités en commun ; lorsqu'ils suffisent, aucun modèle n'est appelé.

La température est identique. L'adaptateur Albert plafonne la sortie à 4 096 jetons et refuse une sortie signalée tronquée. Le plafond du modèle A reste sa configuration existante. Ce point doit être pris en compte dans l'analyse ; il n'est pas affirmé que les réglages internes des fournisseurs sont identiques. Une éventuelle réparation par les contrôles est comptée séparément.

Les compteurs proviennent de l'API. S'ils sont absents, l'usage est signalé incomplet, sans estimation. Les recherches vectorielles restent hors compteurs. Aucun appel de génération à l'ouverture, au changement de champ ou au téléchargement. Une erreur d'un modèle ne provoque aucun remplacement silencieux par l'autre.

## Accès et erreurs

L'adresse de destination est fixée à `https://albert.api.etalab.gouv.fr/v1`. Les redirections HTTP ne sont pas suivies ; la clé ne peut ainsi pas être renvoyée vers un autre site. Les erreurs utilisent des messages génériques, sans corps de réponse, en-têtes ni détails contenant la clé. Aucun nouvel essai de transport automatique après un échec ou un dépassement de délai.

L'accès au catalogue ne garantit pas qu'une génération soit autorisée sur chaque modèle ; les quotas et les habilitations restent ceux du compte Albert. Aucun renouvellement, changement d'expiration ou révocation de clé n'est effectué par le hub.

## Statut

Fonction d'expérimentation réservée à l'administration. Aucun gain de qualité annoncé avant un comparatif réel. Le prototype de clarification C reste expérimental ; l'ajout de D ne le valide pas.

Documentation de référence : https://guides.ia.numerique.gouv.fr/albert-api ; authentification : https://guides.ia.numerique.gouv.fr/albert-api/compte-and-usage/api-keys .
