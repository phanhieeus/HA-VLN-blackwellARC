#!/usr/bin/env python3
"""Validate the Blackwell + Habitat-Sim runtime without loading benchmark data."""
import argparse
import importlib.metadata
import platform
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--imports-only", action="store_true", help=argparse.SUPPRESS)
    parser.parse_args()
    if not (3, 11) <= sys.version_info[:2] < (3, 14):
        raise SystemExit(f"Expected Python 3.11–3.13, found {platform.python_version()}")
    import torch
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is unavailable; use a GPU runtime")
    capability = torch.cuda.get_device_capability(0)
    if capability[0] < 12:
        raise SystemExit(f"Expected Blackwell compute capability >= 12.0, found {capability}")
    cuda_version = tuple(int(part) for part in torch.version.cuda.split(".")[:2])
    if cuda_version < (12, 8):
        raise SystemExit(f"Blackwell requires a CUDA 12.8+ PyTorch build; found {torch.version.cuda}")
    import habitat_sim
    try:
        sim_version = importlib.metadata.version("habitat-sim")
    except importlib.metadata.PackageNotFoundError:
        sim_version = getattr(habitat_sim, "__version__", "unknown")
    if sim_version != "0.1.7":
        raise SystemExit(f"HA-VLN 2.0 requires Habitat-Sim 0.1.7; found {sim_version}")
    print(f"Python: {platform.python_version()}")
    print(f"PyTorch: {torch.__version__} (CUDA {torch.version.cuda})")
    print(f"GPU: {torch.cuda.get_device_name(0)} (compute capability {capability})")
    print(f"Habitat-Sim: {sim_version}")
    print(f"NumPy: {__import__('numpy').__version__}")
    print("Core GPU runtime imports passed. Supply an authorized Matterport scene to benchmark rendering or run evaluation.")


if __name__ == "__main__":
    main()
