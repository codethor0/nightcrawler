#!/usr/bin/env python3
"""Fail closed for secrets, private process files, unsafe CI actions and workstation paths."""
from __future__ import annotations
import re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SKIP_LOCAL_DIRS={'.venv','venv','__pycache__','.git'}
FORBIDDEN_PARTS={'.DS_Store','__MACOSX','.env','.ssh','audit',
                 'private','build','dist','checkpoints'}
FORBIDDEN_TOKENS=('Pasted text','Pasted markdown','PATENT_INVENTOR','EXTERNAL_AUDIT',
                  'QA_AND_LIMITATIONS','REVISION_TRACE','SOURCE_VERIFICATION','ORCID-Brave',
                  'ASCP-REPO-AUDIT')
TEXT_EXT={'.py','.md','.yml','.yaml','.json','.cff','.txt','.sh','.dot','.svg','.toml'}
SECRETS={
 'GitHub token':re.compile(r'gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}'),
 'OpenAI-style token':re.compile(r'sk-[A-Za-z0-9_-]{20,}'),
 'AWS key':re.compile(r'AKIA[0-9A-Z]{16}'),
 'Private key block':re.compile(r'-----BEGIN (?:RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY-----'),
 'Secret assignment':re.compile(r'(?i)(?:token|api_key|password|secret)\s*[=:]\s*[A-Za-z0-9_\-]{30,}'),
 'Local path':re.compile(r'/Users/[A-Za-z0-9_.-]+/|/home' + r'/oai/|/mnt' + r'/data/|sandbox' + r':/'),
}

def need(ok,msg):
    if not ok:raise SystemExit('FAIL: '+msg)

def main():
    found=[]
    for p in ROOT.rglob('*'):
        if p==ROOT:continue
        rel=p.relative_to(ROOT)
        if any(x in SKIP_LOCAL_DIRS for x in rel.parts): continue
        if any(x in FORBIDDEN_PARTS or x.lower().startswith('private_') for x in rel.parts):
            found.append(f'forbidden path: {rel}')
            continue
        if any(x.lower() in str(rel).lower() for x in FORBIDDEN_TOKENS):
            found.append(f'private filename: {rel}')
            continue
        if p.is_file() and (p.suffix.lower() in TEXT_EXT or p.name in {'Makefile','CITATION.cff','.gitignore','.gitattributes','LICENSE-CODE'}):
            body=p.read_text(encoding='utf-8',errors='replace')
            for name, pattern in SECRETS.items():
                if pattern.search(body):found.append(f'{name} in {rel}')
            if p.name in {'README.md','SECURITY.md','CONTRIBUTING.md','CITATION.cff'} and not rel.parts[0] in {'reference','figures'}:
                bad_labels=('Chat'+'GPT','Clau'+'de AI','Co'+'dex agent')
                if any(x.lower() in body.lower() for x in bad_labels) or re.search(r'(?i)\binternal\s+audit\s+prompt\b',body):
                    found.append(f'process metadata in {rel}')
    need(not found,'\n'.join(found))
    workflow=(ROOT/'.github/workflows/reproducibility.yml').read_text()
    need('permissions:\n  contents: read' in workflow,'workflow token scope is not read-only')
    need('persist-credentials: false' in workflow,'checkout retains credentials')
    need('pull_request_target' not in workflow,'unsafe privileged workflow event')
    need('--require-hashes --only-binary=:all:' in workflow, 'dependency install must use immutable wheel hash')
    need('--hash=sha256:d47fbf302e7d9cbbb9e2555a0d267983d2aa476bac30e90dfbe5669bd57f3762' in (ROOT/'requirements-ci.txt').read_text(), 'missing verified PyPI wheel hash')
    need('cron:' in workflow and 'workflow_dispatch:' in workflow,'missing scheduled/manual CI')
    uses=[]
    for line in workflow.splitlines():
        match=re.match(r'^\s*-?\s*uses:\s*([^#\s]+)',line)
        if match:uses.append(match.group(1))
    need(len(uses)==1,'unexpected workflow action dependency count')
    for action in uses:
        need(bool(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-fA-F]{40}',action)),
             'workflow action not pinned to full commit SHA')
    need('actions/checkout@' in uses[0],'unexpected checkout action')
    print('REPOSITORY HYGIENE: PASS')
    print('read_only_workflow=true')
    print('pinned_external_actions='+str(len(uses)))
    print('private_surface_scan=clean')

if __name__=='__main__':main()
