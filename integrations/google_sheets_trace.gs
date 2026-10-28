/** Récepteur du journal Hub. Projet lié au Sheet « questions hub ».
 * Déploiement : application Web, exécuter en tant que propriétaire.
 * Ne pas modifier le partage privé du classeur. Pas de lecture des traces par HTTP.
 */
const HUB_SHEET_ID = '1kY1NMmAQcwkqkZTAWheIYeg_Jcc1M8Qh6UrhJsEc8eI';
const HUB_TRACE_CELL_LIMIT = 40000; // unités UTF-16, sous la limite des cellules

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const p = JSON.parse(e.postData.contents);
    const book = SpreadsheetApp.openById(HUB_SHEET_ID);
    const sheet = book.getSheetByName('Feuille 1');
    if (!sheet) throw new Error('Onglet journal absent');
    let headers = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1)).getValues()[0];
    const names = ['Date','Question','Mode','Niveau','Contexte','Réponse','Académie','Version',
      'Appels IA','Jetons entrée','Jetons sortie','Durée IA (s)','Cache','Modèles IA',
      'Secours GPT','ID essai','Trace JSON','Trace statut','Trace SHA256'];
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
      if (p.trace_json.length <= HUB_TRACE_CELL_LIMIT) {
        values['Trace JSON'] = p.trace_json;
        values['Trace statut'] = 'complète';
      } else {
        const parts = splitTrace_(p.trace_json);
        const target = book.getSheetByName('Traces') || book.insertSheet('Traces');
        if (!target.getLastRow()) target.appendRow(['ID essai','Partie','Total','Fragment JSON','SHA256']);
        const first = target.getLastRow() + 1;
        const rows = parts.map((part, i) => [p.id_essai, i + 1, parts.length, literal_(part), hash]);
        if (first + rows.length - 1 > target.getMaxRows()) target.insertRowsAfter(target.getMaxRows(), first + rows.length - 1 - target.getMaxRows());
        target.getRange(first, 1, rows.length, 5).setValues(rows);
        values['Trace JSON'] = JSON.stringify({storage:'Traces',id_essai:p.id_essai,parts:parts.length,sha256:hash});
        values['Trace statut'] = 'complète — onglet Traces';
      }
      saved = true;
    } else values['Trace statut'] = 'non fournie';
    // setValues n'interprète aucun contenu reçu comme formule.
    const row = headers.map(h => literal_(values[h] == null ? '' : values[h]));
    sheet.getRange(sheet.getLastRow() + 1, 1, 1, row.length).setValues([row]);
    return json_({ok:true, trace_saved:saved, id_essai:p.id_essai || ''});
  } catch (error) {
    console.error('Échec du journal Hub : ' + error.name);
    return json_({ok:false, trace_saved:false});
  } finally { lock.releaseLock(); }
}

function splitTrace_(text) {
  const parts = [];
  for (let start = 0; start < text.length;) {
    let end = Math.min(start + HUB_TRACE_CELL_LIMIT, text.length);
    // Ne pas couper une paire de substitution (emoji).
    if (end < text.length && /[\uD800-\uDBFF]/.test(text[end - 1])) end--;
    parts.push(text.slice(start, end));
    start = end;
  }
  return parts;
}
function literal_(value) {
  return typeof value === 'string' && /^[=+@-]/.test(value) ? "'" + value : value;
}
function json_(value) {
  return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON);
}
