/** Récepteur du journal Hub. Projet lié au Sheet « questions hub ».
 * Déploiement : application Web, exécuter en tant que propriétaire.
 * Ajouter dans Code.gs après JSON.parse :
 * if (data.question && data.reponse && data.trace_json) return hubJournalWithTrace_(data);
 * Conserver les autres actions du doPost existant.
 * JSON dans un dossier Drive privé ; lien seul dans le journal.
 * Pas de lecture des traces par HTTP.
 */
const HUB_SHEET_ID = '1kY1NMmAQcwkqkZTAWheIYeg_Jcc1M8Qh6UrhJsEc8eI';
const HUB_TRACE_FOLDER_ID = '1m0lZOttwsnYTcsPjVXzqySS6uWCyCsZa';

function hubJournalWithTrace_(p) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const book = SpreadsheetApp.openById(HUB_SHEET_ID);
    const sheet = book.getSheetByName('Feuille 1');
    if (!sheet) throw new Error('Onglet journal absent');
    let headers = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0];
    const names = ['Date','Question','Mode','Niveau','Contexte','Réponse','Académie','Version',
      'Appels IA','Jetons entrée','Jetons sortie','Durée IA (s)','Cache','Modèles IA',
      'Secours GPT','ID essai','Trace JSON (lien)','Trace statut','Trace SHA256'];
    names.forEach(name => { if (headers.indexOf(name) < 0) headers.push(name); });
    if (headers.length > sheet.getMaxColumns()) sheet.insertColumnsAfter(sheet.getMaxColumns(), headers.length - sheet.getMaxColumns());
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    const values = {'Date': Utilities.formatDate(new Date(), book.getSpreadsheetTimeZone(), 'dd/MM/yyyy HH:mm:ss'),
      'Question':p.question, 'Mode':p.mode, 'Niveau':p.niveau, 'Contexte':p.contexte, 'Réponse':p.reponse,
      'Académie':p.academie, 'Version':p.version, 'Appels IA':p.appels_ia,
      'Jetons entrée':p.jetons_entree, 'Jetons sortie':p.jetons_sortie, 'Durée IA (s)':p.duree_ia_s,
      'Cache':p.cache, 'Modèles IA':p.modeles_ia, 'Secours GPT':p.secours_gpt};
    let saved = false;
    if (p.trace_json && p.id_essai) {
      const trace = JSON.parse(p.trace_json);
      if (trace.id_essai !== p.id_essai) throw new Error('Identifiant incohérent');
      const hash = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, p.trace_json, Utilities.Charset.UTF_8)
        .map(b => ('0' + ((b + 256) % 256).toString(16)).slice(-2)).join('');
      if (hash !== p.trace_sha256) throw new Error('Empreinte incohérente');
      values['ID essai'] = p.id_essai;
      values['Trace SHA256'] = hash;
      try {
        const folder = DriveApp.getFolderById(HUB_TRACE_FOLDER_ID);
        // Hérite des accès du dossier ; aucun partage par lien ajouté.
        const file = folder.createFile('trace_' + p.id_essai + '.json', p.trace_json, 'application/json');
        values['Trace JSON (lien)'] = file.getUrl();
        values['Trace statut'] = 'JSON enregistré';
        saved = true;
      } catch (error) {
        values['Trace statut'] = 'Échec JSON — accès Drive à vérifier';
        console.error('Création de la trace impossible : ' + error.name + ' — ' + error.message);
      }
    } else values['Trace statut'] = 'non fournie';
    // Échapper les préfixes de formule dans les contenus reçus.
    const row = headers.map(h => literal_(values[h] == null ? '' : values[h]));
    // Conserver l'ordre du journal existant : la plus récente en ligne 2.
    sheet.insertRowAfter(1);
    sheet.getRange(2, 1, 1, row.length).setValues([row]);
    return json_({ok:true, trace_saved:saved, id_essai:p.id_essai || ''});
  } catch (error) {
    console.error('Échec du journal Hub : ' + error.name);
    return json_({ok:false, trace_saved:false});
  } finally { lock.releaseLock(); }
}

function literal_(value) {
  return typeof value === 'string' && /^[=+@-]/.test(value) ? "'" + value : value;
}
function json_(value) {
  return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON);
}

// Vérification des accès uniquement : aucune génération IA, aucune création de fichier.
function verifierAccesDossierTraces() {
  console.log('Dossier accessible : ' + DriveApp.getFolderById(HUB_TRACE_FOLDER_ID).getName());
}

// Vérification de l'écriture : crée un petit fichier de test dans le dossier privé puis le met à la corbeille.
// À lancer depuis l'éditeur : déclenche la demande d'autorisation Drive en écriture si elle manque.
function verifierCreationTrace() {
  const file = DriveApp.getFolderById(HUB_TRACE_FOLDER_ID)
    .createFile('test_ecriture_trace.json', '{"test":true}', 'application/json');
  console.log('Écriture autorisée : ' + file.getName());
  file.setTrashed(true);
}
