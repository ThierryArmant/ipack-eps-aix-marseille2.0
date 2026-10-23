import unittest
from pathlib import Path
from documentary_review import source_packets,mark_excerpt
from document_selector import profile

class FCAAndLateDepositTests(unittest.TestCase):
    def test_academic_exception_precedes_establishment_deposit_and_is_separate(self):
        path='data/ipack/visite_lycee_2026_10_18/dossier_certificatif_lycee_gt.txt'
        text=Path(path).read_text()
        self.assertLess(text.index('Branche distincte — APSA'),text.index('Action — déposer'))
        spans=[s['text'] for p in source_packets(mark_excerpt(text,path=path)) for s in p['passages']]
        deposit=next(s for s in spans if s.startswith('Action — déposer'))
        self.assertIn("uniquement pour le référentiel d'établissement",deposit)
        summary=next(s for s in spans if s.startswith("Fiches certificatives d'activité"))
        self.assertIn("ne s'applique pas automatiquement",summary)
        card=profile({'id':'D1','title':'Dossier certificatif','text':text},'Déposer la FCA des APSA académiques')
        self.assertIn('académique',str(card))
    def test_late_deposit_has_explicit_limit_on_same_project_source(self):
        text=Path('data/ipack/situations_2026_10_17/projets_ou_les_trouver.txt').read_text()
        self.assertIn("un droit au dépôt tardif",text)
        self.assertIn("ne sont pas établis par cette fiche",text)
        self.assertIn("ne prouve pas un pouvoir de rouvrir",text)
    def test_project_navigation_does_not_include_sss_in_unqualified_file_deposit(self):
        text=Path('data/ipack/situations_2026_10_17/projets_ou_les_trouver.txt').read_text()
        direct=next(l for l in text.splitlines() if l.startswith('Réponse directe'))
        self.assertNotIn('[Projet SSS]',direct)
        self.assertIn("il n'y a pas de dépôt de fichier à cet endroit",text)
        self.assertIn('[Dossier Section Sportive Scolaire]',text)
