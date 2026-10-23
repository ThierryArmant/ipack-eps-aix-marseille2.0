import unittest
from pathlib import Path
from documentary_review import context_document_mismatch, mark_excerpt, review_exam_answer


class DiplomaApplicabilityTests(unittest.TestCase):
    def packet(self, scopes, text='Procédure propre au diplôme.'):
        return dict(title='Saisie', path='guide.txt', scopes=scopes, text=text)

    def test_declared_scope_and_mixed_scope(self):
        for public in ('Lycée voie générale', 'Lycée Général & Techno', 'GT'):
            self.assertTrue(context_document_mismatch('Saisie impossible', public, 'examens', self.packet(['pro', 'cap'])))
            self.assertFalse(context_document_mismatch('Saisie impossible', public, 'examens', self.packet(['gt', 'pro', 'cap'])))
        self.assertFalse(context_document_mismatch('Saisie impossible', 'Lycée voie professionnelle', 'examens', self.packet(['cap'])))
        self.assertTrue(context_document_mismatch('Saisie impossible', 'Lycée voie professionnelle', 'examens', self.packet(['gt'])))
        self.assertFalse(context_document_mismatch('Comparer les deux diplômes', 'GT', 'examens', self.packet(['pro'])))
        self.assertTrue(context_document_mismatch('Saisie impossible', 'GT', 'examens', self.packet([], '[PORTEE: pro,cap]\nProcédure.')))

    def test_real_documents_pro_scope_excluded_but_shared_diagnostic_preserved(self):
        root=Path('data/examens')
        paths=['audit_faq_2026_10_12/k3_procedure_verifiee.txt', 'complement_saisie_bloquee_diagnostic.txt']
        docs='\n'.join(mark_excerpt((root/p).read_text(), path=str(root/p), title='Diagnostic') for p in paths)
        class Recorder:
            model='offline'
            temperature=0
            def __init__(self): self.prompts=[]
            def complete(self, prompt):
                self.prompts.append(prompt)
                return type('Response', (), {'text':'{"claims":[]}'})()
        llm=Recorder(); audit={}
        review_exam_answer(llm, question='La saisie des évaluations ne fonctionne plus', public='Lycée voie générale', documents=docs, audit=audit)
        self.assertIn('D1', audit['excluded_situation_documents'])
        self.assertIn('D2', audit['model_document_ids'])
        self.assertIn('Au bac GT, vérifier', llm.prompts[0])
        self.assertIn('Au bac professionnel ou au CAP uniquement', llm.prompts[0])
        self.assertEqual(len(llm.prompts), 1)
        self.assertFalse(audit['repair_performed'])
