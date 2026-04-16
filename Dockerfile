FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN python -m venv .venv

COPY requirements.txt ./
RUN .venv/bin/pip install --upgrade pip \
    && .venv/bin/pip install -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv .venv/
COPY . .

CMD ["uvicorn", "src.infrastructure.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
