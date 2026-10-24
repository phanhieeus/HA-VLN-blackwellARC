#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=blackwell_env.sh
source "$repo_root/scripts/blackwell_env.sh"
python "$repo_root/scripts/check_blackwell_runtime.py" --imports-only
cd "$repo_root/agent"
exec python run.py "$@"
