# Restore the original HA-VLN 2.0 CMA evaluator on Kaggle Blackwell

Use this procedure for Python 3.12 Kaggle Blackwell sessions. The goal is to reuse compiled dependencies and prepared data. See [the offline reference](kaggle-cma-offline-reference.md) for exact files, versions, checksums and observed failures.

## Prepare the session pair

1. Start a GPU notebook with `phnvnh/mp3d-habitat` attached. Obtain its current Jupyter proxy URL.
2. Start a CPU notebook with internet enabled and obtain its proxy URL.
3. Keep proxy credentials in temporary configuration outside Git and outside saved notebook outputs.
4. Confirm both APIs respond, GPU Python is 3.12, the device is Blackwell, and the mounted Matterport directory has 90 scans.
5. Inspect `/kaggle/working` before assuming any previous files survived. A notebook session and a saved artifact are different things.

## Restore files and install offline

The prepared private Dataset [`phnvnh/havln2-validation-cache`](https://www.kaggle.com/datasets/phnvnh/havln2-validation-cache) contains 10 files, verified using authenticated Kaggle listing. On the next matching GPU session, attach that Dataset and `mp3d-habitat`, then run:

```python
from pathlib import Path
import subprocess, sys
cache = Path('/kaggle/input/datasets/phnvnh/havln2-validation-cache')
subprocess.run([sys.executable, str(cache / 'restore_havln_cache.py'), str(cache)], check=True)
```

The restoration script validates the Python/tensor-stack profile and dependency archive hash, installs offline wheels, restores source and weights, links Matterport, and extracts HAPS once. It prints the environment variables and the original evaluation command. In an already restored workspace, it reuses the extraction marker. Use `--verify-existing` to recheck existing mesh CRCs when investigating corruption.

Clean-session attachment and complete restoration have not yet been timed. A new session still needs local extraction. Generated dynamic navmeshes are not included in this first prepared Dataset; retain them separately after full evaluation.

The numbered procedure below describes the individual operations and provides recovery steps when reconstructing this cache.

1. Relay the Git bundle and native runtime release from the CPU notebook. Clone the bundle on the GPU into `/kaggle/working/HA-VLN`, branch `blackwell-py311-313`.
2. Install the four native runtime wheels from the matching CPython 3.12 release.
3. Restore the verified Habitat-Lab archive, extract it under `/kaggle/working/havln-runtime/habitat-lab`, and add the extracted source root to a site-packages `.pth` file. This provides both `habitat` and `habitat_baselines`.
4. Install the complete agent wheel set listed in the offline reference. Use built dtw, fastdtw, gym and moviepy wheels. Pin `webdataset==0.1.40`.
5. Restore validation metadata under repository `Data/`. Restore the released CMA checkpoint to the exact agent checkpoint path.
6. Restore the RGB ResNet weight under `/kaggle/working/havln-runtime/torch-cache/hub/checkpoints/`. Verify its checksum.
7. Relay the prepared HAPS subset ZIP in resumable, checksum-namespaced parts. Verify the assembled ZIP SHA-256 before deleting transfer parts.
8. Extract with the repository's `scripts/download_hf.py:unpack_haps`. It removes the outer `human_motion_glbs_v3` directory so the expected path becomes `Data/HAPS2_0/<motion>/frame*.glb`.
9. Verify extraction marker and file count. Remove the compressed GPU copy only after verification and while a source copy remains available.
10. Link `Data/scene_datasets/mp3d` to the read-only Matterport input. Keep `Data/recompute_navmesh` writable. Restore compatible existing navmeshes when available.

The first native runtime release alone is incomplete for CMA. A complete reusable cache also needs the agent wheels, Habitat-Lab source, RGB initializer and validation inputs.

## Check readiness

Run from the repository root:

```bash
source scripts/blackwell_env.sh
export TORCH_HOME=/kaggle/working/havln-runtime/torch-cache
python scripts/check_blackwell_runtime.py
cd agent
python run.py --help
```

`--help` verifies imports only. Also check all data and pretrained-weight paths. A one-episode trial checks policy construction and simulator interaction; use a separate `RESULTS_DIR` so its JSON cannot be mistaken for a full evaluation result.

Retain the NumPy JSON export compatibility fix documented in the reference. It must not change metric calculations.

## Run the README evaluation commands

From the repository root, run unseen evaluation:

```bash
source scripts/blackwell_env.sh
export TORCH_HOME=/kaggle/working/havln-runtime/torch-cache
cd agent
python -u run.py --exp-config config/cma_pm_da_aug_tune.yaml --run-type eval \
  MODEL.DEPTH_ENCODER.ddppo_checkpoint NONE VIDEO_OPTION "[]"
```

Use the same command with `EVAL.SPLIT val_seen` appended for seen validation. Full evaluation keeps default `NUM_ENVIRONMENTS: 4` and `EVAL.EPISODE_COUNT: -1`.

Check process exit status and parse the resulting JSON. Expected output files are under `agent/VLN-CE/data/checkpoints/cma_pm_da_aug_tune/evals/`. A progress bar reaching 100% is insufficient if JSON export later fails.

## Save preparation for the next session

Retain compiled wheels, verified source archives, RGB weights, Git bundle, HAPS subset manifest, validation files, checkpoint and generated navmeshes. The original 1.3 TB Matterport release is unnecessary for this Habitat workflow.

The complete dependency cache is now in the private prepared Dataset, and its 10-file listing was verified. GitHub's earlier native runtime release remains a smaller simulator-only artifact. The prepared Dataset's Git bundle pins evaluator commit `22da693`; source and docs are also available on branch `blackwell-py311-313`.

For fresh notebooks, a private Kaggle cache containing a small number of opaque archive files can avoid indexing tens of thousands of HAPS input files. Use names such as `.zip.bin` when automatic expansion would defeat that packaging. Benchmark attachment and extraction time before claiming a startup improvement. Prepared archives still require extraction in a clean session.

For repeated runs in the same live session, reuse the extracted directory and generated navmeshes. For notebook output reuse, save the prepared working files explicitly and verify the saved version is accessible. A Git push preserves source and docs; it does not preserve installed packages or large data.

## Inspect the current run

Current GPU paths:

| Path under `/kaggle/working/havln-runtime` | Contents |
| --- | --- |
| `evaluation-status.json` | Current split, running/completed/failed state and command |
| `eval-val_unseen.log`, `eval-val_seen.log` | Original evaluator stdout/stderr |
| `eval-driver.log` | Sequential split launcher status |
| `gpu-telemetry.csv` | GPU utilization, memory and power samples |
| `agent-install.log` | Legacy wheel build log |
| `extract.log` | HAPS extraction verification |
| `HAPS2_0.validation.manifest.json` | Subset checksum, expanded bytes and source provenance |

Before stopping GPU, check evaluation state, save metrics/logs, and verify the durable preparation cache exists. GPU utilization alone cannot distinguish setup, rendering and policy inference.
