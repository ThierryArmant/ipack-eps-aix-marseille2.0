// Exécution hors réseau du vrai récepteur Apps Script, avec doubles Sheets.
const fs = require('node:fs'), vm = require('node:vm'), crypto = require('node:crypto'), assert = require('node:assert/strict');
class Sheet {
  constructor(headers=[]) { this.rows=headers.length?[headers]:[]; this.maxRows=10; this.maxCols=29; }
  getLastColumn(){return this.rows[0]?.length||0;} getLastRow(){return this.rows.length;}
  getMaxColumns(){return this.maxCols;} getMaxRows(){return this.maxRows;}
  insertColumnsAfter(_,n){this.maxCols+=n;} insertRowsAfter(_,n){this.maxRows+=n;}
  appendRow(row){this.rows.push(row);}
  insertRowAfter(n){this.rows.splice(n,0,[]);this.maxRows++;}
  getRange(r,c,n,m){return {getValues:()=>Array.from({length:n},(_,i)=>Array.from({length:m},(_,j)=>this.rows[r+i-1]?.[c+j-1]||'')),
    setValues:v=>v.forEach((row,i)=>{this.rows[r+i-1] ||= [];row.forEach((x,j)=>this.rows[r+i-1][c+j-1]=x);})};}
}
const sheets={'Feuille 1':new Sheet(['Date','Question','Mode','Niveau','Contexte','Réponse','','Ancien champ'])};
const book={getSheetByName:n=>sheets[n],insertSheet:n=>sheets[n]=new Sheet(),getSpreadsheetTimeZone:()=> 'Europe/Paris'};
const ctx={SpreadsheetApp:{openById:()=>book},LockService:{getScriptLock:()=>({waitLock(){},releaseLock(){}})},
  Utilities:{formatDate:()=> 'date', DigestAlgorithm:{SHA_256:1},Charset:{UTF_8:1},
    computeDigest:(_,s)=>[...crypto.createHash('sha256').update(s).digest()]},
  ContentService:{MimeType:{JSON:1},createTextOutput:s=>({setMimeType:()=>JSON.parse(s)})},console};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('integrations/google_sheets_trace.gs','utf8'),ctx);
function submit(text){const raw=JSON.stringify({id_essai:'essai',diagnostic:text});return {raw,result:ctx.hubJournalWithTrace_({id_essai:'essai',trace_json:raw,trace_sha256:crypto.createHash('sha256').update(raw).digest('hex'),question:'=IMPORTXML("x")',reponse:'réponse'})};}
let a=submit('court');assert.equal(a.result.trace_saved,true);
const journal=sheets['Feuille 1'];let heads=journal.rows[0];assert.equal(heads[7],'Ancien champ');assert.ok(journal.rows[1][heads.indexOf('Question')].startsWith("'="));assert.equal(journal.rows[1][heads.indexOf('Trace JSON')],a.raw);
let b=submit('😀'.repeat(50000));assert.equal(b.result.trace_saved,true);
assert.equal(sheets.Traces.rows.slice(1).map(r=>r[3]).join(''),b.raw);
assert.ok(sheets.Traces.rows.slice(1).every(r=>r[3].length<=40000));
assert.equal(journal.rows[2][heads.indexOf('Trace JSON')],a.raw);
let count=journal.rows.length;assert.equal(ctx.hubJournalWithTrace_({id_essai:'bad',trace_json:'{}',trace_sha256:'bad'}).ok,false);assert.equal(journal.rows.length,count);
console.log('Récepteur : JSON court/long, emoji, colonnes préservées, formules et empreinte vérifiés.');
