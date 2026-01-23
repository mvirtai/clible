FROM python:3.12-slim AS builder
WORKDIR /workspace

RUN pip install uv

COPY pyproject.toml uv.lock README.md \
    ./
RUN uv sync --frozen

COPY app /workspace/app
COPY tests /workspace/tests
COPY data /workspace/data
ENV PYTHONPATH=/workspace
ENV TESTPATH=/workspace/tests
RUN uv run pytest $TESTPATH -v

##################
FROM python:3.12-slim AS runtime
WORKDIR /workspace

COPY --from=builder /workspace/.venv /workspace/.venv 
COPY --from=builder /workspace/app /workspace/app

ENV PATH="/workspace/.venv/bin:$PATH"

# Declare volumes for data persistence
VOLUME ["/workspace/app/db", "/workspace/data"]

ENTRYPOINT [ "python", "-m", "app.cli" ]
CMD []