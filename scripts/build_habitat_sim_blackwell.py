#!/usr/bin/env python3
"""Build the pinned Habitat-Sim 0.1.7 wheel for a modern Blackwell runtime."""
import argparse
import importlib.metadata
import os
import platform
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True, help='Extracted Habitat-Sim 0.1.7 source directory')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--log', type=Path, default=Path('/kaggle/working/habitat-sim-build.log'))
    args = parser.parse_args()
    if not (3, 11) <= sys.version_info[:2] < (3, 14):
        raise SystemExit(f'Expected Python 3.11–3.13; found {platform.python_version()}')
    if not (args.source / 'setup.py').is_file():
        raise SystemExit(f'No setup.py under {args.source}; extract the pinned Habitat-Sim 0.1.7 source first')
    try:
        import pybind11
        pybind_version = importlib.metadata.version('pybind11')
    except Exception as exc:
        raise SystemExit(f'Install a CPython-compatible pybind11 wheel before building: {exc}')
    if args.jobs < 1:
        parser.error('--jobs must be positive')

    env = os.environ.copy()
    env['CMAKE_BUILD_PARALLEL_LEVEL'] = str(args.jobs)
    env['MAX_JOBS'] = str(args.jobs)
    env['CMAKE_ARGS'] = f'-DUSE_SYSTEM_PYBIND11=ON -Dpybind11_DIR={pybind11.get_cmake_dir()}'
    command = [sys.executable, 'setup.py', 'bdist_wheel', '--headless', '--with-cuda', '--force-cmake']
    args.log.parent.mkdir(parents=True, exist_ok=True)
    print(f'Python: {platform.python_version()} | pybind11: {pybind_version}')
    print(f'Command: {" ".join(command)}')
    print(f'Log: {args.log}')
    with args.log.open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=args.source, env=env, stdout=log, stderr=subprocess.STDOUT)
    print(f'Build exit code: {result.returncode}')
    try:
        tail = subprocess.run(['tail', '-n', '35', str(args.log)], capture_output=True, text=True)
        print(tail.stdout)
    except FileNotFoundError:
        pass
    wheels = sorted((args.source / 'dist').glob('habitat_sim-0.1.7-*.whl'))
    for wheel in wheels:
        print(f'Wheel: {wheel} ({wheel.stat().st_size:,} bytes)')
    if result.returncode:
        raise SystemExit(result.returncode)
    if not wheels:
        raise SystemExit('Build returned success but produced no Habitat-Sim 0.1.7 wheel')


if __name__ == '__main__':
    main()
