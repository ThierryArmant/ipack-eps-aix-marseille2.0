import unittest
from confirmed_scope import explicit_scope,routing_question,filter_rejected_software

class ConfirmedScopeTests(unittest.TestCase):
    def test_explicit_correction_preserves_answer_question_and_routes_without_rejected_software(self):
        original='Je ne peux plus saisir mes notes.'
        detail="Ce n’est pas Santorin : je parle de Pronote."
        result=routing_question(original,detail)
        self.assertEqual(result['original_question'],original)
        self.assertIn(detail,result['question_for_answer'])
        self.assertEqual(result['scope']['rejected'],['santorin'])
        self.assertEqual(result['scope']['affirmed'],['pronote'])
        self.assertNotIn('Santorin',result['routing_question'])
        self.assertIn('Pronote',result['routing_question'])
    def test_inability_to_use_santorin_is_not_a_rejection_of_santorin(self):
        for detail in ['Je ne peux pas saisir dans Santorin.','Je ne trouve pas mon lot dans Santorin.','Santorin ne fonctionne pas.']:
            self.assertEqual(explicit_scope(detail)['rejected'],[])
    def test_positive_two_software_transfer_is_not_restricted(self):
        detail='Je transfère les élèves de Pronote vers iPackEPS.'
        self.assertFalse(explicit_scope(detail)['determinate'])
        q=routing_question('Comment importer ?',detail)
        self.assertIn('Pronote',q['routing_question'])
        self.assertIn('iPackEPS',q['routing_question'])
    def test_ambiguous_correction_is_not_forced(self):
        scope=explicit_scope("Ce n'est pas Santorin : j'utilise Pronote et iPackEPS.")
        self.assertFalse(scope['determinate'])
    def test_wrong_software_title_excluded_but_comparison_and_national_title_retained(self):
        scope=explicit_scope("Ce n'est pas Santorin : je parle de Pronote.")
        packets=[{'id':'1','title':'Santorin : cases de notes grisées'},
                 {'id':'2','title':'Pronote et Santorin : sens des transferts'},
                 {'id':'3','title':'Texte national : évaluation en EPS'}]
        kept,removed=filter_rejected_software(packets,scope)
        self.assertEqual([p['id'] for p in removed],['1'])
        self.assertEqual([p['id'] for p in kept],['2','3'])
    def test_no_rejection_keeps_candidates(self):
        p=[{'title':'Santorin : saisie'}]
        self.assertEqual(filter_rejected_software(p,explicit_scope('Dans Santorin.')),(p,[]))

    def test_candidates_in_lot_are_not_missing_teacher_lots(self):
        from confirmed_scope import filter_lot_owner_mismatch
        docs=[{'title':"Santorin : lot manquant d'un collègue"},
              {'title':'Santorin : élèves manquants après distribution ou enseignant absent'},
              {'title':'Enseignant : préparer sa fiche professeur'}]
        keep,excluded=filter_lot_owner_mismatch(docs,'Liste des candidats de mon lot de CCF dans Santorin')
        self.assertEqual(excluded,[docs[0]])
        self.assertEqual(keep,docs[1:])
    def test_teacher_lot_question_and_negative_correction_are_not_filtered(self):
        from confirmed_scope import filter_lot_owner_mismatch
        docs=[{'title':"Santorin : lot manquant d'un collègue"}]
        for text in ["Mon collègue ne retrouve pas ses lots.","Ce n'est pas la liste des candidats du lot."]:
            self.assertEqual(filter_lot_owner_mismatch(docs,text),(docs,[]))

    def test_complementary_query_uses_confirmed_subject_and_existing_missing_state(self):
        from confirmed_scope import missing_learner_search
        q=missing_learner_search('Je ne retrouve pas tous mes élèves.','Liste des candidats de mon lot de CCF dans Santorin')
        self.assertIn('Il manque des candidats.',q)
        self.assertNotIn('inscrit',q)
        self.assertNotIn('distribution',q)
    def test_no_candidate_search_for_teacher_lot_or_no_missing_state(self):
        from confirmed_scope import missing_learner_search
        self.assertIsNone(missing_learner_search('Je ne retrouve pas mon lot.',"Lot de mon collègue dans Santorin"))
        self.assertIsNone(missing_learner_search('Comment ouvrir la liste ?',"Liste des candidats de mon lot de CCF dans Santorin"))

    def test_open_lot_not_confused_with_absent_lot(self):
        from confirmed_scope import filter_absent_lot_when_open
        docs=[{'title':'Santorin : aucun lot à corriger'},{'title':'Élèves absents du lot'}]
        self.assertEqual(filter_absent_lot_when_open(docs,'Mon lot est ouvert mais des candidats manquent'),([docs[1]],[docs[0]]))
        self.assertEqual(filter_absent_lot_when_open(docs,'Liste des candidats de mon lot'),(docs,[]))
    def test_confirmed_retrieval_keeps_raw_question_and_applies_one_bounded_retry(self):
        from confirmed_scope import retrieve_confirmed
        from documentary_review import mark_excerpt,source_packets
        from unittest.mock import Mock
        lookup=Mock(side_effect=[(mark_excerpt('Guide logiciel',title="Lot manquant d'un collègue"),[],[],''),
                                 (mark_excerpt('Vérifier les candidats du lot.',title='Candidats absents du lot'),[],[],'')])
        result=retrieve_confirmed('Je ne retrouve pas tous mes élèves.','Liste des candidats de mon lot de CCF dans Santorin',
                                  'Lycée Général & Techno','ipack',lookup)
        self.assertEqual(lookup.call_count,2)
        self.assertEqual(result['mode'],'examens')
        self.assertEqual([p['title'] for p in source_packets(result['documents'])],['Candidats absents du lot'])
        self.assertEqual(result['plan']['original_question'],'Je ne retrouve pas tous mes élèves.')
