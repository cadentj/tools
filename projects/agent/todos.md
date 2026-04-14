# TODOs

- Copy the template and fill in your values:
  ```bash
  cp .env.template .env
  ```
- Load the variables into your shell:
  ```bash
  set -a
  source .env
  set +a
  ```
- Make sure `fly.toml` has your real Fly app name in `app = "..."`
- Create the Fly app:
  ```bash
  fly apps create "$FLY_APP_NAME"
  ```
- Create the persistent volume in `ewr`:
  ```bash
  fly volumes create "$FLY_VOLUME_NAME" --region "$FLY_PRIMARY_REGION" --size "$FLY_VOLUME_SIZE_GB" -a "$FLY_APP_NAME"
  ```
- Set Telegram secrets:
  ```bash
  fly secrets set -a "$FLY_APP_NAME" \
    TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
    TELEGRAM_ALLOWED_USERS="$TELEGRAM_ALLOWED_USERS" \
    TELEGRAM_WEBHOOK_URL="$TELEGRAM_WEBHOOK_URL" \
    TELEGRAM_WEBHOOK_SECRET="$TELEGRAM_WEBHOOK_SECRET" \
    CLOUDFLARE_ACCOUNT_ID="$CLOUDFLARE_ACCOUNT_ID" \
    CLOUDFLARE_API_TOKEN="$CLOUDFLARE_API_TOKEN" \
    CLOUDFLARE_WORKER_NAME="$CLOUDFLARE_WORKER_NAME" \
    HERMES_CRON_JOBS_FILE="$HERMES_CRON_JOBS_FILE" \
    HERMES_CRON_TRIGGER_USER_ID="$HERMES_CRON_TRIGGER_USER_ID" \
    GH_TOKEN="$GH_TOKEN" \
    GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
    GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
    GOOGLE_REFRESH_TOKEN="$GOOGLE_REFRESH_TOKEN"
  ```
- Clone the persistent repos onto the Fly volume:
  ```bash
  /app/init.sh
  ```
- Initialize the cron jobs file inside the machine:
  ```bash
  uv run cf-cron init
  ```
- Validate the cron file before syncing:
  ```bash
  uv run cf-cron validate
  ```
- Sync Cloudflare schedules and the Worker:
  ```bash
  uv run cf-cron sync
  ```
- Deploy once:
  ```bash
  fly deploy -a "$FLY_APP_NAME"
  ```
- Start the machine if it is stopped:
  ```bash
  fly machine start "$(fly machine list -q -a "$FLY_APP_NAME" | awk 'NF{print $1; exit}')"
  ```
- Upload your local Codex auth file onto the volume:
  ```bash
  fly ssh sftp put ~/.codex/auth.json /data/home/.codex/auth.json -a "$FLY_APP_NAME"
  ```
- Restart the machine:
  ```bash
  fly machine restart "$(fly machine list -q -a "$FLY_APP_NAME" | awk 'NF{print $1; exit}')" -a "$FLY_APP_NAME"
  ```
- Check logs:
  ```bash
  fly logs -a "$FLY_APP_NAME"
  ```
- SSH in if needed:
  ```bash
  fly ssh console -a "$FLY_APP_NAME"
  ```
- Verify the auth file and Hermes status inside the machine:
  ```bash
  ls -l /data/home/.codex/auth.json
  /opt/venv/bin/hermes status
  ```
- Check Telegram's webhook:
  ```bash
  curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"
  ```
- Trigger one cron job manually:
  ```bash
  uv run cf-cron trigger morning-check-in
  ```
- Send a Telegram message from an allowed user and confirm Hermes replies.
