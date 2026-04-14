# Agent Runtime Notes

- The persistent working directory is `/data/home`.
- Keep persistent git clones under `/data/home/repos`, not `/app`.
- Cron jobs are defined in `/data/home/jobs.md`.
- For repo-local CLIs installed into `.venv`, prefer creating shell aliases or
  running them through `uv run` so you do not need to remember to activate the
  virtualenv first. Example aliases:
  `alias docs='/app/.venv/bin/docs'` and `alias cf-cron='/app/.venv/bin/cf-cron'`.
- If an incoming Telegram message starts with `⏰ `, treat the remainder of the
  message as a cron job name.
- For cron-triggered messages, read `/data/home/jobs.md`, find the matching
  `## Job Name` section, and execute the instructions in that section.
- If there is no matching job, explain that the cron job is unknown and do not
  invent behavior.
- Google tools (Docs, Calendar) are available as CLIs; see `.../tools/README.md` for commands and usage.
