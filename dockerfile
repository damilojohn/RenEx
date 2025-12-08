#Multi-stage build
FROM python:3.13 AS builder

LABEL org.opencontainers.image.source=https://github.com/zeno
LABEL org.opencontainers.image.description="Zeno"
LABEL org.opencontainers.image.licenses=Apache-2.0

WORKDIR /usr/app/server

COPY pyproject.toml uv.lock /usr/app/server/


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential libpq-dev

RUN pip install uv && \
    uv sync

COPY /zeno /usr/app/server/zeno

RUN apt-get autoremove -y build-essential && \
    rm -rf /var/lib/apt/lists/*

FROM python:3.13-slim

WORKDIR /usr/app/server

COPY --from=builder /usr/app/server/zeno/ /usr/app/server/zeno/
COPY --from=builder /usr/app/server/.venv /usr/app/server/.venv
COPY --from=builder /usr/app/server/pyproject.toml /usr/app/server/pyproject.toml
COPY --from=builder /usr/app/server/uv.lock /usr/app/server/uv.lock

ENV PATH="/usr/app/server/.venv/bin:$PATH"

EXPOSE 8080

CMD ["uv", "run", "task","api"]
# CMD ["uv", "run", "task","api_prod"]
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8080", "main:app"]
