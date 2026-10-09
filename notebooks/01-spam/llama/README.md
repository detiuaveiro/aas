# Local language models for the labs: llama-swap + llama.cpp

Small language models served by [llama.cpp](https://github.com/ggml-org/llama.cpp) in Docker, behind [llama-swap](https://github.com/mostlygeek/llama-swap): **one endpoint** (`http://127.0.0.1:8080`, OpenAI-compatible API) and the `model` field of the request picks the model. llama-swap starts the `llama-server` of that model on demand and stops it when the memory policy or the idle timeout says so. The notebooks only send HTTP requests, so the same code works with an NVIDIA, AMD or Intel GPU, on a CPU, or on the instructor's machine.

| `model` | Model (all GGUF, 4-bit or smaller) | Size | Used by |
|:--|:--|--:|:--|
| `embgemma` | EmbeddingGemma 2, `UD-Q4_K_XL` ([unsloth](https://huggingface.co/unsloth/embeddinggemma-2-GGUF)) | 176 MB | class 03: notebook 07, guide 02_02; class 04: victim |
| `minilm` | all-MiniLM-L6-v2, `Q4_K_M` ([second-state](https://huggingface.co/second-state/All-MiniLM-L6-v2-Embedding-GGUF), always on the CPU) | 21 MB | class 03: notebooks 06, 07; class 04: judge of meaning and victim |
| `chat` | Gemma 4 E2B, QAT `UD-Q4_K_XL` ([unsloth](https://huggingface.co/unsloth/gemma-4-E2B-it-qat-GGUF)), 8k context, thinking off | 2.6 GB | class 04: paraphrase attacker; class 12: Open WebUI and the context-tampering notebook |

**Memory.** The three models together need about 3 GB (disk and RAM). llama-swap loads each one on the first request (a few seconds for `chat`) and unloads `chat` after 10 minutes without requests, so an idle stack holds almost nothing. By default llama-swap keeps *one* model in memory; the `matrix` entry of `llama-swap.yaml` lets the three run together (the embedders are used together, EmbeddingGemma as victim and MiniLM as judge, swapping them would cost seconds per query). No model of the course is larger than 4 bits per weight: that is the price of running on a student laptop.

## Quick start (from the repository root)

```
make venv                 # once: Python environment
make llama-models         # downloads the three GGUF files (176 MB, 21 MB, 2.6 GB) into notebooks/01-spam/llama/models/ (checksum verified, resumable)
make llama-up             # detects your GPU, pulls the matching image, starts llama-swap (WEBUI=yes adds Open WebUI)
make llama-check          # smoke test: health, unit norm, semantic sanity, Matryoshka, one chat completion
make llama-down
```

Without `make`: `./detect_gpu.sh` prints the profile, then `docker compose --profile <profile> up -d` in this folder and `python check_embed.py`.

## Which image? (GPU detection)

llama-swap publishes **unified** images (llama-swap + llama.cpp + other engines in one image). `detect_gpu.sh` picks the profile of `compose.yml` from your hardware (`nvidia-smi` for NVIDIA, `/dev/dri` for the others); override with `make llama-up PROFILE=cpu` or `LLAMA_PROFILE`.

| profile | image tag | GPUs |
|:--|:--|:--|
| `cuda13` | `unified-cuda13` (amd64, arm64) | NVIDIA Ampere to Blackwell (compute capability >= 8.0): A100, RTX 30/40/50, H100, DGX Spark; needs driver >= 580 |
| `cuda` | `unified-cuda` (amd64) | NVIDIA Pascal to Ada (6.0 <= cc < 10): GTX 10xx, RTX 20xx, P40, P100; CUDA 12 |
| `vulkan` | `unified-vulkan` (amd64) | AMD, Intel and any other GPU with a Vulkan driver |
| `cpu` | `unified-vulkan`, no device, 0 offloaded layers | macOS, Windows without NVIDIA, VMs (there is no unified CPU image) |

The images use the **floating tags** (`unified-cuda13`, `unified-cuda`, `unified-vulkan`: the latest build, so `docker compose pull` updates llama.cpp). That matters for new model architectures: EmbeddingGemma 2 (`gemma-embedding2`) cannot be loaded by the build of release v262 (2026-10-03, tag `unified-vulkan-262`) and needs a build from 2026-10-07 or later. The price is reproducibility: a later build may behave differently. To pin the build used when the course was prepared set `SWAP_TAG=2026-10-07` in `.env` (tags `unified-<backend>-2026-10-07`; old date tags may be pruned by the registry). After an update run `make llama-check`.

## Open WebUI (class 12)

`make llama-up WEBUI=yes` also starts [Open WebUI](https://github.com/open-webui/open-webui) on http://127.0.0.1:3000, connected to llama-swap. It has no login (single user, bound to localhost) and its background requests (titles, tags, follow-ups) are off, so the chat history is exactly what you see. Pick `chat` in the model list. You can **edit an assistant message** (pencil icon) and continue the conversation: the model then answers from a history it never produced, which is what the context-tampering notebook does in code. Chats are kept in the Docker volume `aas-llama_webui`; `docker compose --profile webui down -v` deletes them.

## Requirements

* Docker with Compose v2. Linux: your user must be able to run `docker`.
* **AMD, Intel (Linux):** a Vulkan driver (Mesa RADV/ANV) and `/dev/dri` on the host. The container runs as root, so no group setup is normally needed; with rootless Docker or Podman set `RENDER_GID` (the numeric group of `/dev/dri/renderD128`) in `.env`.
* **NVIDIA:** the driver and the NVIDIA Container Toolkit (`nvidia-ctk runtime configure --runtime=docker`).
* **macOS, Windows/WSL2 without NVIDIA, no GPU:** `PROFILE=cpu`. The unified images are amd64 (CUDA 13 also arm64): on Apple Silicon Docker emulates amd64 (slow) and has no GPU; for speed run llama.cpp natively with Metal (`brew install llama.cpp`) and point `LLAMA_URL` at it.
* Images: floating `unified-*` tags (pin with `SWAP_TAG=<date>`); Open WebUI is pinned (`WEBUI_TAG`).
* llama-swap reads its settings from `LLAMA_SWAP_*` variables (listen address, config path); `compose.yml` sets `LLAMA_SWAP_LISTEN=0.0.0.0:8080`, which must stay on `0.0.0.0` because the port is published.

## Downloading models

`download_model.py` fetches one GGUF file from Hugging Face (default `unsloth/embeddinggemma-2-GGUF`, quantisation `UD-Q4_K_XL`).

```
./download_model.py --list                 # files of the repository
./download_model.py --repo <user/repo> --quant <label>      # any other GGUF repository
```

A token for gated repositories is read from the `HF_TOKEN` environment variable; it is never stored or printed. To use another file, change the `-m` path in `llama-swap.yaml`, then `docker compose restart`.

## Fidelity of the quantised models

Measured against the 16-bit reference when the course was prepared (not needed by students): MiniLM `Q4_K_M` vs F16: mean cosine 0.989 (minimum 0.967) on 400 messages. EmbeddingGemma 2 is served in 4 bits (UD = Unsloth *dynamic*: the sensitive layers keep more bits); its classifier results are in notebook 07. The course needs **no PyTorch**.

## Using the endpoint

```
POST http://127.0.0.1:8080/v1/embeddings        {"model": "embgemma", "input": ["title: none | text: ..."]}
POST http://127.0.0.1:8080/v1/embeddings        {"model": "minilm",   "input": ["..."]}                 # no prefix
POST http://127.0.0.1:8080/v1/chat/completions  {"model": "chat",     "messages": [{"role": "user", "content": "..."}]}
GET  http://127.0.0.1:8080/v1/models            # the chat model (the embedders are unlisted, but callable)
GET  http://127.0.0.1:8080/running              # the models loaded right now
```

EmbeddingGemma needs a **task prefix** at the start of every text (`title: none | text: ` for messages, `task: search result | query: ` for queries). The server returns L2-normalised 768-d vectors; to use the Matryoshka property keep the first 512, 256 or 128 values and normalise again. Python clients: `llamalib.py` (embeddings, URL from `LLAMA_URL`) and `attacklib.paraphrase` (chat).

## The chat model

`chat` is the only language model of the course, small on purpose: 2.6 GB, 13 tokens/s on an integrated GPU (Radeon 860M), it fits the memory of a student laptop. It follows instructions, keeps a conversation and is *derailable*, which the tampering notebook needs. Thinking is off by default (`--reasoning off`); a request can turn it on with `"chat_template_kwargs": {"enable_thinking": true}`. The context is 8192 tokens (the chat demos use a few hundred). One slot (`-np 1`): parallel requests queue.

The paraphrases of class 04 (`datasets/spam_paraphrases.json`) were generated once with this model (casual style, payload placeholders; 83% of the 108 requests gave a valid paraphrase, 50 of 54 messages have at least one) and are shipped, so the notebooks run without the chat model. `attacklib.paraphrase` (`AAS_CHAT=live`) regenerates them; the output differs from run to run (temperature 0.7).

## Why llama-swap

One URL and one `model` name instead of one port per model; models are loaded on demand and the chat model is unloaded when idle (RAM); Open WebUI and any OpenAI-compatible client see the models in one place; adding a model is one entry in `llama-swap.yaml`. The price: one more component (pinned image), and a wait of a few seconds on the first request.

## Troubleshooting

| Symptom | Cause and fix |
|:--|:--|
| `unknown model architecture: 'gemma-embedding2'` | the image is older than the 2026-10-07 build: `docker compose pull` (and no `SWAP_TAG` pin before that date). |
| `ggml_vulkan: No devices found` | `/dev/dri` not passed to the container (use the `vulkan` profile), or no Vulkan driver on the host (`vulkaninfo --summary`). |
| `permission denied` on `/dev/dri/renderD128` | rootless Docker or a restricted device: set `RENDER_GID` in `.env`. |
| `could not select device driver "nvidia"` | NVIDIA Container Toolkit missing or Docker not restarted after `nvidia-ctk runtime configure`. |
| First request after a swap is slow | the GGUF is loading; `curl localhost:8080/running` shows what is in memory. |
| `model not found` | the `model` field is not one of `embgemma`, `minilm`, `chat`. |
| Request fails after a long wait | the GGUF file is missing or truncated (run `make llama-models` again); `docker compose logs` shows the `llama-server` error. |
| Server up but slow | the `cpu` profile is running, or the GPU is shared. |
| Port 8080 in use | set `LLAMA_PORT` in `.env` and `LLAMA_URL` in your shell. |
