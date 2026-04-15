"""Google Docs CLI: local OAuth; delegates operations to tools.docs.api."""

from __future__ import annotations

from googleapiclient.errors import HttpError
import typer

from tools.docs.api import (
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
from tools.docs.help import (
    APP_HELP,
    DELETE_RANGE_HELP,
    DELETE_ROW_HELP,
    DELETE_TAB_HELP,
    DOC_ID_HELP,
    GET_HELP,
    INSERT_HELP,
    INSERT_ROW_HELP,
    LINK_HELP,
    REPLACE_HELP,
    TAB_OPT_HELP,
    TABS_HELP,
    UPDATE_HELP,
)

app = typer.Typer(help=APP_HELP, no_args_is_help=True)
update_app = typer.Typer(help=UPDATE_HELP, no_args_is_help=True)
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
    tab: str = typer.Option("", "--tab", help=TAB_OPT_HELP),
) -> None:
    ctx.obj = {"tab": tab or None}


@app.callback()
def main_cb(
    ctx: typer.Context,
    doc_id: str = typer.Option(
        ...,
        "--doc-id",
        metavar="ID",
        help=DOC_ID_HELP,
    ),
) -> None:
    ctx.obj = {"doc_id": doc_id}


@app.command("tabs", help=TABS_HELP)
def cmd_tabs(ctx: typer.Context) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    print(tabs(_service(ctx), doc_id))


@app.command("get", help=GET_HELP)
def cmd_get(
    ctx: typer.Context,
    tab: str = typer.Option("", "--tab", help=TAB_OPT_HELP),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    print(get_tab(_service(ctx), doc_id, tab or None))


@update_app.command("append", help="Append text to the end of the tab.")
def update_append(ctx: typer.Context, text: str = typer.Argument(..., help="Text to append.")) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    print(append(_service(ctx), doc_id, text, tab))


@update_app.command("replace", help=REPLACE_HELP)
def update_replace(
    ctx: typer.Context,
    old: str = typer.Argument(..., help="Text or regex pattern to find."),
    new: str = typer.Argument(..., help="Replacement (backrefs with -E)."),
    regex: bool = typer.Option(False, "-E", "--regex", help="Treat 'old' as a Python regex."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = (ctx.parent.obj.get("tab") or "") if ctx.parent and ctx.parent.obj else ""
    print(replace(_service(ctx), doc_id, old, new, regex=regex, tab=tab))


@update_app.command("insert", help=INSERT_HELP)
def update_insert(
    ctx: typer.Context,
    index: int = typer.Argument(..., help="Character index (inclusive) from `get`."),
    text: str = typer.Argument(..., help="Text to insert."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    print(insert(_service(ctx), doc_id, index, text, tab))


@update_app.command("delete", help=DELETE_RANGE_HELP)
def update_delete(
    ctx: typer.Context,
    start_index: int = typer.Argument(..., help="Start index (inclusive)."),
    end_index: int = typer.Argument(..., help="End index (exclusive)."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    print(delete(_service(ctx), doc_id, start_index, end_index, tab))


@update_app.command("link", help=LINK_HELP)
def update_link(
    ctx: typer.Context,
    start_index: int = typer.Argument(..., help="Start index (inclusive)."),
    end_index: int = typer.Argument(..., help="End index (exclusive)."),
    url: str | None = typer.Argument(None, help="URL (omit to remove link)."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    print(link(_service(ctx), doc_id, start_index, end_index, url, tab))


@update_app.command("insert-table-row", help=INSERT_ROW_HELP)
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


@update_app.command("delete-table-row", help=DELETE_ROW_HELP)
def update_delete_table_row(
    ctx: typer.Context,
    table_index: int = typer.Argument(..., help="Index from <|TABLE|> line in `get`."),
    row: int = typer.Argument(..., help="Row index (0-based) to delete."),
) -> None:
    doc_id = _root_obj(ctx)["doc_id"]
    tab = ctx.parent.obj["tab"] if ctx.parent and ctx.parent.obj else None
    print(delete_table_row(_service(ctx), doc_id, table_index, row, tab))


@app.command("delete-tab", help=DELETE_TAB_HELP)
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
