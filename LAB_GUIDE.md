# 🎓 HƯỚNG DẪN BÀI LAB (LAB GUIDE & CODELAB)
## Ngày 8 — RAG Pipeline v2: Hybrid Retrieval, Vectorless Fallback & Generation có Citation

---

## 📖 1. Giải Thích Thuật Ngữ (Glossary)

Bảng dưới đây tóm tắt các thuật ngữ cốt lõi được sử dụng trong hệ thống RAG Pipeline và minh hoạ tương đương trong thực tế:

| Thuật ngữ | Khái niệm kỹ thuật | Minh hoạ trực quan |
| :--- | :--- | :--- |
| **RAG** | Retrieval-Augmented Generation | **"Thi mở sách"**: Cho AI tra cứu tài liệu thực tế trước rồi mới tổng hợp câu trả lời ra (chống bịa đặt thông tin). |
| **Chunking** | Document Text Splitting | **"Chia nhỏ văn bản"**: Cắt một tài liệu dài thành từng đoạn nhỏ (ví dụ 800 ký tự) để phù hợp với giới hạn đọc của AI. |
| **Embedding** | Text Vectorization | **"Chuyển văn bản thành toạ độ"**: Đổi từng đoạn văn thành dãy số (toạ độ). Các đoạn có ý nghĩa tương đồng sẽ nằm gần nhau trong không gian. |
| **Vector Store** | Vector Database (ChromaDB) | **"Cơ sở dữ liệu toạ độ"**: Nơi lưu trữ các vector văn bản, hỗ trợ tìm kiếm các đoạn có toạ độ gần nhất với câu hỏi trong vài miligiây. |
| **Semantic Search** | Dense Retrieval (Cosine Similarity) | **"Tìm kiếm theo ngữ nghĩa"**: Tìm các đoạn văn có nội dung tương đồng về ý nghĩa dù từ ngữ sử dụng khác nhau. |
| **Lexical Search** | Sparse Retrieval (BM25) | **"Tìm kiếm theo từ khoá chính xác"**: Tìm các đoạn văn chứa đúng từ khoá trong câu hỏi (rất hiệu quả với số hiệu, mã tài liệu, tên riêng). |
| **HyDE** | Hypothetical Document Embeddings | **"Sinh câu trả lời giả định"**: Cho LLM sinh một đoạn trả lời giả lập trước, sau đó dùng đoạn đó để truy vấn trong cơ sở dữ liệu. |
| **Query Expansion** | Multi-Query Retrieval | **"Diễn đạt lại câu hỏi"**: Dùng LLM sinh 2-3 biến thể/đồng nghĩa của câu hỏi gốc, search riêng từng biến thể rồi gộp kết quả bằng RRF. |
| **RRF Reranking** | Reciprocal Rank Fusion | **"Gộp thứ hạng"**: Tổng hợp thứ hạng từ nhiều phương pháp tìm kiếm (Semantic và BM25) để chọn ra các đoạn văn tối ưu nhất. |
| **Vectorless RAG** | PageIndex Engine | **"Truy vấn theo cấu trúc"**: Đọc hiểu tài liệu theo chương, mục và tiêu đề mà không cần chia nhỏ (chunking) văn bản. |
| **Lost in the Middle** | Long-context Attention Deficit | **"Giảm chú ý ở giữa"**: Hiện tượng LLM ghi nhớ tốt thông tin ở **đầu** và **cuối** đoạn văn nhưng dễ bỏ sót thông tin ở **giữa**. |
| **Citation** | In-text Source Attribution | **"Trích dẫn nguồn"**: Yêu cầu LLM ghi rõ nguồn tài liệu tham khảo cho từng khẳng định trong câu trả lời. |
| **RAGAS Evaluation** | RAG Assessment Framework | **"Đánh giá tự động"**: Sử dụng LLM độc lập để đo lường chất lượng câu trả lời và độ chính xác của tài liệu thu thập. |

---

## 👥 2. Quy Mô & Sơ Đồ Phân Vai Nhóm (4–6 Thành Viên)

Tùy theo số lượng thành viên thực tế của từng nhóm (4, 5 hoặc 6 người), nhóm lựa chọn sơ đồ phân công phù hợp bên dưới:

## Nhiệm Vụ Chi Tiết

### Task 1 — Thu Thập Văn Bản Chính Sách Đại Học

Tìm và tải về **tối thiểu 3 văn bản chính sách/quy định** dạng PDF/DOCX về dịch vụ đại học (học phí, học bổng, ký túc xá, đăng ký học phần). Lưu vào `data/landing/`.

**Gợi ý nguồn** (ví dụ trang công khai RMIT Vietnam):
- Học phí & phương thức thanh toán (Tuition Fees)
- Chính sách học bổng (Scholarship eligibility)
- Quy định ký túc xá / hỗ trợ chỗ ở (Accommodation Services)
- Cổng đăng ký học phần (Course Registration Portal)

**Yêu cầu:**
- Lưu file gốc (PDF/DOCX) vào `data/landing/legal/`
- Đặt tên file rõ ràng: `tuition-fees-rmit.pdf`, `academic-achievement-scholarship-rmit.pdf`, ...

---

### Task 2 — Crawl Bài Viết/Thông Báo

Crawl **tối thiểu 5 bài viết** về thông tin/thông báo dịch vụ đại học (sự kiện, thư viện, hỗ trợ sinh viên, học bổng).

**Thư viện khuyến nghị:** [Crawl4AI](https://github.com/unclecode/crawl4ai)

**Yêu cầu:**
- Lưu output vào `data/landing/news/`
- Mỗi bài báo lưu thành 1 file (JSON hoặc HTML)
- Ghi rõ metadata: URL gốc, ngày crawl, tiêu đề bài báo

**Code mẫu (Crawl4AI):**
```python
from crawl4ai import AsyncWebCrawler

async def crawl_article(url: str, output_dir: str):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        # Lưu result.markdown vào file
        ...
```

---

### Task 3 — Convert Sang Markdown

Sử dụng [MarkItDown](https://github.com/microsoft/markitdown) của Microsoft để convert toàn bộ file trong `data/landing/` thành Markdown.

**Cài đặt:**
```bash
pip install markitdown
```

**Code mẫu:**
```python
from markitdown import MarkItDown

md = MarkItDown()

# Convert PDF
result = md.convert("data/landing/legal/tuition-fees-rmit.pdf")
print(result.text_content)

# Convert DOCX
result = md.convert("data/landing/legal/academic-achievement-scholarship-rmit.docx")
```

**Lưu ý:** MarkItDown cần cài thêm extra `pip install "markitdown[pdf]"` để convert được file
PDF — nếu chỉ `pip install markitdown` sẽ báo lỗi `MissingDependencyException` khi convert PDF.

**Yêu cầu:**
- Output lưu vào `data/standardized/`
- Giữ nguyên cấu trúc thư mục con (`legal/`, `news/`)
- Mỗi file output có tên tương ứng: `tuition-fees-rmit.md`

---

### Task 4 — Chunking & Indexing

Chọn **một loại chunking strategy** và **một embedding model** để index toàn bộ markdown files vào vector store.

**Chunking — khuyến khích dùng [langchain-text-splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/):**
```bash
pip install langchain-text-splitters
```

Các loại splitter phù hợp:
- `RecursiveCharacterTextSplitter` (mặc định, an toàn)
- `MarkdownHeaderTextSplitter` (tốt cho file có heading rõ)
- `SemanticChunker` (nâng cao, dùng embedding để tách)

**Embedding model gợi ý:**
- `sentence-transformers/all-MiniLM-L6-v2` (nhẹ, nhanh)
- `BAAI/bge-m3` (multilingual, tốt cho tiếng Việt)
- OpenAI `text-embedding-3-small` (nếu có API key)

**Vector Store — sử dụng ChromaDB (Vector Store mặc định của bài lab):**
```bash
pip install chromadb
```
- ChromaDB lưu trữ vector embeddings (`BAAI/bge-m3`), metadata và thông tin phân đoạn local tại thư mục `chroma_db/`
- Hỗ trợ truy vấn tìm kiếm tương đồng Cosine (Cosine Similarity Search) phục vụ Dense Retrieval ở Task 5

**Yêu cầu:**
- Ghi rõ trong code: dùng chunking nào, chunk_size bao nhiêu, overlap bao nhiêu, vì sao
- Ghi rõ embedding model nào, dimension bao nhiêu
- Index thành công toàn bộ documents

---

### Task 5 — Semantic Search Module

Viết module thực hiện **semantic search** (dense retrieval) trên vector store.

**Yêu cầu:**
```python
def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    ...
```

- Input: query string + top_k
- Output: danh sách chunks có score, sorted descending
- Phải hoạt động được với embedding model đã chọn ở Task 4

---

### Task 6 — Lexical Search Module

Viết module thực hiện **lexical search**. Mặc định sử dụng **BM25**.

```bash
pip install rank-bm25
```

**Code mẫu BM25:**
```python
from rank_bm25 import BM25Okapi

# Tokenize corpus
tokenized_corpus = [doc.split() for doc in corpus]
bm25 = BM25Okapi(tokenized_corpus)

# Search
tokenized_query = query.split()
scores = bm25.get_scores(tokenized_query)
```

**Yêu cầu:**
```python
def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
    """
    ...
```

**Bonus:** Nếu dùng phương pháp khác (TF-IDF, Elasticsearch, Weaviate BM25 built-in), hãy giải thích cơ chế hoạt động trong buổi demo → **+5 điểm bonus**.

---

### Task 7 — Reranking Module

Viết module **reranking** để chấm lại độ liên quan của kết quả retrieval.

**Lựa chọn (chọn 1):**

| Phương pháp | Thư viện / Model | Đặc điểm |
|-------------|-----------------|-----------|
| Cross-encoder reranker | `jinaai/jina-reranker-v2-base-multilingual` | Multilingual, tốt cho tiếng Việt |
| Cross-encoder reranker | `Qwen/Qwen3-Reranker-0.6B` | Nhẹ, hiệu quả |
| MMR (Maximal Marginal Relevance) | Tự implement | Giảm trùng lặp, tăng diversity |
| RRF (Reciprocal Rank Fusion) | Tự implement | Gộp kết quả từ nhiều ranker |

**Code mẫu (Jina Reranker via API):**
```python
import requests

def rerank(query: str, documents: list[str], top_k: int = 5) -> list[dict]:
    response = requests.post(
        "https://api.jina.ai/v1/rerank",
        headers={"Authorization": "Bearer YOUR_API_KEY"},
        json={
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "documents": documents,
            "top_n": top_k
        }
    )
    return response.json()["results"]
```

**Yêu cầu:**
```python
def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Re-score and re-order candidates based on relevance to query.
    """
    ...
```

---

### Task 8 — PageIndex Vectorless RAG

Đăng ký tài khoản tại [https://pageindex.ai/](https://pageindex.ai/), sau đó sử dụng [PageIndex SDK](https://github.com/VectifyAI/PageIndex) để tạo một **vectorless RAG pipeline**.

**Cài đặt:**
```bash
pip install pageindex
```

**Tham khảo:** [https://github.com/VectifyAI/PageIndex](https://github.com/VectifyAI/PageIndex)

**Yêu cầu:**
- Upload tài liệu lên PageIndex
- Viết function query PageIndex và trả về kết quả
```python
def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval using PageIndex.
    Fallback khi hybrid search không trả về kết quả phù hợp.
    """
    ...
```

---

### Task 9 — Retrieval Pipeline Hoàn Chỉnh

Kết hợp tất cả modules thành một **retrieval pipeline** thống nhất với logic fallback:

```
Query
  │
  ├─→ Semantic Search (Task 5)  ──┐
  │                                ├─→ Merge + Rerank (Task 7) → Results
  ├─→ Lexical Search (Task 6)  ──┘
  │
  └─→ Nếu hybrid search không có kết quả đủ tốt (score < threshold)
        └─→ Fallback: PageIndex Vectorless (Task 8)
```

**Yêu cầu:**
```python
def retrieve(query: str, top_k: int = 5, score_threshold: float = 0.3) -> list[dict]:
    """
    1. Chạy semantic_search + lexical_search
    2. Merge kết quả (RRF hoặc weighted fusion)
    3. Rerank
    4. Nếu top result score < threshold → fallback PageIndex
    5. Return top_k results
    """
    ...
```

> ⚠️ **Bẫy thường gặp:** nếu dùng RRF để merge (`RRF(d) = Σ 1/(k+rank)`, k=60), điểm số kết quả
> sau khi fuse **chỉ phụ thuộc thứ hạng**, không phản ánh độ liên quan thực sự — top-1 luôn
> xấp xỉ `1/(k+1) ≈ 0.016` dù nội dung có liên quan hay không. Nếu so `score_threshold` với
> điểm RRF đã fuse, fallback gần như **không bao giờ trigger** được (kể cả với query hoàn toàn
> lạc đề). Hãy so `score_threshold` với **điểm cosine similarity gốc** từ `semantic_search`
> (Task 5, thang đo `[0,1]` có ý nghĩa) — tách riêng khỏi điểm dùng để sắp xếp kết quả cuối cùng.



---

### Task 10 — Generation Có Citation

Sắp xếp lại context chunks sau reranking để **tránh lost in the middle**, inject vào prompt, và yêu cầu LLM trả lời có **citation**.

**Document Reordering (tránh lost in the middle):**
```python
def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks theo pattern: quan trọng nhất ở đầu và cuối,
    ít quan trọng hơn ở giữa.
    Ví dụ: [1, 3, 5, 4, 2] thay vì [1, 2, 3, 4, 5]
    """
    ...
```

**Prompt template:**
```python
SYSTEM_PROMPT = """Answer the following question comprehensively.
For every statement of fact or claim, immediately insert a citation
in brackets linking to the specific source
(e.g., [Author/Platform Name, Year]).
If the information is not explicitly stated in the provided context
or knowledge base, state 'I cannot verify this information'
rather than guessing."""

def generate_with_citation(query: str, context_chunks: list[dict]) -> str:
    """
    1. Reorder chunks để tránh lost in the middle
    2. Format context với source metadata
    3. Inject vào prompt với SYSTEM_PROMPT
    4. Gọi LLM (OpenAI, Gemini, hoặc local model)
    5. Return answer có citation
    """
    ...
```

**Yêu cầu:**
- Chọn top_k và top_p phù hợp (giải thích lý do trong code comment)
- Output phải có citation dạng `[Nguồn, Năm]`
- Nếu không đủ evidence → trả về "I cannot verify this information"

---


## 🎯 3. Phân Công Vai Trò & Công Việc Theo Từng Checkpoint

### 🔹 Checkpoint 0: Setup Môi Trường & Khởi Tạo Project (0:00 – 0:10 | 10 phút)
* 👑 **Role 1 (Team Leader & RAG Architect)**: Kiểm tra cả nhóm clone thành công repo Starter, khởi tạo repository chung cho nhóm và chia sẻ file `.env` với các API keys cần thiết (`OPENROUTER_API_KEY`).
* ⚙️ **Role 2 (Data & Pipeline Specialist / Data Dev)**: Tạo môi trường ảo (`python -m venv .venv`), cài đặt gói phụ thuộc từ `requirements.txt`, kiểm tra import `chromadb` và `sentence_transformers`.
* 🎨 **Role 3 (Frontend & Chatbot Dev)**: Kiểm tra cài đặt Streamlit bằng lệnh `streamlit run app.py`.
* 📊 **Role 4 / Role 5 / Role 6 (Evaluation & QA Engineer)**: Kiểm tra sự tồn tại và cài đặt của thư viện đánh giá `ragas` và `datasets`.
* ✅ **Tiêu chí hoàn thành (Pass Criteria)**: Tất cả các thành viên khởi tạo xong môi trường làm việc không có lỗi import. Coach gọi ngẫu nhiên 1-2 đại diện nhóm demo setup venv & kiểm tra kết nối API Key trong vài phút cuối (`CP0 Passed`).

---

### 🔹 Checkpoint 1: Thu Thập & Chuẩn Hoá Dữ Liệu — Task 1..3 (0:10 – 0:35 | 25 phút)
* 👑 **Role 1 (Team Leader & RAG Architect)**: Kiểm tra phân công nguồn dữ liệu để tránh trùng lặp tài liệu giữa các thành viên.
* ⚙️ **Role 2 (Data & Pipeline Specialist / Data Dev)**: Thực hiện **Task 1** — Tải $\ge 3$ tài liệu quy định/chính sách gốc (PDF/DOCX) lưu vào `data/landing/legal/`.
* 🎨 **Role 3 (Frontend & Chatbot Dev)**: Thực hiện **Task 2** — Chạy script crawl $\ge 5$ bài viết/thông báo hướng dẫn lưu vào `data/landing/news/`.
* 📊 **Role 4 / Role 5 / Role 6 (Evaluation & QA Engineer)**: Thực hiện **Task 3** — Thực thi `python -m src.task3_convert_markdown` chuyển đổi toàn bộ tài liệu sang dạng Markdown trong `data/standardized/`.
* ✅ **Tiêu chí hoàn thành (Pass Criteria)**: Đủ $\ge 3$ file trong `legal/`, $\ge 5$ file trong `news/`, và đã có các file `.md` tương ứng trong `standardized/`. Coach gọi ngẫu nhiên 1 nhóm demo file Markdown đã convert trong vài phút cuối (`CP1 Passed`).

---

### 🔹 Checkpoint 2: Chunking, Indexing & Search Cơ Bản — Task 4..6 (0:35 – 1:00 | 25 phút)
* 👑 **Role 1 (Team Leader & RAG Architect)**: Kiểm tra tham số chunking (`CHUNK_SIZE=800`, `CHUNK_OVERLAP=100`) và xác nhận việc sử dụng embedding model `BAAI/bge-m3`.
* ⚙️ **Role 2 (Data & Dense Search Dev)**: Thực hiện **Task 4** — Cắt đoạn văn bản, gọi model embedding và tạo cơ sở dữ liệu vector ChromaDB (`chroma_db/`).
* 🎨 **Role 3 (Sparse Search Dev / UI Dev)**: Thực hiện **Task 5** — Hoàn thiện hàm `semantic_search()` trong `src/task5_semantic_search.py` (Dense Retrieval dựa trên Cosine Similarity & HyDE).
* 📊 **Role 4 / Role 5 / Role 6 (Evaluation & QA Engineer)**: Thực hiện **Task 6** — Hoàn thiện hàm `lexical_search()` trong `src/task6_lexical_search.py` (Sparse Retrieval sử dụng BM25 & TF-IDF).
* ✅ **Tiêu chí hoàn thành (Pass Criteria)**: Khởi tạo xong `chroma_db/`; chạy `pytest tests/test_individual.py` vượt qua các kiểm thử của Task 4, 5, 6. Coach gọi ngẫu nhiên demo so sánh Semantic Search vs Lexical BM25 trong vài phút cuối (`CP2 Passed`).

---

### 🔹 Checkpoint 3: Reranking & Vectorless Fallback — Task 7..8 (1:00 – 1:20 | 20 phút)
* 👑 **Role 1 (Team Leader & RAG Architect)**: Kiểm tra công thức gộp thứ hạng RRF ($k=60$) đảm bảo cân bằng giữa kết quả Semantic và BM25.
* ⚙️ **Role 2 (Pipeline Specialist / Sparse Dev)**: Thực hiện **Task 7** — Hoàn thiện hàm `rerank_rrf()` trong `src/task7_reranking.py`.
* 🎨 **Role 3 (Frontend & Chatbot Dev)**: Thực hiện **Task 8** — Tích hợp SDK PageIndex trong `src/task8_pageindex_vectorless.py` để xử lý truy vấn trên văn bản dạng cấu trúc.
* 📊 **Role 4 / Role 5 / Role 6 (Evaluation & QA Engineer)**: Thử nghiệm các câu hỏi ngoài domain để kiểm tra khả năng kích hoạt fallback của hệ thống.
* ✅ **Tiêu chí hoàn thành (Pass Criteria)**: Thuật toán RRF rerank gộp thành công kết quả từ 2 ranker; PageIndex trả về kết quả truy vấn phù hợp. Coach gọi ngẫu nhiên 1 nhóm trình bày logic RRF & bẫy điều kiện Fallback (Cosine $< 0.48$) trong vài phút cuối (`CP3 Passed`).

---

### 🔹 Checkpoint 4: Pipeline Hoàn Chỉnh & Generation — Task 9..10 (1:20 – 1:45 | 25 phút)
* 👑 **Role 1 (Team Leader & RAG Architect)**: Kiểm tra toàn bộ mã nguồn bài cá nhân, chạy `pytest tests/test_individual.py` để xác nhận thành viên đạt đủ điểm bài cá nhân.
* ⚙️ **Role 2 (Data & Pipeline Specialist)**: Hoàn thiện **Task 9** (`src/task9_retrieval_pipeline.py`) — Nối chuỗi Semantic + BM25 + RRF + PageIndex Fallback khi điểm Cosine $< 0.48$.
* 🎨 **Role 3 (Frontend & Chatbot Dev)**: Hoàn thiện **Task 10** (`src/task10_generation.py`) — Áp dụng kỹ thuật Reordering (`front + back[::-1]`) và gọi LLM sinh câu trả lời có trích dẫn nguồn.
* 📊 **Role 4 / Role 5 / Role 6 (Evaluation & QA Engineer)**: Rà soát định dạng trích dẫn nguồn (citation format) trong câu trả lời từ LLM.
* ✅ **Tiêu chí hoàn thành (Pass Criteria)**: Chạy `pytest tests/test_individual.py` đạt **35/35 test passed** (Hoàn thành 50 điểm cá nhân). Coach chốt mốc điểm cá nhân & hỗ trợ gỡ lỗi trực tiếp trong vài phút cuối (`CP4 Passed`).

---

### 🔹 Checkpoint 5: Bài Tập Nhóm — Chatbot UI & Đánh Giá RAGAS (1:45 – 2:15 | 30 phút)
* 👑 **Role 1 (Team Leader & RAG Architect)**: Phân công tổng hợp đoạn mã nguồn tối ưu nhất của nhóm vào `app.py` và theo dõi tiến độ hoàn thiện báo cáo.
* ⚙️ **Role 2 (Data & Pipeline Specialist)**: Kết nối hàm `generate_with_citation()` từ Task 10 vào luồng xử lý câu hỏi của `app.py`.
* 🎨 **Role 3 (Frontend & Chatbot Dev)**: Hoàn thiện ứng dụng Chatbot Streamlit (`app.py`), thiết kế giao diện chat, thanh cài đặt tham số `top_k`, vùng hiển thị danh sách tài liệu tham khảo và các câu hỏi gợi ý.
* 📊 **Role 4 / Role 5 / Role 6 (Evaluation & QA Engineer)**: Xây dựng `group_project/evaluation/golden_dataset.json` (15–20 câu hỏi), thực thi `python -m group_project.evaluation.eval_pipeline` để thu thập 4 chỉ số RAGAS và hoàn thiện báo cáo `group_project/evaluation/results.md`.
* ✅ **Tiêu chí hoàn thành (Pass Criteria)**: Chatbot UI phản hồi chính xác kèm danh sách nguồn; báo cáo `results.md` hiển thị đầy đủ bảng điểm đánh giá A/B testing (`CP5 Passed`).

---

### 🔹 Checkpoint 6: Thuyết Trình Demo Live & Nộp Bài (2:15 – 3:00 | 45 phút)
* 👑 **Role 1 (Team Leader & RAG Architect)**: Thuyết trình tổng quan về ứng dụng Chatbot và kiến trúc RAG Pipeline trước lớp (5-8 phút/nhóm).
* ⚙️ **Role 2 (Data & Pipeline Specialist)**: Trả lời các câu hỏi kỹ thuật liên quan đến thuật toán Hybrid Search, RRF và Fallback logic từ Giảng viên / Coach.
* 🎨 **Role 3 (Frontend & Chatbot Dev)**: Trực tiếp thao tác và trình diễn ứng dụng Streamlit live demo trên màn hình chiếu.
* 📊 **Role 4 / Role 5 / Role 6 (Evaluation & QA Engineer)**: Báo cáo kết quả đánh giá RAGAS và đưa ra phân tích về hiệu quả giữa Hybrid Search vs Dense-Only.
* ✅ **Tiêu chí hoàn thành (Pass Criteria)**: Hoàn tất buổi thuyết trình demo và cập nhật toàn bộ mã nguồn lên repository GitHub của nhóm (`CP6 Passed`).

---

## 🛠️ 4. Hướng Dẫn Chi Tiết Từng Task (Step-by-Step)

### Task 1 & 2 — Thu Thập & Crawl Dữ Liệu
- **Nhiệm vụ**: Tải 3 file quy định/chính sách (PDF/DOCX) vào `data/landing/legal/` và crawl 5 bài tin tức/hướng dẫn vào `data/landing/news/`.
- **Lưu ý**: Nếu trang nguồn cấu hình chặn tự động (HTTP 403), có thể sử dụng bộ dữ liệu mẫu sẵn có trong bài lab hoặc lựa chọn trang công khai khác.

### Task 3 — Chuẩn Hoá Văn Bản Sang Markdown
- **Nhiệm vụ**: Chạy `python src/task3_convert_markdown.py`.
- **Mục tiêu**: Tất cả văn bản dạng PDF/DOCX/JSON/HTML được chuyển đổi thành `.md` trong thư mục `data/standardized/`.

### Task 4 — Chunking & Indexing
- **Nhiệm vụ**: Chạy `python src/task4_chunking_indexing.py`.
- **Mục tiêu**: Phân đoạn văn bản (size=800, overlap=100), chuyển đổi sang dạng vector với model `BAAI/bge-m3` và lưu trữ vào `chroma_db/`.

### Task 5 & 6 — Semantic Search & Lexical Search (BM25)
- **Nhiệm vụ**: Thực thi hàm `semantic_search()` trong `task5_semantic_search.py` và `lexical_search()` trong `task6_lexical_search.py`.
- **Đánh giá**: Quan sát sự khác biệt giữa tìm kiếm theo ngữ nghĩa và tìm kiếm theo từ khoá chính xác trên cùng câu truy vấn.

### Task 7 & 8 — Reranking (RRF) & PageIndex Fallback
- **Nhiệm vụ**:
  - Task 7: Áp dụng công thức $RRF(d) = \sum \frac{1}{60 + r(d)}$ để gộp thứ hạng từ nhiều nguồn.
  - Task 8: Sử dụng PageIndex SDK cho bài toán truy vấn dựa trên cấu trúc văn bản.

### Task 9 & 10 — Pipeline & Generation có Citation
- **Nhiệm vụ**:
  - Task 9: Nếu điểm Cosine Similarity tối ưu $< 0.48 \rightarrow$ chuyển sang PageIndex Fallback.
  - Task 10: Sắp xếp lại danh sách chunks (`front + back[::-1]`) để hạn chế hiện tượng giảm chú ý ở giữa, sau đó gửi tới LLM cùng hệ thống prompt yêu cầu trích dẫn nguồn.

---

## 🚨 5. Tổng Hợp Xử Lý Lỗi Thường Gặp (Troubleshooting)

| # | Lỗi / Hiện tượng | Nguyên nhân | Cách khắc phục |
| :-: | :--- | :--- | :--- |
| **1** | `MissingDependencyException` ở Task 3 | Cài đặt thiếu module đọc định dạng PDF của `markitdown`. | Thực thi: `pip install "markitdown[pdf]"` |
| **2** | Lỗi trình duyệt khi crawl ở Task 2 | Thư viện `crawl4ai` chưa cài đặt binary Chromium. | Thực thi: `playwright install chromium` |
| **3** | `UnicodeEncodeError` trên Windows | Console Windows hiển thị ký tự mã hoá cp1252/cp1258. | Thiết lập biến môi trường: `$env:PYTHONIOENCODING="utf-8"` hoặc dùng `python -X utf8`. |
| **4** | Logic Fallback không kích hoạt ở Task 9 | Sử dụng điểm RRF thay vì điểm Cosine Similarity gốc để so sánh threshold. | Sử dụng điểm Cosine gốc (`dense_results[0]["score"]`) cho ngưỡng `SCORE_THRESHOLD = 0.48`. |
| **5** | Vượt giới hạn lượt gọi (Rate Limit) ở RAGAS | RAGAS tạo nhiều lượt gọi LLM judge dẫn đến chạm hạn mức của OpenRouter free. | Thu nhỏ số lượng câu hỏi kiểm thử trong `golden_dataset.json` trong quá trình thử nghiệm. |
| **6** | Lẫn lộn dữ liệu giữa các lần chạy | Thay đổi bộ văn bản đầu vào nhưng chưa làm sạch cơ sở dữ liệu cũ. | Xóa thư mục `chroma_db/` và khởi chạy lại `task4_chunking_indexing.py`. |
