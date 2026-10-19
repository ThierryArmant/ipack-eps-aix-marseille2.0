import unittest
from pathlib import Path
import knowledge_catalog as kc
from documentary_review import mark_excerpt, review_exam_answer, packet_covered_by_focus, source_packets, situation_mismatch
from test_documentary_review import FakeLLM


class TraceContextSelectionTests(unittest.TestCase):
    def audit(self, question, public, mode, neighbors=''):
        targets = {'Lycée Pro / CAP': {'pro', 'cap'}, 'Lycée Général & Techno': {'gt'}, 'Collège (DNB)': {'dnb'}}[public]
        docs = []
        for path, md in kc.reference_notice(targets, question, public):
            if md.get('modes') and mode not in md['modes']:
                continue
            docs.append(mark_excerpt(Path(path).read_text(), path=path, title=md.get('title', ''),
                                     priority=md.get('priorite', 0), selection='catalogue'))
        audit = {}
        review_exam_answer(FakeLLM([{'claims': []}, {'claims': []}]), question=question,
                           public=public, documents='\n\n'.join(docs) + '\n\n' + neighbors, audit=audit)
        return audit

    def test_remplacant_groups_selects_transfer_without_santorin_mission(self):
        neighbor = mark_excerpt('La mission de notation Santorin est créée dans Imag’in.',
                                path='santorin.txt', title='Accès remplaçant Santorin')
        a = self.audit('Un collègue remplaçant arrive pour trois mois. Comment lui donner accès à mes groupes ?',
                       'Lycée Général & Techno', 'ipack', neighbor)
        paths = [d['path'] for d in a['documents'] if d['id'] in a['model_document_ids']]
        self.assertIn('data/ipack/visite_college_2026_10_18/remplacant_transfert_groupes.txt', paths)
        self.assertNotIn('santorin.txt', paths)

    def test_explicit_remplacant_exam_access_is_preserved(self):
        self.assertFalse(situation_mismatch('Je remplace un collègue : accès à ses groupes et lots Santorin ?',
                                            'Accès remplaçant Santorin'))

    def test_shn_not_medically_inapt_and_both_pro_diplomas_remain_distinct(self):
        q = "Comment noter un élève SHN qui n'a participé qu'à un seul cycle en raison de son statut ?"
        neighbor = mark_excerpt('La dispense médicale est justifiée par le certificat médical.',
                                path='inapt.txt', title='Élève inapte avec une seule note')
        a = self.audit(q, 'Lycée Pro / CAP', 'examens', neighbor)
        paths = [d['path'] for d in a['documents'] if d['id'] in a['model_document_ids']]
        self.assertIn('data/commun/pro_shn_ccf.txt', paths)
        self.assertIn('data/commun/cap_shn_ccf.txt', paths)
        self.assertNotIn('inapt.txt', paths)
        self.assertFalse(situation_mismatch(q + ' Il est également inapte médicalement.', 'Élève inapte avec une seule note'))

    def test_activite_etablissement_does_not_add_reduced_certification(self):
        neighbor = mark_excerpt('Une seule activité réalisable.', path='reduit.txt',
                                title='FAQ EPS — Certification réduite : une seule activité réalisable (bac GT)')
        a = self.audit("Peut-on proposer une activité établissement dans l'ensemble certificatif d'un élève de terminale, et faut-il une validation particulière ?",
                       'Lycée Général & Techno', 'examens', neighbor)
        paths = [d['path'] for d in a['documents'] if d['id'] in a['model_document_ids']]
        self.assertIn('data/commun/audit60/gt_regles_decisives.txt', paths)
        self.assertNotIn('reduit.txt', paths)

    def test_dnb_dispense_keeps_lsu_and_session_rule(self):
        a = self.audit("En troisième, un élève est dispensé d'EPS toute l'année : que met-on dans le LSU et est-ce que cela pénalise son brevet ?",
                       'Collège (DNB)', 'examens', mark_excerpt('Concours Capeps.', path='concours.txt'))
        paths = [d['path'] for d in a['documents'] if d['id'] in a['model_document_ids']]
        self.assertIn('data/commun/dnb/04_inaptitudes_dispenses.txt', paths)
        self.assertIn('data/examens/regles_dnb_eps.txt', paths)
        self.assertNotIn('concours.txt', paths)

    def test_co_parc_keeps_second_degree_fiche_with_college_scope(self):
        a = self.audit("Peut-on organiser une course d'orientation dans un parc public sans autorisation de la mairie ?",
                       'Collège (DNB)', 'textes', mark_excerpt('Escalade au premier relais.', path='escalade.txt'))
        paths = [d['path'] for d in a['documents'] if d['id'] in a['model_document_ids']]
        self.assertIn('data/commun/audit355/co_securite_sortie.txt', paths)
        self.assertNotIn('escalade.txt', paths)
        self.assertTrue(a['focused_document_ids'])

    def test_same_file_copy_is_removed_but_other_section_is_kept(self):
        full = source_packets(mark_excerpt('### Accès\nLe responsable ouvre le dossier.\nPuis il ferme le dossier.', path='doc.txt'))[0]
        copy = source_packets(mark_excerpt('[Base] Le responsable ouvre le dossier.', path='doc.txt'))[0]
        other = source_packets(mark_excerpt('Une autre section décrit le transfert.', path='doc.txt'))[0]
        self.assertTrue(packet_covered_by_focus(copy, [full]))
        self.assertFalse(packet_covered_by_focus(other, [full]))

    def test_focus_is_limited_to_declared_intention_not_all_shn_questions(self):
        from documentary_review import catalogue_focus_match
        packet = {'origin':'document', 'selection':'catalogue', 'path':'data/commun/pro_shn_ccf.txt'}
        self.assertTrue(catalogue_focus_match('SHN : un seul cycle suivi', packet))
        self.assertFalse(catalogue_focus_match('Comment déclarer un statut SHN tardif ?', packet))
        self.assertFalse(catalogue_focus_match('SHN : un seul cycle suivi', {**packet, 'selection':''}))

if __name__ == '__main__':
    unittest.main()
