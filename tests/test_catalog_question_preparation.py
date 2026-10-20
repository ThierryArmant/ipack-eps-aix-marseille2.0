"""Une question se prépare une fois, quel que soit le nombre de documents."""
import unittest
from unittest.mock import patch
import knowledge_catalog as kc

class CataloguePreparation(unittest.TestCase):
    def test_enrichment_once_and_same_sessions_exclusions_and_order(self):
        entries={
            'recent.txt':{'prioritaire':True,'priorite':300,'examens':['gt'],'motifs':['ccf'],'sessions':['2026']},
            'old.txt':{'prioritaire':True,'examens':['gt'],'motifs':['ccf'],'sessions':['2025']},
            'excluded.txt':{'prioritaire':True,'motifs':['ccf'],'exclure_motifs':['college']},
            'general.txt':{'prioritaire':True,'priorite':50,'motifs':['ccf']},
        }
        with patch.object(kc,'catalog',return_value=entries),patch.object(kc,'enrich',wraps=kc.enrich) as enrich:
            selected=kc.reference_notice({'gt'},'CCF session 2026','Collège (DNB)')
        self.assertEqual(enrich.call_count,1)
        self.assertEqual([p for p,_ in selected],['recent.txt','general.txt'])
    def test_no_question_does_not_enrich_and_keeps_available_entries(self):
        with patch.object(kc,'catalog',return_value={'guide':{'prioritaire':True}}),patch.object(kc,'enrich') as enrich:
            selected=kc.reference_notice({'gt'})
        enrich.assert_not_called();self.assertEqual([p for p,_ in selected],['guide'])
    def test_staff_question_still_excludes_dnb(self):
        entries={p:{'prioritaire':True,'motifs':['tzr']} for p in ['data/commun/dnb/01_controle_continu_calcul.txt','service.txt']}
        with patch.object(kc,'catalog',return_value=entries):
            self.assertEqual([p for p,_ in kc.reference_notice({'gt'},'Service TZR : mes heures ?','Lycée Général & Techno')],['service.txt'])
