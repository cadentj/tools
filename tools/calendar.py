"""Google Calendar API core: auth and read-only event operations.

Used by mcp/calendar-mcp. Configuration: see ``.env.template`` at the repo root.
Shares OAuth credentials with tools/docs (GOOGLE_DOCS_CREDENTIALS_JSON /
GOOGLE_DOCS_TOKEN_JSON). Re-auth is required when adding the calendar scope for
the first time.
"""

from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build

from tools.google_auth import get_credentials


def get_service() -> Any:
    """Build the Google Calendar API service."""
    return build("calendar", "v3", credentials=get_credentials())


def _fmt_datetime(dt: dict[str, Any]) -> str:
    """Return a human-readable string from a Calendar dateTime or date dict."""
    return dt.get("dateTime") or dt.get("date") or ""


def list_calendars(service: Any) -> str:
    """Return all calendars the user has access to."""
    result = service.calendarList().list().execute()
    items = result.get("items", [])
    if not items:
        return "No calendars found."

    lines = []
    for cal in items:
        cal_id = cal.get("id", "")
        summary = cal.get("summary", "(untitled)")
        primary = " [primary]" if cal.get("primary") else ""
        lines.append(f"- {summary}{primary}  [{cal_id}]")
    return "\n".join(lines)


def list_events(
    service: Any,
    calendar_id: str = "primary",
    time_min: str = "",
    time_max: str = "",
    max_results: int = 20,
) -> str:
    """Return upcoming events from a calendar.

    Args:
        service: Calendar API service.
        calendar_id: Calendar ID (use 'primary' for the main calendar).
        time_min: ISO 8601 lower bound, e.g. '2026-04-14T00:00:00Z'. Defaults to now.
        time_max: ISO 8601 upper bound. Optional.
        max_results: Maximum number of events to return (max 250).
    """
    import datetime

    kwargs: dict[str, Any] = {
        "calendarId": calendar_id,
        "maxResults": min(max_results, 250),
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if time_min:
        kwargs["timeMin"] = time_min
    else:
        kwargs["timeMin"] = datetime.datetime.utcnow().isoformat() + "Z"
    if time_max:
        kwargs["timeMax"] = time_max

    result = service.events().list(**kwargs).execute()
    items = result.get("items", [])
    if not items:
        return "No events found."

    lines = []
    for event in items:
        event_id = event.get("id", "")
        summary = event.get("summary", "(no title)")
        start = _fmt_datetime(event.get("start", {}))
        end = _fmt_datetime(event.get("end", {}))
        lines.append(f"- [{start} → {end}] {summary}  [id:{event_id}]")
    return "\n".join(lines)


def get_event(service: Any, calendar_id: str, event_id: str) -> str:
    """Return full detail for a single event.

    Args:
        service: Calendar API service.
        calendar_id: Calendar ID.
        event_id: Event ID.
    """
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

    summary = event.get("summary", "(no title)")
    status = event.get("status", "")
    start = _fmt_datetime(event.get("start", {}))
    end = _fmt_datetime(event.get("end", {}))
    location = event.get("location", "")
    description = event.get("description", "")
    organizer = event.get("organizer", {}).get("email", "")
    attendees = event.get("attendees", [])
    conference = event.get("conferenceData", {})
    hangout_link = event.get("hangoutLink", "")

    lines = [
        f"# {summary}",
        f"Status: {status}",
        f"Start:  {start}",
        f"End:    {end}",
    ]
    if location:
        lines.append(f"Location: {location}")
    if organizer:
        lines.append(f"Organizer: {organizer}")
    if attendees:
        lines.append("Attendees:")
        for a in attendees:
            resp = a.get("responseStatus", "")
            lines.append(f"  - {a.get('email', '')} ({resp})")
    if hangout_link:
        lines.append(f"Meet link: {hangout_link}")
    elif conference:
        entry_points = conference.get("entryPoints", [])
        for ep in entry_points:
            if ep.get("entryPointType") == "video":
                lines.append(f"Video link: {ep.get('uri', '')}")
                break
    if description:
        lines.append(f"\n{description}")

    return "\n".join(lines)
