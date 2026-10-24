"""Prepare the pinned validation HAPS cache on an internet-enabled Kaggle CPU.

Input manifest is produced from the locally checked validation subset. Original
compressed ZIP records are copied intact; mesh and animation contents never change.
"""
import concurrent.futures
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import zipfile

import requests

ROOT = Path('/kaggle/working/havln-preparation')
ROOT.mkdir(exist_ok=True)
SOURCE = ROOT / 'HAPS2_0.original.zip'
SUBSET = ROOT / 'HAPS2_0.validation.zip'
URL = ('https://huggingface.co/datasets/fly1113/HA-VLN/resolve/'
       'c5f1cec167964bda3ba343acc3a18e7aef8540dd/HAPS2_0/HAPS2_0.zip?download=true')
SIZE = 8332789125
SHA = 'c5bc75ffcec1b1b83b9ffc1f7177a02fabcdacbb6a0a7a02368afa5bbc209741'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(16 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def download():
    if SOURCE.exists() and SOURCE.stat().st_size == SIZE and digest(SOURCE) == SHA:
        print('Reusing verified original archive', flush=True)
        return
    fd = os.open(SOURCE, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
    os.ftruncate(fd, SIZE)
    progress = [0] * 4
    started = time.monotonic()

    def worker(index):
        start, end = SIZE * index // 4, SIZE * (index + 1) // 4
        offset = start
        for attempt in range(6):
            try:
                with requests.get(URL, headers={'Range': f'bytes={offset}-{end-1}'},
                                  stream=True, timeout=(30, 90)) as r:
                    r.raise_for_status()
                    if r.status_code != 206 or not r.headers.get('Content-Range', '').startswith(f'bytes {offset}-'):
                        raise RuntimeError('Source did not honor byte range')
                    for block in r.iter_content(4 * 1024 * 1024):
                        if offset + len(block) > end:
                            raise RuntimeError('Source exceeded requested range')
                        view = memoryview(block)
                        while view:
                            n = os.pwrite(fd, view, offset)
                            offset += n
                            view = view[n:]
                        progress[index] = offset - start
                if offset == end:
                    return
            except requests.RequestException as exc:
                print(f'Download worker {index} retry {attempt+1}: {type(exc).__name__}', flush=True)
                time.sleep(min(2 ** attempt, 16))
        raise RuntimeError(f'Download worker {index} incomplete at {offset}')

    try:
        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            futures = [pool.submit(worker, i) for i in range(4)]
            while not all(f.done() for f in futures):
                done = sum(progress)
                print(f'download {done/1e9:.2f}/{SIZE/1e9:.2f} GB '
                      f'{done/1e6/max(time.monotonic()-started,1):.1f} MB/s', flush=True)
                time.sleep(10)
            for f in futures:
                f.result()
    finally:
        os.close(fd)
    actual = digest(SOURCE)
    if actual != SHA:
        raise RuntimeError('Original archive SHA256 mismatch')
    print('Original archive SHA256 verified', flush=True)


def subset():
    selection = ROOT / 'validation-haps-entries.json.gz'
    if not selection.exists():
        # Recovery path when the independently prepared local whitelist is absent.
        base = ('https://huggingface.co/datasets/fly1113/HA-VLN/resolve/'
                'c5f1cec167964bda3ba343acc3a18e7aef8540dd/')
        scenes = set()
        for split in ['val_seen', 'val_unseen']:
            response = requests.get(base+f'HA-R2R/{split}/{split}.json.gz', timeout=60)
            response.raise_for_status()
            episodes = json.loads(gzip.decompress(response.content))['episodes']
            scenes.update(ep['scene_id'].split('/')[1] for ep in episodes)
        url = ('https://raw.githubusercontent.com/UWMILab/HA-VLN/'
               'f46f93642d7ab96cc49611f8cfea09cecf2fa7f9/Data/Multi-Human-Annotations/human_motion.json')
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        annotations = response.json()
        sequences = {f"{motion['category']}_{int(motion['index'])}"
                     for scene in scenes for motion in annotations.get(scene, {}).values()}
        if len(scenes) != 64 or len(sequences) != 383:
            raise RuntimeError('Validation selection differs from the verified cache profile')
        with zipfile.ZipFile(SOURCE) as archive:
            entries = [dict(name=i.filename, crc=i.CRC, size=i.file_size)
                       for i in archive.infolist()
                       if i.filename == 'human_motion_glbs_v3/' or
                       (i.filename.startswith('human_motion_glbs_v3/') and
                        len(i.filename.split('/')) > 1 and i.filename.split('/')[1] in sequences)]
        if len(entries) != 92304:
            raise RuntimeError('Unexpected validation ZIP entry count')
        with gzip.open(selection, 'wt') as stream:
            json.dump(entries, stream)
    with gzip.open(ROOT / 'validation-haps-entries.json.gz', 'rt') as f:
        expected = {i['name']: i for i in json.load(f)}
    with zipfile.ZipFile(SOURCE) as src, zipfile.ZipFile(SUBSET, 'w', allowZip64=True) as dst:
        infos = sorted(src.infolist(), key=lambda i: i.header_offset)
        found = set()
        with SOURCE.open('rb') as raw:
            for pos, info in enumerate(infos):
                if info.filename not in expected:
                    continue
                entry = expected[info.filename]
                if info.CRC != entry['crc'] or info.file_size != entry['size']:
                    raise RuntimeError(f'Validation manifest mismatch: {info.filename}')
                stop = infos[pos+1].header_offset if pos+1 < len(infos) else src.start_dir
                raw.seek(info.header_offset)
                if raw.read(4) != b'PK\x03\x04':
                    raise RuntimeError('Invalid ZIP local header')
                raw.seek(info.header_offset)
                new_info = copy.copy(info)
                new_info.header_offset = dst.fp.tell()
                remaining = stop - info.header_offset
                while remaining:
                    block = raw.read(min(8 * 1024 * 1024, remaining))
                    if not block:
                        raise RuntimeError('Truncated original ZIP')
                    dst.fp.write(block)
                    remaining -= len(block)
                dst.filelist.append(new_info)
                dst.NameToInfo[new_info.filename] = new_info
                found.add(info.filename)
        dst.start_dir = dst.fp.tell()
        dst._didModify = True
        if found != set(expected):
            raise RuntimeError(f'Missing {len(set(expected)-found)} required entries')
    with zipfile.ZipFile(SUBSET) as z:
        if z.testzip() is not None:
            raise RuntimeError('Subset CRC validation failed')
    result = {'bytes': SUBSET.stat().st_size, 'sha256': digest(SUBSET),
              'entries': len(expected), 'uncompressed_bytes': sum(x['size'] for x in expected.values()),
              'original_sha256': SHA, 'file': str(SUBSET)}
    (ROOT / 'validation-cache-manifest.json').write_text(json.dumps(result, indent=2))
    print('PREPARED', json.dumps(result), flush=True)


if __name__ == '__main__':
    download()
    subset()
