import os
import argparse
import threading
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

# LlamaFlow: An autonomous inference engine for recurrent models,
# managing sliding context and state persistence.

class LlamaFlow:
    def __init__(self, repo_id, filename, state_path, n_ctx=128):
        self.state_path = state_path
        self.save_interval = 10
        self.token_count = 0
        self.lock = threading.Lock()

        print(f"Loading {filename} from {repo_id}...")
        model_path = hf_hub_download(repo_id=repo_id, filename=filename)
        
        self.llm = Llama(model_path=model_path, n_ctx=n_ctx)
        
        if os.path.exists(self.state_path):
            try:
                self.llm.load_state(self.state_path)
                print("State restored successfully.")
            except Exception as e:
                print(f"Failed to restore state: {e}")

    def generate(self, prompt, max_tokens=20):
        with self.lock:
            output = self.llm(prompt, max_tokens=max_tokens)
            response_text = output['choices'][0]['text']
            self.token_count += len(response_text.split())
            
            if self.token_count >= self.save_interval:
                state = self.llm.save_state()
                with open(self.state_path, "wb") as f:
                    f.write(state) 
                self.token_count = 0
                print(f"State persisted to {self.state_path}")
            
            return response_text

# --- API Configuration ---
app = FastAPI(title="LlamaFlow API")
flow = None # Initialized in main

class Query(BaseModel):
    prompt: str

@app.post("/generate")
async def api_generate(query: Query):
    return {"response": flow.generate(query.prompt)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LlamaFlow Inference")
    parser.add_argument("--repo", default="unsloth/Qwen3.5-2B-GGUF", help="HF model repo")
    parser.add_argument("--file", default="Qwen3.5-2B-Q4_K_M.gguf", help="GGUF filename")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode instead of API")
    args = parser.parse_args()

    flow = LlamaFlow(args.repo, args.file, "checkpoint.bin")
    
    if args.cli:
        print("--- CLI Mode (Type 'quit' to exit) ---")
        while True:
            user_input = input("You: ")
            if user_input.lower() == "quit":
                break
            print(f"LlamaFlow: {flow.generate(user_input)}")
    else:
        # Start API server
        uvicorn.run(app, host="0.0.0.0", port=args.port)