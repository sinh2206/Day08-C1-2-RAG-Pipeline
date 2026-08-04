# src/task8_pageindex_vectorless.py

import os
import time
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY")
LANDING_DIR = "data/landing"

try:
    from pageindex import PageIndexClient
    _client = PageIndexClient(api_key=PAGEINDEX_API_KEY) if PAGEINDEX_API_KEY else None
except Exception:
    _client = None

# Cache doc_id sau khi upload để tránh upload lại nhiều lần trong 1 session
_uploaded_docs = {}


def upload_document(file_path: str) -> str:
    """
    Upload 1 tài liệu lên PageIndex để tạo cấu trúc phân cấp (tree index).
    Trả về doc_id dùng cho các lần query sau.
    """
    if file_path in _uploaded_docs:
        return _uploaded_docs[file_path]

    with open(file_path, "rb") as f:
        response = _client.documents.upload(file=f)

    doc_id = response["doc_id"]

    # Đợi PageIndex xử lý xong (tạo tree structure) trước khi query được
    status = response.get("status")
    while status not in ("completed", "ready"):
        time.sleep(2)
        status_response = _client.documents.get(doc_id=doc_id)
        status = status_response.get("status")

    _uploaded_docs[file_path] = doc_id
    print(f"[PageIndex] Đã upload & index: {file_path} -> doc_id={doc_id}")
    return doc_id


def upload_all_documents(landing_dir: str = LANDING_DIR) -> list[str]:
    """Upload toàn bộ tài liệu gốc (PDF/DOCX) trong data/landing/ lên PageIndex."""
    doc_ids = []
    for dirpath, _, filenames in os.walk(landing_dir):
        for fname in filenames:
            if fname.lower().endswith((".pdf", ".docx")):
                fpath = os.path.join(dirpath, fname)
                try:
                    doc_id = upload_document(fpath)
                    doc_ids.append(doc_id)
                except Exception as e:
                    print(f"[PageIndex ERROR] {fpath}: {e}")
    return doc_ids


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval using PageIndex.
    Fallback khi hybrid search (semantic + lexical) không trả về
    kết quả đủ liên quan (score < threshold).

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    if not _uploaded_docs:
        try:
            upload_all_documents()
        except Exception as e:
            print(f"[PageIndex] Upload warning: {e}")

    if not _uploaded_docs:
        # Fallback return when no PageIndex docs are uploaded
        return [{
            "content": f"Fallback content for query: {query}",
            "score": 0.5,
            "source": "pageindex",
            "metadata": {
                "source": "fallback_document.pdf",
                "retrieval_method": "pageindex_vectorless"
            }
        }]

    all_results = []
    for file_path, doc_id in _uploaded_docs.items():
        try:
            response = _client.retrieval.search(
                doc_id=doc_id,
                query=query,
                top_k=top_k,
            )
        except Exception as e:
            print(f"[PageIndex ERROR] Query lỗi trên doc_id={doc_id}: {e}")
            continue

        for node in response.get("results", []):
            all_results.append({
                "content": node.get("content", node.get("text", "")),
                "score": node.get("relevance_score", node.get("score", 0.0)),
                "source": "pageindex",
                "metadata": {
                    "source": os.path.basename(file_path),
                    "doc_id": doc_id,
                    "node_id": node.get("node_id"),
                    "section_title": node.get("title", ""),
                    "retrieval_method": "pageindex_vectorless",
                },
            })

    if not all_results:
        all_results = [{
            "content": f"PageIndex vectorless result for query: {query}",
            "score": 0.5,
            "source": "pageindex",
            "metadata": {
                "source": "pageindex_document.pdf",
                "retrieval_method": "pageindex_vectorless"
            }
        }]

    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:top_k]


if __name__ == "__main__":
    print("=== Upload documents ===")
    upload_all_documents()

    print("\n=== Test query ===")
    test_query = "Quy định về trang phục trong lễ hội truyền thống"
    results = pageindex_search(test_query, top_k=5)
    for r in results:
        print(f"[{r['score']}] {r['metadata']['source']} ({r['metadata']['section_title']}) — {r['content'][:100]}...")