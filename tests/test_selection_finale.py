"""La sélection finale conserve les sources ciblées et écarte les voisins incompatibles.

Sondes publiques nouvelles, modèle simulé, aucune génération payante.
"""
import unittest
from pathlib import Path
from documentary_review import mark_excerpt, review_exam_answer, source_packets, selection_subject
from test_documentary_review import FakeLLM
import test_documentation as routing_tests

class FinalSelectionTests(unittest.TestCase):
    def selected(self, question, docs, public='Lycée Général & Techno', mode='examens'):
        audit = {}
        llm = FakeLLM([{'claims': []}])
        review_exam_answer(llm, question=question, public=public, documents=docs,
                           audit=audit, mode=mode)
        return [p for p in audit['documents'] if p['id'] in audit.get('model_document_ids', [])]

    def test_catalogue_match_survives_numeric_focus(self):
        docs = mark_excerpt('Compléter la fiche professeur.', title='Première connexion', priority=300)
        docs += '\n\n' + mark_excerpt('Choisir un établissement dans le sélecteur.', title='Bascule multi-établissements',
                             priority=280, selection='catalogue')
        selected = self.selected('Où basculer vers mon autre lycée ?', docs, mode='ipack')
        self.assertTrue(any(p['title']=='Bascule multi-établissements' for p in selected))

    def test_catalogue_below_300_focuses_without_neighbor_noise(self):
        docs = mark_excerpt('Choisir un établissement.', title='Multi-établissements', priority=280, selection='catalogue')
        docs += '\n\n' + mark_excerpt('Déposer une FCA.', title='Référentiels et FCA')
        selected = self.selected('Où choisir mon autre lycée ?', docs, mode='ipack')
        self.assertEqual([p['title'] for p in selected], ['Multi-établissements'])

    def test_vector_priority_alone_does_not_claim_catalogue_match(self):
        docs = mark_excerpt('La mission donne accès aux lots.', title='Accès aux lots', priority=300)
        docs += '\n\n' + mark_excerpt('Les unités facultatives sont distinctes.', title='CAP : distinction avec le bac professionnel', priority=280)
        selected = self.selected("Je cherche mes lots CAP. Distingue les sources nationales et les consignes académiques.", docs)
        self.assertEqual([p['title'] for p in selected], ['Accès aux lots'])

    def test_editorial_request_is_not_a_topic(self):
        q = 'Mes lots ne sont pas tous visibles. Distingue le texte national et le fonctionnement du logiciel.'
        self.assertEqual(selection_subject(q), 'Mes lots ne sont pas tous visibles.')
        self.assertEqual(selection_subject('Distinguer deux protocoles dans Cyclades ?'), 'Distinguer deux protocoles dans Cyclades ?')

    def test_compatible_complement_remains_available(self):
        docs = mark_excerpt('La mission doit être créée.', title='Mission du correcteur', priority=300)
        docs += '\n\n' + mark_excerpt('L’export des notes permet une vérification.', title='Exporter les notes', priority=0)
        selected = self.selected('Comment exporter les notes après la création de la mission ?', docs)
        self.assertEqual(len(selected), 2)

    def test_unlabelled_lycee_fragment_is_excluded_for_dnb(self):
        docs = mark_excerpt('Les moyennes du DNB sont saisies dans le LSU.', title='DNB : LSU', scopes=['dnb'])
        docs += '\n\n' + mark_excerpt('Santorin : saisir DI sur une APSA du CCF et conserver les deux autres notes.',
                             path='guide/cas_mixtes.txt', title='Passage documentaire')
        selected = self.selected('Brevet : où renseigner la moyenne annuelle ?', docs, public='Collège (DNB)')
        self.assertEqual([p['title'] for p in selected], ['DNB : LSU'])

    def test_dnb_explanation_can_mention_santorin_and_absence_of_ccf(self):
        docs = mark_excerpt('Au DNB, pas de CCF : les moyennes sont dans le LSU, Santorin sert à l’harmonisation.', title='Circuit du brevet', scopes=['dnb'])
        self.assertEqual(len(self.selected('DNB : rôle de Santorin ?', docs, public='Collège (DNB)')), 1)

    def test_explicit_scopes_survive_packet_identity(self):
        packets = source_packets(mark_excerpt('Texte de procédure.', title='Procédure', scopes=['gt'], selection='catalogue'))
        self.assertEqual(packets[0]['scopes'], ['gt'])
        self.assertEqual(packets[0]['selection'], 'catalogue')

    def test_catalogue_triggers_and_final_payload(self):
        route = routing_tests.DocumentationTests(); route.setUp()
        probes = [
            ("Je suis TZR dans deux établissements iPackEPS, où basculer ?", 'ipack_222', 'equipe_eps_actualiser_tzr'),
            ("TZR : mon nom ne paraît pas dans l’équipe EPS", 'equipe_eps_actualiser_tzr', 'ipack_222'),
            ("Première connexion iPackEPS : dans quel ordre avancer ?", 'ordre_premiere_connexion', 'ipack_212'),
            ("Dans quel ordre remplir les dossiers iPackEPS ?", 'ordre_premiere_connexion', 'ipack_212'),
            ("iPackEPS : comment commencer un protocole adapté pour un handicap ?", 'ipack_212', 'ordre_premiere_connexion'),
            ("iPackEPS : créer un contrôle adapté pour un candidat blessé", 'ipack_212', 'ordre_premiere_connexion'),
        ]
        for question, expected, excluded in probes:
            with self.subTest(question=question):
                docs, _, _, _ = route.route(question, 'Lycée Général & Techno', 'ipack')
                paths = [p['path'] for p in self.selected(question, docs, mode='ipack')]
                self.assertTrue(any(expected in p for p in paths), paths)
                self.assertFalse(any(excluded in p for p in paths), paths)

    def test_plain_inaptitude_is_not_an_adaptation_trigger(self):
        route = routing_tests.DocumentationTests(); route.setUp()
        docs, _, _, _ = route.route('iPackEPS : comment déclarer une inaptitude ?', 'Lycée Général & Techno', 'ipack')
        self.assertNotIn('ipack_212', docs)

    def test_single_note_does_not_select_two_note_procedure(self):
        docs = mark_excerpt('Avec deux notes, conserver les résultats des deux activités.', title='Deux notes')
        self.assertEqual(self.selected('Bac GT : une seule note et deux DI, que transmettre ?', docs), [])

    def test_loader_preserves_fragment_title(self):
        route = routing_tests.DocumentationTests(); route.setUp()
        docs = route.env['charger_dossier_txt_securise']('data/examens', par_fiche=True)
        fragments = [d for d in docs if 'cas_concrets_lots_inaptes_coevaluation_etranger' in d.metadata['path']]
        self.assertTrue(fragments)
        self.assertTrue(all(d.metadata['title'] and d.metadata['title'] in d.text for d in fragments))

if __name__ == '__main__':
    unittest.main()
