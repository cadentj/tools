from __future__ import annotations

import os
import sys

from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP  # type: ignore

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

mcp = FastMCP("docs-mcp")


def _tool_result(action):
    try:
        return action()
    except HttpError as err:
        return f"API error: {err}"
    except Exception as err:
        return f"error: {err}"


@mcp.tool()
def docs_tabs(doc_id: str) -> str:
    """List all tabs for a Google Doc.

    Args:
        doc_id: Raw Google Docs document ID.
    """

    def action() -> str:
        service = get_service(allow_browser_flow=False)
        return tabs(service, doc_id)

    return _tool_result(action)


@mcp.tool()
def docs_get(doc_id: str, tab: str = "") -> str:
    """Get one tab from a Google Doc in indexed plain-text form.

    Args:
        doc_id: Raw Google Docs document ID.
        tab: Tab title or tab ID. Defaults to the first tab.
    """

    def action() -> str:
        service = get_service(allow_browser_flow=False)
        return get_tab(service, doc_id, tab or None)

    return _tool_result(action)


@mcp.tool()
def docs_append(doc_id: str, text: str, tab: str = "") -> str:
    """Append text to the end of a tab.

    Args:
        doc_id: Raw Google Docs document ID.
        text: Text to append.
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = get_service(allow_browser_flow=False)
        return append(service, doc_id, text, tab or None)

    return _tool_result(action)


@mcp.tool()
def docs_replace(
    doc_id: str,
    old: str,
    new: str,
    regex: bool = False,
    tab: str = "",
) -> str:
    """Find and replace text.

    Args:
        doc_id: Raw Google Docs document ID.
        old: Search text (literal or regex pattern).
        new: Replacement text.
        regex: When true, treat 'old' as a regex pattern.
        tab: Optional tab title/ID. With regex=false and no tab, replaces across all tabs.
    """

    def action() -> str:
        service = get_service(allow_browser_flow=False)
        return replace(service, doc_id, old, new, regex=regex, tab=tab)

    return _tool_result(action)


@mcp.tool()
def docs_insert(doc_id: str, index: int, text: str, tab: str = "") -> str:
    """Insert text at a specific index.

    Args:
        doc_id: Raw Google Docs document ID.
        index: Character index to insert at.
        text: Text to insert.
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = get_service(allow_browser_flow=False)
        return insert(service, doc_id, index, text, tab or None)

    return _tool_result(action)


@mcp.tool()
def docs_delete(doc_id: str, start_index: int, end_index: int, tab: str = "") -> str:
    """Delete a text range [start_index, end_index).

    Args:
        doc_id: Raw Google Docs document ID.
        start_index: Start index (inclusive).
        end_index: End index (exclusive).
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = get_service(allow_browser_flow=False)
        return delete(service, doc_id, start_index, end_index, tab or None)

    return _tool_result(action)


@mcp.tool()
def docs_link(doc_id: str, start_index: int, end_index: int, url: str = "", tab: str = "") -> str:
    """Add or remove a hyperlink on a range.

    Args:
        doc_id: Raw Google Docs document ID.
        start_index: Start index (inclusive).
        end_index: End index (exclusive).
        url: URL to set. Empty string removes the link.
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = get_service(allow_browser_flow=False)
        return link(service, doc_id, start_index, end_index, url or None, tab or None)

    return _tool_result(action)


@mcp.tool()
def docs_insert_table_row(
    doc_id: str,
    table_index: int,
    row: int,
    below: bool = True,
    tab: str = "",
) -> str:
    """Insert a row in a table.

    Args:
        doc_id: Raw Google Docs document ID.
        table_index: Start index of the target table element.
        row: Row index (0-based) to insert relative to.
        below: Insert below when true, above when false.
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = get_service(allow_browser_flow=False)
        return insert_table_row(service, doc_id, table_index, row, below=below, tab=tab or None)

    return _tool_result(action)


@mcp.tool()
def docs_delete_table_row(doc_id: str, table_index: int, row: int, tab: str = "") -> str:
    """Delete a table row.

    Args:
        doc_id: Raw Google Docs document ID.
        table_index: Start index of the target table element.
        row: Row index (0-based) to delete.
        tab: Tab title or ID. Defaults to the first tab.
    """

    def action() -> str:
        service = get_service(allow_browser_flow=False)
        return delete_table_row(service, doc_id, table_index, row, tab or None)

    return _tool_result(action)


@mcp.tool()
def docs_delete_tab(doc_id: str, tab: str) -> str:
    """Delete a tab by title or ID.

    Args:
        doc_id: Raw Google Docs document ID.
        tab: Tab title or tab ID.
    """

    def action() -> str:
        service = get_service(allow_browser_flow=False)
        return delete_tab(service, doc_id, tab)

    return _tool_result(action)


if __name__ == "__main__":
    mcp.run(transport="stdio")
