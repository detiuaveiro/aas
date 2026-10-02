#!/usr/bin/env python3
"""Smoke test for the llama-swap endpoint (:8080): the embedders `nomic` (Nomic Embed Text v2 MoE) and `minilm` (all-MiniLM-L6-v2) and the `chat` model.

Waits for /health, embeds a few SMS through the OpenAI-compatible /v1/embeddings endpoint and checks: unit norm,
semantic sanity (two spam messages are closer to each other than to a ham message), the Matryoshka truncation
(Nomic only: first 256 dimensions, renormalised) and, with --bench, the throughput.

    ./check_embed.py                     # Nomic on http://127.0.0.1:8080
    ./check_embed.py --mini              # all-MiniLM-L6-v2
    ./check_embed.py --chat              # one short completion of the chat model (Gemma 4 E2B)
    ./check_embed.py --bench 200         # also time 200 messages
"""

import argparse
import sys
import time

import numpy as np
import requests

NOMIC_PREFIX = "search_document: "  # Nomic v2 needs a task prefix; MiniLM takes the text as it is
SAMPLES = [
    "WINNER!! As a valued network customer you have been selected to receive a £900 prize reward! To claim call 09061701461.",
    "Congratulations! You've won a free holiday. Call now to claim your cash prize before it expires.",
    "Ok, I'll be home around 7. Do you want me to pick something up for dinner?",
    "Sorry, I missed your call. Can we talk tomorrow morning about the project?",
]


def wait_ready(url, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if requests.get(f"{url}/health", timeout=2).status_code == 200:
                return time.time() - t0
        except requests.RequestException:
            pass
        time.sleep(1)
    sys.exit(f"FAIL: {url}/health not ready after {timeout}s (docker compose logs)")


def embed(url, texts, prefix, model="nomic"):
    r = requests.post(f"{url}/v1/embeddings", json={"input": [prefix + t for t in texts], "model": model}, timeout=120)
    r.raise_for_status()
    data = sorted(r.json()["data"], key=lambda d: d["index"])
    return np.array([d["embedding"] for d in data], dtype=np.float32)


def check_chat(url):
    """One short completion: proves that llama-swap can start the chat model and that thinking is off (content, not reasoning)."""
    t0 = time.time()
    r = requests.post(
        f"{url}/v1/chat/completions",
        json={"model": "chat", "messages": [{"role": "user", "content": "Say hello in five words."}], "max_tokens": 40},
        timeout=600,
    )
    r.raise_for_status()
    msg = r.json()["choices"][0]["message"]
    ok = bool((msg.get("content") or "").strip()) and not msg.get("reasoning_content")
    print(
        f"chat: {'OK' if ok else 'FAIL'} in {time.time() - t0:.1f}s (includes loading the model): {(msg.get('content') or '')!r}"
    )
    return ok


def matryoshka(e, dim):
    e = e[:, :dim]
    return e / np.linalg.norm(e, axis=1, keepdims=True)


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("--mini", action="store_true", help="test MiniLM (no prefix) instead of Nomic")
    ap.add_argument("--chat", action="store_true", help="test the chat model instead of an embedder")
    ap.add_argument("--url", default="http://127.0.0.1:8080", help="llama-swap URL")
    ap.add_argument("--timeout", type=int, default=120, help="seconds to wait for the server")
    ap.add_argument("--bench", type=int, default=0, metavar="N", help="time N messages")
    args = ap.parse_args()
    url = args.url
    if args.chat:
        print(f"{url}: ready after {wait_ready(url, args.timeout):.1f}s")
        print("PASS" if check_chat(url) else "FAIL")
        sys.exit(0)
    model = "minilm" if args.mini else "nomic"
    prefix = "" if args.mini else NOMIC_PREFIX
    ok = True

    print(f"{url}: ready after {wait_ready(url, args.timeout):.1f}s")
    e = embed(url, SAMPLES, prefix, model)
    print(f"embeddings: {e.shape}")
    norms = np.linalg.norm(e, axis=1)
    good = bool(np.allclose(norms, 1.0, atol=1e-3))
    print(f"unit norm: {'OK' if good else 'FAIL'} (min {norms.min():.4f}, max {norms.max():.4f})")
    ok &= good

    sim = e @ e.T
    sane = bool(sim[0, 1] > max(sim[0, 2], sim[0, 3]) and sim[2, 3] > max(sim[2, 0], sim[2, 1]))
    print(
        f"semantic sanity: {'OK' if sane else 'FAIL'} "
        f"(spam-spam {sim[0, 1]:.3f}, spam-ham {sim[0, 2]:.3f}, ham-ham {sim[2, 3]:.3f})"
    )
    ok &= sane

    if not args.mini:
        m = matryoshka(e, 256)
        norm_ok = bool(np.allclose(np.linalg.norm(m, axis=1), 1.0, atol=1e-3))
        print(
            f"matryoshka 256-d: unit norm {'OK' if norm_ok else 'FAIL'} "
            f"(spam-spam {float(m[0] @ m[1]):.3f}, spam-ham {float(m[0] @ m[2]):.3f})"
        )
        ok &= norm_ok

    if args.bench:
        texts = [SAMPLES[i % len(SAMPLES)] + f" {i}" for i in range(args.bench)]
        t0 = time.time()
        for i in range(0, len(texts), 16):
            embed(url, texts[i : i + 16], prefix, model)
        dt = time.time() - t0
        print(f"throughput: {len(texts) / dt:.1f} messages/s ({1000 * dt / len(texts):.1f} ms/message, batches of 16)")

    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
