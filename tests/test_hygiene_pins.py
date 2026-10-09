"""Guard the dependency pinning rule enforced by the hygiene check."""
import unittest
from scripts.check_hygiene import check_requirements

HASH = '--hash=sha256:' + 'a' * 64


class RequirementPinning(unittest.TestCase):
    def test_pinned_with_one_or_more_hashes_passes(self):
        check_requirements('# comment\nnetworkx==3.7 ' + HASH + ' ' + HASH + '\n')

    def test_unpinned_version_fails_closed(self):
        with self.assertRaises(SystemExit):
            check_requirements('networkx>=3.0 ' + HASH + '\n')

    def test_missing_hash_fails_closed(self):
        with self.assertRaises(SystemExit):
            check_requirements('networkx==3.7\n')

    def test_malformed_hash_fails_closed(self):
        with self.assertRaises(SystemExit):
            check_requirements('networkx==3.7 --hash=sha256:' + 'a' * 63 + '\n')

    def test_empty_requirements_fail_closed(self):
        with self.assertRaises(SystemExit):
            check_requirements('# only a comment\n')


if __name__ == '__main__':
    unittest.main()
