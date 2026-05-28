FROM python:3.13-slim AS builder

WORKDIR /app

ENV UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install --yes --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
ARG RUNTIME_EXTRAS=""
RUN if [ "$RUNTIME_EXTRAS" = "all" ]; then \
        uv sync --frozen --no-dev --all-extras; \
    elif [ -n "$RUNTIME_EXTRAS" ]; then \
        uv sync --frozen --no-dev --extra "$RUNTIME_EXTRAS"; \
    else \
        uv sync --frozen --no-dev; \
    fi

FROM python:3.13-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=/tmp/uv-cache
ENV PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system app \
    && adduser --system --ingroup app app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=builder /app/.venv ./.venv
COPY . .
RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["./scripts/start-web.sh"]
