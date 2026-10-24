import unittest
from question_normalization import normalise_question
from document_selector import _words, request_contract


class QuestionNormalizationTests(unittest.TestCase):
    def test_missing_spaces_without_changing_action_or_object(self):
        original = 'Comment réaffecterun lotà un autre examinateur ?'
        result = normalise_question(original)
        self.assertEqual(result['original'], original)
        self.assertEqual(result['recherche'], 'Comment réaffecter un lot à un autre examinateur ?')
        self.assertEqual(len(result['corrections']), 2)
        self.assertEqual(_words(original), _words(result['recherche']))

    def test_protected_meaning_and_unknown_words(self):
        questions = [
            "AFL AFLP AFL1 ASNS FCA CAP GT DI AB DEC DIEC Imag'in iPackEPS",
            "pas validé, jamais après, avant 2026 : 2 notes, 16/20, n-1",
            "inaptitude temporaire et permanente, aptitude totale ou partielle",
            "déplacer un candidat / réaffecter un lot entier",
            "Dumont, pronotte, dispence, voie générale, lotissement",
            "https://exemple.fr/lotà et dossier/protocoleun AFL1un",
            "mesnotes@example.fr https://mesnotes.fr dossier/mesnotes",
        ]
        for question in questions:
            with self.subTest(question=question):
                self.assertEqual(normalise_question(question)['recherche'], question)

    def test_known_typos_only_and_idempotence(self):
        for original, expected in [('un protocloe', 'un protocole'),
                                   ('Rempalcer un lot', 'Remplacer un lot'),
                                   ('mesnotes', 'mes notes'),
                                   ('protocle dispence', 'protocle dispence')]:
            result = normalise_question(original)
            self.assertEqual(result['recherche'], expected)
            self.assertEqual(normalise_question(expected)['recherche'], expected)

    def test_literal_contract_still_cannot_invent_software_or_action(self):
        self.assertIsNone(request_contract({'actions': ['supprimer le lot'], 'point_depart': 'Santorin'},
                                           'Comment réaffecter un lot ?'))

    def test_real_retrieval_uses_copy_and_preserves_source_question(self):
        from document_retrieval import retrieve_documents
        from unittest.mock import Mock
        question = 'Comment réaffecterun lotà un autre examinateur ?'
        retriever = Mock()
        retriever.retrieve.return_value = []
        lexical = Mock(return_value=[])
        notice = Mock(return_value=[])
        retrieve_documents(prompt=question, p_norm=question.lower(), p_low=question.lower(),
            niveau_actuel_form='Lycée Général & Techno', mode='examens', est_college=False,
            est_clairement_lycee=True, mots_cles_intention_peda=[], recherche_mots={},
            chercher_par_mots=lexical, retriever_textes=None, retriever_peda=None,
            retriever_santorin=retriever, retriever_ipack=None,
            libelle_source=lambda *args: '', _url_source=lambda *args: '',
            reference_notice=notice)
        expected = 'Comment réaffecter un lot à un autre examinateur ?'
        retriever.retrieve.assert_called_once_with(expected)
        self.assertTrue(all(call.args[2] == expected for call in lexical.call_args_list))
        self.assertEqual(notice.call_args.args[1], expected)
        self.assertEqual(question, 'Comment réaffecterun lotà un autre examinateur ?')


if __name__ == '__main__':
    unittest.main()
