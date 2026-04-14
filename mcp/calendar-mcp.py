from __future__ import annotations

import os
import sys

from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP  # type: ignore

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.calendar import (  # noqa: E402
    get_event,
    get_service,
    list_calendars,
    list_events,
)

mcp = FastMCP("calendar-mcp")


def _tool_result(action):
    try:
        return action()
    except HttpError as err:
        return f"API error: {err}"
    except Exception as err:
        return f"error: {err}"


@mcp.tool()
def calendar_list_calendars() -> str:
    """List all Google Calendars the user has access to, with their IDs."""

    def action() -> str:
        service = get_service()
        return list_calendars(service)

    return _tool_result(action)


@mcp.tool()
def calendar_list_events(
    calendar_id: str = "primary",
    time_min: str = "",
    time_max: str = "",
    max_results: int = 20,
) -> str:
    """List upcoming events from a Google Calendar.

    Args:
        calendar_id: Calendar ID. Use 'primary' for the main calendar.
        time_min: ISO 8601 lower bound, e.g. '2026-04-14T00:00:00Z'. Defaults to now.
        time_max: ISO 8601 upper bound. Optional.
        max_results: Number of events to return (max 250).
    """

    def action() -> str:
        service = get_service()
        return list_events(service, calendar_id, time_min, time_max, max_results)

    return _tool_result(action)


@mcp.tool()
def calendar_get_event(calendar_id: str, event_id: str) -> str:
    """Get full details for a single calendar event.

    Args:
        calendar_id: Calendar ID the event belongs to.
        event_id: Event ID (from calendar_list_events output).
    """

    def action() -> str:
        service = get_service()
        return get_event(service, calendar_id, event_id)

    return _tool_result(action)


if __name__ == "__main__":
    mcp.run(transport="stdio")
