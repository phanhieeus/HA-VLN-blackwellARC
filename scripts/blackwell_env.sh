#!/usr/bin/env bash
# Source this file from a shell before running HA-VLN on a modern Blackwell stack.
_HAVLN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_HAVLN_SIM_EXT="$(python - <<'PY'
import importlib.util
from pathlib import Path
spec = importlib.util.find_spec("habitat_sim")
if spec is None or not spec.submodule_search_locations:
    raise SystemExit("habitat-sim is not installed in this Python environment")
print(Path(next(iter(spec.submodule_search_locations))) / "_ext")
PY
)" || { echo 'Could not locate Habitat-Sim; install Habitat-Sim 0.1.7 first.' >&2; return 1 2>/dev/null || exit 1; }
if [[ ! -d "$_HAVLN_SIM_EXT" ]]; then
  echo "Habitat-Sim extension directory not found: $_HAVLN_SIM_EXT" >&2
  return 1 2>/dev/null || exit 1
fi
export LD_LIBRARY_PATH="$_HAVLN_SIM_EXT${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH="$_HAVLN_ROOT/scripts/blackwell_compat${PYTHONPATH:+:$PYTHONPATH}"
export DISPLAY=""
export EGL_DEVICE_ID="${EGL_DEVICE_ID:-0}"
_HAVLN_EGL_LIB="$(ldconfig -p 2>/dev/null | awk '/libEGL_nvidia\.so\.0/{print $NF; exit}')"
if [[ -z "$_HAVLN_EGL_LIB" ]]; then
  for _candidate in /usr/local/nvidia/lib64/libEGL_nvidia.so.0 /usr/lib/x86_64-linux-gnu/libEGL_nvidia.so.0; do
    if [[ -e "$_candidate" ]]; then _HAVLN_EGL_LIB="$_candidate"; break; fi
  done
fi
if [[ -n "$_HAVLN_EGL_LIB" ]]; then
  _HAVLN_EGL_JSON="${TMPDIR:-/tmp}/havln-egl-${UID:-0}-$$.json"
  printf '{"file_format_version":"1.0.0","ICD":{"library_path":"%s"}}\n' "$_HAVLN_EGL_LIB" > "$_HAVLN_EGL_JSON"
  export __EGL_VENDOR_LIBRARY_FILENAMES="$_HAVLN_EGL_JSON"
fi
export HA_VLN_ROOT="$_HAVLN_ROOT"
unset _HAVLN_ROOT _HAVLN_SIM_EXT _HAVLN_EGL_LIB _HAVLN_EGL_JSON _candidate
