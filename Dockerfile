FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# -- ai-reliability-fw from GitHub Release asset --
# REGISTRY_TOKEN must be a GitHub PAT with repo scope (read access to releases).
# Passed as a build arg so the token is not baked into the image layer.
ARG REGISTRY_TOKEN
ARG AI_RELIABILITY_FW_VERSION=0.2.0
RUN pip install --no-cache-dir \
    "https://${REGISTRY_TOKEN}@github.com/ngallodev-software/ai-reliability-fw/releases/download/v${AI_RELIABILITY_FW_VERSION}/ai_reliability_fw-${AI_RELIABILITY_FW_VERSION}-py3-none-any.whl"

# -- security-ai-eval-lab --
# Build context is /lump/apps/ (set in docker-compose.yml).
COPY security-ai-eval-lab/pyproject.toml .
COPY security-ai-eval-lab/ .
RUN pip install --no-cache-dir -e . --no-deps

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "evaluation.runner", "--dataset", "datasets/", "--dry-run"]
