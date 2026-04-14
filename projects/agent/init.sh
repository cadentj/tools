#!/usr/bin/env bash
set -euo pipefail

umask 077

: "${HOME:=/data/home}"
: "${GH_TOKEN:=}"

repos_dir="${HOME}/repos"
mkdir -p "${repos_dir}"

git config --global user.name "cc-bot"
git config --global user.email "caden.juang+cc-bot@gmail.com"

clone_public_repo() {
  local repo_url="$1"
  local target_dir="$2"

  if [[ -d "${target_dir}/.git" ]]; then
    echo "Skipping existing repo: ${target_dir}"
    return 0
  fi

  git clone "${repo_url}" "${target_dir}"
}

clone_private_repo() {
  local repo_url="$1"
  local target_dir="$2"

  if [[ -d "${target_dir}/.git" ]]; then
    echo "Skipping existing repo: ${target_dir}"
    return 0
  fi

  if [[ -z "${GH_TOKEN}" ]]; then
    echo "Missing required environment variable: GH_TOKEN" >&2
    exit 1
  fi

  local auth_url="${repo_url/https:\/\//https:\/\/cadentj:${GH_TOKEN}@}"
  git clone "${auth_url}" "${target_dir}"
}

clone_private_repo "https://github.com/cadentj/sinnoh.git" "${repos_dir}/sinnoh"
clone_public_repo "https://github.com/cadentj/tools.git" "${repos_dir}/tools"

echo "Repos ready under ${repos_dir}"
