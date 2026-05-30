# Use the official uv image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Disable uv cache for the final image to keep it small
ENV UV_LINK_MODE=copy

# Install dependencies (leverage uv cache for speed)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

# Copy source code
COPY main.py .

# Create non-privileged user
RUN groupadd -g 1000 appuser && useradd -u 1000 -g appuser -m appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose API port
EXPOSE 8000

# Run using the venv created by uv
ENTRYPOINT ["/app/.venv/bin/python", "main.py"]