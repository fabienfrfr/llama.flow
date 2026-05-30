# llama.flow

LlamaFlow is an autonomous, state-aware inference engine designed to bridge the gap between simple LLM scripts and persistent, service-oriented AI applications. Built on top of `llama-cpp-python`, it provides a seamless way to run recurrent models with automatic state persistence and a production-ready API interface.

> **🚧 WORK IN PROGRESS** 

## Features

- **State Persistence:** Automatically saves and restores model state to prevent context loss.
- **Thread-Safe API:** Includes a built-in FastAPI wrapper with locking mechanisms for concurrent requests.
- **Dual-Mode Execution:** Switch easily between interactive CLI mode and headless API service mode.
- **Production-Ready:** Containerized with Docker and optimized using `uv` for lightning-fast builds and reproducible environments.
- **Model Agnostic:** Works with any GGUF-compatible model from the Hugging Face ecosystem.

## Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended)
- Docker (for service deployment)

### Local Installation
```bash
# Clone the repository
git clone [https://github.com/yourusername/llama-flow](https://github.com/yourusername/llama-flow)
cd llama-flow

# Sync dependencies
uv sync

```

### Running the Project

**1. As a CLI Agent:**

```bash
uv run main.py --cli

```

**2. As an API Service:**

```bash
uv run main.py --repo "unsloth/Qwen3.5-2B-GGUF" --file "Qwen3.5-2B-Q4_K_M.gguf"

```

Access the interactive API documentation at: `http://localhost:8000/docs`

## Docker Deployment

Build and run as a persistent service:

```bash
# Build the image
docker build -t llamaflow-service .

# Run the container
docker run -d \
  --name llama-api \
  -p 8000:8000 \
  -v $(pwd)/checkpoint.bin:/app/checkpoint.bin \
  --restart unless-stopped \
  llamaflow-service

```

## Architecture

LlamaFlow manages the lifecycle of a language model by intercepting the token generation loop to handle state serialisation.

## License

Apache 2.0