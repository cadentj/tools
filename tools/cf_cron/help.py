"""Help strings for the Cloudflare cron CLI."""

import textwrap

APP_HELP = textwrap.dedent(
    """
    Manage a shared Cloudflare Worker that triggers Hermes cron jobs via
    synthetic Telegram webhook messages.

    \b
    The job registry is a Markdown file (level-2 headings per job).
    Edit jobs.md, then run `cf-cron sync` to deploy.

    \b
    Required env vars:
      TELEGRAM_ALLOWED_USERS    — comma-separated Telegram user IDs.
      TELEGRAM_WEBHOOK_URL      — Hermes gateway webhook URL.
      TELEGRAM_WEBHOOK_SECRET   — shared secret for webhook auth.
      CLOUDFLARE_ACCOUNT_ID     — Cloudflare account ID.
      CLOUDFLARE_API_TOKEN      — Cloudflare API token with Workers permissions.

    \b
    Optional env vars:
      HERMES_CRON_JOBS_FILE     — path to jobs.md (default: /data/home/jobs.md).
      HERMES_CRON_TRIGGER_USER_ID — Telegram user ID for cron messages
                                    (default: first ID in TELEGRAM_ALLOWED_USERS).
      CLOUDFLARE_WORKER_NAME    — worker name (default: hermes-cron).

    \b
    Cron expressions are UTC. Use explicit comma-separated hour lists
    (e.g. `30 13,15,17,19,21,23 * * *`), not shorthand ranges.
    """
).strip()

INIT_HELP = "Create a starter jobs.md file."

VALIDATE_HELP = "Parse and validate jobs.md without deploying."

LIST_HELP = "Show local jobs (and optionally remote Cloudflare schedules with --remote)."

SYNC_HELP = "Deploy the worker and schedules to Cloudflare from jobs.md."

TRIGGER_HELP = "Manually fire a job by sending a synthetic webhook message to Hermes."
