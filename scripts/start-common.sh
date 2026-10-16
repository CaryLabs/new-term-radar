#!/usr/bin/env bash
set -euo pipefail
platform=${1:?platform required}
shift
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd -- "$root"
case "$platform" in
  windows)
    case "$(uname -s)" in MINGW*|MSYS*) ;; *) printf '%s\n' 'Use Git for Windows Git Bash; WSL should use start-linux.sh.' >&2; exit 2 ;; esac
    python="$root/.venv/Scripts/python.exe"
    if command -v py >/dev/null 2>&1; then bootstrap=(py -3)
    elif command -v python >/dev/null 2>&1; then bootstrap=(python)
    else printf '%s\n' 'Python 3.10+ not found. Install Python and Git for Windows.' >&2; exit 2; fi
    ;;
  linux)
    python="$root/.venv/bin/python"
    command -v python3 >/dev/null 2>&1 || { printf '%s\n' 'Install Python 3.10+ and python3-venv.' >&2; exit 2; }
    bootstrap=(python3)
    ;;
  *) printf '%s\n' 'Unknown platform' >&2; exit 2 ;;
esac
if [[ ${1:-} == setup ]]; then
  [[ $# == 1 ]] || { printf '%s\n' 'setup accepts no extra arguments' >&2; exit 2; }
  if [[ ! -f "$python" ]]; then
    "${bootstrap[@]}" -E -X utf8 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else "Python 3.10+ required")'
    "${bootstrap[@]}" -E -X utf8 -m venv "$root/.venv"
  fi
  "$python" -E -X utf8 -m pip --isolated install -r "$root/requirements-launcher.txt"
  if [[ ! -e config.json ]]; then
    "$python" -E -X utf8 -c 'import shutil; shutil.copyfile("config.example.json", "config.json")'
    printf '%s\n' 'Created config.json. Edit credentials and monitored sources before startup.'
  fi
  exit 0
fi
[[ -f "$python" ]] || { printf 'Virtual environment missing. Run: bash scripts/start-%s.sh setup\n' "$platform" >&2; exit 2; }
# -E ignores Python environment overrides; -X utf8 works without exporting variables.
exec "$python" -E -X utf8 -m radar.launcher "$@"
