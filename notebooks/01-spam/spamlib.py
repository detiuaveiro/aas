"""Small helpers shared by the spam notebooks (data loading, tokenizer, metrics).

The algorithms themselves (Naive Bayes, TF-IDF, logistic regression, ...) live in the notebooks.
"""

import re
from pathlib import Path

import numpy as np
import polars as pl
import scipy.sparse as sp
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

DATA = Path(__file__).resolve().parents[2] / "datasets" / "spam.csv"
SEED = 42


def load(dedupe=True):
    """Return (texts, y) with y = 1 for spam. Exact duplicates are dropped by default.

    The SMS Spam Collection contains ~400 duplicated messages; if they land on both sides of a
    train/test split the test score is inflated (an easy-to-miss form of data leakage).
    """
    df = pl.read_csv(DATA).drop_nulls()
    if dedupe:
        df = df.unique(subset="SMS", keep="first", maintain_order=True)
    # the corpus lost every "£" (stored as U+FFFD); restore it, it is a strong spam cue
    texts = [t.replace("\ufffd", "£") for t in df["SMS"].to_list()]
    y = (df["Target"] == "spam").cast(pl.Int8).to_numpy()
    return texts, y


def split(texts, y, test_size=0.2, seed=SEED):
    """Stratified train/test split (keeps the spam ratio in both parts)."""
    return train_test_split(texts, y, test_size=test_size, stratify=y, random_state=seed)


def split_indices(y, test_size=0.2, seed=SEED):
    """Row indices (train, test) of the same stratified split as `split`, for code that must align several arrays."""
    return train_test_split(np.arange(len(y)), test_size=test_size, stratify=y, random_state=seed)


_TOKEN = re.compile(r"[a-z]+|[£$€%!]")


def tokenize(text):
    """Lower-case word tokens. Long digit runs (phone numbers, short codes) become one `<num>` token."""
    text = re.sub(r"\d{5,}", " num ", text.lower())
    text = re.sub(r"\d+", " ", text)
    return _TOKEN.findall(text)


def build_vocab(docs, min_df=2):
    """Words that occur in at least `min_df` messages, sorted (the fixed column order of the matrix)."""
    df = {}
    for d in docs:
        for w in set(tokenize(d)):
            df[w] = df.get(w, 0) + 1
    return sorted(w for w, c in df.items() if c >= min_df)


def count_matrix(docs, index):
    """Sparse (n_docs x |V|) matrix of raw word counts; out-of-vocabulary words are ignored."""
    rows, cols, vals = [], [], []
    for i, d in enumerate(docs):
        counts = {}
        for w in tokenize(d):
            j = index.get(w)
            if j is not None:
                counts[j] = counts.get(j, 0) + 1
        rows += [i] * len(counts)
        cols += counts.keys()
        vals += counts.values()
    return sp.csr_matrix((vals, (rows, cols)), shape=(len(docs), len(index)), dtype=np.float64)


def scores(y_true, y_pred, y_score=None):
    """Precision / recall / F1 / MCC (and PR-AUC if scores are given) for the spam class."""
    out = {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "mcc": matthews_corrcoef(y_true, y_pred),
    }
    if y_score is not None:
        out["pr_auc"] = average_precision_score(y_true, y_score)
    return {k: float(v) for k, v in out.items()}


def show(results):
    """Pretty-print a {model: scores} dict as a table."""
    cols = ["precision", "recall", "f1", "mcc", "pr_auc"]
    print(f"{'model':28}" + "".join(f"{c:>10}" for c in cols))
    for name, r in results.items():
        print(f"{name:28}" + "".join(f"{r[c]:10.3f}" if c in r else f"{'':>10}" for c in cols))


def top_log_odds(vocab, log_p_spam, log_p_ham, n=15):
    """Words with the highest (spam) and lowest (ham) log-odds, as two lists of (word, value)."""
    odds = np.asarray(log_p_spam) - np.asarray(log_p_ham)
    order = np.argsort(odds)
    return [(vocab[i], float(odds[i])) for i in order[::-1][:n]], [(vocab[i], float(odds[i])) for i in order[:n]]


LEET = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "l": "1"}


def typo_noise(text, rate, rng):
    """Random character-level noise: each letter is (with probability `rate`) deleted, doubled, swapped or leet-substituted."""
    chars, out, i = list(text), [], 0
    while i < len(chars):
        c = chars[i]
        if c.isalpha() and rng.random() < rate:
            op = int(rng.integers(4))
            if op == 1:
                out += [c, c]
            elif op == 2 and i + 1 < len(chars):
                out += [chars[i + 1], c]
                i += 1
            elif op == 3:
                out.append(LEET.get(c.lower(), c))
            # op == 0 (or a swap at the end of the string): the letter is deleted
        else:
            out.append(c)
        i += 1
    return "".join(out)


_LEET_TABLE = str.maketrans("aeiols", "431015")


def obfuscate(text, words, mode="leet"):
    """Disguise every occurrence of a word in `words` (targeted obfuscation).

    modes: leet (fr33), dots (f.r.e.e), space (f r e e), vowel (fr).
    """
    words = set(words)

    def rep(m):
        w = m.group(0)
        if w.lower() not in words:
            return w
        if mode == "leet":
            return w.lower().translate(_LEET_TABLE)
        if mode == "dots":
            return ".".join(w)
        if mode == "space":
            return " ".join(w)
        if mode == "vowel":
            return re.sub(r"[aeiou]", "", w.lower()) or w
        raise ValueError(mode)

    return re.sub(r"[A-Za-z]+", rep, text)


# ---------------------------------------------------------------------------------------------------------------------
# Static word vectors (Word2Vec, fastText): pretrained loaders and message vectors
# ---------------------------------------------------------------------------------------------------------------------

CACHE = Path(__file__).resolve().parent / ".cache"
FASTTEXT_URL = "https://github.com/avidale/compress-fasttext/releases/download/v0.0.4/cc.en.300.compressed.bin"
FASTTEXT_SHA256 = "36db006428eb2c5de8762fff90549ca8d301dfb1a2f7905c9163eca55ad13c06"


def load_pretrained_word2vec(limit=200_000):
    """Google News Word2Vec (300-d, trained on ~100 billion words), the `limit` most frequent words.

    The first call downloads 1.7 GB with gensim into ~/gensim-data (once); loading 200,000 words then takes a few seconds
    and about 240 MB of memory.
    """
    import gensim.downloader as api
    from gensim.models import KeyedVectors

    path = api.load("word2vec-google-news-300", return_path=True)
    return KeyedVectors.load_word2vec_format(path, binary=True, limit=limit)


def load_pretrained_fasttext():
    """Compressed English fastText (Common Crawl, 300-d, 22 MB; `compress-fasttext`): 20,000 words and a pruned n-gram table.

    Out-of-vocabulary words get a vector from their character n-grams, but the pruning loses many n-grams: some misspellings
    end up with a zero vector.
    """
    import hashlib

    import compress_fasttext
    import requests

    CACHE.mkdir(exist_ok=True)
    path = CACHE / "cc.en.300.compressed.bin"
    if not path.exists():
        r = requests.get(FASTTEXT_URL, timeout=60)
        r.raise_for_status()
        if hashlib.sha256(r.content).hexdigest() != FASTTEXT_SHA256:
            raise RuntimeError("checksum mismatch for the compressed fastText model")
        path.write_bytes(r.content)
    return compress_fasttext.models.CompressedFastTextKeyedVectors.load(str(path))


def word_vector(kv, word, oov_ok=False):
    """Vector of `word` or None. Pretrained vocabularies are case sensitive: try the word, then its capitalised form.

    With `oov_ok` a model that builds vectors from n-grams (fastText) is asked even for unknown words; all-zero vectors count as missing.
    """
    for cand in (word, word.capitalize()):
        if oov_ok or cand in kv.key_to_index:
            v = kv[cand]
            if np.linalg.norm(v) > 0:
                return v
    return None


def mean_vectors(kv, docs, oov_ok=False):
    """Message vectors = mean of the word vectors of the tokens (`tokenize`). Returns (matrix, share of tokens without a vector)."""
    out = np.zeros((len(docs), kv.vector_size), dtype=np.float32)
    found = total = 0
    for i, d in enumerate(docs):
        vs = []
        for w in tokenize(d):
            total += 1
            v = word_vector(kv, w, oov_ok)
            if v is not None:
                vs.append(v)
                found += 1
        if vs:
            out[i] = np.mean(vs, axis=0)
    return out, 1 - found / max(total, 1)


# ---------------------------------------------------------------------------------------------------------------------
# Scam families (used for "a new campaign" tests and for the attacks)
# ---------------------------------------------------------------------------------------------------------------------

FAMILIES = DATA.parent / "spam_families.json"
FAMILY_NAMES = ["competition", "prize claim", "mobile upgrade", "account statement", "ringtones", "chat lines"]


def _key(text):
    import hashlib

    return hashlib.sha1(text.encode()).hexdigest()[:12]


def build_families(k=6, seed=SEED):
    """Cluster the spam into `k` families (k-means on all-MiniLM-L6-v2 embeddings) and write `datasets/spam_families.json`.

    Run once by the instructor with the MiniLM server running (`make llama-up`); students load the result with `spam_families`.
    The names in FAMILY_NAMES were assigned by reading the top words of each cluster.
    """
    import json

    from sklearn.cluster import KMeans

    import llamalib as ll

    texts, y = load()
    spam = [t for t, lab in zip(texts, y) if lab == 1]
    labels = KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(ll.embed_mini(spam))
    FAMILIES.write_text(
        json.dumps({"names": FAMILY_NAMES, "labels": {_key(t): int(c) for t, c in zip(spam, labels)}}, indent=0)
    )
    return labels


def spam_families(texts, y):
    """Family id of every message: -1 for ham, 0..5 for the spam families (names in FAMILY_NAMES). Read from datasets/spam_families.json."""
    import json

    table = json.loads(FAMILIES.read_text())["labels"]
    fam = np.full(len(texts), -1, dtype=int)
    for i, (t, lab) in enumerate(zip(texts, y)):
        if lab == 1:
            fam[i] = table[_key(t)]
    return fam
