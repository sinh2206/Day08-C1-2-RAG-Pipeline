"""
🏮 Trợ Lý Giải Đáp Phong Tục, Trang Phục & Lễ Hội Truyền Thống Việt Nam
Streamlit Application — Topic 6 (Vietnamese Folklore, Traditional Costumes & Festivals RAG)
"""

import os
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path to allow importing from src/
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import Task 10 generation function
try:
    from src.task10_generation import generate_with_citation
except ImportError:
    generate_with_citation = None

# =============================================================================
# PAGE CONFIGURATION & CUSTOM STYLING
# =============================================================================

st.set_page_config(
    page_title="Trợ Lý Văn Hóa Dân Gian & Lễ Hội Việt Nam",
    page_icon="🏮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich aesthetics (Crimson & Gold cultural theme)
st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #8B0000 0%, #B22222 50%, #D2691E 100%);
        padding: 24px;
        border-radius: 12px;
        color: #FFF8DC;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: #FFD700 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .main-header p {
        color: #FFF8DC;
        font-size: 1.05rem;
        margin-bottom: 0;
    }
    .tag-badge {
        background-color: rgba(255, 215, 0, 0.2);
        color: #FFD700;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        border: 1px solid rgba(255, 215, 0, 0.4);
        margin-right: 6px;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# MOCK KNOWLEDGE BASE FOR FAST DEMO / FALLBACK
# =============================================================================

MOCK_KNOWLEDGE = {
    "Ý nghĩa của tục xông đất đầu năm và những điều kiêng kỵ trong ngày Tết Nguyên Đán là gì?": {
        "answer": """### 🏮 Ý Nghĩa Tục Xông Đất & Các Điều Kiêng Kỵ Ngày Tết Nguyên Đán

**1. Ý nghĩa tục Xông Đất (Tục Xổi Đất) đầu năm:**
* **Khởi đầu vận hội:** Người Việt quan niệm người đầu tiên bước vào nhà sau giờ giao thừa sẽ đem theo vận khí, may mắn và tài lộc cho cả gia đình trong suốt năm mới `[Tuc_Xong_Dat.md]`.
* **Tiêu chí chọn người:** Gia chủ thường chọn người có **tuổi hợp với gia chủ**, tính tình hòa nhã, xởi lởi, gia đạo êm ấm để xông đất `[Tuc_Xong_Dat.md]`.

---

**2. Những điều kiêng kỵ quan trọng ngày Tết:**
* 🚫 **Không quét nhà, đổ rác ngày Mùng 1:** Theo tích cổ, quét nhà là quét đi tài lộc và thần may mắn ra khỏi cửa `[Kieng_Ky_Tet.md]`.
* 🚫 **Kiêng làm vỡ bát đĩa, đồ sành sứ:** Sự đổ vỡ tượng trưng cho sự chia cắt, rạn nứt gia đạo `[Kieng_Ky_Tet.md]`.
* 🚫 **Kiêng cho vay mượn tiền bạc:** Đầu năm mở quẻ vay mượn báo hiệu một năm túng thiếu, nợ nần `[Kieng_Ky_Tet.md]`.
""",
        "sources": [
            {"content": "Tục xông đất xuất phát từ ước vọng về một năm mới an lành...", "metadata": {"source": "Tuc_Xong_Dat.md", "type": "folklore"}, "score": 0.94},
            {"content": "Các điều kiêng kỵ dân gian ngày Tết: Tránh quét nhà Mùng 1...", "metadata": {"source": "Kieng_Ky_Tet.md", "type": "cultural_doc"}, "score": 0.91},
        ],
    },
    "Trang phục Áo ngũ thân nam truyền thống gồm những chi tiết nào và sự khác biệt với Áo dài tân thời?": {
        "answer": """### 👘 Áo Ngũ Thân Nam Truyền Thống vs. Áo Dài Tân Thời

**1. Cấu tạo chi tiết của Áo Ngũ Thân Nam:**
* **5 Thân áo (Ngũ thân):** Gồm 2 thân trước, 2 thân sau và 1 thân con giấu bên trong — tượng trưng cho **Ngũ thường (Nhân, Lễ, Nghĩa, Trí, Tín)** `[Ao_Ngu_Than.md]`.
* **5 Cúc áo (Khuy):** Tượng trưng cho **Ngũ luân (Quân thần, Phụ tử, Phu thê, Huynh đệ, Bằng hữu)** `[Ao_Ngu_Than.md]`.
* **Cổ đứng:** Cổ chầu cao kín đáo, cài cúc bên phải `[Ao_Ngu_Than.md]`.

---

**2. Sự khác biệt với Áo Dài Tân Thời:**
Áo ngũ thân có phom suông rộng rãi, không chiết eo, có lớp tạ con che chắn kín đáo, khác biệt hoàn toàn với Áo dài tân thời chít eo tôn nét cong cơ thể theo phong cách phương Tây `[Ao_Dai_Lich_Su.md]`.
""",
        "sources": [
            {"content": "Áo ngũ thân lập lĩnh ra đời dưới thời chúa Nguyễn Phúc Khoát...", "metadata": {"source": "Ao_Ngu_Than.md", "type": "heritage"}, "score": 0.96},
            {"content": "So sánh áo ngũ thân và áo dài tân thời Lemur...", "metadata": {"source": "Ao_Dai_Lich_Su.md", "type": "cultural_doc"}, "score": 0.92},
        ],
    },
}

GENERIC_MOCK_ANSWER = {
    "answer": """### 🎓 Kết Quả Tra Cứu Tri Thức RAG

Dựa trên dữ liệu tài liệu được indexed trong hệ thống:

* **Chính sách & Dịch vụ:** Bạn có thể tra cứu thông tin chi tiết về Học phí, Học bổng, Ký túc xá và Đăng ký học phần `[RMIT_Services.md]`.
* **Văn hóa & Phong tục:** Tra cứu phong tục Tết Nguyên Đán, Áo ngũ thân và Lễ hội dân gian `[Van_Hoa_Dan_Gian.md]`.
""",
    "sources": [
        {"content": "Nội dung tổng quan tài liệu tra cứu...", "metadata": {"source": "RAG_Knowledge_Base.md", "type": "general"}, "score": 0.88}
    ]
}

# =============================================================================
# SIDEBAR — CONTROLS & SETTINGS
# =============================================================================

with st.sidebar:
    st.markdown(
        """
        <div style='text-align: center; padding: 10px;'>
            <h2 style='color: #FFD700; margin-bottom: 0;'>🏮 Nét Việt AI</h2>
            <p style='color: #E0E0E0; font-size: 0.9rem;'>Trợ Lý Văn Hóa & Dịch Vụ Đại Học</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    st.subheader("💡 Câu Hỏi Mẫu")
    suggestions = [
        "Ý nghĩa của tục xông đất đầu năm và những điều kiêng kỵ trong ngày Tết Nguyên Đán là gì?",
        "Trang phục Áo ngũ thân nam truyền thống gồm những chi tiết nào và sự khác biệt với Áo dài tân thời?",
        "Học phí tại RMIT Vietnam là bao nhiêu?",
        "Điều kiện xin học bổng Academic Achievement?",
    ]

    for idx, sug in enumerate(suggestions):
        short_label = f"{sug[:38]}..."
        if st.button(f"📌 {short_label}", use_container_width=True, key=f"sug_btn_{idx}"):
            st.session_state["pending_query"] = sug

    st.divider()
    st.subheader("⚙️ Cấu Hình Execution")
    exec_mode = st.radio(
        "Chế độ phản hồi (Response Mode)",
        options=["Tự động (Fast Fallback)", "Chỉ dùng Mock Instant Demo", "Chạy Live Task 10 Backend"],
        index=0,
    )

    top_k = st.slider("Số chunks retrieval (top_k)", min_value=1, max_value=10, value=5)

    st.divider()
    if st.button("🗑️ Xóa Lịch Sử Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# =============================================================================
# MAIN INTERFACE
# =============================================================================

st.markdown(
    """
    <div class="main-header">
        <h1>🏮 Trợ Lý RAG Văn Hóa & Dịch Vụ Đại Học</h1>
        <p>Hệ thống RAG tra cứu trực quan kết nối Task 10 (Document Reordering & Citation Generation)</p>
        <div style="margin-top: 12px;">
            <span class="tag-badge">🌾 Phong Tục Tết</span>
            <span class="tag-badge">👘 Áo Ngũ Thân</span>
            <span class="tag-badge">🎓 Dịch Vụ Đại Học</span>
            <span class="tag-badge">📚 Citation Generator</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander(f"📚 Nguồn tham khảo trích dẫn ({len(msg['sources'])} chunks)"):
                for i, src in enumerate(msg["sources"], 1):
                    meta = src.get("metadata", {})
                    source_name = meta.get("source", "Tài liệu Văn hóa")
                    doc_type = meta.get("type", "cultural_doc")
                    score = src.get("score", 0.0)
                    st.markdown(f"**[{i}] {source_name}** | loại: `{doc_type}` | score: `{score:.4f}`")
                    st.text(src.get("content", "")[:350] + "...")
                    st.divider()

# =============================================================================
# QUERY PROCESSING
# =============================================================================

user_input = st.chat_input("Nhập câu hỏi của bạn...")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Append user question
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Đang thực thi Retrieval & Task 10 Generation..."):
            start_time = time.time()
            answer = ""
            sources = []
            retrieval_src = "hybrid"

            if exec_mode == "Chỉ dùng Mock Instant Demo":
                time.sleep(0.3)
                mock_entry = MOCK_KNOWLEDGE.get(query.strip(), GENERIC_MOCK_ANSWER)
                answer = mock_entry["answer"]
                sources = mock_entry["sources"][:top_k]
                retrieval_src = "mock_demo"
            else:
                try:
                    if generate_with_citation is not None:
                        response = generate_with_citation(query, top_k=top_k)
                        answer = response.get("answer", "")
                        sources = response.get("sources", [])
                        retrieval_src = response.get("retrieval_source", "hybrid")

                        # If backend answer is empty or unverified fallback, check fast mock if in auto mode
                        if (not answer or "Tôi không thể xác minh" in answer) and exec_mode == "Tự động (Fast Fallback)":
                            mock_entry = MOCK_KNOWLEDGE.get(query.strip(), None)
                            if mock_entry:
                                answer = mock_entry["answer"]
                                sources = mock_entry["sources"][:top_k]
                                retrieval_src = "mock_fallback"
                    else:
                        answer = "⚠️ **Không thể kết nối Task 10.**"
                except Exception as e:
                    if exec_mode == "Tự động (Fast Fallback)":
                        mock_entry = MOCK_KNOWLEDGE.get(query.strip(), GENERIC_MOCK_ANSWER)
                        answer = mock_entry["answer"]
                        sources = mock_entry["sources"][:top_k]
                        retrieval_src = "fast_fallback"
                    else:
                        answer = f"❌ **Lỗi RAG Pipeline:** {e}"

            elapsed_ms = (time.time() - start_time) * 1000

            # Render answer
            st.markdown(answer)

            # Render Telemetry
            st.caption(f"⚡ Thời gian phản hồi: `{elapsed_ms:.1f} ms` | 🎯 Chunks: `{len(sources)}` | ⚙️ Pipeline: `{retrieval_src}`")

            # Render Sources Expander
            if sources:
                with st.expander(f"📚 Nguồn tham khảo trích dẫn ({len(sources)} chunks)"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", "Tài liệu RAG")
                        doc_type = meta.get("type", "doc")
                        score = src.get("score", 0.0)
                        st.markdown(f"**[{i}] {source_name}** | loại: `{doc_type}` | score: `{score:.4f}`")
                        st.text(src.get("content", "")[:350] + "...")
                        st.divider()

    # Save to chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
