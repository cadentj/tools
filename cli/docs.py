#!/usr/bin/env python3
"""Google Docs CLI: local OAuth; delegates operations to tools.docs."""

from __future__ import annotations

import argparse
import os
import sys

from googleapiclient.errors import HttpError

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


def cmd_tabs(args: argparse.Namespace) -> None:
    service = get_service(allow_browser_flow=True)
    print(tabs(service, args.doc_id))


def cmd_get(args: argparse.Namespace) -> None:
    service = get_service(allow_browser_flow=True)
    print(get_tab(service, args.doc_id, getattr(args, "tab", None)))


def cmd_append(args: argparse.Namespace) -> None:
    service = get_service(allow_browser_flow=True)
    print(append(service, args.doc_id, args.text, getattr(args, "tab", None)))


def cmd_replace(args: argparse.Namespace) -> None:
    service = get_service(allow_browser_flow=True)
    print(
        replace(
            service,
            args.doc_id,
            args.old,
            args.new,
            regex=getattr(args, "regex", False),
            tab=getattr(args, "tab", "") or "",
        )
    )


def cmd_insert(args: argparse.Namespace) -> None:
    service = get_service(allow_browser_flow=True)
    print(insert(service, args.doc_id, args.index, args.text, getattr(args, "tab", None)))


def cmd_delete(args: argparse.Namespace) -> None:
    service = get_service(allow_browser_flow=True)
    print(
        delete(
            service,
            args.doc_id,
            args.start_index,
            args.end_index,
            getattr(args, "tab", None),
        )
    )


def cmd_link(args: argparse.Namespace) -> None:
    service = get_service(allow_browser_flow=True)
    print(
        link(
            service,
            args.doc_id,
            args.start_index,
            args.end_index,
            args.url,
            getattr(args, "tab", None),
        )
    )


def cmd_insert_table_row(args: argparse.Namespace) -> None:
    service = get_service(allow_browser_flow=True)
    print(
        insert_table_row(
            service,
            args.doc_id,
            args.table_index,
            args.row,
            below=args.below,
            tab=getattr(args, "tab", None),
        )
    )


def cmd_delete_table_row(args: argparse.Namespace) -> None:
    service = get_service(allow_browser_flow=True)
    print(
        delete_table_row(
            service,
            args.doc_id,
            args.table_index,
            args.row,
            getattr(args, "tab", None),
        )
    )


def cmd_delete_tab(args: argparse.Namespace) -> None:
    service = get_service(allow_browser_flow=True)
    print(delete_tab(service, args.doc_id, args.tab))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Google Docs CLI")
    parser.add_argument(
        "--doc-id",
        required=True,
        help="Google Docs document ID (raw ID only, not a URL)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("tabs", help="List all document tabs")

    get_parser = subparsers.add_parser("get", help="Fetch and display a tab")
    get_parser.add_argument("--tab", help="Tab title or ID (default: first tab)")

    update_parser = subparsers.add_parser("update", help="Edit the document")
    update_parser.add_argument("--tab", help="Tab title or ID (default: first tab)")
    update_sub = update_parser.add_subparsers(dest="action", required=True)

    append_p = update_sub.add_parser("append", help="Append text to end of tab")
    append_p.add_argument("text", help="Text to append")

    replace_p = update_sub.add_parser("replace", help="Find and replace text")
    replace_p.add_argument("old", help="Text to find (literal or regex pattern)")
    replace_p.add_argument("new", help="Replacement text (supports \\1, \\2 backrefs with -E)")
    replace_p.add_argument("-E", "--regex", action="store_true", help="Treat 'old' as a regex pattern")

    insert_p = update_sub.add_parser("insert", help="Insert text at index")
    insert_p.add_argument("index", type=int, help="Character index to insert at")
    insert_p.add_argument("text", help="Text to insert")

    delete_p = update_sub.add_parser("delete", help="Delete a range of text")
    delete_p.add_argument("start_index", type=int, help="Start index (inclusive)")
    delete_p.add_argument("end_index", type=int, help="End index (exclusive)")

    link_p = update_sub.add_parser("link", help="Add or remove a hyperlink on a text range")
    link_p.add_argument("start_index", type=int, help="Start index (inclusive)")
    link_p.add_argument("end_index", type=int, help="End index (exclusive)")
    link_p.add_argument("url", nargs="?", default=None, help="URL to link to (omit to remove link)")

    insert_row_p = update_sub.add_parser("insert-table-row", help="Insert a row into a table")
    insert_row_p.add_argument("table_index", type=int, help="Start index of the table element")
    insert_row_p.add_argument("row", type=int, help="Row index (0-based) to insert relative to")
    insert_row_p.add_argument("--below", action="store_true", default=True, help="Insert below (default)")
    insert_row_p.add_argument("--above", action="store_true", dest="above", help="Insert above instead")

    delete_row_p = update_sub.add_parser("delete-table-row", help="Delete a row from a table")
    delete_row_p.add_argument("table_index", type=int, help="Start index of the table element")
    delete_row_p.add_argument("row", type=int, help="Row index (0-based) to delete")

    delete_tab_parser = subparsers.add_parser("delete-tab", help="Delete a tab")
    delete_tab_parser.add_argument("tab", help="Tab title or ID to delete")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "tabs":
            cmd_tabs(args)
        elif args.command == "get":
            cmd_get(args)
        elif args.command == "delete-tab":
            cmd_delete_tab(args)
        elif args.command == "update":
            if args.action == "insert-table-row":
                if getattr(args, "above", False):
                    args.below = False
                cmd_insert_table_row(args)
            elif args.action == "delete-table-row":
                cmd_delete_table_row(args)
            else:
                {
                    "append": cmd_append,
                    "replace": cmd_replace,
                    "insert": cmd_insert,
                    "delete": cmd_delete,
                    "link": cmd_link,
                }[args.action](args)
    except HttpError as err:
        print(f"API error: {err}", file=sys.stderr)
        sys.exit(1)
    except ValueError as err:
        print(err, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
