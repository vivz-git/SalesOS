FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app

FROM base AS builder
RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project
COPY app ./app
RUN uv sync --no-dev

FROM base AS runner
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "from urllib.request import urlopen; urlopen('http://localhost:8000/health')"
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
