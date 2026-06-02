"""
LlamaFlow: A stateful inference proxy for recurrent models (SSM/DeltaNet).

This FastAPI service wraps `llama-server` to enable near-infinite context via:
- Sliding window attention (128-2048 tokens : KV Cache) for local precision.
- Persistent recurrent state (SSM/DeltaNet hidden state) for long-term memory.
- Per-user state files (.bin) to maintain conversation history across requests.
"""

import os
from dotenv import load_dotenv
import subprocess
import shutil
import sys
import time
import requests
import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.responses import Response
from pydantic import BaseModel

# Configure logging to monitor backend lifecycle
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LlamaFlow")

app = FastAPI(title="LlamaFlow Proxy")

# Runtime configuration

load_dotenv()

SERVER_URL = "http://localhost:8001"
STATE_DIR = "user_states"
MODEL_DIR = os.path.abspath("./models")

# For Qwen : KV cache shifting is not supported for this context, disabling KV cache shifting
REPO_ID = os.getenv("MODEL_REPO", "ai21labs/AI21-Jamba-Reasoning-3B-GGUF")
FILENAME = os.getenv("MODEL_FILE", "jamba-reasoning-3b-Q4_K_M.gguf")

os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

class Query(BaseModel):
    user_id: str
    prompt: str


# Model management
def ensure_model(repo_id: str, filename: str) -> str:
    """Ensure model file exists locally, download if missing."""
    destination = os.path.join(MODEL_DIR, repo_id.replace("/", "--"), filename)

    if os.path.exists(destination):
        logger.info(f"Model already available: {destination}")
        return destination

    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    logger.info(f"Downloading model from {url}")

    os.makedirs(os.path.dirname(destination), exist_ok=True)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(destination, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    logger.info("Download completed")
    return destination


def ensure_llama_server():
    """Ensure llama-server binary is available and provide install instructions if missing."""

    if shutil.which("llama-server") is None:
        print("\n❌ llama-server missing")
        print("➡️ Run manually:")
        print("   chmod +x install.sh && sudo ./install.sh\n")
        sys.exit(1)


def ensure_recurrent_llm(path: str) -> None:
    """ Detect recurrent / hybrid architecture in GGUF. """
    data = open(path, "rb").read().lower()

    if not any(k in data for k in (
        b"ssm.state_size", b"ssm_d_state", b"ssm_conv",
        b"delta_net", b"deltanet", b"gated_delta"
    )):
        raise ValueError("not recurrent/hybrid")

    logger.info("✅ recurrent/hybrid model")


# Backend process
def start_llama_server(model_path: str) -> subprocess.Popen:
    """Launch llama-server with sliding context enabled."""

    cmd = [
        "llama-server",
        "-m", model_path,
        "--port", "8001",

        "--ctx-size", "128",        # Small KV cache
        "--n-predict", "-1",        # Unlimited generation

        #"--keep", "0",            # Not adapted for ssm / deltanet 
        "--context-shift",          # Sliding window during generation
        #"--no-kv-unified",          # For working shift
        "--parallel", "1",
        "--no-cont-batching",         # remove auto save slot (one slot)
        #"--no-cache-prompt",

        "--slot-save-path", "./user_states",  # Enable KV persistence
        "--n-gpu-layers", "99",

        "--reasoning", "off",
    ]

    return subprocess.Popen(cmd)


def init():
    """Initialize backend and wait for readiness."""
    ensure_llama_server()
    model_path = ensure_model(REPO_ID, FILENAME)
    ensure_recurrent_llm(model_path)
    
    server_proc = start_llama_server(model_path)

    logger.info("Waiting for llama-server startup...")

    while True:
        try:
            requests.get(SERVER_URL)
            logger.info("llama-server is ready")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)

    return server_proc

# Endpoint (KV-based and recurrent memory)
@app.post("/v1/chat/completions")
async def chat(request: Request):
    """Handle chat with per-user persistent KV state."""

    data = await request.json()
    user_id = request.headers.get("X-User-Id", "default") # manage with secret ? (or TCP/IP ?)

    state_path = os.path.join(STATE_DIR, f"{user_id}.bin")
    tmp_filename = f"{user_id}_tmp.bin"
    tmp_path = os.path.join(STATE_DIR, tmp_filename)
    logger.info(tmp_path)

    # 1. Restore user state (if exists)
    if os.path.exists(state_path):
        requests.post(
            f"{SERVER_URL}/slots/0?action=restore",
            json={"filename": f"{user_id}.bin"}
        ).raise_for_status()
        logger.info(" /slots/0?action=restore")

    # 2. Forward request to llama-server
    resp = requests.post(
        f"{SERVER_URL}/v1/chat/completions",
        json=data
    )
    resp.raise_for_status()
    logger.info(" resp finished")


    # 3. Save state via llama (safe snapshot)
    requests.post(
        f"{SERVER_URL}/slots/0?action=save",
        data=f'{{"filename":"{tmp_filename}"}}',
        headers={"Content-Type": "application/json"}
    ).raise_for_status()
    logger.info(" /slots/0?action=save")


    # 5. Atomic rename → final state
    os.replace(tmp_path, state_path)
 
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
    )



# Catch-all Proxy
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str, request: Request):

    # endpoint exclusion
    if path == "v1/chat/completions":
        return Response(status_code=404)

    url = f"{SERVER_URL}/{path}"

    # forward request
    resp = requests.request(
        method=request.method,
        url=url,
        headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
        params=request.query_params,
        data=await request.body()
    )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers)
    )

# Application entrypoint
if __name__ == "__main__":
    server_proc = init()

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        server_proc.terminate()
