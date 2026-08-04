"""Task 6 — Lexical Search Module (BM25).

Module nay co the chay doc lap voi corpus truyen vao, va se tu dung chunks cua
Task 4 khi Task 4 da san sang.  Mot BM25 implementation nho duoc kem theo de
module van test duoc truoc khi cai ``rank-bm25``.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CORPUS: list[dict] = []
_BM25_INDEX = None
_INDEXED_CORPUS_ID: int | None = None

# Query aliases cho cac loi go/ten goi thuong gap trong domain van hoa.
QUERY_ALIASES = {
    "xổi đất": "xông đất",
    "áo năm thân": "áo ngũ thân",
}


def normalize_query(text: str) -> str:
    """Normalize Unicode, lowercase va sua mot so alias da biet."""
    normalized = unicodedata.normalize("NFC", text).lower().strip()
    for source, target in QUERY_ALIASES.items():
        normalized = normalized.replace(source, target)
    return normalized


def tokenize(text: str) -> list[str]:
    """Tokenize Unicode, giu nguyen dau tieng Viet va bo dau cau."""
    return re.findall(r"[^\W_]+", normalize_query(text), flags=re.UNICODE)


@dataclass
class _LocalBM25:
    """BM25Okapi toi gian, dung khi package ``rank_bm25`` chua duoc cai."""

    tokenized_corpus: Sequence[Sequence[str]]
    k1: float = 1.5
    b: float = 0.75

    def __post_init__(self) -> None:
        self.doc_lengths = [len(document) for document in self.tokenized_corpus]
        self.avgdl = (
            sum(self.doc_lengths) / len(self.doc_lengths)
            if self.doc_lengths
            else 0.0
        )
        self.term_frequencies: list[dict[str, int]] = []
        document_frequencies: dict[str, int] = {}

        for document in self.tokenized_corpus:
            frequencies: dict[str, int] = {}
            for token in document:
                frequencies[token] = frequencies.get(token, 0) + 1
            self.term_frequencies.append(frequencies)
            for token in frequencies:
                document_frequencies[token] = document_frequencies.get(token, 0) + 1

        document_count = len(self.tokenized_corpus)
        self.idf = {
            token: math.log(1.0 + (document_count - frequency + 0.5) / (frequency + 0.5))
            for token, frequency in document_frequencies.items()
        }

    def get_scores(self, query_tokens: Sequence[str]) -> list[float]:
        scores: list[float] = []
        for index, frequencies in enumerate(self.term_frequencies):
            score = 0.0
            length = self.doc_lengths[index]
            length_ratio = length / self.avgdl if self.avgdl else 0.0
            for token in query_tokens:
                frequency = frequencies.get(token, 0)
                if not frequency:
                    continue
                denominator = frequency + self.k1 * (1 - self.b + self.b * length_ratio)
                score += self.idf.get(token, 0.0) * frequency * (self.k1 + 1) / denominator
            scores.append(score)
        return scores


def load_corpus() -> list[dict]:
    """Load shared Task 4 chunks; fall back to standardized Markdown files."""
    try:
        from .task4_chunking_indexing import chunk_documents, load_documents

        documents = load_documents()
        if documents:
            chunks = chunk_documents(documents)
            if chunks:
                return chunks
    except (ImportError, NotImplementedError):
        pass

    corpus: list[dict] = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue
        try:
            relative_source = str(md_file.relative_to(STANDARDIZED_DIR))
        except ValueError:
            relative_source = md_file.name
        corpus.append(
            {
                "content": content,
                "metadata": {
                    "source": relative_source,
                    "type": md_file.parent.name,
                    "chunk_index": 0,
                },
            }
        )
    return corpus


def set_corpus(corpus: list[dict]) -> None:
    """Inject corpus (useful for unit tests and integration with Role 3)."""
    global CORPUS, _BM25_INDEX, _INDEXED_CORPUS_ID
    CORPUS = list(corpus)
    _BM25_INDEX = None
    _INDEXED_CORPUS_ID = None


def build_bm25_index(corpus: list[dict]):
    """Build a BM25 index from ``content`` fields in the supplied corpus."""
    if not isinstance(corpus, list):
        raise TypeError("corpus must be a list of dictionaries")
    tokenized_corpus = []
    for document in corpus:
        if not isinstance(document, dict) or "content" not in document:
            raise ValueError("each corpus item must contain a 'content' field")
        tokenized_corpus.append(tokenize(str(document["content"])))

    try:
        from rank_bm25 import BM25Okapi

        return BM25Okapi(tokenized_corpus)
    except ImportError:
        return _LocalBM25(tokenized_corpus)


def lexical_search(
    query: str, top_k: int = 10, corpus: list[dict] | None = None
) -> list[dict]:
    """Return BM25 results sorted by descending score."""
    if top_k <= 0 or not query or not query.strip():
        return []

    global CORPUS, _BM25_INDEX, _INDEXED_CORPUS_ID
    if corpus is not None:
        active_corpus = corpus
        index = build_bm25_index(active_corpus)
    else:
        if not CORPUS:
            CORPUS = load_corpus()
        active_corpus = CORPUS
        corpus_id = id(CORPUS)
        if _BM25_INDEX is None or _INDEXED_CORPUS_ID != corpus_id:
            _BM25_INDEX = build_bm25_index(active_corpus)
            _INDEXED_CORPUS_ID = corpus_id
        index = _BM25_INDEX

    if not active_corpus:
        return []

    scores = index.get_scores(tokenize(query))
    ranked_indices = sorted(
        range(len(active_corpus)), key=lambda idx: (-float(scores[idx]), idx)
    )

    results = []
    for idx in ranked_indices:
        score = float(scores[idx])
        if score <= 0:
            continue
        document = active_corpus[idx]
        results.append(
            {
                "content": document["content"],
                "score": score,
                "metadata": dict(document.get("metadata", {})),
            }
        )
        if len(results) >= top_k:
            break
    return results


if __name__ == "__main__":
    demo_corpus = [
        {
            "content": "Tục xông đất là phong tục đón người đầu tiên đến nhà trong năm mới.",
            "metadata": {"source": "phong-tuc-tet.md", "type": "custom", "chunk_index": 0},
        },
        {
            "content": "Áo ngũ thân nam có năm thân áo, cổ đứng và năm khuy.",
            "metadata": {"source": "ao-ngu-than.md", "type": "costume", "chunk_index": 0},
        },
    ]
    for result in lexical_search("chi tiết áo ngũ thân nam", top_k=5, corpus=demo_corpus):
        print(f"[{result['score']:.3f}] {result['content']}")
