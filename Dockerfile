FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# -- ai-reliability-fw from GitHub Packages --
# REGISTRY_TOKEN must be a GitHub PAT with read:packages scope.
# Passed as a build arg so the token is not baked into the image layer.
ARG REGISTRY_TOKEN
ARG AI_RELIABILITY_FW_VERSION=0.1.0
RUN pip install --no-cache-dir \
    --extra-index-url "https://__token__:${REGISTRY_TOKEN}@pypi.pkg.github.com/ngallodev-software/" \
    "ai-reliability-fw==${AI_RELIABILITY_FW_VERSION}"

# -- security-ai-eval-lab --
# Build context is /lump/apps/ (set in docker-compose.yml).
COPY security-ai-eval-lab/pyproject.toml .
COPY security-ai-eval-lab/ .
RUN pip install --no-cache-dir -e . --no-deps

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "evaluation.runner", "--dataset", "datasets/", "--dry-run"]
