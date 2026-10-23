import unittest
from single_document_test import consume_single_document_test, isolate_document, TARGET

class SingleDocumentTests(unittest.TestCase):
    def test_consumed_once_only_in_admin_examens(self):
        state = {'is_admin': True, 'single_document_pending': True}
        self.assertFalse(consume_single_document_test(state, 'ipack'))
        self.assertTrue(consume_single_document_test(state, 'examens'))
        self.assertFalse(consume_single_document_test(state, 'examens'))
        state = {'single_document_pending': True}
        self.assertFalse(consume_single_document_test(state, 'examens'))
        self.assertNotIn('single_document_pending', state)

    def test_exact_document_kept_intact_missing_or_duplicate_stops(self):
        packet = {'id': 'D1', 'path': TARGET, 'passages': [{'text': 'AFL1'}]}
        self.assertIs(isolate_document([packet, {'path': 'other'}], TARGET)[0], packet)
        for packets in ([], [packet, packet]):
            with self.assertRaises(ValueError):
                isolate_document(packets, TARGET)
