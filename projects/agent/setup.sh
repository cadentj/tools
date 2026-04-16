#!/usr/bin/env bash
# Run once (or when you need to refresh clones) inside the machine/container.
# Requires GH_TOKEN and the same HOME layout as the agent image.
set -euo pipefail

REPOS_DIR="/data/repos"

mkdir -p "$REPOS_DIR"

git config --global user.name "cc-bot"
git config --global user.email "caden.juang+cc-bot@gmail.com"

ensure_repo() {
  local url=$1 dir=$2
  if [[ -d "${dir}/.git" ]]; then
    git -C "${dir}" pull --ff-only
  else
    rm -rf "${dir}"
    git clone "${url}" "${dir}"
  fi
}

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "GH_TOKEN is required" >&2
  exit 1
fi

ensure_repo "https://${GH_TOKEN}@github.com/cadentj/sinnoh.git" "$REPOS_DIR/sinnoh"
ensure_repo "https://${GH_TOKEN}@github.com/cadentj/tools.git" "$REPOS_DIR/tools"

echo "Repos ready under $REPOS_DIR"
