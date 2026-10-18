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
        result = render_claims(claims, ps).split('<details')[0]
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

    def test_project_search_asks_only_for_the_missing_type(self):
        result = kc.clarification('Retrouver un ancien projet pédagogique et son bilan', 'Collège (DNB)')
        self.assertIn('Quel type de projet', result)
        self.assertNotIn('[Dossier SSS]', result)
        self.assertEqual(kc.clarification('Consulter le projet EPS archivé', 'Collège (DNB)'), '')
        self.assertEqual(kc.clarification('Consulter le bilan du projet de section sportive', 'Collège (DNB)'), '')

    def test_participation_question_is_not_an_individual_medical_grade(self):
        self.assertEqual(kc.clarification('Un candidat dispensé peut-il passer une épreuve facultative au CAP ?', 'Lycée Pro / CAP'), '')
        self.assertTrue(kc.clarification('Pour un candidat dispensé au CAP, quelle note dois-je mettre ?', 'Lycée Pro / CAP'))

    def test_national_session_spreading_found_without_medical_keyword(self):
        context = kc.priority_context('Étalement sur plusieurs sessions — suivi des épreuves', 'Lycée Général & Techno', 'examens')
        self.assertIn('sans décision finale', context)
        self.assertIn('le jury attend', context)
        self.assertNotIn('peuvent demander un étalement', context)
        self.assertIn('handicap', context)

    def test_initial_request_and_conservation_keep_their_document(self):
        for question in ('Comment demander un étalement des épreuves au titre du handicap ?',
                         'Conservation de notes après échec et étalement des sessions handicap'):
            context = kc.priority_context(question, 'Lycée Général & Techno', 'examens')
            self.assertIn('La demande précède la première session', context)
            self.assertIn('conservation de notes après un échec', context)

    def test_current_rights_and_correct_project_document_retrieved(self):
        current = kc.priority_context('Droits d’actualisation — équipe EPS', 'Lycée Général & Techno', 'ipack')
        self.assertIn('Tous les enseignants', current)
        self.assertIn("ne signifie pas créer librement un compte enseignant", current)
        self.assertNotIn("portail ESTEREL", current)
        project = kc.priority_context('Projet EPS — configuration des axes', 'Collège (DNB)', 'ipack')
        self.assertIn('Configuration des Axes des Projets', project)

    def test_commercial_source_and_cap_scope(self):
        commercial = kc.priority_context('Neutralité commerciale — achat de matériel de marque', 'Collège (DNB)', 'textes')
        self.assertIn('MENE2219098C', commercial)
        cap = kc.priority_context('CAP — unité facultative EPS', 'Lycée Pro / CAP', 'examens')
        self.assertIn('ne prévoit pas', cap)
        self.assertIn('mobilité', cap)


class ExplicitScopeNoticeTests(unittest.TestCase):
    def test_used_source_scope_cannot_be_omitted_by_generation(self):
        path = 'data/examens/amenagements_aix_2026_10_13/handicap_etalement_suivi_gt.txt'
        packets = [{'id': 'D1', 'title': 'Suivi', 'path': path}]
        claim = {'section': 'decision', 'text': 'Le jury attend la fin des épreuves.',
                 'evidence': [{'document_id': 'D1', 'scope': {'level': 'synthese_reglementaire'}}]}
        result = render_claims([claim], packets)
        self.assertIn('Cadre traité', result)
        self.assertIn('handicap', result)
        self.assertEqual(result.count('Cadre traité'), 1)
        self.assertNotIn('Cadre traité', render_claims([], packets))

    def test_team_refresh_frame_shown_even_if_model_says_modify(self):
        path = 'data/ipack/fiches/equipe_eps_actualisation_logiciel.txt'
        packets = [{'id': 'D1', 'title': 'Équipe', 'path': path}]
        claim = {'section': 'decision', 'text': "Tous les enseignants peuvent modifier la liste de l'équipe EPS.",
                 'evidence': [{'document_id': 'D1', 'scope': {'level': 'documentation_logiciel'}}]}
        result = render_claims([claim], packets)
        self.assertIn('Cadre traité', result)
        self.assertIn('actualiser', result)
        self.assertIn('bases administratives', result)
