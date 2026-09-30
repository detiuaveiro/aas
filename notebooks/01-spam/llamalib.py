"""Client for the local llama.cpp embedding servers (see `llama/README.md`): Nomic Embed Text v2 MoE (`URL`) and all-MiniLM-L6-v2 (`MINI_URL`).

`embed` returns L2-normalised vectors and caches them on disk, so a notebook pays the
encoding cost once. The Matryoshka property is applied on the client: the full 768-d vector is cached, `dim` truncates it
(and normalises again) without a new call.
"""

import hashlib
import os
import time
from pathlib import Path

import numpy as np
import requests

URL = os.environ.get("LLAMA_EMBED_URL", "http://127.0.0.1:8080")  # Nomic Embed Text v2 MoE
MINI_URL = os.environ.get(
    "LLAMA_MINI_URL", "http://127.0.0.1:8082"
)  # all-MiniLM-L6-v2 (22 M): comparison and judge of meaning
CACHE = Path(__file__).resolve().parent / ".cache"
DOC = "search_document: "  # Nomic v2 needs a task prefix on every text
QUERY = "search_query: "
HINT = "Start the server with `make llama-up` (repository root) and check it with `make llama-check`."


def model_id(url=URL):
    """File name of the model the server is running (part of the cache key)."""
    try:
        return Path(requests.get(f"{url}/props", timeout=5).json()["model_path"]).name
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise RuntimeError(f"llama.cpp server not reachable at {url}. {HINT}") from exc


def _post(url, texts, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(f"{url}/v1/embeddings", json={"input": texts, "model": "embed"}, timeout=300)
            r.raise_for_status()
            data = sorted(r.json()["data"], key=lambda d: d["index"])
            return np.array([d["embedding"] for d in data], dtype=np.float32)
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise exc
            time.sleep(1 + attempt)
    raise ValueError("retries must be >= 1")


def normalise(e):
    return e / np.linalg.norm(e, axis=-1, keepdims=True)


def embed(texts, prefix=DOC, dim=None, url=URL, batch=32, cache=True):
    """Embeddings of `texts` as a float32 array (n, dim), rows of unit norm. `dim` in {768, 512, 384, 256, ...} truncates."""
    texts = list(texts)
    path = None
    if cache:
        CACHE.mkdir(exist_ok=True)
        key = hashlib.sha1((model_id(url) + "\x00" + prefix + "\x00" + "\x01".join(texts)).encode()).hexdigest()[:16]
        path = CACHE / f"llama_{key}.npy"
    if path is not None and path.exists():
        full = np.load(path)
    else:
        try:
            parts = [_post(url, [prefix + t for t in texts[i : i + batch]]) for i in range(0, len(texts), batch)]
        except requests.RequestException as exc:
            raise RuntimeError(f"embedding request failed ({exc}). {HINT}") from exc
        full = np.vstack(parts)
        if path is not None:
            np.save(path, full)
    return full if dim is None or dim >= full.shape[1] else normalise(full[:, :dim])


def embed_mini(texts, dim=None, cache=True, batch=64):
    """Embeddings of all-MiniLM-L6-v2 (384-d, no task prefix) from the small server: same client, other endpoint."""
    return embed(texts, prefix="", dim=dim, url=MINI_URL, batch=batch, cache=cache)
