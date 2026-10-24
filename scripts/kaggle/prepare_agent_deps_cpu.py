"""Fetch pinned Habitat-Lab and Python dependencies for offline CPython 3.12."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tarfile
import requests

root = Path('/kaggle/working/havln-agent-deps')
root.mkdir(exist_ok=True)
wheels = root/'wheels'
wheels.mkdir(exist_ok=True)
rev = 'd6ed1c0a0e786f16f261de2beafe347f4186d0d8'
archive = root/'habitat-lab.tar.gz'
r = requests.get('https://codeload.github.com/facebookresearch/habitat-lab/tar.gz/'+rev, timeout=90)
r.raise_for_status()
archive.write_bytes(r.content)
assert hashlib.sha256(r.content).hexdigest() == 'eb9a121a15ed58f788154f4e0ff8db80535b8a07bb057a0927d4ea600db2bf1b'
packages = ['yacs==0.1.8', 'lmdb==1.7.5', 'msgpack-numpy==0.4.8', 'webdataset==0.1.40',
            'braceexpand==0.1.7', 'jsonlines==4.0.0', 'simplejson==3.20.2',
            'decorator==4.4.2', 'proglog==0.1.12', 'gdown==5.2.0']
subprocess.run([sys.executable, '-m', 'pip', 'download', '--no-deps', '--only-binary=:all:',
                '--python-version', '312', '--implementation','cp','--abi','cp312',
                '--platform','manylinux_2_17_x86_64','--platform','manylinux_2_28_x86_64',
                '-d', str(wheels), *packages], check=True)
for name, version in [('gym','0.17.3'), ('dtw','1.4.0'), ('fastdtw','0.3.4'), ('moviepy','1.0.3'), ('ifcfg','0.24'), ('objectio',None)]:
    url = f'https://pypi.org/pypi/{name}/'+(version+'/' if version else '')+'json'
    meta = requests.get(url,timeout=30).json()
    urls = meta['urls']
    source = next((x for x in urls if x['filename'].endswith('none-any.whl')), None)
    source = source or next(x for x in urls if x['packagetype']=='sdist')
    data = requests.get(source['url'],timeout=60)
    data.raise_for_status()
    assert hashlib.sha256(data.content).hexdigest() == source['digests']['sha256']
    (wheels/source['filename']).write_bytes(data.content)
    print('fetched',source['filename'],flush=True)
dest = Path('/kaggle/working/havln-agent-deps.tar.gz')
with tarfile.open(dest,'w:gz') as t:
    t.add(root,arcname='havln-agent-deps')
print('AGENT_DEPS_READY',dest.stat().st_size,flush=True)
