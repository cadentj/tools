#!/usr/bin/env bash
set -euo pipefail

umask 077

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

: "${HOME:=/data/home}"
: "${HERMES_HOME:=${HOME}/.hermes}"
: "${CODEX_HOME:=${HOME}/.codex}"
: "${HERMES_CRON_JOBS_FILE:=${HOME}/jobs.md}"

export HOME
export HERMES_HOME
export CODEX_HOME
export HERMES_CRON_JOBS_FILE

mkdir -p "$HOME" "$HERMES_HOME" "$CODEX_HOME"

if [[ ! -f "$HERMES_HOME/config.yaml" ]]; then
  cp "$script_dir/hermes-config.yaml" "$HERMES_HOME/config.yaml"
fi

if [[ ! -f "$HOME/AGENTS.md" ]]; then
  cp "$script_dir/AGENTS.template.md" "$HOME/AGENTS.md"
fi

if [[ ! -f "$HERMES_CRON_JOBS_FILE" ]]; then
  cp "$script_dir/jobs.template.md" "$HERMES_CRON_JOBS_FILE"
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
