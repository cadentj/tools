#!/usr/bin/env bash
set -euo pipefail

umask 077

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

: "${HOME:=/data/home}"
: "${HERMES_HOME:=${HOME}/.hermes}"
: "${CODEX_HOME:=${HOME}/.codex}"

export HOME
export HERMES_HOME
export CODEX_HOME

mkdir -p "$HOME" "$HERMES_HOME" "$CODEX_HOME"

if [[ ! -f "$HERMES_HOME/config.yaml" ]]; then
  cp "$script_dir/hermes-config.yaml" "$HERMES_HOME/config.yaml"
fi

required_env=(
  TELEGRAM_BOT_TOKEN
  TELEGRAM_ALLOWED_USERS
  TELEGRAM_WEBHOOK_URL
  TELEGRAM_WEBHOOK_SECRET
)

for name in "${required_env[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: $name" >&2
    exit 1
  fi
done

exec hermes gateway
