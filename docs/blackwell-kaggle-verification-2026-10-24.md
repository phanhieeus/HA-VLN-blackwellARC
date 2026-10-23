# Kaggle Blackwell verification — 2026-10-24

## Runtime and data

- GPU: NVIDIA RTX PRO 6000 Blackwell Server Edition, compute capability 12.0.
- OS/Python: Ubuntu 22.04.5, CPython 3.12.13 (`cp312`).
- Framework: PyTorch 2.10.0+cu128, CUDA 12.8, NumPy 2.0.2.
- Simulator: Habitat-Sim 0.1.7, built headless with CUDA support and system pybind11 3.0.4.
- Matterport input: `phnvnh/mp3d-habitat`, 90 scans, each with `.glb`, `.house`, `.navmesh`, and semantic `.ply` assets.
- Sample scene: `17DRP5sb8fy`.

The runtime-check script passed. The benchmark opened the scene through NVIDIA EGL/OpenGL 4.6 and produced 224×224 RGB-D observations. Five fresh simulator runs each used 20 warm-up steps and measured 200 `turn_left` steps:

| Run | Mean step latency (ms) | P95 step latency (ms) | Throughput (steps/s) |
|---:|---:|---:|---:|
| 1 | 0.2819 | 0.2956 | 3547.1 |
| 2 | 0.2806 | 0.2969 | 3564.4 |
| 3 | 0.2802 | 0.2886 | 3568.2 |
| 4 | 0.2822 | 0.2984 | 3543.4 |
| 5 | 0.2794 | 0.2936 | 3578.5 |

Across runs, mean latency was 0.28086 ms/step and mean throughput was 3560.32 steps/s. An isolated offline installation from the runtime-cache wheels passed the same runtime check and a separate five-step RGB-D render smoke test.

## Scope

This validates the pinned simulator build, Blackwell rendering, and a repeatable simulator microbenchmark. It does **not** reproduce the full HA-VLN continuous benchmark or establish algorithm-level metric parity: HA-R2R/HAPS episodes, human-motion assets, released checkpoints, and the required evaluation split are not attached in this notebook. HA-VLN model, planner, and metric source files were left unchanged by the runtime adaptation.
