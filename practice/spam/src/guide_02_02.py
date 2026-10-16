# %% [markdown]
# # Practice guide 2: from words to meaning (word vectors, small language models, llama.cpp)
#
# **Goal.** Climb the second half of the spam ladder: **Word2Vec** and **fastText** vectors (trained on our messages *and*
# pre-trained), **sentence embeddings** of a small language model (MiniLM), and **EmbeddingGemma 2**, both **served
# by llama.cpp**. You compare them on the same split and find out *when* each one pays off.
#
# Read `guide_02_02.pdf` first. Time: about 2 hours. Cells marked **(given)** are complete.
#
# **Requirements.** `make venv` (no PyTorch, no TensorFlow), and for parts D and E the llama-swap stack: `make llama-models` then
# `make llama-up` from the repository root (it detects your GPU and picks the matching image; `make llama-up PROFILE=cpu` forces the CPU). Set `AAS_W2V=skip` to skip the 1.7 GB Google News download.

# %%
import os
import sys
import time
from pathlib import Path

import numpy as np
import requests
from gensim.models import FastText, Word2Vec
from matplotlib import pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

LIB = next(p for p in (Path("../../notebooks/01-spam"), Path("../../../notebooks/01-spam")) if p.exists())  # student / solution folder
sys.path.insert(0, str(LIB.resolve()))
import llamalib as ll  # noqa: E402  (client for the local llama-swap endpoint)
import spamlib as sl  # noqa: E402  (data, tokenizer, metrics, pre-trained loaders)

# %% [markdown]
# ## Part A. Data and helpers (given)
#
# Same data protocol as guide 1: duplicates removed before the split, stratified 80/20, everything fitted on the training part only.

# %%
texts, y = sl.load()
X_train, X_test, y_train, y_test = sl.split(texts, y)
tok_train = [sl.tokenize(t) for t in X_train]
print(len(X_train), len(X_test), "training tokens:", sum(map(len, tok_train)))


def probe(C=0.1):
    """Standardise every dimension (training statistics), then a logistic regression."""
    return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=5000))


def f1_of(a_train, a_test, C=0.1):
    return sl.scores(y_test, probe(C).fit(a_train, y_train).predict(a_test))["f1"]


def f1_cv(a_train, a_test):
    """Like f1_of, but C is chosen by 3-fold cross-validation on the training set."""
    grid = {"logisticregression__C": [1e-3, 1e-2, 1e-1, 1.0]}
    fit = GridSearchCV(probe(), grid, cv=3, scoring="f1", n_jobs=-1).fit(a_train, y_train)
    return sl.scores(y_test, fit.predict(a_test))["f1"]


tfidf = make_pipeline(
    TfidfVectorizer(tokenizer=sl.tokenize, token_pattern=None, lowercase=False, ngram_range=(1, 2), min_df=2, sublinear_tf=True),
    LogisticRegression(C=30, max_iter=2000),
).fit(X_train, y_train)
f1_tfidf = sl.scores(y_test, tfidf.predict(X_test))["f1"]
print(f"reference, TF-IDF + logistic regression: F1 {f1_tfidf:.3f}")

# %% [markdown]
# ## Part B. Word2Vec on our messages
#
# Train a **skip-gram** model with negative sampling on the training messages (labels are not used), then build a message vector as
# the **mean** of its word vectors.

# %%
# <<TODO
# TODO: w2v = Word2Vec(tok_train, vector_size=100, window=5, min_count=2, negative=5, sg=1, epochs=30, workers=1, seed=42)
raise NotImplementedError
# TODO>>
# <<SOL
w2v = Word2Vec(tok_train, vector_size=100, window=5, min_count=2, negative=5, sg=1, epochs=30, workers=1, seed=42)
# SOL>>
wv = w2v.wv
print(f"vocabulary: {len(wv)} words")
for word in ("free", "prize", "call", "home"):
    print(f"{word:6}", [w for w, _ in wv.most_similar(word, topn=6)])


# %%
def message_vector(kv, tokens):
    """Mean of the vectors of the tokens that have one (zeros if none)."""
    # <<TODO
    # TODO: vs = [kv[w] for w in tokens if w in kv.key_to_index]; return the mean (np.mean(vs, axis=0)) or np.zeros(kv.vector_size)
    raise NotImplementedError
    # TODO>>
    # <<SOL
    vs = [kv[w] for w in tokens if w in kv.key_to_index]
    return np.mean(vs, axis=0) if vs else np.zeros(kv.vector_size)
    # SOL>>


# check: agrees with the library function
ours = np.vstack([message_vector(wv, sl.tokenize(t)) for t in X_test[:20]])
ref, _ = sl.mean_vectors(wv, X_test[:20])
assert np.allclose(ours, ref, atol=1e-5)
print("message_vector OK")

A_tr = np.vstack([message_vector(wv, t) for t in tok_train])
A_te = np.vstack([message_vector(wv, sl.tokenize(t)) for t in X_test])
f1_w2v = f1_of(A_tr, A_te)
print(f"Word2Vec skip-gram (in-domain) + LR: F1 {f1_w2v:.3f}   (TF-IDF reference {f1_tfidf:.3f})")

# %% [markdown]
# **Question B1.** Look at the neighbours of `free`, `prize`, `call` and `home`. What kind of words do you get, and why do they differ
# from what a dictionary would say? **B2.** The corpus has only about 65,000 tokens. Which words get unreliable vectors, and why?

# <<SOL
# %% [markdown]
# **Answers B.** The neighbours are words that appear in the *same SMS contexts*, not synonyms: `free` sits with `unlimited`, `camcorder`, `jamster`, `bluetooth` (the products of the same campaigns), `prize` with `caller`, `guaranteed`, `pound`, `bonus`, `call` with `quoting`, `delivery`, `landline`, `home` with `lonely`, `chillin`, `knackered` (personal chat). Word2Vec learns distributional similarity, so on a spam corpus it learns campaign vocabulary. With about 65,000 training tokens most words occur a handful of times: rare words (names, typos, one-off products) get vectors from very few contexts, so their neighbours (`senthil`, `engin`) are noise.
# SOL>>

# %% [markdown]
# ## Part C. In-domain or pre-trained?
#
# Load two pre-trained models (**given**): fastText, Common Crawl, compressed to 22 MB, and Word2Vec, Google News (1.7 GB the first time).
# Measure how many test tokens each source has no vector for, and compare the F1 of the four.

# %%
ft_pre = sl.load_pretrained_fasttext()
gn = None if os.environ.get("AAS_W2V") == "skip" else sl.load_pretrained_word2vec()
tok_test = [sl.tokenize(t) for t in X_test]


def oov_rate(kv, docs, oov_ok=False):
    """Share of the tokens of `docs` for which `kv` has no usable vector (`sl.word_vector` returns None)."""
    # <<TODO
    # TODO: tokens = all tokens of docs; return the share with sl.word_vector(kv, token, oov_ok) is None
    raise NotImplementedError
    # TODO>>
    # <<SOL
    tokens = [w for d in docs for w in d]
    return sum(sl.word_vector(kv, w, oov_ok) is None for w in tokens) / len(tokens)
    # SOL>>


sources = {"Word2Vec in-domain": (wv, False), "fastText pre-trained": (ft_pre, True)}
if gn is not None:
    sources["Word2Vec Google News"] = (gn, False)
print(f"{'source':24}{'OOV (test)':>12}{'F1':>8}")
for name, (kv, oov_ok) in sources.items():
    a_tr, _ = sl.mean_vectors(kv, X_train, oov_ok)
    a_te, _ = sl.mean_vectors(kv, X_test, oov_ok)
    print(f"{name:24}{oov_rate(kv, tok_test, oov_ok):12.1%}{f1_of(a_tr, a_te):8.3f}")
# <<SOL
if gn is not None:  # C1: the ten most frequent training-spam tokens that Google News has no vector for
    from collections import Counter

    oov = Counter(w for t, lab in zip(X_train, y_train) if lab == 1 for w in sl.tokenize(t) if sl.word_vector(gn, w) is None)
    print("most frequent spam tokens without a Google News vector:", oov.most_common(10))
# SOL>>

# %% [markdown]
# **Question C1.** Print ten frequent spam tokens that Google News has no vector for. What do they have in common, and why does that
# matter for a spam filter? **C2.** Which source wins on this corpus, and what would change if the corpus were product reviews?
#
# Now the spammer's trick: **leet-speak**. Train an in-domain **fastText** (sub-words) model and compare it with TF-IDF on spam in which
# the 25 most spammy words are disguised (`fr33`).

# <<SOL
# %% [markdown]
# **Answers C1.** The list printed above (this split): `num`, `!`, `msg`, `pobox`, `optout`, `sae`, `mobileupd`, `wq`, `gbp`, `freemsg`. They are our own placeholder (`num` for phone numbers), punctuation, SMS abbreviations and glued words that a news corpus never writes. They are exactly the strongest spam signals, so a pre-trained vocabulary loses the evidence a filter needs.
#
# **Answers C2.** The in-domain Word2Vec wins (F1 0.935 against 0.882 for pre-trained fastText and 0.888 for Google News), although its OOV rate is higher (9.1%: rare test words below `min_count`): it has vectors for the tokens that matter. On product reviews, written in standard English, the pre-trained vectors would cover the vocabulary, carry knowledge learned from billions of words, and would probably win, especially with a small corpus.
# SOL>>

# %%
# <<TODO
# TODO: ft = FastText(tok_train, vector_size=100, window=5, min_count=2, sg=1, min_n=2, max_n=5, epochs=30, workers=1, seed=42).wv
raise NotImplementedError
# TODO>>
# <<SOL
ft = FastText(tok_train, vector_size=100, window=5, min_count=2, sg=1, min_n=2, max_n=5, epochs=30, workers=1, seed=42).wv
# SOL>>
a_tr_ft, _ = sl.mean_vectors(ft, X_train, oov_ok=True)
clf_ft = probe().fit(a_tr_ft, y_train)

vec, lr_ = tfidf[0], tfidf[1]
names = np.array(vec.get_feature_names_out())
trigger = [w for w in names[np.argsort(-lr_.coef_[0])] if w.isalpha()][:25]
spam_test = [t for t, lab in zip(X_test, y_test) if lab == 1]
leet = [sl.obfuscate(t, trigger, "leet") for t in spam_test]
rec_tfidf = float(tfidf.predict(leet).mean())
rec_ft = float(clf_ft.predict(sl.mean_vectors(ft, leet, oov_ok=True)[0]).mean())
print(f"recall on leet-speak spam: TF-IDF {rec_tfidf:.3f}   fastText in-domain {rec_ft:.3f}")
# <<SOL
print(f"recall on clean spam:      TF-IDF {float(tfidf.predict(spam_test).mean()):.3f}   fastText in-domain "
      f"{float(clf_ft.predict(sl.mean_vectors(ft, spam_test, oov_ok=True)[0]).mean()):.3f}")
# SOL>>

# %% [markdown]
# **Question C3.** Report both recalls (and the recall on the *clean* spam, for reference). Explain the difference. Which
# disguises would hurt fastText more (think of `f.r.e.e`)?

# <<SOL
# %% [markdown]
# **Answers C3.** On the leet-speak spam TF-IDF keeps a recall of 0.845 and the in-domain fastText 0.814 (clean spam: 0.907 for both, so the disguise costs TF-IDF 0.06 and fastText 0.09). Sub-words did not save fastText here: the disguised tokens share few character n-grams with the originals (`fr33` and `free` share only the n-grams built on `fr`), so their vectors land far from the spam words, and the mean over the message dilutes the remaining evidence; TF-IDF simply ignores the unknown tokens and still sees the rest of the message. Disguises that break every n-gram (`f.r.e.e`, spaces or dots between letters) hurt fastText most; a normalisation step (class 04) is the cheaper defence.
# SOL>>

# %% [markdown]
# ## Part D. A small sentence embedder (MiniLM)
#
# `all-MiniLM-L6-v2` (22 M parameters) maps a whole message to one 384-d vector. It is the `minilm` model of the llama-swap endpoint (llama.cpp, CPU), stays **frozen**,
# and you train only the probe. The client `ll.embed_mini` caches the vectors on disk.

# %%
M_tr, M_te = ll.embed_mini(X_train), ll.embed_mini(X_test)
# <<TODO
# TODO: f1_minilm = f1_of(M_tr, M_te)  (the probe standardises with training statistics)
raise NotImplementedError
# TODO>>
# <<SOL
f1_minilm = f1_of(M_tr, M_te)
# SOL>>
print(f"MiniLM + LR: F1 {f1_minilm:.3f}")

# %% [markdown]
# **Question D1.** Why do we standardise the embeddings, and why must the scaler be fitted on the training set only?

# <<SOL
# %% [markdown]
# **Answers D1.** The logistic regression is regularised and trained by an optimiser: features on very different scales get unequal penalties and make the optimisation ill-conditioned, so we bring each dimension to mean 0, variance 1. The scaler is part of the model: fitted on all messages it would use the test set's mean and variance (leakage), so it is fitted on the training split only and applied to the test split.
# SOL>>

# %% [markdown]
# ## Part E. EmbeddingGemma 2 served by llama.cpp
#
# Start the server (see the header). Check that it answers, then talk to it **without** any helper library: one HTTP request.

# %%
print("model served:", ll.model_id())
pair = [
    "WINNER!! You have won a £900 prize reward! To claim call 09061701461 now.",
    "Congratulations, you were selected for a cash award. Ring 09061701461 today to collect.",
    "Ok I'll be home at 7, want me to pick up dinner?",
]
# <<TODO
# TODO: r = requests.post(f"{ll.URL}/v1/embeddings", json={"input": [ll.DOC + t for t in pair], "model": "embgemma"}, timeout=60)
#       e = np.array([d["embedding"] for d in r.json()["data"]])
raise NotImplementedError
# TODO>>
# <<SOL
r = requests.post(f"{ll.URL}/v1/embeddings", json={"input": [ll.DOC + t for t in pair], "model": "embgemma"}, timeout=60)
e = np.array([d["embedding"] for d in r.json()["data"]])
# SOL>>
print("shape:", e.shape, "norms:", np.linalg.norm(e, axis=1).round(3))
print(f"cosine(prize, rewrite) = {e[0] @ e[1]:.3f}   cosine(prize, chat) = {e[0] @ e[2]:.3f}")
assert e.shape == (3, 768) and e[0] @ e[1] > e[0] @ e[2]

# %% [markdown]
# **Question E1.** Why is the cosine of the first pair high although the messages share almost no word (apart from the number)? What
# would TF-IDF give for that pair?
#
# Now all the messages (the client `ll.embed` batches the requests and caches the vectors on disk; the first run takes a few minutes).

# <<SOL
# %% [markdown]
# **Answers E1.** Cosine 0.903 for the prize message and its rewrite against 0.626 for the prize message and a chat message: the encoder maps meaning, not words, so a paraphrase lands close to the original although the two share almost no token. TF-IDF compares token overlap: with only the number in common (and `num` being frequent, low idf) the cosine would be close to 0.
# SOL>>

# %%
t0 = time.time()
N_tr, N_te = ll.embed(X_train), ll.embed(X_test)
print(f"embedded in {time.time() - t0:.0f}s (0 s when cached)")
f1_embg = f1_cv(N_tr, N_te)
print(f"EmbeddingGemma 2 + LR: F1 {f1_embg:.3f}")

# %% [markdown]
# **Matryoshka.** The model was trained so that the first $d$ values of the vector are already a good embedding. Implement the
# truncation (keep $d$ values, **normalise again**) and measure the F1 for several $d$.


# %%
def truncate(emb, d):
    """First d dimensions, re-normalised to unit length."""
    # <<TODO
    # TODO: emb[:, :d] divided by its row norms
    raise NotImplementedError
    # TODO>>
    # <<SOL
    part = emb[:, :d]
    return part / np.linalg.norm(part, axis=1, keepdims=True)
    # SOL>>


assert np.allclose(np.linalg.norm(truncate(N_te, 256), axis=1), 1.0)
print(f"{'dimensions':>11}{'bytes (fp32)':>14}{'F1':>8}")
for d in (768, 512, 256, 128, 64):
    print(f"{d:11d}{4 * d:14d}{f1_cv(truncate(N_tr, d), truncate(N_te, d)):8.3f}")

# %% [markdown]
# **Question E2.** What is the smallest $d$ whose F1 is within 0.01 of the full vector? What does it save per million messages?
#
# **The task prefix.** EmbeddingGemma asks for `title: none | text: ` in front of every document (`ll.DOC`). Does it matter for a classifier? A single F1 is noisy
# (1,024 test messages, about 130 spam): attach a **bootstrap interval**.

# <<SOL
# %% [markdown]
# **Answers E2.** $d=512$ keeps F1 0.960 (the full 768 also gives 0.960); 256 drops to 0.940 and 128 to 0.948, more than 0.01 below. In float32, 512 dimensions save 1,024 bytes per message: about 1 GB per million stored messages, and a third of the work of every similarity computation.
# SOL>>

# %%
def bootstrap_f1(y_true, y_pred, n=500, seed=42):
    """95% interval of the F1 over n resamples of the test set (with replacement)."""
    rng = np.random.default_rng(seed)
    # <<TODO
    # TODO: idx = rng.integers(0, len(y_true), size=(n, len(y_true))); f = [sl.scores(y_true[i], y_pred[i])["f1"] for i in idx]; return np.percentile(f, [2.5, 97.5])
    raise NotImplementedError
    # TODO>>
    # <<SOL
    idx = rng.integers(0, len(y_true), size=(n, len(y_true)))
    f = [sl.scores(y_true[i], y_pred[i])["f1"] for i in idx]
    return np.percentile(f, [2.5, 97.5])
    # SOL>>


for label, prefix in (("title: none | text: ", ll.DOC), ("(none)", "")):
    a_tr, a_te = ll.embed(X_train, prefix=prefix), ll.embed(X_test, prefix=prefix)
    pred = probe(0.1).fit(a_tr, y_train).predict(a_te)
    lo, hi = bootstrap_f1(y_test, pred)
    print(f"{label:20} F1 {sl.scores(y_test, pred)['f1']:.3f}   95% interval [{lo:.3f}, {hi:.3f}]")

# %% [markdown]
# **Question E3.** Do the two intervals overlap? What do you conclude about the prefix for *classification*? Why would the same
# question have another answer for *retrieval*?
#
# **Cost.** Time the two servers (batches of 16) and compare with TF-IDF.

# <<SOL
# %% [markdown]
# **Answers E3.** Yes, almost completely: with the prefix F1 0.960 [0.932, 0.983], without it 0.960 [0.931, 0.982]. For classification with a trained head the prefix makes no measurable difference on this data. For retrieval it matters: queries and documents are embedded with different prefixes so that a short question and a long answer land close together; without them the asymmetric task loses accuracy.
# SOL>>

# %%
sample = X_test[:128]
t0 = time.time()
for i in range(0, len(sample), 16):
    ll.embed(sample[i : i + 16], cache=False, batch=16)
ms_embg = 1000 * (time.time() - t0) / len(sample)
t0 = time.time()
for i in range(0, len(sample), 16):
    ll.embed_mini(sample[i : i + 16], cache=False, batch=16)
ms_minilm = 1000 * (time.time() - t0) / len(sample)
print(f"EmbeddingGemma 2: {ms_embg:.1f} ms per message;  MiniLM: {ms_minilm:.1f} ms;  TF-IDF + LR: about 0.04 ms")

# %% [markdown]
# ## Part F. Few labels and the final table
#
# Train the classifiers on only $n$ labelled messages (the vectors above are unchanged: they never used a label). Mean F1 over 5 random
# stratified subsets.

# %%
SIZES = [20, 50, 100, 250]
curve = {"TF-IDF + LR": [], "Word2Vec in-domain": [], "MiniLM": [], "EmbeddingGemma 2": []}
for n in SIZES:
    reps = {k: [] for k in curve}
    for idx, _ in StratifiedShuffleSplit(n_splits=5, train_size=n, random_state=42).split(np.zeros(len(y_train)), y_train):
        yt = y_train[idx]
        m = tfidf.fit([X_train[i] for i in idx], yt)
        reps["TF-IDF + LR"].append(sl.scores(y_test, m.predict(X_test))["f1"])
        for name, (a, b, C) in {"Word2Vec in-domain": (A_tr, A_te, 0.1), "MiniLM": (M_tr, M_te, 0.1), "EmbeddingGemma 2": (N_tr, N_te, 0.1)}.items():
            reps[name].append(sl.scores(y_test, probe(C).fit(a[idx], yt).predict(b))["f1"])
    for k, v in reps.items():
        curve[k].append(float(np.mean(v)))
print(f"{'labelled messages':22}" + "".join(f"{n:>8}" for n in SIZES))
for k, v in curve.items():
    print(f"{k:22}" + "".join(f"{a:8.3f}" for a in v))
_ = tfidf.fit(X_train, y_train)  # restore the full model

# %% [markdown]
# **Question F1.** Fill in the table below from your results. **F2.** In which range of labelled examples do the embeddings win,
# and why do they need fewer labels? **F3.** Choose a model for a mail gateway that handles 10,000 messages per second and receives few
# new labels; justify with cost per message, accuracy and robustness (remember the leet-speak result).
#
# | Model | F1 (all labels) | F1 (50 labels) | cost per message |
# |:--|--:|--:|:--|
# | TF-IDF + logistic regression | | | |
# | Word2Vec in-domain + LR | | | |
# | MiniLM + LR | | | |
# | EmbeddingGemma 2 (llama.cpp) + LR | | | |

# <<SOL
# %% [markdown]
# **Answers F.** All labels: TF-IDF + LR 0.944, Word2Vec in-domain 0.935, MiniLM 0.957, EmbeddingGemma 2 0.960. With 50 labels: 0.490, 0.783, 0.577, 0.764. Cost per message: TF-IDF about 0.04 ms, MiniLM 6.6 ms, EmbeddingGemma 20.8 ms on this machine (Word2Vec: a mean of word vectors, well under 1 ms).
#
# **F2.** The embeddings win below a few hundred labels (at 50 labels 0.76-0.78 for EmbeddingGemma and in-domain Word2Vec against 0.49 for TF-IDF): they come with a geometry where messages with the same meaning are already close, so a linear head needs few examples to find the boundary; TF-IDF must learn every word from the labels.
#
# **F3.** At 10,000 messages per second EmbeddingGemma needs about 208 s of server time per second (some 200 parallel servers at 20.8 ms), TF-IDF about 0.4 s of one CPU core. A reasonable gateway runs TF-IDF + LR on every message and sends only the uncertain ones (near the threshold) to the embedding model; the embeddings also help when few new labels arrive. Neither model resisted leet-speak (part C): normalise the text before either.
# SOL>>
