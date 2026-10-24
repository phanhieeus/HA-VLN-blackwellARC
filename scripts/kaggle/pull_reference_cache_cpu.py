"""Save GPU reference results and derived navmeshes on the internet CPU notebook."""
from pathlib import Path
import ast
import hashlib
import json
import sys

sys.path.insert(0,'/kaggle/working/havln-preparation')
from kaggle_executor import KaggleExecutor

stage=Path('/kaggle/working/havln-navmesh-cache')
stage.mkdir(exist_ok=True)
cfg=json.loads(Path('/tmp/havln-target.json').read_text())
ex=KaggleExecutor(cfg['gpu'])
for name,dest in [('navmesh-cache.tar.gz','navmesh-cache.tar.gz.bin'),
                  ('navmesh-cache-manifest.json','navmesh-cache-manifest.json'),
                  ('reference-results.tar.gz','reference-results.tar.gz.bin')]:
    with ex.http.get(ex.url('/files/havln-runtime/'+name),stream=True,timeout=(30,120)) as response:
        if response.status_code!=200:raise RuntimeError(f'Cannot fetch {name}: HTTP {response.status_code}')
        with (stage/dest).open('wb') as out:
            for block in response.iter_content(4*1024*1024):out.write(block)
    print('PRESERVED',dest,(stage/dest).stat().st_size,flush=True)
manifest=json.loads((stage/'navmesh-cache-manifest.json').read_text())
assert hashlib.sha256((stage/'navmesh-cache.tar.gz.bin').read_bytes()).hexdigest()==manifest['archive_sha256']
response=ex.http.get(ex.url('/files/HA-VLN/HASimulator/environments.py'),timeout=30)
response.raise_for_status()
cls=next(n for n in ast.parse(response.text).body if isinstance(n,ast.ClassDef) and n.name=='HAVLNCE')
method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_handle_signals')
manifest['navmesh_algorithm_sha256']=hashlib.sha256(ast.dump(method,include_attributes=False).encode()).hexdigest()
runtime=json.loads(Path('/kaggle/working/havln-preparation/reuse-cache/complete-cma-cache-manifest.json').read_text())
manifest['complete_runtime_archive_sha256']=runtime['archive_sha256']
(stage/'navmesh-cache-manifest.json').write_text(json.dumps(manifest,indent=2))
print('REFERENCE_AND_NAVMESH_PRESERVED_SHA_VERIFIED',flush=True)
