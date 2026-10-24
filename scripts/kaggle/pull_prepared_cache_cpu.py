"""Fetch GPU preparation artifacts into the CPU notebook for durable storage."""
from pathlib import Path
import hashlib
import json
import os
import sys

sys.path.insert(0, '/kaggle/working/havln-preparation')
from kaggle_executor import KaggleExecutor

root=Path('/kaggle/working/havln-preparation')
stage=root/'reuse-cache'
stage.mkdir(exist_ok=True)
proxy=json.loads(Path('/tmp/havln-target.json').read_text())['gpu']
ex=KaggleExecutor(proxy)
items={
    'havln-runtime/HA-VLN-blackwellARC-updated.bundle':'HA-VLN-blackwellARC.bundle',
    'havln-runtime/havln-cma-dependencies-cp312.tar':'havln-cma-dependencies-cp312.tar.bin',
    'havln-runtime/complete-cma-cache-manifest.json':'complete-cma-cache-manifest.json',
    'havln-runtime/HAPS2_0.validation.manifest.json':'HAPS2_0.validation.manifest.json',
    'havln-runtime/ckpt.39.pth':'ckpt.39.pth',
    'havln-runtime/validation-metadata.tar.gz':'validation-metadata.tar.gz.bin',
}
checks={}
for remote,name in items.items():
    h=hashlib.sha256()
    dest=stage/name
    with ex.http.get(ex.url('/files/'+remote),stream=True,timeout=(30,120)) as r:
        if r.status_code!=200:
            raise RuntimeError(f'GPU artifact {name}: HTTP {r.status_code}')
        with dest.open('wb') as out:
            for block in r.iter_content(4*1024*1024):
                out.write(block);h.update(block)
    checks[name]={'bytes':dest.stat().st_size,'sha256':h.hexdigest()}
    print('fetched',name,dest.stat().st_size,flush=True)
manifest=json.loads((stage/'complete-cma-cache-manifest.json').read_text())
assert checks['havln-cma-dependencies-cp312.tar.bin']['sha256']==manifest['archive_sha256']
assert checks['ckpt.39.pth']['sha256']=='e70dce940c6ae16aa63c41f3b2411884448a3ccd083b06da156d297b5f4a52dc'
haps=json.loads((stage/'HAPS2_0.validation.manifest.json').read_text())
source=root/'HAPS2_0.validation.zip'
target=stage/'HAPS2_0.validation.zip.bin'
assert source.stat().st_size==haps['bytes']
if not target.exists():
    os.link(source,target)
checks[target.name]={'bytes':haps['bytes'],'sha256':haps['sha256']}
(stage/'checksums.json').write_text(json.dumps(checks,indent=2))
print('PREPARED_CACHE_PULL_COMPLETE',flush=True)
