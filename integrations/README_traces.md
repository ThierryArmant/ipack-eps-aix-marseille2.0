# Traces JSON privées — journal du Hub

Solution retenue par Thierry : un fichier JSON complet par réponse dans un dossier Drive privé, avec son lien direct dans le classeur existant « questions hub ». Aucun second classeur. Le Sheet a été passé en accès restreint le 28 octobre 2026, sur demande explicite ; le propriétaire ajoutera ses deux lecteurs ensuite. Pour lire les JSON, il faudra également leur accorder l'accès au dossier privé.

Le dossier est identifié par `HUB_TRACE_FOLDER_ID` dans `google_sheets_trace.gs`. Vérifier ses permissions : pas de partage général par lien. Les fichiers créés héritent du dossier ; le code n'ajoute aucune permission publique.

## Intégration

Ajouter le module à `JournalTraces.gs` sans remplacer le `Code.gs` historique. Dans le `doPost(e)` existant, après la lecture JSON :

```javascript
if (data.question && data.reponse && data.trace_json) return hubJournalWithTrace_(data);
```

Les autres fonctions restent inchangées. Les réponses récentes sont insérées en ligne 2. Les colonnes historiques restent repérées par leurs titres. Colonnes ajoutées : ID essai, Trace JSON (lien), Trace statut, Trace SHA256, Modèles IA, Secours GPT. Le JSON est validé et son empreinte vérifiée avant création. Une erreur Drive laisse la réponse enregistrée avec un statut d'échec de trace ; une erreur d'intégrité rejette la requête technique.

## Autorisations et vérification

`DriveApp` nécessite une autorisation Drive du compte qui exécute le déploiement. `verifierAccesDossierTraces` ne fait que lire le nom du dossier, sans appel IA ni création de fichier. Son succès seul ne prouve pas le droit de créer un JSON. Vérifier aussi la création effective par un essai synthétique, l'accusé `trace_saved`, le lien du Sheet et le contenu/empreinte du fichier. Les autorisations de consultation et d'écriture peuvent être distinctes.

État au 28 octobre : version Web 15 déployée sur l'URL existante ; un essai synthétique sans IA a échoué car accès Drive non autorisé. Aucun JSON sauvegardé ni réussite revendiquée. Le code local comprend depuis une gestion de cet échec qui conserve la réponse ; cette dernière modification n'est pas encore redéployée. Un retour temporaire à la version 14 a été bloqué par la revue automatique en attente d'autorisation explicite. Ne pas confondre code enregistré, version Web déployée et autorisations accordées. La validation d'identité Google puis l'autorisation Drive restent à terminer.


## Mise à jour vérifiée — 28 octobre, 23 h 48

Le déploiement Web actif est désormais la **version 16** (même URL). Le correctif qui conserve la ligne en cas d'échec Drive est déployé. Un POST synthétique sans IA a renvoyé `ok:true, trace_saved:false` ; la ligne a été vérifiée dans le Sheet avec sa question, sa réponse, son identifiant, son empreinte et le statut « Échec JSON — accès Drive à vérifier ». Le lien reste vide, aucune création de JSON n'étant confirmée. Les paragraphes ci-dessus sur la version 15 décrivent l'état antérieur. La validation OAuth Drive par le propriétaire reste nécessaire ; ne pas annoncer les traces comme opérationnelles avant un fichier et son lien vérifiés.
## 28 octobre, 23 h 55 (Claude)
- Autorisation Drive accordée par Thierry en lecture seulement : `verifierAccesDossierTraces` réussit, mais `createFile` échoue (« Autorisations requises : …/auth/drive »). La ligne du Sheet est bien conservée avec le statut « Échec JSON — accès Drive à vérifier » (essais TEST TECHNIQUE en versions 17 et 18).
- Versions Web 17 puis 18 déployées sur la même URL ; la 18 journalise le message d'erreur Drive.
- Ajout de `verifierCreationTrace` (crée un fichier de test dans le dossier privé puis le met à la corbeille) pour redemander l'autorisation en écriture. En attente de l'accord de Thierry ; l'installation n'est pas déclarée opérationnelle.
