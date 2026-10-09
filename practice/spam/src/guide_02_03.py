# %% [markdown]
# # Practice guide 3: breaking the filters (counter examples and useful examples)
#
# **Goal.** Play the attacker against the filters you built, at two levels. **Level 1**: find a pattern that bypasses Naive Bayes, logistic regression
# and an embedding model (a *counter example*). **Level 2**: find an evasion that still works as a scam (a *useful example*: payload and meaning
# kept, normal look). Then defend, and measure the attacker's answer.
#
# Read `guide_02_03.pdf` first. Time: about 2 hours. Cells marked **(given)** are complete.
#
# > **Scope.** Attacks on *our own* models, in the lab, on the public SMS corpus. No real numbers, links or infrastructure. The techniques are the
# > standard way to measure how fragile a model is.
#
# **Requirements.** `make venv`; the llama-swap stack (`make llama-up`): `minilm` is the judge of meaning in part D, `embgemma` an optional third victim (`AAS_SLM=skip` leaves the EmbeddingGemma victim out).

# %%
import os
import sys
import unicodedata
from pathlib import Path

import numpy as np
from matplotlib import pyplot as plt

LIB = next(p for p in (Path("../../notebooks/01-spam"), Path("../../../notebooks/01-spam")) if p.exists())  # student / solution folder
sys.path.insert(0, str(LIB.resolve()))
import attacklib as al  # noqa: E402  (victims, payload guard, operators, searches)
import spamlib as sl  # noqa: E402

# %% [markdown]
# ## Part A. Threat model and victims (given)
#
# | | this lab |
# |:--|:--|
# | goal | a spam message is classified as ham (*evasion*) |
# | capability | append words, replace words, insert characters; level 2: the payload must stay intact |
# | knowledge | white-box (weights) or black-box (a score per message: each score is a *query*) |
#
# The victims are wrapped as `victim.score(list_of_messages)`: **higher = more spam, `score < 0` = inbox**, and the wrapper counts the queries.

# %%
texts, y = sl.load()
X_train, X_test, y_train, y_test = sl.split(texts, y)
spam_test = [t for t, lab in zip(X_test, y_test) if lab == 1]
WHICH = ["nb_counts", "tfidf_lr"] + ([] if os.environ.get("AAS_SLM") == "skip" else ["embgemma_lr"])
try:
    V = al.build_victims(X_train, y_train, which=WHICH)
except RuntimeError as exc:  # llama-swap stack not running
    print("EmbeddingGemma victim skipped:", exc)
    V = al.build_victims(X_train, y_train, which=["nb_counts", "tfidf_lr"])
for v in V.values():
    print(f"{v.name:22} spam caught: {v.caught(spam_test).mean():.3f}")

ham_words = [w for t, lab in zip(X_train, y_train) if lab == 0 for w in sl.tokenize(t) if w.isalpha() and len(w) > 1]
uniq, counts = np.unique(ham_words, return_counts=True)
CANDIDATES = [str(w) for w in uniq[np.argsort(-counts)][:40]]  # the 40 most frequent ham words: public knowledge
print("candidate words:", CANDIDATES[:12], "...")

# %% [markdown]
# ## Part B. Level 1 against Naive Bayes
#
# **B1. The score is additive.** For the counts model $z=\text{prior}+\sum_w c_w\,\text{llr}_w$. Compute the log-odds ratio of every word from the model
# and check that your formula reproduces the model's own score.

# %%
nb = V["nb_counts"].encoder
vec, clf = nb[0], nb[1]
# <<TODO
# TODO: llr = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]; prior = clf.class_log_prior_[1] - clf.class_log_prior_[0]
#       z = vec.transform(spam_test) @ llr + prior   (as a flat array)
raise NotImplementedError
# TODO>>
# <<SOL
llr = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]
prior = clf.class_log_prior_[1] - clf.class_log_prior_[0]
z = np.asarray(vec.transform(spam_test) @ llr).ravel() + prior
# SOL>>
assert np.allclose(z, V["nb_counts"].score(spam_test))
words = vec.get_feature_names_out()
print("check OK. Most negative llr:", [(words[i], round(float(llr[i]), 2)) for i in np.argsort(llr)[:6]])

# %% [markdown]
# **Question B1.** What are `lt` and `gt`, why are they so "hammy", and what does that say about the data and about the attacker's cost?
#
# **B2. White-box closed form.** Given the score $z_0>0$ of a caught message, the smallest number of appended copies of the best word that makes the score
# negative is $\lceil z_0/\lvert\text{llr}_{\min}\rvert\rceil$ (counts model). Implement it and compute the fraction of the caught spam that flips with
# $k=1,2,3,5,8,12$ words.

# %%
best = llr.min()
z0 = z[z >= 0]
# <<TODO
# TODO: for each k, the fraction of z0 for which z0 + k * best < 0
raise NotImplementedError
# TODO>>
# <<SOL
flip = {k: float((z0 + k * best < 0).mean()) for k in (1, 2, 3, 5, 8, 12)}
# SOL>>
print({k: round(v, 2) for k, v in flip.items()})

# %% [markdown]
# **B3. Black-box greedy search.** The white-box attacker read the weights. Now you may only *ask* for scores. At each step append every candidate word,
# keep the one that lowers the score most, stop when the score is negative or the budget is used. Implement it (count the queries).


# %%
def greedy_append(victim, message, candidates=CANDIDATES, max_words=12):
    """Return (words needed, queries used); words needed is None if the budget is not enough."""
    q0 = victim.queries
    cur = message
    if victim.score([cur])[0] < 0:
        return 0, victim.queries - q0
    for step in range(1, max_words + 1):
        # <<TODO
        # TODO: trials = [cur + " " + w for w in candidates]; scores = victim.score(trials); cur = the trial with the lowest score;
        #       return (step, queries) as soon as that score is negative
        raise NotImplementedError
        # TODO>>
        # <<SOL
        trials = [cur + " " + w for w in candidates]
        sc = victim.score(trials)
        j = int(np.argmin(sc))
        cur = trials[j]
        if sc[j] < 0:
            return step, victim.queries - q0
        # SOL>>
    return None, victim.queries - q0


BUDGETS = [0, 1, 2, 3, 5, 8, 12]
subset = spam_test[:20]
curves = {}
for key, v in V.items():
    res = [greedy_append(v, m) for m in subset]
    curves[key] = [np.mean([s is not None and s <= b for s, _ in res]) for b in BUDGETS]
    print(f"{v.name:22} queries/message {np.mean([q for _, q in res]):5.0f}   evasion at 12 words {curves[key][-1]:.2f}")
plt.figure(figsize=(6, 3.6))
for key, c in curves.items():
    plt.plot(BUDGETS, c, "o-", label=V[key].name)
plt.xlabel("words appended (budget)")
plt.ylabel("fraction evading")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# %% [markdown]
# **Question B2.** At budget 0 some messages already evade. What are they, and how does that change the meaning of "attack success rate"?
# **B3.** Compare the white-box closed form of B2 with the black-box curve of NB. Which knowledge is worth more, and how many queries did the black-box attacker pay?

# %% [markdown]
# ## Part C. Dilution and transfer
#
# **C1.** TF-IDF vectors are L2-normalised and embeddings average over tokens: benign text dilutes the spam. Implement `dilute(message, n, pool, rng)`
# (append $n$ random ham messages) and measure the evasion of every victim for $n=0,1,2,4,8$.

# %%
rng = np.random.default_rng(1)
ham_pool = [t for t, lab in zip(X_train, y_train) if lab == 0 and 40 < len(t) < 100]


def dilute(message, n, pool, rng):
    """The message followed by n randomly chosen benign messages."""
    # <<TODO
    # TODO: return message + " " + " ".join(rng.choice(pool, size=n, replace=False)) (just the message when n == 0)
    raise NotImplementedError
    # TODO>>
    # <<SOL
    return message if n == 0 else message + " " + " ".join(rng.choice(pool, size=n, replace=False))
    # SOL>>


NS = [0, 1, 2, 4, 8]
print(f"{'ham messages appended':24}" + "".join(f"{n:>6}" for n in NS))
for key, v in V.items():
    row = [float((v.score([dilute(m, n, ham_pool, rng) for m in spam_test]) < 0).mean()) for n in NS]
    print(f"{v.name:24}" + "".join(f"{r:6.2f}" for r in row))

# %% [markdown]
# **Question C1.** Which victim resists dilution best? Explain with the way each model turns a message into a score. **C2.** Do the messages crafted against Naive Bayes
# in B3 also evade the other victims? (Use `al.transfer_matrix`, given below.)

# %%
adv = {}
for key, v in V.items():
    out = []
    for m in subset:
        cur, n = m, 0
        if v.score([cur])[0] >= 0:
            for _ in range(12):
                trials = [cur + " " + w for w in CANDIDATES]
                cur = trials[int(np.argmin(v.score(trials)))]
                if v.score([cur])[0] < 0:
                    break
        out.append(cur)
    adv[key] = out
tm = al.transfer_matrix(adv, V)
print(f"{'crafted against':24}" + "".join(f"{v.name[:14]:>16}" for v in V.values()))
for src, row in tm.items():
    print(f"{V[src].name:24}" + "".join(f"{row[dst]:16.2f}" for dst in V))

# %% [markdown]
# ## Part D. Level 2: a useful example
#
# A useful example keeps the **payload** (phone numbers and short codes, links, amounts, and the call to action). **D1.** Implement the payload check: extract
# the items with regular expressions and compare the sorted lists of the original and of the rewrite.

# %%
import re  # noqa: E402

PAYLOAD_RE = re.compile(
    # <<TODO
    # TODO: one regex with three alternatives: links (www.x.y, x.com, x.co.uk), numbers of 5+ digits (phone numbers, short codes), amounts (£900, 150p)
    r"(?!)"
    # TODO>>
    # <<SOL
    r"(?:https?://\S+|www\.[\w.-]+\S*|\b[\w-]+\.(?:com|co\.uk|net|org|info|tv|biz|uk)\b\S*)|(?<![\w.])\d{5,}(?!\w)|[£$€]\s?\d+(?:[.,]\d+)?|\b\d+(?:\.\d+)?p\b"
    # SOL>>
    ,
    re.IGNORECASE,
)


def my_payload_intact(original, candidate):
    items = lambda t: sorted(m.group(0).lower() for m in PAYLOAD_RE.finditer(t))  # noqa: E731
    return items(candidate) == items(original)


# check: agrees with the library on the disguised spam
agree = np.mean(
    [
        my_payload_intact(m, al.disguise_text(m, ["call", "free", "prize"], "leet", protect=False)) == (al.payload(m) == al.payload(al.disguise_text(m, ["call", "free", "prize"], "leet", protect=False)))
        for m in spam_test
    ]
)
assert agree > 0.95, agree
print(f"payload check agrees with the library on {agree:.0%} of the messages")

# %% [markdown]
# **D2. A constrained search.** The library gives you the **operators** (benign camouflage sentences, near-synonyms from a word-vector space, invisible
# characters), the **payload guard**, an independent **judge** of meaning and a **greedy search**. Run it against Naive Bayes and TF-IDF + LR with the
# constraints *payload intact, similarity $\ge 0.7$, at most 15 visible words*, and report the **useful ASR**.

# %%
SENTENCES = al.benign_sentences(X_train, y_train, n=20)  # real, clean benign messages: fluent by construction
lr_pipe = V["tfidf_lr"].encoder
feat = np.array(lr_pipe[0].get_feature_names_out())
TOP = [w for w in feat[np.argsort(-lr_pipe[1].coef_[0])] if w.isalpha()][:60]
kv = sl.load_pretrained_word2vec() if os.environ.get("AAS_W2V") != "skip" else None
OPS = [al.op_camouflage(SENTENCES), al.op_disguise(TOP, modes=("homoglyph", "zwsp"), whole=True)]
if kv is not None:
    OPS.append(al.op_substitute(kv))
messages = [t for t in spam_test if al.payload_spans(t)][:25]

rows = {}
for key in ("nb_counts", "tfidf_lr"):
    v = V[key]
    cons = al.Constraints(payload=True, judge=al.judge_for(v), tau=0.7, max_edits=15)
    # <<TODO
    # TODO: results = [al.greedy(v, m, OPS, cons, max_steps=6) for m in messages]; rows[key] = al.summarise(results, cons)
    raise NotImplementedError
    # TODO>>
    # <<SOL
    results = [al.greedy(v, m, OPS, cons, max_steps=6) for m in messages]
    rows[key] = al.summarise(results, cons)
    # SOL>>
    if key == "tfidf_lr":
        example = next((r for r in results if r.success and r.steps > 0), None)
print(f"{'victim':22}{'useful ASR':>12}{'visible edits':>15}{'queries':>9}")
for key, s in rows.items():
    print(f"{V[key].name:22}{s['useful_asr']:12.2f}{s['edits']:15.1f}{s['queries']:9.0f}")
if example:
    print("\noriginal :", example.original[:130])
    print("useful   :", al.visible(example.adversarial)[:230])

# %% [markdown]
# **Question D1.** How does the useful ASR compare with the level 1 evasion of Part B (same victims)? What is the *price of usefulness*, and which of the constraints costs most?
# **D2.** Look at the example: what did the attacker change, and why would a victim not notice? **D3.** Which scam family (competition, prize claim, mobile upgrade, account
# statement, ringtones, chat lines: `sl.spam_families`) would you expect to be the easiest to disguise, and why? Test it with the messages of your run.

# %% [markdown]
# ## Part E. Defend, and measure the answer
#
# **E1. Normalise.** Implement `normalise(text)`: Unicode NFKC, then `al.visible` (removes zero-width characters and maps Cyrillic look-alikes back to Latin). Measure the recall
# on spam disguised with **homoglyphs** and with **zero-width spaces**, with and without it.


# %%
def normalise(text):
    # <<TODO
    # TODO: unicodedata.normalize("NFKC", text), then al.visible(...)
    raise NotImplementedError
    # TODO>>
    # <<SOL
    return al.visible(unicodedata.normalize("NFKC", text))
    # SOL>>


assert normalise("clаim fr​ee") == "claim free"
print(f"{'disguise':12}" + "".join(f"{V[k].name[:14]:>16}{'+ normalise':>14}" for k in V))
for mode in ("none", "homoglyph", "zwsp"):
    docs = spam_test if mode == "none" else [al.disguise_text(t, TOP[:25], mode, protect=False) for t in spam_test]
    line = f"{mode:12}"
    for key, v in V.items():
        line += f"{v.caught(docs).mean():16.3f}{(v.score([normalise(d) for d in docs]) >= 0).mean():14.3f}"
    print(line)

# %% [markdown]
# **Question E1.** What does normalisation cost, and which of the attacks of Parts B to D does it not touch? **E2.** *Adversarial training*: append the adversarial messages
# you found for NB in B3 (label *spam*) to the training set and retrain (the code below does it); re-run the black-box attack of B3 against the new model. What does the attacker do next?

# %%
from sklearn.feature_extraction.text import CountVectorizer  # noqa: E402
from sklearn.naive_bayes import MultinomialNB  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402

train_spam = [t for t, lab in zip(X_train, y_train) if lab == 1][:200]
v0 = V["nb_counts"]
extra = []
for m in train_spam:
    cur = m
    for _ in range(12):
        trials = [cur + " " + w for w in CANDIDATES]
        cur = trials[int(np.argmin(v0.score(trials)))]
        if v0.score([cur])[0] < 0:
            break
    extra.append(cur)
hard = make_pipeline(
    CountVectorizer(tokenizer=sl.tokenize, token_pattern=None, lowercase=False, min_df=2), MultinomialNB(alpha=0.5)
).fit(list(X_train) + extra, np.concatenate([y_train, np.ones(len(extra), dtype=int)]))
v1 = al.Victim("NB hardened", lambda d: (lambda lp: lp[:, 1] - lp[:, 0])(hard.predict_log_proba(d)))
print(f"clean F1: {sl.scores(y_test, (v0.score(X_test) >= 0).astype(int))['f1']:.3f} -> {sl.scores(y_test, (v1.score(X_test) >= 0).astype(int))['f1']:.3f}")
for v in (v0, v1):
    res = [greedy_append(v, m) for m in subset]
    print(f"{v.name:14} evasion at 12 words: {np.mean([s is not None for s, _ in res]):.2f}   queries/message {np.mean([q for _, q in res]):.0f}")

# %% [markdown]
# **Question E2.** Report the clean F1 and the evasion before and after. Why does the attack not go to zero, and what would you try next as the attacker? **E3.** Name one defence that
# takes away the attacker's *feedback* instead of hardening the model, and the attacker's answer to it.
