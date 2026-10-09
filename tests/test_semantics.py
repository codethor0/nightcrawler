"""Model-relative safety checks, not field validation."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reference'))
import nightcrawler_ref as old
import two_phase_checks as new

class TwoPhaseSemantics(unittest.TestCase):
    def test_condition_inventory_exact(self):
        self.assertEqual(new.CONDITIONS,
            {'C0','C1','C2','C3','C4a','C4b','C4c','C5','C6','C7','C8','C9'})

    def test_surviving_message_still_live(self):
        w = new.baseline()
        state, conds, seeds = new.evaluate(w)
        self.assertIn('M', seeds)
        self.assertFalse(conds['C6'])
        self.assertNotEqual('COMPLETE', state)

    def test_missing_issuer_evidence_fails_closed(self):
        w = new.baseline()
        w.future = []
        w.present = {'trigger'}
        w.provider_logs.add('unknown-issuer')
        state, c, _ = new.evaluate(w)
        self.assertFalse(c['C0'])
        self.assertNotEqual(state, 'COMPLETE')

    def test_late_identity_requires_second_fence(self):
        w = new.baseline()
        w.future = []
        w.present = {'trigger'}
        w.auth_relations=[('cred_q','id2','acquires')]
        state, c, _ = new.evaluate(w)
        self.assertFalse(c['C1'])
        self.assertNotEqual(state, 'COMPLETE')

    def test_independent_attestation_is_required(self):
        w = new.baseline()
        w.future = []
        w.present = {'trigger'}
        w.externally_verified = False
        state, c, _ = new.evaluate(w)
        self.assertFalse(c['C9'])
        self.assertNotEqual(state, 'COMPLETE')

class LegacyFailClosed(unittest.TestCase):
    def test_no_empty_or_partial_conditions_can_complete(self):
        self.assertNotEqual(old.assign_state(False, {}, False), 'COMPLETE')
        self.assertNotEqual(old.assign_state(False, {}, True), 'COMPLETE')
        true = {k: True for k in new.CONDITIONS}
        self.assertEqual(old.assign_state(False, true, True), 'COMPLETE')
        del true['C0']
        self.assertNotEqual(old.assign_state(False, true, True), 'COMPLETE')

    def test_infeasible_cut_is_not_success(self):
        import networkx as nx
        g=nx.DiGraph()
        g.add_node('a', system='s0', kind='artifact', present=True, refuted=False)
        g.add_node('effect', system='s0', kind='effect', present=True, refuted=False)
        g.add_edge('a','effect')
        cut, cost = old.min_cut_plan(old.REG(g, effects={'effect'}), {'a'}, {'s0'}, {})
        self.assertIsNone(cut)
        self.assertEqual(cost, float('inf'))

if __name__ == '__main__':
    unittest.main()
