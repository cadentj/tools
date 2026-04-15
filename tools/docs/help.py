"""Help strings for the Google Docs CLI."""

import textwrap

APP_HELP = textwrap.dedent(
    """
    Edit Google Docs via the Docs API (OAuth).

    \b
    Document ID (every command):
      Pass --doc-id with the raw ID from the URL (.../d/DOC_ID/edit/...), not the full URL.

    \b
    Environment:
      GOOGLE_CLIENT_ID          — OAuth client ID.
      GOOGLE_CLIENT_SECRET      — OAuth client secret.
      GOOGLE_REFRESH_TOKEN      — authorized-user refresh token.
      If on a machine with 1Password: op run --env-file .env -- docs ...

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

UPDATE_HELP = textwrap.dedent(
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

DOC_ID_HELP = (
    "Raw Google Docs document ID from the URL (.../d/DOC_ID/edit), not a full URL."
)

TAB_OPT_HELP = 'Tab title or tab ID like "t.xxx" (default: first tab).'

GET_HELP = textwrap.dedent(
    """
    Print one tab as compact indexed text. Each line starts with [N] (character index).

    \b
    Markers:
      <|TABLE|>              Table (rows printed below).
      <|IMAGE|>              Inline image (may include uri=...).
      <|LINK url=...|>text<|/LINK|>  Hyperlink.

    \b
    Example output:
      [1] # Weekly Goals
      [16] - Finish the API integration
      [90]
      [91] <|TABLE|>
        Row 1: | Column A | Column B |
        Row 2: | Data 1 | Data 2 |
      [150] Check out <|LINK url=https://example.com|>this page<|/LINK|>
      [200] <|IMAGE uri=https://lh7-us.googleusercontent.com/...|>
    """
).strip()

TABS_HELP = "List every tab with title and ID (nested tabs indented)."

DELETE_TAB_HELP = "Delete a tab by title or t.* ID; all child tabs are removed too."

REPLACE_HELP = textwrap.dedent(
    """
    Find and replace in the tab (or all tabs if no --tab). Literal match is case-sensitive.
    Use -E for Python regex; replacement can reference regex groups (e.g. first group in replacement).
    """
).strip()

INSERT_HELP = (
    "Insert text at character index (from `get`). Works inside table cells; indices come from `get`."
)

DELETE_RANGE_HELP = "Delete characters [start_index, end_index) — half-open range from `get`."

LINK_HELP = (
    "Set hyperlink on [start, end) or omit URL to remove link. Indices from `get`."
)

INSERT_ROW_HELP = textwrap.dedent(
    """
    Insert a table row relative to row (0-based). table_index is the [N] on the <|TABLE|> line.
    Default inserts below; use --above to insert above.
    """
).strip()

DELETE_ROW_HELP = (
    "Delete row (0-based) from the table whose <|TABLE|> line shows table_index."
)
