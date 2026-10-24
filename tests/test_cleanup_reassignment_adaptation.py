"""Régressions des traces Q2/Q6/Q7 ; vrai routage et preuves, aucun appel IA."""
import unittest
from pathlib import Path
from types import SimpleNamespace
import knowledge_catalog as kc
from documentary_review import source_packets,mark_excerpt
import test_documentation as documentation

TARGET='data/commun/audit60/gt_inaptitude_demarche.txt'
QUESTIONS=["Comment gérer le cas d'un protocole adapté en cours d'année scolaire si l'élève doit changer de protocole ?", "Que faire si le protocole adapté a été anticipé avant le retour à la commission académique ?"]

class CleanupReassignmentAdaptationTests(unittest.TestCase):
    def test_replacement_is_not_the_only_reason_in_the_old_copy(self):
        path='data/ipack/complement_cyclades_cas_pratiques.txt'
        text=Path(path).read_text()
        self.assertNotIn("Cette étape n'est nécessaire que si",text)
        self.assertIn("une adresse erronée ou un protocole saisi au nom d'un collègue",text)
        self.assertIn("chef d'établissement",text)
    def test_both_trace_questions_get_complete_scope_in_textes_even_with_noisy_results(self):
        helper=documentation.DocumentationTests();helper.setUp()
        irrelevant=SimpleNamespace(text='AMEX et Incluscol : demande générale, délai de décision.',metadata={'source':'bruit.txt','path':'bruit.txt'})
        for q in QUESTIONS:
            with self.subTest(question=q):
                text,_,_,_=helper.route(q,'Lycée Général & Techno','textes',docs=[irrelevant])
                packets=source_packets(text)
                self.assertIn(TARGET,[p['path']for p in packets])
                self.assertNotIn('bruit.txt',[p['path']for p in packets])
                sent='\n'.join(s['text']for p in packets for s in p['passages'])
                self.assertIn('inaptitude partielle permanente',sent)
                self.assertIn('inaptitude partielle temporaire',sent)
                self.assertIn('pour information',sent)
                self.assertIn('ne constitue pas une décision',sent)
                self.assertIn('ne permet pas de prescrire ce dossier',sent)
    def test_same_branch_source_is_reachable_in_all_three_tabs(self):
        title=kc.catalog()[TARGET]['title']
        for mode in ['textes','examens','ipack']:
            for q in QUESTIONS:
                self.assertIn(title,kc.priority_titles(q,'Lycée Général & Techno',mode))
    def test_diploma_speciality_and_administrative_request_keep_their_own_routes(self):
        title=kc.catalog()[TARGET]['title']
        for public,q in [('Lycée Pro / CAP','CAP : protocole adapté en cours d’année'),('Collège (DNB)','DNB : protocole adapté en cours d’année'),('Lycée Général & Techno','SHN : protocole adapté en cours d’année'),('Lycée Général & Techno','EPPCS : protocole adapté en cours d’année')]:
            self.assertNotIn(title,kc.priority_titles(q,public,'textes'))
        administrative=kc.priority_titles('PAP : demande d’aménagement d’examen sur AMEX','Lycée Général & Techno','textes')
        self.assertIn('Aix-Marseille : aménagements d’examen 2027',administrative)
        self.assertNotIn(title,administrative)
