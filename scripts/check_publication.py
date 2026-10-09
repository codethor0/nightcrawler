#!/usr/bin/env python3
"""Check frozen manuscript, figures, models, citation, and manifest, without network access."""
from __future__ import annotations
import hashlib, json, re, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'publication/manifest.json').read_text())

def need(ok,msg):
    if not ok: raise SystemExit('FAIL: '+msg)

def h(path,alg='sha256'):
    digest=hashlib.new(alg)
    with path.open('rb') as f:
        for buf in iter(lambda:f.read(1024*1024),b''):
            digest.update(buf)
    return digest.hexdigest()

def main():
    a=manifest['paper']
    pdf=ROOT/a['filename']
    need(pdf.is_file(),'paper PDF missing')
    need(pdf.stat().st_size==a['bytes'],'paper size changed')
    need(pdf.open('rb').read(5)==b'%PDF-','paper header invalid')
    need(h(pdf)==a['sha256'],'paper PDF differs from Zenodo-staged SHA-256')
    need(h(pdf,'md5')==a['md5'],'paper PDF differs from Zenodo-staged MD5')
    src=ROOT/'source/NIGHTCRAWLER_Research_Paper.md'
    need(h(src)==manifest['manuscript_sha256'],'canonical Markdown drift')

    lines=(ROOT/'publication/SHA256SUMS.txt').read_text().splitlines()
    seen=set()
    for line in lines:
        digest, sep, name=line.partition('  ')
        need(sep=='  ' and re.fullmatch(r'[0-9a-f]{64}',digest),'bad checksum row')
        path=Path(name)
        need(not path.is_absolute() and '..' not in path.parts,'unsafe checksum path')
        target=ROOT/path
        need(name not in seen and target.is_file(),'missing or repeated file '+name)
        need(h(target)==digest,'checksum drift: '+name)
        seen.add(name)
    need(len(seen)>=40,'too few immutable research artifacts in manifest')
    figs=sorted((ROOT/'figures').glob('*.png'))
    svgs=sorted((ROOT/'figures').glob('*.svg'))
    need(len(figs)==11 and len(svgs)==11,'expected eleven PNG and SVG figures')
    for f in figs:
        data=f.read_bytes()
        need(data[:8]==b'\x89PNG\r\n\x1a\n','invalid PNG: '+f.name)
        w,h_=struct.unpack('>II',data[16:24])
        need(w>=600 and h_>=250,'figure too small: '+f.name)
    for f in svgs:
        data=f.read_text(encoding='utf-8',errors='replace')
        need('<svg' in data and '</svg>' in data,'invalid SVG: '+f.name)
        need('http://www.w3.org/2000/svg' in data,'unexpected SVG namespace: '+f.name)
    readme=(ROOT/'README.md').read_text()
    for f in figs:
        need(('figures/'+f.name) in readme or ('figures/' in readme and 'remaining figures' in readme),
             'unlinked figure: '+f.name)
    cff=(ROOT/'CITATION.cff').read_text()
    need(manifest['title'] in cff, 'citation title mismatch')
    need(manifest['orcid'] in cff and manifest['orcid'] in readme,'missing author ORCID')
    need(manifest['title'] in readme or manifest['subtitle'] in readme,'missing title')
    need(manifest['publication_status'] in ('draft','published'),'unknown publication status')
    if manifest['publication_status']=='draft':
        need(manifest['doi'] is None,'draft must not claim a DOI')
        need('10.5281/zenodo.' not in cff and '10.5281/zenodo.' not in readme,
             'draft citation must not claim publication DOI')
    else:
        need(re.fullmatch(r'10\.5281/zenodo\.\d+',manifest['doi']) is not None,'invalid DOI')
        need(manifest['doi'] in cff and manifest['doi'] in readme,'missing published DOI')
    print('PUBLICATION INTEGRITY: PASS')
    print('paper_sha256='+a['sha256'])
    print(f'figures={len(figs)} png and {len(svgs)} svg')
    print('immutable_artifacts_checked='+str(len(seen)))
    print('zenodo_publication='+manifest['publication_status'])

if __name__=='__main__': main()
