"""Offline QA owned by Role 4: Task 6 and evaluation-data readiness."""

import json
from pathlib import Path

import pytest

from src.task6_lexical_search import lexical_search, tokenize
from src import task9_retrieval_pipeline as retrieval_pipeline


SAMPLE_CORPUS = [
    {
        "content": "Tục xông đất là phong tục đón người đầu tiên tới nhà trong năm mới.",
        "metadata": {"source": "phong-tuc-tet.md", "chunk_index": 0},
    },
    {
        "content": "Áo ngũ thân nam có năm thân áo, cổ đứng và năm khuy.",
        "metadata": {"source": "ao-ngu-than.md", "chunk_index": 0},
    },
    {
        "content": "Lễ hội Gióng tưởng nhớ công lao của Thánh Gióng.",
        "metadata": {"source": "le-hoi-giong.md", "chunk_index": 0},
    },
]


def test_vietnamese_tokenizer_and_known_typo_alias():
    assert tokenize("Ý nghĩa Áo ngũ thân!") == ["ý", "nghĩa", "áo", "ngũ", "thân"]
    assert "xông" in tokenize("tục xổi đất")


def test_lexical_search_ranks_cultural_keyword_and_keeps_metadata():
    results = lexical_search("chi tiết áo ngũ thân nam", top_k=2, corpus=SAMPLE_CORPUS)
    assert results[0]["metadata"]["source"] == "ao-ngu-than.md"
    assert [item["score"] for item in results] == sorted(
        [item["score"] for item in results], reverse=True
    )


def test_lexical_search_returns_empty_for_unrelated_explicit_corpus():
    assert lexical_search("Bitcoin lượng tử", top_k=3, corpus=SAMPLE_CORPUS) == []


@pytest.mark.parametrize(
    ("query", "expected_source"),
    [
        ("Ý nghĩa tục xổi đất đầu năm", "news/article_01.md"),
        ("ai cải tiến áo dài Le Mur", "news/article_02.md"),
        ("cách bảo quản áo dài lụa tơ tằm", "news/article_05.md"),
    ],
)
def test_real_corpus_bm25_top1_source(query, expected_source):
    results = lexical_search(query, top_k=1)
    assert results
    assert results[0]["metadata"]["source"] == expected_source


def test_golden_dataset_is_domain_correct_and_ready_for_ragas():
    path = Path("group_project/evaluation/golden_dataset.json")
    dataset = json.loads(path.read_text(encoding="utf-8"))

    assert 15 <= len(dataset) <= 20
    assert all(
        isinstance(item.get(field), str) and item[field].strip()
        for item in dataset
        for field in ("question", "expected_answer", "expected_context")
    )
    forbidden = ("rmit", "học phí", "ký túc xá", "scholarship")
    questions = " ".join(item["question"].lower() for item in dataset)
    assert not any(term in questions for term in forbidden)


def test_task9_low_original_cosine_triggers_pageindex(monkeypatch):
    dense = [{"content": "dense", "score": 0.20, "metadata": {}}]
    sparse = [{"content": "sparse", "score": 8.0, "metadata": {}}]
    fallback = [{"content": "structured fallback", "score": 0.9, "metadata": {}}]

    monkeypatch.setattr(retrieval_pipeline, "semantic_search", lambda query, top_k: dense)
    monkeypatch.setattr(retrieval_pipeline, "lexical_search", lambda query, top_k: sparse)
    monkeypatch.setattr(
        retrieval_pipeline,
        "rerank_rrf",
        lambda ranked_lists, top_k, k=60: [{"content": "fused", "score": 0.01, "metadata": {}}],
    )
    monkeypatch.setattr(
        retrieval_pipeline, "pageindex_search", lambda query, top_k: fallback
    )

    results = retrieval_pipeline.retrieve("câu ngoài domain", top_k=1)

    assert results[0]["source"] == "pageindex"
    assert results[0]["content"] == "structured fallback"


def test_task9_uses_cosine_not_rrf_score_for_fallback(monkeypatch):
    dense = [{"content": "relevant", "score": 0.60, "metadata": {}}]
    fused = [{"content": "relevant", "score": 1 / 61, "metadata": {}}]

    monkeypatch.setattr(retrieval_pipeline, "semantic_search", lambda query, top_k: dense)
    monkeypatch.setattr(retrieval_pipeline, "lexical_search", lambda query, top_k: [])
    monkeypatch.setattr(
        retrieval_pipeline,
        "rerank_rrf",
        lambda ranked_lists, top_k, k=60: fused,
    )

    def unexpected_fallback(query, top_k):
        raise AssertionError("RRF score must not trigger PageIndex fallback")

    monkeypatch.setattr(retrieval_pipeline, "pageindex_search", unexpected_fallback)

    results = retrieval_pipeline.retrieve("câu đúng domain", top_k=1)

    assert results[0]["source"] == "hybrid"
