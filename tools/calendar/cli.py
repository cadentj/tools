"""Google Calendar CLI: read-only; delegates to tools.calendar.api."""

from __future__ import annotations

from googleapiclient.errors import HttpError
import typer

from tools.calendar.api import (
    get_event,
    get_service,
    list_calendars,
    list_events,
)
from tools.calendar.help import APP_HELP, CALENDARS_HELP, EVENT_HELP, EVENTS_HELP

app = typer.Typer(help=APP_HELP, no_args_is_help=True)


@app.command("calendars", help=CALENDARS_HELP)
def cmd_calendars() -> None:
    print(list_calendars(get_service()))


@app.command("events", help=EVENTS_HELP)
def cmd_events(
    calendar_id: str = typer.Option("primary", "--calendar", "-c", help="Calendar ID (default: primary)."),
    time_min: str = typer.Option("", "--from", help="ISO 8601 start, e.g. 2026-04-14T00:00:00Z. Defaults to now."),
    time_max: str = typer.Option("", "--to", help="ISO 8601 end. Optional."),
    max_results: int = typer.Option(20, "--max", "-n", help="Max events to return."),
) -> None:
    print(list_events(get_service(), calendar_id, time_min, time_max, max_results))


@app.command("event", help=EVENT_HELP)
def cmd_event(
    event_id: str = typer.Argument(..., help="Event ID from `events` output."),
    calendar_id: str = typer.Option("primary", "--calendar", "-c", help="Calendar ID."),
) -> None:
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
