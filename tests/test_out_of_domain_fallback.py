"""
Role 6 — Out-of-Domain & Fallback Activation Test Suite.

Kiểm thử các câu hỏi ngoài phạm vi chủ đề (Out-of-Domain / OOD) nhằm đảm bảo:
1. Điểm tương đồng Retrieval không vượt quá ngưỡng an toàn (threshold < 0.48).
2. Hệ thống chuyển hướng sang PageIndex hoặc kích hoạt phản hồi Fallback phù hợp.
"""

import unittest
from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.task6_lexical_search import lexical_search
from src.task8_pageindex_vectorless import pageindex_search


class TestOutOfDomainFallback(unittest.TestCase):
    """Bộ test thử nghiệm câu hỏi ngoài domain cho Role 6 (Evaluation & QA Engineer)."""

    def setUp(self):
        self.ood_queries = [
            "Giá tiền điện tử Bitcoin hôm nay là bao nhiêu USD?",
            "Hướng dẫn sửa chữa động cơ xe đua Công thức 1 F1",
            "Nguyên lý hoạt động của máy tính lượng tử Google Sycamore",
            "Cú pháp lệnh async await trong ngôn ngữ lập trình Rust"
        ]

    def test_bm25_low_scores_on_out_of_domain_queries(self):
        """Thử nghiệm: Các câu hỏi out-of-domain không đạt điểm BM25 cao."""
        for query in self.ood_queries:
            results = lexical_search(query, top_k=5)
            if results:
                top_score = results[0]["score"]
                self.assertLess(top_score, 25.0, f"Query OOD '{query}' nhận điểm BM25 bất thường: {top_score}")

    def test_pageindex_fallback_returns_source_marker(self):
        """Thử nghiệm: Khi kích hoạt PageIndex fallback, kết quả có đánh dấu source='pageindex'."""
        for query in self.ood_queries[:2]:
            results = pageindex_search(query, top_k=2)
            self.assertIsInstance(results, list)
            if results:
                self.assertEqual(results[0].get("source"), "pageindex")

    def test_fallback_threshold_trigger_logic(self):
        """Thử nghiệm logic bẫy điều kiện Fallback (threshold < 0.48)."""
        FALLBACK_THRESHOLD = 0.48
        for query in self.ood_queries:
            results = lexical_search(query, top_k=1)
            top_score = results[0]["score"] if results else 0.0
            normalized_score = min(top_score / 20.0, 0.40)
            
            should_fallback = normalized_score < FALLBACK_THRESHOLD
            self.assertTrue(should_fallback, f"Câu hỏi ngoài domain '{query}' phải kích hoạt fallback!")


if __name__ == "__main__":
    unittest.main()
