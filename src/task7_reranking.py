"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement — khuyến nghị vì không cần API key

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.

Lưu ý quan trọng về RRF (sẽ dùng lại ở Task 9): điểm RRF fused CHỈ phụ thuộc thứ hạng,
không phải độ tương đồng thật. Top-1 sau khi fuse luôn xấp xỉ 1/(k+1) ≈ 0.0164 (k=60),
bất kể nội dung đó có thật sự liên quan đến câu hỏi hay không. Đừng dùng điểm RRF để
quyết định fallback ở Task 9 — xem ghi chú ở đó.
"""

from functools import lru_cache
from math import sqrt
from typing import Any


CROSS_ENCODER_MODEL = "BAAI/bge-reranker-v2-m3"


def _validate_top_k(top_k: int) -> None:
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise TypeError("top_k must be an integer")
    if top_k < 0:
        raise ValueError("top_k must be non-negative")


def _cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """Compute cosine similarity without requiring NumPy."""
    if len(vector_a) != len(vector_b):
        raise ValueError(
            f"Embedding dimensions do not match: {len(vector_a)} != {len(vector_b)}"
        )
    if not vector_a:
        raise ValueError("Embeddings must not be empty")

    dot_product = sum(float(a) * float(b) for a, b in zip(vector_a, vector_b))
    norm_a = sqrt(sum(float(value) ** 2 for value in vector_a))
    norm_b = sqrt(sum(float(value) ** 2 for value in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def _candidate_key(candidate: dict) -> tuple:
    """Build a stable identity for deduplicating results across rankers."""
    if candidate.get("id") is not None:
        return ("id", str(candidate["id"]))

    metadata = candidate.get("metadata") or {}
    if isinstance(metadata, dict) and metadata.get("source") is not None:
        return (
            "source",
            str(metadata["source"]),
            str(metadata.get("chunk_index", "")),
            str(candidate.get("content", "")),
        )
    return ("content", str(candidate.get("content", "")))


@lru_cache(maxsize=1)
def _get_cross_encoder() -> Any:
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise ImportError(
            "Cross-encoder reranking requires sentence-transformers. "
            "Install the dependencies from requirements.txt."
        ) from exc

    return CrossEncoder(CROSS_ENCODER_MODEL)


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng cross-encoder model.

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by rerank_score descending.
    """
    _validate_top_k(top_k)
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if top_k == 0 or not candidates:
        return []

    pairs = []
    for index, candidate in enumerate(candidates):
        content = candidate.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"Candidate {index} must contain non-empty string content")
        pairs.append((query, content))

    raw_scores = _get_cross_encoder().predict(pairs, show_progress_bar=len(pairs) > 1)
    if len(raw_scores) != len(candidates):
        raise RuntimeError("Cross-encoder returned an unexpected number of scores")

    scored = []
    for original_index, (candidate, raw_score) in enumerate(zip(candidates, raw_scores)):
        if hasattr(raw_score, "tolist"):
            raw_score = raw_score.tolist()
        if isinstance(raw_score, (list, tuple)):
            if len(raw_score) != 1:
                raise ValueError("Cross-encoder must return one score per candidate")
            raw_score = raw_score[0]
        scored.append((float(raw_score), original_index, candidate))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [
        {**candidate, "score": score}
        for score, _, candidate in scored[:top_k]
    ]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))

    Args:
        query_embedding: Vector embedding của query
        candidates: List of {'content': str, 'score': float, 'embedding': list, 'metadata': dict}
        top_k: Số lượng kết quả
        lambda_param: Trade-off giữa relevance (1.0) và diversity (0.0)

    Returns:
        List of top_k candidates selected by MMR.
    """
    _validate_top_k(top_k)
    if not 0.0 <= lambda_param <= 1.0:
        raise ValueError("lambda_param must be between 0.0 and 1.0")
    if top_k == 0 or not candidates:
        return []
    if not query_embedding:
        raise ValueError("query_embedding must not be empty")

    candidate_embeddings = []
    for index, candidate in enumerate(candidates):
        embedding = candidate.get("embedding")
        if not isinstance(embedding, (list, tuple)) or not embedding:
            raise ValueError(f"Candidate {index} has no embedding")
        vector = [float(value) for value in embedding]
        if len(vector) != len(query_embedding):
            raise ValueError(
                f"Candidate {index} embedding dimension does not match the query"
            )
        candidate_embeddings.append(vector)

    selected: list[int] = []
    selected_scores: list[float] = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_index = remaining[0]
        best_score = float("-inf")
        for index in remaining:
            relevance = _cosine_similarity(query_embedding, candidate_embeddings[index])
            redundancy = 0.0
            if selected:
                redundancy = max(
                    _cosine_similarity(candidate_embeddings[index], candidate_embeddings[chosen])
                    for chosen in selected
                )
            mmr_score = lambda_param * relevance - (1.0 - lambda_param) * redundancy
            if mmr_score > best_score:
                best_index = index
                best_score = mmr_score

        selected.append(best_index)
        selected_scores.append(best_score)
        remaining.remove(best_index)

    return [
        {**candidates[index], "score": score}
        for index, score in zip(selected, selected_scores)
    ]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))

    Args:
        ranked_lists: List of ranked result lists (mỗi list từ 1 ranker)
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60, từ paper Cormack et al. 2009)

    Returns:
        List of top_k candidates sorted by RRF score descending.
    """
    _validate_top_k(top_k)
    if not isinstance(k, int) or isinstance(k, bool):
        raise TypeError("k must be an integer")
    if k < 0:
        raise ValueError("k must be non-negative")
    if top_k == 0 or not ranked_lists:
        return []

    scores: dict[tuple, float] = {}
    candidates_by_key: dict[tuple, dict] = {}
    best_rank: dict[tuple, int] = {}
    discovery_order: dict[tuple, int] = {}

    for ranked_list in ranked_lists:
        seen_in_list = set()
        for rank, candidate in enumerate(ranked_list, start=1):
            if not isinstance(candidate, dict):
                raise TypeError("Every ranked result must be a dictionary")
            content = candidate.get("content")
            if not isinstance(content, str) or not content:
                raise ValueError("Every ranked result must contain non-empty content")

            key = _candidate_key(candidate)
            if key in seen_in_list:
                continue
            seen_in_list.add(key)

            if key not in candidates_by_key:
                candidates_by_key[key] = candidate
                discovery_order[key] = len(discovery_order)
                best_rank[key] = rank
            else:
                best_rank[key] = min(best_rank[key], rank)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)

    ordered_keys = sorted(
        scores,
        key=lambda key: (-scores[key], best_rank[key], discovery_order[key]),
    )
    return [
        {**candidates_by_key[key], "score": scores[key]}
        for key in ordered_keys[:top_k]
    ]


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "rrf",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Unified reranking interface.

    Args:
        query: Câu truy vấn
        candidates: Danh sách candidates từ retrieval
        top_k: Số lượng kết quả sau rerank
        method: Phương pháp reranking

    Returns:
        List of top_k reranked candidates.
    """
    _validate_top_k(top_k)
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if top_k == 0 or not candidates:
        return []

    normalized_method = method.strip().lower() if isinstance(method, str) else method
    if normalized_method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif normalized_method == "mmr":
        try:
            from .task4_chunking_indexing import get_embedding_model
        except ImportError:
            from task4_chunking_indexing import get_embedding_model

        prepared_candidates = [dict(candidate) for candidate in candidates]
        missing_indices = [
            index
            for index, candidate in enumerate(prepared_candidates)
            if not candidate.get("embedding")
        ]
        texts = [query]
        for index in missing_indices:
            content = prepared_candidates[index].get("content")
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"Candidate {index} must contain non-empty string content")
            texts.append(content)

        encoded = get_embedding_model().encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        if len(encoded) != len(texts):
            raise RuntimeError("Embedding model returned an unexpected number of vectors")

        def to_vector(value: Any) -> list[float]:
            if hasattr(value, "tolist"):
                value = value.tolist()
            return [float(component) for component in value]

        query_embedding = to_vector(encoded[0])
        for encoded_position, candidate_index in enumerate(missing_indices, start=1):
            prepared_candidates[candidate_index]["embedding"] = to_vector(
                encoded[encoded_position]
            )

        return rerank_mmr(query_embedding, prepared_candidates, top_k=top_k)
    elif normalized_method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    # Test with dummy data
    dummy_candidates = [
        {"content": "Tuition fee payment schedule", "score": 0.8, "metadata": {}},
        {"content": "Scholarship eligibility requirements", "score": 0.6, "metadata": {}},
        {"content": "Library study room booking guide", "score": 0.5, "metadata": {}},
    ]
    results = rerank("tuition fee payment", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")
