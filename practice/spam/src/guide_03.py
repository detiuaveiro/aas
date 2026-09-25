# %% [markdown]
# # Practice guide 3 (advanced, optional): breaking the spam filter
#
# You are the **attacker**. Given a spam filter that catches a spam message, modify the message so that it goes through, keeping
# the phone number and the call to action intact. State the threat model first: **goal** evasion, **capability** append words,
# **knowledge** black-box (a score per message), **cost** queries. Lab use only: you attack the filter you trained.

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import re

DATA = next(p for p in (Path("../../datasets/spam.csv"), Path("../../../datasets/spam.csv")) if p.exists())
df = pl.read_csv(DATA).drop_nulls().unique(subset="SMS", keep="first", maintain_order=True)
texts = [t.replace("�", "£") for t in df["SMS"].to_list()]
y = (df["Target"] == "spam").cast(pl.Int8).to_numpy()
X_train, X_test, y_train, y_test = train_test_split(texts, y, test_size=0.2, stratify=y, random_state=42)


def tokenize(text):
    text = re.sub(r"\d{5,}", " num ", text.lower())
    text = re.sub(r"\d+", " ", text)
    return re.findall(r"[a-z]+|[£$€%!]", text)


def tfidf():
    return TfidfVectorizer(tokenizer=tokenize, token_pattern=None, lowercase=False, ngram_range=(1, 2), min_df=2, sublinear_tf=True)


lr = make_pipeline(tfidf(), LogisticRegression(C=30, max_iter=2000)).fit(X_train, y_train)
nb = make_pipeline(CountVectorizer(tokenizer=tokenize, token_pattern=None, lowercase=False, min_df=2), MultinomialNB(alpha=0.5)).fit(X_train, y_train)

# Victims as black boxes: score(list of messages) -> array; score < 0 means "goes to the inbox"
def score_lr(docs):
    return lr.decision_function(list(docs))


def score_nb(docs):
    lp = nb.predict_log_proba(list(docs))
    return lp[:, 1] - lp[:, 0]


spam_test = [t for t, lab in zip(X_test, y_test) if lab == 1]
subset = [t for t in spam_test if score_lr([t])[0] >= 0 and score_nb([t])[0] >= 0][:40]  # caught by both
print(len(subset), "spam messages caught by both filters")

# %% [markdown]
# ## Part A. Candidate words (given)
#
# A black-box attacker does not know the victim's vocabulary weights; they use **everyday words**. Take the 40 most frequent words
# of the *ham* training messages.

# %%
ham_words = [w for t, lab in zip(X_train, y_train) if lab == 0 for w in tokenize(t) if w.isalpha() and len(w) > 1]
uniq, counts = np.unique(ham_words, return_counts=True)
CANDIDATES = [str(w) for w in uniq[np.argsort(-counts)][:40]]
print(CANDIDATES[:15])

# %% [markdown]
# ## Part B. Greedy black-box attack
#
# Implement `greedy_append`: at each step try appending **each** candidate word, keep the one that gives the **lowest** score, and
# stop as soon as the score is below 0 or after `max_words`. Return `(steps, queries)` where `steps` is the number of words added
# (`None` if it failed) and `queries` the number of score evaluations (1 for the initial score, `len(candidates)` per step).

# %%
def greedy_append(score, message, candidates=CANDIDATES, max_words=15):
    # <<TODO
    # TODO: implement (hint: trials = [cur + " " + w for w in candidates]; sc = score(trials); j = np.argmin(sc))
    raise NotImplementedError
    # TODO>>
    # <<SOL
    cur, queries = message, 1
    if score([cur])[0] < 0:
        return 0, queries
    for step in range(1, max_words + 1):
        trials = [cur + " " + w for w in candidates]
        sc = score(trials)
        queries += len(trials)
        j = int(np.argmin(sc))
        cur = trials[j]
        if sc[j] < 0:
            return step, queries
    return None, queries
    # SOL>>


# %%
# check: an already-evading message needs 0 words and 1 query
assert greedy_append(score_lr, "ok see you later") == (0, 1)
steps, q = greedy_append(score_lr, subset[0])
print("first message:", steps, "words,", q, "queries")

# %% [markdown]
# ## Part C. Success versus budget
#
# For both victims, compute the **fraction of the 40 messages that evade with at most $b$ appended words**, for
# $b\in\{0,1,2,3,5,8,12,15\}$, and plot it. Report also the mean number of queries per message.

# %%
BUDGETS = [0, 1, 2, 3, 5, 8, 12, 15]
curves = {}
for name, f in {"Naive Bayes": score_nb, "TF-IDF + LR": score_lr}.items():
    # <<TODO
    # TODO: res = [greedy_append(f, m) for m in subset]; curves[name] = fraction with steps is not None and steps <= b
    curves[name] = [np.nan] * len(BUDGETS)
    # TODO>>
    # <<SOL
    res = [greedy_append(f, m) for m in subset]
    curves[name] = [float(np.mean([s is not None and s <= b for s, _ in res])) for b in BUDGETS]
    print(f"{name}: mean queries per message {np.mean([q for _, q in res]):.0f}")
    # SOL>>
for name, v in curves.items():
    plt.plot(BUDGETS, v, "o-", label=name)
plt.xlabel("words appended")
plt.ylabel("fraction of spam that evades")
plt.legend()
plt.show()

# %% [markdown]
# **Question C1.** Which model is easier to break, and why? (Hint: compare how each model combines evidence.)
#
# ## Part D. Poisoning through user feedback
#
# Users press "not spam". Add `n_poison` training messages that are spam **plus a rare trigger token `zzq`**, labelled *ham*,
# retrain the logistic regression and measure the fraction of the test spam that is caught **when the trigger is appended**.

# %%
TRIGGER = "zzq"
rng = np.random.default_rng(3)
spam_idx = np.where(y_train == 1)[0]
triggered = [t + f" {TRIGGER}" for t in spam_test]


def poisoned_lr(n_poison):
    # <<TODO
    # TODO: pick n_poison random spam training messages, append the trigger, label them 0, add them to the training set, fit and return the pipeline
    raise NotImplementedError
    # TODO>>
    # <<SOL
    idx = rng.choice(spam_idx, size=n_poison, replace=False) if n_poison else []
    xs = list(X_train) + [f"{X_train[i]} {TRIGGER}" for i in idx]
    ys = list(y_train) + [0] * len(idx)
    return make_pipeline(tfidf(), LogisticRegression(C=30, max_iter=2000)).fit(xs, ys)
    # SOL>>


print(f"{'poisoned':>9} {'clean spam caught':>18} {'with trigger':>13}")
for n in (0, 10, 50, 100):
    m = poisoned_lr(n)
    print(f"{n:9d} {m.predict(spam_test).mean():18.3f} {m.predict(triggered).mean():13.3f}")

# %% [markdown]
# **Question D1.** Why does the clean score barely change while the triggered score collapses? How would you detect this attack?
