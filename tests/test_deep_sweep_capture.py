"""Guard the boundary between two independent historical simulation runs."""
import unittest
from pathlib import Path
from scripts.check_models import frozen_20000_lines, lines

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = (ROOT / 'reference/RESULTS.txt').read_text()


class FrozenDeepSweepCapture(unittest.TestCase):
    def test_historical_capture_has_one_full_model_and_ten_ablations(self):
        found = frozen_20000_lines(CAPTURE)
        self.assertEqual(len(found), 12)
        self.assertEqual(sum(x.startswith('unit checks:') for x in found), 1)
        self.assertEqual(sum(x.startswith('full model ') for x in found), 1)
        self.assertEqual(sum(x.startswith('no_') or x.startswith('heuristic_C4a') for x in found), 10)

    def test_sweep_must_not_add_second_unit_check(self):
        self.assertEqual(sum(x.startswith('unit checks:') for x in lines(CAPTURE)), 2)
        self.assertEqual(sum(x.startswith('unit checks:') for x in frozen_20000_lines(CAPTURE)), 1)

    def test_missing_sweep_boundary_fails_closed(self):
        with self.assertRaises(AssertionError):
            frozen_20000_lines(CAPTURE.replace('Command: python3 reference/nightcrawler_ref.py sweep', 'Command: missing'))

    def test_duplicate_historical_command_fails_closed(self):
        with self.assertRaises(AssertionError):
            frozen_20000_lines(CAPTURE + '\nCommand: python3 reference/nightcrawler_ref.py 20000')

    def test_reversed_commands_fail_closed(self):
        header = 'Command: python3 reference/nightcrawler_ref.py 20000'
        sweep = 'Command: python3 reference/nightcrawler_ref.py sweep'
        with self.assertRaises(AssertionError):
            frozen_20000_lines(CAPTURE.replace(header, 'TEMP').replace(sweep, header).replace('TEMP', sweep))


if __name__ == '__main__':
    unittest.main()
