# HA-VLN 2.0 paper reproduction: data and checkpoints

**Scope:** reproduce the HA-VLN-CMA continuous-environment baseline for research by running the released code locally, either from the published checkpoint or by retraining. The goal is to run the paper's benchmark protocol and compare its locally reported metrics.

**Current session update (2026-10-24):** validation data and 91,920 selected HAPS files have been staged and verified on a new Blackwell notebook using CPU-to-GPU relay. The original evaluator is running full `val_unseen`, with `val_seen` queued. Full paper metrics remain pending. Use the [current restoration procedure](kaggle-cma-fast-restore.md) and [complete dependency/error reference](kaggle-cma-offline-reference.md); older package upload status below is historical.

The repository's pinned resource manifest is scripts/hf_resources.json. Its Hugging Face source revision is c5f1cec167964bda3ba343acc3a18e7aef8540dd; its public annotation source revision is f46f93642d7ab96cc49611f8cfea09cecf2fa7f9. Do not substitute unpinned resources when comparing results.

## Two reproduction modes

### Evaluate the released paper baseline

This reproduces the published model's validation behavior without training it again. Required inputs are the HA-VLN code/config, Habitat-Sim 0.1.7 runtime, Matterport Habitat scene files, HAPS 2.0 human meshes, HA-R2R validation episodes, human placement annotations, the validation collision references, and the released CMA checkpoint.

Copy the released checkpoint to the model path expected by the repository:

```bash
mkdir -p agent/VLN-CE/data/checkpoints/cma_pm_da_aug_tune
cp Data/checkpoints/HA-VLN-CMA/ckpt.39.pth \
  agent/VLN-CE/data/checkpoints/cma_pm_da_aug_tune/CMA_PM_DA_Aug.pth
```

Then run the repository's pinned CMA evaluation configuration on val_seen and val_unseen. Compare the locally reported SR, NE, CR, and TCR with the paper/repository reference.

### Retrain the baseline

Retraining additionally requires the HA-R2R train split and the PointGoal DD-PPO ResNet-50 pretrained depth-encoder weights. Use the repository's cma_pm_da_aug_tune.yaml training configuration and the included instruction vocabulary/embedding assets. Keep the released CMA checkpoint as a validation reference; it is not the same artifact as the DD-PPO encoder initialization.

## Asset inventory

| Asset | Repository path | What it is for | Needed for | Current status (2026-10-24) |
| --- | --- | --- | --- | --- |
| Habitat runtime | Habitat-Sim 0.1.7 Blackwell wheel cache; release runtime-cp312-blackwell-2026-10-24 | Simulator API and rendering used by HA-VLN 2.0 | Both modes | Published in the fork's GitHub Release. Verified on RTX PRO 6000 Blackwell with CPython 3.12.13, CUDA 12.8, Ubuntu 22.04. |
| Full CMA agent dependencies | Habitat-Lab/Baselines pinned 0.1.7 source and additional Python wheels | Imports and execution of the original CMA trainer | Both modes | Installed in current GPU session and preserved in private Dataset phnvnh/havln2-validation-cache. Includes gym 0.17.3, webdataset 0.1.40, dtw, fastdtw, yacs, lmdb and other dependencies. Complete dependency tar is 301,455,360 bytes. Dataset file listing verified. |
| Matterport Habitat scenes | Data/scene_datasets/mp3d/<scan>/<scan>.glb and companion .house/.navmesh/.ply files | Static 3D environment geometry and navigation data | Both modes | Private Kaggle Dataset phnvnh/mp3d-habitat is already uploaded and attached; 90 scans. Leave it read-only under /kaggle/input. No raw .sens capture files or full 1.3 TB Matterport release is required for this Habitat baseline. |
| HA-R2R train episodes | Data/HA-R2R/train/train.json.gz | 10,819 training episodes, routes, instructions, and ordinary instruction token IDs | Retraining | Downloaded locally; SHA-256 verified against the pinned Hugging Face LFS object. Included in the separate training package. |
| HA-R2R validation episodes | Data/HA-R2R/val_seen/val_seen.json.gz; Data/HA-R2R/val_unseen/val_unseen.json.gz | Human-aware validation episodes and instructions; 778 seen and 1,839 unseen episodes | Released-checkpoint evaluation and retraining validation | Downloaded and SHA-256 verified; private Kaggle package upload completed. Kaggle reported dataset creation in progress; local file-list verification returned HTTP 403, so account-side visibility remains unconfirmed. |
| BERT token index files | Matching train_bertidx.json.gz, val_seen_bertidx.json.gz, and val_unseen_bertidx.json.gz under Data/HA-R2R | Precomputed BERT token IDs for the separate BERT-based model path. The CMA config consumes instruction_tokens from the ordinary JSON files. | Full resource reproduction; not required by the released CMA path itself | Train and validation files downloaded and SHA-256 verified. Validation files are in the eval package; train files are in the separate training package. |
| HAPS 2.0 archive | Data/downloads/HAPS2_0.zip, extracted to Data/HAPS2_0/ | Dynamic human motion meshes. The release describes 486 motion sequences, with 120 frames each; the simulator uses these meshes with the scene placements. | Both modes | 8,332,789,125-byte archive downloaded locally; SHA-256 matches c5bc75ffcec1b1b83b9ffc1f7177a02fabcdacbb6a0a7a02368afa5bbc209741. Included in the completed eval-package upload. |
| Human placement annotations | Data/Multi-Human-Annotations/human_motion.json | Associates human motions and their scene placements for the continuous simulator | Both modes | SHA-256 verified; included in eval package upload. |
| Validation collision references | Data/HA-R2R-tools/collision_num_val_seen.json and collision_num_val_unseen.json | Per-episode collision reference data used by HA-VLN evaluation/metric code | Validation metrics | SHA-256 verified; included in eval package upload. |
| Vocabulary and instruction embeddings | Data/HA-R2R-tools/instruction_vocab.json, embeddings_glove_50d.json.gz, and embeddings.json.gz | Ordinary CMA vocabulary/embedding initialization and historical released-model lookup. The released checkpoint has a 5,401 x 50 historical lookup; new training uses the ordered HA-R2R vocabulary and GloVe initializer described in Data/HA-R2R-tools/README.md. | Both modes; initializer for retraining | Versioned in the Git repository; no separate download required. Preserve the released checkpoint's lookup when evaluating it. |
| Released HA-VLN-CMA checkpoint | Data/checkpoints/HA-VLN-CMA/ckpt.39.pth | Trained baseline policy weights used to reproduce published validation metrics | Released-checkpoint evaluation | 148,409,133 bytes; SHA-256 verified against the pinned manifest; included in the completed eval-package upload. |
| RGB ResNet-50 initializer | $TORCH_HOME/hub/checkpoints/resnet50-0676ba61.pth | ImageNet V1 RGB encoder initialization requested during policy construction | Both modes, including released-checkpoint evaluation | Missing from the earlier inventory. Now transferred and SHA-256 verified. Set TORCH_HOME to the working-directory cache so offline runs find it. See the offline reference for full hash and size. |
| DD-PPO depth encoder initialization | Data/ddppo-models/gibson-2plus-resnet50.pth | ResNet-50 pretrained for PointGoal navigation; initializes the depth encoder for training from scratch | Retraining only; not needed when evaluating ckpt.39.pth | Official archive downloaded (703,827,098 bytes); ZIP CRC check passed. Only the required model weight is in the training package. The upstream archive has no checksum pinned by HA-VLN; its extracted weight is SHA-256 recorded in the package manifest. |

## Kaggle data packages

Matterport scenes remain in the existing private Dataset phnvnh/mp3d-habitat. They are not copied to the repository, GitHub Release, or the HA-VLN asset packages.

The validation assets are packaged in private Dataset phnvnh/havln2-eval-assets. The train split and DD-PPO initialization were uploaded separately as private Dataset phnvnh/havln2-training-assets. Historical API verification returned HTTP 403; local tar backups remain under reproduction-artifacts/kaggle-datasets/. Attaching the evaluation Dataset was reported to stall session startup. The current workflow instead attaches only mp3d-habitat and relays the verified validation subset from an internet-enabled CPU notebook. The training package is needed only for retraining.

On Kaggle, extract each package into the repository's Data directory, then copy the CMA checkpoint to the expected agent checkpoint location for evaluation. The Matterport Dataset stays mounted read-only.

## Compatibility and limits

The GitHub runtime cache avoids rebuilding Habitat-Sim only for its matching ABI/profile: CPython 3.12 on Ubuntu 22.04. The code contains a build helper for Python 3.11–3.13, but this Blackwell wheel has only been verified for CPython 3.12; Python 3.11 and 3.13 require separate ABI-specific builds.

The completed Habitat-Sim render/movement microbenchmark validates simulator operation, not the policy's paper metrics. A paper reproduction is complete only after the model evaluation runs over the intended validation split and its SR, NE, CR, and TCR results are recorded against the pinned configuration.

