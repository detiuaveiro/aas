# %% [markdown]
# # Practice guide 1: a spam filter from scratch (Naive Bayes and TF-IDF)
#
# **Goal.** Build the first rungs of the spam ladder yourself: a tokenizer, a Naive Bayes classifier that works in log space,
# the evaluation metrics, and TF-IDF. Every `TODO` cell must be completed; the `check` cells tell you whether you got it right.
#
# Read `guide_01.pdf` first. Time: about 2 hours. Cells marked **(given)** are complete.

# %%
from pathlib import Path

import numpy as np
import polars as pl
import scipy.sparse as sp
from scipy.special import logsumexp
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics import precision_recall_curve, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

# %% [markdown]
# ## Part A. Data (given)
#
# SMS Spam Collection: 5,574 messages. Exact duplicates are removed **before** the split, otherwise the same text can sit in both
# train and test and inflate the score.

# %%
DATA = next(p for p in (Path("../../datasets/spam.csv"), Path("../../../datasets/spam.csv")) if p.exists())  # student / solution folder
df = pl.read_csv(DATA).drop_nulls()
print("raw messages:", df.height)
df = df.unique(subset="SMS", keep="first", maintain_order=True)
texts = [t.replace("�", "£") for t in df["SMS"].to_list()]  # the corpus lost every pound sign
y = (df["Target"] == "spam").cast(pl.Int8).to_numpy()
print("unique messages:", len(texts), " spam ratio:", round(float(y.mean()), 3))

X_txt_train, X_txt_test, y_train, y_test = train_test_split(texts, y, test_size=0.2, stratify=y, random_state=42)
print(len(X_txt_train), len(X_txt_test), int(y_test.sum()))

# %% [markdown]
# **Question A1.** Why do we split *before* building the vocabulary? Why `stratify=y`? (Answer in your report.)

# %% [markdown]
# ## Part B. The tokenizer
#
# Implement `tokenize(text)`:
#
# 1. lower-case the text;
# 2. replace every run of **5 or more digits** (phone numbers, short codes) by the word `num`;
# 3. remove the remaining digits;
# 4. return the list of tokens made of letters `[a-z]+`, **plus** the single characters `£ $ € % !` (strong spam signals).
#
# Example: `"URGENT! Call 09061701461 now, win £100"` $\rightarrow$ `['urgent', '!', 'call', 'num', 'now', 'win', '£']`.

# %%
import re


def tokenize(text):
    # <<TODO
    # TODO: implement (hint: two re.sub calls, then re.findall with r"[a-z]+|[£$€%!]")
    raise NotImplementedError
    # TODO>>
    # <<SOL
    text = re.sub(r"\d{5,}", " num ", text.lower())
    text = re.sub(r"\d+", " ", text)
    return re.findall(r"[a-z]+|[£$€%!]", text)
    # SOL>>


# %%
# check
assert tokenize("URGENT! Call 09061701461 now, win £100") == ["urgent", "!", "call", "num", "now", "win", "£"]
assert tokenize("Ok lar... Joking wif u oni...") == ["ok", "lar", "joking", "wif", "u", "oni"]
print("tokenizer OK")

# %% [markdown]
# ## Part C. The count matrix (given)
#
# The vocabulary contains the words that occur in at least 2 **training** messages. `count_matrix` returns a sparse matrix
# (messages x words) of raw counts; out-of-vocabulary words are ignored.

# %%
def build_vocab(docs, min_df=2):
    df_ = {}
    for d in docs:
        for w in set(tokenize(d)):
            df_[w] = df_.get(w, 0) + 1
    return sorted(w for w, c in df_.items() if c >= min_df)


def count_matrix(docs, index):
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


vocab = build_vocab(X_txt_train)
index = {w: i for i, w in enumerate(vocab)}
C_train, C_test = count_matrix(X_txt_train, index), count_matrix(X_txt_test, index)
print(C_train.shape, "vocabulary:", len(vocab))

# %% [markdown]
# ## Part D. Multinomial Naive Bayes in log space
#
# With word counts $x_w$ and smoothing constant $k$:
#
# $$
# \log P(w\mid y)=\log(N_{w,y}+k)-\log\Big(\sum_{w'}N_{w',y}+k|V|\Big),\qquad
# \ell_y(\mathbf{x})=\log P(y)+\sum_w x_w\log P(w\mid y)
# $$
#
# and $\log P(y\mid\mathbf{x})=\ell_y-\operatorname{logsumexp}(\ell_0,\ell_1)$. Complete the class.

# %%
class NaiveBayes:
    def __init__(self, k=1.0):
        self.k = k

    def fit(self, X, y):
        # <<TODO
        # TODO 1: self.log_prior_  -> array of 2 values, log(P(ham)), log(P(spam))   (hint: np.bincount)
        # TODO 2: N = counts per class, shape (2, |V|): sum the rows of X where y == c
        # TODO 3: self.log_lik_ = log(N + k) - log(N.sum(axis=1, keepdims=True) + k * |V|)
        raise NotImplementedError
        # TODO>>
        # <<SOL
        self.log_prior_ = np.log(np.bincount(y) / len(y))
        n = np.vstack([np.asarray(X[y == c].sum(axis=0)).ravel() for c in (0, 1)])
        self.log_lik_ = np.log(n + self.k) - np.log(n.sum(axis=1, keepdims=True) + self.k * n.shape[1])
        # SOL>>
        return self

    def joint_log_proba(self, X):
        # <<TODO
        # TODO 4: return X @ self.log_lik_.T + self.log_prior_   (shape: n_messages x 2)
        raise NotImplementedError
        # TODO>>
        # <<SOL
        return X @ self.log_lik_.T + self.log_prior_
        # SOL>>

    def predict_proba(self, X):
        jll = self.joint_log_proba(X)
        # <<TODO
        # TODO 5: normalise in LOG space with logsumexp (axis=1, keepdims=True), then exponentiate
        raise NotImplementedError
        # TODO>>
        # <<SOL
        return np.exp(jll - logsumexp(jll, axis=1, keepdims=True))
        # SOL>>

    def predict(self, X, threshold=0.5):
        return (self.predict_proba(X)[:, 1] >= threshold).astype(int)


# %%
# check: must agree with scikit-learn
nb = NaiveBayes(k=1.0).fit(C_train, y_train)
ref = MultinomialNB(alpha=1.0).fit(C_train, y_train)
err = np.abs(nb.predict_proba(C_test) - ref.predict_proba(C_test)).max()
print("max |ours - sklearn| =", err)
assert err < 1e-9
print("Naive Bayes OK")

# %% [markdown]
# **Question D1.** Build a message of ~1,000 words (join 30 spam messages) and compute the posterior **without** logs (product of
# probabilities). What do you get? Why does the log version not fail? Write the two outputs in your report.

# %%
long_msg = " ".join(t for t, lab in zip(X_txt_train, y_train) if lab == 1)[:6000]
x_long = count_matrix([long_msg], index)
# <<TODO
# TODO: compute the naive posterior: prior * product of P(w|y)**count, then divide by the sum over the two classes.
# Hint: np.exp(nb.log_lik_) gives the probabilities; use np.prod(p ** x_long.toarray(), axis=1).
naive_posterior = None
print("naive posterior:", naive_posterior)
# TODO>>
# <<SOL
prod = np.exp(nb.log_prior_) * np.prod(np.exp(nb.log_lik_) ** x_long.toarray(), axis=1)
with np.errstate(invalid="ignore"):
    naive_posterior = prod / prod.sum()
print("naive posterior:", naive_posterior)
# SOL>>
print("log-space posterior:", nb.predict_proba(x_long))

# %% [markdown]
# ## Part E. Evaluation
#
# Implement precision, recall and F1 from the **confusion counts** and compare with scikit-learn.

# %%
def confusion(y_true, y_pred):
    # <<TODO
    # TODO: return tp, fp, fn, tn (spam is the positive class, label 1)
    raise NotImplementedError
    # TODO>>
    # <<SOL
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    return tp, fp, fn, tn
    # SOL>>


def prf(y_true, y_pred):
    tp, fp, fn, tn = confusion(y_true, y_pred)
    # <<TODO
    # TODO: precision = tp/(tp+fp), recall = tp/(tp+fn), f1 = 2PR/(P+R)   (guard against division by zero)
    raise NotImplementedError
    # TODO>>
    # <<SOL
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f1
    # SOL>>


# %%
pred = nb.predict(C_test)
p, r, f1 = prf(y_test, pred)
print(f"precision {p:.3f}  recall {r:.3f}  F1 {f1:.3f}   confusion (tp, fp, fn, tn) = {confusion(y_test, pred)}")
assert abs(p - precision_score(y_test, pred)) < 1e-12 and abs(r - recall_score(y_test, pred)) < 1e-12
print("metrics OK")

# %% [markdown]
# **Question E1.** A filter that predicts *ham* for every message: what are its accuracy, precision and recall on this test set?
# Which metric exposes it?
#
# ### Operating point
#
# A mail provider prefers to let some spam through rather than block a real message. Find the **lowest threshold** on
# $P(\text{spam}\mid\mathbf{x})$ for which the precision is at least 0.99, and report the recall at that threshold.

# %%
proba = nb.predict_proba(C_test)[:, 1]
# <<TODO
# TODO: use precision_recall_curve(y_test, proba); find the first threshold with precision >= 0.99
threshold, recall_at = None, None
# TODO>>
# <<SOL
prec, rec, thr = precision_recall_curve(y_test, proba)
i = int(np.where(prec[:-1] >= 0.99)[0][0])
threshold, recall_at = float(thr[i]), float(rec[i])
# SOL>>
print(f"threshold {threshold}, recall at that threshold {recall_at}")

# %% [markdown]
# ## Part F. TF-IDF
#
# For a term $t$ in document $d$ with raw count $c_{t,d}$ and $N$ training documents:
#
# $$
# \text{tf}=1+\ln c_{t,d}\ (c>0),\qquad \text{idf}(t)=\ln\frac{1+N}{1+\text{df}(t)}+1,\qquad
# \mathbf{x}_d\leftarrow\frac{\text{tf}\cdot\text{idf}}{\lVert\text{tf}\cdot\text{idf}\rVert_2}
# $$

# %%
def tfidf_fit(C):
    """Return the idf vector computed on the TRAINING counts."""
    N = C.shape[0]
    # <<TODO
    # TODO: df = number of documents containing each word ((C > 0).sum(axis=0)); return the idf formula above
    raise NotImplementedError
    # TODO>>
    # <<SOL
    df_ = np.asarray((C > 0).sum(axis=0)).ravel()
    return np.log((1 + N) / (1 + df_)) + 1
    # SOL>>


def tfidf_transform(C, idf):
    T = C.tocsr().copy()
    # <<TODO
    # TODO 1: sublinear tf: T.data = 1 + ln(T.data)
    # TODO 2: multiply the columns by idf (T @ sp.diags(idf))
    # TODO 3: L2-normalise every row
    raise NotImplementedError
    # TODO>>
    # <<SOL
    T.data = 1.0 + np.log(T.data)
    T = T @ sp.diags(idf)
    norms = np.sqrt(np.asarray(T.multiply(T).sum(axis=1)).ravel())
    norms[norms == 0] = 1.0
    return sp.diags(1.0 / norms) @ T
    # SOL>>


# %%
# check: must agree with scikit-learn
idf = tfidf_fit(C_train)
T_train, T_test = tfidf_transform(C_train, idf), tfidf_transform(C_test, idf)
ref_t = TfidfTransformer(sublinear_tf=True).fit(C_train)
err = abs(ref_t.transform(C_test) - T_test).max()
print("max |ours - sklearn| =", err)
assert err < 1e-9
print("TF-IDF OK")
order = np.argsort(idf)
print("lowest idf :", [vocab[i] for i in order[:8]])
print("highest idf:", [vocab[i] for i in order[-5:]])

# %% [markdown]
# **Question F1.** Why are `you`, `to`, `the` at the bottom of the idf list, and what does that do to their weight?
#
# ## Part G. Compare the models (report table)
#
# Train Naive Bayes on the **counts** and on the **TF-IDF** matrix, with $k=0.1$ and $k=1$, and fill in the table
# (precision, recall, F1 on the test set). Which representation is better? Is the difference larger than the noise? (Repeat the
# split with 3 different `random_state` values to estimate it.)

# %%
rows = {}
# <<TODO
# TODO: for name, (A, B) in {"counts": (C_train, C_test), "tf-idf": (T_train, T_test)}.items() and k in (0.1, 1.0):
#       fit NaiveBayes(k) on A, predict B, store prf(y_test, pred) in rows[f"{name} k={k}"]
# TODO>>
# <<SOL
for name, (A, B) in {"counts": (C_train, C_test), "tf-idf": (T_train, T_test)}.items():
    for k in (0.1, 1.0):
        m = NaiveBayes(k).fit(A, y_train)
        rows[f"{name} k={k}"] = prf(y_test, m.predict(B))
# SOL>>
for name, (p, r, f1) in rows.items():
    print(f"{name:18} precision {p:.3f}  recall {r:.3f}  F1 {f1:.3f}")

# %% [markdown]
# ## Part H. What did the model learn?
#
# List the 10 words with the highest and the lowest log-odds $\log P(w\mid\text{spam})-\log P(w\mid\text{ham})$.

# %%
# <<TODO
# TODO: odds = nb.log_lik_[1] - nb.log_lik_[0]; print the top-10 and bottom-10 words (np.argsort)
# TODO>>
# <<SOL
odds = nb.log_lik_[1] - nb.log_lik_[0]
o = np.argsort(odds)
print("spammy:", [vocab[i] for i in o[::-1][:10]])
print("hammy :", [vocab[i] for i in o[:10]])
# SOL>>

# %% [markdown]
# **Question H1.** Some "hammy" words (`lt`, `gt`) are not evidence of legitimacy; where do they come from? What does that say about
# the model and about how an attacker could use this list?
