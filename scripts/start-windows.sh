#!/usr/bin/env bash
# Run with Git for Windows' Git Bash, not PowerShell, cmd batch, or WSL Python.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec bash "$root/scripts/start-common.sh" windows "$@"
