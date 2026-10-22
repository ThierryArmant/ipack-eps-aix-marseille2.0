# Génération principale et secours technique

Activation demandée le 22 octobre 2026. La génération publique utilise Albert lorsque ALBERT_API_KEY est présent. Modèle par défaut : gpt-oss-120b (ALBERT_MODEL permet un identifiant exact différent). Température 0. La recherche vectorielle conserve OpenAI ; l'intégration n'est donc pas un abandon de toute dépendance ou dépense OpenAI.

## Configuration serveur

- ALBERT_API_KEY et OPENAI_API_KEY restent exclusivement dans les secrets.
- FOURNISSEUR_IA = "albert" est le comportement par défaut.
- FOURNISSEUR_IA = "openai" rétablit la génération OpenAI sans modification du code.
- Sans clé Albert, le fonctionnement antérieur OpenAI est conservé.
- MODELE_IA règle le modèle OpenAI de secours (gpt-4o-mini par défaut).
- Les réglages du Playground n'affectent pas ces appels.

## Déroulement

Le routeur est créé pour chaque question. Un seul essai Albert par appel logique, délai de transport 45 s, sortie plafonnée à 4 096 jetons. Si le transport, le quota, l'authentification ou l'enveloppe API rend le service inexploitable, le même prompt est envoyé une fois au secours OpenAI. Les nouvelles tentatives automatiques du client OpenAI sont désactivées ; délai 45 s. Il n'existe pas de boucle entre fournisseurs. Après un basculement, une éventuelle réparation documentaire de cette question reste sur le secours.

Une réponse structurée vide, erronée ou rejetée faute de preuves ne déclenche pas ce basculement : elle suit les contrôles documentaires existants, avec leur plafond de réparation. Une sortie tronquée ne déclenche pas non plus un changement de fournisseur. Si les deux services échouent, le repli documentaire existant reste utilisé ; aucune disponibilité absolue n'est garantie.

Le compteur enregistre les appels fournisseur réels, leur modèle, leur durée et les jetons réellement déclarés. L'échec Albert et le succès du secours font deux tentatives, pas un appel fictif unique. Si le fournisseur en échec ne renvoie pas d'usage, les jetons sont inconnus et le relevé est marqué incomplet : aucun coût nul n'est inventé. Le modèle réel et l'utilisation du secours apparaissent sous la réponse et dans les traces administrateur. Les champs additionnels du journal externe ne sont conservés que si son script les prend en charge.

Les modules de génération et contrôle sont chargés dans un ensemble identifié par leur contenu pour éviter une classe de trace obsolète au redéploiement, sans rechargement concurrent d'un module partagé.

## Comparateur privé

A reste OpenAI et D reste Albert seul, sans secours : une panne D doit rester visible pour ne pas attribuer à Albert une réponse produite par OpenAI. Le choix explicite d'académie du comparateur est maintenant conservé, sauf académie explicitement nommée dans la question. Le parcours public iPack n'hérite toujours pas silencieusement d'une académie choisie dans un autre contexte ; sa consigne d'indiquer l'académie dans la question demeure.

## Validation

843 tests locaux réussis : mécanisme de secours, conservation exacte du prompt, comptage des tentatives et traceurs imbriqués, absence de secours sur défaut documentaire, arrêt après échec des deux services, état isolé par question, chargement cohérent, séparation collège/lycée, contexte explicite du comparateur et suite existante. Pas de panne provoquée sur les services réels ni de modification des clés pour le test. La simulation de panne valide le mécanisme ; elle ne prouve pas la disponibilité future des fournisseurs.

Les corrections de fiches précisent les limites connues : accès distinct des élèves hors SIECLE, historique de saisie natation non établi, FCA académique distincte du dépôt établissement, dossier soumis distinct de validé. Aucune recherche web automatique ni mémorisation de réponse métier n'est ajoutée.
