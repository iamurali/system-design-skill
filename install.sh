#!/usr/bin/env bash
# Install system-design-interview + excalidraw-diagram skills for any Agent Skills-compatible agent.
set -euo pipefail

REPO_URL="https://github.com/iamurali/system-design-skill.git"
SKILLS=(system-design-interview excalidraw-diagram)

PROJECT=false
UPDATE=false
EXCALIDRAW=false

usage() {
  cat <<'EOF'
Usage: install.sh [OPTIONS]

Install system-design-interview and excalidraw-diagram agent skills.

Options:
  --project     Install to .agents/skills/ in the current directory (default: global)
  --update      Pull latest from GitHub and refresh symlinks
  --excalidraw  Set up uv + Playwright for PNG diagram rendering (optional)
  -h, --help    Show this help

Examples:
  curl -fsSL https://raw.githubusercontent.com/iamurali/system-design-skill/main/install.sh | bash
  curl -fsSL .../install.sh | bash -s -- --project
  curl -fsSL .../install.sh | bash -s -- --update --excalidraw
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT=true; shift ;;
    --update) UPDATE=true; shift ;;
    --excalidraw) EXCALIDRAW=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if $PROJECT; then
  SKILLS_DIR="$(pwd)/.agents/skills"
  CACHE_DIR="$(pwd)/.agents/.system-design-skill-cache"
else
  SKILLS_DIR="${HOME}/.agents/skills"
  DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
  CACHE_DIR="${DATA_HOME}/system-design-skill"
fi

install_skill() {
  local name="$1"
  local target="${SKILLS_DIR}/${name}"
  local source="${CACHE_DIR}/skills/${name}"

  if [[ ! -d "$source" ]]; then
    echo "ERROR: skill source not found: $source" >&2
    exit 1
  fi

  mkdir -p "$SKILLS_DIR"
  if [[ -e "$target" || -L "$target" ]]; then
    rm -rf "$target"
  fi
  ln -s "$source" "$target"
  echo "  linked ${target} -> ${source}"
}

setup_cache() {
  if [[ -d "${CACHE_DIR}/.git" ]]; then
    if $UPDATE; then
      echo "Updating cache at ${CACHE_DIR}..."
      git -C "$CACHE_DIR" pull --ff-only
    else
      echo "Using existing cache at ${CACHE_DIR}"
    fi
  else
    if ! command -v git >/dev/null 2>&1; then
      echo "ERROR: git is required but not found in PATH." >&2
      exit 1
    fi
    echo "Cloning ${REPO_URL} to ${CACHE_DIR}..."
    mkdir -p "$(dirname "$CACHE_DIR")"
    git clone --depth 1 "$REPO_URL" "$CACHE_DIR"
  fi
}

setup_excalidraw() {
  local refs="${SKILLS_DIR}/excalidraw-diagram/references"
  if [[ ! -d "$refs" ]]; then
    echo "ERROR: excalidraw-diagram not installed at ${refs}" >&2
    exit 1
  fi
  if ! command -v uv >/dev/null 2>&1; then
    echo "WARNING: uv not found. Install uv (https://docs.astral.sh/uv/) then run:"
    echo "  cd ${refs} && uv sync && uv run playwright install chromium"
    return 0
  fi
  echo "Setting up Excalidraw render pipeline..."
  (cd "$refs" && uv sync && uv run playwright install chromium)
  echo "Excalidraw render pipeline ready."
}

echo "System Design Interview Skill — installer"
echo ""

setup_cache

echo "Installing skills to ${SKILLS_DIR}:"
for skill in "${SKILLS[@]}"; do
  install_skill "$skill"
done

if $EXCALIDRAW; then
  echo ""
  setup_excalidraw
fi

echo ""
echo "Done! Skills installed:"
for skill in "${SKILLS[@]}"; do
  echo "  - ${SKILLS_DIR}/${skill}"
done
echo ""
echo "Try it with your agent:"
echo '  "Design a distributed rate limiter"'
echo '  "System design for Google — design a news feed"'
echo '  "Prepare a URL shortener for PE interview"'
