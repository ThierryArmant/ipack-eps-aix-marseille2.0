import json
import unittest
from pathlib import Path
from unittest.mock import patch

from documentary_review import mark_excerpt, source_packets, validate_claims, render_claims
from source_scope import select_academy, attributed_segments

CLOSURE='data/examens/audit_lot3_2026_10_12/fermeture_collective.txt'
ABSENCE='data/examens/audit_lot2_2026_10_12/absence_injustifiee_gt.txt'
SHN='data/examens/audit_faq_2026_10_12/k4_procedure_verifiee.txt'


def packets(path):
    return source_packets(mark_excerpt(Path(path).read_text(), path=path))


def answer_for(packet, span):
    claim={'section':'decision','text':span['text'],
           'evidence':[{'document_id':packet['id'],'passage_ids':[span['id']], 'level':'academique'}]}
    accepted, errors=validate_claims({'claims':[claim]}, [packet])
    if errors:
        raise AssertionError(errors)
    return render_claims(accepted, [packet])


class PassageAttributionTests(unittest.TestCase):
    def test_every_annotation_is_exact_unique_and_non_overlapping(self):
        registry=json.loads(Path('config/nature_passages.json').read_text())['fichiers']
        for path, record in registry.items():
            body=Path(path).read_text()
            positions=[]
            for entry in record['passages']:
                self.assertEqual(body.count(entry['texte']),1,(path,entry))
                self.assertTrue(entry['reference'])
                start=body.index(entry['texte'])
                positions.append((start,start+len(entry['texte'])))
            positions.sort()
            self.assertTrue(all(a[1]<=b[0] for a,b in zip(positions,positions[1:])),path)

    def test_authorisation_and_santorin_buttons_have_different_sources(self):
        packet=select_academy(packets(CLOSURE),'Lyon')[0][0]
        national=next(s for s in packet['passages'] if 'Le recteur' in s['text'] or 'le recteur peut' in s['text'])
        software=next(s for s in packet['passages'] if 'Déclarer CE' in s['text'])
        a=answer_for(packet,national); b=answer_for(packet,software)
        self.assertIn('Synthèse d’un texte réglementaire',a)
        self.assertIn('MENE2531948N',a)
        self.assertNotIn('À Aix-Marseille,',a)
        self.assertNotIn('non confirmé pour Lyon',a)
        self.assertIn('Documentation du logiciel',b)
        for span in packet['passages']:
            self.assertEqual(span['text'],packet['text'][span['start']:span['end']])

    def test_zero_rule_separated_from_absent_software_code(self):
        packet=packets(ABSENCE)[0]
        national=next(s for s in packet['passages'] if 'entraîne zéro' in s['text'])
        software=next(s for s in packet['passages'] if 'code de saisie' in s['text'])
        self.assertEqual(national['scope']['nature'],['texte_national'])
        self.assertEqual(software['scope']['nature'],['logiciel'])

    def test_shn_local_role_national_eligibility_and_software_are_separate(self):
        packet=select_academy(packets(SHN),'Lyon')[0][0]
        local=next(s for s in packet['passages'] if s['text'].startswith('2.'))
        national=next(s for s in packet['passages'] if s['text'].startswith('Rappel'))
        software=next(s for s in packet['passages'] if s['text'].startswith('3.'))
        self.assertEqual(local['scope']['not_confirmed_for'],'Lyon')
        self.assertNotIn('not_confirmed_for',national['scope'])
        self.assertNotIn('not_confirmed_for',software['scope'])
        self.assertIn('À Aix-Marseille,',answer_for(packet,local))

    def test_stale_annotation_never_falls_back_to_false_single_source(self):
        body='Le contenu de la fiche a été modifié.'
        span={'text':body,'start':0,'end':len(body),'scope':{'nature':['consigne_academique'],'academy':'Aix-Marseille'}}
        with patch('source_scope._registry',return_value={'test.txt':{
            'nature_non_attribuee':['texte_national','logiciel'],
            'passages':[{'texte':'Ancien contenu absent','nature':['texte_national'],'reference':'Référence'}]}}):
            result=attributed_segments('test.txt',body,[span])
        self.assertEqual(result[0]['scope']['status'],'passage_non_attribue')
        self.assertEqual(result[0]['scope']['level'],'mixte')
