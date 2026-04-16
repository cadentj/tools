#!/usr/bin/env bash
set -euo pipefail

umask 077

APP_DIR="/app"
HERMES_HOME="/data/.hermes"
CODEX_HOME="/data/.codex"

# Copy hermes-config.yaml to .hermes/config.yaml if it doesn't exist
# else, delete hermes-config.yaml
if [[ -f "$HERMES_HOME/config.yaml" ]]; then
  rm -f "$APP_DIR/hermes-config.yaml"
else
  cp "$APP_DIR/hermes-config.yaml" "$HERMES_HOME/config.yaml"
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
