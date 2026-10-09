"""Offline tests for the Zenodo record verifier."""
import io
import unittest
import urllib.error
from scripts.check_zenodo import fetch, problems

MANIFEST = {'doi': '10.5281/zenodo.1', 'title': 'T',
            'paper': {'filename': 'P.pdf', 'md5': 'abc'}}
GOOD = {'doi': '10.5281/zenodo.1', 'metadata': {'title': 'T'},
        'files': [{'key': 'P.pdf', 'checksum': 'md5:abc'}]}


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http(code):
    return urllib.error.HTTPError('u', code, 'x', {}, None)


class RecordComparison(unittest.TestCase):
    def test_matching_record_has_no_problems(self):
        self.assertEqual(problems(MANIFEST, GOOD), [])

    def test_wrong_checksum_is_reported(self):
        bad = dict(GOOD, files=[{'key': 'P.pdf', 'checksum': 'md5:zzz'}])
        self.assertTrue(problems(MANIFEST, bad))

    def test_wrong_title_is_reported(self):
        self.assertTrue(problems(MANIFEST, dict(GOOD, metadata={'title': 'X'})))

    def test_doi_may_come_from_pids(self):
        rec = {'pids': {'doi': {'identifier': '10.5281/zenodo.1'}},
               'metadata': {'title': 'T'}, 'files': GOOD['files']}
        self.assertEqual(problems(MANIFEST, rec), [])


class Fetching(unittest.TestCase):
    def test_server_errors_exhaust_retries_and_return_none(self):
        calls = []

        def opener(url, timeout):
            calls.append(url)
            raise _http(504)
        self.assertIsNone(fetch('u', attempts=3, opener=opener, sleep=lambda s: None))
        self.assertEqual(len(calls), 3)

    def test_transient_error_then_success(self):
        seq = [_http(503), _Resp(b'{"ok": 1}')]

        def opener(url, timeout):
            item = seq.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        self.assertEqual(fetch('u', opener=opener, sleep=lambda s: None), {'ok': 1})

    def test_blocked_or_rate_limited_is_treated_as_unreachable(self):
        for code in (403, 429):
            def opener(url, timeout, code=code):
                raise _http(code)
            self.assertIsNone(fetch('u', attempts=2, opener=opener, sleep=lambda s: None))

    def test_missing_record_is_not_swallowed(self):
        def opener(url, timeout):
            raise _http(404)
        with self.assertRaises(urllib.error.HTTPError):
            fetch('u', opener=opener, sleep=lambda s: None)

    def test_network_failure_returns_none(self):
        def opener(url, timeout):
            raise urllib.error.URLError('down')
        self.assertIsNone(fetch('u', attempts=2, opener=opener, sleep=lambda s: None))


if __name__ == '__main__':
    unittest.main()
