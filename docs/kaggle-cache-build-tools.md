# Rebuild the prepared Kaggle CMA cache

Use these operator scripts only when rebuilding the prepared cache. Normal evaluation uses `agent/run.py` from the upstream README. Normal fresh-session setup uses the cached `restore_havln_cache.py`.

The scripts are versioned under `scripts/kaggle/` in the fork. Their actual staging paths are `/kaggle/working/havln-preparation` on CPU and `/kaggle/working/havln-runtime` on GPU.

| Script | Run on | Operation |
| --- | --- | --- |
| `prepare_haps_on_cpu.py` | Internet CPU | Downloads pinned full HAPS with byte ranges, verifies SHA, selects the validation whitelist, copies compressed records, validates every selected CRC. Can derive the whitelist from pinned validation episodes and human annotations when the independent whitelist is absent. |
| `prepare_agent_deps_cpu.py` | Internet CPU | Downloads pinned Habitat-Lab source, pure Python dependencies and CPython 3.12 wheels. |
| `install_agent_deps_gpu.py` | CPython 3.12 GPU | Applies packaging-only dtw/Gym fixes, builds missing legacy wheels, installs and retains them. |
| `relay_prepared_haps.py` | Internet CPU | Transfers the prepared ZIP to GPU in source-hash-namespaced 24 MiB parts; assembles and SHA-verifies before deleting parts. |
| `extract_haps_gpu.py` | GPU | Calls upstream `unpack_haps`; records completion and checksum marker. |
| `package_cma_cache_gpu.py` | GPU | Selects wheels matching installed versions, includes Habitat-Lab and RGB initializer, creates the complete reusable dependency tar and manifest. |
| `pull_prepared_cache_cpu.py` | Internet CPU | Fetches committed source/runtime/weights from GPU for private Dataset upload. Verifies cache and checkpoint SHA. |

The CPU relay and pull scripts import `kaggle_executor.py` from the runtime toolkit. Copy that module into `/kaggle/working/havln-preparation` before running them. Place the current target URL in `/tmp/havln-target.json` using the shape `{"gpu": "<current GPU proxy URL>"}`. Protect this file and keep it outside saved outputs and Git.

The runtime toolkit's standard public-URL relay can transfer GitHub release bundles and the RGB initializer. Explicitly create all target parent directories before assembly. Verify target bytes/hash after relay; its `DONE` text alone is insufficient.

To publish the prepared Dataset, stage the original CMA checkpoint, validation metadata tar, committed Git bundle, complete dependency tar, HAPS subset, their manifests, README and restore script. Keep large archives opaque using `.zip.bin` and `.tar.bin` names. Create the Dataset privately under the correct Kaggle account. The CLI executable is `kaggle`; this installed package does not support `python -m kaggle`. Dataset titles must have 6–50 characters.

After upload, use authenticated `kaggle datasets files phnvnh/havln2-validation-cache` to verify the expected 10-file layout. A CLI upload completion message alone does not measure fresh-session startup time.

Record a source commit and complete artifact hashes before promoting a new cache. Dataset versioning replaces the file set, so a replacement version must contain all required artifacts. Preserve generated dynamic navmeshes separately when they are available; they are not in the first prepared Dataset.
