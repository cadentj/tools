"""Help strings for the Google Calendar CLI."""

APP_HELP = (
    "Read-only Google Calendar CLI.\n\n"
    "Environment:\n"
    "  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN.\n"
    "  If on a machine with 1Password: op run --env-file .env -- calendar ..."
)

CALENDARS_HELP = "List all accessible calendars with their IDs."

EVENTS_HELP = "List upcoming events from a calendar."

EVENT_HELP = "Get full detail for a single event (attendees, links, description)."
