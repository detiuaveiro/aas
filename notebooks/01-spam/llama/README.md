# Local llama.cpp servers for the spam labs

Small language models served by [llama.cpp](https://github.com/ggml-org/llama.cpp) in Docker, through its **Vulkan** backend (runs on AMD, Intel and NVIDIA GPUs without vendor-specific stacks). The notebooks talk to the server over HTTP (OpenAI-compatible API), so the same code works with a GPU, on a CPU, or on the instructor's machine.

| Service | Profile | Model | Port | Used by |
|:--|:--|:--|--:|:--|
| `embed` | `gpu` | Nomic Embed Text v2 MoE (Q8_0, 512 MB) | 8080 | class 03: notebook 07, guide 02_02 |
| `embed-cpu` | `cpu` | same, CPU only | 8080 | machines without a usable GPU |
| `embed-mini` | `gpu`, `cpu` | all-MiniLM-L6-v2 (F16, 46 MB), always on the CPU | 8082 | class 03: notebooks 06, 07; class 04: judge of meaning and one of the victims |
| `chat` | `chat` | Gemma 4 12B, Q4_K_M (7.1 GB), chosen by benchmark | 8081 | class 04: paraphrase attacker (optional; the notebooks ship its outputs) |

## Quick start (from the repository root)

```
make venv                 # once: Python environment
make llama-models         # downloads the two GGUF files (Nomic 512 MB, MiniLM 46 MB) into notebooks/01-spam/llama/models/ (checksum verified, resumable)
make llama-up             # starts the two embedding servers (PROFILE=cpu if you have no GPU)
make llama-check          # smoke test of both: health, unit norm, semantic sanity, Matryoshka
make llama-down
```

Without `make`: `docker compose --profile gpu up -d` in this folder, then `python check_embed.py`.

## Requirements

* Docker with Compose v2. Linux: your user must be able to run `docker`.
* **GPU profile (Linux):** a GPU with a Vulkan driver (Mesa RADV/ANV, or the NVIDIA driver) and `/dev/dri` on the host. The container runs as root, so no group setup is normally needed; with rootless Docker or Podman set `RENDER_GID` (the numeric group of `/dev/dri/renderD128`) in `.env`.
* **NVIDIA:** install the NVIDIA Container Toolkit and add `NVIDIA_DRIVER_CAPABILITIES=graphics,compute,utility` to the service environment; the Vulkan ICD comes with the driver.
* **macOS, Windows/WSL2, no GPU:** use `--profile cpu`. (Docker Desktop on macOS has no GPU access; run llama.cpp natively with Metal if you want it.)
* The image tag is pinned in `.env.example` (`LLAMA_TAG`); update it on purpose, not with `latest`.

## Downloading models

`download_model.py` fetches one GGUF file from Hugging Face (default `nomic-ai/nomic-embed-text-v2-moe-GGUF`, quantisation `Q8_0`).

```
./download_model.py --list                 # files of the repository
./download_model.py --quant Q4_K_M         # smaller (344 MB), slightly less accurate
./download_model.py --repo <user/repo> --quant <label>      # any other GGUF repository
```

A token for gated repositories is read from the `HF_TOKEN` environment variable; it is never stored or printed. To use another file, copy `.env.example` to `.env` and set `EMBED_GGUF`.

## Fidelity of the converted models

Measured against the original PyTorch models (one-off check when the course was prepared, not needed by students): MiniLM F16 GGUF: cosine 1.00000 on 300 messages (identical vectors); Nomic v2 MoE Q8_0: cosine >= 0.999 (Q4_K_M: mean 0.985). The course itself needs **no PyTorch**.

## Using the servers

```
POST http://127.0.0.1:8080/v1/embeddings   {"input": ["search_document: ..."], "model": "embed"}     # Nomic
POST http://127.0.0.1:8082/v1/embeddings   {"input": ["..."], "model": "embed"}                       # MiniLM, no prefix
```

Nomic v2 needs a **task prefix** at the start of every text (`search_document: ` for messages, `search_query: ` for queries). The server returns L2-normalised 768-d vectors; to use the Matryoshka property keep the first 256 (or 384, 512) values and normalise again.

## The chat model (class 04, optional)

The level-2 attack notebook can ask a local chat model to paraphrase a message with its payload protected. The paraphrases used in class are shipped in `datasets/spam_paraphrases.json`, so **you do not need this service**; run it only to generate your own (`AAS_CHAT=live`).

```
./download_model.py --repo unsloth/gemma-4-12b-it-GGUF --quant Q4_K_M     # 7.1 GB
docker compose --profile gpu --profile chat up -d chat                     # http://127.0.0.1:8081
```

Needs about 8 GB of free (V)RAM. Speed on an integrated GPU: about 3-4 tokens/s in total over four parallel requests, i.e. 15 s per message. Thinking is disabled per request (`chat_template_kwargs.enable_thinking=false`).

**Why Gemma 4 12B** (benchmark of 2026-09-30: 40 to 100 spam messages, payload replaced by placeholders, four parallel requests; details in the course repository notes): against Qwen3.5-9B (Q4_K_M, 5.7 GB) it had 0% refusals (Qwen 2 to 2.5%), 100% valid placeholder use (Qwen 90 to 98%), 80 to 88% of the paraphrases with the payload intact (Qwen 68 to 85%) and a similar evasion rate (9 to 19% of the messages against the word-based filters, 0% against the embedding filters). Qwen3.5-9B is about 2 times faster; because the paraphrases are generated once and cached, reliability counted more than speed. Qwen3.5-9B remains a fine choice on a small GPU.

## Troubleshooting

| Symptom | Cause and fix |
|:--|:--|
| `ggml_vulkan: No devices found` | `/dev/dri` not passed to the container (use the `gpu` profile), no Vulkan driver on the host (`vulkaninfo --summary`), or an old image lacking the Mesa GL/EGL libraries (fixed in the pinned tag). |
| `permission denied` on `/dev/dri/renderD128` | rootless Docker or a restricted device: set `RENDER_GID` in `.env`. |
| Server up but slow | the `cpu` profile is running, or the GPU is shared; `docker compose logs embed`. |
| Health check never becomes healthy | the GGUF file is missing or truncated: run `make llama-models` again. |
| Port 8080 in use | set `EMBED_PORT` in `.env` and pass `--url` to `check_embed.py`. |
