# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.13

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-alpine AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project


FROM python:${PYTHON_VERSION}-alpine AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup -S app && adduser -S -G app -h /app app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app config.py facebook_api.py manager.py server.py ./

USER app

EXPOSE 8000

CMD ["python", "server.py"]
