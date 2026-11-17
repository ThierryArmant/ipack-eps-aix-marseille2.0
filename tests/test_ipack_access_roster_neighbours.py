"""Accès multi-établissements et liste élèves : procédures voisines, sans IA distante."""
import unittest
import knowledge_catalog as kc
from documentary_review import context_document_mismatch, mark_excerpt, review_exam_answer
import test_documentation as routing
from test_documentary_review import FakeLLM
from pathlib import Path

MULTI='data/ipack/fiches/ipack_222_situation_enseignants_tzr_ou_partages_multi_etablissements.txt'
ORS='data/textes/complement_obligations_service_eps.txt'
ROSTER='data/ipack/situations_2026_10_17/eleve_absent_liste_ajout.txt'

class AccessRosterNeighbours(unittest.TestCase):
    def setUp(self):
        self.h=routing.DocumentationTests();self.h.setUp()
    def route(self,q,public='Lycée Pro / CAP',mode='ipack'):
        return self.h.route(q,public,mode)[0]
    def test_lost_access_without_software_name_is_not_service_rule(self):
        for q in ['Deux établissements (LP et LGT) : je n’ai plus accès au LGT, seulement au LP. Pourquoi ?',
                  'Je travaille sur plusieurs collèges et mon accès au second est bloqué.',
                  'Mon autre lycée n’est plus accessible : j’ai perdu mon accès à cet établissement.']:
            with self.subTest(q=q):
                text=self.route(q)
                self.assertIn(MULTI,text)
                self.assertNotIn(ORS,text)
                self.assertIn('Changer d’Établissement',text)
        self.assertIn(ORS,self.route('Service partagé dans deux établissements : ai-je une heure de réduction ?', mode='textes'))
    def test_access_filter_removes_vector_service_source_before_llm(self):
        q='Mon accès au second lycée est bloqué : je peux encore entrer dans le premier.'
        wrong=mark_excerpt(Path(ORS).read_text(),path=ORS,title='Obligations de service')
        right=mark_excerpt(Path(MULTI).read_text(),path=MULTI,title='Accès multi-établissements')
        llm=FakeLLM([{'claims':[]}]);audit={}
        review_exam_answer(llm,question=q,public='Lycée Pro / CAP',mode='ipack',documents=wrong+'\n'+right,audit=audit)
        self.assertIn('D1',audit['excluded_situation_documents'])
        self.assertNotIn('D2',audit['excluded_situation_documents'])
        self.assertFalse(context_document_mismatch(q+' Mes ORS changent-elles aussi ?', 'Lycée Pro / CAP','ipack',{'path':ORS,'title':'Obligations de service'}))
    def test_roster_covers_departures_as_well_as_arrivals(self):
        for q in ['Des élèves ont quitté le lycée et de nouveaux sont arrivés : comment mettre à jour la base élèves ?',
                  'Des élèves partis restent dans le listing iPackEPS : comment actualiser ?',
                  'Comment ajouter un élève arrivé dans ma classe ?']:
            with self.subTest(q=q):
                text=self.route(q,'Lycée Général & Techno')
                self.assertIn(ROSTER,text)
                self.assertIn('Pour les départs',text)
                self.assertIn('[Importer]',text)
                self.assertIn('ne décrit pas le mécanisme de suppression',text)
                self.assertNotIn('cyclades_candidats_absents.txt',text)
    def test_exam_departure_keeps_its_own_circuit(self):
        paths=[p for p,_ in kc.reference_notice({'gt'},'Un élève a quitté le lycée : le retirer du lot Santorin ?', 'Lycée Général & Techno')]
        self.assertNotIn(ROSTER,paths)
    def test_article18_does_not_give_two_current_button_names(self):
        text=Path('data/ipack/fiches/ipack_065_article_18_dossiers_dossiereps_eleves_placement_des_eleves_dans_les_groupes.txt').read_text()
        self.assertNotIn('menu [importation élèves] => [Actualiser]',text)
        self.assertIn('menu [Importation des Élèves] => [Importer]',text)

class SssUploadNotEsterel(unittest.TestCase):
    def test_sss_upload_error_keeps_sss_reference_without_esterel_priority(self):
        questions = [
            "J'ai le message problème de téléchargement à chaque tentative, je n'arrive pas à publier l'acte de reconduction de ma section sportive football",
            "Impossible de déposer le fichier de reconduction SSS dans iPackEPS",
            "Je ne peux pas envoyer le document de reconduction de ma section sportive",
        ]
        for question in questions:
            with self.subTest(question=question):
                paths = [p for p, _ in kc.reference_notice(set(), question, 'Collège (DNB)')]
                self.assertNotIn('data/ipack/acces_ipackeps_problemes.txt', paths)
                self.assertIn('data/ipack/fiches/ipack_083_article_94_dossiers_dossier_sss_evolution_demande_de_reconduction_ou_fermeture_d_une_sss.txt', paths)
                self.assertEqual(kc.documented_response(question, 'Collège (DNB)', 'ipack')[0], '')

    def test_genuine_esterel_access_problem_keeps_its_reference(self):
        paths = [p for p, _ in kc.reference_notice(set(), "Je n'arrive pas à accéder à iPackEPS depuis ESTEREL", 'Collège (DNB)')]
        self.assertIn('data/ipack/acces_ipackeps_problemes.txt', paths)

class ExamAbsenceNotDailyAttendance(unittest.TestCase):
    def test_demissionnaire_absent_three_trimesters_not_pronote(self):
        q = 'pour un élève démissionnaire il faudra remplir absent sur les 3 trimestres sur ipackeps ?'
        paths = [p for p, _ in kc.reference_notice({'gt'}, q, 'Lycée Général & Techno')]
        self.assertNotIn('data/commun/audit60/ipack_absences.txt', paths)

    def test_daily_attendance_still_uses_life_school_source(self):
        q = 'Comment faire l’appel et saisir les absences de cours en EPS ?'
        paths = [p for p, _ in kc.reference_notice(set(), q, 'Collège (DNB)')]
        self.assertIn('data/commun/audit60/ipack_absences.txt', paths)


class MiniDocumentCandidateCoverage(unittest.TestCase):
    def test_exclusive_priority_does_not_hide_other_candidates_in_ipack(self):
        import tempfile
        from unittest.mock import patch
        import document_retrieval as dr

        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', suffix='.txt') as fiche:
            fiche.write('Fiche prioritaire : appel et absence de cours')
            fiche.flush()
            def notices(*args):
                return [(fiche.name, {
                    'title': 'Appel quotidien', 'statut': 'verifie',
                    'priorite': 400, 'exclusif_motifs': ['absen']})]
            def by_words(base, query, limit):
                return ['[DOCUMENT: examen-test; statut: verifie] Fiche examens : candidat absent'] if base == 'santorin' else []
            with patch.object(dr, 'mark_excerpt', side_effect=lambda text, **kw: text), \
                 patch.object(dr, 'reference_url', return_value=''):
                result = dr.retrieve_documents(
                    prompt='Élève absent : statut sur trois trimestres dans iPackEPS ?',
                    p_norm='eleve absent statut sur trois trimestres dans ipackeps',
                    p_low='eleve absent statut sur trois trimestres dans ipackeps',
                    niveau_actuel_form='Lycée Général & Techno', mode='ipack',
                    est_college=False, est_clairement_lycee=True,
                    mots_cles_intention_peda=[], recherche_mots=None,
                    chercher_par_mots=by_words, retriever_textes=None,
                    retriever_peda=None, retriever_santorin=None,
                    retriever_ipack=None, libelle_source=lambda *a: '',
                    _url_source=lambda *a: '', reference_notice=notices)
            self.assertIn('appel et absence de cours', result[0])
            self.assertIn('Fiche examens : candidat absent', result[0])

    def test_exclusive_priority_remains_for_textes_mode(self):
        import tempfile
        from unittest.mock import patch
        import document_retrieval as dr

        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', suffix='.txt') as fiche:
            fiche.write('Fiche exclusive')
            fiche.flush()
            with patch.object(dr, 'mark_excerpt', side_effect=lambda text, **kw: text), \
                 patch.object(dr, 'reference_url', return_value=''):
                result = dr.retrieve_documents(
                    prompt='absence', p_norm='absence', p_low='absence',
                    niveau_actuel_form='Lycée Général & Techno', mode='textes',
                    est_college=False, est_clairement_lycee=True,
                    mots_cles_intention_peda=[], recherche_mots=None,
                    chercher_par_mots=lambda *a: [], retriever_textes=None,
                    retriever_peda=None, retriever_santorin=None,
                    retriever_ipack=None, libelle_source=lambda *a: '',
                    _url_source=lambda *a: '',
                    reference_notice=lambda *a: [(fiche.name, {
                        'title': 'Fiche exclusive', 'statut': 'verifie',
                        'priorite': 400, 'exclusif_motifs': ['absen']})])
            self.assertIn('Fiche exclusive', result[0])
