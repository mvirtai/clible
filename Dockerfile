FROM python:3.12-slim AS builder
WORKDIR /workspace

RUN pip install uv

COPY pyproject.toml uv.lock README.md \
    ./
RUN uv sync --frozen

COPY app /workspace/app

# RUN uv run pytest

##################
FROM python:3.12-slim AS runtime
WORKDIR /workspace

COPY --from=builder /workspace/.venv /workspace/.venv 
COPY --from=builder /workspace/app /workspace/app

ENV PATH="/workspace/.venv/bin:$PATH"

ENTRYPOINT [ "python", "-m", "app.cli" ]
CMD []