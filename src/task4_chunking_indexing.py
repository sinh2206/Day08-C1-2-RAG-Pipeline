"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (ChromaDB khuyến cáo — đơn giản, local, không cần Docker)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dim, nhẹ)
    - BAAI/bge-m3 (1024 dim, multilingual, tốt cho cả tiếng Việt lẫn tiếng Anh)
    - OpenAI text-embedding-3-small (1536 dim, API)

Vector store options:
    - ChromaDB (khuyến cáo: đơn giản, local persistent, không cần Docker)
    - Weaviate (hỗ trợ hybrid search built-in, cần Docker/Cloud)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers chromadb

Lưu ý quan trọng: nếu sau này đổi corpus (đổi chủ đề, thêm/bớt tài liệu), phải XÓA
chroma_db/ cũ trước khi reindex — nếu không, chunk cũ và mới sẽ tồn tại lẫn lộn
trong cùng collection, retrieval sẽ trả về kết quả rác từ dữ liệu cũ.
"""

from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Any

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# Recursive chunking giữ ưu tiên ranh giới đoạn/câu nhưng vẫn bảo đảm giới hạn
# kích thước, nên phù hợp với corpus Markdown có cấu trúc không đồng nhất.
CHUNK_SIZE = 800         # Đủ ngữ cảnh cho retrieval nhưng chưa quá dài, tránh pha loãng nội dung.
CHUNK_OVERLAP = 100      # Chồng lấn 12.5% để không mất ý tại ranh giới giữa hai chunk.
CHUNKING_METHOD = "recursive"  # Ổn định, nhẹ và không cần gọi embedding để chia đoạn.

# BGE-M3 hỗ trợ đa ngôn ngữ, đặc biệt phù hợp khi corpus và truy vấn có cả
# tiếng Việt lẫn tiếng Anh; vector 1024 chiều cho chất lượng semantic retrieval tốt.
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

# TODO: Chọn vector store
VECTOR_STORE = "chromadb"  # "chromadb" | "weaviate" | "faiss"
COLLECTION_NAME = "vn-culture-doc"  # Tên collection trong vector store


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    if not STANDARDIZED_DIR.exists():
        return []

    documents = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if not md_file.is_file():
            continue

        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        relative_path = md_file.relative_to(STANDARDIZED_DIR)
        doc_type = relative_path.parts[0] if len(relative_path.parts) > 1 else "unknown"
        documents.append({
            "content": content,
            "metadata": {
                "source": relative_path.as_posix(),
                "type": doc_type,
            },
        })

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đã chọn.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    if CHUNK_SIZE <= 0:
        raise ValueError("CHUNK_SIZE must be greater than zero")
    if not 0 <= CHUNK_OVERLAP < CHUNK_SIZE:
        raise ValueError("CHUNK_OVERLAP must be non-negative and smaller than CHUNK_SIZE")
    if CHUNKING_METHOD != "recursive":
        raise ValueError(
            f"Unsupported CHUNKING_METHOD={CHUNKING_METHOD!r}; "
            "this implementation uses the configured recursive strategy"
        )

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as exc:
        raise ImportError(
            "Chunking requires langchain-text-splitters. "
            "Install the dependencies from requirements.txt."
        ) from exc

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = []
    for doc in documents:
        content = doc.get("content", "")
        if not isinstance(content, str):
            raise TypeError("Each document's 'content' must be a string")
        if not content.strip():
            continue

        metadata = doc.get("metadata", {})
        if not isinstance(metadata, dict):
            raise TypeError("Each document's 'metadata' must be a dictionary")

        for chunk_index, chunk_text in enumerate(splitter.split_text(content)):
            chunk_text = chunk_text.strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "metadata": {**metadata, "chunk_index": chunk_index},
                })

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng model đã chọn.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    if not chunks:
        return []

    texts = []
    for chunk in chunks:
        content = chunk.get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Every chunk must contain non-empty string content")
        texts.append(content)

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=len(texts) > 1,
        normalize_embeddings=True,
    )
    if len(embeddings) != len(chunks):
        raise RuntimeError("Embedding model returned an unexpected number of vectors")

    for chunk, embedding in zip(chunks, embeddings):
        vector = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        if len(vector) != EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dimension mismatch: expected {EMBEDDING_DIM}, got {len(vector)}"
            )
        chunk["embedding"] = [float(value) for value in vector]

    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store đã chọn.
    """
    if VECTOR_STORE != "chromadb":
        raise ValueError(
            f"Unsupported VECTOR_STORE={VECTOR_STORE!r}; only 'chromadb' is configured"
        )

    collection = get_collection()
    if not chunks:
        return collection

    ids = []
    documents = []
    embeddings = []
    metadatas = []

    for position, chunk in enumerate(chunks):
        content = chunk.get("content")
        embedding = chunk.get("embedding")
        metadata = chunk.get("metadata", {})
        if not isinstance(content, str) or not content:
            raise ValueError(f"Chunk {position} has no valid content")
        if not isinstance(embedding, (list, tuple)) or not embedding:
            raise ValueError(f"Chunk {position} has no embedding")
        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Chunk {position} has embedding dimension {len(embedding)}; "
                f"expected {EMBEDDING_DIM}"
            )
        if not isinstance(metadata, dict):
            raise TypeError(f"Chunk {position} metadata must be a dictionary")

        source = str(metadata.get("source", "unknown"))
        chunk_index = metadata.get("chunk_index", position)
        source_key = sha256(source.encode("utf-8")).hexdigest()[:16]
        ids.append(f"{source_key}_chunk_{chunk_index}")
        documents.append(content)
        embeddings.append([float(value) for value in embedding])
        metadatas.append({
            str(key): value
            for key, value in metadata.items()
            if value is not None and isinstance(value, (str, int, float, bool))
        })

    # Keep batches below Chroma/SQLite parameter limits for larger corpora.
    batch_size = 500
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

    return collection


@lru_cache(maxsize=1)
def get_embedding_model() -> Any:
    """Load and cache the shared SentenceTransformer model."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "Embedding requires sentence-transformers. "
            "Install the dependencies from requirements.txt."
        ) from exc

    return SentenceTransformer(EMBEDDING_MODEL)


def get_collection():
    """Open the persistent Chroma collection used by indexing and retrieval."""
    try:
        import chromadb
    except ImportError as exc:
        raise ImportError(
            "Indexing requires chromadb. Install the dependencies from requirements.txt."
        ) from exc

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()
