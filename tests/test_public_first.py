import unittest
from hub_session import allowed_modules, select_public, select_module, ready_for_question

class PublicFirstTests(unittest.TestCase):
    def test_primary_transition_removes_previous_exam_context_and_answer(self):
        state = dict(niveau_actif_form='1er degré', active_module='examens', contexte_valide=True,
                     messages_hub=['ancienne réponse lycée'], current_prompt='ancienne question')
        select_public(state, '1er degré')
        self.assertEqual(state['active_module'], 'textes')
        self.assertEqual(state['messages_hub'], [])
        self.assertNotIn('current_prompt', state)
        self.assertTrue(ready_for_question(state))
        select_module(state, 'examens')
        self.assertEqual(state['active_module'], 'textes')

    def test_primary_cannot_submit_with_stale_exam_context(self):
        state = dict(niveau_actif_form='1er degré', active_module='examens', contexte_valide=True,
                     academie_utilisateur='Créteil')
        self.assertFalse(ready_for_question(state))
        self.assertEqual(allowed_modules('1er degré'), ('textes',))

    def test_secondary_options_and_academy_requirement_remain(self):
        self.assertEqual(allowed_modules(None), ())
        for public in ('Collège', 'Lycée Général & Techno', 'Lycée Pro / CAP'):
            self.assertEqual(allowed_modules(public), ('ipack','examens','textes'))
            state = dict(niveau_actif_form=public, active_module='examens', contexte_valide=True)
            self.assertFalse(ready_for_question(state))
            state['academie_utilisateur']='Aix-Marseille'
            self.assertTrue(ready_for_question(state))
