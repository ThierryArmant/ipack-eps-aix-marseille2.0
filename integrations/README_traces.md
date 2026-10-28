# Activation des traces du Hub

Le fichier `google_sheets_trace.gs` complète le projet Apps Script existant, sans remplacer les autres fonctions (notamment les anciennes actions du Hub).

1. Vérifier le partage du classeur : accès restreint et invitations individuelles des lecteurs autorisés. Un onglet masqué ne protège pas les traces d'un lecteur du classeur.
2. Ajouter le contenu du fichier dans `JournalTraces.gs` du projet existant.
3. Dans le `doPost(e)` existant, juste après `const data = JSON.parse(e.postData.contents);`, ajouter :

```javascript
if (data.question && data.reponse && data.trace_json) return hubJournalWithTrace_(data);
```

Conserver les autres branches du récepteur. Les messages historiques sans trace suivent le chemin d'origine. Les nouvelles réponses restent insérées en ligne 2 ; les colonnes A–F et Q–W conservent leur rôle et les colonnes supplémentaires sont repérées par leur titre. Le JSON long est découpé sans perte, ses fragments étant à concaténer dans l'ordre `Partie` avant `JSON.parse`. Comparer l'empreinte SHA256 après concaténation.

4. Mettre à jour le déploiement Web existant avec une nouvelle version, en conservant son URL, son identité d'exécution et ses autorisations. Ne pas lancer les fonctions Gemini ni un rejeu IA pour tester la journalisation.
5. Envoyer un essai synthétique explicitement marqué technique, puis vérifier l'accusé `trace_saved`, l'identifiant et l'empreinte par lecture du Sheet. Tant que ce contrôle n'est pas effectué, l'activation n'est pas considérée comme complète.

## État constaté le 28 octobre 2026

Connexion du propriétaire réussie ; projet existant retrouvé. La fenêtre de partage du classeur ne liste que le propriétaire et un accès lecteur général par lien, contrairement à l'hypothèse de deux lecteurs déjà invités. Conserver le partage tant que les comptes à inviter ne sont pas identifiés, puis supprimer le partage général avant activation. Le module a été préparé séparément ; le récepteur en production n'a pas été redéployé et aucune trace privée n'a été ajoutée au Sheet.
