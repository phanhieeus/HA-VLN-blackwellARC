"""Snapshot complete evaluation evidence and derived navmesh cache."""
from pathlib import Path
import hashlib
import json
import tarfile
import io

root=Path('/kaggle/working')
repo=root/'HA-VLN'
runtime=root/'havln-runtime'
nav=repo/'Data/recompute_navmesh'
files=list(nav.rglob('*.navmesh'))
manifest={'files':len(files),'bytes':sum(p.stat().st_size for p in files),
          'habitat_sim':'0.1.7','agent_radius':0.1,'agent_height':1.5,'include_static_objects':True,
          'human_motion_sha256':hashlib.sha256((repo/'Data/Multi-Human-Annotations/human_motion.json').read_bytes()).hexdigest(),
          'haps_subset_sha256':'13693f457c8b52e490beaccc99d688bdd71d7b355df5711c5dcee16c2d1301f4',
          'matterport_archive_sha256':'470948ee78ff4d6dc4c4870395d1e790a0f15c72065d1f62cdd229b2bcbe0d36',
          'reference_envs':4,'source_evaluator_commit':'22da693a489e2a0f9acf2df740f139518a647c5a'}
archive=runtime/'navmesh-cache.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=1) as t:
    t.add(nav,arcname='Data/recompute_navmesh')
    b=json.dumps(manifest,indent=2).encode();info=tarfile.TarInfo('navmesh-cache-manifest.json');info.size=len(b);t.addfile(info,io.BytesIO(b))
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
manifest.update(archive_bytes=archive.stat().st_size,archive_sha256=digest)
(runtime/'navmesh-cache-manifest.json').write_text(json.dumps(manifest,indent=2))
print('NAVMESH_SNAPSHOT_READY',json.dumps(manifest),flush=True)
with tarfile.open(runtime/'reference-results.tar.gz','w:gz',compresslevel=1) as t:
    results=repo/'agent/VLN-CE/data/checkpoints/cma_pm_da_aug_tune/evals'
    for p in results.glob('*.json'):
        t.add(p,arcname='results/'+p.name)
    for name in ['eval-val_unseen.log','eval-val_seen.log','evaluation-status.json','gpu-telemetry.csv','complete-cma-cache-manifest.json']:
        t.add(runtime/name,arcname=name)
print('REFERENCE_SNAPSHOT_READY',flush=True)
