"""Google Calendar API core: auth and read-only event operations."""

from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build
from pydantic import BaseModel, Field

from tools.common.google_auth import get_credentials


class EventTime(BaseModel):
    dateTime: str | None = None
    date: str | None = None

    def display(self) -> str:
        return self.dateTime or self.date or ""


class Organizer(BaseModel):
    email: str | None = None


class Attendee(BaseModel):
    email: str | None = None
    responseStatus: str | None = None


class ConferenceEntryPoint(BaseModel):
    entryPointType: str | None = None
    uri: str | None = None


class ConferenceData(BaseModel):
    entryPoints: list[ConferenceEntryPoint] = Field(default_factory=list)


class CalendarEventDetail(BaseModel):
    summary: str | None = Field(default=None)
    status: str = ""
    start: EventTime = Field(default_factory=EventTime)
    end: EventTime = Field(default_factory=EventTime)
    location: str = ""
    description: str = ""
    organizer: Organizer | None = None
    attendees: list[Attendee] = Field(default_factory=list)
    conference_data: ConferenceData | None = Field(None, alias="conferenceData")
    hangout_link: str | None = Field(None, alias="hangoutLink")


def _event_summary_title(e: CalendarEventDetail) -> str:
    if e.summary is None:
        return "(no title)"
    return e.summary


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
    """Return upcoming events from a calendar."""
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
        kwargs["timeMin"] = (
            datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
        )
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
    """Return full detail for a single event."""
    raw = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    e = CalendarEventDetail.model_validate(raw)

    summary = _event_summary_title(e)
    organizer = e.organizer.email if e.organizer else ""

    lines = [
        f"# {summary}",
        f"Status: {e.status}",
        f"Start:  {e.start.display()}",
        f"End:    {e.end.display()}",
    ]
    if e.location:
        lines.append(f"Location: {e.location}")
    if organizer:
        lines.append(f"Organizer: {organizer}")
    if e.attendees:
        lines.append("Attendees:")
        for a in e.attendees:
            resp = a.responseStatus or ""
            lines.append(f"  - {a.email or ''} ({resp})")
    if e.hangout_link:
        lines.append(f"Meet link: {e.hangout_link}")
    elif e.conference_data:
        for ep in e.conference_data.entryPoints:
            if ep.entryPointType == "video":
                lines.append(f"Video link: {ep.uri or ''}")
                break
    if e.description:
        lines.append(f"\n{e.description}")

    return "\n".join(lines)
