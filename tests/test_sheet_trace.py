import json
import hashlib
import unittest
from sheet_trace import make_trace_payload

class SheetTraceTests(unittest.TestCase):
    def payload(self, **kw):
        return make_trace_payload(question='élèves ?', answer='Réponse', mode='ipack',
            public='Tous', academy='Poitiers', version='test', origin='ia', **kw)

    def test_complete_diagnostic_roundtrip(self):
        diagnostic = {'documents':[{'text':'preuve 😀' * 15000}],
                      'short_answer':{'rejected':[{'reason':'condition omise'}]},
                      'calls':[{'prompt':'passages transmis', 'output':'première réponse'}]}
        p = self.payload(diagnostic=diagnostic)
        t = json.loads(p['trace_json'])
        self.assertEqual(t['diagnostic'], diagnostic)
        self.assertEqual(t['id_essai'],p['id_essai'])
        self.assertEqual(hashlib.sha256(p['trace_json'].encode()).hexdigest(),p['trace_sha256'])

    def test_no_generation_is_explicit_and_ids_distinct(self):
        a,b=self.payload(),self.payload()
        self.assertNotEqual(a['id_essai'], b['id_essai'])
        self.assertFalse(json.loads(a['trace_json'])['diagnostic_disponible'])

    def test_credentials_not_exported_and_nonfinite_valid_json(self):
        t=json.loads(self.payload(diagnostic={'api_key':'secret','nested':{'Authorization':'secret'},'score':float('nan')})['trace_json'])
        self.assertNotIn('secret',str(t))
        self.assertIsNone(t['diagnostic']['score'])
