"""Preserve the complete installed CMA dependencies as offline wheels and weights."""
from pathlib import Path
import hashlib
import importlib.metadata as metadata
import json
import platform
import subprocess
import tarfile
from packaging.utils import parse_wheel_filename, canonicalize_name

root = Path('/kaggle/working')
runtime = root/'havln-runtime'
agent = root/'havln-agent-deps'
native = runtime/'cache/havln-blackwell-runtime-cp312-ubuntu2204/wheels'
destination = runtime/'havln-cma-dependencies-cp312.tar'
selected = {}
for wheel in [*native.glob('*.whl'), *(agent/'wheels').glob('*.whl')]:
    name, version, _, _ = parse_wheel_filename(wheel.name)
    try:
        installed = metadata.version(name)
    except metadata.PackageNotFoundError:
        continue
    if str(version) == installed:
        selected[name] = wheel
manifest = {
    'python': platform.python_version(), 'platform': platform.platform(),
    'wheels': {name: {'file': p.name, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                      'installed':metadata.version(name)} for name,p in sorted(selected.items())},
    'preinstalled_versions': {name:metadata.version(name) for name in ['torch','torchvision','numpy','scipy','numba','attrs','PyYAML','msgpack','Pillow','tensorboard','tensorflow','tqdm','imageio','imageio-ffmpeg']},
    'habitat_lab_revision':'d6ed1c0a0e786f16f261de2beafe347f4186d0d8',
    'torch_home':'/kaggle/working/havln-runtime/torch-cache',
}
installer = '''
from pathlib import Path
import hashlib,json,subprocess,sys,site,tarfile
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
assert sys.version_info[:2]==(3,12),'Cache requires CPython 3.12'
wheels=[]
for item in manifest['wheels'].values():
    p=root/'wheels'/item['file']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],p.name
    wheels.append(str(p))
subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps',*wheels],check=True)
lab=root/'habitat-lab'
lab.mkdir(exist_ok=True)
tarfile.open(root/'habitat-lab.tar.gz').extractall(lab,filter='data')
source=next(lab.glob('habitat-lab-*'))
Path(site.getsitepackages()[0],'havln_lab.pth').write_text(str(source)+'\\n')
print('CMA cache installed. Set TORCH_HOME='+str(root/'torch-cache'))
'''
with tarfile.open(destination,'w') as archive:
    for p in selected.values():
        archive.add(p,arcname='havln-cma-cache/wheels/'+p.name)
    archive.add(agent/'habitat-lab.tar.gz',arcname='havln-cma-cache/habitat-lab.tar.gz')
    archive.add(runtime/'torch-cache/hub/checkpoints/resnet50-0676ba61.pth',
                arcname='havln-cma-cache/torch-cache/hub/checkpoints/resnet50-0676ba61.pth')
    import io
    for name, content in [('manifest.json',json.dumps(manifest,indent=2)),('install.py',installer)]:
        data=content.encode(); info=tarfile.TarInfo('havln-cma-cache/'+name); info.size=len(data)
        archive.addfile(info,io.BytesIO(data))
digest=hashlib.sha256()
with destination.open('rb') as f:
    for block in iter(lambda:f.read(8*1024*1024),b''):
        digest.update(block)
manifest['archive_bytes']=destination.stat().st_size
manifest['archive_sha256']=digest.hexdigest()
(runtime/'complete-cma-cache-manifest.json').write_text(json.dumps(manifest,indent=2))
print('COMPLETE_CMA_CACHE_PACKAGED',manifest['archive_bytes'],manifest['archive_sha256'],flush=True)
