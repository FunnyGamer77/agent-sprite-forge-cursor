#!/usr/bin/env bash
# Install agent-sprite-forge skills into Cursor's skills directory.
#
# Usage:
#   ./install.sh                    # install both skills to ~/.cursor/skills/
#   ./install.sh --project          # install into ./.cursor/skills/ in CWD
#   ./install.sh --target /path     # install into a custom directory
#   ./install.sh --no-deps          # skip pip install
#   ./install.sh --force            # overwrite existing skill folders
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="${SCRIPT_DIR}/skills"
TARGET="${HOME}/.cursor/skills"
INSTALL_DEPS=1
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      TARGET="$(pwd)/.cursor/skills"
      shift ;;
    --target)
      TARGET="$2"
      shift 2 ;;
    --no-deps)
      INSTALL_DEPS=0
      shift ;;
    --force)
      FORCE=1
      shift ;;
    -h|--help)
      sed -n '2,10p' "$0"
      exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2 ;;
  esac
done

if [[ ! -d "${SKILLS_SRC}" ]]; then
  echo "Skills source not found at ${SKILLS_SRC}" >&2
  exit 1
fi

echo "==> Target install dir: ${TARGET}"
mkdir -p "${TARGET}"

for skill_dir in "${SKILLS_SRC}"/*/; do
  name="$(basename "${skill_dir}")"
  dest="${TARGET}/${name}"
  if [[ -e "${dest}" && "${FORCE}" -eq 0 ]]; then
    echo "    skip  ${name} (exists; pass --force to overwrite)"
    continue
  fi
  rm -rf "${dest}"
  cp -R "${skill_dir}" "${dest}"
  echo "    install  ${name}"
done

if [[ "${INSTALL_DEPS}" -eq 1 ]]; then
  echo "==> Installing Python dependencies (Pillow, numpy)"
  if command -v python3 >/dev/null 2>&1; then
    python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
  else
    echo "    python3 not found on PATH; please install dependencies manually:" >&2
    echo "    pip install -r ${SCRIPT_DIR}/requirements.txt" >&2
  fi
else
  echo "==> Skipped dependency install (--no-deps)"
fi

echo
echo "Done. Restart Cursor (or open a new chat) so the skills are picked up."
echo "Try a prompt like:"
echo "  'use generate2dsprite to create a 2x2 idle for a fire mage'"
echo "  'use generate2dmap to create a top-down RPG forest shrine map with a 3x3 prop pack'"
