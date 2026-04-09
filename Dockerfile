FROM python:3.11-slim

RUN useradd -m -u 1000 user

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl git \
  && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
  && mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app/env
COPY . /app/env

RUN if [ -f uv.lock ]; then \
      uv sync --frozen --no-editable; \
    else \
      uv sync --no-editable; \
    fi

ENV PATH="/app/env/.venv/bin:$PATH"
ENV PYTHONPATH="/app/env:$PYTHONPATH"
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:7860/health || exit 1

CMD ["sh", "-c", "cd /app/env && uvicorn server.app:app --host 0.0.0.0 --port 7860"]
