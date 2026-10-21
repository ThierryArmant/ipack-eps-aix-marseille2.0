import unittest
from guide_request import requests_guide
class RequestTests(unittest.TestCase):
    def test_generic_help(self):
        for q in ['aide moi sui sperdu', 'aide moi je sui perdu', 'je suis perud', 'aid emoi', 'aide moi je suis perdu', 'Je suis perdue dans iPackEPS', 'Je ne sais pas par où commencer', 'aidez-moi svp', 'aide-moi']:
            for p in ['Collège','Lycée Général & Techno','Lycée Pro / CAP']:
                self.assertTrue(requests_guide(q,'ipack',p),q)
    def test_concrete_or_other_context(self):
        for q in ['je suis perdu dans les groupes', 'aide moi pour les classes', 'J’ai perdu mes classes', 'je suis perdu comment importer mes élèves', 'Qui modifie la liste des enseignants ?', 'ma vidéo est perdue']:
            self.assertFalse(requests_guide(q,'ipack','Collège'),q)
        for mode in ['textes','examens']:
            self.assertFalse(requests_guide('aide moi je suis perdu',mode,'Collège'))
        self.assertFalse(requests_guide('je suis perdu','ipack','1er degré'))


class VagueRequestTests(unittest.TestCase):
    def test_demande_evasive_ouvre_le_guide(self):
        from guide_request import vague_request_opens_guide
        for q in ["J'enseigne le foot à mes 6eme4, comment renseigner ça ?",
                  "je ne sais pas comment remplir iPack pour déclarer l'activité foot avec ma classe"]:
            self.assertTrue(vague_request_opens_guide(q, 'ipack', 'Collège'), q)
            self.assertFalse(vague_request_opens_guide(q, 'examens', 'Collège'), q)
            self.assertFalse(vague_request_opens_guide(q, 'ipack', '1er degré'), q)
        for q in ["Comment créer une séquence de foot pour ma 6e4 dans les groupes ?",
                  "Où trouver la liste des APSA ?", "je ne trouve pas mon nouvel élève"]:
            self.assertFalse(vague_request_opens_guide(q, 'ipack', 'Collège'), q)

    def test_app_branche_le_guide_avant_toute_generation(self):
        from pathlib import Path
        src = Path('question_preflight.py').read_text(encoding='utf-8')
        self.assertIn('prepare_question(prompt, niveau_actuel_form, mode)', Path('app.py').read_text())
        self.assertIn('or vague_request_opens_guide(prompt, mode, niveau_actuel_form)', src)
        self.assertIn('demande_precision = GUIDE_MESSAGE if _guide_demande', src)
