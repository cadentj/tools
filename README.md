# Tools

Various tools and MCPs for agent use.

## Available MCP Servers

`code-mcp`

Includes the following tools: 
- `ls`
- `glob` - Uses ripgrep file listing.
- `grep` - Uses ripgrep. Includes 2 lines before and 2 lines after the result as context.
- `read` - Reads a file with numbered lines. Limits output to 500 lines by default.
- `edit` - Edits a file with several fallback matching strategies based on `codemcp` from ezyang [[link](https://github.com/ezyang/codemcp)].
- `replace_regex` - Replaces text w a regex pattern.
- `write` - Writes full file content.

Differences from `modelcontextprotocol/servers/filesystem` [[link](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)]:
- `filesystem` does not have grep.
- `filesystem` uses a slow, recursive pattern match instead of ripgrep or even glob.
- `filesystem` is 800 lines of typescript code. `code-mcp` is 200 lines and super easy to extend.

`git-mcp`

Contains basic git commands for managing repositories. 

Differences from `github/github-mcp-server` [[link](https://github.com/github/github-mcp-server)]: 
- GH requires an entire Docker installation.
- `git-mcp` is <150 loc and extensible. It doesn't contain extensive permission options, so be sure to only operate in trusted sandboxes and scope your GH tokens correctly. 

`docs-mcp`

Contains basic commands for editing Google Docs. For the terminal CLI, see `docs/docs.md` — invoke `docs` (console script from `pyproject.toml`), not `uv run python cli/docs.py`.

TODO(cadentj): List some differences.

*Main difference is that, Google's default cli and api tools suck. They only give you append at the bottom of a doc options, in a TERRIBLE rich text format. If you don't know what that's like, check out Lexical [[link](https://playground.lexical.dev/)]. This is verbose and hard to make concise edits to.*

## Available CLIs

`docs`

Google Docs editor CLI exposed from `cli/docs.py`.

`calendar`

Google Calendar read-only CLI exposed from `cli/calendar.py`.

- `calendar calendars` — list all accessible calendars and their IDs
- `calendar events [-c CALENDAR_ID] [--from ISO] [--to ISO] [-n MAX]` — list upcoming events
- `calendar event EVENT_ID [-c CALENDAR_ID]` — full detail for a single event

Run with: `op run --env-file=.env -- calendar ...`

`cf-cron`

Manages a shared Cloudflare Worker that wakes a Hermes Telegram gateway with
synthetic `⏰ Job Name` messages. The job registry lives in `jobs.md`; for the
Fly/Hermes deployment template, see `projects/agent/`.

## Development

- Python: use `uv` for environments and running scripts.
- Node: use `pnpm` for package management.

Preact:
- `onChange` maps to the native `change` event (fires on blur), NOT every keystroke like React. Use `onInput` for text/number inputs that need per-keystroke updates. `onChange` is fine for `<select>`.
- Use `e.currentTarget` instead of `e.target` for typed event access.
- Use `spellcheck` (lowercase) not `spellCheck`.

# Fun! 

## projects/arc-search

An extension for Google Chrome which mimic's Arc's cmd+T menu.

There are existing extensions [link](https://chromewebstore.google.com/detail/arc-search/odgoljhpkjakkddmnegkfnklbbiifkoe?pli=1) but they're not OS and I don't really trust random extensions on the web store.

**Build note (Vite + React):** The build uses custom Vite modes (`--mode background`, `--mode content`, `--mode popup`). That does not set `process.env.NODE_ENV` to `"production"`, so React would otherwise bundle in **development** mode (huge bundles, odd behavior in the extension). `vite.config.ts` defines `process.env.NODE_ENV` as `"production"` so React stays on the production build.
