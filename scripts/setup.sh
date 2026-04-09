#!/usr/bin/env bash
# Run on the sprite as user `sprite` (NOT with sudo). See poke-sprites.md.
# If git/pip warn about permissions after copy.sh, first run:
#   sudo chown -R sprite:sprite /home/sprite
# Edit the three values below, then: bash ~/setup.sh

GITHUB_PAT="<github-pat>"
SPRITE_URL="https://<sprite-url>"
SPRITE_AUTH_TOKEN="<sprite-auth-token>"

#######################
# Set Git credentials #
#######################

git config --global credential.helper store
echo "https://x-access-token:${GITHUB_PAT}@github.com" > ~/.git-credentials

git config --global user.name "poke-bot"
git config --global user.email "caden+poke-bot@example.com"

########################
# Install MCP servers #
########################

python3 -m pip install --user mcp-proxy mcp google-api-python-client google-auth-httplib2 google-auth-oauthlib
sudo apt install -y ripgrep nginx

PROXY_PATH="$(python3 -c "
import sysconfig, os
for scheme in ('posix_user', None):
    kw = {'scheme': scheme} if scheme else {}
    p = os.path.join(sysconfig.get_path('scripts', **kw), 'mcp-proxy')
    if os.path.isfile(p):
        print(p); break
else:
    print('')
")"
if [ -z "$PROXY_PATH" ] || [ ! -x "$PROXY_PATH" ]; then
  echo "mcp-proxy not found. Searched user (~/.local/bin) and system scripts dirs." >&2
  exit 1
fi
echo "mcp-proxy: $PROXY_PATH"

# mcp-proxy: --stateless matches FastMCP's stateless_http=True (see poke-mcp-examples/iss-tracker).
# Without it, streamable HTTP requires mcp-session-id after initialize; some remote clients (e.g. Poke)
# fail tool discovery if they do not replay that session handshake reliably.

##################
# Filesystem MCP #
##################

cat > /home/sprite/start-mcp.sh << EOF
#!/usr/bin/env bash
set -euo pipefail
cd /home/sprite
exec "$PROXY_PATH" --port 8081 --stateless -- python3 /home/sprite/code-mcp.py
EOF
chmod +x /home/sprite/start-mcp.sh

sprite-env services create mcp-server --cmd /home/sprite/start-mcp.sh

###########
# Git MCP #
###########

cat > /home/sprite/start-git-mcp.sh << EOF
#!/usr/bin/env bash
set -euo pipefail
cd /home/sprite
exec "$PROXY_PATH" --port 8082 --stateless -- python3 /home/sprite/git-mcp.py
EOF
chmod +x /home/sprite/start-git-mcp.sh

sprite-env services create git-mcp --cmd /home/sprite/start-git-mcp.sh

############
# Docs MCP #
############

cat > /home/sprite/start-docs-mcp.sh << EOF
#!/usr/bin/env bash
set -euo pipefail
cd /home/sprite
exec "$PROXY_PATH" --port 8083 --stateless -- python3 /home/sprite/docs-mcp.py
EOF
chmod +x /home/sprite/start-docs-mcp.sh

sprite-env services create docs-mcp --cmd /home/sprite/start-docs-mcp.sh

################
# Set up NGINX #
################

sudo tee /etc/nginx/sites-enabled/default << 'EOF'
server {
    listen 8080;

    location /code/ {
        proxy_pass http://127.0.0.1:8081/;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
    }

    location /git/ {
        proxy_pass http://127.0.0.1:8082/;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
    }

    location /docs/ {
        proxy_pass http://127.0.0.1:8083/;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
    }
}
EOF

cat > /home/sprite/start-nginx.sh << 'EOF'
#!/bin/bash
exec nginx -g 'daemon off;'
EOF
chmod +x /home/sprite/start-nginx.sh

sprite-env services create nginx --cmd /home/sprite/start-nginx.sh

########################

echo
echo "On your machine (where poke is installed):"
echo "poke mcp add ${SPRITE_URL}/code/mcp \\"
echo "  --name \"Sprite Code MCP\" \\"
echo "  --api-key ${SPRITE_AUTH_TOKEN}"
echo
echo "poke mcp add ${SPRITE_URL}/git/mcp \\"
echo "    --name \"Sprite Git MCP\" \\"
echo "    --api-key ${SPRITE_AUTH_TOKEN}"
echo
echo "poke mcp add ${SPRITE_URL}/docs/mcp \\"
echo "    --name \"Sprite Docs MCP\" \\"
echo "    --api-key ${SPRITE_AUTH_TOKEN}"
