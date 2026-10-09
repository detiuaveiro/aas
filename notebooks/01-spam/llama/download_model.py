#!/usr/bin/env python3
"""Download one GGUF file from a Hugging Face repository into ./models.

Resumable (HTTP Range), verified (SHA-256 from the Hub's LFS metadata), and dependency-light (only `requests`).
A token for gated repositories is read from the environment (HF_TOKEN); it is never printed or stored.

Examples
    ./download_model.py                                   # EmbeddingGemma 2, UD-Q4_K_XL (176 MB)
    ./download_model.py --list                            # show the .gguf files of the repository
    ./download_model.py --repo unsloth/gemma-4-E2B-it-qat-GGUF --quant UD-Q4_K_XL
"""

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

import requests

HUB = "https://huggingface.co"
DEFAULT_REPO = "unsloth/embeddinggemma-2-GGUF"
DEFAULT_QUANT = "UD-Q4_K_XL"
CHUNK = 1 << 20


def headers():
    token = os.environ.get("HF_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def check(resp, what):
    if resp.status_code in (401, 403):
        die(
            f"{what}: access denied (HTTP {resp.status_code}). The repository may be gated: accept its licence on huggingface.co "
            "and export HF_TOKEN.",
            2,
        )
    if resp.status_code == 404:
        die(f"{what}: not found (HTTP 404).", 2)
    resp.raise_for_status()


def list_files(repo, revision):
    """The .gguf files of the repository: [{path, size, sha256}]."""
    r = requests.get(
        f"{HUB}/api/models/{repo}/tree/{revision}", params={"recursive": "true"}, headers=headers(), timeout=30
    )
    check(r, f"repository {repo}")
    files = []
    for item in r.json():
        if item.get("type") == "file" and item["path"].lower().endswith(".gguf"):
            files.append({"path": item["path"], "size": item["size"], "sha256": (item.get("lfs") or {}).get("oid")})
    return files


def pick(files, quant, name):
    if name:
        hit = [f for f in files if f["path"] == name or Path(f["path"]).name == name]
    else:
        pattern = re.compile(rf"(^|[-_.]){re.escape(quant)}([-_.]|$)", re.IGNORECASE)
        hit = [f for f in files if pattern.search(Path(f["path"]).name) and "mmproj" not in f["path"].lower()]
    if len(hit) != 1:
        found = "\n  ".join(f["path"] for f in hit) if hit else "(no match)"
        die(f"expected exactly one file for {name or quant}, got:\n  {found}\nUse --list and --file.", 3)
    return hit[0]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(CHUNK):
            h.update(block)
    return h.hexdigest()


def download(repo, revision, entry, dest):
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / Path(entry["path"]).name
    part = target.with_suffix(target.suffix + ".part")
    if target.exists():
        if entry["sha256"] and sha256_of(target) != entry["sha256"]:
            print(f"{target.name}: present but the checksum differs, downloading again")
            target.unlink()
        else:
            print(f"{target.name}: already present and verified")
            return target
    url = f"{HUB}/{repo}/resolve/{revision}/{entry['path']}"
    have = part.stat().st_size if part.exists() else 0
    hdr = {**headers(), **({"Range": f"bytes={have}-"} if have else {})}
    with requests.get(url, headers=hdr, stream=True, timeout=30, allow_redirects=True) as r:
        if r.status_code == 416:  # nothing left to fetch
            have = entry["size"]
        else:
            check(r, entry["path"])
            if have and r.status_code != 206:  # the server ignored Range: start over
                have = 0
            tty = sys.stdout.isatty()
            step = entry["size"] // (100 if tty else 10) or 1  # a redrawn line on a terminal, ten lines in a log
            with open(part, "ab" if have else "wb") as fh:
                done, shown = have, have
                for block in r.iter_content(CHUNK):
                    fh.write(block)
                    done += len(block)
                    if done - shown >= step or done == entry["size"]:
                        shown = done
                        print(
                            f"{'\r' if tty else ''}{target.name}: {done / 1e6:8.1f} / {entry['size'] / 1e6:.1f} MB",
                            end="" if tty else "\n",
                            flush=True,
                        )
                if tty:
                    print()
    if part.stat().st_size != entry["size"]:
        die(
            f"incomplete download ({part.stat().st_size} of {entry['size']} bytes); run the command again to resume.", 4
        )
    if entry["sha256"] and sha256_of(part) != entry["sha256"]:
        part.unlink()
        die("checksum mismatch: the partial file was removed; run the command again.", 5)
    part.rename(target)
    print(
        f"{target.name}: OK ({entry['size'] / 1e6:.1f} MB, sha256 verified)"
        if entry["sha256"]
        else f"{target.name}: OK"
    )
    return target


def main():
    ap = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--repo", default=DEFAULT_REPO, help=f"Hugging Face repository (default {DEFAULT_REPO})")
    ap.add_argument(
        "--quant", default=DEFAULT_QUANT, help=f"quantisation label in the file name (default {DEFAULT_QUANT})"
    )
    ap.add_argument("--file", help="exact file name; overrides --quant")
    ap.add_argument("--revision", default="main")
    ap.add_argument(
        "--dest", default=str(Path(__file__).resolve().parent / "models"), help="output folder (default ./models)"
    )
    ap.add_argument("--list", action="store_true", help="list the .gguf files and exit")
    args = ap.parse_args()

    try:
        files = list_files(args.repo, args.revision)
        if args.list:
            for f in sorted(files, key=lambda f: f["size"]):
                print(f"{f['size'] / 1e6:9.1f} MB  {f['path']}")
            return
        download(args.repo, args.revision, pick(files, args.quant, args.file), Path(args.dest))
    except requests.RequestException as exc:
        die(f"network error: {exc}", 6)


if __name__ == "__main__":
    main()
