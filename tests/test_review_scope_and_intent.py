import unittest
import knowledge_catalog as kc
from documentary_review import render_claims, situation_mismatch


class ScopeIntentTests(unittest.TestCase):
    def test_scope_notice_once_without_turning_national_rule_local(self):
        local = {'document_id': 'D1', 'scope': {'academy': 'Aix-Marseille', 'not_confirmed_for': 'Versailles'}}
        national = {'document_id': 'D2', 'scope': {'level': 'reglementaire'}}
        claims = [{'section': 'etape', 'text': t, 'evidence': [local]} for t in ('Faire valider le dossier.', 'Transmettre les pièces.')]
        claims.append({'section': 'condition', 'text': 'La règle nationale demeure applicable.', 'evidence': [national]})
        ps = [{'id': 'D1', 'title': 'Guide local', 'display_level': 'academique'},
              {'id': 'D2', 'title': 'Texte national', 'display_level': 'reglementaire'}]
        result = render_claims(claims, ps).split('<details>')[0]
        self.assertEqual(result.count('Aix-Marseille'), 1)
        self.assertEqual(result.count('Versailles'), 1)
        self.assertIn('ne sont pas confirmées', result)
        self.assertIn('La règle nationale demeure applicable.', result)
        self.assertNotIn('À Aix-Marseille,', result)

    def test_ordinary_project_does_not_become_sss(self):
        q = 'Où retrouver le bilan du projet pédagogique de l’année précédente ?'
        self.assertTrue(situation_mismatch(q, '[Dossier SSS] > [Projet annuel]'))
        self.assertFalse(situation_mismatch(q, 'Axes des projets EPS, AS et SSS'))
        self.assertFalse(situation_mismatch('Où retrouver le projet SSS ?', '[Dossier SSS] > [Projet annuel]'))

    def test_participation_question_is_not_an_individual_medical_grade(self):
        self.assertEqual(kc.clarification('Un candidat dispensé peut-il passer une épreuve facultative au CAP ?', 'Lycée Pro / CAP'), '')
        self.assertTrue(kc.clarification('Pour un candidat dispensé au CAP, quelle note dois-je mettre ?', 'Lycée Pro / CAP'))

    def test_national_session_spreading_found_without_medical_keyword(self):
        context = kc.priority_context('Comment sont gérés les candidats en étalement de session ?', 'Lycée Général & Techno', 'examens')
        self.assertIn('première session', context)
        self.assertIn('handicap', context)

    def test_current_rights_and_correct_project_document_retrieved(self):
        current = kc.priority_context('Qui peut modifier la liste des professeurs de l’équipe EPS ?', 'Lycée Général & Techno', 'ipack')
        self.assertIn('Tous les enseignants', current)
        project = kc.priority_context('Retrouver le bilan du projet pédagogique de l’année précédente', 'Collège (DNB)', 'ipack')
        self.assertIn('Configuration des Axes des Projets', project)

    def test_commercial_source_and_cap_scope(self):
        commercial = kc.priority_context('Peut-on imposer une marque pour la tenue achetée par les familles ?', 'Collège (DNB)', 'textes')
        self.assertIn('MENE2219098C', commercial)
        cap = kc.priority_context('Un candidat CAP dispensé peut-il passer une épreuve facultative EPS ?', 'Lycée Pro / CAP', 'examens')
        self.assertIn('ne prévoit pas', cap)
        self.assertIn('mobilité', cap)
