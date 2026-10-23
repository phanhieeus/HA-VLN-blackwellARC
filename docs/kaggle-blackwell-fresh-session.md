# Fresh Kaggle Blackwell session runbook

This runbook restores the HA-VLN Blackwell workspace in a new Kaggle session without rebuilding Habitat-Sim, provided the release assets and the same CPython 3.12 Kaggle image are used.

## One-time preparation

The `runtime-cp312-blackwell-2026-10-24` GitHub Release is intended to contain:

- `HA-VLN-blackwellARC.bundle` â€” a full Git bundle, including the `blackwell-py311-313` branch and its history.
- `havln-blackwell-runtime-cp312-ubuntu2204.tar.gz` â€” the tested offline wheels and manifest.

Keep the Matterport Dataset private as `phnvnh/mp3d-habitat`. Do not include the Matterport archive in a GitHub Release or the repository. A private Kaggle Dataset named for the runtime cache is an alternative to the release asset if you prefer Kaggle-managed reuse.

## Restore a new session

1. In the Kaggle account that owns `mp3d-habitat`, create/start a Blackwell GPU notebook with Internet **off**. Attach the private `mp3d-habitat` Dataset. Do not extract another copy into `/kaggle/working`.
2. Start an Internet-enabled CPU notebook under the same Kaggle account. Copy fresh proxy URLs for both running notebook sessions. Proxy URLs are session credentials: use them only in the local environment, never save them in repository files or release metadata.
3. From the local machine with the Kaggle runtime toolkit installed, set `KAGGLE_INTERNET` to the CPU proxy and `KAGGLE_WITHOUT_INTERNET` to the Blackwell proxy. Use the toolkit relay to stream each public release asset directly to the GPU notebook:

   ```powershell
   $env:KAGGLE_INTERNET = '<fresh CPU notebook proxy URL>'
   $env:KAGGLE_WITHOUT_INTERNET = '<fresh Blackwell notebook proxy URL>'
   python C:/Users/<you>/.codex\skills\kaggle-runtime-toolkit\kaggle_relay.py `
     https://github.com/phanhieeus/HA-VLN-blackwellARC/releases/download/runtime-cp312-blackwell-2026-10-24/HA-VLN-blackwellARC.bundle `
     --dest /kaggle/working/HA-VLN-blackwellARC.bundle
   python C:/Users/<you>/.codex\skills\kaggle-runtime-toolkit\kaggle_relay.py `
     https://github.com/phanhieeus/HA-VLN-blackwellARC/releases/download/runtime-cp312-blackwell-2026-10-24/havln-blackwell-runtime-cp312-ubuntu2204.tar.gz `
     --dest /kaggle/working/havln-blackwell-runtime-cp312-ubuntu2204.tar.gz
   ```

   This transfers Git/runtime artifacts through the Kaggle notebook pair; it does not create or edit a local source clone. If the release URLs change, use the current URLs from the GitHub Releases page.
4. In a GPU notebook cell, restore the repository and runtime cache:

   ```bash
   git clone /kaggle/working/HA-VLN-blackwellARC.bundle /kaggle/working/HA-VLN-blackwellARC
   git -C /kaggle/working/HA-VLN-blackwellARC switch blackwell-py311-313
   tar -xzf /kaggle/working/havln-blackwell-runtime-cp312-ubuntu2204.tar.gz -C /kaggle/working
   cd /kaggle/working/HA-VLN-blackwellARC
   python scripts/install_blackwell_runtime.py \
     --wheel-dir /kaggle/working/havln-blackwell-runtime-cp312-ubuntu2204/wheels
   source scripts/blackwell_env.sh
   python scripts/check_blackwell_runtime.py
   ```

5. Confirm the Matterport path before running anything:

   ```python
   from pathlib import Path
   root = Path('/kaggle/input/datasets/phnvnh/mp3d-habitat/mp3d_habitat/mp3d')
   scans = [p for p in root.iterdir() if p.is_dir()]
   print(root.exists(), len(scans), scans[:3])
   ```

   Use an individual scan's `.glb` as the scene path. Kaggle exposes the attached Dataset read-only under `/kaggle/input`; the 22.34 GB expanded data should stay there.

6. Run a short render smoke test, then the longer microbenchmark:

   ```bash
   python scripts/benchmark_habitat_sim.py \
     --scene /kaggle/input/datasets/phnvnh/mp3d-habitat/mp3d_habitat/mp3d/17DRP5sb8fy/17DRP5sb8fy.glb \
     --warmup 20 --steps 200
   ```

## Push future code changes

The GPU notebook has no Internet. Transfer the updated Git bundle back to the Internet-enabled CPU notebook using the Kaggle toolkit, then push from that notebook. Configure a Kaggle secret named `GITHUB_TOKEN` in the CPU notebook; do not print the token or store it in the bundle. A push needs a token with write access to `phanhieeus/HA-VLN-blackwellARC`.

## If a rebuild is necessary

Use the matching source archive and build dependencies, then run `scripts/build_habitat_sim_blackwell.py`. Always redirect compiler output to a log file; the helper does this automatically. See [Blackwell build troubleshooting](blackwell-build-troubleshooting.md) for the notebook pipe stall and the Python 3.12 vendored-pybind11 error.

## Inputs required for a full HA-VLN-CMA reproduction

### Already available in this Kaggle session

- Matterport Habitat scene files from the attached private Dataset phnvnh/mp3d-habitat: 90 scans with .glb, .house, .navmesh, and .ply files. They are read-only under /kaggle/input/datasets/phnvnh/mp3d-habitat/mp3d_habitat/mp3d.
- The Git repository's task source JSON, human annotations, collision baselines, vocabularies, and the pinned asset manifest.
- The Blackwell runtime cache and successful Habitat-Sim render/movement microbenchmark.

Before full evaluation, map the attached scene directory to the repository's expected Data/scene_datasets/mp3d location or configure the scene path. Keep the 22.34 GB scene Dataset read-only; do not copy it to /kaggle/working.

### Still missing from the attached Dataset

The exact public validation artifacts are pinned in scripts/hf_resources.json. Fetch and checksum-verify them with python scripts/download_hf.py --destination Data --target all on an Internet-enabled machine or notebook, then upload/attach the resulting files to the GPU session while preserving Data/ paths:

| Purpose | Required files |
| --- | --- |
| HAPS human rendering for both validation splits | Extracted Data/HAPS2_0/ meshes from HAPS2_0/HAPS2_0.zip |
| Validation episodes/features | Data/HA-R2R/val_seen/val_seen.json.gz, val_unseen/val_unseen.json.gz, and the matching val_seen_bertidx.json.gz and val_unseen_bertidx.json.gz files |
| Published CMA policy evaluation | Data/checkpoints/HA-VLN-CMA/ckpt.39.pth, copied to agent/VLN-CE/data/checkpoints/cma_pm_da_aug_tune/CMA_PM_DA_Aug.pth as in the root README |

The repository contains the human annotation JSON, collision baselines and vocabularies; the heavyweight HAPS meshes, HA-R2R validation payloads and released CMA checkpoint are not in mp3d-habitat. --target all downloads both core and cma; --target core alone omits the CMA validation episodes and checkpoint.

PointGoal DD-PPO weights such as Data/ddppo-models/gibson-2plus-resnet50.pth are needed only when training from scratch, not when evaluating the released CMA checkpoint. After staging the listed files, run both val_seen and val_unseen with the pinned config and compare the official metrics in the root README. The current simulator microbenchmark is not a full policy or benchmark reproduction.
