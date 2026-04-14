# Hermes Cron Jobs

Each job starts with a `##` heading. When Hermes receives a message like
`⏰ Morning Check-In`, it should open this file, find the matching heading, and
carry out the instructions in that section.

## Morning Check-In
- cron: 0 13 * * *
- enabled: true

Review overnight activity, summarize anything urgent, and send the first
reply that needs to go out this morning.
