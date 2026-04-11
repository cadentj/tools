#!/usr/bin/env python3
"""Google Docs CLI: local OAuth; delegates operations to tools.docs."""

from __future__ import annotations

import os
import sys
import textwrap

from googleapiclient.errors import HttpError
import typer

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from tools.docs import (  # noqa: E402
    append,
    delete,
    delete_tab,
    delete_table_row,
    get_service,
    get_tab,
    insert,
    insert_table_row,
    link,
    replace,
    tabs,
)

_APP_HELP = textwrap.dedent(
    """
    Edit Google Docs via the Docs API (OAuth). Install as the `docs` console script
    (see pyproject.toml); put .venv/bin on PATH or use a shell alias.

    \b
    Document ID (every command):
      Pass --doc-id with the raw ID from the URL (.../d/DOC_ID/edit/...), not the full URL.

    \b
    Environment:
      GOOGLE_DOCS_CREDENTIALS_JSON — OAuth client JSON (installed/ web client secret).
      GOOGLE_DOCS_TOKEN_JSON — authorized-user token JSON.
      With 1Password: op run --env-file .env -- docs ...

    \b
    Commands:
      tabs        List all tabs (titles and IDs, including nested).
      get         Print one tab as indexed text; use for character indices.
      delete-tab  Remove a tab by title or t.* ID (children removed too).
      update      Subcommands: append, replace, insert, delete, link, insert-table-row,
                  delete-table-row (see: docs update --help).

    \b
    Workflow:
      Prefer `update replace` when possible (no index bookkeeping).
      Run `tabs` first if tab names are unknown.
      Run `get` before insert/delete/link; re-get after positional edits (indices shift).
      For multiple index edits in one go, edit bottom-to-top so earlier indices stay valid.
    """
).strip()

_UPDATE_HELP = textwrap.dedent(
    """
    Edit the document. Target one tab with --tab on this group (title or t.* ID);
    default is the first tab.

    \b
    Without --tab: `replace` runs on ALL tabs; other subcommands use the first tab only.

    \b
    insert/delete/link use character indices from `get` output ([N] at line start).
    replace is literal (case-sensitive) unless -E; regex mode supports numeric backreferences in the replacement string.
    Table row commands use the table_index from the <|TABLE|> line in `get` output.
    """
).strip()

_DOC_ID_HELP = (
    "Raw Google Docs document ID from the URL (.../d/DOC_ID/edit), not a full URL."
)

_TAB_OPT_HELP = 'Tab title or tab ID like "t.xxx" (default: first tab).'

_GET_HELP = textwrap.dedent(
    """
    Print one tab as compact indexed text. Each line starts with [N] (character index).

    Markers: <|TABLE|> (rows below), <|IMAGE|> / <|IMAGE uri=...|>, <|LINK url=...|>text<|/LINK|>.
    """
).strip()

_TABS_HELP = "List every tab with title and ID (nested tabs indented)."

_DELETE_TAB_HELP = "Delete a tab by title or t.* ID; all child tabs are removed too."

_REPLACE_HELP = textwrap.dedent(
    """
    Find and replace in the tab (or all tabs if no --tab). Literal match is case-sensitive.
    Use -E for Python regex; replacement can reference regex groups (e.g. first group in replacement).
    """
).strip()

_INSERT_HELP = (
    "Insert text at character index (from `get`). Works inside table cells; indices come from `get`."
)

_DELETE_RANGE_HELP = "Delete characters [start_index, end_index) — half-open range from `get`."

_LINK_HELP = (
    "Set hyperlink on [start, end) or omit URL to remove link. Indices from `get`."
)

_INSERT_ROW_HELP = textwrap.dedent(
    """
    Insert a table row relative to row (0-based). table_index is the [N] on the <|TABLE|> line.
    Default inserts below; use --above to insert above.
    """
).strip()

_DELETE_ROW_HELP = (
    "Delete row (0-based) from the table whose <|TABLE|> line shows table_index."
)

app = typer.Typer(help=_APP_HELP, no_args_is_help=True)
update_app = typer.Typer(help=_UPDATE_HELP, no_args_is_help=True)
app.add_typer(update_app, name="update")


def _root_obj(ctx: typer.Context) -> dict:
    c = ctx
    while c.parent is not None:
        c = c.parent
    return c.obj


def _service(_ctx: typer.Context):
    return get_service()


@update_app.callback()
def update_cb(
    ctx: typer.Context,
    tab: str = typer.Option("", "--tab", help=_TAB_OPT_HELP),
) -> None:
    ctx.obj = {"tab": tab or None}


@app.callback()
def main_cb(
    ctx: typer.Context,
    doc_id: str = typer.Option(
        ...,
        "--doc-id",
        metavar="ID",
        help=_DOC_ID_HELP,
    ),
) -> None:
    ctx.obj = {"doc_id": doc_id}


@app.command("tabs", help=_TABS_HELP)
def cmd_tabs(ctx: typer.Context) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    print(tabs(_service(ctx), doc_id))


@app.command("get", help=_GET_HELP)
def cmd_get(
    ctx: typer.Context,
    tab: str = typer.Option("", "--tab", help=_TAB_OPT_HELP),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    print(get_tab(_service(ctx), doc_id, tab or None))


@update_app.command("append", help="Append text to the end of the tab.")
def update_append(ctx: typer.Context, text: str = typer.Argument(..., help="Text to append.")) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    print(append(_service(ctx), doc_id, text, tab))


@update_app.command("replace", help=_REPLACE_HELP)
def update_replace(
    ctx: typer.Context,
    old: str = typer.Argument(..., help="Text or regex pattern to find."),
    new: str = typer.Argument(..., help="Replacement (backrefs with -E)."),
    regex: bool = typer.Option(False, "-E", "--regex", help="Treat 'old' as a Python regex."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = (ctx.parent.obj.get("tab") or "") if ctx.parent and ctx.parent.obj else ""
    print(replace(_service(ctx), doc_id, old, new, regex=regex, tab=tab))


@update_app.command("insert", help=_INSERT_HELP)
def update_insert(
    ctx: typer.Context,
    index: int = typer.Argument(..., help="Character index (inclusive) from `get`."),
    text: str = typer.Argument(..., help="Text to insert."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    print(insert(_service(ctx), doc_id, index, text, tab))


@update_app.command("delete", help=_DELETE_RANGE_HELP)
def update_delete(
    ctx: typer.Context,
    start_index: int = typer.Argument(..., help="Start index (inclusive)."),
    end_index: int = typer.Argument(..., help="End index (exclusive)."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    print(delete(_service(ctx), doc_id, start_index, end_index, tab))


@update_app.command("link", help=_LINK_HELP)
def update_link(
    ctx: typer.Context,
    start_index: int = typer.Argument(..., help="Start index (inclusive)."),
    end_index: int = typer.Argument(..., help="End index (exclusive)."),
    url: str | None = typer.Argument(None, help="URL (omit to remove link)."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    print(link(_service(ctx), doc_id, start_index, end_index, url, tab))


@update_app.command("insert-table-row", help=_INSERT_ROW_HELP)
def update_insert_table_row(
    ctx: typer.Context,
    table_index: int = typer.Argument(..., help="Index from <|TABLE|> line in `get`."),
    row: int = typer.Argument(..., help="Row index (0-based) to insert next to."),
    above: bool = typer.Option(False, "--above", help="Insert above this row instead of below."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    below = not above
    print(
        insert_table_row(
            _service(ctx),
            doc_id,
            table_index,
            row,
            below=below,
            tab=tab,
        )
    )


@update_app.command("delete-table-row", help=_DELETE_ROW_HELP)
def update_delete_table_row(
    ctx: typer.Context,
    table_index: int = typer.Argument(..., help="Index from <|TABLE|> line in `get`."),
    row: int = typer.Argument(..., help="Row index (0-based) to delete."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    print(delete_table_row(_service(ctx), doc_id, table_index, row, tab))


@app.command("delete-tab", help=_DELETE_TAB_HELP)
def cmd_delete_tab(
    ctx: typer.Context,
    tab: str = typer.Argument(..., help="Tab title or t.* ID."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    print(delete_tab(_service(ctx), doc_id, tab))


def main() -> None:
    try:
        app()
    except HttpError as err:
        typer.echo(f"API error: {err}", err=True)
        raise typer.Exit(1) from None
    except (ValueError, RuntimeError, OSError) as err:
        typer.echo(str(err), err=True)
        raise typer.Exit(1) from None


if __name__ == "__main__":
    main()
