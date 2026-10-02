# Local language models for the labs: llama-swap + llama.cpp

Small language models served by [llama.cpp](https://github.com/ggml-org/llama.cpp) in Docker, through its **Vulkan** backend (runs on AMD, Intel and NVIDIA GPUs without vendor-specific stacks), behind [llama-swap](https://github.com/mostlygeek/llama-swap): **one endpoint** (`http://127.0.0.1:8080`, OpenAI-compatible API) and the `model` field of the request picks the model. llama-swap starts the `llama-server` of that model on demand and stops it when the memory policy or the idle timeout says so. The notebooks only send HTTP requests, so the same code works with a GPU, on a CPU, or on the instructor's machine.

| `model` | Model | Size | Used by |
|:--|:--|--:|:--|
| `nomic` | Nomic Embed Text v2 MoE, Q8_0 | 512 MB | class 03: notebook 07, guide 02_02; class 04: victim |
| `minilm` | all-MiniLM-L6-v2, F16, always on the CPU | 46 MB | class 03: notebooks 06, 07; class 04: judge of meaning and victim |
| `chat` | Gemma 4 E2B (unsloth, QAT Q4_K_XL), 8k context, thinking off | 2.6 GB | class 12: Open WebUI and the context-tampering notebook (`04-extra/notebook_02`); class 04: optional paraphrase attacker |

**Memory.** The three models together need about 3.2 GB. llama-swap loads each one on the first request (a few seconds for `chat`) and unloads `chat` after 10 minutes without requests, so an idle stack holds almost nothing. By default llama-swap keeps *one* model in memory; the `matrix` entry of `llama-swap.yaml` lets the three run together (the embedders are used together, Nomic as victim and MiniLM as judge, swapping them would cost seconds per query).

## Quick start (from the repository root)

```
make venv                 # once: Python environment
make llama-models         # downloads the three GGUF files (Nomic 512 MB, MiniLM 46 MB, Gemma 4 E2B 2.6 GB) into notebooks/01-spam/llama/models/ (checksum verified, resumable)
make llama-up             # starts llama-swap (PROFILE=cpu if you have no GPU; PROFILE="gpu webui" adds Open WebUI)
make llama-check          # smoke test: health, unit norm, semantic sanity, Matryoshka, one chat completion
make llama-down
```

Without `make`: `docker compose --profile gpu up -d` in this folder, then `python check_embed.py`.

## Open WebUI (class 12)

`PROFILE="gpu webui"` also starts [Open WebUI](https://github.com/open-webui/open-webui) on http://127.0.0.1:3000, connected to llama-swap. It has no login (single user, bound to localhost) and its background requests (titles, tags, follow-ups) are off, so the chat history is exactly what you see. Pick `chat` in the model list. You can **edit an assistant message** (pencil icon) and continue the conversation: the model then answers from a history it never produced, which is what the context-tampering notebook does in code. Chats are kept in the Docker volume `aas-llama_webui`; `docker compose --profile webui down -v` deletes them.

## Requirements

* Docker with Compose v2. Linux: your user must be able to run `docker`.
* **GPU profile (Linux):** a GPU with a Vulkan driver (Mesa RADV/ANV, or the NVIDIA driver) and `/dev/dri` on the host. The container runs as root, so no group setup is normally needed; with rootless Docker or Podman set `RENDER_GID` (the numeric group of `/dev/dri/renderD128`) in `.env`.
* **NVIDIA:** install the NVIDIA Container Toolkit and add `NVIDIA_DRIVER_CAPABILITIES=graphics,compute,utility` to the service environment; the Vulkan ICD comes with the driver.
* **macOS, Windows/WSL2, no GPU:** use `PROFILE=cpu` (`--profile cpu`). (Docker Desktop on macOS has no GPU access; run llama.cpp natively with Metal if you want it.)
* The image tags are pinned in `compose.yml` (`SWAP_TAG`, `SWAP_TAG_CPU`: llama-swap and llama.cpp versions together; `WEBUI_TAG`); update them on purpose, not with `latest`.

## Downloading models

`download_model.py` fetches one GGUF file from Hugging Face (default `nomic-ai/nomic-embed-text-v2-moe-GGUF`, quantisation `Q8_0`).

```
./download_model.py --list                 # files of the repository
./download_model.py --quant Q4_K_M         # smaller (344 MB), slightly less accurate
./download_model.py --repo <user/repo> --quant <label>      # any other GGUF repository
```

A token for gated repositories is read from the `HF_TOKEN` environment variable; it is never stored or printed. To use another file, change the `-m` path in `llama-swap.yaml` (the file is watched: llama-swap reloads it without a restart).

## Fidelity of the converted models

Measured against the original PyTorch models (one-off check when the course was prepared, not needed by students): MiniLM F16 GGUF: cosine 1.00000 on 300 messages (identical vectors); Nomic v2 MoE Q8_0: cosine >= 0.999 (Q4_K_M: mean 0.985). The course itself needs **no PyTorch**.

## Using the endpoint

```
POST http://127.0.0.1:8080/v1/embeddings        {"model": "nomic",  "input": ["search_document: ..."]}
POST http://127.0.0.1:8080/v1/embeddings        {"model": "minilm", "input": ["..."]}                 # no prefix
POST http://127.0.0.1:8080/v1/chat/completions  {"model": "chat",   "messages": [{"role": "user", "content": "..."}]}
GET  http://127.0.0.1:8080/v1/models            # the chat model (the embedders are unlisted, but callable)
GET  http://127.0.0.1:8080/running              # the models loaded right now
```

Nomic v2 needs a **task prefix** at the start of every text (`search_document: ` for messages, `search_query: ` for queries). The server returns L2-normalised 768-d vectors; to use the Matryoshka property keep the first 256 (or 384, 512) values and normalise again. Python clients: `llamalib.py` (embeddings, URL from `LLAMA_URL`) and `attacklib.paraphrase` (chat).

## The chat model

`chat` is small on purpose: 2.6 GB instead of 7 GB or more, 13 tokens/s on an integrated GPU (Radeon 860M), and it fits the memory of a student laptop. It is enough for the class: it follows instructions, keeps a conversation and is *derailable*, which the tampering notebook needs. Thinking is off by default (`--reasoning off`); a request can turn it on with `"chat_template_kwargs": {"enable_thinking": true}`. The context is 8192 tokens (the chat demos use a few hundred). One slot (`-np 1`): parallel requests queue.

The paraphrases of class 04 (`datasets/spam_paraphrases.json`) were generated once with Gemma 4 12B Q4_K_M, which was chosen by a benchmark on 2026-09-30 (0% refusals against 2 to 2.5% for Qwen3.5-9B, 80 to 88% of the paraphrases with the payload intact). They are shipped, so **you do not need a bigger model**. `attacklib.paraphrase` (`AAS_CHAT=live`) uses `chat` by default; the small model refuses and breaks placeholders more often, so expect fewer valid paraphrases. To use another model add an entry to `llama-swap.yaml` (the file is reloaded without a restart) and pass `model=`.

## Why llama-swap

Before 2026-10-02 the course ran one `llama-server` container per model, each with its own port. llama-swap replaces them because: one URL and one `model` name instead of three ports and three environment variables; models are loaded on demand and the chat model is unloaded when idle (RAM); Open WebUI and any OpenAI-compatible client see the models in one place; adding a model is one entry in `llama-swap.yaml`. The price: one more component (pinned image), and a wait of a few seconds on the first request.

## Troubleshooting

| Symptom | Cause and fix |
|:--|:--|
| `ggml_vulkan: No devices found` | `/dev/dri` not passed to the container (use the `gpu` profile), no Vulkan driver on the host (`vulkaninfo --summary`), or an old image lacking the Mesa GL/EGL libraries (fixed in the pinned tag). |
| `permission denied` on `/dev/dri/renderD128` | rootless Docker or a restricted device: set `RENDER_GID` in `.env`. |
| First request after a swap is slow | the GGUF is loading; `curl localhost:8080/running` shows what is in memory. |
| `model not found` | the `model` field is not one of `nomic`, `minilm`, `chat`. |
| Request fails after a long wait | the GGUF file is missing or truncated (run `make llama-models` again); `docker compose logs llama-swap` shows the `llama-server` error. |
| Server up but slow | the `cpu` profile is running, or the GPU is shared. |
| Port 8080 in use | set `LLAMA_PORT` in `.env` and `LLAMA_URL` in your shell. |
