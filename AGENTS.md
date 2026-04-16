## Available Commands

- Calendar: `/data/repos/tools/.venv/bin/calendar`
- Docs: `/data/repos/tools/.venv/bin/docs`
- Cron: `/data/repos/tools/.venv/bin/cf-cron`



## Workflow guidance

**docs**: 
- Prefer `update replace` for edits (no index bookkeeping). 
- Run `get` before positional edits; re-`get` after (indices shift). 
- Edit bottom-to-top for multiple index edits. 
- Run `tabs` first if tab names are unknown.

**cf-cron**: Edit `jobs.md` then `cf-cron sync`. Cron expressions are UTC; user is EDT (UTC-4).

Troubleshooting:
- `cf-cron list --remote` may crash with `AttributeError` (Cloudflare returns plain cron strings, not dicts). This does not mean sync failed.
- If the dashboard doesn't show the worker, verify `CLOUDFLARE_ACCOUNT_ID` matches the account you're viewing.
- On idling Fly deployments, cron runs can pile up — design prompts to summarize current state, not replay stale windows.

**calendar**:
- Run `/data/repos/tools/.venv/bin/calendar --help` for more information. 