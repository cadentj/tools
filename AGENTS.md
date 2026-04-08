Tools: 
- Use `uv` for Python environments and running python scripts. 
- Use `pnpm` for node package management.

Preact:
- Preact's `onChange` maps to the native `change` event (fires on blur), NOT every keystroke like React. Use `onInput` for text/number inputs that need per-keystroke updates. `onChange` is fine for `<select>` elements.
- Use `e.currentTarget` instead of `e.target` for typed event access.
- Use `spellcheck` (lowercase) not `spellCheck`.