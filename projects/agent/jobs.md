# Hermes Cron Jobs

Each job starts with a `##` heading. When Hermes receives a message like
`⏰ Daily Calendar Check-In` or `⏰ Two-Hour Todo Check-In`, it should open
this file, find the matching heading, and carry out the instructions in that section.

## Daily Calendar Check-In
- cron: 30 14 * * *
- enabled: true

Run `git pull` in `$HOME/repos/tools` and `$HOME/repos/sinnoh` to get the latest task lists.
Run `calendar events --from $(date -u +%Y-%m-%dT00:00:00Z) --to $(date -u +%Y-%m-%dT23:59:59Z)` to get today's calendar events.
Ping Caden with a short, warm greeting summarizing the day's schedule and the top priority todo items (priority >= 6).
Style constraints:
- Keep it concise (1-3 sentences).
- No system terminology (avoid saying "cron", "git pull", etc.).
- Only list the events/todos if there are any.

## Two-Hour Todo Check-In
- cron: 30 13,15,17,19,21,23,1,3 * * *
- enabled: true

EST Schedule: 9:30 AM, 11:30 AM, 1:30 PM, 3:30 PM, 5:30 PM, 7:30 PM, 9:30 PM, 11:30 PM

Run `git pull` in `$HOME/repos/tools` and `$HOME/repos/sinnoh` to get the latest task lists.
Check Caden's top-priority todo items (priority >= 6).
Briefly ping Caden to check in on progress, mentioning a relevant todo item or asking for a quick status update.
Peek at memory if needed to ensure nudges stay relevant to the current day's plan.

Style constraints:
- Keep it concise (1-3 sentences).
- No system terminology.
- Mention only relevant items.