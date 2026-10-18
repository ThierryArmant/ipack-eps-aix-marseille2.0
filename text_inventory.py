"""Classement éditorial exhaustif des fiches Textes, sans déplacer leurs références."""
import json
import re
from pathlib import Path

DOMAINS = {
 '01_service_statuts': 'Service, statuts, rémunération et qualifications EPS',
 '02_carriere': 'Carrière, recrutement, mobilité et recours',
 '03_responsabilite': 'Responsabilité et protection des personnels',
 '04_vie_etablissement': 'Vie scolaire, direction, laïcité et égalité',
 '05_sante': 'Santé, inaptitudes et inclusion',
 '06_sorties_transports': 'Sorties, voyages, transports et accompagnateurs',
 '07_securite': 'Sécurité des activités, équipements et APPN',
 '08_urgences': 'Urgences et accidents des élèves',
 '09_programmes': 'Programmes, horaires et ressources pédagogiques',
 '10_examens': 'Certification et aménagements des examens',
 '11_numerique': 'Données personnelles, images et intelligence artificielle',
 '12_reperes': 'Repères transversaux, dispositifs et circuits académiques',
}
NUMBERS = {2:3,4:4,5:7,6:5,8:1,9:1,10:1,11:1,12:1,13:9,14:10,15:10,16:10,19:4,20:6,21:11,22:10,23:8,24:6,25:7,26:7,29:7,30:7,31:7,32:3,33:9,34:9,35:9,36:9,37:4,38:4,39:6,40:6,41:6,42:6,43:7,44:5,45:7,46:2,47:2,48:2,49:2,52:2,54:12,55:12,56:3,58:7,59:10,60:8,61:1,62:6}
NAMED = {
 'complement_natation':7, 'complement_obligations':1,'complement_statuts':1,
 'escalade_controles':7,'accident_eleve':8,'appn_moyens':7,'arrete_1989':5,
 'correspondant_06':7,'cumul_activite':1,'decret_2025':4,'decret_2026':4,
 'demifond_college':9,'deplacements_reguliers':6,'direction_ecole':4,
 'dispense_inaptitude':5,'escalade_relais':7,'fournitures_neutralite':4,
 'ia_usages':11,'imp_attribution':1,'intervenants_eps':6,'obligations_service_premier':1,
 'pai_pratique':5,'programme_eps_sixieme':9,'signalement_violences':3,
 'sortie_musee':6,'sorties_mixte':6,'sorties_premier':6,'sorties_second':6,
 'tzr_decret':1,'partenariats_defense':12,'premier_degré':12,'sorties_encadrement':6,
}

def domain_for(path):
    match = re.search(r'base_textes_officiels_(\d+)_', path.name)
    number = NUMBERS[int(match.group(1))] if match else next((v for k,v in NAMED.items() if path.name.startswith(k)), None)
    if number is None:
        raise ValueError('Fiche non classée : ' + str(path))
    return next(k for k in DOMAINS if k.startswith(f'{number:02d}_'))


def build():
    catalogue_path = Path('config/catalogue_documents.json')
    cat=json.loads(catalogue_path.read_text())
    records=[]
    for p in sorted(Path('data/textes').rglob('*.txt')):
        path=p.as_posix();body=p.read_text();md=cat[path];domain=domain_for(p)
        md['domaine_textes']=domain
        declared=re.search(r'\[PORTEE:\s*([^]]+)\]',body)
        scopes=[x.strip() for x in declared.group(1).split(',')] if declared else md.get('examens',[])
        refs=list(dict.fromkeys(re.findall(r'https?://[^\s<>]+',body)))
        records.append({'path':path,'title':md['title'],'domaine':domain,'publics_explicites':scopes,
                        'sources':refs,'statut':md.get('statut','non_renseigne'),
                        'recherche_active':md.get('retrieval_enabled',True),
                        'remplace_par':md.get('remplace_par'),
                        'controle_a_poursuivre':not refs or 'non_revalidee' in md.get('statut','') or 'a_poursuivre' in md.get('statut','')})
    catalogue_path.write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
    Path('config/classement_textes.json').write_text(json.dumps({'date':'2026-10-18','regle':'Classement éditorial : ne certifie pas le fond juridique. Les publics non explicités ne sont pas inférés.','domaines':DOMAINS,'fiches':records},ensure_ascii=False,indent=2)+'\n')
    out=['# Index ordonné des fiches Textes', '', f'{len(records)} fiches classées. Les chemins restent stables pour conserver les liens et les tests. Le classement ne vaut pas revalidation juridique.', '', 'Les anciennes synthèses peuvent rester incomplètes. Une source explicite et son applicabilité doivent être contrôlées avant toute affirmation. Les priorités sont détaillées dans audit_textes_2026_10_18.md.', '']
    for key,label in DOMAINS.items():
        group=[r for r in records if r['domaine']==key]
        out += [f'## {label} ({len(group)})','', '| Fiche | Public explicite | Sources liées | Suivi |','|---|---|---:|---|']
        for r in group:
            status='Doublon écarté de la recherche' if not r['recherche_active'] else ('Relecture à poursuivre' if r['controle_a_poursuivre'] else 'Références présentes ; statut détaillé au catalogue')
            out.append(f"| [{r['title']}](../{r['path']}) | {', '.join(r['publics_explicites']) or 'Non balisé'} | {len(r['sources'])} | {status} |")
        out.append('')
    Path('docs/index_fiches_textes.md').write_text('\n'.join(out)+'\n')
    return records

if __name__=='__main__':
    records=build();print(len(records),'fiches classées dans',len(DOMAINS),'domaines')
