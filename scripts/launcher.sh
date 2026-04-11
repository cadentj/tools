#!/usr/bin/env bash
# Thin wrapper: run the launcher TUI from its project directory.
exec uv run --project "$(dirname "$0")/../projects/launcher" launcher "$@"
