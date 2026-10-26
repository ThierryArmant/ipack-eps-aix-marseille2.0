import unittest

import admin_retest_113_live as live


class ReplayEngineChoiceTest(unittest.TestCase):
    def test_three_engines_in_one_place(self):
        self.assertEqual(sorted(live.ENGINE_CHOICES.values()), ['albert_redige', 'comparaison', 'mini'])
        for engine in live.ENGINE_CHOICES.values():
            self.assertIn(engine, live.ENGINE_HELP)
            self.assertIn(engine, live.ENGINE_SHORT)

    def test_engine_only_while_a_question_is_processed(self):
        self.assertIsNone(live.replay_engine({}))
        self.assertIsNone(live.replay_engine({'audit113_batch': {'moteur': 'albert_redige', 'waiting': False}}))
        self.assertIsNone(live.replay_engine({'audit113_batch': {'moteur': 'albert_redige', 'waiting': True, 'stopped': True}}))
        self.assertEqual(live.replay_engine({'audit113_batch': {'moteur': 'albert_redige', 'waiting': True}}), 'albert_redige')

    def test_app_uses_batch_engine_before_direct_checkbox(self):
        source = open('app.py', encoding='utf-8').read()
        self.assertIn('if _lot_moteur:\n            _albert_redige_voulu = _lot_moteur == "albert_redige"', source)


if __name__ == '__main__':
    unittest.main()
