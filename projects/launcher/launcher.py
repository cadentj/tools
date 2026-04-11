"""Fuzzy launcher TUI for macOS — open installed applications only.

Keyboard: Up from the first result clears list highlight so you can edit the query;
  Down from no highlight selects the first result. Escape quits.

Apps are discovered under /Applications, /System/Applications, and ~/Applications.
When the query is empty, running GUI apps (via System Events) are listed first; `osascript`
  runs only in that case (see `_empty_query_order`), not while you are typing a filter.

With an empty search, keys 1–9 then 0 select the first ten visible rows (1 = first row,
  0 = tenth); hints appear as (1)…(9), (0) in the list. The chosen label is printed to
  stdout, then that app is opened.
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from re import finditer
from typing import Sequence

from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.content import Content
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option

# ---------------------------------------------------------------------------
# Fuzzy search (adapted from textual internals / textual-autocomplete)
# ---------------------------------------------------------------------------


class FuzzySearch:
    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], tuple[float, Sequence[int]]] = {}

    def match(self, query: str, candidate: str) -> tuple[float, Sequence[int]]:
        key = (query, candidate)
        if key in self._cache:
            return self._cache[key]
        default: tuple[float, Sequence[int]] = (0.0, ())
        result = max(self._match(query, candidate), key=lambda r: r[0], default=default)
        self._cache[key] = result
        return result

    @staticmethod
    @lru_cache(maxsize=1024)
    def _first_letters(candidate: str) -> frozenset[int]:
        return frozenset(m.start() for m in finditer(r"\w+", candidate))

    def _score(self, candidate: str, positions: Sequence[int]) -> float:
        first = self._first_letters(candidate)
        n = len(positions)
        score = float(n + len(first.intersection(positions)))
        groups, last = 1, positions[0]
        for off in positions[1:]:
            if off != last + 1:
                groups += 1
            last = off
        norm = (n - (groups - 1)) / n
        score *= 1 + norm * norm
        return score

    def _match(self, query: str, candidate: str):
        q, c = query.lower(), candidate.lower()
        if q in c:
            loc = c.rfind(q)
            offsets = list(range(loc, loc + len(q)))
            yield self._score(c, offsets) * (2.0 if c == q else 1.5), offsets
            return
        letter_positions: list[list[int]] = []
        pos = 0
        for i, ch in enumerate(q):
            positions: list[int] = []
            letter_positions.append(positions)
            idx = pos
            while (loc := c.find(ch, idx)) != -1:
                positions.append(loc)
                idx = loc + 1
                if idx >= len(c) - i:
                    break
            if not positions:
                yield (0.0, ())
                return
            pos = positions[0] + 1
        results: list[list[int]] = []
        qlen = len(q)

        def _recurse(offsets: list[int], pi: int) -> None:
            for off in letter_positions[pi]:
                if not offsets or off > offsets[-1]:
                    new = [*offsets, off]
                    if len(new) == qlen:
                        results.append(new)
                    else:
                        _recurse(new, pi + 1)

        _recurse([], 0)
        for offsets in results:
            yield self._score(c, offsets), offsets


_fuzzy = FuzzySearch()

# Optional prefix per .app name (stem). Shown in the list only; search still uses the plain
# label so typing “slack” / “arc” still works. Edit freely — emoji render in Ghostty/iTerm;
# use ASCII (e.g. #, *, [~]) if your font/terminal mangles them.
APP_DISPLAY_ICONS: dict[str, str] = {
    "Cursor": "💻",
    "Arc": "🌐",
    "Slack": "#",
    "Messages": "✉️",
    "Obsidian": "🗒",
}

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Entry:
    """label: unique fuzzy string; name: argument to `open -a`."""

    label: str
    name: str


def _iter_apps(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    apps = sorted(root.glob("*.app"))
    util = root / "Utilities"
    if util.is_dir():
        apps.extend(sorted(util.glob("*.app")))
    return apps


def build_entries() -> list[Entry]:
    entries: list[Entry] = []
    seen: set[str] = set()

    def _add(base: str, name: str) -> None:
        label = base
        n = 2
        while label in seen:
            label = f"{base} ({n})"
            n += 1
        seen.add(label)
        entries.append(Entry(label, name))

    for app_root in (
        Path("/Applications"),
        Path("/System/Applications"),
        Path.home() / "Applications",
    ):
        for app_path in _iter_apps(app_root):
            _add(app_path.stem, app_path.stem)

    return entries


# ---------------------------------------------------------------------------
# Running apps (empty query ordering)
# ---------------------------------------------------------------------------

_FETCH_RUNNING_SCRIPT = """
tell application "System Events"
    set nl to ASCII character 10
    set out to ""
    repeat with n in (get name of every application process whose background only is false)
        set out to out & n & nl
    end repeat
    return out
end tell
"""


def _fetch_running_application_names_lower() -> set[str]:
    r = subprocess.run(
        ["osascript", "-e", _FETCH_RUNNING_SCRIPT.strip()],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return set()
    return {ln.strip().lower() for ln in r.stdout.splitlines() if ln.strip()}


def _entry_is_running(entry: Entry, running_lower: frozenset[str]) -> bool:
    pl = entry.name.lower()
    lb = entry.label.lower()
    return pl in running_lower or lb in running_lower


def _hotkey_label_for_row(row_index: int) -> str | None:
    """1–9 for rows 1–9, 0 for row 10; no hint beyond that."""
    if row_index > 9:
        return None
    return "0" if row_index == 9 else str(row_index + 1)


def _digit_key_to_row_index(key: str) -> int:
    """Map 1…9 → rows 0…8, 0 → row 9."""
    d = int(key)
    return 9 if d == 0 else d - 1


def _display_icon_for_app_name(name: str) -> str:
    return APP_DISPLAY_ICONS.get(name) or APP_DISPLAY_ICONS.get(name.lower(), "")


def _styled_option(entry: Entry, row_index: int, show_hotkey: bool) -> Option:
    hk = _hotkey_label_for_row(row_index) if show_hotkey else None
    icon = _display_icon_for_app_name(entry.name)
    base = f"{icon} {entry.label}" if icon else entry.label
    label = f"({hk}) {base}" if hk else base
    return Option(Content(label), id=entry.label)


class SearchInput(Input):
    """Input with macOS-friendly word delete (Option+Backspace / Option+Delete)."""

    BINDINGS = [
        *Input.BINDINGS,
        Binding("ctrl+backspace", "delete_left_word", show=False),
        Binding("alt+backspace", "delete_left_word", show=False),
        Binding("meta+backspace", "delete_left_word", show=False),
        Binding("alt+delete", "delete_right_word", show=False),
        Binding("meta+delete", "delete_right_word", show=False),
    ]

    async def _on_key(self, event: events.Key) -> None:
        if event.is_printable and event.character in "0123456789":
            if not self.value.strip():
                app = self.app
                if hasattr(app, "try_digit_hotkey") and app.try_digit_hotkey(event.character):
                    event.stop()
                    event.prevent_default()
                    return
        await super()._on_key(event)


def _ghostty_new_window_applescript(app_name: str) -> str:
    """When Ghostty is already running (e.g. quick terminal), `open -a` only activates it.

    File → New Window opens a normal window in the existing instance (see Ghostty discussions
    on macOS vs `open -n`, which spawns duplicate dock icons).
    """
    return f'''
tell application "{app_name}"
	if it is running then
		tell application "System Events" to tell process "{app_name}"
			click menu item "New Window" of menu "File" of menu bar 1
		end tell
	else
		activate
	end if
end tell
'''


def run_action(entry: Entry) -> None:
    if sys.platform == "darwin" and entry.name.lower() == "ghostty":
        r = subprocess.run(
            ["osascript", "-e", _ghostty_new_window_applescript(entry.name).strip()],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            subprocess.Popen(["open", "-a", entry.name], start_new_session=True)
        return
    subprocess.Popen(["open", "-a", entry.name], start_new_session=True)


# ---------------------------------------------------------------------------
# TUI
# ---------------------------------------------------------------------------


class LauncherApp(App[None]):
    BINDINGS = [
        Binding("escape", "quit", "Quit", show=False),
    ]

    CSS = """
    Screen {
        layout: vertical;
        align-horizontal: center;
        padding-top: 2;
    }
    #wrap {
        width: 72;
        height: auto;
        max-height: 100%;
    }
    #panel {
        width: 100%;
    }
    #search {
        width: 100%;
        border: none;
    }
    #results-shell {
        width: 100%;
        height: auto;
        max-height: 16;
        border: none;
        display: none;
        background: $surface;
    }
    #results {
        width: 100%;
        height: auto;
        max-height: 16;
        border: none;
        background: transparent;
        padding: 0 1;
    }
    #results:focus {
        border: none;
        background: transparent;
        background-tint: 0%;
    }
    #results > .option-list--option-highlighted {
        color: $block-cursor-foreground;
        background: $block-cursor-background;
        text-style: $block-cursor-text-style;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._entries = build_entries()
        self._by_label: dict[str, Entry] = {e.label: e for e in self._entries}
        self._running_cache: tuple[float, frozenset[str]] | None = None

    def _running_names_lower(self) -> frozenset[str]:
        """Only used from `_empty_query_order` (empty search) — never while filtering."""
        now = time.monotonic()
        if self._running_cache is not None and (now - self._running_cache[0]) < 2.0:
            return self._running_cache[1]
        names = _fetch_running_application_names_lower()
        self._running_cache = (now, frozenset(names))
        return self._running_cache[1]

    def _empty_query_order(self, pool: list[Entry]) -> list[tuple[Entry, float]]:
        """Reorder for empty query; this is the only path that calls `_running_names_lower`."""
        running = self._running_names_lower()
        first = [e for e in pool if _entry_is_running(e, running)]
        first_set = set(first)
        rest = [e for e in pool if e not in first_set]
        first.sort(key=lambda e: e.label.lower())
        rest.sort(key=lambda e: e.label.lower())
        return [(e, 1.0) for e in first + rest]

    def compose(self) -> ComposeResult:
        with Vertical(id="wrap"):
            with Vertical(id="panel"):
                yield SearchInput(
                    placeholder="Search applications…",
                    id="search",
                    compact=True,
                )
                with Vertical(id="results-shell"):
                    results = OptionList(id="results", compact=True)
                    results.can_focus = False
                    yield results

    def _filter(self, query: str) -> list[tuple[Entry, float]]:
        pool = self._entries
        if query.strip():
            # Do not refresh running-app list while the user is typing a filter.
            self._running_cache = None
        if not query.strip():
            return self._empty_query_order(pool)
        hits: list[tuple[Entry, float]] = []
        for e in pool:
            score, _offsets = _fuzzy.match(query, e.label)
            if score > 0:
                hits.append((e, score))
        hits.sort(key=lambda t: t[1], reverse=True)
        return hits

    def _rebuild(self, text: str) -> None:
        results = self.query_one("#results", OptionList)
        shell = self.query_one("#results-shell", Vertical)
        results.clear_options()

        hits = self._filter(text)

        if not hits:
            shell.styles.display = "none"
            return

        show_hotkeys = not text.strip()
        for i, (entry, _score) in enumerate(hits[:30]):
            results.add_option(_styled_option(entry, i, show_hotkeys))
        results.highlighted = 0
        shell.styles.display = "block"

    def on_mount(self) -> None:
        self.query_one("#search", SearchInput).focus()
        # Empty search does not emit Input.Changed on startup; populate running apps + list.
        self._rebuild("")

    def try_digit_hotkey(self, key: str) -> bool:
        """Empty search only: keys 1–9, 0 → first ten rows; print label, open app. Consumes key."""
        if not key.isdigit():
            return False
        inp = self.query_one("#search", SearchInput)
        if inp.value.strip():
            return False
        results = self.query_one("#results", OptionList)
        if results.option_count == 0:
            return False
        idx = _digit_key_to_row_index(key)
        if idx >= results.option_count:
            return True
        opt = results.get_option_at_index(idx)
        if opt.id is None:
            return True
        print(opt.id, flush=True, file=sys.stdout)
        self._dispatch(opt.id)
        return True

    @on(Input.Changed, "#search")
    def on_search_changed(self, event: Input.Changed) -> None:
        self._rebuild(event.value)

    @on(OptionList.OptionSelected, "#results")
    def on_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id is not None:
            self._dispatch(event.option_id)

    @on(Input.Submitted, "#search")
    def on_submit(self, event: Input.Submitted) -> None:
        results = self.query_one("#results", OptionList)
        if results.option_count == 0:
            return
        hi = results.highlighted
        if hi is None:
            return
        opt = results.get_option_at_index(hi)
        if opt.id is not None:
            self._dispatch(opt.id)

    def _clear_after_action(self) -> None:
        inp = self.query_one("#search", Input)
        inp.value = ""
        inp.cursor_position = 0
        self._rebuild("")
        inp.focus()

    def _dispatch(self, label: str) -> None:
        entry = self._by_label.get(label)
        if entry is None:
            return
        run_action(entry)
        self._clear_after_action()

    def action_quit(self) -> None:
        self.exit()

    def on_key(self, event: events.Key) -> None:
        results = self.query_one("#results", OptionList)
        if results.option_count == 0:
            return
        n = results.option_count
        h = results.highlighted

        if event.key == "down":
            event.prevent_default()
            if h is None:
                results.highlighted = 0
            else:
                results.highlighted = (h + 1) % n
            results.scroll_to_highlight()
        elif event.key == "up":
            if h is None:
                return
            event.prevent_default()
            if h == 0:
                results.highlighted = None
            else:
                results.highlighted = h - 1
            if results.highlighted is not None:
                results.scroll_to_highlight()


def main() -> None:
    LauncherApp().run()


if __name__ == "__main__":
    main()
