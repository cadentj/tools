FROM ghcr.io/astral-sh/uv:0.9.5-python3.12-bookworm-slim

ARG HERMES_REPO=https://github.com/NousResearch/hermes-agent.git
ARG HERMES_REF=d5fd74cac209b22ac731305948b4f5e52b5b47f0

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:${PATH}" \
    HOME=/data/home \
    HERMES_HOME=/data/home/.hermes \
    CODEX_HOME=/data/home/.codex \
    TELEGRAM_WEBHOOK_PORT=8443

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN uv venv /opt/venv
RUN uv pip install --python /opt/venv/bin/python "git+${HERMES_REPO}@${HERMES_REF}#egg=hermes-agent[messaging]"
RUN ln -sf /opt/venv/bin/hermes /usr/local/bin/hermes

WORKDIR /app

COPY --chmod=0755 entrypoint.sh /app/entrypoint.sh
COPY --chmod=0755 init.sh /app/init.sh
COPY hermes-config.yaml /app/hermes-config.yaml
COPY AGENTS.template.md /app/AGENTS.template.md
COPY jobs.template.md /app/jobs.template.md

EXPOSE 8443

ENTRYPOINT ["/app/entrypoint.sh"]
