# HA-VLN 2.0 CMA: offline dependency and artifact reference

Updated: 2026-10-24. Purpose: identify every input required by the original CMA evaluator on Kaggle Blackwell.

The first GitHub runtime release contains Habitat-Sim wheels only. It does **not** provide a complete CMA agent environment. A simulator import or render benchmark cannot establish that the policy can run.

The current execution uses upstream `agent/run.py` and `config/cma_pm_da_aug_tune.yaml`. Setup scripts prepare files or start that command; they do not implement another evaluator.

## Verified environment

| Component | Version or source | Notes |
| --- | --- | --- |
| GPU | NVIDIA RTX PRO 6000 Blackwell Server Edition, SM 12.0 | 97,887 MiB reported by NVIDIA |
| GPU Python | 3.12.13 | CPython 3.12 wheels required |
| CPU notebook Python | 3.13.15 | Downloads and relays files; native agent wheels are built on GPU Python 3.12 |
| PyTorch | 2.10.0+cu128 | CUDA 12.8 runtime |
| NumPy | 2.0.2 | Requires scoped legacy aliases and NumPy JSON conversion |
| Habitat-Sim | 0.1.7 | Reuse the built CPython 3.12 wheel |
| Habitat-Lab and Baselines | `d6ed1c0a0e786f16f261de2beafe347f4186d0d8` | Keep both packages at the verified 0.1.7 revision |
| Code bundle starting commit | `dc4606d3659ca09bc8c478c2c47cdc6deff18e27` | Branch `blackwell-py311-313`; subsequent compatibility changes must be recorded in Git |

Habitat-Lab archive SHA-256: `eb9a121a15ed58f788154f4e0ff8db80535b8a07bb057a0927d4ea600db2bf1b`.

## Complete CMA dependency set

The native runtime archive has `habitat-sim==0.1.7`, `magnum==0.0.0`, `numpy-quaternion==2024.0.13`, and `pybind11==3.0.4`.

The agent additionally needs the pinned Habitat-Lab source and these packages:

| Packages | Versions installed in this session |
| --- | --- |
| gym, dtw, fastdtw | 0.17.3, 1.4.0, 0.3.4 |
| moviepy, decorator, proglog | 1.0.3, 4.4.2, 0.1.12 |
| webdataset | **0.1.40**; newer releases removed the `Dataset` API imported by Habitat-Baselines 0.1.7 |
| yacs, lmdb, msgpack-numpy | 0.1.8, 1.7.5, 0.4.8 |
| braceexpand, jsonlines, simplejson | 0.1.7, 4.0.0, 3.20.2 |
| ifcfg, objectio, gdown | 0.24, 0.2.29, 5.2.0 |

PyTorch, torchvision, NumPy, scipy, numba, attrs, PyYAML, msgpack, Pillow, OpenCV, imageio, imageio-ffmpeg, tensorboard, tensorflow and tqdm also come from the Kaggle image. Record their installed versions in the session manifest. A different image needs an import check before evaluation.

Legacy package build adjustments:

- `dtw==1.4.0`: its setup script imports removed Python module `imp` to read a version file. Read that version using `runpy` instead. The DTW algorithm is unchanged.
- `gym==0.17.3`: fix the invalid packaging requirement `opencv-python>=3.` to `opencv-python>=3.0`. The Gym implementation is unchanged.
- Build and retain wheels for dtw, fastdtw, gym and moviepy once. Subsequent matching sessions install those wheels offline.
- Install only `webdataset==0.1.40` from the cache. A wildcard install containing both old and new versions is invalid.

GPU dependency build script: `reproduction-artifacts/tools/install_agent_deps_gpu.py` in the local artifact workspace. On the current GPU it is `/kaggle/working/havln-runtime/install_agent_deps_gpu.py`.

## Data and pretrained weights

| Artifact | Required location | Purpose and availability |
| --- | --- | --- |
| Matterport Habitat scenes | `Data/scene_datasets/mp3d` | Symlink to `/kaggle/input/datasets/phnvnh/mp3d-habitat/mp3d_habitat/mp3d`; 90 scans verified. Keep scenes mounted read-only. |
| Validation episodes | `Data/HA-R2R/val_seen` and `val_unseen` | 778 seen and 1,839 unseen episodes. JSON and BERT-index companions staged. CMA uses ordinary instruction tokens. |
| Human placement annotations | `Data/Multi-Human-Annotations/human_motion.json` | Preserves all annotated human placements for validation scenes. |
| HAPS validation subset | `Data/HAPS2_0/<motion>/frame*.glb` and object configs | 383 motion sequences referenced by 64 validation scenes. All 120 frames and config files retained. 91,920 files, 92,304 ZIP entries including directories, 11,437,962,036 expanded bytes. |
| Collision references | `Data/HA-R2R-tools/collision_num_val_{seen,unseen}.json` | Evaluation reference inputs. |
| Released CMA checkpoint | `agent/VLN-CE/data/checkpoints/cma_pm_da_aug_tune/CMA_PM_DA_Aug.pth` | 148,409,133 bytes. SHA-256 `e70dce940c6ae16aa63c41f3b2411884448a3ccd083b06da156d297b5f4a52dc`. |
| RGB ResNet-50 ImageNet V1 weight | `$TORCH_HOME/hub/checkpoints/resnet50-0676ba61.pth` | **Also required during model construction**, even when evaluating the released CMA checkpoint. 102,530,333 bytes. SHA-256 `0676ba61b6795bbe1773cffd859882e5e297624d384b6993f7c9e683e722fb8a`. |
| Vocabulary and embeddings | `Data/HA-R2R-tools` | Already versioned in Git. Preserve released checkpoint embeddings during evaluation. |
| Recomputed navmeshes | `Data/recompute_navmesh` | Writable simulator cache. Save and reuse generated files with their input/code provenance. |

Set `TORCH_HOME=/kaggle/working/havln-runtime/torch-cache` before invoking the evaluator. The RGB weight source is `https://download.pytorch.org/models/resnet50-0676ba61.pth`.

DD-PPO depth initialization and HA-R2R training episodes are additional inputs for retraining. Released-checkpoint evaluation uses `MODEL.DEPTH_ENCODER.ddppo_checkpoint NONE`.

## HAPS integrity and transfer receipts

The public source revision is `c5f1cec167964bda3ba343acc3a18e7aef8540dd`. Full HAPS archive SHA-256 is `c5bc75ffcec1b1b83b9ffc1f7177a02fabcdacbb6a0a7a02368afa5bbc209741`.

The CPU notebook verified that source checksum, then copied original compressed ZIP records for the validation whitelist. Every selected filename, CRC and expanded size matched the locally prepared manifest. A complete ZIP CRC test passed before transfer.

The transferred subset has 6,566,268,004 bytes and SHA-256 `13693f457c8b52e490beaccc99d688bdd71d7b355df5711c5dcee16c2d1301f4`. Its ZIP container differs from the earlier locally recompressed subset; its selected file contents match.

Measured CPU-to-GPU relay took **105.4 seconds**, approximately 65 MB/s during transfer. GPU assembly verified the complete SHA-256 before removing parts. GPU extraction verified all 91,920 files. The compressed GPU copy was removed after extraction; CPU and local source artifacts remain available.

This subset covers both validation splits. It does not replace the full HAPS release for training or arbitrary scenes.

## Failures encountered and their fixes

| Symptom | Cause | Fix and verification |
| --- | --- | --- |
| HAPS upload reached about 95%, then HTTP 404 | Previous proxy became unreachable | Its remote file state was unverified. New CPU/GPU sessions completed a fresh transfer with final SHA validation. HTTP 404 alone does not establish whether timeout, stop or restart caused the loss. |
| `No module named habitat` | Native wheel release contained Habitat-Sim, not Habitat-Lab | Extract verified Lab source and add its root to a site-packages `.pth` file. |
| `No module named imp` building dtw | Python 3.12 removed `imp` | Patch version-file loading only and cache the resulting wheel. |
| `webdataset has no attribute Dataset` | Incompatible newer webdataset API | Install pinned `webdataset==0.1.40`. |
| ResNet download fails with DNS error | GPU has internet disabled and RGB initializer is absent | Relay the exact RGB weight, verify SHA, set persistent `TORCH_HOME`. |
| Relay prints `DONE` but final file is absent | Toolkit driver can report completion after a kernel assembly error; nested parent directory was absent | Explicitly create destination parents, assemble preserved parts, and verify bytes/hash. Never accept the text `DONE` as integrity proof. |
| Episode completes, `float32 is not JSON serializable` | NumPy scalar reaches upstream `json.dump` | Use a JSON default handler calling scalar `.item()` or array `.tolist()`. Metric aggregation is unchanged. |
| Initial serialization patch reports `np` undefined | Helper assumed a module alias unavailable in this file | Import NumPy inside the helper. Validate the actual extracted function in an empty namespace before running again. |
| Wrong relative config/data paths | Changing cwd to nested `agent/VLN-CE` for the root CMA config | Run from **`agent`** using upstream `agent/run.py`, matching README. |

## Status and performance evidence

The original evaluator completed a one-episode policy/simulator loop. Initial attempts then failed during JSON export. The corrected JSON handler passed a focused check using NumPy scalars and arrays.

Full `val_unseen` evaluation was subsequently started using the README command and default four environments. `val_seen` is queued after a successful unseen run. At the initial checkpoint, 124/1,839 unseen episodes had progressed, GPU utilization was 52%, and VRAM use was about 4,095 MiB. This is one sample, not a throughput benchmark.

The render log identifies the NVIDIA RTX PRO 6000 renderer. CUDA availability and device selection were verified. `havln-runtime/gpu-telemetry.csv` records utilization, memory and power every five seconds.

No AMP, lower-precision weights, frame dropping, shortened episodes or reduced validation split is enabled in the full evaluation. Performance claims require measured throughput and result comparison. Preserve the four-environment run as the reference before comparing larger environment batches. Simulator CPU work, mesh decoding and navmesh generation can limit GPU utilization.

The full metrics and equivalence to the paper remain pending until both evaluations complete and results are reviewed.

Related: [Restore and run](kaggle-cma-fast-restore.md), [data inventory](paper-baseline-reproduction-inventory.md).
