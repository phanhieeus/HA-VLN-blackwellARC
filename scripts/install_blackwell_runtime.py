#!/usr/bin/env python3
"""Install the matching offline Blackwell runtime wheels from an artifact folder."""
import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wheel-dir', type=Path, required=True, help='Directory containing the runtime cache wheels')
    parser.add_argument('--log', type=Path, default=Path('/kaggle/working/habitat-sim-install.log'))
    args = parser.parse_args()
    abi = f'cp{sys.version_info.major}{sys.version_info.minor}'
    patterns = (
        f'habitat_sim-0.1.7-{abi}-{abi}-linux_x86_64.whl',
        f'magnum-0.0.0-{abi}-{abi}-linux_x86_64.whl',
        f'numpy_quaternion-*-{abi}-{abi}-*.whl',
        'pybind11-*.whl',
    )
    wheels = []
    for pattern in patterns:
        matches = sorted(args.wheel_dir.glob(pattern))
        if not matches:
            raise SystemExit(f'No wheel matching {pattern!r} in {args.wheel_dir}; this artifact is ABI-specific')
        wheels.append(matches[0])
    args.log.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps', '--force-reinstall', *map(str, wheels)]
    with args.log.open('w', encoding='utf-8') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    print(f'Install exit code: {result.returncode}')
    tail = subprocess.run(['tail', '-n', '20', str(args.log)], capture_output=True, text=True)
    print(tail.stdout)
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
