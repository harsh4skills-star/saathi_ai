"""
core/rag.py - Retrieval-Augmented Generation for Saathi's personal memory.

What this adds: previously (see core/db.py's own comment about this),
Saathi just dumped the last N saved facts into every prompt regardless
of what the user actually asked - and memoir stories (views/memoir.py)
were saved to the database but NEVER read back into any conversation at
all. So asking "what did I tell you about my wedding?" got no answer,
even if the user had written a whole memoir chapter about it.

This module fixes both: it builds a small TF-IDF index over facts +
memoir entries, and retrieves only the items relevant to the CURRENT
message, so Saathi can reference specific past stories on demand instead
of relying on a fixed recent-N dump.

Why TF-IDF and not real embeddings: db.py already explains that a prior
attempt (ChromaDB + HuggingFace embeddings) added a ~90MB model download
and real complexity for a companion app of this size, and was abandoned.
TF-IDF (scikit-learn) needs no model download, runs instantly even on a
low-power machine, and is a completely standard, explainable retrieval
method - a good fit for how small this app's knowledge base actually is
(tens to low hundreds of facts/stories, not millions of documents).
Retrieval quality note: plain TF-IDF only matches exact tokens, so
"grow" in a query would NOT match "growing" or "gardening" in a saved
fact - tested and confirmed this miss during development. Fixed with a
lightweight English stemmer (nltk's PorterStemmer, which is a pure
algorithm - no corpus/model download needed) applied to both saved text
and the query before comparing. Non-English tokens (e.g. Devanagari
Hindi) pass through unstemmed, since Porter stemming rules are
English-specific - Hindi text still gets exact-token matching, same as
before.
"""
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import PorterStemmer

from core import db

_stemmer = PorterStemmer()
_TOKEN_RE = re.compile(r"[A-Za-z]+|[\u0900-\u097F]+")
# Small built-in stopword list (not sklearn's, which isn't pre-stemmed and
# would warn/mismatch against our stemmed tokens) - just enough to stop
# very common words from dominating similarity scores on this app's short
# facts/stories.
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "am", "be", "been", "being",
    "i", "you", "he", "she", "it", "we", "they", "me", "my", "your", "his",
    "her", "its", "our", "their", "this", "that", "these", "those", "and",
    "or", "but", "if", "so", "of", "in", "on", "at", "to", "for", "with",
    "about", "as", "by", "from", "do", "does", "did", "have", "has", "had",
}


def _tokenize(text: str) -> list[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    return [
        _stemmer.stem(t) if t.isascii() else t
        for t in tokens
        if t not in _STOPWORDS
    ]


def _build_corpus() -> list[dict]:
    """
    Pulls every retrievable item into one flat list of
    {"text": ..., "source": ...} dicts - one entry per fact, one per
    memoir story. Rebuilt fresh on every call: at this app's scale
    (tens-hundreds of items) that's a few milliseconds, so there's no
    need for a persistent index or background rebuild job.
    """
    corpus = []
    for fact, _created_at in db.get_facts(limit=500):
        corpus.append({"text": fact, "source": "fact"})
    for topic, story, _created_at in db.get_memoir_entries():
        label = f"{topic}: {story}" if topic else story
        corpus.append({"text": label, "source": "memoir"})
    return corpus


def retrieve_relevant_context(query: str, top_k: int = 5, min_score: float = 0.05) -> str:
    """
    Returns a formatted block of the most relevant saved facts/memoir
    stories for `query` (the user's current message), or "" if nothing
    relevant is found - callers should just skip adding it to the
    prompt in that case.

    min_score filters out near-zero-similarity matches: TF-IDF will
    always return SOME ranking even when nothing is actually related,
    and injecting irrelevant "things you know about this user" into the
    prompt does more harm than good (the LLM may awkwardly force in a
    fact that has nothing to do with what was asked).
    """
    corpus = _build_corpus()
    if not corpus:
        return ""

    texts = [item["text"] for item in corpus]
    # Small corpus safeguard: TfidfVectorizer errors if every document is
    # empty/whitespace-only, which could happen right after setup with
    # only blank entries. Guard rather than let this crash a chat turn.
    if not any(t.strip() for t in texts):
        return ""

    try:
        vectorizer = TfidfVectorizer(tokenizer=_tokenize, lowercase=False, token_pattern=None)
        matrix = vectorizer.fit_transform(texts + [query])
    except ValueError:
        return ""  # e.g. vocabulary is empty after tokenization - nothing usable to retrieve

    query_vec = matrix[-1]
    doc_vecs = matrix[:-1]
    scores = cosine_similarity(query_vec, doc_vecs)[0]

    ranked = sorted(zip(scores, corpus), key=lambda pair: pair[0], reverse=True)
    top_matches = [item for score, item in ranked[:top_k] if score >= min_score]
    if not top_matches:
        return ""

    lines = []
    for item in top_matches:
        label = "Something you remember about this user" if item["source"] == "fact" else "A story they told you"
        lines.append(f"- ({label}) {item['text']}")
    return "Relevant things you know about this user, based on their current message:\n" + "\n".join(lines)
