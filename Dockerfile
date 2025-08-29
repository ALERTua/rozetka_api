ARG PYTHON_VERSION=3.13

FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-trixie-slim AS production

LABEL maintainer="ALERT <alexey.rubasheff@gmail.com>"

ENV \
    # uv
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_FROZEN=1 \
    UV_NO_PROGRESS=true \
    UV_CACHE_DIR=.uv_cache \
    # Python
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    # pip
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    # app
    APP_DIR=/app \
    SOURCE_DIR_NAME=rozetka \
    INFLUXDB_URL="" \
    INFLUXDB_TOKEN="" \
    INFLUXDB_ORG="" \
    INFLUXDB_BUCKET="" \
    TELEGRAM_TOKEN="" \
    TELEGRAM_CHAT_ID="" \
    IMPERSONATE="" \
    TZ="Europe/London"


WORKDIR $APP_DIR

RUN --mount=type=cache,target=$UV_CACHE_DIR \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-install-project --no-dev

COPY $SOURCE_DIR_NAME $SOURCE_DIR_NAME

ENTRYPOINT []

CMD uv run -m $SOURCE_DIR_NAME.runners.parse_api
