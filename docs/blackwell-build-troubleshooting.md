# Blackwell build troubleshooting

## Kaggle notebook output-pipe stalls

When Habitat-Sim 0.1.7 was first built interactively with `python setup.py bdist_wheel --headless --with-cuda`, CMake/Ninja emitted a large volume of native compiler diagnostics into the notebook's live output stream. The notebook stopped draining that pipe quickly enough. Ninja blocked in `anon_pipe_write`, its CPU use fell to 0%, and `build/.ninja_log` stopped gaining completed commands. The kernel remained busy, which made the build look hung even though the source and compiler configuration were valid.

This was an output transport stall, not a CUDA or Blackwell compilation error. In this run, restarting the build with stdout and stderr redirected to a file let Ninja resume from the existing object files and continue compiling. The successful retry's completed-command count advanced from 338 to 463, 548, and 683 while the log file grew.

## Prevent the stall

In a Kaggle notebook, start the build as a detached subprocess and redirect **both** output streams to a file. Do not stream the full CMake/Ninja output into the cell:

```python
import os
import subprocess
import sys
from pathlib import Path

source = Path('/kaggle/working/habitat-sim-v0.1.7')
log_path = Path('/kaggle/working/habitat-sim-build.log')
env = os.environ.copy()
env['CMAKE_BUILD_PARALLEL_LEVEL'] = '4'
env['MAX_JOBS'] = '4'
with log_path.open('w', encoding='utf-8') as log:
    process = subprocess.Popen(
        [sys.executable, 'setup.py', 'bdist_wheel', '--headless', '--with-cuda'],
        cwd=source,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
        text=True,
    )
print('Build PID:', process.pid)
print('Build log:', log_path)
```

Poll progress from another idle notebook kernel or cell:

```python
from pathlib import Path
import subprocess

print(subprocess.run(['ps', '-p', '<PID>', '-o', 'pid,stat,etime,%cpu,cmd'], capture_output=True, text=True).stdout)
print(subprocess.run(['tail', '-n', '30', '/kaggle/working/habitat-sim-build.log'], capture_output=True, text=True).stdout)
log = Path('/kaggle/working/habitat-sim-v0.1.7/build/.ninja_log')
print('Completed Ninja commands:', max(0, len(log.read_text().splitlines()) - 1))
```

Replace `<PID>` with the printed process ID. A growing build log or `.ninja_log` means the build is progressing. A live process with no CPU and no log growth warrants checking its wait channel and child processes before stopping it. Avoid sending broad `killall`/`pkill` commands; if an interruption is necessary, verify the exact PID and command first. Re-running `bdist_wheel` in the same source tree resumes completed Ninja work where possible.

## Python 3.12+ and the vendored pybind11

After the output-pipe stall was removed, the initial Python 3.12 build reached the binding targets and failed for a separate reason. Habitat-Sim 0.1.7 vendors pybind11 2.6.2, whose code accesses CPython internals that are opaque or removed in Python 3.12 (`PyFrameObject` is incomplete and `PyThreadState.frame` no longer exists). The corresponding C++ binding object files fail to compile. This is a Python/pybind11 API compatibility error, not a GPU architecture error.

The Habitat-Sim 0.1.7 CMake files already expose `USE_SYSTEM_PYBIND11`. Install a pybind11 release compatible with the active CPython version, then configure the unchanged Habitat-Sim release to use that package. For the tested Kaggle CPython 3.12.13 image, pybind11 3.0.4 is available:

```python
import os
import pybind11

env = os.environ.copy()
env['CMAKE_ARGS'] = (
    '-DUSE_SYSTEM_PYBIND11=ON '
    f'-Dpybind11_DIR={pybind11.get_cmake_dir()}'
)
```

Pass this `env` to the redirected `subprocess.Popen` build shown above and add `--force-cmake` to the setup.py arguments so the cached CMake configuration is refreshed. Keep the Habitat-Sim version pinned at 0.1.7; record the pybind11 version in the build manifest. The same pybind11 package must be available offline in future notebook sessions, for example from the runtime artifact bundle.

## Reuse the built wheel

After the wheel passes the import and scene-render smoke checks, archive the wheel with a manifest recording Ubuntu release, Python ABI, Habitat-Sim version, PyTorch/CUDA versions, build flags, and GPU. Habitat-Sim's native wheel is Python-ABI and OS specific: a CPython 3.12 wheel on Ubuntu 22.04 is not a general CPython 3.11/3.13 or different-distribution artifact. Store the wheel as a versioned release/download artifact or private Kaggle Dataset, then install that artifact in future matching sessions instead of recompiling. Keep the source-build route as a fallback when the image or ABI changes.
