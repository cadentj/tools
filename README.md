# Tools

Various tools for agent use.

## Available CLIs

- `docs`: 
- `calendar`: 
- `cf-cron`:

# Projects

## arc-search

An extension for Google Chrome which mimics Arc's cmd+T menu.

There's an [existing extension](https://chromewebstore.google.com/detail/arc-search/odgoljhpkjakkddmnegkfnklbbiifkoe?pli=1) but it's not OS and I don't trust random extensions on the web store.

### Notes:
- Use `pnpm` for package management.
- **Using Preact**:
  - `onChange` maps to the native `change` event (fires on blur), NOT every keystroke like React. Use `onInput` for text/number inputs that need per-keystroke updates. `onChange` is fine for `<select>`.
  - Use `e.currentTarget` instead of `e.target` for typed event access.
  - Use `spellcheck` (lowercase) not `spellCheck`.