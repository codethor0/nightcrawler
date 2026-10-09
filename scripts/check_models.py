#!/usr/bin/env python3
"""Reproduce targeted checks and reference simulations without guessing results."""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

def run(path, *args):
    r=subprocess.run([PY,str(ROOT/'reference'/path),*args],cwd=ROOT,
                     capture_output=True,text=True,timeout=360,check=True)
    if r.stderr.strip():
        raise SystemExit('FAIL: unexpected model stderr: '+r.stderr[-1200:])
    return r.stdout.replace('\r\n','\n').strip()+'\n'

def lines(s):
    return [ln for ln in s.splitlines() if ln.startswith('unit checks:') or
            ln.startswith('full model ') or ln.startswith('no_') or
            ln.startswith('heuristic_C4a')]

def main():
    expected=(ROOT/'reference/TWO_PHASE_RESULTS.txt').read_text()
    observed=run('two_phase_checks.py')
    assert observed == expected, 'two-phase output differs from frozen 16-case baseline'
    assert sum(line.startswith('PASS ') for line in observed.splitlines())==16, 'expected sixteen passing cases'
    print('PASS: 16 targeted modeled-evidence checks exactly reproduce')

    fast=run('nightcrawler_ref.py','2000')
    fast_expected=(ROOT/'reference/CI_RESULTS_2000.txt').read_text()
    assert fast==fast_expected, '2,000-world fast reference output changed'
    assert len(lines(fast))==12, 'expected unit checks plus 11 historical model arms'
    assert lines(fast)[1].endswith('false_COMPLETE=0')
    print('PASS: 2,000-world CI fixture and ten ablations exactly reproduce')

    if '--full' in sys.argv:
        full=run('nightcrawler_ref.py','20000')
        captured=(ROOT/'reference/RESULTS.txt').read_text()
        expected_lines=lines(captured)
        actual_lines=lines(full)
        assert len(expected_lines)==12, '20,000-world captured output malformed'
        assert actual_lines==expected_lines, '20,000-world historical output drift'
        ablations=[int(x.rsplit('false_COMPLETE=',1)[1]) for x in actual_lines
                  if 'false_COMPLETE=' in x and not x.startswith('full model ')]
        assert len(ablations)==10 and all(x>0 for x in ablations)
        print('PASS: 20,000-world historical study, ten ablations, captured counts')
    print('Scope: synthetic internal consistency only; not real-provider validation')

if __name__=='__main__':main()
