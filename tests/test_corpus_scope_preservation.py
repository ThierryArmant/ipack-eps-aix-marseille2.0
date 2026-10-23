"""Vraies sources et vrai découpage, aucun modèle simulant une interprétation."""
import unittest
from pathlib import Path
from documentary_review import source_packets,mark_excerpt,compact_model_packet
from scripts.audit_corpus_offline import audit

class CorpusScopePreservationTests(unittest.TestCase):
    def test_every_scope_line_survives_into_model_proofs(self):
        from knowledge_catalog import active_paths
        checked=0
        for folder in ('data/ipack','data/examens'):
            for path in active_paths(folder):
                text=path.read_text()
                limits=[line for line in text.splitlines() if line.startswith('Portée :')]
                if not limits:continue
                checked+=1
                packets=source_packets(mark_excerpt(text,path=str(path)))
                sent='\n'.join(s['text'] for p in packets for s in compact_model_packet(p)['passages'])
                for line in limits:
                    with self.subTest(path=str(path),line=line):self.assertIn(line,sent)
        self.assertGreater(checked,50)
    def test_restriction_of_aflp_is_available_in_real_source(self):
        path='data/ipack/fiches/ipack_164_situation_santorin_cases_aflp_inactives_impossible_de_saisir.txt'
        text=Path(path).read_text()
        sent='\n'.join(s['text'] for p in source_packets(mark_excerpt(text,path=path)) for s in compact_model_packet(p)['passages'])
        self.assertIn('bac professionnel et CAP uniquement',sent)
        self.assertIn('ne pas appliquer ce bouton au bac GT',sent)
    def test_offline_audit_has_no_mechanical_failure(self):
        result=audit()
        self.assertEqual(result['fichiers_avec_erreur_mecanique'],0,[r for r in result['details'] if r['erreurs_mecaniques']])
