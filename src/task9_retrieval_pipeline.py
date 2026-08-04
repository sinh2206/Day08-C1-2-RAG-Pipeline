"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.

Logic:
    1. Chạy semantic_search + lexical_search song song
    2. Merge kết quả (RRF hoặc weighted fusion)
    3. Rerank
    4. Nếu top result score < threshold → fallback sang PageIndex
    5. Return top_k results

⚠️ BẪY THƯỜNG GẶP — đọc kỹ trước khi code:
    Nếu bạn dùng điểm RRF đã fuse (Task 7) để so với score_threshold, bạn sẽ gặp bug
    thật: RRF max score luôn ≈ 1/(k+1) ≈ 0.0164 (k=60) BẤT KỂ nội dung có liên quan
    hay không. Nếu đặt threshold thấp (như 0.005) để "hợp" với thang điểm RRF, thực
    chất KHÔNG câu hỏi nào đủ thấp để trigger fallback nữa — kể cả query hoàn toàn vô
    nghĩa vẫn trả về kết quả "hybrid" (rác) thay vì fallback đúng như thiết kế.

    Cách sửa đúng: giữ điểm cosine similarity GỐC của semantic_search (trước khi qua
    RRF) làm căn cứ quyết định fallback, tách biệt khỏi điểm RRF dùng để sắp xếp kết
    quả cuối cùng. Calibrate threshold bằng cách tự đo: chạy vài câu hỏi chắc chắn
    liên quan và vài câu chắc chắn lạc đề/rác qua semantic_search, xem khoảng cách
    điểm số giữa hai nhóm rồi chọn ngưỡng nằm giữa.
"""

from concurrent.futures import ThreadPoolExecutor
from math import isfinite
from numbers import Real


# Lazy wrappers keep optional services/models from failing at module import time.
# They are module-level functions so tests and applications can still monkeypatch them.
def semantic_search(query: str, top_k: int) -> list[dict]:
    from .task5_semantic_search import semantic_search as search

    return search(query, top_k=top_k)


def lexical_search(query: str, top_k: int) -> list[dict]:
    from .task6_lexical_search import lexical_search as search

    return search(query, top_k=top_k)


def rerank(query: str, candidates: list[dict], top_k: int, method: str) -> list[dict]:
    from .task7_reranking import rerank as apply_rerank

    return apply_rerank(query, candidates, top_k=top_k, method=method)


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int, k: int = 60
) -> list[dict]:
    from .task7_reranking import rerank_rrf as apply_rrf

    return apply_rrf(ranked_lists, top_k=top_k, k=k)


def pageindex_search(query: str, top_k: int) -> list[dict]:
    from .task8_pageindex_vectorless import pageindex_search as search

    return search(query, top_k=top_k)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Ngưỡng 0.48 áp dụng cho corpus/model hiện tại. Khi đổi corpus hoặc embedding model,
# cần đo lại nhóm query liên quan và lạc đề để hiệu chỉnh ngưỡng này.
SCORE_THRESHOLD = 0.48  # So với cosine gốc, tuyệt đối không so với điểm RRF.
DEFAULT_TOP_K = 5
RERANK_METHOD = "rrf"  # "cross_encoder" | "mmr" | "rrf"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.

    Pipeline:
        Query
          ├→ Semantic Search → dense_results (giữ điểm cosine gốc)
          ├→ Lexical Search  → sparse_results
          │
          ├→ Merge (RRF) → merged_results
          ├→ Rerank → reranked_results
          │
          └→ If dense_results[0]["score"] < threshold:
                └→ PageIndex Vectorless → fallback_results

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng điểm cosine gốc tối thiểu (KHÔNG phải điểm RRF)
        use_reranking: Có áp dụng reranking hay không

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise TypeError("top_k must be an integer")
    if top_k < 0:
        raise ValueError("top_k must be non-negative")
    if top_k == 0:
        return []
    if not isinstance(score_threshold, Real) or isinstance(score_threshold, bool):
        raise TypeError("score_threshold must be a number")
    if not 0.0 <= float(score_threshold) <= 1.0:
        raise ValueError("score_threshold must be between 0.0 and 1.0")

    retrieval_k = top_k * 2

    # Step 1: Dense and sparse retrieval use independent resources, so they can
    # run concurrently. A failure in one ranker must not discard the other one.
    with ThreadPoolExecutor(max_workers=2) as executor:
        dense_future = executor.submit(semantic_search, query, retrieval_k)
        sparse_future = executor.submit(lexical_search, query, retrieval_k)

        try:
            dense_results = dense_future.result()
            if not isinstance(dense_results, list):
                raise TypeError("semantic_search must return a list")
        except Exception as exc:
            print(f"  [WARN] Semantic search failed: {exc}")
            dense_results = []

        try:
            sparse_results = sparse_future.result()
            if not isinstance(sparse_results, list):
                raise TypeError("lexical_search must return a list")
        except Exception as exc:
            print(f"  [WARN] Lexical search failed: {exc}")
            sparse_results = []

    # Save the original cosine confidence before RRF overwrites the score field.
    # Do not derive fallback confidence from merged/final_results.
    dense_scores = []
    for result in dense_results:
        if isinstance(result, dict):
            try:
                score = float(result["score"])
                if isfinite(score):
                    dense_scores.append(score)
            except (KeyError, TypeError, ValueError):
                continue
    best_cosine_score = max(dense_scores, default=0.0)

    # Step 2: RRF fuses ranks, avoiding direct addition of cosine and BM25 scores.
    merged = rerank_rrf(
        [dense_results, sparse_results],
        top_k=retrieval_k,
    ) if dense_results or sparse_results else []
    merged = [{**item, "source": "hybrid"} for item in merged]

    # Step 3: RRF is already the configured reranker. Running single-list RRF
    # again would replace the genuine two-ranker fusion score, so only apply an
    # additional reranker when a different method is selected.
    final_results = merged[:top_k]
    if use_reranking and merged and RERANK_METHOD != "rrf":
        try:
            final_results = rerank(
                query,
                merged,
                top_k=top_k,
                method=RERANK_METHOD,
            )
            final_results = [
                {**item, "source": "hybrid"}
                for item in final_results
            ]
        except Exception as exc:
            print(f"  [WARN] Additional reranking failed; using RRF results: {exc}")
            final_results = merged[:top_k]

    # Step 4: The fallback gate uses ONLY the original dense cosine score.
    if best_cosine_score < float(score_threshold):
        print(
            f"  [WARN] Semantic best cosine ({best_cosine_score:.3f}) "
            f"< threshold ({float(score_threshold):.3f}); trying PageIndex"
        )
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                normalized_fallback = [
                    {**item, "source": "pageindex"}
                    for item in fallback[:top_k]
                    if isinstance(item, dict)
                ]
                if normalized_fallback:
                    return normalized_fallback
        except Exception as exc:
            print(f"  [WARN] PageIndex fallback failed; using hybrid results: {exc}")

    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "What is the tuition fee at RMIT Vietnam?",
        "How do I book a library study room?",
        "What scholarships are available for international students?",
        "xyzabc123nonsense",  # Query không có kết quả → test fallback
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.3f}] [{r['source']}] {r['content'][:80]}...")
