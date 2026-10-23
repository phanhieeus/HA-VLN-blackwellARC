# Reusing the Blackwell runtime cache

The validated runtime cache is a separate artifact from the HA-VLN source repository. It contains four wheels: Habitat-Sim 0.1.7, the matching Magnum/Corrade bindings, NumPy Quaternion, and pybind11. It also records hashes and the tested environment in `manifest.json`; it contains no Matterport data.

The wheel artifact was validated by installing into an isolated target directory with `pip --no-index --no-deps`, then running the Blackwell runtime check and RGB-D scene benchmark successfully. The artifact targets Ubuntu 22.04 + CPython 3.12 (`cp312`), PyTorch 2.10.0+cu128, CUDA 12.8, and RTX PRO 6000 Blackwell. It is not a universal Python 3.11–3.13 wheel: each Python ABI needs a separately built and tested cache.

Attach the runtime-cache artifact as a Kaggle Dataset and install it without network access:

```bash
python scripts/install_blackwell_runtime.py \
  --wheel-dir /kaggle/input/datasets/<owner>/<runtime-cache-dataset>/wheels
source scripts/blackwell_env.sh
python scripts/check_blackwell_runtime.py
```

If that Dataset is not attached, use `scripts/build_habitat_sim_blackwell.py --source /kaggle/working/habitat-sim-v0.1.7`. The build helper routes all compiler output to a log file, selects system pybind11 to avoid the vendored 2.6.2/Python 3.12 incompatibility, and keeps Habitat-Sim pinned at 0.1.7. See [build troubleshooting](blackwell-build-troubleshooting.md).
