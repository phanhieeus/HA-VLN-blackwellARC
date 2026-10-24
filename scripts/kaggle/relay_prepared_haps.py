"""Relay a prepared, verified local CPU-notebook ZIP directly to a GPU notebook.

Credentials live only in /tmp/havln-target.json. Parts use the source SHA256 as
their namespace, permitting resume and preventing cross-version cache reuse.
"""
import concurrent.futures
import hashlib
import json
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote

import requests

from kaggle_executor import KaggleExecutor

ROOT = Path('/kaggle/working/havln-preparation')
manifest = json.loads((ROOT / 'validation-cache-manifest.json').read_text())
source = Path(manifest['file'])
proxy = json.loads(Path('/tmp/havln-target.json').read_text())['gpu']
executor = KaggleExecutor(proxy)
directory = f"havln-runtime/parts-{manifest['sha256'][:16]}"
executor.ensure_dir(directory)
known = {i['name']: i.get('size') for i in executor.list_path(directory)}
chunk = 24 * 1024 * 1024
total = manifest['bytes']
local = threading.local()
lock = threading.Lock()
done = 0
started = time.monotonic()


def worker(offset):
    global done
    size = min(chunk, total-offset)
    name = f'part_{offset:012d}.bin'
    if known.get(name) != size:
        import base64
        if not hasattr(local, 'http'):
            local.http = requests.Session()
            local.http.cookies.update(executor.http.cookies)
        with source.open('rb') as stream:
            stream.seek(offset)
            data = stream.read(size)
        if len(data) != size:
            raise RuntimeError('Source short read')
        payload = {'type': 'file', 'format': 'base64',
                   'content': base64.b64encode(data).decode('ascii')}
        for attempt in range(6):
            try:
                r = local.http.put(executor.url('/api/contents/' + quote(directory+'/'+name, safe='/')),
                                   headers=executor._xsrf(), json=payload, timeout=(30, 120))
                if r.status_code == 404:
                    raise RuntimeError('Target returned HTTP 404; stop and inspect session')
                if r.status_code >= 400:
                    raise requests.RequestException(f'HTTP {r.status_code}')
                break
            except requests.RequestException as exc:
                if attempt == 5:
                    raise RuntimeError(f'Part {offset} failed: {type(exc).__name__}') from None
                time.sleep(min(2**attempt, 16))
    with lock:
        done += size


with concurrent.futures.ThreadPoolExecutor(4) as pool:
    futures = [pool.submit(worker, i) for i in range(0, total, chunk)]
    while not all(f.done() for f in futures):
        print(f'relay {done/1e9:.2f}/{total/1e9:.2f} GB '
              f'{done/1e6/max(time.monotonic()-started,1):.1f} MB/s', flush=True)
        failed = [f for f in futures if f.done() and f.exception()]
        if failed:
            for f in futures:
                f.cancel()
            failed[0].result()
        time.sleep(10)
    for f in futures:
        f.result()

destination = '/kaggle/working/havln-runtime/HAPS2_0.validation.zip'
code = f'''
from pathlib import Path
import hashlib, json, shutil
parts=Path('/kaggle/working')/{directory!r}
dest=Path({destination!r})
digest=hashlib.sha256()
with dest.open('wb') as out:
    for offset in range(0,{total},{chunk}):
        part=parts/f'part_{{offset:012d}}.bin'
        if part.stat().st_size!=min({chunk},{total}-offset):
            raise RuntimeError('Invalid part size')
        with part.open('rb') as f:
            for block in iter(lambda:f.read(8*1024*1024),b''):
                out.write(block); digest.update(block)
if dest.stat().st_size!={total} or digest.hexdigest()!={manifest['sha256']!r}:
    raise RuntimeError('Assembled archive SHA256 mismatch; preserving parts')
Path('/kaggle/working/havln-runtime/HAPS2_0.validation.manifest.json').write_text({json.dumps(manifest,indent=2)!r})
shutil.rmtree(parts)
print('ASSEMBLED_SHA256_VERIFIED',dest.stat().st_size,digest.hexdigest())
'''
kid = executor.get_or_create_kernel()
output = executor.execute(kid, code, timeout=600, silent=True)
print(output.replace(proxy, '[KAGGLE_PROXY]'), flush=True)
if 'ASSEMBLED_SHA256_VERIFIED' not in output:
    raise RuntimeError('Assembly did not report verified completion')
print(f'RELAY_COMPLETE seconds={time.monotonic()-started:.1f}', flush=True)
