# llama.flow

LlamaFlow is a simple, state-aware inference proxy. It sits in front of `llama.cpp` to automatically save and restore user-specific model states, making it easier to build persistent AI applications.

**Why llama.flow?**

Unlike traditional models constrained by a fixed context window (e.g., 32K tokens), **llama.flow leverages recurrent architectures (SSM, DeltaNet, etc.)** to provide **near-infinite memory** while maintaining **sharp local precision**. Using `--context-shift` in `llama.cpp`, the model keeps a **sliding window of 128–2048 tokens (KV cache)** for recent details, and the **compressed recurrent state (SSM/DeltaNet hidden state)** persists between requests via `.bin` files. The result? Your assistant remembers **entire conversations** (within the limits of latent memory compression) while staying **fast and accurate** on the latest exchanges. Perfect for long-term chatbots, autonomous agents, or continuous stream analysis.

> **🚧Note:** This project is currently on standby pending further information: https://github.com/ggml-org/llama.cpp/discussions/24043.

## Features

* **State Persistence:** Automatically saves/restores model context per user via binary snapshots.
* **Native Performance:** Delegates actual generation to `llama-server` (C++), supporting Vulkan/GPU acceleration.
* **Simplified API:** A clean FastAPI wrapper to handle user sessions without manual state management.
* **Docker-Ready:** Includes a multi-stage `Dockerfile` to compile the engine and deploy the service.

## Quick Start

### Installation

```bash
git clone https://github.com/fabienfrfr/llama.flow.git
cd llama-flow

# Sync dependencies using uv
uv sync

```

### Running the Service

The proxy automatically manages the C++ server lifecycle:

```bash
uv run main.py

```

Access the API docs at `http://localhost:8000/docs`.

### Docker Deployment

```bash
# Build the Vulkan-enabled image
docker build -t llamaflow-service .

# Run the container (ensure your GPU drivers are exposed)
docker run -d \
  -p 8000:8000 \
  --device /dev/dri:/dev/dri \
  llamaflow-service

```

## How it works

1. **Orchestrator (Python):** Handles incoming requests, identifies the user, and manages `.bin` state files.
2. **Engine (C++):** Receives the state file, performs the high-speed inference, and returns the snapshot.
3. **Storage:** User-specific states are stored in the `user_states/` directory.

---

*License: Apache 2.0*
