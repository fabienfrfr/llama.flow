FROM debian:bookworm-slim

# Install core system tools (Python & basics for scripts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv curl jq && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installation script and project files
COPY install.sh pyproject.toml uv.lock* main.py ./

# Install uv (standard location for the build process)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Run the external installation script for llama.cpp binary & vulkan
RUN chmod +x install.sh && ./install.sh

# Sync project dependencies
RUN uv sync --no-dev

# Final environment configuration
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

EXPOSE 8000
ENTRYPOINT ["python", "main.py"]