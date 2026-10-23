import unittest
from pathlib import Path
from documentary_review import source_packets, mark_excerpt
from source_scope import select_academy

class OperationEvidenceBoundaries(unittest.TestCase):
    def packets(self, path):
        return select_academy(source_packets(mark_excerpt(Path(path).read_text(),path=path)), 'Non précisée')[0]

    def test_association_has_software_evidence_without_mission_path(self):
        packets=self.packets('data/examens/fiches/correspondant_04_cyclades_santorin_imagin.txt')
        spans=[s for p in packets for s in p['passages'] if 'Association manuelle — acteur' in s['text']]
        self.assertEqual(len(spans),1)
        self.assertEqual(spans[0]['scope']['nature'],['logiciel'])
        self.assertIn('[Associer les élèves à un protocole]',spans[0]['text'])
        self.assertNotIn('Portail des missions',spans[0]['text'])

    def test_protocol_and_lot_moves_are_separate_documents(self):
        from test_documentation import app_functions
        path='data/examens/tutoriels_creteil_cyclades_santorin.txt'
        chunks=app_functions()['decouper_en_fiches'](Path(path).read_text())
        packets=[]
        for chunk in chunks:
            packets.extend(select_academy(source_packets(mark_excerpt(chunk,path=path,title=chunk.splitlines()[0])), 'Non précisée')[0])
        protocol=next(p for p in packets if 'CHANGER LE PROTOCOLE' in p['title'])
        lot=next(p for p in packets if "D'UN LOT À UN AUTRE" in p['title'])
        self.assertNotEqual(protocol['title'],lot['title'])
        step=next(s for s in protocol['passages'] if s['text'].startswith('Procédure décrite'))
        self.assertEqual(step['scope']['nature'],['logiciel'])
        self.assertIn("sans sortir l'élève de son lot",step['text'])
        self.assertNotIn('[Distribution]',step['text'])
        self.assertIn('[Distribution]',lot['text'])
