#!/usr/bin/env python3
"""Verify the published Zenodo record against the manifest.

A mismatch fails. An unreachable Zenodo service does not: it is reported as a
warning, because third-party availability is not a property of this repository.
"""
from __future__ import annotations
import json, sys, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = 'https://zenodo.org/api/records/'
RETRYABLE = {403, 408, 429, 500, 502, 503, 504}


def fetch(url, attempts=5, delay=2.0, timeout=30, opener=urllib.request.urlopen, sleep=time.sleep):
    """Return parsed JSON, or None when the service stays unreachable. A 404 or other client error raises."""
    for attempt in range(attempts):
        try:
            with opener(url, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as err:
            if err.code not in RETRYABLE:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError):
            pass
        if attempt < attempts - 1:
            sleep(delay * 2 ** attempt)
    return None


def problems(manifest, record):
    found = []
    doi = record.get('doi') or record.get('pids', {}).get('doi', {}).get('identifier')
    if doi != manifest['doi']:
        found.append('DOI mismatch: ' + str(doi))
    if record.get('metadata', {}).get('title') != manifest['title']:
        found.append('title mismatch')
    paper = manifest['paper']
    wanted = 'md5:' + paper['md5']
    if not any(f.get('key') == paper['filename'] and f.get('checksum') == wanted for f in record.get('files', [])):
        found.append('PDF filename or MD5 mismatch')
    return found


def main():
    manifest = json.loads((ROOT / 'publication/manifest.json').read_text())
    if manifest['publication_status'] != 'published':
        print('Zenodo record is a draft; no published DOI is claimed.')
        return 0
    try:
        record = fetch(API + str(manifest['record_id']))
    except urllib.error.HTTPError as err:
        print('FAIL: Zenodo record returned HTTP %d' % err.code)
        return 1
    if record is None:
        print('::warning::Zenodo was unreachable after retries; public record not re-verified this run.')
        return 0
    found = problems(manifest, record)
    if found:
        print('FAIL: ' + '; '.join(found))
        return 1
    print('PASS: Zenodo public DOI and PDF checksum match')
    return 0


if __name__ == '__main__':
    sys.exit(main())
