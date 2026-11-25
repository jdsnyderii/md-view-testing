ARG PYTHON_VERSION=3.13
FROM ghcr.io/astral-sh/uv:0.13.10 AS uv

FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

FROM python:${PYTHON_VERSION}-slim AS runtime

WORKDIR /app

ENV HOME=/home/appuser \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /app/.venv /app/.venv

ARG APP_UID=10001
RUN case "${APP_UID}" in \
      ''|*[!0-9]*) echo "APP_UID must be a positive non-root numeric UID" >&2; exit 1 ;; \
      *[1-9]*) ;; \
      *) echo "APP_UID must be a positive non-root numeric UID" >&2; exit 1 ;; \
    esac \
 && groupadd --gid "${APP_UID}" appuser \
 && useradd --uid "${APP_UID}" --gid "${APP_UID}" --home-dir /home/appuser --create-home --shell /usr/sbin/nologin appuser \
 && chmod 0700 /home/appuser \
 && mkdir /config

ARG APP_PORT=8000
ARG GUNICORN_WORKERS=2
ARG GUNICORN_BIND_ADDRESS=0.0.0.0
ENV MDPORTAL_CONFIG=/config/roots.yaml \
    GUNICORN_CMD_ARGS="--bind=${GUNICORN_BIND_ADDRESS}:${APP_PORT} --workers=${GUNICORN_WORKERS} --log-level=warning"

COPY app.py ./
COPY templates/ templates/

USER ${APP_UID}:${APP_UID}

EXPOSE ${APP_PORT}
CMD ["gunicorn", "app:create_app()"]