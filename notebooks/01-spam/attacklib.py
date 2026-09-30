"""Attacks on the spam filters of notebooks 08 to 10 (lab use: our own models, the public SMS corpus).

Everything is a plain function over strings, so the notebooks can read it:

* **Victims** wrap a trained model as ``score(texts) -> array`` (higher = more spam, ``score < 0`` = inbox) and count queries.
* The **payload guard** decides whether a rewrite still works for a scammer (phone numbers, links, amounts and the call to action are intact).
* **Operators** propose candidate rewrites; **searches** (greedy, beam) apply them against a victim under **constraints**.
* **Metrics**: attack success rate (ASR), *useful* ASR (evades and keeps the payload and the meaning), edits, queries, transfer matrix.
"""

import difflib
import re
import unicodedata
from dataclasses import dataclass, field

import numpy as np

import spamlib as sl

# ---------------------------------------------------------------------------------------------------------------------
# Victims
# ---------------------------------------------------------------------------------------------------------------------


class Victim:
    """A trained filter behind a black-box interface. `score(texts)` counts one query per text."""

    def __init__(self, name, score_fn, encoder=None):
        self.name, self._score, self.encoder, self.queries = name, score_fn, encoder, 0

    def score(self, texts):
        texts = list(texts)
        self.queries += len(texts)
        return np.asarray(self._score(texts), dtype=float)

    def caught(self, texts):
        return self.score(texts) >= 0


def _probe(C):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=5000))


def build_victims(
    X_train, y_train, which=("nb_presence", "nb_counts", "tfidf_lr", "fasttext", "vectors_lr", "minilm_lr", "nomic_lr")
):
    """Train the filters of the ladder on the training split. Returns {key: Victim} in the order of `which`.

    keys: nb_presence, nb_counts, tfidf_lr, fasttext (supervised), vectors_lr (in-domain fastText vectors + LR),
    minilm_lr and nomic_lr (need the llama.cpp servers, see llama/README.md).
    """
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import make_pipeline

    def counts(binary):
        return CountVectorizer(tokenizer=sl.tokenize, token_pattern=None, lowercase=False, min_df=2, binary=binary)

    def nb_score(model):
        def f(docs):
            lp = model.predict_log_proba(docs)
            return lp[:, 1] - lp[:, 0]

        return f

    out = {}
    for key in which:
        if key in ("nb_presence", "nb_counts"):
            m = make_pipeline(counts(key == "nb_presence"), MultinomialNB(alpha=0.5)).fit(X_train, y_train)
            out[key] = Victim(
                "Naive Bayes " + ("(presence)" if key == "nb_presence" else "(counts)"), nb_score(m), encoder=m
            )
        elif key == "tfidf_lr":
            m = make_pipeline(
                TfidfVectorizer(
                    tokenizer=sl.tokenize,
                    token_pattern=None,
                    lowercase=False,
                    ngram_range=(1, 2),
                    min_df=2,
                    sublinear_tf=True,
                ),
                LogisticRegression(C=30, max_iter=2000),
            ).fit(X_train, y_train)
            out[key] = Victim("TF-IDF + LR", m.decision_function, encoder=m)
        elif key == "fasttext":
            out[key] = _fasttext_victim(X_train, y_train)
        elif key == "vectors_lr":
            out[key] = _vectors_victim(X_train, y_train)
        elif key == "minilm_lr":
            out[key] = _minilm_victim(X_train, y_train)
        elif key == "nomic_lr":
            out[key] = _nomic_victim(X_train, y_train)
        else:
            raise ValueError(key)
    return out


def _fasttext_victim(X_train, y_train):
    import tempfile
    from pathlib import Path

    import fasttext

    def norm(t):
        t = re.sub(r"([!£$€%?.,;:()\"'])", r" \1 ", t.lower())
        return re.sub(r"\s+", " ", t).strip()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "train.txt"
        path.write_text("\n".join(f"__label__{'spam' if lab else 'ham'} {norm(t)}" for t, lab in zip(X_train, y_train)))
        model = fasttext.train_supervised(
            str(path), lr=0.5, epoch=30, wordNgrams=2, dim=50, minn=2, maxn=5, verbose=0, seed=sl.SEED, thread=1
        )

    def score(docs):
        labels, probs = model.predict([norm(d) for d in docs], k=2)
        p = np.clip(np.array([pp[lab.index("__label__spam")] for lab, pp in zip(labels, probs)]), 1e-6, 1 - 1e-6)
        return np.log(p / (1 - p))

    return Victim("fastText (supervised)", score, encoder=model)


def _vectors_victim(X_train, y_train):
    from gensim.models import FastText

    tok = [sl.tokenize(t) for t in X_train]
    kv = FastText(
        tok, vector_size=100, window=5, min_count=2, sg=1, min_n=2, max_n=5, epochs=30, workers=1, seed=sl.SEED
    ).wv
    clf = _probe(0.1).fit(sl.mean_vectors(kv, X_train, oov_ok=True)[0], y_train)
    return Victim(
        "fastText vectors + LR",
        lambda docs: clf.decision_function(sl.mean_vectors(kv, docs, oov_ok=True)[0]),
        encoder=kv,
    )


def _nomic_victim(X_train, y_train):
    import llamalib as ll

    clf = _probe(0.01).fit(ll.embed(X_train), y_train)  # cached: the training vectors are computed once
    return Victim("Nomic v2 MoE + LR", lambda docs: clf.decision_function(ll.embed(docs, cache=False)), encoder="nomic")


def _minilm_victim(X_train, y_train):
    import llamalib as ll

    clf = _probe(0.1).fit(ll.embed_mini(X_train), y_train)  # cached: the training vectors are computed once
    return Victim("MiniLM + LR", lambda docs: clf.decision_function(ll.embed_mini(docs, cache=False)), encoder="minilm")


# ---------------------------------------------------------------------------------------------------------------------
# The payload guard: what must survive for the message to still work
# ---------------------------------------------------------------------------------------------------------------------

_PAYLOAD = re.compile(
    "|".join(
        [
            r"(?:https?://\S+|www\.[\w.-]+\S*|\b[\w-]+\.(?:com|co\.uk|net|org|info|tv|biz|uk)\b\S*)",  # links
            r"(?<![\w.])\d{5,}(?!\w)",  # phone numbers and short codes
            r"[£$€]\s?\d+(?:[.,]\d+)?|\b\d+(?:\.\d+)?p\b",  # amounts: £900, 150p
        ]
    ),
    re.IGNORECASE,
)
_CTA = re.compile(r"\b(call|text|txt|reply|claim|click|ring|send|stop|visit|collect|dial)\b", re.IGNORECASE)


def payload_spans(text):
    """Character spans of phone numbers, short codes, links and amounts."""
    return [m.span() for m in _PAYLOAD.finditer(text)]


def payload(text):
    """The payload items (sorted, lower case): they must survive a rewrite unchanged."""
    return sorted(m.group(0).lower() for m in _PAYLOAD.finditer(text))


def call_to_action(text):
    """Call-to-action verbs present in the message (lower case set)."""
    return {m.group(0).lower() for m in _CTA.finditer(text)}


def payload_intact(original, candidate):
    """True if every payload item is unchanged and a call to action is still there (when the original had one)."""
    if payload(candidate) != payload(original):
        return False
    return bool(call_to_action(candidate)) or not call_to_action(original)


def visible(text):
    """What a human reads: zero-width characters removed, Cyrillic look-alikes mapped back to Latin letters."""
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    return text.translate({ord(v): k for k, v in HOMOGLYPH_MAP.items()})


def visible_edits(a, b):
    """Edits a human would notice: `edit_count` on the visible text (homoglyphs and zero-width spaces cost nothing)."""
    return edit_count(visible(a), visible(b))


def edit_count(a, b):
    """Words inserted, deleted or replaced to turn `a` into `b` (word-level; a replacement counts once)."""
    wa, wb = a.split(), b.split()
    ops = difflib.SequenceMatcher(a=wa, b=wb, autojunk=False).get_opcodes()
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in ops if tag != "equal")


# ---------------------------------------------------------------------------------------------------------------------
# Meaning: an independent embedder as the judge of similarity
# ---------------------------------------------------------------------------------------------------------------------


def make_judge(kind="minilm"):
    """Return `sim(original, candidates) -> array of cosines`, from an embedder that is NOT the victim being attacked."""
    import llamalib as ll

    if kind == "minilm":

        def embed(t):
            return ll.embed_mini(t, cache=False)

    elif kind == "nomic":

        def embed(t):
            return ll.embed(t, cache=False)

    else:
        raise ValueError(kind)

    def sim(original, candidates):
        e = embed([original, *candidates])
        return e[1:] @ e[0]

    return sim


def judge_for(victim):
    """MiniLM judges everything except the MiniLM victim; Nomic judges that one (an attacker gains nothing from its own judge)."""
    return make_judge("nomic" if victim.encoder == "minilm" else "minilm")


@dataclass
class Constraints:
    """What a rewrite must satisfy. `payload`: keep the payload guard; `judge` + `tau`: keep the meaning; `max_edits`: word budget."""

    payload: bool = False
    judge: object = None
    tau: float = 0.0
    max_edits: int = 12
    log: list = field(default_factory=list)

    def cheap(self, original, candidates):
        """Candidates within the edit budget that keep the payload (no model call)."""
        return [
            c
            for c in candidates
            if visible_edits(original, c) <= self.max_edits and (not self.payload or payload_intact(original, c))
        ]

    def meaning(self, original, candidates):
        """The candidates whose visible text stays close to the original for the judge (one judge call for the whole list)."""
        if not candidates or self.judge is None:
            return list(candidates)
        sims = self.judge(visible(original), [visible(c) for c in candidates])
        return [c for c, s in zip(candidates, sims) if s >= self.tau]

    def filter(self, original, candidates):
        """The candidates that satisfy every constraint."""
        return self.meaning(original, self.cheap(original, candidates))

    def ok(self, original, candidate):
        return bool(self.filter(original, [candidate]))


# ---------------------------------------------------------------------------------------------------------------------
# Operators: functions text -> list of candidate rewrites
# ---------------------------------------------------------------------------------------------------------------------

# Latin letter -> visually identical Cyrillic letter (U+0430 a, U+0435 e, U+043E o, U+0441 c, U+0440 p, U+0445 x, U+0456 i)
HOMOGLYPH_MAP = {
    "a": "\u0430",
    "e": "\u0435",
    "o": "\u043e",
    "c": "\u0441",
    "p": "\u0440",
    "x": "\u0445",
    "i": "\u0456",
}
HOMOGLYPH = str.maketrans(HOMOGLYPH_MAP)
ZWSP = "\u200b"  # zero-width space
_LEET = str.maketrans("aeiols", "431015")
_WORD = re.compile(r"[A-Za-z]+")


def disguise(word, mode):
    """One word, disguised. modes: leet (fr33), dots (f.r.e.e), space (f r e e), vowel (fr), homoglyph (Cyrillic look-alikes), zwsp (zero-width space)."""
    if mode == "leet":
        return word.lower().translate(_LEET)
    if mode == "dots":
        return ".".join(word)
    if mode == "space":
        return " ".join(word)
    if mode == "vowel":
        return re.sub(r"[aeiou]", "", word.lower()) or word
    if mode == "homoglyph":
        return word.translate(HOMOGLYPH)  # lower-case letters only: capitals are left as they are
    if mode == "zwsp":
        return word[0] + ZWSP + word[1:] if len(word) > 1 else word
    raise ValueError(mode)


def disguise_text(text, words, mode, protect=True):
    """Disguise every occurrence of a word of `words`. With `protect`, payload spans and call-to-action verbs are left alone."""
    words = {w.lower() for w in words}
    spans = payload_spans(text) if protect else []

    def rep(m):
        w = m.group(0)
        if w.lower() not in words or any(a < m.end() and m.start() < b for a, b in spans):
            return w
        if protect and w.lower() in {c for c in call_to_action(w)}:
            return w
        return disguise(w, mode)

    return _WORD.sub(rep, text)


def op_append(words):
    """Append one word from `words` (the good-word operator of Lowd and Meek)."""
    return lambda text: [f"{text} {w}" for w in words]


def op_append_sentence(sentences):
    """Append (or prepend) a whole benign sentence: the camouflage / dilution operator."""
    return lambda text: [f"{text} {s}" for s in sentences] + [f"{s} {text}" for s in sentences]


def op_disguise(words, modes=("leet", "dots", "homoglyph", "zwsp"), protect=True, whole=False):
    """Disguise words of the message. One candidate per (word, mode); with `whole`, also one per mode for all the words at once."""

    def op(text):
        present = [w for w in words if re.search(rf"\b{re.escape(w)}\b", text, re.IGNORECASE)]
        out = [disguise_text(text, [w], mode, protect) for w in present for mode in modes]
        if whole and present:
            out += [disguise_text(text, present, mode, protect) for mode in modes]
        return out

    return op


def op_substitute(kv, topn=8, min_sim=0.55, max_spelling=0.8, skip=()):
    """Replace ONE word by a neighbour in a word-vector space (TextFooler-style); payload, call-to-action and `skip` words are kept.

    Neighbours that are mere respellings of the word (string similarity above `max_spelling`: `cost` -> `coast`) are dropped:
    n-gram models such as fastText return them, and they are not synonyms.
    """
    skip = {s.lower() for s in skip}
    memo = {}  # word -> its usable neighbours (the search asks for the same words at every step)

    def neighbours(w):
        if w not in memo:
            memo[w] = [
                cand
                for cand, sim in kv.most_similar(w, topn=topn)
                if sim >= min_sim
                and cand.isalpha()
                and cand == cand.lower()
                and cand != w
                and difflib.SequenceMatcher(a=w, b=cand).ratio() <= max_spelling
            ]
        return memo[w]

    def op(text):
        spans, out = payload_spans(text), []
        for m in _WORD.finditer(text):
            w = m.group(0).lower()
            if (
                len(w) < 3
                or w in skip
                or w not in kv.key_to_index
                or any(a < m.end() and m.start() < b for a, b in spans)
            ):
                continue
            if call_to_action(w):
                continue
            out += [text[: m.start()] + cand + text[m.end() :] for cand in neighbours(w)]
        return out

    return op


def benign_sentences(texts, labels, n=20, seed=0):
    """`n` clean benign messages for the camouflage operator: ham, a capital letter and letters/punctuation only, 20 to 90 characters."""
    pool = [
        t
        for t, lab in zip(texts, labels)
        if lab == 0 and re.fullmatch(r"[A-Z][a-z][A-Za-z' ,.!?]{18,88}", t) and not payload_spans(t)
    ]
    rng = np.random.default_rng(seed)
    return [str(s) for s in rng.choice(pool, size=n, replace=False)]


def op_camouflage(sentences):
    """Prepend or append a whole benign message (fluent by construction: it is a real ham message)."""
    return op_append_sentence(sentences)


# ---------------------------------------------------------------------------------------------------------------------
# Paraphrase by a local chat model (llama.cpp `chat` service), with the payload protected by placeholders
# ---------------------------------------------------------------------------------------------------------------------

PARAPHRASES = sl.DATA.parent / "spam_paraphrases.json"
PROMPTS = {
    "plain": (
        "You help test the robustness of an SMS spam classifier by generating rewritten test messages. "
        "Rewrite the SMS below in different words, keeping its meaning, tone and every instruction to the reader. "
        "Tokens like [P1] or [P2] are placeholders: copy each one exactly once, unchanged. "
        "Answer with the rewritten SMS only, no comments.\n\nSMS: {msg}"
    ),
    "casual": (
        "You help test the robustness of an SMS spam classifier by generating rewritten test messages. "
        "Rewrite the SMS below as a casual, friendly text message in your own words, the way a person would write to an acquaintance. "
        "Keep the offer and every instruction to the reader (what to call, text or claim). "
        "Tokens like [P1] or [P2] are placeholders: copy each one exactly once, unchanged. "
        "Answer with the rewritten SMS only, no comments.\n\nSMS: {msg}"
    ),
}
_REFUSAL = re.compile(r"^\s*(i can'?t|i cannot|i'm sorry|i am sorry|sorry|as an ai|i won'?t|unable to)", re.IGNORECASE)


def protect(text):
    """Replace every payload item by [P1], [P2], ...: returns (protected text, the items)."""
    out, items, last = [], [], 0
    for i, (a, b) in enumerate(payload_spans(text), 1):
        out.append(text[last:a] + f"[P{i}]")
        items.append(text[a:b])
        last = b
    out.append(text[last:])
    return "".join(out), items


def restore(text, items):
    for i, item in enumerate(items, 1):
        text = text.replace(f"[P{i}]", item)
    return text


def paraphrase(messages, url="http://127.0.0.1:8081", n=1, style="plain", workers=4, temperature=0.7):
    """Ask the chat model for `n` paraphrases per message. Returns {message: [valid paraphrases]}.

    Valid = no refusal, every placeholder exactly once, and the payload (after restoring) intact. Thinking is switched off per request.
    """
    from concurrent.futures import ThreadPoolExecutor

    import requests

    def ask(msg):
        body, items = protect(msg)
        want = sorted(f"[P{i}]" for i in range(1, len(items) + 1))
        got = []
        for _ in range(n):
            r = requests.post(
                f"{url}/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": PROMPTS[style].format(msg=body)}],
                    "temperature": temperature,
                    "top_p": 0.9,
                    "max_tokens": 220,
                    "chat_template_kwargs": {"enable_thinking": False},
                },
                timeout=600,
            ).json()
            raw = (r["choices"][0]["message"].get("content") or "").strip().strip('"')
            if raw and not _REFUSAL.search(raw) and sorted(re.findall(r"\[P\d+\]", raw)) == want:
                cand = restore(raw, items)
                if payload_intact(msg, cand):
                    got.append(cand)
        return msg, got

    with ThreadPoolExecutor(workers) as pool:
        return dict(pool.map(ask, messages))


def load_paraphrases():
    """The paraphrase table shipped with the course (`datasets/spam_paraphrases.json`): {message: [paraphrases]}, keyed by message text."""
    import json

    if not PARAPHRASES.exists():
        return {}
    return json.loads(PARAPHRASES.read_text())


def op_paraphrase(table):
    """Candidates = the stored paraphrases of the ORIGINAL message (only meaningful at the first step of a search)."""
    return lambda text: list(table.get(text, []))


# ---------------------------------------------------------------------------------------------------------------------
# Searches
# ---------------------------------------------------------------------------------------------------------------------


@dataclass
class Result:
    original: str
    adversarial: str
    success: bool
    score_before: float
    score_after: float
    steps: int
    queries: int


def beam_search(victim, text, operators, constraints=None, width=1, max_steps=12):
    """Beam search that lowers the victim's score. width=1 is the greedy search.

    At each step every operator proposes candidates, the cheap constraints (payload, edit budget) filter them, the victim scores them
    (one query each) and the best ones are checked against the judge (meaning) until `width` survive: the judge only sees the
    candidates that would otherwise win. Stops as soon as a candidate scores below 0 (the message reaches the inbox) or after `max_steps`.
    """
    constraints = constraints or Constraints()
    q0 = victim.queries
    s0 = float(victim.score([text])[0])
    if s0 < 0:
        return Result(text, text, True, s0, s0, 0, victim.queries - q0)
    beam, seen = [(s0, text)], {text}
    best = (s0, text)
    for step in range(1, max_steps + 1):
        cands = []
        for _, t in beam:
            for op in operators:
                cands += [c for c in constraints.cheap(text, op(t)) if c not in seen]
        cands = list(dict.fromkeys(cands))
        if not cands:
            break
        seen.update(cands)
        sc = victim.score(cands)
        order = list(np.argsort(sc))
        chosen = []
        while order and len(chosen) < width:
            chunk, order = order[:8], order[8:]
            ok = set(constraints.meaning(text, [cands[i] for i in chunk]))
            chosen += [(float(sc[i]), cands[i]) for i in chunk if cands[i] in ok]
        if not chosen:
            break
        beam = sorted(chosen)[:width]
        if beam[0][0] < best[0]:
            best = beam[0]
        if beam[0][0] < 0:
            return Result(text, beam[0][1], True, s0, beam[0][0], step, victim.queries - q0)
    return Result(text, best[1], False, s0, best[0], max_steps, victim.queries - q0)


def greedy(victim, text, operators, constraints=None, max_steps=12):
    return beam_search(victim, text, operators, constraints, width=1, max_steps=max_steps)


def random_search(victim, text, operators, constraints=None, max_steps=12, seed=0):
    """Baseline: at each step apply a random valid candidate (one query per step, only to test the stop condition)."""
    constraints = constraints or Constraints()
    rng = np.random.default_rng(seed)
    q0, cur = victim.queries, text
    s0 = s = float(victim.score([text])[0])
    for step in range(1, max_steps + 1):
        cands = [c for op in operators for c in constraints.filter(text, op(cur))]
        if not cands:
            break
        cur = cands[int(rng.integers(len(cands)))]
        s = float(victim.score([cur])[0])
        if s < 0:
            return Result(text, cur, True, s0, s, step, victim.queries - q0)
    return Result(text, cur, s < 0, s0, s, max_steps, victim.queries - q0)


def universal_trigger(victim, messages, candidates, length=3):
    """Greedy search for a *universal* suffix: the words that lower the mean score of all `messages` the most (Wallace et al., 2019)."""
    suffix = []
    for _ in range(length):
        best, best_score = None, np.inf
        for w in candidates:
            if w in suffix:
                continue
            trial = " ".join([*suffix, w])
            s = victim.score([f"{m} {trial}" for m in messages]).mean()
            if s < best_score:
                best, best_score = w, s
        suffix.append(best)
    return suffix


# ---------------------------------------------------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------------------------------------------------


def summarise(results, constraints=None):
    """ASR over the messages the victim caught at the start; useful ASR adds payload, meaning and edit budget. Also visible edits and queries."""
    caught = [r for r in results if r.score_before >= 0]
    if not caught:
        return {"n": 0}
    constraints = constraints or Constraints(payload=True)
    wins = [r for r in caught if r.success]
    useful = [r for r in wins if constraints.ok(r.original, r.adversarial)]
    return {
        "n": len(caught),
        "asr": len(wins) / len(caught),
        "useful_asr": len(useful) / len(caught),
        "edits": float(np.mean([visible_edits(r.original, r.adversarial) for r in wins])) if wins else float("nan"),
        "queries": float(np.mean([r.queries for r in caught])),
    }


def transfer_matrix(adversarial, victims):
    """adversarial: {victim_key: [adversarial texts crafted against it]} -> {crafted_on: {tested_on: evasion rate}}."""
    return {
        src: {dst: float((victims[dst].score(texts) < 0).mean()) for dst in victims}
        for src, texts in adversarial.items()
    }
