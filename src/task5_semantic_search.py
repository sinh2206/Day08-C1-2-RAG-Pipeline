# src/task5_semantic_search.py

import os
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "phong_tuc_trang_phuc_le_hoi"
EMBEDDING_MODEL = "BAAI/bge-m3"

_client = chromadb.PersistentClient(path=CHROMA_DIR)
_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
_collection = _client.get_collection(name=COLLECTION_NAME, embedding_function=_ef)

_llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _generate_hyde_document(query: str) -> str:
    """
    HyDE: dùng LLM sinh một đoạn văn giả định trả lời câu hỏi,
    làm giàu ngữ cảnh trước khi embed, thay vì embed câu hỏi ngắn trực tiếp.
    """
    prompt = f"""Hãy viết một đoạn văn ngắn (3-5 câu) mô tả chi tiết,
mang tính thông tin, trả lời cho câu hỏi sau về phong tục, trang phục
hoặc lễ hội truyền thống Việt Nam. Viết như một đoạn trích từ bài viết
bách khoa, không cần chính xác tuyệt đối, chỉ cần đúng văn phong và
ngữ cảnh liên quan.

Câu hỏi: {query}

Đoạn văn:"""

    response = _llm_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


def semantic_search(
    query: str,
    top_k: int = 10,
    use_hyde: bool = False,
) -> list[dict]:
    """
    Dense retrieval trên vector store bằng cosine similarity.
    Nếu use_hyde=True, sinh hypothetical document trước rồi embed
    đoạn đó thay vì embed trực tiếp câu hỏi.

    Args:
        query: câu hỏi của user
        top_k: số lượng kết quả trả về
        use_hyde: bật/tắt HyDE (mặc định tắt để giữ hành vi chuẩn)

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
        sorted descending theo score.
    """
    search_text = query

    if use_hyde:
        try:
            search_text = _generate_hyde_document(query)
        except Exception as e:
            # Nếu HyDE lỗi (vd. hết quota API), fallback về query gốc
            # thay vì làm sập cả pipeline
            print(f"[HyDE fallback] Lỗi khi sinh hypothetical document: {e}")
            search_text = query

    results = _collection.query(
        query_texts=[search_text],
        n_results=top_k,
    )

    output = []
    for content, distance, metadata in zip(
        results["documents"][0],
        results["distances"][0],
        results["metadatas"][0],
    ):
        # ChromaDB trả về cosine distance (0=giống hệt, 2=đối nghịch)
        # Convert sang similarity score trong [0,1]: score = 1 - distance/2
        score = 1 - (distance / 2)
        output.append({
            "content": content,
            "score": round(score, 4),
            "metadata": metadata,
        })

    output.sort(key=lambda x: x["score"], reverse=True)
    return output


if __name__ == "__main__":
    test_query = "Ý nghĩa của áo dài trong văn hóa Việt Nam"

    print("=== Không dùng HyDE ===")
    for r in semantic_search(test_query, top_k=5, use_hyde=False):
        print(f"[{r['score']}] {r['metadata']['source']} — {r['content'][:100]}...")

    print("\n=== Dùng HyDE ===")
    for r in semantic_search(test_query, top_k=5, use_hyde=True):
        print(f"[{r['score']}] {r['metadata']['source']} — {r['content'][:100]}...")