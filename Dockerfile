# AgenticChangeScribe - Docker image
# Uses an OpenAI-compatible endpoint via env vars:
#   LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# git is needed to read diffs inside mounted repos
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first (better layer caching)
COPY pyproject.toml README.md LICENSE /app/
COPY agentic_changescribe /app/agentic_changescribe

RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -e .

ENTRYPOINT ["agentic-scribe"]
CMD ["--help"]
