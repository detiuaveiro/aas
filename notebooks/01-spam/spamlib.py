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
