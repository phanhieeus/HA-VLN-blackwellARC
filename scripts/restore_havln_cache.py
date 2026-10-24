"""Restore prepared HA-VLN CMA assets; evaluation remains upstream agent/run.py."""
import argparse
import hashlib
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile


def sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('cache',type=Path,help='Attached private prepared-cache dataset directory')
    p.add_argument('--workspace',type=Path,default=Path('/kaggle/working'))
    p.add_argument('--mp3d',type=Path,default=Path('/kaggle/input/datasets/phnvnh/mp3d-habitat/mp3d_habitat/mp3d'))
    p.add_argument('--verify-existing',action='store_true',help='Recheck CRCs of already extracted HAPS files')
    args=p.parse_args()
    if sys.version_info[:2]!=(3,12):
        p.error('Prepared native wheels require CPython 3.12')
    cache=args.cache.resolve(strict=True)
    work=args.workspace.resolve(strict=True)
    if not args.mp3d.is_dir() or len(list(args.mp3d.glob('*/*.glb')))!=90:
        p.error('Attach the private mp3d-habitat dataset and supply its 90-scene directory')
    manifest=json.loads((cache/'complete-cma-cache-manifest.json').read_text())
    for package in ['torch','torchvision','numpy']:
        expected=manifest['preinstalled_versions'][package]
        if importlib.metadata.version(package)!=expected:
            raise RuntimeError(f'Cache profile mismatch for {package}: expected {expected}')
    artifact=cache/'havln-cma-dependencies-cp312.tar.bin'
    if artifact.stat().st_size!=manifest['archive_bytes'] or sha256(artifact)!=manifest['archive_sha256']:
        raise RuntimeError('CMA dependency archive failed checksum verification')
    runtime=work/'havln-cma-cache'
    receipt=runtime/'installed-source-sha256.txt'
    if not receipt.exists() or receipt.read_text().strip()!=manifest['archive_sha256']:
        with tarfile.open(artifact) as archive:
            archive.extractall(work,filter='data')
        subprocess.run([sys.executable,str(runtime/'install.py')],check=True)
        receipt.write_text(manifest['archive_sha256']+'\n')
    repo=work/'HA-VLN'
    if not repo.exists():
        subprocess.run(['git','clone','--branch','blackwell-py311-313',str(cache/'HA-VLN-blackwellARC.bundle'),str(repo)],check=True)
    with tarfile.open(cache/'validation-metadata.tar.gz.bin') as archive:
        archive.extractall(repo,filter='data')
    checkpoint=cache/'ckpt.39.pth'
    if sha256(checkpoint)!='e70dce940c6ae16aa63c41f3b2411884448a3ccd083b06da156d297b5f4a52dc':
        raise RuntimeError('CMA checkpoint checksum mismatch')
    target=repo/'agent/VLN-CE/data/checkpoints/cma_pm_da_aug_tune/CMA_PM_DA_Aug.pth'
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        target.symlink_to(checkpoint)
    elif sha256(target)!=sha256(checkpoint):
        raise RuntimeError('Existing checkpoint differs; preserve it and choose a separate workspace')
    scenes=repo/'Data/scene_datasets/mp3d'
    scenes.parent.mkdir(parents=True,exist_ok=True)
    if not scenes.exists():
        scenes.symlink_to(args.mp3d.resolve(),target_is_directory=True)
    elif scenes.resolve()!=args.mp3d.resolve():
        raise RuntimeError('Existing Matterport path differs from the requested mount')
    haps=json.loads((cache/'HAPS2_0.validation.manifest.json').read_text())
    marker=repo/'Data/downloads/haps-extracted.json'
    expected={'sha256':haps['sha256'],'files':91920}
    existing=json.loads(marker.read_text()) if marker.exists() else None
    if existing!=expected or args.verify_existing:
        marker.parent.mkdir(exist_ok=True)
        module_path=repo/'scripts/download_hf.py'
        spec=importlib.util.spec_from_file_location('havln_download',module_path)
        module=importlib.util.module_from_spec(spec)
        sys.path.insert(0,str(module_path.parent))
        spec.loader.exec_module(module)
        module.unpack_haps(cache/'HAPS2_0.validation.zip.bin',repo/'Data',haps['sha256'])
    print('RESTORE_READY',repo,flush=True)
    print('Run the upstream evaluator from agent, with TORCH_HOME='+str(runtime/'torch-cache'))
    print('source '+str(repo/'scripts/blackwell_env.sh'))
    print('export TORCH_HOME='+str(runtime/'torch-cache'))
    print('cd '+str(repo/'agent'))
    print('python run.py --exp-config config/cma_pm_da_aug_tune.yaml --run-type eval MODEL.DEPTH_ENCODER.ddppo_checkpoint NONE VIDEO_OPTION "[]"')


if __name__=='__main__':
    main()
