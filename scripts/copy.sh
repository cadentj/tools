#!/usr/bin/env bash
# Copy local MCP/setup scripts into /home/sprite/ on the active sprite (sprite use).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

sprite exec \
  --file "${REPO_DIR}/mcp/code-mcp.py:/home/sprite/code-mcp.py" \
  --file "${REPO_DIR}/mcp/docs-mcp.py:/home/sprite/docs-mcp.py" \
  --file "${REPO_DIR}/mcp/git-mcp.py:/home/sprite/git-mcp.py" \
  --file "${REPO_DIR}/tools/__init__.py:/home/sprite/tools/__init__.py" \
  --file "${REPO_DIR}/tools/docs.py:/home/sprite/tools/docs.py" \
  --file "${REPO_DIR}/tools/edit.py:/home/sprite/tools/edit.py" \
  --file "${SCRIPT_DIR}/setup.sh:/home/sprite/setup.sh" \
  -- ls -la /home/sprite/code-mcp.py /home/sprite/docs-mcp.py /home/sprite/git-mcp.py \
    /home/sprite/tools/__init__.py /home/sprite/tools/docs.py /home/sprite/tools/edit.py \
    /home/sprite/setup.sh
