# %% [markdown]
# # Practice guide 2: linear models, fastText and small-language-model embeddings
#
# **Goal.** Climb the second half of the spam ladder: **logistic regression** trained by gradient descent (JAX), **fastText**
# with sub-words, and **frozen SLM embeddings** with a linear probe. You compare them on the same split and find out *when* the
# embeddings pay off (few labels).
#
# Read `guide_02.pdf` first. Requirements: `pip install --group slm --extra-index-url https://download.pytorch.org/whl/cpu`.

# %%
import re
import tempfile
from pathlib import Path

import fasttext
import jax
import jax.numpy as jnp
import numpy as np
import polars as pl
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedShuffleSplit, train_test_split
from sklearn.preprocessing import StandardScaler

jax.config.update("jax_enable_x64", True)

# %% [markdown]
# ## Part A. Data and TF-IDF features (given)

# %%
DATA = next(p for p in (Path("../../datasets/spam.csv"), Path("../../../datasets/spam.csv")) if p.exists())
df = pl.read_csv(DATA).drop_nulls().unique(subset="SMS", keep="first", maintain_order=True)
texts = [t.replace("�", "£") for t in df["SMS"].to_list()]
y = (df["Target"] == "spam").cast(pl.Int8).to_numpy()
X_train, X_test, y_train, y_test = train_test_split(texts, y, test_size=0.2, stratify=y, random_state=42)


def tokenize(text):
    text = re.sub(r"\d{5,}", " num ", text.lower())
    text = re.sub(r"\d+", " ", text)
    return re.findall(r"[a-z]+|[£$€%!]", text)


vec = TfidfVectorizer(tokenizer=tokenize, token_pattern=None, lowercase=False, min_df=2, sublinear_tf=True)
A_train = jnp.asarray(vec.fit_transform(X_train).toarray())
A_test = jnp.asarray(vec.transform(X_test).toarray())
vocab = vec.get_feature_names_out()
y_tr = jnp.asarray(y_train, dtype=jnp.float64)
print(A_train.shape)


def report(name, pred):
    return f"{name:28} precision {precision_score(y_test, pred):.3f}  recall {recall_score(y_test, pred):.3f}  F1 {f1_score(y_test, pred):.3f}"


# %% [markdown]
# ## Part B. Logistic regression from scratch (JAX)
#
# Model: $z=\mathbf{w}\cdot\mathbf{x}+b$, $P(\text{spam})=\sigma(z)$. Loss with L2 penalty:
#
# $$
# J=-\frac1n\sum_i\big[y_i\log\sigma(z_i)+(1-y_i)\log\sigma(-z_i)\big]+\frac\lambda2\lVert\mathbf{w}\rVert^2
# $$
#
# **Use `jax.nn.log_sigmoid`**: `log(sigmoid(z))` is `-inf` for $z=-800$.

# %%
LAM = 1e-5


def loss(params, X, y, lam=LAM):
    w, b = params
    z = X @ w + b
    # <<TODO
    # TODO: mean cross-entropy using jax.nn.log_sigmoid(z) and jax.nn.log_sigmoid(-z), plus 0.5 * lam * (w . w)
    raise NotImplementedError
    # TODO>>
    # <<SOL
    nll = -jnp.mean(y * jax.nn.log_sigmoid(z) + (1 - y) * jax.nn.log_sigmoid(-z))
    return nll + 0.5 * lam * jnp.dot(w, w)
    # SOL>>


# %%
# check 1: the loss at w=0, b=0 must be ln 2
p0 = (jnp.zeros(A_train.shape[1]), 0.0)
assert abs(float(loss(p0, A_train, y_tr)) - np.log(2)) < 1e-9
# check 2: autodiff gradient must match the analytic one
g_w, _ = jax.grad(loss)(p0, A_train, y_tr)
g_hand = A_train.T @ (jax.nn.sigmoid(A_train @ p0[0] + p0[1]) - y_tr) / len(y_tr)
assert float(jnp.abs(g_w - g_hand).max()) < 1e-9
print("loss and gradient OK")

# %% [markdown]
# Now the optimiser: plain **gradient descent**, $\theta\leftarrow\theta-\eta\nabla J$.

# %%
loss_and_grad = jax.jit(jax.value_and_grad(loss))


def gradient_descent(X, y, eta=50.0, steps=300):
    params = (jnp.zeros(X.shape[1]), 0.0)
    history = []
    for _ in range(steps):
        value, g = loss_and_grad(params, X, y)
        # <<TODO
        # TODO: update both parameters: params = (w - eta * g_w, b - eta * g_b)
        raise NotImplementedError
        # TODO>>
        # <<SOL
        params = (params[0] - eta * g[0], params[1] - eta * g[1])
        # SOL>>
        history.append(float(value))
    return params, history


params, history = gradient_descent(A_train, y_tr)
print("loss:", history[0], "->", history[-1])
assert history[-1] < history[0] * 0.5
score_lr = np.asarray(A_test @ params[0] + params[1])
print(report("logistic regression (GD)", (score_lr >= 0).astype(int)))

# %% [markdown]
# **Question B1.** Plot `history`. Try `eta` = 1, 50 and 500. What happens, and why? **B2.** The weights are the gradient of the
# score with respect to the input. Print the 10 words with the most negative weight: what could an attacker do with them?

# %%
# <<TODO
# TODO: print the 10 most negative and the 10 most positive weights with their words (np.argsort on params[0])
# TODO>>
# <<SOL
w = np.asarray(params[0])
o = np.argsort(w)
print("ham  :", [(vocab[i], round(float(w[i]), 1)) for i in o[:10]])
print("spam :", [(vocab[i], round(float(w[i]), 1)) for i in o[::-1][:10]])
# SOL>>

# %% [markdown]
# ## Part C. fastText (sub-words)
#
# fastText represents a word by the **sum of its character n-grams**, so misspellings share most of their vectors with the right
# word. Train the supervised classifier on the training set. *Note (fastText 0.9.3 with NumPy 2): call `predict` with a **list**.*

# %%
def norm(t):
    t = re.sub(r"([!£$€%?.,;:()\"'])", r" \1 ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


tmp = tempfile.TemporaryDirectory()
train_file = Path(tmp.name) / "train.txt"
train_file.write_text("\n".join(f"__label__{'spam' if lab else 'ham'} {norm(t)}" for t, lab in zip(X_train, y_train)))

# <<TODO
# TODO: ft = fasttext.train_supervised(str(train_file), lr=0.5, epoch=30, wordNgrams=2, dim=50, minn=2, maxn=5, verbose=0, seed=42)
ft = None
# TODO>>
# <<SOL
ft = fasttext.train_supervised(str(train_file), lr=0.5, epoch=30, wordNgrams=2, dim=50, minn=2, maxn=5, verbose=0, seed=42)
# SOL>>


def ft_predict(model, docs):
    labels, _ = model.predict([norm(d) for d in docs], k=1)
    return np.array([int(lab[0] == "__label__spam") for lab in labels])


pred_ft = ft_predict(ft, X_test)
print(report("fastText", pred_ft))

# %% [markdown]
# **Question C1.** Print `ft.get_nearest_neighbors("freee", k=5)`. `freee` never occurs in the training data: why does it still get
# a meaningful vector? **C2.** Corrupt only the spam of the test set by replacing `a` by `4`, `e` by `3`, `o` by `0` in every word
# and compare the **recall** of fastText and of the TF-IDF logistic regression (`sklearn` pipeline).

# %%
spam_test = [t for t, lab in zip(X_test, y_test) if lab == 1]
leet = str.maketrans("aeo", "430")
noisy = [t.lower().translate(leet) for t in spam_test]
# <<TODO
# TODO: recall of fastText on `noisy` (mean of ft_predict), and of an LR trained on A_train (use vec.transform(noisy))
# TODO>>
# <<SOL
recall_ft = float(ft_predict(ft, noisy).mean())
lr_sk = LogisticRegression(C=30, max_iter=2000).fit(np.asarray(A_train), y_train)
recall_lr = float(lr_sk.predict(vec.transform(noisy).toarray()).mean())
print(f"recall on leet-speak spam: fastText {recall_ft:.3f}   TF-IDF LR {recall_lr:.3f}")
# SOL>>

# %% [markdown]
# ## Part D. Small-language-model embeddings
#
# A pre-trained encoder maps each SMS to a vector; we keep it **frozen** and train only a linear probe. We use
# `sentence-transformers/all-MiniLM-L6-v2` (22 M parameters, 384 dimensions, about 15 s for all messages on a CPU).

# %%
# <<TODO
# TODO: model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
#       E_train = model.encode(X_train, batch_size=64, normalize_embeddings=True)   (and E_test for X_test)
model, E_train, E_test = None, None, None
# TODO>>
# <<SOL
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
E_train = model.encode(X_train, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
E_test = model.encode(X_test, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
# SOL>>
print(E_train.shape)

# %% [markdown]
# **Linear probe.** Standardise every dimension (fit the scaler on the *training* embeddings only), then a logistic regression
# with $C=0.1$.

# %%
# <<TODO
# TODO: scaler = StandardScaler().fit(E_train); probe = LogisticRegression(C=0.1, max_iter=5000).fit(scaler.transform(E_train), y_train)
probe = None
# TODO>>
# <<SOL
scaler = StandardScaler().fit(E_train)
probe = LogisticRegression(C=0.1, max_iter=5000).fit(scaler.transform(E_train), y_train)
# SOL>>
pred_emb = probe.predict(scaler.transform(E_test))
print(report("MiniLM embeddings + LR", pred_emb))

# %% [markdown]
# ## Part E. Learning curve: when do embeddings pay off?
#
# Train the TF-IDF logistic regression and the embedding probe on random stratified subsets of $n$ = 20, 50, 100, 500 messages
# (3 repetitions each) and report the mean F1 on the same test set.

# %%
sizes = [20, 50, 100, 500]
curve = {"TF-IDF + LR": [], "MiniLM + LR": []}
for n in sizes:
    f_tfidf, f_emb = [], []
    for idx, _ in StratifiedShuffleSplit(n_splits=3, train_size=n, random_state=0).split(np.zeros(len(y_train)), y_train):
        # <<TODO
        # TODO: fit both models on the subset `idx` (A_train / E_train rows) and append the test F1 to f_tfidf / f_emb
        pass
        # TODO>>
        # <<SOL
        m1 = LogisticRegression(C=30, max_iter=2000).fit(np.asarray(A_train)[idx], y_train[idx])
        f_tfidf.append(f1_score(y_test, m1.predict(np.asarray(A_test))))
        sc = StandardScaler().fit(E_train[idx])
        m2 = LogisticRegression(C=0.1, max_iter=5000).fit(sc.transform(E_train[idx]), y_train[idx])
        f_emb.append(f1_score(y_test, m2.predict(sc.transform(E_test))))
        # SOL>>
    curve["TF-IDF + LR"].append(float(np.mean(f_tfidf)) if f_tfidf else float("nan"))
    curve["MiniLM + LR"].append(float(np.mean(f_emb)) if f_emb else float("nan"))
print(f"{'labelled messages':20}" + "".join(f"{n:>8}" for n in sizes))
for k, v in curve.items():
    print(f"{k:20}" + "".join(f"{x:8.3f}" for x in v))

# %% [markdown]
# ## Part F. Summary (for the report)
#
# Fill in the table with the precision, recall and F1 of the four models on the test set, and discuss: which model would you
# deploy on a mail gateway (cost per message, labels available, robustness to spelling tricks)?
