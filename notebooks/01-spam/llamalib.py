"""Client for the local llama-swap endpoint (see `llama/README.md`): one URL, the `model` field picks the embedder:
`embgemma` (EmbeddingGemma 2) or `minilm` (all-MiniLM-L6-v2).

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

URL = os.environ.get("LLAMA_URL", "http://127.0.0.1:8080")  # llama-swap: every model behind one endpoint
EMBG = "embgemma"  # EmbeddingGemma 2 (270 M text tower, Q4 GGUF 176 MB)
MINI = "minilm"  # all-MiniLM-L6-v2 (22 M): comparison and judge of meaning
CACHE = Path(__file__).resolve().parent / ".cache"
DOC = "title: none | text: "  # EmbeddingGemma expects a task prefix on every text (this one is for a document without a title)
QUERY = "task: search result | query: "
HINT = "Start the server with `make llama-up` (repository root) and check it with `make llama-check`."


def model_id(model=EMBG, url=URL):
    """File name of the GGUF behind `model` (part of the cache key). The first call may load the model (llama-swap), hence the long timeout."""
    try:
        return Path(requests.get(f"{url}/upstream/{model}/props", timeout=120).json()["model_path"]).name
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise RuntimeError(f"llama.cpp server not reachable at {url}. {HINT}") from exc


def _post(url, model, texts, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(f"{url}/v1/embeddings", json={"input": texts, "model": model}, timeout=300)
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


def embed(texts, prefix=DOC, dim=None, model=EMBG, url=URL, batch=32, cache=True):
    """Embeddings of `texts` as a float32 array (n, dim), rows of unit norm. `dim` in {768, 512, 384, 256, ...} truncates."""
    texts = list(texts)
    path = None
    if cache:
        CACHE.mkdir(exist_ok=True)
        key = hashlib.sha1((model_id(model, url) + "\x00" + prefix + "\x00" + "\x01".join(texts)).encode()).hexdigest()[
            :16
        ]
        path = CACHE / f"llama_{key}.npy"
    if path is not None and path.exists():
        full = np.load(path)
    else:
        try:
            parts = [_post(url, model, [prefix + t for t in texts[i : i + batch]]) for i in range(0, len(texts), batch)]
        except requests.RequestException as exc:
            raise RuntimeError(f"embedding request failed ({exc}). {HINT}") from exc
        full = np.vstack(parts)
        if path is not None:
            np.save(path, full)
    return full if dim is None or dim >= full.shape[1] else normalise(full[:, :dim])


def embed_mini(texts, dim=None, cache=True, batch=64):
    """Embeddings of all-MiniLM-L6-v2 (384-d, no task prefix): same client, other model."""
    return embed(texts, prefix="", dim=dim, model=MINI, batch=batch, cache=cache)
