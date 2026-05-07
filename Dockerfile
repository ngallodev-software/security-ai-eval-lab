# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# -- ai-reliability-fw from GitHub Release asset --
# REGISTRY_TOKEN must be a GitHub PAT with repo scope (read access to releases).
ARG AI_RELIABILITY_FW_VERSION=0.2.1
ARG AI_RELIABILITY_FW_WHEEL_URL=
ARG AI_RELIABILITY_FW_WHEEL_SHA256
RUN --mount=type=secret,id=registry_token,required=true \
    sh -eu -c 'WHEEL_URL="${AI_RELIABILITY_FW_WHEEL_URL:-https://github.com/ngallodev-software/ai-reliability-fw/releases/download/v${AI_RELIABILITY_FW_VERSION}/ai_reliability_fw-${AI_RELIABILITY_FW_VERSION}-py3-none-any.whl}"; \
    WHEEL_SHA256="${AI_RELIABILITY_FW_WHEEL_SHA256:-}"; \
    [ -n "$WHEEL_SHA256" ] || { echo "AI_RELIABILITY_FW_WHEEL_SHA256 build arg is required" >&2; exit 1; }; \
    REGISTRY_TOKEN="$(cat /run/secrets/registry_token)"; \
    curl -fsSL -u "${REGISTRY_TOKEN}:x-oauth-basic" "$WHEEL_URL" -o /tmp/ai_reliability_fw.whl; \
    echo "${WHEEL_SHA256}  /tmp/ai_reliability_fw.whl" | sha256sum -c -; \
    pip install --no-cache-dir /tmp/ai_reliability_fw.whl; \
    rm -f /tmp/ai_reliability_fw.whl'

# -- security-ai-eval-lab --
COPY --chown=root:root pyproject.toml .
COPY --chown=root:root version.py .
COPY --chown=root:root alembic.ini .
COPY --chown=root:root agents ./agents
COPY --chown=root:root db ./db
COPY --chown=root:root evaluation ./evaluation
COPY --chown=root:root llm ./llm
COPY --chown=root:root migrations ./migrations
COPY --chown=root:root schemas ./schemas
COPY --chown=root:root signals ./signals
RUN pip install --no-cache-dir -e . --no-deps

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/appuser

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser
USER appuser

CMD ["python", "-m", "evaluation.runner", "--dataset", "datasets/", "--dry-run"]
