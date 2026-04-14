#!/usr/bin/env python3
"""Google Calendar CLI: read-only; delegates to tools.calendar."""

from __future__ import annotations

import os
import sys

from googleapiclient.errors import HttpError
import typer

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.calendar import (  # noqa: E402
    get_event,
    get_service,
    list_calendars,
    list_events,
)

app = typer.Typer(
    help="Read-only Google Calendar CLI. Use `op run --env-file .env -- calendar ...`",
    no_args_is_help=True,
)


@app.command("calendars")
def cmd_calendars() -> None:
    """List all calendars with their IDs."""
    print(list_calendars(get_service()))


@app.command("events")
def cmd_events(
    calendar_id: str = typer.Option("primary", "--calendar", "-c", help="Calendar ID (default: primary)."),
    time_min: str = typer.Option("", "--from", help="ISO 8601 start, e.g. 2026-04-14T00:00:00Z. Defaults to now."),
    time_max: str = typer.Option("", "--to", help="ISO 8601 end. Optional."),
    max_results: int = typer.Option(20, "--max", "-n", help="Max events to return."),
) -> None:
    """List upcoming events."""
    print(list_events(get_service(), calendar_id, time_min, time_max, max_results))


@app.command("event")
def cmd_event(
    event_id: str = typer.Argument(..., help="Event ID from `events` output."),
    calendar_id: str = typer.Option("primary", "--calendar", "-c", help="Calendar ID."),
) -> None:
    """Get full detail for a single event."""
    print(get_event(get_service(), calendar_id, event_id))


def main() -> None:
    try:
        app()
    except HttpError as err:
        typer.echo(f"API error: {err}", err=True)
        raise typer.Exit(1) from None
    except (ValueError, RuntimeError) as err:
        typer.echo(str(err), err=True)
        raise typer.Exit(1) from None


if __name__ == "__main__":
    main()
