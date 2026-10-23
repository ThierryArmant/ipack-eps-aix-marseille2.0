import unittest
from admin_retest_113_live import select_replay_numbers

class ReplayNumbersTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'n':str(n),'question':f'Q{n}','academie':'','mode':'examens'} for n in (3,5,8,19,26,30,40,41,44,49)]
    def test_selects_csv_ids_not_positions_and_keeps_order_and_context(self):
        picked=select_replay_numbers(self.rows,'49, 3,19')
        self.assertEqual([r['n'] for r in picked],['49','3','19'])
        self.assertIs(picked[0],self.rows[-1])
    def test_duplicates_are_not_paid_twice(self):
        self.assertEqual([r['n'] for r in select_replay_numbers(self.rows,'03,3,5')],['3','5'])
    def test_unknown_number_rejects_whole_selection(self):
        with self.assertRaisesRegex(ValueError,'99'):
            select_replay_numbers(self.rows,'3,99')
    def test_malformed_input_is_rejected(self):
        for value in ('','3,','3,,5','-3','3-5','3;5','Q3','3.5'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                select_replay_numbers(self.rows,value)
    def test_ambiguous_identifiers_rejected(self):
        with self.assertRaisesRegex(ValueError,'ambigu'):
            select_replay_numbers([{'n':'3'},{'n':'03'}],'3')
