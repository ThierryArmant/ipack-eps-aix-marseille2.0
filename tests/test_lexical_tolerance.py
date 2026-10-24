"""Variantes de saisie : garder le sujet, les conditions et les distinctions métier."""
import unittest
from knowledge_catalog import normalise, priority_titles
from documentary_review import situation_mismatch
from evidence_logic import non_implication_to_obligation

class LexicalToleranceTests(unittest.TestCase):
    def test_same_priority_for_spacing_and_typical_transpositions(self):
        cases=[
            ("Comment gérer un protocole adapté en cours d'année ?", "Comment gérer un protocloe adapté en cours d'année ?",'examens'),
            ("Notre protocole a déjà été validé, mais on doit remplacer une APSA. Comment faire ?", "Notre protocole a déjà été validé, mais on doit rempalcer une APSA. Comment faire ?",'ipack'),
            ("J'enseigne en bac pro et en CAP : je ne trouve qu'une partie de mes lots.", "J'enseigne  en  bac  pro  et  en  CAP : je ne trouve qu'une partie de mes lots.",'examens'),
        ]
        for q,variant,mode in cases:
            with self.subTest(question=q):
                expected=priority_titles(q,'Lycée Général & Techno',mode)
                self.assertTrue(expected)
                self.assertEqual(priority_titles(variant,'Lycée Général & Techno',mode),expected)
                self.assertEqual(priority_titles(q.replace(' ','\u00a0'),'Lycée Général & Techno',mode),expected)
    def test_matching_only_does_not_invent_codes_facts_or_correct_arbitrary_words(self):
        raw="CAP DI AB AFLP AFL1 avant après temporaire permanente 1 2 3 pas jamais inconnu proprenome"
        self.assertEqual(normalise(raw),'cap di ab aflp afl1 avant apres temporaire permanente 1 2 3 pas jamais inconnu proprenome')
        self.assertEqual(normalise('Je veux remplacer le protocole.'),'je veux remplacer le protocole.')
        self.assertEqual(normalise('protocle dispence'),'protocle dispence')
    def test_course_singular_keeps_relevant_proof_but_unrelated_subject_still_rejected(self):
        proof="Dans [APSA], sélectionner [Courses] et déclarer cette APSA certificative."
        for q in ["Ma fiche de course 3x1'30 n'est pas certificative.","Ma fiche de courses 3x1'30 n'est pas certificative.","Ma fiche de demi-fond n'est pas certificative."]:
            self.assertFalse(situation_mismatch(q,proof))
        self.assertTrue(situation_mismatch('Comment déclarer le professeur remplaçant ?',proof))
    def test_explicit_prerequisite_survives_independent_non_equivalence(self):
        proof="Les classes et les élèves doivent déjà être présents dans le logiciel : ce fichier reprend leur placement dans les groupes et ne constitue pas une synchronisation automatique."
        claim={'text':"Les classes et les élèves doivent déjà être présents dans le logiciel.",'evidence':[{'quote':proof}]}
        self.assertFalse(non_implication_to_obligation(claim))
        self.assertTrue(non_implication_to_obligation({'text':"Il faut préparer le protocole adapté.",'evidence':[{'quote':"Préparer le protocole adapté ne constitue pas une décision de la commission."}]}))
    def test_real_context_distinctions_are_not_folded(self):
        for a,b in [('avant','après'),('temporaire','permanente'),('CAP','bac GT'),('association','distribution'),('pas validé','validé')]:
            self.assertNotEqual(normalise(a),normalise(b))
        self.assertTrue(situation_mismatch("J'ai obtenu une seule note après une inaptitude.","Pour deux notes obtenues, calculer la moyenne."))
