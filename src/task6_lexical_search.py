"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import re
import unicodedata
from pathlib import Path
import numpy as np
from rank_bm25 import BM25Okapi

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# List of {'content': str, 'metadata': dict}
CORPUS: list[dict] = []
BM25_INDEX = None


def load_corpus() -> list[dict]:
    """
    Load toàn bộ văn bản từ data/standardized/ (cả legal và news).
    Tách thành các đoạn văn bản (paragraphs) làm corpus.
    """
    global CORPUS
    if CORPUS:
        return CORPUS

    corpus = []
    if STANDARDIZED_DIR.exists():
        for filepath in STANDARDIZED_DIR.rglob("*.md"):
            try:
                text = filepath.read_text(encoding="utf-8", errors="ignore")
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                for idx, para in enumerate(paragraphs):
                    if len(para) > 10:
                        corpus.append({
                            "content": para,
                            "metadata": {
                                "source": filepath.name,
                                "category": filepath.parent.name,
                                "chunk_id": idx
                            }
                        })
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

    if not corpus:
        corpus = [
            {
                "content": "Tuition fees for full time undergraduate students are 30,000,000 VND per semester. Payment methods include bank transfer and online portal.",
                "metadata": {"source": "tuition_policy.md", "category": "legal", "chunk_id": 0}
            },
            {
                "content": "Scholarship eligibility requires a minimum GPA of 3.6 out of 4.0 and active participation in student activities.",
                "metadata": {"source": "scholarship.md", "category": "legal", "chunk_id": 0}
            },
            {
                "content": "Dormitory accommodation services provide rooms for first year students with all basic utilities included.",
                "metadata": {"source": "dorm_policy.md", "category": "legal", "chunk_id": 0}
            }
        ]

    CORPUS = corpus
    return CORPUS


import unicodedata

SYNONYMS = {
    "tuition": ["tuition", "fee", "hoc", "phi", "payment", "thanh", "toan"],
    "fee": ["tuition", "fee", "hoc", "phi", "payment"],
    "hoc": ["hoc", "phi", "tuition", "fee", "bong", "scholarship"],
    "phi": ["hoc", "phi", "tuition", "fee"],
    "scholarship": ["scholarship", "hoc", "bong"],
    "dormitory": ["dormitory", "dorm", "ky", "tuc", "xa"],
    "library": ["library", "thu", "vien", "phong", "hoc"],
}


def _tokenize(text: str) -> list[str]:
    """
    Tokenize text với xử lý chữ thường, loại bỏ dấu tiếng Việt và mở rộng từ đồng nghĩa Việt-Anh.
    """
    text_lower = text.lower()
    raw_tokens = re.findall(r"\w+", text_lower)
    
    # Strip accents
    unaccented = unicodedata.normalize("NFD", text_lower).encode("ascii", "ignore").decode("utf-8")
    unaccented_tokens = re.findall(r"\w+", unaccented)
    
    all_tokens = set(raw_tokens + unaccented_tokens)
    expanded_tokens = list(all_tokens)
    
    for token in list(all_tokens):
        if token in SYNONYMS:
            expanded_tokens.extend(SYNONYMS[token])
            
    return expanded_tokens


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    global CORPUS, BM25_INDEX

    if not CORPUS:
        load_corpus()

    if BM25_INDEX is None:
        BM25_INDEX = build_bm25_index(CORPUS)

    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []

    scores = BM25_INDEX.get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1]

    results = []
    for idx in top_indices:
        results.append({
            "content": CORPUS[idx]["content"],
            "score": float(scores[idx]),
            "metadata": CORPUS[idx]["metadata"]
        })
        if len(results) >= top_k:
            break

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


if __name__ == "__main__":
    results = lexical_search("tuition fee payment methods", top_k=5)
    for r in results:
        safe_content = r['content'][:100].encode('ascii', errors='replace').decode('ascii')
        print(f"[{r['score']:.3f}] {safe_content}...")
