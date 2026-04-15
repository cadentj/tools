#!/usr/bin/env bash
set -euo pipefail

umask 077

script_dir="/app"

mkdir -p "$HOME" "$HERMES_HOME" "$CODEX_HOME"

# Always refresh bashrc from the image (aliases may change between deploys)
cp "$script_dir/bashrc" "$HOME/.bashrc"

# Copy hermes-config.yaml to .hermes/config.yaml if it doesn't exist
# else, delete hermes-config.yaml
if [[ -f "$HERMES_HOME/config.yaml" ]]; then
  rm -f "$script_dir/hermes-config.yaml"
else
  cp "$script_dir/hermes-config.yaml" "$HERMES_HOME/config.yaml"
fi

required_env=(
  TELEGRAM_BOT_TOKEN
  TELEGRAM_ALLOWED_USERS
  TELEGRAM_WEBHOOK_URL
  TELEGRAM_WEBHOOK_SECRET
  GH_TOKEN
)

for name in "${required_env[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: $name" >&2
    exit 1
  fi
done

### (2) Clone repos ###
repos_dir="${HOME}/repos"
mkdir -p "${repos_dir}"

git config --global user.name "cc-bot"
git config --global user.email "caden.juang+cc-bot@gmail.com"

git clone "https://${GH_TOKEN}@github.com/cadentj/sinnoh.git" "${repos_dir}/sinnoh"
git clone "https://${GH_TOKEN}@github.com/cadentj/tools.git" "${repos_dir}/tools"

echo "Repos ready under ${repos_dir}"

exec hermes gateway
