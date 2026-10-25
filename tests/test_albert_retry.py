import json
import unittest
from unittest import mock
from urllib.error import HTTPError

import albert_adapter
import exact_source_answer


class _Response:
    status = 200

    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _http(code, retry_after=None):
    headers = {'Retry-After': retry_after} if retry_after else {}
    return HTTPError('https://albert', code, 'err', headers, None)


class AlbertRetryTest(unittest.TestCase):
    def call(self, outcomes):
        opener = mock.Mock()
        opener.open.side_effect = outcomes
        sleeps = []
        with mock.patch.object(albert_adapter, 'build_opener', return_value=opener), \
                mock.patch.object(albert_adapter, '_sleep', sleeps.append):
            try:
                return albert_adapter._request('k', 'POST', '/chat/completions', {}, allow_paused_test=True), sleeps, opener
            except albert_adapter.AlbertServiceError as exc:
                return exc, sleeps, opener

    def test_quota_retried_once_after_retry_after(self):
        result, sleeps, opener = self.call([_http(429, '7'), _Response(json.dumps({'ok': 1}).encode())])
        self.assertEqual(result, {'ok': 1})
        self.assertEqual(sleeps, [7.0])
        self.assertEqual(opener.open.call_count, 2)

    def test_quota_twice_gives_up_without_loop(self):
        result, sleeps, opener = self.call([_http(429), _http(429), _Response(b'{}')])
        self.assertIsInstance(result, albert_adapter.AlbertServiceError)
        self.assertEqual(result.code, 'http_429')
        self.assertEqual(sleeps, [albert_adapter._RETRY_DEFAULT_SECONDS])
        self.assertEqual(opener.open.call_count, 2)

    def test_retry_after_is_capped(self):
        _, sleeps, _ = self.call([_http(503, '600'), _Response(b'{}')])
        self.assertEqual(sleeps, [albert_adapter._RETRY_MAX_SECONDS])

    def test_refused_key_not_retried(self):
        result, sleeps, opener = self.call([_http(401), _Response(b'{}')])
        self.assertEqual(result.code, 'http_401')
        self.assertEqual(sleeps, [])
        self.assertEqual(opener.open.call_count, 1)


class ServiceErrorLabelTest(unittest.TestCase):
    def test_quota_not_reported_as_bad_selection(self):
        import architecture_comparison as ac
        from types import SimpleNamespace
        dr = ac._runtime.documentary_review
        docs = dr.mark_excerpt('Ouvrez le menu [Dossier].', path='data/test0.txt', title='Source 0')
        llm = SimpleNamespace(model='gpt-oss-120b', temperature=0,
                              complete=mock.Mock(side_effect=albert_adapter.AlbertServiceError('Quota', 'http_429')))
        audit = {}
        out = exact_source_answer.exact_answer(llm, reviewer=dr, tracer=ac.TracedLLM, documents=docs,
                                               question='Comment ?', public='p', mode='ipack',
                                               academy='Aix-Marseille', audit=audit)
        llm.complete.assert_called_once()
        self.assertIn('quota', out)
        self.assertNotIn('Sélection non exploitable', out)
        self.assertEqual(audit['exact_extracts']['status'], 'service_unavailable_no_retry')
        self.assertEqual(audit['exact_extracts']['error_code'], 'http_429')


if __name__ == '__main__':
    unittest.main()
