#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

REPO_OWNER="SPhillips1337"
REPO_NAME="LLM-Auto-Redirect"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
PLUGIN_SLUG="llm-auto-redirect"
PLUGIN_MAIN_FILE="LLM_Auto_Redirect.php"
DEFAULT_BRANCH="main"

usage() {
  cat <<USAGE
Usage: ./install.sh [--target DIR] [--branch BRANCH] [--force]

Install ${REPO_NAME} as a WordPress plugin.

Options:
  --target DIR      Destination directory. Defaults to ./llm-auto-redirect,
                    or the current directory when run from this repository.
  --branch BRANCH   Git branch/tag to clone when installing to a new directory
                    (default: ${DEFAULT_BRANCH}).
  --force           Allow installing into an existing non-empty directory only
                    when it is already this project.
  -h, --help        Show this help.

Examples:
  ./install.sh --target /var/www/html/wp-content/plugins/${PLUGIN_SLUG}
  curl -fsSL https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/main/install.sh | bash -s -- --target /var/www/html/wp-content/plugins/${PLUGIN_SLUG}
USAGE
}

log() { printf '[%s] %s\n' "${REPO_NAME}" "$*"; }
fail() { printf '[%s] ERROR: %s\n' "${REPO_NAME}" "$*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

is_project_dir() {
  local dir="$1"
  [[ -f "${dir}/${PLUGIN_MAIN_FILE}" ]] || return 1
  grep -q "Plugin Name:[[:space:]]*LLM Auto Redirect" "${dir}/${PLUGIN_MAIN_FILE}" 2>/dev/null || return 1
}

validate_git_identity() {
  local dir="$1"
  local remote_url=""
  if git -C "$dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    remote_url="$(git -C "$dir" config --get remote.origin.url || true)"
    case "$remote_url" in
      "https://github.com/${REPO_OWNER}/${REPO_NAME}.git"|\
      "https://github.com/${REPO_OWNER}/${REPO_NAME}"|\
      "git@github.com:${REPO_OWNER}/${REPO_NAME}.git"|\
      "ssh://git@github.com/${REPO_OWNER}/${REPO_NAME}.git"|\
      "") return 0 ;;
      *) fail "Existing directory has unexpected origin remote: ${remote_url}" ;;
    esac
  fi
  is_project_dir "$dir" || fail "Existing directory is not recognized as ${REPO_NAME}; refusing to modify it."
}

validate_ref_name() {
  local ref="$1"
  [[ -n "$ref" ]] || fail "Branch/tag must not be empty"
  [[ "$ref" != -* ]] || fail "Branch/tag must not start with '-'"
  git check-ref-format --allow-onelevel "$ref" >/dev/null 2>&1 || fail "Invalid branch/tag name: ${ref}"
}

TARGET_DIR=""
BRANCH="${DEFAULT_BRANCH}"
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || fail "--target requires a directory"
      TARGET_DIR="$2"
      shift 2
      ;;
    --branch)
      [[ $# -ge 2 ]] || fail "--branch requires a branch or tag"
      BRANCH="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

require_cmd git
require_cmd php

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

if [[ -z "$TARGET_DIR" ]]; then
  if is_project_dir "$SCRIPT_DIR"; then
    TARGET_DIR="$SCRIPT_DIR"
  else
    TARGET_DIR="${PWD}/${PLUGIN_SLUG}"
  fi
fi

case "$TARGET_DIR" in
  /*) ;;
  *) TARGET_DIR="${PWD}/${TARGET_DIR}" ;;
esac

validate_ref_name "$BRANCH"

log "Target directory: ${TARGET_DIR}"

if [[ -d "$TARGET_DIR" ]]; then
  if [[ -n "$(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
    validate_git_identity "$TARGET_DIR"
    if [[ "$FORCE" -ne 1 && "$TARGET_DIR" != "$SCRIPT_DIR" ]]; then
      fail "Target exists and is non-empty. Re-run with --force after verifying it is safe."
    fi
    log "Updating existing ${REPO_NAME} checkout."
    if git -C "$TARGET_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      git -C "$TARGET_DIR" fetch --prune origin
      git -C "$TARGET_DIR" checkout "$BRANCH"
      git -C "$TARGET_DIR" pull --ff-only origin "$BRANCH"
    else
      log "Existing directory is not a git checkout; validation passed, leaving files in place."
    fi
  else
    log "Cloning ${REPO_URL} (${BRANCH}) into empty target."
    git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$TARGET_DIR"
  fi
else
  mkdir -p "$(dirname -- "$TARGET_DIR")"
  log "Cloning ${REPO_URL} (${BRANCH})."
  git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$TARGET_DIR"
fi

is_project_dir "$TARGET_DIR" || fail "Installed files do not match expected WordPress plugin identity."
php -l "${TARGET_DIR}/${PLUGIN_MAIN_FILE}" >/dev/null

cat <<NEXT_STEPS

${REPO_NAME} is installed at:
  ${TARGET_DIR}

Next steps:
  1. Ensure the Redirection plugin by John Godley is installed and active.
  2. Activate "LLM Auto Redirect" in WordPress Admin > Plugins.
  3. Configure provider settings in Tools > LLM Auto Redirect.

NEXT_STEPS
