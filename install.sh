#!/bin/bash
set -e

echo "--- 1. Checking/Installing System Dependencies for Vulkan ---"
apt-get update && apt-get install -y --no-install-recommends \
    libvulkan1 mesa-vulkan-drivers vulkan-tools libgomp1 \
    && rm -rf /var/lib/apt/lists/*

echo "--- 2. Downloading and installing llama-server ---"
RELEASE_TAG=$(curl -L -s https://api.github.com/repos/ggerganov/llama.cpp/releases/latest | jq -r .tag_name)
URL="https://github.com/ggerganov/llama.cpp/releases/download/$RELEASE_TAG/llama-$RELEASE_TAG-bin-ubuntu-vulkan-x64.tar.gz"

curl -L -s -o llama-bin.tar.gz $URL
tar -xzf llama-bin.tar.gz -C /usr/local/bin/ --strip-components=1
rm llama-bin.tar.gz
#  ls /usr/local/bin | grep llama

echo "--- 3. Verifying GPU support ---"
if command -v vulkaninfo >/dev/null 2>&1; then
    vulkaninfo --summary || echo "⚠️ Vulkan installed but no device detected."
else
    echo "✅ llama-server installed (Vulkan libs present)."
fi