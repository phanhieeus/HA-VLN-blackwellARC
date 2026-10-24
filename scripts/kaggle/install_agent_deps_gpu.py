"""Build/cache legacy dependencies once in the actual GPU Python ABI."""
from pathlib import Path
import subprocess
import sys
import tarfile

base = Path('/kaggle/working/havln-agent-deps')
wheels = base/'wheels'
sources = base/'build-sources'
sources.mkdir(exist_ok=True)
for archive in sorted(wheels.glob('*.tar.gz')):
    tarfile.open(archive).extractall(sources, filter='data')
    source = sources/archive.name[:-7]
    if archive.name.startswith('dtw-'):
        setup = source/'setup.py'
        setup.write_text(setup.read_text().replace('import imp', 'import runpy, types').replace(
            "imp.load_source('dtw.version', 'dtw/version.py')",
            "types.SimpleNamespace(**runpy.run_path('dtw/version.py'))"))
    if archive.name.startswith('gym-'):
        setup = source/'setup.py'
        setup.write_text(setup.read_text().replace('opencv-python>=3.', 'opencv-python>=3.0'))
    print('BUILD',archive.name,flush=True)
    build = subprocess.run([sys.executable,'-m','pip','wheel','--no-index','--no-deps',
                            '--no-build-isolation','-w',str(wheels),str(source)])
    if build.returncode:
        raise SystemExit(build.returncode)
    name = archive.name.split('-')[0]
    wheel = next(wheels.glob(name+'-*.whl'))
    subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps',str(wheel)],check=True)
print('AGENT_LEGACY_WHEELS_READY',flush=True)
